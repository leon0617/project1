from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.monitoring import MonitoringResultResponse, SLAMetrics, SLAAnalyticsRequest
from app.schemas.common import PaginatedResponse, PaginationParams
from app.services.monitoring_service import MonitoringService
from app.api.dependencies import get_pagination_params
from app.tasks.monitoring_task import MonitoringTask
from app.models.website import Website

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


@router.post(
    "/check/{website_id}",
    response_model=MonitoringResultResponse,
    summary="Manually trigger website check",
    description="Manually trigger a monitoring check for a specific website. This will immediately check the website and return the result.",
)
async def trigger_website_check(
    website_id: int,
    db: Session = Depends(get_db),
):
    # Verify website exists
    website = db.query(Website).filter(Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail=f"Website with ID {website_id} not found")

    # Check if there's an active debug session
    from app.models.debug_session import DebugSession
    debug_session = db.query(DebugSession).filter(
        DebugSession.website_id == website_id,
        DebugSession.status == "active"
    ).first()

    debug_session_id = debug_session.id if debug_session else None

    # Perform the check
    result = await MonitoringTask.check_website(
        website,
        db,
        debug_session_id=debug_session_id
    )

    return result
