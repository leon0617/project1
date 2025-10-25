from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.monitoring import MonitoringResultResponse, SLAMetrics, SLAAnalyticsRequest
from app.schemas.common import PaginatedResponse, PaginationParams
from app.services.monitoring_service import MonitoringService
from app.api.dependencies import get_pagination_params

router = APIRouter()


@router.get(
    "/results",
    response_model=PaginatedResponse[MonitoringResultResponse],
    summary="List monitoring results",
    description="Retrieve paginated monitoring results with optional filtering by website, start time, and end time.",
)
async def list_monitoring_results(
    website_id: Optional[int] = Query(None, description="Filter by website ID"),
    start_time: Optional[datetime] = Query(None, description="Filter by start time"),
    end_time: Optional[datetime] = Query(None, description="Filter by end time"),
    pagination: PaginationParams = Depends(get_pagination_params),
    db: Session = Depends(get_db),
):
    results, total = MonitoringService.get_monitoring_results(
        db,
        website_id=website_id,
        start_time=start_time,
        end_time=end_time,
        skip=pagination.skip,
        limit=pagination.limit,
    )
    return PaginatedResponse(
        items=results,
        total=total,
        skip=pagination.skip,
        limit=pagination.limit,
    )
