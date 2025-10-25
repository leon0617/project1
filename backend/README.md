# Project1 Backend API

A modular FastAPI backend with SQLAlchemy, Alembic migrations, and scheduled website monitoring support.

## Features

- **Website Monitoring**: Automated health checks with configurable intervals
- **APScheduler Integration**: Background job scheduling with circuit breaker pattern
- **Downtime Tracking**: Automatic detection and recording of website outages
- **REST API**: Full CRUD operations for website management
- **Database Persistence**: SQLAlchemy ORM with Alembic migrations
- **Comprehensive Testing**: 36+ tests with 91% code coverage

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
- `SCHEDULER_ENABLED`: Enable APScheduler (default: False)
- `PLAYWRIGHT_BROWSER`: Browser type for Playwright (default: "chromium")
- `LOG_LEVEL`: Logging level (default: "INFO")

### Example .env File

```env
# Development with SQLite
DATABASE_TYPE=sqlite
SQLITE_DB_PATH=./app.db
DEBUG=True
LOG_LEVEL=DEBUG

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
- Website endpoints: http://localhost:8000/api/websites
- API docs (Swagger): http://localhost:8000/docs
- Alternative docs (ReDoc): http://localhost:8000/redoc

## Website Monitoring

The application includes a comprehensive website monitoring system. See [SCHEDULER_MONITORING.md](SCHEDULER_MONITORING.md) for detailed documentation.

### Quick Start

1. Ensure scheduler is enabled in `.env`:
```bash
SCHEDULER_ENABLED=true
```

2. Create a website to monitor:
```bash
curl -X POST http://localhost:8000/api/websites \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "name": "Example Site",
    "enabled": true,
    "check_interval": 300
  }'
```

3. The scheduler will automatically start checking the website every 5 minutes (300 seconds)

### Key Features

- **Automated Checks**: HTTP requests with timeout and retry handling
- **Metrics Collection**: Response time, HTTP status, availability
- **Downtime Tracking**: Automatic detection of outages with start/end times
- **Circuit Breaker**: Prevents overwhelming failing sites
- **Dynamic Job Management**: Jobs added/removed when websites enabled/disabled
- **Structured Logging**: Comprehensive logs for monitoring and debugging

See the [monitoring documentation](SCHEDULER_MONITORING.md) for API endpoints, configuration options, and architecture details

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

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00.000000",
  "app_name": "Project1 API",
  "version": "0.1.0"
}
```

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
