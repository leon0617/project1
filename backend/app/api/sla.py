from typing import List
from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.monitoring import SLAMetrics, SLAAnalyticsRequest
from app.services.monitoring_service import MonitoringService

router = APIRouter()


@router.post(
    "/analytics",
    response_model=List[SLAMetrics],
    summary="Get SLA analytics",
    description="Retrieve SLA metrics including uptime percentage, total checks, and average response time for monitored websites.",
)
async def get_sla_analytics(
    request: SLAAnalyticsRequest = Body(default=SLAAnalyticsRequest()),
    db: Session = Depends(get_db),
):
    metrics = MonitoringService.get_sla_analytics(
        db,
        website_id=request.website_id,
        start_date=request.start_date,
        end_date=request.end_date,
    )
    return metrics
