"""
SLA Analytics Service

This service computes Service Level Agreement (SLA) metrics for monitors over arbitrary time ranges.

Metrics Calculated:
- Availability percentage: (uptime / total_time) * 100
- Mean response time: average of all successful check response times
- Percentile response times: p50, p75, p90, p95, p99
- Failure count: number of failed checks
- Downtime duration: total time in downtime state

Assumptions:
1. Missing checks are NOT treated as downtime - only explicit failures are counted
2. Availability is calculated as: (total_time - downtime) / total_time * 100
3. Response times only include successful checks (is_up=True and response_time_ms is not NULL)
4. Downtime windows with ended_at=NULL are considered ongoing and counted up to the query end time
5. For bucketed results, metrics are calculated independently for each bucket period

Time Range Handling:
- Queries are inclusive of start_time and end_time
- Bucketing aligns to natural boundaries (start of day/week/month in UTC)
- Week buckets start on Monday (ISO week format)

Calculation Formulas:
- availability_percent = ((end_time - start_time - total_downtime_seconds) / (end_time - start_time)) * 100
- mean_response_time = sum(response_time_ms) / count(successful_checks)
- percentile_response_time = value at specified percentile of sorted response times
- total_downtime_seconds = sum(min(ended_at or end_time, end_time) - max(started_at, start_time))
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Literal
from dataclasses import dataclass
from functools import lru_cache
import time
from collections import defaultdict

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session
import numpy as np

from app.models.monitoring import MonitorCheck, DowntimeWindow


BucketType = Literal["day", "week", "month"]


@dataclass
class SLAMetrics:
    """Container for SLA metrics"""
    start_time: datetime
    end_time: datetime
    availability_percent: float
    mean_response_time_ms: Optional[float]
    percentile_response_times: Dict[str, Optional[float]]
    failure_count: int
    total_downtime_seconds: float
    total_checks: int
    successful_checks: int


@dataclass
class TimeSeriesPoint:
    """Data point for time series charts"""
    timestamp: datetime
    value: float
    label: str


class CacheEntry:
    """Simple TTL cache entry"""
    def __init__(self, value: Any, ttl_seconds: int):
        self.value = value
        self.expires_at = time.time() + ttl_seconds
    
    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class SLAAnalyticsService:
    """Service for computing SLA metrics with optional caching"""
    
    def __init__(self, cache_ttl_seconds: int = 300, enable_cache: bool = True):
        self.cache_ttl_seconds = cache_ttl_seconds
        self.enable_cache = enable_cache
        self._cache: Dict[str, CacheEntry] = {}
        self._redis_client = None
    
    def set_redis_client(self, redis_client):
        """Optionally configure Redis for distributed caching"""
        self._redis_client = redis_client
    
    def _get_cache_key(self, monitor_id: int, start_time: datetime, end_time: datetime, 
                       bucket: Optional[str]) -> str:
        """Generate cache key for metrics query"""
        return f"sla:{monitor_id}:{start_time.isoformat()}:{end_time.isoformat()}:{bucket or 'none'}"
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get value from cache (Redis or in-memory)"""
        if not self.enable_cache:
            return None
        
        if self._redis_client:
            try:
                import json
                value = self._redis_client.get(key)
                if value:
                    return json.loads(value)
            except Exception:
                pass
        
        entry = self._cache.get(key)
        if entry and not entry.is_expired():
            return entry.value
        elif entry:
            del self._cache[key]
        
        return None
    
    def _set_in_cache(self, key: str, value: Any):
        """Set value in cache (Redis or in-memory)"""
        if not self.enable_cache:
            return
        
        if self._redis_client:
            try:
                import json
                self._redis_client.setex(key, self.cache_ttl_seconds, json.dumps(value))
            except Exception:
                pass
        
        self._cache[key] = CacheEntry(value, self.cache_ttl_seconds)
    
    def calculate_metrics(
        self,
        db: Session,
        monitor_id: int,
        start_time: datetime,
        end_time: datetime,
        percentiles: Optional[List[int]] = None
    ) -> SLAMetrics:
        """
        Calculate SLA metrics for a monitor over a time range.
        
        Args:
            db: Database session
            monitor_id: Monitor ID to calculate metrics for
            start_time: Start of time range (inclusive)
            end_time: End of time range (inclusive)
            percentiles: List of percentiles to calculate (e.g., [50, 90, 95, 99])
        
        Returns:
            SLAMetrics object containing all calculated metrics
        """
        if percentiles is None:
            percentiles = [50, 75, 90, 95, 99]
        
        cache_key = self._get_cache_key(monitor_id, start_time, end_time, None)
        cached = self._get_from_cache(cache_key)
        if cached:
            return SLAMetrics(**cached)
        
        total_period_seconds = (end_time - start_time).total_seconds()
        
        checks = db.query(MonitorCheck).filter(
            MonitorCheck.monitor_id == monitor_id,
            MonitorCheck.checked_at >= start_time,
            MonitorCheck.checked_at <= end_time
        ).all()
        
        total_checks = len(checks)
        successful_checks = [c for c in checks if c.is_up]
        failed_checks = [c for c in checks if not c.is_up]
        failure_count = len(failed_checks)
        
        response_times = [
            c.response_time_ms for c in successful_checks 
            if c.response_time_ms is not None
        ]
        
        mean_response_time = np.mean(response_times) if response_times else None
        
        percentile_response_times = {}
        for p in percentiles:
            if response_times:
                percentile_response_times[f"p{p}"] = float(np.percentile(response_times, p))
            else:
                percentile_response_times[f"p{p}"] = None
        
        downtime_windows = db.query(DowntimeWindow).filter(
            DowntimeWindow.monitor_id == monitor_id,
            or_(
                and_(
                    DowntimeWindow.started_at <= end_time,
                    DowntimeWindow.ended_at >= start_time
                ),
                and_(
                    DowntimeWindow.started_at <= end_time,
                    DowntimeWindow.ended_at.is_(None)
                )
            )
        ).all()
        
        total_downtime_seconds = 0.0
        for window in downtime_windows:
            window_start = max(window.started_at, start_time)
            window_end = min(window.ended_at or end_time, end_time)
            
            if window_end > window_start:
                total_downtime_seconds += (window_end - window_start).total_seconds()
        
        uptime_seconds = total_period_seconds - total_downtime_seconds
        availability_percent = (uptime_seconds / total_period_seconds * 100) if total_period_seconds > 0 else 100.0
        
        metrics = SLAMetrics(
            start_time=start_time,
            end_time=end_time,
            availability_percent=availability_percent,
            mean_response_time_ms=float(mean_response_time) if mean_response_time is not None else None,
            percentile_response_times=percentile_response_times,
            failure_count=failure_count,
            total_downtime_seconds=total_downtime_seconds,
            total_checks=total_checks,
            successful_checks=len(successful_checks)
        )
        
        self._set_in_cache(cache_key, {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "availability_percent": availability_percent,
            "mean_response_time_ms": metrics.mean_response_time_ms,
            "percentile_response_times": percentile_response_times,
            "failure_count": failure_count,
            "total_downtime_seconds": total_downtime_seconds,
            "total_checks": total_checks,
            "successful_checks": len(successful_checks)
        })
        
        return metrics
    
    def get_bucketed_metrics(
        self,
        db: Session,
        monitor_id: int,
        start_time: datetime,
        end_time: datetime,
        bucket_type: BucketType,
        percentiles: Optional[List[int]] = None
    ) -> List[SLAMetrics]:
        """
        Calculate SLA metrics bucketed by time period (day/week/month).
        
        Args:
            db: Database session
            monitor_id: Monitor ID to calculate metrics for
            start_time: Start of time range (inclusive)
            end_time: End of time range (inclusive)
            bucket_type: Type of bucketing - "day", "week", or "month"
            percentiles: List of percentiles to calculate
        
        Returns:
            List of SLAMetrics, one per bucket
        """
        cache_key = self._get_cache_key(monitor_id, start_time, end_time, bucket_type)
        cached = self._get_from_cache(cache_key)
        if cached:
            return [SLAMetrics(**m) for m in cached]
        
        buckets = self._generate_buckets(start_time, end_time, bucket_type)
        
        results = []
        for bucket_start, bucket_end in buckets:
            metrics = self.calculate_metrics(
                db, monitor_id, bucket_start, bucket_end, percentiles
            )
            results.append(metrics)
        
        self._set_in_cache(cache_key, [
            {
                "start_time": m.start_time.isoformat(),
                "end_time": m.end_time.isoformat(),
                "availability_percent": m.availability_percent,
                "mean_response_time_ms": m.mean_response_time_ms,
                "percentile_response_times": m.percentile_response_times,
                "failure_count": m.failure_count,
                "total_downtime_seconds": m.total_downtime_seconds,
                "total_checks": m.total_checks,
                "successful_checks": m.successful_checks
            }
            for m in results
        ])
        
        return results
    
    def _generate_buckets(
        self, 
        start_time: datetime, 
        end_time: datetime, 
        bucket_type: BucketType
    ) -> List[tuple[datetime, datetime]]:
        """Generate time buckets aligned to natural boundaries"""
        buckets = []
        
        if bucket_type == "day":
            current = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
            while current < end_time:
                bucket_end = min(current + timedelta(days=1), end_time)
                if current >= start_time:
                    buckets.append((current, bucket_end))
                current += timedelta(days=1)
        
        elif bucket_type == "week":
            current = start_time - timedelta(days=start_time.weekday())
            current = current.replace(hour=0, minute=0, second=0, microsecond=0)
            while current < end_time:
                bucket_end = min(current + timedelta(weeks=1), end_time)
                if current >= start_time or bucket_end > start_time:
                    actual_start = max(current, start_time)
                    buckets.append((actual_start, bucket_end))
                current += timedelta(weeks=1)
        
        elif bucket_type == "month":
            current = start_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            while current < end_time:
                if current.month == 12:
                    next_month = current.replace(year=current.year + 1, month=1)
                else:
                    next_month = current.replace(month=current.month + 1)
                bucket_end = min(next_month, end_time)
                if current >= start_time:
                    buckets.append((current, bucket_end))
                current = next_month
        
        return buckets
    
    def get_availability_time_series(
        self,
        db: Session,
        monitor_id: int,
        start_time: datetime,
        end_time: datetime,
        bucket_type: BucketType = "day"
    ) -> List[TimeSeriesPoint]:
        """
        Get availability percentage as a time series for charting.
        
        Returns:
            List of TimeSeriesPoint objects suitable for chart libraries
        """
        metrics = self.get_bucketed_metrics(db, monitor_id, start_time, end_time, bucket_type)
        
        return [
            TimeSeriesPoint(
                timestamp=m.start_time,
                value=m.availability_percent,
                label=self._format_bucket_label(m.start_time, bucket_type)
            )
            for m in metrics
        ]
    
    def get_response_time_time_series(
        self,
        db: Session,
        monitor_id: int,
        start_time: datetime,
        end_time: datetime,
        bucket_type: BucketType = "day",
        metric: str = "mean"
    ) -> List[TimeSeriesPoint]:
        """
        Get response time as a time series for charting.
        
        Args:
            metric: "mean" or percentile like "p95"
        
        Returns:
            List of TimeSeriesPoint objects suitable for chart libraries
        """
        metrics = self.get_bucketed_metrics(db, monitor_id, start_time, end_time, bucket_type)
        
        return [
            TimeSeriesPoint(
                timestamp=m.start_time,
                value=m.mean_response_time_ms if metric == "mean" else m.percentile_response_times.get(metric),
                label=self._format_bucket_label(m.start_time, bucket_type)
            )
            for m in metrics
        ]
    
    def _format_bucket_label(self, timestamp: datetime, bucket_type: BucketType) -> str:
        """Format bucket timestamp as human-readable label"""
        if bucket_type == "day":
            return timestamp.strftime("%Y-%m-%d")
        elif bucket_type == "week":
            return f"{timestamp.strftime('%Y-W%U')}"
        elif bucket_type == "month":
            return timestamp.strftime("%Y-%m")
        return timestamp.isoformat()
    
    def clear_cache(self):
        """Clear all cached metrics"""
        self._cache.clear()
        if self._redis_client:
            try:
                for key in self._redis_client.scan_iter("sla:*"):
                    self._redis_client.delete(key)
            except Exception:
                pass
