from fastapi import APIRouter
from app.api.health import router as health_router
from app.api.websites import router as websites_router
from app.api.monitoring import router as monitoring_router
from app.api.sla import router as sla_router
from app.api.debug import router as debug_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(websites_router, prefix="/websites", tags=["websites"])
api_router.include_router(monitoring_router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(sla_router, prefix="/sla", tags=["sla"])
api_router.include_router(debug_router, prefix="/debug", tags=["debug"])

__all__ = ["api_router"]
