# Debug Capture with Playwright

This feature provides comprehensive browser debugging capabilities using Playwright to capture network events, console messages, and errors in real-time.

## Features

- **Network Event Capture**: Records all HTTP requests and responses including headers, bodies, and timing
- **Console Error Tracking**: Captures console errors and warnings from the browser
- **Real-time Streaming**: WebSocket support for live event streaming to clients
- **Historical Query**: Persistent storage of all captured events for historical analysis
- **Session Management**: Support for multiple concurrent debug sessions
- **Duration Limits**: Configurable session timeouts and automatic cleanup
- **Periodic Flushing**: Regular persistence of captured data to prevent data loss

## Setup

### 1. Install Playwright Browsers

After installing the Python dependencies, you need to install Playwright browser binaries:

```bash
cd backend
python setup_playwright.py
```

Or manually:

```bash
python -m playwright install chromium
python -m playwright install-deps chromium  # May require sudo
```

### 2. Run Database Migrations

```bash
alembic upgrade head
```

This will create the necessary tables:
- `debug_sessions` - Stores debug session metadata
- `network_events` - Stores captured network requests/responses
- `console_errors` - Stores console errors and warnings

### 3. Configuration

Set environment variables in `.env`:

```env
# Playwright Settings
PLAYWRIGHT_BROWSER=chromium
PLAYWRIGHT_HEADLESS=true
PLAYWRIGHT_EXECUTABLE_PATH=  # Optional: custom browser path

# Debug Session Settings
DEBUG_SESSION_MAX_DURATION=300  # Maximum session duration (seconds)
DEBUG_SESSION_FLUSH_INTERVAL=5   # How often to flush events (seconds)
```

## API Endpoints

### Create Debug Session

```http
POST /api/debug/sessions
Content-Type: application/json

{
  "target_url": "https://example.com",
  "duration_limit": 60
}
```

Response:
```json
{
  "id": 1,
  "target_url": "https://example.com",
  "status": "pending",
  "duration_limit": 60,
  "created_at": "2024-01-15T10:00:00Z",
  "started_at": null,
  "stopped_at": null,
  "error_message": null
}
```

### Start Debug Session

```http
POST /api/debug/sessions/{session_id}/start
```

This triggers:
1. Browser context creation
2. Page navigation to target URL
3. Network event capture activation
4. Console error monitoring

Response: Updated session with `status: "active"`

### Stop Debug Session

```http
POST /api/debug/sessions/{session_id}/stop
```

This:
1. Stops event capture
2. Flushes remaining events to database
3. Closes browser context
4. Updates session status

Response: Updated session with `status: "stopped"`

### Get Session Details

```http
GET /api/debug/sessions/{session_id}
```

Response includes session metadata plus all captured events:
```json
{
  "id": 1,
  "target_url": "https://example.com",
  "status": "stopped",
  "network_events": [...],
  "console_errors": [...]
}
```

### Query Network Events

```http
GET /api/debug/sessions/{session_id}/events?limit=100&offset=0
```

Paginated list of network events for historical analysis.

### Stream Live Events (WebSocket)

```
WS /api/debug/sessions/{session_id}/stream
```

WebSocket endpoint that streams events in real-time:

```javascript
const ws = new WebSocket('ws://localhost:8000/api/debug/sessions/1/stream');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'network_event') {
    console.log('Network event:', data.event);
  } else if (data.type === 'console_error') {
    console.log('Console error:', data.error);
  } else if (data.type === 'status') {
    console.log('Status update:', data.status, data.message);
  }
};
```

## Usage Example

### Using cURL

```bash
# 1. Create session
SESSION=$(curl -X POST http://localhost:8000/api/debug/sessions \
  -H "Content-Type: application/json" \
  -d '{"target_url": "https://example.com", "duration_limit": 60}' \
  | jq -r '.id')

# 2. Start session
curl -X POST http://localhost:8000/api/debug/sessions/$SESSION/start

# 3. Wait for capture...
sleep 10

# 4. Stop session
curl -X POST http://localhost:8000/api/debug/sessions/$SESSION/stop

# 5. Get captured events
curl http://localhost:8000/api/debug/sessions/$SESSION/events | jq
```

### Using Python

```python
import httpx
import asyncio

async def debug_session():
    async with httpx.AsyncClient() as client:
        # Create session
        response = await client.post(
            "http://localhost:8000/api/debug/sessions",
            json={"target_url": "https://example.com", "duration_limit": 60}
        )
        session_id = response.json()["id"]
        
        # Start session
        await client.post(f"http://localhost:8000/api/debug/sessions/{session_id}/start")
        
        # Wait for capture
        await asyncio.sleep(10)
        
        # Stop session
        await client.post(f"http://localhost:8000/api/debug/sessions/{session_id}/stop")
        
        # Get events
        response = await client.get(f"http://localhost:8000/api/debug/sessions/{session_id}/events")
        events = response.json()
        
        print(f"Captured {len(events)} network events")
        for event in events[:5]:
            print(f"  {event['method']} {event['url']}")

asyncio.run(debug_session())
```

### Using WebSocket for Real-time Streaming

```python
import asyncio
import websockets
import json

async def stream_session(session_id):
    uri = f"ws://localhost:8000/api/debug/sessions/{session_id}/stream"
    
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            
            if data['type'] == 'network_event':
                event = data['event']
                print(f"[NET] {event['method']} {event['url']}")
            elif data['type'] == 'console_error':
                error = data['error']
                print(f"[ERR] {error['level']}: {error['message']}")
            elif data['type'] == 'status':
                print(f"[STATUS] {data['status']}: {data['message']}")

# Start in parallel with session
asyncio.run(stream_session(1))
```

## Architecture

### Services

1. **PlaywrightService** (`app/services/playwright_service.py`)
   - Manages browser lifecycle
   - Creates browser contexts
   - Singleton service initialized on app startup

2. **DebugSessionService** (`app/services/debug_session_service.py`)
   - Manages debug sessions
   - Handles network event capture
   - Coordinates event persistence and streaming
   - Manages session timeouts

3. **StreamingService** (`app/services/streaming_service.py`)
   - Manages WebSocket connections
   - Broadcasts events to connected clients
   - Handles connection cleanup

### Database Models

1. **DebugSession** - Session metadata
2. **NetworkEvent** - HTTP requests/responses
3. **ConsoleError** - Browser console messages

### Event Flow

```
1. Client creates session → Pending state
2. Client starts session → Active state
   ├─ Browser launched
   ├─ Page navigates to URL
   └─ Event handlers registered
3. Events captured → Buffered in memory
4. Periodic flush (every 5s) → Database + WebSocket
5. Client stops OR timeout → Stopped state
   └─ Final flush + cleanup
```

## Testing

### Run Tests

```bash
cd backend
pytest tests/test_debug_session.py -v
pytest tests/test_debug_integration.py -v
```

### Test with Real Browser

To test with a real browser (headed mode):

```env
PLAYWRIGHT_HEADLESS=false
```

Then run the API and create a session.

### Mock Testing

The tests use mocked Playwright components to avoid requiring browser binaries in CI:

```python
@pytest.mark.asyncio
async def test_with_mock():
    with patch('app.services.playwright_service.playwright_service.create_context'):
        # Test logic here
        pass
```

## Troubleshooting

### Browser Binary Not Found

```bash
python -m playwright install chromium
```

### Permission Errors

On Linux, you may need system dependencies:

```bash
sudo python -m playwright install-deps chromium
```

### Database Locked

If using SQLite in production with high concurrency, consider PostgreSQL:

```env
DATABASE_TYPE=postgres
POSTGRES_HOST=localhost
POSTGRES_USER=dbuser
POSTGRES_PASSWORD=dbpass
POSTGRES_DB=project1
```

### Memory Issues

Long-running sessions can accumulate many events. Consider:
- Setting shorter `duration_limit`
- Implementing event retention policies
- Regular database cleanup

## Production Considerations

1. **Concurrency**: Each debug session requires a browser context. Monitor resource usage.
2. **Security**: Validate and sanitize target URLs to prevent SSRF attacks
3. **Rate Limiting**: Implement rate limits on session creation
4. **Storage**: Large response bodies can fill the database quickly
5. **Privacy**: Consider PII in captured data; implement filtering if needed

## Future Enhancements

- [ ] Screenshot capture at intervals
- [ ] HAR file export
- [ ] Network throttling simulation
- [ ] Custom JavaScript injection
- [ ] Performance metrics (FCP, LCP, etc.)
- [ ] Video recording
- [ ] Multi-page session support
