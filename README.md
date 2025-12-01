# Project1 - Site Monitoring System

A comprehensive site monitoring and analytics platform with a FastAPI backend and modern React frontend.

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
│   ├── requirements.txt  # Python dependencies
│   ├── pyproject.toml    # Poetry configuration
│   └── README.md         # Backend documentation
├── frontend/             # React + TypeScript frontend
│   ├── src/              # Source code
│   │   ├── components/   # React components
│   │   ├── hooks/        # Custom React hooks
│   │   ├── lib/          # API client and utilities
│   │   ├── pages/        # Page components
│   │   ├── stores/       # State management (Zustand)
│   │   └── types/        # TypeScript types
│   ├── e2e/              # End-to-end tests
│   └── README.md         # Frontend documentation
└── project1.py           # Original CLI script (legacy)
```

## Quick Start

### Backend Setup

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

The backend API will be available at http://localhost:8000

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The frontend application will be available at http://localhost:5173

## Features

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: ORM for database operations
- **Alembic**: Database migration management
- **Pydantic Settings**: Configuration management with environment variables
- **APScheduler**: Support for scheduled background tasks
- **Playwright**: Browser automation support
- **Testing**: Pytest with async support and coverage

### Frontend
- **React 19** with TypeScript
- **Vite**: Fast development and build tool
- **Tailwind CSS**: Utility-first CSS framework
- **React Router**: Client-side routing
- **TanStack Query**: API state management and caching
- **Zustand**: Local state management
- **Recharts**: Data visualization
- **Vitest** + React Testing Library: Unit testing
- **Playwright**: E2E testing

### Application Features
- 📊 **Dashboard**: Real-time uptime metrics, response time charts, and downtime timelines
- 🌐 **Site Management**: Add, edit, and remove monitored sites
- 🐛 **Debug Console**: DevTools-like interface with live event streaming (SSE)
- 📈 **SLA Reports**: Comprehensive availability and performance reports
- ⚙️ **Settings**: Configure monitoring behavior

## Development Workflow

### Running the Full Stack

1. Start the backend (in terminal 1):
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

2. Start the frontend (in terminal 2):
```bash
cd frontend
npm run dev
```

The frontend is configured to proxy API requests to the backend automatically.

### Testing

Backend tests:
```bash
cd backend
pytest
```

Frontend unit tests:
```bash
cd frontend
npm test
```

Frontend e2e tests:
```bash
cd frontend
npm run test:e2e
```

### Building for Production

Backend: The FastAPI application can be run with any ASGI server (Uvicorn, Gunicorn + Uvicorn workers)

Frontend:
```bash
cd frontend
npm run build
```

Build artifacts will be in `frontend/dist/`

## Documentation

- Backend Documentation: [backend/README.md](backend/README.md)
- Frontend Documentation: [frontend/README.md](frontend/README.md)

## API Access

- Health Check: http://localhost:8000/api/health
- API Docs (Swagger UI): http://localhost:8000/docs
- API Docs (ReDoc): http://localhost:8000/redoc

## Configuration

Both backend and frontend use environment variables for configuration. See the respective `.env.example` files in each directory.

## Legacy CLI Script

The original `project1.py` script is preserved for reference but is no longer the primary application entry point.
