# Website Monitoring & Scheduler

This document describes the website monitoring and scheduler functionality implemented in the Project1 API.

## Overview

The application uses APScheduler (AsyncIOScheduler) to perform recurring health checks on configured websites. Each check measures response time, HTTP status, and availability, persisting results to the database and tracking downtime periods.

## Features

### 1. Website Management
- **CRUD Operations**: Create, read, update, and delete websites via REST API
- **Configurable Intervals**: Each website can have its own check interval (60-3600 seconds)
- **Enable/Disable**: Toggle monitoring per website without deletion
- **Dynamic Job Management**: Jobs automatically added/removed when websites enabled/disabled

### 2. Monitoring Service
- **HTTP Checks**: Uses `httpx.AsyncClient` with timeout and retry handling
- **Metrics Collected**:
  - Response time (seconds)
  - HTTP status code
  - Availability (boolean based on 2xx-3xx status codes)
  - Error messages (for failures)
- **State Tracking**: Opens/closes downtime windows on state transitions

### 3. Scheduler
- **APScheduler Integration**: AsyncIOScheduler for non-blocking job execution
- **Automatic Sync**: Syncs jobs with database on startup
- **Circuit Breaker**: Prevents repeated failures from overwhelming the system
  - Default: 5 failures trigger circuit breaker
  - 5-minute timeout before retry
- **Structured Logging**: Comprehensive logs for job execution, failures, and state changes

### 4. Downtime Tracking
- **Automatic Window Creation**: Opens when website becomes unavailable
- **Automatic Window Closure**: Closes when website recovers
- **Duration Calculation**: Tracks exact downtime periods
- **No Duplicates**: Single open window per website at any time

## API Endpoints

### List Websites
```http
GET /api/websites
```

**Response:**
```json
[
  {
    "id": 1,
    "url": "https://example.com",
    "name": "Example Site",
    "enabled": true,
    "check_interval": 300,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

### Create Website
```http
POST /api/websites
Content-Type: application/json

{
  "url": "https://example.com",
  "name": "Example Site",
  "enabled": true,
  "check_interval": 300
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "url": "https://example.com",
  "name": "Example Site",
  "enabled": true,
  "check_interval": 300,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Get Website
```http
GET /api/websites/{id}
```

### Update Website
```http
PATCH /api/websites/{id}
Content-Type: application/json

{
  "name": "Updated Name",
  "enabled": false,
  "check_interval": 600
}
```

**Note:** Changing `enabled` or `check_interval` automatically updates scheduler jobs.

### Delete Website
```http
DELETE /api/websites/{id}
```

**Response:** `204 No Content`

## Configuration

### Environment Variables

Add to `.env` file:

```env
# Enable/disable scheduler
SCHEDULER_ENABLED=true

# Scheduler timezone (default: UTC)
SCHEDULER_TIMEZONE=UTC
```

### Website Configuration

When creating a website:
- **url**: Must start with `http://` or `https://`
- **name**: Display name for the website
- **enabled**: Whether monitoring is active (default: `true`)
- **check_interval**: Seconds between checks, range: 60-3600 (default: 300)

## Database Schema

### websites
- `id`: Primary key
- `url`: Unique website URL
- `name`: Display name
- `enabled`: Monitoring status
- `check_interval`: Check frequency in seconds
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### monitor_checks
- `id`: Primary key
- `website_id`: Foreign key to websites
- `timestamp`: Check execution time
- `status_code`: HTTP status code (null if failed to connect)
- `response_time`: Request duration in seconds
- `is_available`: Boolean availability status
- `error_message`: Error description (if any)

### downtime_windows
- `id`: Primary key
- `website_id`: Foreign key to websites
- `start_time`: Downtime start timestamp
- `end_time`: Downtime end timestamp (null if still down)
- `created_at`: Record creation timestamp

## Architecture

### Monitoring Flow

1. **Scheduler** triggers job at configured interval
2. **Circuit Breaker** checks if website is blocked due to repeated failures
3. **Monitoring Service** performs HTTP request with timeout/retry
4. **Result Persistence** saves MonitorCheck record to database
5. **State Management** opens/closes DowntimeWindow if availability changed

### Circuit Breaker

The circuit breaker prevents overwhelming failing websites:

- Tracks failure count per website
- Opens circuit after 5 consecutive failures
- Blocks checks for 5 minutes
- Automatically closes and retries after timeout
- Resets on successful check

### Dynamic Job Management

Jobs are automatically managed:

- **On Startup**: All enabled websites scheduled
- **On Create**: New enabled website immediately scheduled
- **On Update**:
  - Enable → Job added
  - Disable → Job removed
  - Interval change → Job recreated with new interval
- **On Delete**: Job removed

## Logging

The system uses structured logging:

- **DEBUG**: Job execution details, circuit breaker state
- **INFO**: Successful checks, downtime window closures, job sync events
- **WARNING**: Timeouts, connection errors, downtime window openings
- **ERROR**: Unexpected errors, persistence failures

Example log output:
```
INFO:app.services.monitoring:Check completed for https://example.com: status=200, time=0.123s, available=True
WARNING:app.services.monitoring:Downtime window opened for Example Site at 2024-01-01T00:00:00Z
INFO:app.services.monitoring:Downtime window closed for Example Site. Duration: 120.5s
WARNING:app.services.scheduler:Circuit breaker opened for website 1. Blocked for 300s after 5 failures.
```

## Testing

Comprehensive test suite includes:

- **Unit Tests**:
  - Circuit breaker logic
  - Monitoring service HTTP checks
  - Downtime window management
  - Scheduler job lifecycle

- **Integration Tests**:
  - API endpoint functionality
  - Database persistence
  - Dynamic job management
  - State transitions

Run tests:
```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

Run with coverage:
```bash
pytest tests/ --cov=app --cov-report=term-missing
```

## Error Handling

### HTTP Request Failures

- **Timeout**: Recorded with error message, marked unavailable
- **Connection Error**: DNS/network failures, marked unavailable
- **HTTP Errors**: 4xx/5xx status codes, marked unavailable
- **Unexpected Errors**: Logged with full traceback, job continues

### Persistence Failures

- **Database Errors**: Logged and rolled back, circuit breaker records failure
- **Constraint Violations**: Handled at API level (e.g., duplicate URLs)

### Scheduler Failures

- **Job Errors**: Logged via APScheduler event listener
- **Website Not Found**: Job automatically removed
- **Disabled Website**: Job automatically removed

## Performance Considerations

- **Async I/O**: Non-blocking HTTP requests and database operations
- **Connection Pooling**: SQLAlchemy manages database connections
- **Retry Logic**: Built into httpx transport (default: 3 retries)
- **Timeout**: Default 30-second timeout per request
- **Circuit Breaker**: Prevents resource exhaustion from repeated failures

## Best Practices

1. **Check Intervals**: Balance between responsiveness and server load
   - High-priority sites: 60-120 seconds
   - Normal sites: 300-600 seconds (5-10 minutes)
   - Low-priority: 900-3600 seconds (15-60 minutes)

2. **Monitoring Multiple Sites**: Consider total request load
   - Example: 100 sites × 5-minute intervals = ~0.33 requests/second

3. **Database Maintenance**: Consider archiving old MonitorCheck records
   - Retention policy based on business needs
   - Aggregate older data for historical analysis

4. **Circuit Breaker**: Tune thresholds based on your needs
   - Adjust failure_threshold in `services/scheduler.py`
   - Adjust timeout duration

## Troubleshooting

### Jobs Not Running

1. Check `SCHEDULER_ENABLED=true` in `.env`
2. Verify websites are enabled: `GET /api/websites`
3. Check logs for errors: Look for "Starting APScheduler" message
4. Verify database connection

### High Failure Rate

1. Check network connectivity from server
2. Verify website URLs are correct and accessible
3. Review timeout settings (may need to increase)
4. Check if circuit breaker is blocking checks

### Database Growing Too Fast

1. Implement data retention policy
2. Archive old MonitorCheck records
3. Aggregate data into summary tables
4. Consider separate database for monitoring data

## Future Enhancements

Potential improvements:

- [ ] Alert notifications (email, Slack, etc.)
- [ ] Status dashboard/UI
- [ ] Multi-region checks
- [ ] Custom HTTP headers per website
- [ ] POST/PUT endpoint checks
- [ ] SSL certificate expiration monitoring
- [ ] Response content validation
- [ ] Scheduled maintenance windows
- [ ] SLA reporting
- [ ] API for retrieving check history and downtime statistics
