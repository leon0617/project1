# Quick Start Guide

This guide will get you up and running with the Project1 API in under 5 minutes.

## Prerequisites

- Python 3.10 or higher
- pip

## Setup

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database:**
   ```bash
   alembic upgrade head
   ```

5. **Start the server:**
   ```bash
   uvicorn app.main:app --reload
   ```

## Verify Installation

Visit these URLs in your browser:

- **Health Check:** http://localhost:8000/api/health
- **API Documentation:** http://localhost:8000/docs
- **Alternative Docs:** http://localhost:8000/redoc

You should see a JSON response from the health endpoint:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00.000000",
  "app_name": "Project1 API",
  "version": "0.1.0"
}
```

## Next Steps

- Read the [full README](README.md) for detailed documentation
- Modify configuration in `.env` file
- Add your own API endpoints in `app/api/`
- Create database models in `app/models/`
- Write business logic in `app/services/`

## Troubleshooting

**Server won't start?**
- Make sure you're in the `backend` directory
- Check that the virtual environment is activated
- Verify all dependencies are installed

**Database errors?**
- Run `alembic upgrade head` to ensure migrations are up to date
- Check file permissions on the database file

**Port already in use?**
- Use a different port: `uvicorn app.main:app --reload --port 8001`
