"""
Comprehensive unit tests for SLA Analytics Service

Test scenarios:
1. Continuous uptime - 100% availability
2. Intermittent outages - varying availability percentages
3. Missing data - periods with no checks
4. Response time calculations - mean and percentiles
5. Downtime calculations - ongoing and completed windows
6. Bucketed metrics - day/week/month aggregation
7. Time series generation - chart-friendly data
8. Caching behavior - in-memory cache validation
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.database import Base
from app.models.monitoring import Monitor, MonitorCheck, DowntimeWindow
from app.services.sla_analytics import SLAAnalyticsService


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture
def monitor(db_session: Session):
    """Create a test monitor"""
    monitor = Monitor(
        name="Test Monitor",
        url="https://example.com",
        check_interval_seconds=60
    )
    db_session.add(monitor)
    db_session.commit()
    db_session.refresh(monitor)
    return monitor


@pytest.fixture
def sla_service():
    """Create SLA analytics service instance"""
    return SLAAnalyticsService(enable_cache=True, cache_ttl_seconds=300)


class TestContinuousUptime:
    """Test scenarios with 100% uptime"""
    
    def test_perfect_uptime(self, db_session: Session, monitor: Monitor, sla_service: SLAAnalyticsService):
        """Test 100% availability with all successful checks"""
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 1, 2, 0, 0, 0)
        
        for i in range(24):
            check = MonitorCheck(
                monitor_id=monitor.id,
                checked_at=start_time + timedelta(hours=i),
                response_time_ms=100.0 + i * 5,
                status_code=200,
                is_up=True
            )
            db_session.add(check)
        
        db_session.commit()
        
        metrics = sla_service.calculate_metrics(db_session, monitor.id, start_time, end_time)
        
        assert metrics.availability_percent == 100.0
        assert metrics.total_downtime_seconds == 0.0
        assert metrics.failure_count == 0
        assert metrics.total_checks == 24
        assert metrics.successful_checks == 24
        assert metrics.mean_response_time_ms is not None
        assert 100.0 <= metrics.mean_response_time_ms <= 215.0
    
    def test_no_checks_no_downtime(self, db_session: Session, monitor: Monitor, sla_service: SLAAnalyticsService):
        """Test that missing checks don't count as downtime (per assumptions)"""
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 1, 2, 0, 0, 0)
        
        metrics = sla_service.calculate_metrics(db_session, monitor.id, start_time, end_time)
        
        assert metrics.availability_percent == 100.0
        assert metrics.total_downtime_seconds == 0.0
        assert metrics.failure_count == 0
        assert metrics.total_checks == 0
        assert metrics.mean_response_time_ms is None


class TestIntermittentOutages:
    """Test scenarios with varying levels of downtime"""
    
    def test_single_downtime_window(self, db_session: Session, monitor: Monitor, sla_service: SLAAnalyticsService):
        """Test metrics with one completed downtime window"""
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 1, 2, 0, 0, 0)
        
        for i in range(24):
            is_up = not (6 <= i < 8)
            check = MonitorCheck(
                monitor_id=monitor.id,
                checked_at=start_time + timedelta(hours=i),
                response_time_ms=100.0 if is_up else None,
                status_code=200 if is_up else 500,
                is_up=is_up
            )
            db_session.add(check)
        
        downtime = DowntimeWindow(
            monitor_id=monitor.id,
            started_at=datetime(2024, 1, 1, 6, 0, 0),
            ended_at=datetime(2024, 1, 1, 8, 0, 0),
            failure_count=2
        )
        db_session.add(downtime)
        db_session.commit()
        
        metrics = sla_service.calculate_metrics(db_session, monitor.id, start_time, end_time)
        
        total_seconds = 24 * 3600
        downtime_seconds = 2 * 3600
        expected_availability = ((total_seconds - downtime_seconds) / total_seconds) * 100
        
        assert abs(metrics.availability_percent - expected_availability) < 0.01
        assert metrics.total_downtime_seconds == downtime_seconds
        assert metrics.failure_count == 2
        assert metrics.successful_checks == 22
    
    def test_ongoing_downtime(self, db_session: Session, monitor: Monitor, sla_service: SLAAnalyticsService):
        """Test metrics with ongoing downtime (ended_at=NULL)"""
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 1, 2, 0, 0, 0)
        
        for i in range(12):
            check = MonitorCheck(
                monitor_id=monitor.id,
                checked_at=start_time + timedelta(hours=i),
                response_time_ms=100.0,
                status_code=200,
                is_up=True
            )
            db_session.add(check)
        
        for i in range(12, 24):
            check = MonitorCheck(
                monitor_id=monitor.id,
                checked_at=start_time + timedelta(hours=i),
                response_time_ms=None,
                status_code=500,
                is_up=False
            )
            db_session.add(check)
        
        downtime = DowntimeWindow(
            monitor_id=monitor.id,
            started_at=datetime(2024, 1, 1, 12, 0, 0),
            ended_at=None,
            failure_count=12
        )
        db_session.add(downtime)
        db_session.commit()
        
        metrics = sla_service.calculate_metrics(db_session, monitor.id, start_time, end_time)
        
        assert metrics.availability_percent == 50.0
        assert metrics.total_downtime_seconds == 12 * 3600
        assert metrics.failure_count == 12
    
    def test_multiple_downtime_windows(self, db_session: Session, monitor: Monitor, sla_service: SLAAnalyticsService):
        """Test metrics with multiple non-overlapping downtime windows"""
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 1, 4, 0, 0, 0)
        
        downtime1 = DowntimeWindow(
            monitor_id=monitor.id,
            started_at=datetime(2024, 1, 1, 10, 0, 0),
            ended_at=datetime(2024, 1, 1, 11, 0, 0),
            failure_count=1
        )
        downtime2 = DowntimeWindow(
            monitor_id=monitor.id,
            started_at=datetime(2024, 1, 2, 14, 0, 0),
            ended_at=datetime(2024, 1, 2, 16, 0, 0),
            failure_count=2
        )
        downtime3 = DowntimeWindow(
            monitor_id=monitor.id,
            started_at=datetime(2024, 1, 3, 8, 0, 0),
            ended_at=datetime(2024, 1, 3, 9, 30, 0),
            failure_count=2
        )
        
        db_session.add_all([downtime1, downtime2, downtime3])
        db_session.commit()
        
        metrics = sla_service.calculate_metrics(db_session, monitor.id, start_time, end_time)
        
        total_downtime = 1 * 3600 + 2 * 3600 + 1.5 * 3600
        assert metrics.total_downtime_seconds == total_downtime
    
    def test_partial_downtime_window(self, db_session: Session, monitor: Monitor, sla_service: SLAAnalyticsService):
        """Test downtime window that extends beyond query range"""
        start_time = datetime(2024, 1, 1, 12, 0, 0)
        end_time = datetime(2024, 1, 2, 12, 0, 0)
        
        downtime = DowntimeWindow(
            monitor_id=monitor.id,
            started_at=datetime(2024, 1, 1, 6, 0, 0),
            ended_at=datetime(2024, 1, 2, 18, 0, 0),
            failure_count=10
        )
        db_session.add(downtime)
        db_session.commit()
        
        metrics = sla_service.calculate_metrics(db_session, monitor.id, start_time, end_time)
        
        assert metrics.total_downtime_seconds == 24 * 3600
        assert metrics.availability_percent == 0.0


class TestResponseTimeCalculations:
    """Test response time metrics (mean and percentiles)"""
    
    def test_mean_response_time(self, db_session: Session, monitor: Monitor, sla_service: SLAAnalyticsService):
        """Test mean response time calculation"""
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 1, 1, 12, 0, 0)
        
        response_times = [100, 150, 200, 250, 300]
        for i, rt in enumerate(response_times):
            check = MonitorCheck(
                monitor_id=monitor.id,
                checked_at=start_time + timedelta(hours=i),
                response_time_ms=rt,
                status_code=200,
                is_up=True
            )
            db_session.add(check)
        
        db_session.commit()
        
        metrics = sla_service.calculate_metrics(db_session, monitor.id, start_time, end_time)
        
        expected_mean = sum(response_times) / len(response_times)
        assert metrics.mean_response_time_ms == expected_mean
    
    def test_percentile_calculations(self, db_session: Session, monitor: Monitor, sla_service: SLAAnalyticsService):
        """Test percentile response time calculations"""
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 1, 1, 12, 0, 0)
        
        response_times = list(range(100, 200, 10))
        for i, rt in enumerate(response_times):
            check = MonitorCheck(
                monitor_id=monitor.id,
                checked_at=start_time + timedelta(minutes=i * 10),
                response_time_ms=float(rt),
                status_code=200,
                is_up=True
            )
            db_session.add(check)
        
        db_session.commit()
        
        metrics = sla_service.calculate_metrics(
            db_session, monitor.id, start_time, end_time, 
            percentiles=[50, 90, 95, 99]
        )
        
        assert "p50" in metrics.percentile_response_times
        assert "p90" in metrics.percentile_response_times
        assert "p95" in metrics.percentile_response_times
        assert "p99" in metrics.percentile_response_times
        
        assert metrics.percentile_response_times["p50"] is not None
        assert metrics.percentile_response_times["p90"] >= metrics.percentile_response_times["p50"]
        assert metrics.percentile_response_times["p95"] >= metrics.percentile_response_times["p90"]
        assert metrics.percentile_response_times["p99"] >= metrics.percentile_response_times["p95"]
    
    def test_failed_checks_excluded_from_response_times(self, db_session: Session, monitor: Monitor, sla_service: SLAAnalyticsService):
        """Test that failed checks don't affect response time calculations"""
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 1, 1, 12, 0, 0)
        
        for i in range(5):
            check = MonitorCheck(
                monitor_id=monitor.id,
                checked_at=start_time + timedelta(hours=i),
                response_time_ms=100.0,
                status_code=200,
                is_up=True
            )
            db_session.add(check)
        
        for i in range(5, 10):
            check = MonitorCheck(
                monitor_id=monitor.id,
                checked_at=start_time + timedelta(hours=i),
                response_time_ms=None,
                status_code=500,
                is_up=False
            )
            db_session.add(check)
        
        db_session.commit()
        
        metrics = sla_service.calculate_metrics(db_session, monitor.id, start_time, end_time)
        
        assert metrics.mean_response_time_ms == 100.0
        assert metrics.failure_count == 5


class TestBucketedMetrics:
    """Test bucketing by day/week/month"""
    
    def test_daily_buckets(self, db_session: Session, monitor: Monitor, sla_service: SLAAnalyticsService):
        """Test daily bucketing of metrics"""
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 1, 4, 0, 0, 0)
        
        for day in range(3):
            for hour in range(24):
                check = MonitorCheck(
                    monitor_id=monitor.id,
                    checked_at=start_time + timedelta(days=day, hours=hour, minutes=30),
                    response_time_ms=100.0,
                    status_code=200,
                    is_up=True
                )
                db_session.add(check)
        
        db_session.commit()
        
        metrics_list = sla_service.get_bucketed_metrics(
            db_session, monitor.id, start_time, end_time, "day"
        )
        
        assert len(metrics_list) == 3
        
        for metrics in metrics_list:
            assert metrics.availability_percent == 100.0
            assert metrics.total_checks == 24
    
    def test_weekly_buckets(self, db_session: Session, monitor: Monitor, sla_service: SLAAnalyticsService):
        """Test weekly bucketing of metrics"""
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 1, 29, 0, 0, 0)
        
        for day in range(28):
            check = MonitorCheck(
                monitor_id=monitor.id,
                checked_at=start_time + timedelta(days=day),
                response_time_ms=100.0,
                status_code=200,
                is_up=True
            )
            db_session.add(check)
        
        db_session.commit()
        
        metrics_list = sla_service.get_bucketed_metrics(
            db_session, monitor.id, start_time, end_time, "week"
        )
        
        assert len(metrics_list) >= 4
    
    def test_monthly_buckets(self, db_session: Session, monitor: Monitor, sla_service: SLAAnalyticsService):
        """Test monthly bucketing of metrics"""
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 4, 1, 0, 0, 0)
        
        for month in range(1, 4):
            for day in range(1, 11):
                check = MonitorCheck(
                    monitor_id=monitor.id,
                    checked_at=datetime(2024, month, day),
                    response_time_ms=100.0,
                    status_code=200,
                    is_up=True
                )
                db_session.add(check)
        
        db_session.commit()
        
        metrics_list = sla_service.get_bucketed_metrics(
            db_session, monitor.id, start_time, end_time, "month"
        )
        
        assert len(metrics_list) == 3
        
        for metrics in metrics_list:
            assert metrics.availability_percent == 100.0


class TestTimeSeriesGeneration:
    """Test chart-friendly time series data generation"""
    
    def test_availability_time_series(self, db_session: Session, monitor: Monitor, sla_service: SLAAnalyticsService):
        """Test availability time series generation"""
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 1, 4, 0, 0, 0)
        
        for day in range(3):
            for hour in range(24):
                check = MonitorCheck(
                    monitor_id=monitor.id,
                    checked_at=start_time + timedelta(days=day, hours=hour),
                    response_time_ms=100.0,
                    status_code=200,
                    is_up=True
                )
                db_session.add(check)
        
        db_session.commit()
        
        time_series = sla_service.get_availability_time_series(
            db_session, monitor.id, start_time, end_time, "day"
        )
        
        assert len(time_series) == 3
        
        for point in time_series:
            assert hasattr(point, "timestamp")
            assert hasattr(point, "value")
            assert hasattr(point, "label")
            assert point.value == 100.0
            assert "2024-01" in point.label
    
    def test_response_time_time_series(self, db_session: Session, monitor: Monitor, sla_service: SLAAnalyticsService):
        """Test response time time series generation"""
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 1, 4, 0, 0, 0)
        
        for day in range(3):
            for hour in range(24):
                check = MonitorCheck(
                    monitor_id=monitor.id,
                    checked_at=start_time + timedelta(days=day, hours=hour),
                    response_time_ms=100.0 + day * 10,
                    status_code=200,
                    is_up=True
                )
                db_session.add(check)
        
        db_session.commit()
        
        time_series = sla_service.get_response_time_time_series(
            db_session, monitor.id, start_time, end_time, "day", "mean"
        )
        
        assert len(time_series) == 3
        assert abs(time_series[0].value - 100.0) < 1.0
        assert abs(time_series[1].value - 110.0) < 1.0
        assert abs(time_series[2].value - 120.0) < 1.0


class TestCacheBehavior:
    """Test caching functionality"""
    
    def test_cache_hit(self, db_session: Session, monitor: Monitor):
        """Test that repeated queries use cache"""
        sla_service = SLAAnalyticsService(enable_cache=True, cache_ttl_seconds=300)
        
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 1, 2, 0, 0, 0)
        
        check = MonitorCheck(
            monitor_id=monitor.id,
            checked_at=start_time + timedelta(hours=1),
            response_time_ms=100.0,
            status_code=200,
            is_up=True
        )
        db_session.add(check)
        db_session.commit()
        
        metrics1 = sla_service.calculate_metrics(db_session, monitor.id, start_time, end_time)
        
        check2 = MonitorCheck(
            monitor_id=monitor.id,
            checked_at=start_time + timedelta(hours=2),
            response_time_ms=200.0,
            status_code=200,
            is_up=True
        )
        db_session.add(check2)
        db_session.commit()
        
        metrics2 = sla_service.calculate_metrics(db_session, monitor.id, start_time, end_time)
        
        assert metrics1.total_checks == metrics2.total_checks
    
    def test_cache_disabled(self, db_session: Session, monitor: Monitor):
        """Test that cache can be disabled"""
        sla_service = SLAAnalyticsService(enable_cache=False)
        
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 1, 2, 0, 0, 0)
        
        check = MonitorCheck(
            monitor_id=monitor.id,
            checked_at=start_time + timedelta(hours=1),
            response_time_ms=100.0,
            status_code=200,
            is_up=True
        )
        db_session.add(check)
        db_session.commit()
        
        metrics1 = sla_service.calculate_metrics(db_session, monitor.id, start_time, end_time)
        
        check2 = MonitorCheck(
            monitor_id=monitor.id,
            checked_at=start_time + timedelta(hours=2),
            response_time_ms=200.0,
            status_code=200,
            is_up=True
        )
        db_session.add(check2)
        db_session.commit()
        
        metrics2 = sla_service.calculate_metrics(db_session, monitor.id, start_time, end_time)
        
        assert metrics2.total_checks == metrics1.total_checks + 1
    
    def test_clear_cache(self, db_session: Session, monitor: Monitor):
        """Test cache clearing"""
        sla_service = SLAAnalyticsService(enable_cache=True, cache_ttl_seconds=300)
        
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 1, 2, 0, 0, 0)
        
        check = MonitorCheck(
            monitor_id=monitor.id,
            checked_at=start_time + timedelta(hours=1),
            response_time_ms=100.0,
            status_code=200,
            is_up=True
        )
        db_session.add(check)
        db_session.commit()
        
        metrics1 = sla_service.calculate_metrics(db_session, monitor.id, start_time, end_time)
        
        sla_service.clear_cache()
        
        check2 = MonitorCheck(
            monitor_id=monitor.id,
            checked_at=start_time + timedelta(hours=2),
            response_time_ms=200.0,
            status_code=200,
            is_up=True
        )
        db_session.add(check2)
        db_session.commit()
        
        metrics2 = sla_service.calculate_metrics(db_session, monitor.id, start_time, end_time)
        
        assert metrics2.total_checks == metrics1.total_checks + 1


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_zero_duration_query(self, db_session: Session, monitor: Monitor, sla_service: SLAAnalyticsService):
        """Test query with zero duration"""
        start_time = datetime(2024, 1, 1, 12, 0, 0)
        end_time = datetime(2024, 1, 1, 12, 0, 0)
        
        metrics = sla_service.calculate_metrics(db_session, monitor.id, start_time, end_time)
        
        assert metrics.availability_percent == 100.0
    
    def test_overlapping_downtime_windows(self, db_session: Session, monitor: Monitor, sla_service: SLAAnalyticsService):
        """Test handling of overlapping downtime windows (should sum correctly)"""
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 1, 2, 0, 0, 0)
        
        downtime1 = DowntimeWindow(
            monitor_id=monitor.id,
            started_at=datetime(2024, 1, 1, 10, 0, 0),
            ended_at=datetime(2024, 1, 1, 14, 0, 0),
            failure_count=4
        )
        downtime2 = DowntimeWindow(
            monitor_id=monitor.id,
            started_at=datetime(2024, 1, 1, 12, 0, 0),
            ended_at=datetime(2024, 1, 1, 16, 0, 0),
            failure_count=4
        )
        
        db_session.add_all([downtime1, downtime2])
        db_session.commit()
        
        metrics = sla_service.calculate_metrics(db_session, monitor.id, start_time, end_time)
        
        assert metrics.total_downtime_seconds == (4 + 4) * 3600
    
    def test_very_large_response_times(self, db_session: Session, monitor: Monitor, sla_service: SLAAnalyticsService):
        """Test handling of very large response times"""
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 1, 1, 12, 0, 0)
        
        check = MonitorCheck(
            monitor_id=monitor.id,
            checked_at=start_time + timedelta(hours=1),
            response_time_ms=999999.99,
            status_code=200,
            is_up=True
        )
        db_session.add(check)
        db_session.commit()
        
        metrics = sla_service.calculate_metrics(db_session, monitor.id, start_time, end_time)
        
        assert metrics.mean_response_time_ms == 999999.99
