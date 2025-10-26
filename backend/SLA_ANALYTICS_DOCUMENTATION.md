# SLA Analytics Service Documentation

## Overview

The SLA Analytics Service provides comprehensive monitoring analytics capabilities, computing availability metrics, response times, failure counts, and downtime durations over arbitrary time ranges using SQL aggregation.

## Features

- **Availability Percentage**: Calculate uptime percentage over any time range
- **Response Time Metrics**: Mean and percentile (p50, p75, p90, p95, p99) response times
- **Failure Tracking**: Count and analyze failed checks
- **Downtime Analysis**: Calculate total downtime duration including ongoing outages
- **Time Bucketing**: Aggregate metrics by day, week, or month
- **Chart-Friendly Output**: Generate time series data ready for visualization
- **Caching**: Optional in-memory or Redis caching for performance optimization

## Architecture

### Models

#### Monitor
Base entity representing a monitored endpoint.
- `id`: Unique identifier
- `name`: Monitor name
- `url`: Endpoint URL
- `check_interval_seconds`: Check frequency

#### MonitorCheck
Individual check result for a monitor.
- `id`: Unique identifier
- `monitor_id`: Reference to monitor
- `checked_at`: Timestamp of check (indexed)
- `response_time_ms`: Response time in milliseconds (nullable for failed checks)
- `status_code`: HTTP status code
- `is_up`: Boolean indicating success/failure
- `error_message`: Error details if check failed

#### DowntimeWindow
Period of continuous downtime for a monitor.
- `id`: Unique identifier
- `monitor_id`: Reference to monitor
- `started_at`: Downtime start timestamp (indexed)
- `ended_at`: Downtime end timestamp (nullable for ongoing outages)
- `failure_count`: Number of failed checks during this window

### Service Class: SLAAnalyticsService

The main service class providing all analytics functionality.

## Calculation Formulas

### Availability Percentage

```
availability_percent = ((total_time - total_downtime) / total_time) × 100
```

Where:
- `total_time` = `end_time - start_time` (in seconds)
- `total_downtime` = sum of all downtime window durations within the time range

**Example:**
- Time range: 24 hours (86,400 seconds)
- Downtime: 2 hours (7,200 seconds)
- Availability: ((86,400 - 7,200) / 86,400) × 100 = 91.67%

### Mean Response Time

```
mean_response_time = sum(response_times) / count(successful_checks)
```

Only includes:
- Successful checks (`is_up = True`)
- Non-null response times

**Example:**
- Response times: [100ms, 150ms, 200ms, 250ms, 300ms]
- Mean: (100 + 150 + 200 + 250 + 300) / 5 = 200ms

### Percentile Response Time

```
percentile_p = value at position (p/100) × N in sorted response times
```

Where:
- `p` = percentile (e.g., 95 for p95)
- `N` = count of response times
- Response times are sorted in ascending order

**Example (p95):**
- 100 response times sorted: [50ms, 52ms, ..., 980ms, 1000ms]
- p95 position: (95/100) × 100 = 95
- p95 value: 95th value in sorted list

### Downtime Duration

```
downtime_seconds = sum(min(window.ended_at or query.end_time, query.end_time) 
                      - max(window.started_at, query.start_time))
```

For each downtime window:
1. Use `window.ended_at` if set, otherwise use query `end_time` (for ongoing outages)
2. Clip window to query time range using `max(started_at, query.start_time)` and `min(ended_at, query.end_time)`
3. Sum all window durations

**Example:**
```
Query range: 2024-01-01 00:00 to 2024-01-02 00:00

Window 1: 2023-12-31 22:00 to 2024-01-01 02:00
  → Clipped: 2024-01-01 00:00 to 2024-01-01 02:00 = 2 hours

Window 2: 2024-01-01 10:00 to 2024-01-01 12:00
  → Within range: 2 hours

Window 3: 2024-01-01 20:00 to NULL (ongoing)
  → Clipped: 2024-01-01 20:00 to 2024-01-02 00:00 = 4 hours

Total downtime: 2 + 2 + 4 = 8 hours
```

## Key Assumptions

### 1. Missing Checks Are NOT Treated as Downtime

If there are no checks in a time period, availability is still 100% unless explicit downtime windows exist.

**Rationale**: This prevents penalizing metrics due to monitoring system issues rather than actual service outages.

**Alternative approach** (not implemented): Treat gaps larger than `check_interval_seconds` as potential downtime.

### 2. Availability is Based on Downtime Windows, Not Check Success Rate

Availability is calculated from explicit `DowntimeWindow` records, not by counting failed checks.

**Rationale**: Provides more accurate SLA metrics. A single brief outage with multiple rapid checks shouldn't be weighted more heavily than a longer outage with fewer checks.

**Alternative approach** (not implemented): Calculate as `(successful_checks / total_checks) × 100`.

### 3. Response Times Only Include Successful Checks

Failed checks are excluded from response time calculations.

**Rationale**: Response time is a performance metric for successful operations. Timeouts and errors have different meaning.

### 4. Ongoing Downtime Windows Count Until Query End Time

If `ended_at` is `NULL`, the window is treated as ongoing and counted up to the query `end_time`.

**Rationale**: Provides accurate current state for active incidents.

### 5. Bucket Boundaries Align to Natural Periods

- **Day**: Midnight to midnight (UTC)
- **Week**: Monday to Sunday (ISO week)
- **Month**: First day to last day of calendar month

**Rationale**: Intuitive for users and aligns with standard reporting periods.

## Usage Examples

### Basic Metrics Calculation

```python
from datetime import datetime, timedelta
from app.services import SLAAnalyticsService
from app.core.database import get_db

# Initialize service
sla_service = SLAAnalyticsService(
    enable_cache=True,
    cache_ttl_seconds=300  # 5 minutes
)

# Get database session
db = next(get_db())

# Define time range
end_time = datetime.utcnow()
start_time = end_time - timedelta(days=30)

# Calculate metrics
metrics = sla_service.calculate_metrics(
    db=db,
    monitor_id=1,
    start_time=start_time,
    end_time=end_time,
    percentiles=[50, 90, 95, 99]
)

# Access results
print(f"Availability: {metrics.availability_percent:.2f}%")
print(f"Mean Response Time: {metrics.mean_response_time_ms:.2f}ms")
print(f"P95 Response Time: {metrics.percentile_response_times['p95']:.2f}ms")
print(f"Total Downtime: {metrics.total_downtime_seconds / 3600:.2f} hours")
print(f"Failure Count: {metrics.failure_count}")
```

### Bucketed Metrics (Daily)

```python
# Get daily metrics for last 30 days
metrics_list = sla_service.get_bucketed_metrics(
    db=db,
    monitor_id=1,
    start_time=start_time,
    end_time=end_time,
    bucket_type="day",
    percentiles=[95, 99]
)

# Process each day
for daily_metrics in metrics_list:
    print(f"Date: {daily_metrics.start_time.date()}")
    print(f"  Availability: {daily_metrics.availability_percent:.2f}%")
    print(f"  Checks: {daily_metrics.total_checks}")
```

### Time Series for Charts

```python
# Get availability time series
availability_series = sla_service.get_availability_time_series(
    db=db,
    monitor_id=1,
    start_time=start_time,
    end_time=end_time,
    bucket_type="day"
)

# Convert to chart data
chart_data = {
    "labels": [point.label for point in availability_series],
    "values": [point.value for point in availability_series]
}

# Get response time time series (p95)
response_time_series = sla_service.get_response_time_time_series(
    db=db,
    monitor_id=1,
    start_time=start_time,
    end_time=end_time,
    bucket_type="day",
    metric="p95"
)
```

### Using Redis Cache

```python
import redis

# Configure Redis
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True
)

sla_service = SLAAnalyticsService(enable_cache=True)
sla_service.set_redis_client(redis_client)

# Now queries will use Redis for distributed caching
metrics = sla_service.calculate_metrics(db, monitor_id=1, start_time, end_time)
```

### Clearing Cache

```python
# Clear all cached metrics
sla_service.clear_cache()
```

## API Integration Example

Here's how to expose these metrics via FastAPI:

```python
from fastapi import APIRouter, Depends, Query
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.services import SLAAnalyticsService
from app.schemas.sla import SLAMetricsResponse

router = APIRouter(prefix="/api/sla", tags=["SLA Analytics"])
sla_service = SLAAnalyticsService(enable_cache=True)

@router.get("/metrics/{monitor_id}")
def get_sla_metrics(
    monitor_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)
    
    metrics = sla_service.calculate_metrics(
        db, monitor_id, start_time, end_time
    )
    
    return {
        "monitor_id": monitor_id,
        "period_days": days,
        "availability_percent": metrics.availability_percent,
        "mean_response_time_ms": metrics.mean_response_time_ms,
        "percentiles": metrics.percentile_response_times,
        "failure_count": metrics.failure_count,
        "total_downtime_hours": metrics.total_downtime_seconds / 3600,
        "total_checks": metrics.total_checks
    }

@router.get("/timeseries/{monitor_id}/availability")
def get_availability_timeseries(
    monitor_id: int,
    days: int = Query(30, ge=1, le=365),
    bucket: str = Query("day", regex="^(day|week|month)$"),
    db: Session = Depends(get_db)
):
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)
    
    series = sla_service.get_availability_time_series(
        db, monitor_id, start_time, end_time, bucket
    )
    
    return {
        "monitor_id": monitor_id,
        "metric": "availability",
        "bucket": bucket,
        "data": [
            {
                "timestamp": point.timestamp.isoformat(),
                "label": point.label,
                "value": point.value
            }
            for point in series
        ]
    }
```

## Performance Considerations

### Database Indexes

Ensure these indexes exist for optimal performance:

```sql
-- MonitorCheck indexes
CREATE INDEX ix_monitor_checks_monitor_checked 
  ON monitor_checks (monitor_id, checked_at);

-- DowntimeWindow indexes
CREATE INDEX ix_downtime_windows_monitor_started 
  ON downtime_windows (monitor_id, started_at);
```

### Caching Strategy

1. **Cache TTL**: Default 300 seconds (5 minutes)
   - Adjustable based on freshness requirements
   - Shorter TTL for real-time dashboards
   - Longer TTL for historical reports

2. **Cache Keys**: Include all query parameters
   - `sla:{monitor_id}:{start_time}:{end_time}:{bucket_type}`
   - Ensures different queries don't collide

3. **Cache Invalidation**: 
   - Manual via `clear_cache()`
   - TTL-based expiration
   - Consider invalidating on new downtime windows

### Query Optimization

For large datasets:
- Use bucketing to reduce data points
- Limit time ranges for detailed queries
- Consider pre-aggregation for common queries
- Use database read replicas for analytics

## Testing

Comprehensive test suite covers:

- ✅ Continuous uptime scenarios
- ✅ Intermittent outages
- ✅ Missing data handling
- ✅ Response time calculations (mean and percentiles)
- ✅ Downtime calculations (ongoing and completed)
- ✅ Bucketed metrics (day/week/month)
- ✅ Time series generation
- ✅ Cache behavior
- ✅ Edge cases (zero duration, overlapping windows, etc.)

Run tests:
```bash
cd backend
pytest tests/test_sla_analytics.py -v
```

## Future Enhancements

### Potential Improvements

1. **Alternative Availability Calculation**
   ```python
   # Option to calculate from check success rate
   availability = (successful_checks / total_checks) × 100
   ```

2. **Missing Data Handling Options**
   ```python
   # Treat gaps as downtime
   if gap > check_interval_seconds * threshold:
       treat_as_downtime = True
   ```

3. **Weighted Metrics**
   ```python
   # Weight by check importance or time of day
   weighted_availability = sum(weight * uptime) / sum(weight)
   ```

4. **SLA Compliance**
   ```python
   # Check against SLA targets
   sla_target = 99.9
   sla_met = availability_percent >= sla_target
   sla_credit = calculate_credit_if_breach(availability_percent, sla_target)
   ```

5. **Anomaly Detection**
   ```python
   # Detect unusual patterns
   if response_time > mean + (3 * std_dev):
       flag_as_anomaly()
   ```

## Troubleshooting

### Common Issues

**Issue**: Metrics show 0% availability despite successful checks

**Solution**: Ensure `DowntimeWindow` records are created only for actual outages. Check that ended_at is set when incidents resolve.

---

**Issue**: Response times seem incorrect

**Solution**: Verify that `response_time_ms` is set only for successful checks (`is_up=True`). Failed checks should have `NULL` response times.

---

**Issue**: Cache returns stale data

**Solution**: Call `clear_cache()` after significant data changes or reduce `cache_ttl_seconds`.

---

**Issue**: Queries are slow for large time ranges

**Solution**: 
- Verify database indexes exist
- Use bucketing to reduce granularity
- Enable caching
- Consider read replicas

## License

Part of Project1 backend application.
