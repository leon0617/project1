# Monitoring Models Implementation Summary

This document summarizes the implementation of the monitoring data layer for the FastAPI backend application.

## Overview

A comprehensive monitoring system has been implemented with SQLAlchemy ORM models, Pydantic schemas, CRUD services, Alembic migrations, and unit tests. The system supports website monitoring, downtime tracking, debug sessions, and network event logging.

## Components Implemented

### 1. SQLAlchemy ORM Models (`app/models/monitoring.py`)

Five interconnected models have been created to capture all monitoring data:

#### Website
- Stores monitored websites
- Fields: url (unique), name, description, check_interval, timeout, is_active
- Audit timestamps: created_at, updated_at
- Relationships: monitor_checks, downtime_windows, debug_sessions
- Indexes: composite index on (is_active, url)

#### MonitorCheck
- Records individual monitoring checks
- Fields: website_id (FK), status, http_status_code, http_method
- Timing fields: response_time_ms, dns_time_ms, connect_time_ms, tls_time_ms, ttfb_ms
- Error tracking: error_message
- Timestamps: checked_at, created_at
- Indexes: composite indexes on (website_id, checked_at) and (status, checked_at)

#### DowntimeWindow
- Tracks periods of downtime
- Fields: website_id (FK), started_at, ended_at, duration_seconds
- Status tracking: initial_status, recovery_status
- Metrics: affected_checks_count
- Notes: root_cause, notes
- Indexes: composite indexes on (website_id, started_at) and (website_id, ended_at)

#### DebugSession
- Captures debugging sessions
- Fields: website_id (FK), session_key (unique), started_at, completed_at
- Results: success, error_message
- Metadata: user_agent, browser_type
- Relationships: network_events
- Indexes: composite index on (website_id, started_at)

#### NetworkEvent
- Logs network events during debug sessions
- Fields: debug_session_id (FK), event_type, url, method
- HTTP details: status_code, request_headers, response_headers
- Payloads: request_payload, response_payload (truncated)
- Timing: timestamp, duration_ms
- Indexes: composite indexes on (debug_session_id, timestamp) and (event_type, timestamp)

#### Enums
- `MonitorStatus`: UP, DOWN, DEGRADED, UNKNOWN
- `HTTPMethod`: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
- `NetworkEventType`: REQUEST, RESPONSE, ERROR, REDIRECT, TIMEOUT

### 2. Pydantic Schemas (`app/schemas/monitoring.py`)

Complete schema definitions for all operations:

#### Schema Types
- **Base**: Common fields shared across operations
- **Create**: Fields required for creating new records
- **Update**: Optional fields for partial updates
- **Read**: Full model representation with ORM compatibility
- **Extended**: Additional computed fields (e.g., WebsiteWithStats, DebugSessionWithEvents)

#### Collection Responses
Pagination-ready response schemas:
- `WebsiteListResponse`
- `MonitorCheckListResponse`
- `DowntimeWindowListResponse`
- `DebugSessionListResponse`
- `NetworkEventListResponse`

Each includes: items (list), total (int), page (int), page_size (int)

### 3. CRUD Services (`app/services/monitoring_crud.py`)

Five CRUD classes with comprehensive database operations:

#### WebsiteCRUD
- Standard CRUD: create, get_by_id, get_by_url, get_all, update, delete
- Specialized: get_active_websites() - fetch only active websites
- Pagination support with active_only filtering

#### MonitorCheckCRUD
- Standard CRUD: create, get_by_id
- Queries: get_by_website, get_latest_by_website, get_recent_checks
- Analytics: calculate_uptime_percentage(hours=24)
- Time range filtering support

#### DowntimeWindowCRUD
- Standard CRUD: create, get_by_id, update, delete
- Queries: get_by_website, get_ongoing_downtime
- Auto-calculation of duration_seconds on update

#### DebugSessionCRUD
- Standard CRUD: create, get_by_id, get_by_session_key, update, delete
- Queries: get_by_website

#### NetworkEventCRUD
- Standard CRUD: create, get_by_id, delete
- Bulk operations: bulk_create() for efficient batch inserts
- Queries: get_by_session, get_by_time_range

### 4. Alembic Migration (`alembic/versions/1a96e5049f0d_add_monitoring_models.py`)

Comprehensive migration creating all tables, indexes, and constraints:

#### Tables Created
- websites
- debug_sessions
- downtime_windows
- monitor_checks
- network_events

#### Features
- Foreign key constraints with CASCADE deletes
- Unique constraints on urls and session_keys
- Enum types for MonitorStatus, HTTPMethod, NetworkEventType
- Composite indexes for efficient querying
- Complete downgrade support

#### Migration Commands
```bash
# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### 5. Unit Tests (`tests/test_monitoring_models.py`)

Comprehensive test suite with 32 passing tests:

#### Test Coverage
1. **Model Tests** (ORM validation)
   - Website: creation, unique constraints, relationships
   - MonitorCheck: creation, error handling, cascade deletes
   - DowntimeWindow: creation, completion
   - DebugSession: creation, unique keys
   - NetworkEvent: creation, request/response handling

2. **CRUD Tests** (Service layer validation)
   - WebsiteCRUD: all operations, active filtering
   - MonitorCheckCRUD: queries, pagination, uptime calculation
   - DowntimeWindowCRUD: ongoing downtime tracking, updates
   - DebugSessionCRUD: session key lookups, updates
   - NetworkEventCRUD: bulk inserts, time range queries

#### Test Infrastructure
- In-memory SQLite database for isolation
- Pytest fixtures for database session and sample data
- Organized in test classes by model/service
- 79-89% code coverage on implemented modules

## Database Schema

```
websites
├── id (PK)
├── url (unique)
├── name
├── description
├── check_interval
├── timeout
├── is_active
├── created_at
└── updated_at

monitor_checks
├── id (PK)
├── website_id (FK → websites.id, CASCADE)
├── status (enum)
├── http_status_code
├── http_method (enum)
├── response_time_ms
├── dns_time_ms
├── connect_time_ms
├── tls_time_ms
├── ttfb_ms
├── error_message
├── checked_at
└── created_at

downtime_windows
├── id (PK)
├── website_id (FK → websites.id, CASCADE)
├── started_at
├── ended_at
├── duration_seconds
├── initial_status (enum)
├── recovery_status (enum)
├── affected_checks_count
├── root_cause
├── notes
├── created_at
└── updated_at

debug_sessions
├── id (PK)
├── website_id (FK → websites.id, CASCADE)
├── session_key (unique)
├── started_at
├── completed_at
├── success
├── error_message
├── user_agent
├── browser_type
├── created_at
└── updated_at

network_events
├── id (PK)
├── debug_session_id (FK → debug_sessions.id, CASCADE)
├── event_type (enum)
├── url
├── method (enum)
├── status_code
├── request_headers
├── response_headers
├── request_payload
├── response_payload
├── timestamp
├── duration_ms
├── error_message
└── created_at
```

## Key Features

### 1. Cascade Deletes
All foreign key relationships use `ondelete='CASCADE'` ensuring referential integrity:
- Deleting a website removes all associated checks, downtime windows, and debug sessions
- Deleting a debug session removes all associated network events

### 2. Composite Indexes
Optimized queries with composite indexes on frequently queried column combinations:
- (website_id, checked_at) for monitor_checks
- (website_id, started_at) for downtime_windows and debug_sessions
- (debug_session_id, timestamp) for network_events

### 3. Audit Timestamps
All models include automatic timestamps:
- `created_at`: Set on record creation
- `updated_at`: Automatically updated on modification (where applicable)

### 4. Enum Types
Type-safe status fields using Python enums mapped to database enums

### 5. Pagination Support
All list queries return tuples (items, total) for pagination:
```python
items, total = WebsiteCRUD.get_all(db, skip=0, limit=50)
```

### 6. Helper Methods
Domain-specific helpers for common operations:
- `get_active_websites()` - fetch only enabled websites
- `get_ongoing_downtime()` - find current downtime
- `calculate_uptime_percentage()` - compute availability metrics
- `bulk_create()` - efficient batch inserts for network events

## Usage Examples

### Creating a Website
```python
from app.services import WebsiteCRUD
from app.schemas import WebsiteCreate

website_data = WebsiteCreate(
    url="https://example.com",
    name="Example Site",
    check_interval=300,
    timeout=30,
    is_active=True
)
website = WebsiteCRUD.create(db, website_data)
```

### Recording a Monitor Check
```python
from app.services import MonitorCheckCRUD
from app.schemas import MonitorCheckCreate
from app.models import MonitorStatus, HTTPMethod

check_data = MonitorCheckCreate(
    website_id=website.id,
    status=MonitorStatus.UP,
    http_status_code=200,
    http_method=HTTPMethod.GET,
    response_time_ms=150.5
)
check = MonitorCheckCRUD.create(db, check_data)
```

### Calculating Uptime
```python
uptime = MonitorCheckCRUD.calculate_uptime_percentage(
    db, website.id, hours=24
)
print(f"Uptime: {uptime}%")
```

### Tracking Downtime
```python
from app.services import DowntimeWindowCRUD
from app.schemas import DowntimeWindowCreate

downtime_data = DowntimeWindowCreate(
    website_id=website.id,
    started_at=datetime.utcnow(),
    initial_status=MonitorStatus.DOWN
)
downtime = DowntimeWindowCRUD.create(db, downtime_data)

# Later, close the downtime window
update_data = DowntimeWindowUpdate(
    ended_at=datetime.utcnow(),
    recovery_status=MonitorStatus.UP
)
DowntimeWindowCRUD.update(db, downtime.id, update_data)
```

### Debug Session with Network Events
```python
from app.services import DebugSessionCRUD, NetworkEventCRUD
from app.schemas import DebugSessionCreate, NetworkEventCreate
from app.models import NetworkEventType

# Create debug session
session_data = DebugSessionCreate(
    website_id=website.id,
    session_key="debug-123",
    browser_type="chromium"
)
session = DebugSessionCRUD.create(db, session_data)

# Log network events
events = [
    NetworkEventCreate(
        debug_session_id=session.id,
        event_type=NetworkEventType.REQUEST,
        url="https://example.com/api",
        method=HTTPMethod.GET
    ),
    NetworkEventCreate(
        debug_session_id=session.id,
        event_type=NetworkEventType.RESPONSE,
        url="https://example.com/api",
        status_code=200
    )
]
NetworkEventCRUD.bulk_create(db, events)
```

## Testing

Run the test suite:
```bash
cd backend
source venv/bin/activate
pytest tests/test_monitoring_models.py -v
```

All 32 tests pass, covering:
- Model creation and validation
- Unique constraints
- Foreign key relationships
- Cascade deletes
- CRUD operations
- Pagination
- Time range queries
- Bulk operations
- Uptime calculations

## Performance Considerations

1. **Indexes**: Composite indexes optimize common query patterns
2. **Bulk Operations**: `bulk_create()` for network events reduces DB round-trips
3. **Pagination**: All list queries support offset/limit for large datasets
4. **Cascade Deletes**: Database-level cascades prevent orphaned records
5. **In-Memory Tests**: Fast test execution with SQLite :memory:

## Future Enhancements

Potential improvements for future iterations:
1. Add full-text search on error messages
2. Implement data retention policies (automatic cleanup of old checks)
3. Add materialized views for common aggregate queries
4. Implement database partitioning for high-volume tables
5. Add support for alerting thresholds and notification rules

## Migration History

- **001**: Initial placeholder migration
- **1a96e5049f0d**: Add monitoring models (websites, monitor_checks, downtime_windows, debug_sessions, network_events)

## Conclusion

The monitoring data layer is fully implemented and tested, providing:
- ✅ SQLAlchemy ORM models with proper relationships and constraints
- ✅ Pydantic schemas for all CRUD operations
- ✅ Comprehensive CRUD services with helper methods
- ✅ Alembic migration with full upgrade/downgrade support
- ✅ 32 passing unit tests with 79-89% code coverage
- ✅ Performance optimizations through indexing
- ✅ Type safety through Enums and Pydantic validation

All acceptance criteria have been met:
- ✅ Alembic migration creates all persistence structures
- ✅ ORM models round-trip in tests
- ✅ CRUD helpers cover the main entity lifecycles
