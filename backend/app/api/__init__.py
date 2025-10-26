from fastapi import APIRouter
from app.api.health import router as health_router
from app.api.debug import router as debug_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(debug_router, tags=["debug"])

__all__ = ["api_router"]
