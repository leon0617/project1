# Docker Deployment Guide

This guide provides comprehensive instructions for deploying Project1 using Docker and Docker Compose.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Building Images](#building-images)
- [Running Services](#running-services)
- [Health Checks](#health-checks)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Production Deployment](#production-deployment)

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- At least 2GB free disk space
- At least 2GB RAM

## Quick Start

### 1. Clone and Setup

```bash
# Copy environment template
cp .env.example .env

# Review and edit .env if needed
vim .env
```

### 2. Start with Docker Compose (PostgreSQL)

```bash
# Build and start all services
docker compose up --build

# Or run in background
docker compose up -d

# View logs
docker compose logs -f
```

**Services will be available at:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:3000/docs

### 3. Alternative: Development Mode (SQLite)

```bash
# Start with SQLite database (no PostgreSQL)
docker compose -f docker-compose.dev.yml up --build
```

## Architecture

### Services

1. **Backend** (Python/FastAPI)
   - Multi-stage build with Poetry and Playwright
   - Uvicorn ASGI server
   - Automatic database migrations on startup
   - Health check endpoint

2. **Frontend** (Nginx)
   - Node.js build stage
   - Static file serving via Nginx
   - Reverse proxy to backend API
   - Health check monitoring

3. **PostgreSQL** (Production)
   - Alpine-based image
   - Persistent volume storage
   - Health check monitoring

4. **Redis** (Optional)
   - Alpine-based image
   - For caching (enabled with `--profile with-redis`)

### Networks

All services run on a shared `project1-network` bridge network, allowing inter-service communication using service names as hostnames.

### Volumes

- `postgres_data`: PostgreSQL database persistence
- `redis_data`: Redis data persistence (optional)
- `sqlite_dev_data`: SQLite database for development mode

## Configuration

### Environment Variables

Key variables in `.env`:

```bash
# Application
APP_NAME=Project1 API
DEBUG=false

# Database (PostgreSQL)
POSTGRES_USER=project1
POSTGRES_PASSWORD=project1_password
POSTGRES_DB=project1_db

# Service Ports
BACKEND_PORT=8000
FRONTEND_PORT=3000
POSTGRES_PORT=5432

# Features
SCHEDULER_ENABLED=false
PLAYWRIGHT_BROWSER=chromium
SEED_SAMPLE_DATA=false

# Logging
LOG_LEVEL=INFO
```

See `.env.example` for all available options.

### Customizing Ports

If default ports conflict with existing services:

```bash
# Edit .env
BACKEND_PORT=8001
FRONTEND_PORT=3001
POSTGRES_PORT=5433
```

## Building Images

### Build All Services

```bash
docker compose build
```

### Build Specific Service

```bash
docker compose build backend
docker compose build frontend
```

### Build with No Cache

```bash
docker compose build --no-cache
```

### Build Arguments

For production builds with optimizations:

```bash
docker compose build --build-arg BUILD_ENV=production
```

## Running Services

### Start All Services

```bash
# Foreground with logs
docker compose up

# Background (detached)
docker compose up -d

# With specific profile
docker compose --profile with-redis up
```

### Start Specific Services

```bash
# Only backend and database
docker compose up backend postgres

# Only frontend
docker compose up frontend
```

### Stop Services

```bash
# Stop all services
docker compose stop

# Stop specific service
docker compose stop backend

# Stop and remove containers
docker compose down

# Stop and remove containers + volumes
docker compose down -v
```

### Restart Services

```bash
# Restart all services
docker compose restart

# Restart specific service
docker compose restart backend
```

## Health Checks

### View Service Status

```bash
docker compose ps
```

Output shows health status for each service:
- `healthy`: Service is running correctly
- `starting`: Health check in progress
- `unhealthy`: Service failed health check

### Manual Health Checks

```bash
# Backend health
curl http://localhost:8000/api/health

# Frontend health (via Nginx)
curl http://localhost:3000/

# PostgreSQL health
docker compose exec postgres pg_isready -U project1

# Redis health (if enabled)
docker compose exec redis redis-cli ping
```

## Testing

### Run Backend Tests

```bash
# Run all tests
docker compose exec backend pytest

# Run with coverage
docker compose exec backend pytest --cov=app --cov-report=html

# Run specific test file
docker compose exec backend pytest tests/test_health.py

# Run with verbose output
docker compose exec backend pytest -v
```

### View Test Coverage

```bash
# Generate coverage report
docker compose exec backend pytest --cov=app --cov-report=html

# Copy report to host (if needed)
docker compose cp backend:/app/htmlcov ./htmlcov
```

## Database Operations

### Run Migrations

```bash
# Migrations run automatically on startup, but you can run manually:
docker compose exec backend alembic upgrade head

# Check current migration
docker compose exec backend alembic current

# View migration history
docker compose exec backend alembic history
```

### Create New Migration

```bash
# Auto-generate migration from model changes
docker compose exec backend alembic revision --autogenerate -m "add new table"

# Create empty migration
docker compose exec backend alembic revision -m "custom migration"
```

### Rollback Migration

```bash
# Rollback one migration
docker compose exec backend alembic downgrade -1

# Rollback to specific revision
docker compose exec backend alembic downgrade <revision_id>
```

### Access Database

```bash
# PostgreSQL shell
docker compose exec postgres psql -U project1 -d project1_db

# Run SQL query
docker compose exec postgres psql -U project1 -d project1_db -c "SELECT * FROM alembic_version;"
```

### Backup Database

```bash
# Backup PostgreSQL
docker compose exec postgres pg_dump -U project1 project1_db > backup.sql

# Restore PostgreSQL
cat backup.sql | docker compose exec -T postgres psql -U project1 -d project1_db
```

## Logs and Debugging

### View Logs

```bash
# All services
docker compose logs

# Follow logs (tail -f)
docker compose logs -f

# Specific service
docker compose logs backend
docker compose logs frontend

# Last 100 lines
docker compose logs --tail=100 backend
```

### Access Container Shell

```bash
# Backend shell
docker compose exec backend bash

# PostgreSQL shell
docker compose exec postgres sh

# Frontend shell
docker compose exec frontend sh
```

### Inspect Resources

```bash
# Container stats (CPU, memory, network)
docker stats

# Disk usage
docker system df

# Network inspection
docker network inspect project1_project1-network

# Volume inspection
docker volume inspect project1_postgres_data
```

## Troubleshooting

### Port Already in Use

```bash
# Check what's using the port
sudo lsof -i :8000
sudo lsof -i :3000

# Change port in .env
BACKEND_PORT=8001
FRONTEND_PORT=3001
```

### Database Connection Failed

```bash
# Check PostgreSQL is healthy
docker compose ps postgres

# View PostgreSQL logs
docker compose logs postgres

# Restart PostgreSQL
docker compose restart postgres

# Reset database (development only!)
docker compose down -v
docker compose up -d
```

### Migration Failures

```bash
# Check current migration state
docker compose exec backend alembic current

# View detailed error
docker compose logs backend

# Rollback and retry
docker compose exec backend alembic downgrade -1
docker compose exec backend alembic upgrade head
```

### Out of Disk Space

```bash
# Clean up unused Docker resources
docker system prune -a

# Remove unused volumes
docker volume prune

# Remove specific volume
docker volume rm project1_postgres_data
```

### Container Won't Start

```bash
# View detailed logs
docker compose logs backend

# Rebuild with no cache
docker compose build --no-cache backend

# Check for port conflicts
docker compose ps
```

### Playwright Issues

```bash
# Rebuild backend with fresh Playwright install
docker compose build --no-cache backend

# Test Playwright inside container
docker compose exec backend python -c "from playwright.sync_api import sync_playwright; print('OK')"
```

## Production Deployment

### Best Practices

1. **Security**
   - Use Docker secrets for sensitive data
   - Don't commit `.env` files
   - Run containers as non-root users (backend does this)
   - Enable firewall rules

2. **Performance**
   - Use production-grade PostgreSQL instance
   - Enable Redis caching
   - Configure resource limits
   - Use CDN for static assets

3. **Monitoring**
   - Set up logging aggregation
   - Configure health check monitoring
   - Enable metrics collection
   - Set up alerts

4. **Backups**
   - Regular database backups
   - Test restore procedures
   - Store backups off-site

### Production docker-compose.yml Example

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
    restart: always
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Using Docker Secrets

```bash
# Create secrets
echo "my_db_password" | docker secret create db_password -

# Update docker-compose.yml
secrets:
  db_password:
    external: true
```

### Reverse Proxy Setup

Example Nginx reverse proxy configuration:

```nginx
server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Backend README](backend/README.md)
- [Main README](README.md)
