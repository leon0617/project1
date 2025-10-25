# Monitoring Models Quick Reference

## Quick Start

### Import Required Components
```python
from sqlalchemy.orm import Session
from app.models.monitoring import Website, MonitorCheck, MonitorStatus, HTTPMethod
from app.schemas.monitoring import WebsiteCreate, MonitorCheckCreate
from app.services.monitoring_crud import WebsiteCRUD, MonitorCheckCRUD
```

### Database Session
```python
from app.core.database import get_db

# In FastAPI endpoint
def my_endpoint(db: Session = Depends(get_db)):
    # Use db here
    pass

# In tests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base

engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()
```

## Common Operations

### 1. Website Management

```python
# Create a website
website_data = WebsiteCreate(
    url="https://example.com",
    name="Example Site",
    check_interval=300,  # seconds
    timeout=30,
    is_active=True
)
website = WebsiteCRUD.create(db, website_data)

# Get website by ID
website = WebsiteCRUD.get_by_id(db, website_id=1)

# Get website by URL
website = WebsiteCRUD.get_by_url(db, url="https://example.com")

# Get all active websites
active_websites = WebsiteCRUD.get_active_websites(db)

# Update website
from app.schemas.monitoring import WebsiteUpdate
update_data = WebsiteUpdate(name="New Name", check_interval=600)
updated_website = WebsiteCRUD.update(db, website_id=1, website_update=update_data)

# Delete website (cascades to all related records)
success = WebsiteCRUD.delete(db, website_id=1)
```

### 2. Monitor Checks

```python
# Record a successful check
check_data = MonitorCheckCreate(
    website_id=1,
    status=MonitorStatus.UP,
    http_status_code=200,
    http_method=HTTPMethod.GET,
    response_time_ms=150.5,
    dns_time_ms=10.2,
    connect_time_ms=20.3,
    tls_time_ms=15.4,
    ttfb_ms=100.1
)
check = MonitorCheckCRUD.create(db, check_data)

# Record a failed check
check_data = MonitorCheckCreate(
    website_id=1,
    status=MonitorStatus.DOWN,
    error_message="Connection timeout"
)
check = MonitorCheckCRUD.create(db, check_data)

# Get checks for a website (paginated)
checks, total = MonitorCheckCRUD.get_by_website(
    db,
    website_id=1,
    skip=0,
    limit=50
)

# Get checks within date range
from datetime import datetime, timedelta
start_date = datetime.utcnow() - timedelta(days=7)
end_date = datetime.utcnow()
checks, total = MonitorCheckCRUD.get_by_website(
    db,
    website_id=1,
    start_date=start_date,
    end_date=end_date
)

# Get latest check
latest_check = MonitorCheckCRUD.get_latest_by_website(db, website_id=1)

# Calculate uptime percentage (last 24 hours)
uptime = MonitorCheckCRUD.calculate_uptime_percentage(
    db, website_id=1, hours=24
)
print(f"Uptime: {uptime}%")
```

### 3. Downtime Windows

```python
from app.schemas.monitoring import DowntimeWindowCreate, DowntimeWindowUpdate

# Start tracking downtime
downtime_data = DowntimeWindowCreate(
    website_id=1,
    started_at=datetime.utcnow(),
    initial_status=MonitorStatus.DOWN,
    notes="Server not responding"
)
downtime = DowntimeWindowCRUD.create(db, downtime_data)

# Check if website is currently down
ongoing_downtime = DowntimeWindowCRUD.get_ongoing_downtime(db, website_id=1)
if ongoing_downtime:
    print(f"Site has been down since {ongoing_downtime.started_at}")

# End downtime window
update_data = DowntimeWindowUpdate(
    ended_at=datetime.utcnow(),
    recovery_status=MonitorStatus.UP,
    affected_checks_count=10,
    root_cause="Database connection pool exhausted"
)
updated = DowntimeWindowCRUD.update(db, downtime.id, update_data)
print(f"Downtime duration: {updated.duration_seconds} seconds")

# Get downtime history
downtimes, total = DowntimeWindowCRUD.get_by_website(
    db,
    website_id=1,
    include_ongoing=True
)
```

### 4. Debug Sessions

```python
from app.schemas.monitoring import DebugSessionCreate, DebugSessionUpdate

# Start debug session
session_data = DebugSessionCreate(
    website_id=1,
    session_key="debug-2024-01-01-123456",
    user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    browser_type="chromium"
)
session = DebugSessionCRUD.create(db, session_data)

# Retrieve session by key
session = DebugSessionCRUD.get_by_session_key(db, "debug-2024-01-01-123456")

# Complete debug session
update_data = DebugSessionUpdate(
    completed_at=datetime.utcnow(),
    success=True
)
updated = DebugSessionCRUD.update(db, session.id, update_data)

# Get all debug sessions for a website
sessions, total = DebugSessionCRUD.get_by_website(db, website_id=1)
```

### 5. Network Events

```python
from app.schemas.monitoring import NetworkEventCreate
from app.models.monitoring import NetworkEventType

# Log a single network event
event_data = NetworkEventCreate(
    debug_session_id=session.id,
    event_type=NetworkEventType.REQUEST,
    url="https://example.com/api/data",
    method=HTTPMethod.GET,
    request_headers='{"Content-Type": "application/json"}',
    timestamp=datetime.utcnow()
)
event = NetworkEventCRUD.create(db, event_data)

# Log response event
event_data = NetworkEventCreate(
    debug_session_id=session.id,
    event_type=NetworkEventType.RESPONSE,
    url="https://example.com/api/data",
    method=HTTPMethod.GET,
    status_code=200,
    response_headers='{"Content-Type": "application/json"}',
    response_payload='{"status": "success"}',
    duration_ms=150.5
)
event = NetworkEventCRUD.create(db, event_data)

# Bulk create events (more efficient)
events_data = [
    NetworkEventCreate(
        debug_session_id=session.id,
        event_type=NetworkEventType.REQUEST,
        url=f"https://example.com/api/{i}",
        method=HTTPMethod.GET
    )
    for i in range(100)
]
events = NetworkEventCRUD.bulk_create(db, events_data)

# Get all events for a session
events, total = NetworkEventCRUD.get_by_session(db, session_id=session.id)

# Get events in time range
start_time = datetime.utcnow() - timedelta(minutes=5)
end_time = datetime.utcnow()
events = NetworkEventCRUD.get_by_time_range(
    db, session.id, start_time, end_time
)
```

## Enums Reference

```python
from app.models.monitoring import MonitorStatus, HTTPMethod, NetworkEventType

# Monitor Status
MonitorStatus.UP        # Service is operational
MonitorStatus.DOWN      # Service is not responding
MonitorStatus.DEGRADED  # Service is slow or partially unavailable
MonitorStatus.UNKNOWN   # Status cannot be determined

# HTTP Methods
HTTPMethod.GET
HTTPMethod.POST
HTTPMethod.PUT
HTTPMethod.DELETE
HTTPMethod.PATCH
HTTPMethod.HEAD
HTTPMethod.OPTIONS

# Network Event Types
NetworkEventType.REQUEST   # HTTP request initiated
NetworkEventType.RESPONSE  # HTTP response received
NetworkEventType.ERROR     # Network error occurred
NetworkEventType.REDIRECT  # HTTP redirect encountered
NetworkEventType.TIMEOUT   # Request timed out
```

## Database Migration Commands

```bash
# Change to backend directory
cd backend

# Activate virtual environment
source venv/bin/activate

# Check current migration status
alembic current

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# Generate new migration (after modifying models)
alembic revision --autogenerate -m "description of changes"
```

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_monitoring_models.py

# Run with verbose output
pytest tests/test_monitoring_models.py -v

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test class
pytest tests/test_monitoring_models.py::TestWebsiteCRUD -v

# Run specific test method
pytest tests/test_monitoring_models.py::TestWebsiteCRUD::test_create_website_crud -v
```

## API Response Examples

### Website Response
```json
{
  "id": 1,
  "url": "https://example.com",
  "name": "Example Site",
  "description": "A test website",
  "check_interval": 300,
  "timeout": 30,
  "is_active": true,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

### Monitor Check Response
```json
{
  "id": 1,
  "website_id": 1,
  "status": "UP",
  "http_status_code": 200,
  "http_method": "GET",
  "response_time_ms": 150.5,
  "dns_time_ms": 10.2,
  "connect_time_ms": 20.3,
  "tls_time_ms": 15.4,
  "ttfb_ms": 100.1,
  "error_message": null,
  "checked_at": "2024-01-01T00:00:00",
  "created_at": "2024-01-01T00:00:00"
}
```

### Paginated List Response
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "page_size": 50
}
```

## Performance Tips

1. **Use bulk_create for multiple network events** - Much faster than individual inserts
2. **Leverage composite indexes** - Queries on (website_id, timestamp) are optimized
3. **Paginate large result sets** - Use skip/limit parameters
4. **Filter by date ranges** - Use start_date/end_date parameters
5. **Use get_active_websites()** - Faster than filtering manually
6. **Cache frequently accessed data** - Consider caching uptime percentages

## Common Patterns

### Monitoring Loop
```python
async def monitor_website(website: Website, db: Session):
    try:
        # Perform check
        response = await http_client.get(website.url, timeout=website.timeout)
        
        # Record success
        check_data = MonitorCheckCreate(
            website_id=website.id,
            status=MonitorStatus.UP if response.status_code == 200 else MonitorStatus.DEGRADED,
            http_status_code=response.status_code,
            response_time_ms=response.elapsed.total_seconds() * 1000
        )
    except Exception as e:
        # Record failure
        check_data = MonitorCheckCreate(
            website_id=website.id,
            status=MonitorStatus.DOWN,
            error_message=str(e)
        )
    
    check = MonitorCheckCRUD.create(db, check_data)
    
    # Check if this started a downtime
    if check.status == MonitorStatus.DOWN:
        ongoing = DowntimeWindowCRUD.get_ongoing_downtime(db, website.id)
        if not ongoing:
            # Start new downtime window
            downtime_data = DowntimeWindowCreate(
                website_id=website.id,
                started_at=check.checked_at,
                initial_status=MonitorStatus.DOWN
            )
            DowntimeWindowCRUD.create(db, downtime_data)
```

### Debug Session with Event Capture
```python
async def debug_website(website: Website, db: Session):
    # Create debug session
    session_data = DebugSessionCreate(
        website_id=website.id,
        session_key=f"debug-{datetime.utcnow().timestamp()}",
        browser_type="chromium"
    )
    session = DebugSessionCRUD.create(db, session_data)
    
    # Capture network events during browser automation
    events = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Set up event listeners
        page.on("request", lambda req: events.append(
            NetworkEventCreate(
                debug_session_id=session.id,
                event_type=NetworkEventType.REQUEST,
                url=req.url,
                method=HTTPMethod[req.method],
                timestamp=datetime.utcnow()
            )
        ))
        
        await page.goto(website.url)
        await browser.close()
    
    # Save all events
    NetworkEventCRUD.bulk_create(db, events)
    
    # Mark session complete
    update_data = DebugSessionUpdate(
        completed_at=datetime.utcnow(),
        success=True
    )
    DebugSessionCRUD.update(db, session.id, update_data)
```
