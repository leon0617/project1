from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.website import WebsiteCreate, WebsiteUpdate, WebsiteResponse
from app.schemas.common import PaginatedResponse, PaginationParams
from app.services.website_service import WebsiteService
from app.api.dependencies import get_pagination_params

router = APIRouter()


@router.post(
    "/",
    response_model=WebsiteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new website",
    description="Create a new website to monitor. URL must be unique and start with http:// or https://.",
)
async def create_website(
    website: WebsiteCreate,
    db: Session = Depends(get_db),
):
    try:
        db_website = WebsiteService.create_website(db, website)
        return db_website
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/",
    response_model=PaginatedResponse[WebsiteResponse],
    summary="List all websites",
    description="Retrieve a paginated list of all monitored websites.",
)
async def list_websites(
    pagination: PaginationParams = Depends(get_pagination_params),
    db: Session = Depends(get_db),
):
    websites, total = WebsiteService.get_websites(db, pagination.skip, pagination.limit)
    return PaginatedResponse(
        items=websites,
        total=total,
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get(
    "/{website_id}",
    response_model=WebsiteResponse,
    summary="Get a website by ID",
    description="Retrieve details of a specific website by its ID.",
)
async def get_website(
    website_id: int,
    db: Session = Depends(get_db),
):
    website = WebsiteService.get_website(db, website_id)
    if not website:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website not found")
    return website


@router.put(
    "/{website_id}",
    response_model=WebsiteResponse,
    summary="Update a website",
    description="Update an existing website's configuration.",
)
async def update_website(
    website_id: int,
    website_update: WebsiteUpdate,
    db: Session = Depends(get_db),
):
    try:
        updated_website = WebsiteService.update_website(db, website_id, website_update)
        if not updated_website:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website not found")
        return updated_website
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{website_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a website",
    description="Delete a website and all its associated monitoring data.",
)
async def delete_website(
    website_id: int,
    db: Session = Depends(get_db),
):
    success = WebsiteService.delete_website(db, website_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website not found")
