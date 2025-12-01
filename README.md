# Project1

This project has evolved from a simple CLI script to a modular FastAPI backend application with containerized deployment.

## Repository Structure

```
project1/
├── backend/              # FastAPI backend application
│   ├── app/              # Application code
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Core functionality (config, database, logging)
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   ├── tasks/        # Scheduled tasks
│   │   └── main.py       # FastAPI application entry point
│   ├── alembic/          # Database migrations
│   ├── Dockerfile        # Backend Docker image
│   ├── entrypoint.sh     # Backend startup script
│   ├── requirements.txt  # Python dependencies
│   └── pyproject.toml    # Poetry configuration
├── frontend/             # Frontend application
│   ├── public/           # Static assets
│   ├── Dockerfile        # Frontend Docker image
│   ├── nginx.conf        # Nginx configuration
│   └── package.json      # Node.js dependencies
├── docker-compose.yml    # Production orchestration
├── docker-compose.dev.yml # Development orchestration
├── .env.example          # Environment template
└── project1.py           # Original CLI script (legacy)
```

## Quick Start with Docker (Recommended)

The fastest way to get started is using Docker Compose:

### Prerequisites

- Docker 20.10+ and Docker Compose 2.0+
- At least 2GB of free disk space

### 1. Using Docker Compose (PostgreSQL)

```bash
# Copy environment template
cp .env.example .env

# Edit .env if needed (defaults work for local development)

# Build and start all services
docker compose up --build

# Or run in detached mode
docker compose up -d
```

**Services will be available at:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:3000/docs
- Health Check: http://localhost:3000/api/health

### 2. Using Docker Compose (SQLite - Development Mode)

```bash
# Start with SQLite database (no PostgreSQL needed)
docker compose -f docker-compose.dev.yml up --build
```

### 3. Stop Services

```bash
# Stop and remove containers
docker compose down

# Stop and remove containers + volumes (clears database)
docker compose down -v
```

## Manual Development Setup (Without Docker)

If you prefer not to use Docker, you can set up the project manually:

### Development Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run database migrations:
```bash
alembic upgrade head
```

5. Start the API server:
```bash
uvicorn app.main:app --reload
```

6. Access the API:
   - Health Check: http://localhost:8000/api/health
   - API Docs: http://localhost:8000/docs

## Features

- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: ORM for database operations
- **Alembic**: Database migration management
- **Pydantic Settings**: Configuration management with environment variables
- **APScheduler**: Support for scheduled background tasks
- **Playwright**: Browser automation support
- **Testing**: Pytest with async support and coverage

## Docker Commands

### Building Images

```bash
# Build all images
docker compose build

# Build specific service
docker compose build backend
docker compose build frontend

# Build with no cache
docker compose build --no-cache
```

### Running Services

```bash
# Start all services
docker compose up

# Start specific services
docker compose up backend postgres

# Start with Redis cache
docker compose --profile with-redis up

# View logs
docker compose logs -f backend
docker compose logs -f frontend
```

### Running Tests in Containers

```bash
# Run backend tests
docker compose exec backend pytest

# Run tests with coverage
docker compose exec backend pytest --cov=app --cov-report=html

# Run specific test file
docker compose exec backend pytest tests/test_health.py
```

### Database Operations

```bash
# Run migrations manually
docker compose exec backend alembic upgrade head

# Create new migration
docker compose exec backend alembic revision --autogenerate -m "description"

# Check migration status
docker compose exec backend alembic current

# Access PostgreSQL
docker compose exec postgres psql -U project1 -d project1_db
```

### Managing Containers

```bash
# View running containers
docker compose ps

# Stop all services
docker compose stop

# Restart specific service
docker compose restart backend

# Remove all containers and volumes
docker compose down -v

# View resource usage
docker stats
```

## Configuration

The application uses environment variables for configuration:

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` to customize:
   - Database credentials
   - Service ports
   - Debug and logging levels
   - Scheduler settings
   - Playwright configuration

Key configuration options:
- Supports both SQLite (development) and PostgreSQL (production)
- Optional Redis for caching
- Configurable scheduler and Playwright settings
- Flexible logging configuration
- Sample data seeding on startup

See `.env.example` for all available options.

## Health Checks

All services include health checks:

- **Backend**: http://localhost:8000/api/health
- **PostgreSQL**: Automated via `pg_isready`
- **Frontend**: Automated via Nginx status
- **Redis**: Automated via `redis-cli ping`

Health check status:
```bash
docker compose ps
```

## Troubleshooting

### Port Conflicts

If ports are already in use, modify in `.env`:
```bash
BACKEND_PORT=8001
FRONTEND_PORT=3001
POSTGRES_PORT=5433
```

### Database Connection Issues

```bash
# Check if PostgreSQL is healthy
docker compose ps postgres

# View PostgreSQL logs
docker compose logs postgres

# Restart PostgreSQL
docker compose restart postgres
```

### Migration Failures

```bash
# Check migration status
docker compose exec backend alembic current

# Rollback last migration
docker compose exec backend alembic downgrade -1

# Force database reset (development only)
docker compose down -v
docker compose up -d
```

### Frontend Can't Reach Backend

Check network configuration:
```bash
# Inspect network
docker network inspect project1_project1-network

# Ensure both containers are on same network
docker compose ps
```

## Documentation

For comprehensive documentation including:
- Detailed environment setup
- API endpoint documentation
- Database migration guide
- Development workflow
- Testing and code quality tools

Please refer to [backend/README.md](backend/README.md).

## Production Deployment

For production deployments:

1. Use proper secrets management (not `.env` files)
2. Set `DEBUG=false`
3. Use PostgreSQL instead of SQLite
4. Enable HTTPS with reverse proxy (nginx/Caddy)
5. Set resource limits in docker-compose.yml
6. Use Docker secrets for sensitive data
7. Enable monitoring and logging
8. Regular database backups

## Legacy CLI Script

The original `project1.py` script is preserved for reference but is no longer the primary application entry point.
