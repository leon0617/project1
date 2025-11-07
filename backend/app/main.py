import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.api import api_router
from app.tasks.scheduler import task_scheduler

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Database type: {settings.database_type}")
    logger.info(f"Scheduler enabled: {settings.scheduler_enabled}")

    # Initialize and start the scheduler if enabled
    if settings.scheduler_enabled:
        task_scheduler.initialize()
        task_scheduler.start()
        logger.info("Background task scheduler started")

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.app_name}")

    # Clean up scheduler and resources
    if settings.scheduler_enabled:
        await task_scheduler.cleanup()
        logger.info("Background task scheduler stopped")


def create_application() -> FastAPI:
    setup_logging()
    
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )
    
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    application.include_router(api_router, prefix="/api")
    
    return application


app = create_application()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
