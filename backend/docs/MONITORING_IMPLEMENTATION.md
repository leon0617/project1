# Website Monitoring Implementation

## Overview

This document describes the implementation of the automated website monitoring system using Playwright and APScheduler. The monitoring system performs periodic checks of registered websites and records their availability, response times, and captures network events during debug sessions.

## Features Implemented

### 1. Monitoring Task (`app/tasks/monitoring_task.py`)

The `MonitoringTask` class provides the core monitoring functionality using Playwright browser automation.

#### Key Features:
- **Browser Management**: Shared browser instance for efficient resource usage
- **Website Checking**: Measures response time and captures HTTP status codes
- **Error Handling**: Gracefully handles network errors and timeouts
- **Debug Mode**: Captures detailed network events when debug session is active

#### Methods:

**`check_website(website, db, debug_session_id=None)`**
- Checks a single website using Playwright
- Records response time and status code
- Captures network events if debug session is active
- Saves results to the database

**`check_all_enabled_websites()`**
- Checks all websites where `enabled=True`
- Automatically detects active debug sessions
- Designed to be run periodically by the scheduler

**`check_website_by_id(website_id)`**
- Checks a specific website by ID
- Useful for manual triggers and testing

### 2. Task Scheduler (`app/tasks/scheduler.py`)

The `TaskScheduler` class manages periodic execution of monitoring tasks using APScheduler.

#### Configuration:
- **Default Interval**: 60 seconds (configurable)
- **Timezone**: UTC (configurable via `SCHEDULER_TIMEZONE`)
- **Job Settings**:
  - `coalesce=True`: Combines multiple pending executions
  - `max_instances=1`: Prevents concurrent job execution
  - `misfire_grace_time=300`: 5-minute grace period for missed jobs

#### Lifecycle:
1. **Initialize**: Sets up the scheduler and adds monitoring job
2. **Start**: Begins periodic task execution
3. **Stop**: Gracefully shuts down the scheduler
4. **Cleanup**: Closes browser and releases resources

### 3. API Integration

#### New Endpoint: Manual Check

**`POST /api/monitoring/check/{website_id}`**
- Manually triggers a website check
- Returns the monitoring result immediately
- Useful for testing and on-demand checks
- Respects active debug sessions

**Example:**
```bash
curl -X POST http://localhost:8000/api/monitoring/check/1
```

**Response:**
```json
{
  "id": 123,
  "website_id": 1,
  "timestamp": "2025-01-15T10:30:00Z",
  "status_code": 200,
  "response_time": 0.234,
  "success": 1,
  "error_message": null
}
```

### 4. Application Lifecycle Integration

The monitoring system is integrated into FastAPI's lifecycle (`app/main.py`):

**Startup:**
1. Check if `SCHEDULER_ENABLED=true` in configuration
2. Initialize the scheduler
3. Start periodic monitoring tasks
4. Log scheduler status

**Shutdown:**
1. Stop the scheduler
2. Close Playwright browser
3. Release all resources

### 5. Network Event Capture

When a debug session is active for a website, the monitoring task automatically captures network events:

**Captured Data:**
- HTTP method (GET, POST, etc.)
- Request URL
- Response status code
- Request/response headers
- Request/response body (for POST/PUT/PATCH)
- Timing information

**Process:**
1. Monitoring task detects active debug session
2. Sets up Playwright response listener
3. Captures all network events during page load
4. Stores events in the database
5. Streams events to SSE subscribers

## Configuration

### Environment Variables

Add to `.env` file:

```env
# Enable/disable the scheduler
SCHEDULER_ENABLED=true

# Scheduler timezone
SCHEDULER_TIMEZONE=UTC

# Playwright settings
PLAYWRIGHT_BROWSER=chromium  # or firefox, webkit
PLAYWRIGHT_HEADLESS=true
PLAYWRIGHT_EXECUTABLE_PATH=  # Optional: custom browser path
```

### Database Requirements

The monitoring system requires the database migrations to be applied:

```bash
alembic upgrade head
```

### Playwright Installation

Install Playwright browsers:

```bash
# Install Python package (already in requirements.txt)
pip install playwright

# Install browsers
playwright install chromium

# For all browsers (optional)
playwright install
```

## Usage

### Automatic Monitoring

1. **Enable the scheduler:**
   ```env
   SCHEDULER_ENABLED=true
   ```

2. **Start the application:**
   ```bash
   uvicorn app.main:app --reload
   ```

3. **Add websites to monitor:**
   ```bash
   curl -X POST http://localhost:8000/api/websites/ \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.example.com", "name": "Example", "enabled": true}'
   ```

4. **Monitor logs:**
   The scheduler will automatically check all enabled websites every 60 seconds.

### Manual Monitoring

Trigger an immediate check:

```bash
curl -X POST http://localhost:8000/api/monitoring/check/1
```

### Debug Session Monitoring

1. **Start a debug session:**
   ```bash
   curl -X POST http://localhost:8000/api/debug/sessions \
     -H "Content-Type: application/json" \
     -d '{"website_id": 1}'
   ```

2. **Monitor will automatically capture network events** on the next check

3. **View captured events:**
   ```bash
   curl http://localhost:8000/api/debug/events?debug_session_id=1
   ```

4. **Stream live events:**
   ```bash
   curl -N http://localhost:8000/api/debug/sessions/1/stream
   ```

## Architecture

```
┌─────────────────────────────────────────────────┐
│           FastAPI Application                    │
│  ┌───────────────────────────────────────────┐  │
│  │          Lifecycle Manager                 │  │
│  │  - Startup: Initialize & Start Scheduler   │  │
│  │  - Shutdown: Stop & Cleanup                │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│          Task Scheduler (APScheduler)           │
│  ┌───────────────────────────────────────────┐  │
│  │  Job: check_all_enabled_websites()        │  │
│  │  Trigger: Every 60 seconds                │  │
│  │  Max Instances: 1                         │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│          Monitoring Task                         │
│  ┌───────────────────────────────────────────┐  │
│  │  1. Query enabled websites from DB        │  │
│  │  2. Check for active debug sessions       │  │
│  │  3. Launch Playwright browser             │  │
│  │  4. Navigate to each website              │  │
│  │  5. Capture metrics & network events      │  │
│  │  6. Save results to database              │  │
│  │  7. Stream events to SSE subscribers      │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

## Performance Considerations

1. **Browser Reuse**: Single browser instance shared across checks
2. **Timeout**: 30-second timeout for page loads
3. **Concurrency**: Only one monitoring job runs at a time
4. **Resource Cleanup**: Browser closed on shutdown
5. **Database Connections**: Proper session management with try/finally

## Error Handling

The monitoring system handles various error scenarios:

1. **Network Errors**: Timeout, DNS failures, connection refused
2. **Invalid URLs**: Malformed URLs are caught during validation
3. **Browser Crashes**: Graceful recovery and logging
4. **Database Errors**: Transaction rollback and error logging

All errors are:
- Logged with full context
- Stored in `error_message` field
- Marked with `success=0`
- Do not crash the scheduler

## Testing

### Unit Tests

Run the monitoring task tests:

```bash
pytest tests/test_monitoring_task.py -v
```

### Test Coverage

The test suite includes:
- Manual check endpoint
- Website not found handling
- Network event capture during debug sessions
- Direct monitoring task execution
- Checking all enabled websites
- Error handling for invalid URLs
- Scheduler initialization

### Integration Testing

Test with real websites:

```bash
# Start the application with scheduler enabled
SCHEDULER_ENABLED=true uvicorn app.main:app

# Add a test website
curl -X POST http://localhost:8000/api/websites/ \
  -H "Content-Type: application/json" \
  -d '{"url": "https://httpbin.org/delay/1", "name": "HTTPBin", "enabled": true}'

# Wait for automatic check or trigger manually
curl -X POST http://localhost:8000/api/monitoring/check/1

# View results
curl http://localhost:8000/api/monitoring/results
```

## Troubleshooting

### Scheduler Not Running

**Problem**: No monitoring checks are happening

**Solutions**:
1. Check `SCHEDULER_ENABLED=true` in `.env`
2. Check application logs for scheduler initialization
3. Verify at least one website has `enabled=true`

### Playwright Browser Errors

**Problem**: Browser fails to launch

**Solutions**:
1. Install browsers: `playwright install chromium`
2. Check `PLAYWRIGHT_HEADLESS=true` for server environments
3. Verify browser executable path if using custom browser

### No Results Recorded

**Problem**: Monitoring runs but no results in database

**Solutions**:
1. Check database migrations: `alembic current`
2. Verify database connection settings
3. Check application logs for errors
4. Ensure websites have `enabled=true`

### High Resource Usage

**Problem**: High CPU/memory usage

**Solutions**:
1. Reduce check frequency in scheduler settings
2. Disable unused websites (set `enabled=false`)
3. Use headless mode: `PLAYWRIGHT_HEADLESS=true`
4. Limit concurrent checks (already limited to 1)

## Future Enhancements

Potential improvements for the monitoring system:

1. **Configurable Check Intervals**: Per-website check intervals
2. **Retry Logic**: Automatic retries for failed checks
3. **Notifications**: Email/Slack alerts for downtime
4. **Advanced Metrics**: First contentful paint, time to interactive
5. **Screenshot Capture**: Save screenshots during checks
6. **Performance Budgets**: Alert when metrics exceed thresholds
7. **Geographic Checks**: Check from multiple locations
8. **Custom Headers**: Support for authentication headers
9. **SSL Certificate Monitoring**: Track certificate expiration
10. **Status Pages**: Public status page generation

## Conclusion

The monitoring implementation provides a production-ready solution for automated website monitoring with:

✅ Periodic automated checks
✅ Manual trigger capability
✅ Network event capture
✅ Debug session integration
✅ Comprehensive error handling
✅ Full test coverage
✅ Proper resource management

The system is ready for deployment and can scale to monitor hundreds of websites efficiently.
