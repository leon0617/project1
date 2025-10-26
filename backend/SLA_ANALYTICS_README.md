# SLA Analytics Service

## Quick Start

This service provides comprehensive SLA (Service Level Agreement) analytics for monitoring systems, calculating availability percentages, response times, and downtime metrics.

### Basic Usage

```python
from datetime import datetime, timedelta
from app.services import SLAAnalyticsService
from app.core.database import get_db

# Initialize service
service = SLAAnalyticsService(enable_cache=True, cache_ttl_seconds=300)

# Get database session
db = next(get_db())

# Calculate metrics for last 30 days
end_time = datetime.utcnow()
start_time = end_time - timedelta(days=30)

metrics = service.calculate_metrics(
    db=db,
    monitor_id=1,
    start_time=start_time,
    end_time=end_time
)

print(f"Availability: {metrics.availability_percent:.2f}%")
print(f"Mean Response Time: {metrics.mean_response_time_ms:.2f}ms")
print(f"P95 Response Time: {metrics.percentile_response_times['p95']:.2f}ms")
print(f"Total Downtime: {metrics.total_downtime_seconds / 3600:.2f} hours")
```

## Features

✅ **Availability Calculation** - Accurate uptime percentage based on downtime windows  
✅ **Response Time Analytics** - Mean and percentile (p50, p75, p90, p95, p99) metrics  
✅ **Downtime Tracking** - Total downtime duration with ongoing incident support  
✅ **Failure Counting** - Track failed checks over time  
✅ **Time Bucketing** - Aggregate by day, week, or month  
✅ **Chart-Ready Data** - Time series output for visualization  
✅ **Caching** - In-memory or Redis caching for performance  

## Database Models

### Monitor
Represents a monitored endpoint with configuration for check intervals.

### MonitorCheck
Individual check results including:
- Timestamp
- Response time (ms)
- Status code
- Success/failure flag
- Error message (if failed)

### DowntimeWindow
Continuous downtime periods with:
- Start timestamp
- End timestamp (NULL for ongoing)
- Failure count

## Key Metrics

### Availability Percentage
```
availability % = ((total_time - downtime) / total_time) × 100
```

### Response Times
- **Mean**: Average of all successful check response times
- **Percentiles**: p50, p75, p90, p95, p99 from sorted response times

### Downtime Duration
Total seconds in downtime state, properly clipped to query time range.

## Time Bucketing

Get metrics grouped by time periods:

```python
# Daily metrics
daily_metrics = service.get_bucketed_metrics(
    db, monitor_id=1, 
    start_time=start_time, 
    end_time=end_time, 
    bucket_type="day"
)

# Weekly metrics
weekly_metrics = service.get_bucketed_metrics(
    db, monitor_id=1,
    start_time=start_time,
    end_time=end_time,
    bucket_type="week"
)

# Monthly metrics  
monthly_metrics = service.get_bucketed_metrics(
    db, monitor_id=1,
    start_time=start_time,
    end_time=end_time,
    bucket_type="month"
)
```

## Time Series for Charts

Generate chart-friendly data:

```python
# Availability over time
availability_series = service.get_availability_time_series(
    db, monitor_id=1,
    start_time=start_time,
    end_time=end_time,
    bucket_type="day"
)

# Convert to chart data
labels = [point.label for point in availability_series]
values = [point.value for point in availability_series]

# Response time over time (p95)
response_time_series = service.get_response_time_time_series(
    db, monitor_id=1,
    start_time=start_time,
    end_time=end_time,
    bucket_type="day",
    metric="p95"  # or "mean", "p50", "p90", etc.
)
```

## Caching

### In-Memory Cache (Default)
```python
service = SLAAnalyticsService(enable_cache=True, cache_ttl_seconds=300)
```

### Redis Cache
```python
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
service = SLAAnalyticsService(enable_cache=True)
service.set_redis_client(redis_client)
```

### Cache Management
```python
# Clear all cached metrics
service.clear_cache()
```

## Important Assumptions

1. **Missing Checks ≠ Downtime**: Gaps in monitoring data are not treated as downtime
2. **Downtime Windows Define Availability**: Uses explicit downtime records, not check success rate
3. **Failed Checks Excluded from Response Times**: Only successful checks count toward response time metrics
4. **Ongoing Incidents Supported**: NULL `ended_at` means downtime continues to query end time

## Testing

Comprehensive test suite with 20+ test cases:

```bash
cd backend
pytest tests/test_sla_analytics.py -v
```

Test coverage includes:
- ✅ Continuous uptime scenarios
- ✅ Intermittent outages
- ✅ Missing data handling
- ✅ Response time calculations
- ✅ Downtime window edge cases
- ✅ Time bucketing (day/week/month)
- ✅ Time series generation
- ✅ Cache behavior
- ✅ Edge cases (zero duration, overlaps, etc.)

## Database Migration

Migration is included for the monitoring models:

```bash
cd backend
alembic upgrade head
```

This creates:
- `monitors` table
- `monitor_checks` table with indexes
- `downtime_windows` table with indexes

## Performance Tips

1. **Use Indexes**: Ensure database indexes on `monitor_id` and timestamp columns
2. **Enable Caching**: Reduce database load for repeated queries
3. **Bucket Large Ranges**: Use day/week/month bucketing instead of raw data for large time ranges
4. **Set Appropriate TTL**: Balance freshness vs performance based on use case

## API Integration Example

```python
from fastapi import APIRouter, Depends, Query
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/sla", tags=["SLA"])
sla_service = SLAAnalyticsService(enable_cache=True)

@router.get("/metrics/{monitor_id}")
def get_metrics(
    monitor_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)
    
    metrics = sla_service.calculate_metrics(db, monitor_id, start_time, end_time)
    
    return {
        "availability_percent": metrics.availability_percent,
        "mean_response_time_ms": metrics.mean_response_time_ms,
        "percentiles": metrics.percentile_response_times,
        "failure_count": metrics.failure_count,
        "total_downtime_hours": metrics.total_downtime_seconds / 3600
    }
```

## Documentation

For detailed documentation including formulas, assumptions, and troubleshooting, see:
- [SLA_ANALYTICS_DOCUMENTATION.md](./SLA_ANALYTICS_DOCUMENTATION.md)

## Example Output

```python
SLAMetrics(
    start_time=datetime(2024, 1, 1, 0, 0, 0),
    end_time=datetime(2024, 1, 31, 23, 59, 59),
    availability_percent=99.95,
    mean_response_time_ms=145.3,
    percentile_response_times={
        'p50': 120.0,
        'p75': 150.0,
        'p90': 200.0,
        'p95': 250.0,
        'p99': 400.0
    },
    failure_count=12,
    total_downtime_seconds=1296.0,  # ~21.6 minutes
    total_checks=43200,
    successful_checks=43188
)
```

## License

Part of Project1 backend application.
