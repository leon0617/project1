from fastapi import APIRouter
from app.api.health import router as health_router
from app.api.websites import router as websites_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(websites_router, tags=["websites"])

__all__ = ["api_router"]
