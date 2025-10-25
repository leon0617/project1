from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import Website, WebsiteCreate, WebsiteUpdate
from app.services import website_crud, scheduler_service

router = APIRouter()


@router.get("/websites", response_model=List[Website])
def list_websites(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all websites."""
    websites = website_crud.get_websites(db, skip=skip, limit=limit)
    return websites


@router.get("/websites/{website_id}", response_model=Website)
def get_website(website_id: int, db: Session = Depends(get_db)):
    """Get a specific website by ID."""
    website = website_crud.get_website(db, website_id)
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Website with ID {website_id} not found"
        )
    return website


@router.post("/websites", response_model=Website, status_code=status.HTTP_201_CREATED)
def create_website(
    website: WebsiteCreate,
    db: Session = Depends(get_db)
):
    """Create a new website to monitor."""
    # Check if URL already exists
    existing = website_crud.get_website_by_url(db, website.url)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Website with URL {website.url} already exists"
        )
    
    db_website = website_crud.create_website(db, website)
    
    # Add job to scheduler if enabled
    if db_website.enabled:
        scheduler_service.add_or_update_job(db_website)
    
    return db_website


@router.patch("/websites/{website_id}", response_model=Website)
def update_website(
    website_id: int,
    website_update: WebsiteUpdate,
    db: Session = Depends(get_db)
):
    """Update a website's configuration."""
    db_website = website_crud.update_website(db, website_id, website_update)
    if not db_website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Website with ID {website_id} not found"
        )
    
    # Update or remove job in scheduler
    if db_website.enabled:
        scheduler_service.add_or_update_job(db_website)
    else:
        scheduler_service.remove_job(website_id)
    
    return db_website


@router.delete("/websites/{website_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_website(website_id: int, db: Session = Depends(get_db)):
    """Delete a website."""
    success = website_crud.delete_website(db, website_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Website with ID {website_id} not found"
        )
    
    # Remove job from scheduler
    scheduler_service.remove_job(website_id)
    
    return None
