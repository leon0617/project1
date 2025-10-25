from typing import List, Optional
from sqlalchemy.orm import Session

from app.models import Website
from app.schemas import WebsiteCreate, WebsiteUpdate


def get_website(db: Session, website_id: int) -> Optional[Website]:
    return db.query(Website).filter(Website.id == website_id).first()


def get_website_by_url(db: Session, url: str) -> Optional[Website]:
    return db.query(Website).filter(Website.url == url).first()


def get_websites(db: Session, skip: int = 0, limit: int = 100) -> List[Website]:
    return db.query(Website).offset(skip).limit(limit).all()


def get_active_websites(db: Session) -> List[Website]:
    return db.query(Website).filter(Website.enabled == True).all()


def create_website(db: Session, website: WebsiteCreate) -> Website:
    db_website = Website(**website.model_dump())
    db.add(db_website)
    db.commit()
    db.refresh(db_website)
    return db_website


def update_website(
    db: Session, website_id: int, website_update: WebsiteUpdate
) -> Optional[Website]:
    db_website = get_website(db, website_id)
    if db_website:
        update_data = website_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_website, field, value)
        db.commit()
        db.refresh(db_website)
    return db_website


def delete_website(db: Session, website_id: int) -> bool:
    db_website = get_website(db, website_id)
    if db_website:
        db.delete(db_website)
        db.commit()
        return True
    return False
