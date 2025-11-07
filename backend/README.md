# Project1 Backend API

A modular FastAPI backend with SQLAlchemy, Alembic migrations, and scheduled task support.

## Project Structure

```
backend/
├── app/
│   ├── api/              # API endpoints and routes
│   ├── core/             # Core functionality (config, database, logging)
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic services
│   ├── tasks/            # Scheduled tasks
│   └── main.py           # FastAPI application entry point
├── alembic/              # Database migrations
│   ├── versions/         # Migration scripts
│   └── env.py            # Alembic environment configuration
├── pyproject.toml        # Poetry dependencies (alternative)
├── requirements.txt      # Pip dependencies
├── alembic.ini           # Alembic configuration
└── .env                  # Environment variables
```

## Environment Setup

### Using Virtual Environment (venv)

1. Create a virtual environment:
```bash
cd backend
python3 -m venv venv
```

2. Activate the virtual environment:
```bash
# On Linux/Mac:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Playwright browsers (if using Playwright):
```bash
playwright install
```

### Using Poetry

1. Install Poetry (if not already installed):
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Install dependencies:
```bash
cd backend
poetry install
```

3. Install Playwright browsers:
```bash
poetry run playwright install
```

4. Activate the Poetry shell:
```bash
poetry shell
```

## Configuration

The application uses Pydantic Settings to manage configuration. Settings can be configured via environment variables or the `.env` file.

### Key Configuration Options

- `APP_NAME`: Application name (default: "Project1 API")
- `DEBUG`: Enable debug mode (default: False)
- `DATABASE_TYPE`: Database type - "sqlite" or "postgres" (default: "sqlite")
- `SQLITE_DB_PATH`: SQLite database file path (default: "./app.db")
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`: PostgreSQL connection settings
- `SCHEDULER_ENABLED`: Enable APScheduler for automated monitoring (default: False)
- `SCHEDULER_TIMEZONE`: Timezone for scheduled tasks (default: "UTC")
- `PLAYWRIGHT_BROWSER`: Browser type for Playwright (default: "chromium")
- `PLAYWRIGHT_HEADLESS`: Run browser in headless mode (default: True)
- `PLAYWRIGHT_EXECUTABLE_PATH`: Custom browser executable path (optional)
- `LOG_LEVEL`: Logging level (default: "INFO")

### Example .env File

```env
# Application
APP_NAME=Project1 API
DEBUG=True
LOG_LEVEL=DEBUG

# Development with SQLite
DATABASE_TYPE=sqlite
SQLITE_DB_PATH=./app.db

# Scheduler (for automated monitoring)
SCHEDULER_ENABLED=true
SCHEDULER_TIMEZONE=UTC

# Playwright (for website monitoring)
PLAYWRIGHT_BROWSER=chromium
PLAYWRIGHT_HEADLESS=true

# Production with PostgreSQL
# DATABASE_TYPE=postgres
# POSTGRES_HOST=localhost
# POSTGRES_PORT=5432
# POSTGRES_USER=myuser
# POSTGRES_PASSWORD=mypassword
# POSTGRES_DB=project1
```

## Running the API Server

### Using Uvicorn directly

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Using Python

```bash
cd backend
python -m app.main
```

### Using Poetry

```bash
cd backend
poetry run uvicorn app.main:app --reload
```

The API will be available at:
- Health check: http://localhost:8000/api/health
- API docs (Swagger): http://localhost:8000/docs
- Alternative docs (ReDoc): http://localhost:8000/redoc

## Database Migrations with Alembic

### Initialize (already done)

The Alembic environment is already configured and a placeholder initial migration exists.

### Running Migrations

Apply all pending migrations:
```bash
cd backend
alembic upgrade head
```

### Creating New Migrations

After modifying models in `app/models/`, generate a new migration:
```bash
alembic revision --autogenerate -m "description of changes"
```

### Checking Migration Status

View current migration status:
```bash
alembic current
```

View migration history:
```bash
alembic history
```

### Rolling Back Migrations

Downgrade one migration:
```bash
alembic downgrade -1
```

Downgrade to a specific revision:
```bash
alembic downgrade <revision_id>
```

## Development Workflow

1. **Start the API server** (with hot reload):
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Make changes** to code in `app/` directory

3. **Add new models** in `app/models/` and generate migrations:
   ```bash
   alembic revision --autogenerate -m "add new model"
   alembic upgrade head
   ```

4. **Test the API** using:
   - Swagger UI: http://localhost:8000/docs
   - curl or Postman
   - pytest tests

## Testing

Run tests using pytest:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=app --cov-report=html
```

## Code Quality

### Format code with Black

```bash
black app/
```

### Check code with Flake8

```bash
flake8 app/
```

### Sort imports with isort

```bash
isort app/
```

### Type checking with mypy

```bash
mypy app/
```

## API Endpoints

### Health Check

- **GET** `/api/health` - Returns application health status

### Websites (CRUD)

- **POST** `/api/websites/` - Create a new website to monitor
- **GET** `/api/websites/` - List all websites (with pagination)
- **GET** `/api/websites/{website_id}` - Get a specific website
- **PUT** `/api/websites/{website_id}` - Update a website
- **DELETE** `/api/websites/{website_id}` - Delete a website

### Monitoring Results

- **GET** `/api/monitoring/results` - List monitoring results with pagination and filtering
  - Query parameters: `website_id`, `start_time`, `end_time`, `skip`, `limit`
- **POST** `/api/monitoring/check/{website_id}` - Manually trigger a website check
  - Returns the monitoring result immediately

### SLA Analytics

- **POST** `/api/sla/analytics` - Get SLA metrics (uptime %, response times, etc.)
  - Request body: `website_id`, `start_date`, `end_date` (all optional)

### Debug Sessions

- **POST** `/api/debug/sessions` - Start a debug session for a website
- **POST** `/api/debug/sessions/{session_id}/stop` - Stop an active debug session
- **GET** `/api/debug/sessions/{session_id}` - Get a specific debug session
- **GET** `/api/debug/sessions` - List debug sessions with pagination

### Network Events

- **GET** `/api/debug/events` - List network events with pagination and filtering
  - Query parameters: `debug_session_id`, `start_time`, `end_time`, `method`, `skip`, `limit`

### Streaming

- **GET** `/api/debug/sessions/{session_id}/stream` - Stream live network events (SSE)

For detailed API documentation with request/response examples, see [docs/API_EXAMPLES.md](docs/API_EXAMPLES.md)

For monitoring implementation details, see [docs/MONITORING_IMPLEMENTATION.md](docs/MONITORING_IMPLEMENTATION.md)

Interactive documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Automated Website Monitoring

The application includes an automated website monitoring system using Playwright and APScheduler.

### Features

- **Periodic Checks**: Automatically checks all enabled websites every 60 seconds
- **Metrics Tracking**: Records response time, status code, and success/failure
- **Network Event Capture**: Captures detailed network events during debug sessions
- **Manual Triggers**: Supports on-demand website checks via API
- **Error Handling**: Gracefully handles network errors and timeouts

### Enabling Automated Monitoring

1. Set `SCHEDULER_ENABLED=true` in your `.env` file
2. Install Playwright browsers:
   ```bash
   playwright install chromium
   ```
3. Start the application:
   ```bash
   uvicorn app.main:app --reload
   ```
4. Add websites to monitor via the API

The scheduler will automatically start and check all enabled websites every 60 seconds.

### Manual Check

You can also trigger a website check manually:

```bash
curl -X POST http://localhost:8000/api/monitoring/check/1
```

This is useful for testing or immediate validation.

### Viewing Results

View monitoring results:

```bash
# List all results
curl http://localhost:8000/api/monitoring/results

# Filter by website
curl "http://localhost:8000/api/monitoring/results?website_id=1"

# Get SLA analytics
curl -X POST http://localhost:8000/api/sla/analytics \
  -H "Content-Type: application/json" \
  -d '{"website_id": 1}'
```

For more details, see [docs/MONITORING_IMPLEMENTATION.md](docs/MONITORING_IMPLEMENTATION.md)

## Troubleshooting

### Database Connection Issues

- **SQLite**: Ensure the database file path is writable
- **PostgreSQL**: Verify connection credentials and that the database server is running

### Import Errors

Ensure you're running commands from the `backend/` directory and the virtual environment is activated.

### Port Already in Use

Change the port in the uvicorn command:
```bash
uvicorn app.main:app --reload --port 8001
```

## Production Deployment

1. Set environment variables for production
2. Use a production WSGI server (Gunicorn + Uvicorn workers):
   ```bash
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```
3. Use PostgreSQL instead of SQLite
4. Enable proper logging and monitoring
5. Set up reverse proxy (nginx/Apache)
6. Enable HTTPS with SSL certificates

## License

MIT
