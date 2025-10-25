# API Examples

This document provides example requests and responses for all API endpoints.

## Table of Contents

- [Health Check](#health-check)
- [Websites CRUD](#websites-crud)
- [Monitoring Results](#monitoring-results)
- [SLA Analytics](#sla-analytics)
- [Debug Sessions](#debug-sessions)
- [Network Events](#network-events)
- [Streaming](#streaming)

## Health Check

### GET /api/health

Check the API health status.

**Request:**
```bash
curl http://localhost:8000/api/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00.000000Z",
  "app_name": "Project1 API",
  "version": "0.1.0"
}
```

## Websites CRUD

### POST /api/websites/

Create a new website to monitor.

**Request:**
```bash
curl -X POST http://localhost:8000/api/websites/ \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "name": "Example Website",
    "check_interval": 300,
    "enabled": true
  }'
```

**Response:**
```json
{
  "id": 1,
  "url": "https://example.com",
  "name": "Example Website",
  "check_interval": 300,
  "enabled": true,
  "created_at": "2024-01-01T00:00:00.000000Z",
  "updated_at": "2024-01-01T00:00:00.000000Z"
}
```

**Error Cases:**

Invalid URL:
```bash
curl -X POST http://localhost:8000/api/websites/ \
  -H "Content-Type: application/json" \
  -d '{
    "url": "invalid-url",
    "name": "Invalid Website"
  }'
```

Response: `422 Unprocessable Entity`

Duplicate URL:
```bash
# After creating a website, trying to create another with the same URL
```

Response: `400 Bad Request`
```json
{
  "detail": "Website with URL https://example.com already exists"
}
```

### GET /api/websites/

List all websites with pagination.

**Request:**
```bash
curl "http://localhost:8000/api/websites/?skip=0&limit=50"
```

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "url": "https://example.com",
      "name": "Example Website",
      "check_interval": 300,
      "enabled": true,
      "created_at": "2024-01-01T00:00:00.000000Z",
      "updated_at": "2024-01-01T00:00:00.000000Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 50
}
```

### GET /api/websites/{website_id}

Get a specific website by ID.

**Request:**
```bash
curl http://localhost:8000/api/websites/1
```

**Response:**
```json
{
  "id": 1,
  "url": "https://example.com",
  "name": "Example Website",
  "check_interval": 300,
  "enabled": true,
  "created_at": "2024-01-01T00:00:00.000000Z",
  "updated_at": "2024-01-01T00:00:00.000000Z"
}
```

### PUT /api/websites/{website_id}

Update a website's configuration.

**Request:**
```bash
curl -X PUT http://localhost:8000/api/websites/1 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Example Website",
    "check_interval": 600,
    "enabled": false
  }'
```

**Response:**
```json
{
  "id": 1,
  "url": "https://example.com",
  "name": "Updated Example Website",
  "check_interval": 600,
  "enabled": false,
  "created_at": "2024-01-01T00:00:00.000000Z",
  "updated_at": "2024-01-01T00:00:10.000000Z"
}
```

### DELETE /api/websites/{website_id}

Delete a website and all its monitoring data.

**Request:**
```bash
curl -X DELETE http://localhost:8000/api/websites/1
```

**Response:** `204 No Content`

## Monitoring Results

### GET /api/monitoring/results

List monitoring results with optional filters.

**Request:**
```bash
# All results
curl "http://localhost:8000/api/monitoring/results?skip=0&limit=50"

# Filter by website
curl "http://localhost:8000/api/monitoring/results?website_id=1"

# Filter by time range
curl "http://localhost:8000/api/monitoring/results?start_time=2024-01-01T00:00:00Z&end_time=2024-01-31T23:59:59Z"
```

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "website_id": 1,
      "timestamp": "2024-01-01T00:00:00.000000Z",
      "status_code": 200,
      "response_time": 0.534,
      "success": 1,
      "error_message": null
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 50
}
```

## SLA Analytics

### POST /api/sla/analytics

Get SLA metrics for websites.

**Request:**
```bash
# All websites, last 30 days (default)
curl -X POST http://localhost:8000/api/sla/analytics \
  -H "Content-Type: application/json" \
  -d '{}'

# Specific website with date range
curl -X POST http://localhost:8000/api/sla/analytics \
  -H "Content-Type: application/json" \
  -d '{
    "website_id": 1,
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-01-31T23:59:59Z"
  }'
```

**Response:**
```json
[
  {
    "website_id": 1,
    "website_name": "Example Website",
    "uptime_percentage": 99.5,
    "total_checks": 1000,
    "successful_checks": 995,
    "failed_checks": 5,
    "average_response_time": 0.542,
    "start_date": "2024-01-01T00:00:00.000000Z",
    "end_date": "2024-01-31T23:59:59.000000Z"
  }
]
```

## Debug Sessions

### POST /api/debug/sessions

Start a debug session for a website.

**Request:**
```bash
curl -X POST http://localhost:8000/api/debug/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "website_id": 1
  }'
```

**Response:**
```json
{
  "id": 1,
  "website_id": 1,
  "start_time": "2024-01-01T00:00:00.000000Z",
  "end_time": null,
  "status": "active"
}
```

**Error Cases:**

Website not found:
```json
{
  "detail": "Website with ID 9999 not found"
}
```

Overlapping session:
```json
{
  "detail": "Debug session already active for website 1"
}
```

### POST /api/debug/sessions/{session_id}/stop

Stop an active debug session.

**Request:**
```bash
curl -X POST http://localhost:8000/api/debug/sessions/1/stop
```

**Response:**
```json
{
  "id": 1,
  "website_id": 1,
  "start_time": "2024-01-01T00:00:00.000000Z",
  "end_time": "2024-01-01T00:10:00.000000Z",
  "status": "completed"
}
```

### GET /api/debug/sessions/{session_id}

Get a specific debug session.

**Request:**
```bash
curl http://localhost:8000/api/debug/sessions/1
```

**Response:**
```json
{
  "id": 1,
  "website_id": 1,
  "start_time": "2024-01-01T00:00:00.000000Z",
  "end_time": "2024-01-01T00:10:00.000000Z",
  "status": "completed"
}
```

### GET /api/debug/sessions

List debug sessions.

**Request:**
```bash
# All sessions
curl "http://localhost:8000/api/debug/sessions?skip=0&limit=50"

# Filter by website
curl "http://localhost:8000/api/debug/sessions?website_id=1"
```

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "website_id": 1,
      "start_time": "2024-01-01T00:00:00.000000Z",
      "end_time": "2024-01-01T00:10:00.000000Z",
      "status": "completed"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 50
}
```

## Network Events

### GET /api/debug/events

List network events with filters.

**Request:**
```bash
# All events
curl "http://localhost:8000/api/debug/events?skip=0&limit=50"

# Filter by debug session
curl "http://localhost:8000/api/debug/events?debug_session_id=1"

# Filter by time range
curl "http://localhost:8000/api/debug/events?start_time=2024-01-01T00:00:00Z&end_time=2024-01-01T00:10:00Z"

# Filter by HTTP method
curl "http://localhost:8000/api/debug/events?method=GET"

# Combine filters
curl "http://localhost:8000/api/debug/events?debug_session_id=1&method=POST&skip=0&limit=20"
```

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "debug_session_id": 1,
      "timestamp": "2024-01-01T00:00:01.000000Z",
      "method": "GET",
      "url": "https://example.com/",
      "status_code": 200,
      "headers": "{\"Content-Type\": \"text/html\"}",
      "request_body": null,
      "response_body": "<!DOCTYPE html>...",
      "duration": 234
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 50
}
```

## Streaming

### GET /api/debug/sessions/{session_id}/stream

Stream live network events from an active debug session using Server-Sent Events (SSE).

**Request:**
```bash
curl -N http://localhost:8000/api/debug/sessions/1/stream
```

**Response (streaming):**
```
data: {"id": 1, "timestamp": "2024-01-01T00:00:01.000000Z", "method": "GET", "url": "https://example.com/", "status_code": 200, "duration": 234}

data: {"id": 2, "timestamp": "2024-01-01T00:00:02.000000Z", "method": "GET", "url": "https://example.com/style.css", "status_code": 200, "duration": 45}

: keepalive

data: {"id": 3, "timestamp": "2024-01-01T00:00:03.000000Z", "method": "GET", "url": "https://example.com/script.js", "status_code": 200, "duration": 87}
```

**JavaScript Example:**
```javascript
const eventSource = new EventSource('http://localhost:8000/api/debug/sessions/1/stream');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Network event:', data);
};

eventSource.onerror = (error) => {
  console.error('Stream error:', error);
  eventSource.close();
};
```

**Error Cases:**

Session not found:
```json
{
  "detail": "Debug session not found"
}
```

Session not active:
```json
{
  "detail": "Debug session is not active"
}
```

## Pagination

All list endpoints support pagination with the following query parameters:

- `skip`: Number of items to skip (default: 0, min: 0)
- `limit`: Number of items to return (default: 50, min: 1, max: 100)

**Example:**
```bash
curl "http://localhost:8000/api/websites/?skip=10&limit=20"
```

## Error Handling

All endpoints return standard HTTP status codes:

- `200 OK`: Successful GET/PUT/POST request
- `201 Created`: Successful resource creation
- `204 No Content`: Successful DELETE request
- `400 Bad Request`: Invalid request data or business logic error
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

Error responses follow this format:
```json
{
  "detail": "Error message describing what went wrong"
}
```

## OpenAPI Documentation

Interactive API documentation is available at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json
