# Project1

This project has evolved from a simple CLI script to a modular FastAPI backend application.

## Repository Structure

```
project1/
├── backend/              # FastAPI backend application (see backend/README.md for details)
│   ├── app/              # Application code
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Core functionality (config, database, logging)
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   ├── tasks/        # Scheduled tasks
│   │   └── main.py       # FastAPI application entry point
│   ├── alembic/          # Database migrations
│   ├── requirements.txt  # Python dependencies
│   ├── pyproject.toml    # Poetry configuration
│   └── README.md         # Backend documentation
└── project1.py           # Original CLI script (legacy)
```

## Quick Start

For detailed instructions, see [backend/README.md](backend/README.md).

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

## Configuration

The application uses environment variables for configuration. Copy `.env` from the backend directory and adjust as needed:

- Supports both SQLite (development) and PostgreSQL (production)
- Configurable scheduler and Playwright settings
- Flexible logging configuration

## Documentation

For comprehensive documentation including:
- Detailed environment setup
- API endpoint documentation
- Database migration guide
- Development workflow
- Testing and code quality tools

Please refer to [backend/README.md](backend/README.md).

## Legacy CLI Script

The original `project1.py` script is preserved for reference but is no longer the primary application entry point.
