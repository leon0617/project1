from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.website import Website
from app.schemas.website import WebsiteCreate, WebsiteUpdate


class WebsiteService:
    @staticmethod
    def create_website(db: Session, website: WebsiteCreate) -> Website:
        db_website = Website(
            url=website.url,
            name=website.name,
            check_interval=website.check_interval,
            enabled=website.enabled,
        )
        try:
            db.add(db_website)
            db.commit()
            db.refresh(db_website)
            return db_website
        except IntegrityError:
            db.rollback()
            raise ValueError(f"Website with URL {website.url} already exists")

    @staticmethod
    def get_website(db: Session, website_id: int) -> Optional[Website]:
        return db.query(Website).filter(Website.id == website_id).first()

    @staticmethod
    def get_website_by_url(db: Session, url: str) -> Optional[Website]:
        return db.query(Website).filter(Website.url == url).first()

    @staticmethod
    def get_websites(db: Session, skip: int = 0, limit: int = 50) -> tuple[List[Website], int]:
        total = db.query(Website).count()
        websites = db.query(Website).offset(skip).limit(limit).all()
        return websites, total

    @staticmethod
    def update_website(db: Session, website_id: int, website_update: WebsiteUpdate) -> Optional[Website]:
        db_website = db.query(Website).filter(Website.id == website_id).first()
        if not db_website:
            return None
        
        update_data = website_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_website, field, value)
        
        try:
            db.commit()
            db.refresh(db_website)
            return db_website
        except IntegrityError:
            db.rollback()
            raise ValueError(f"Website with URL {website_update.url} already exists")

    @staticmethod
    def delete_website(db: Session, website_id: int) -> bool:
        db_website = db.query(Website).filter(Website.id == website_id).first()
        if not db_website:
            return False
        
        db.delete(db_website)
        db.commit()
        return True
