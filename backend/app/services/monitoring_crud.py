from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_

from app.models.monitoring import (
    Website,
    MonitorCheck,
    DowntimeWindow,
    DebugSession,
    NetworkEvent,
    MonitorStatus,
)
from app.schemas.monitoring import (
    WebsiteCreate,
    WebsiteUpdate,
    MonitorCheckCreate,
    DowntimeWindowCreate,
    DowntimeWindowUpdate,
    DebugSessionCreate,
    DebugSessionUpdate,
    NetworkEventCreate,
)


class WebsiteCRUD:
    """CRUD operations for Website model"""

    @staticmethod
    def create(db: Session, website: WebsiteCreate) -> Website:
        db_website = Website(**website.model_dump())
        db.add(db_website)
        db.commit()
        db.refresh(db_website)
        return db_website

    @staticmethod
    def get_by_id(db: Session, website_id: int) -> Optional[Website]:
        return db.query(Website).filter(Website.id == website_id).first()

    @staticmethod
    def get_by_url(db: Session, url: str) -> Optional[Website]:
        return db.query(Website).filter(Website.url == url).first()

    @staticmethod
    def get_all(
        db: Session, skip: int = 0, limit: int = 100, active_only: bool = False
    ) -> Tuple[List[Website], int]:
        query = db.query(Website)
        if active_only:
            query = query.filter(Website.is_active == True)
        
        total = query.count()
        items = query.order_by(Website.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    @staticmethod
    def get_active_websites(db: Session) -> List[Website]:
        """Fetch all active websites for monitoring"""
        return db.query(Website).filter(Website.is_active == True).all()

    @staticmethod
    def update(
        db: Session, website_id: int, website_update: WebsiteUpdate
    ) -> Optional[Website]:
        db_website = WebsiteCRUD.get_by_id(db, website_id)
        if not db_website:
            return None
        
        update_data = website_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_website, field, value)
        
        db_website.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_website)
        return db_website

    @staticmethod
    def delete(db: Session, website_id: int) -> bool:
        db_website = WebsiteCRUD.get_by_id(db, website_id)
        if not db_website:
            return False
        
        db.delete(db_website)
        db.commit()
        return True


class MonitorCheckCRUD:
    """CRUD operations for MonitorCheck model"""

    @staticmethod
    def create(db: Session, check: MonitorCheckCreate) -> MonitorCheck:
        check_data = check.model_dump()
        if check_data.get("checked_at") is None:
            check_data["checked_at"] = datetime.utcnow()
        
        db_check = MonitorCheck(**check_data)
        db.add(db_check)
        db.commit()
        db.refresh(db_check)
        return db_check

    @staticmethod
    def get_by_id(db: Session, check_id: int) -> Optional[MonitorCheck]:
        return db.query(MonitorCheck).filter(MonitorCheck.id == check_id).first()

    @staticmethod
    def get_by_website(
        db: Session,
        website_id: int,
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Tuple[List[MonitorCheck], int]:
        query = db.query(MonitorCheck).filter(MonitorCheck.website_id == website_id)
        
        if start_date:
            query = query.filter(MonitorCheck.checked_at >= start_date)
        if end_date:
            query = query.filter(MonitorCheck.checked_at <= end_date)
        
        total = query.count()
        items = query.order_by(MonitorCheck.checked_at.desc()).offset(skip).limit(limit).all()
        return items, total

    @staticmethod
    def get_latest_by_website(db: Session, website_id: int) -> Optional[MonitorCheck]:
        return (
            db.query(MonitorCheck)
            .filter(MonitorCheck.website_id == website_id)
            .order_by(MonitorCheck.checked_at.desc())
            .first()
        )

    @staticmethod
    def get_recent_checks(
        db: Session, website_id: int, hours: int = 24
    ) -> List[MonitorCheck]:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return (
            db.query(MonitorCheck)
            .filter(
                and_(
                    MonitorCheck.website_id == website_id,
                    MonitorCheck.checked_at >= cutoff_time,
                )
            )
            .order_by(MonitorCheck.checked_at.desc())
            .all()
        )

    @staticmethod
    def calculate_uptime_percentage(
        db: Session, website_id: int, hours: int = 24
    ) -> Optional[float]:
        """Calculate uptime percentage for a website over a time period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        total_checks = (
            db.query(func.count(MonitorCheck.id))
            .filter(
                and_(
                    MonitorCheck.website_id == website_id,
                    MonitorCheck.checked_at >= cutoff_time,
                )
            )
            .scalar()
        )
        
        if not total_checks or total_checks == 0:
            return None
        
        up_checks = (
            db.query(func.count(MonitorCheck.id))
            .filter(
                and_(
                    MonitorCheck.website_id == website_id,
                    MonitorCheck.checked_at >= cutoff_time,
                    MonitorCheck.status == MonitorStatus.UP,
                )
            )
            .scalar()
        )
        
        return (up_checks / total_checks) * 100 if up_checks else 0.0


class DowntimeWindowCRUD:
    """CRUD operations for DowntimeWindow model"""

    @staticmethod
    def create(db: Session, downtime: DowntimeWindowCreate) -> DowntimeWindow:
        db_downtime = DowntimeWindow(**downtime.model_dump())
        db.add(db_downtime)
        db.commit()
        db.refresh(db_downtime)
        return db_downtime

    @staticmethod
    def get_by_id(db: Session, downtime_id: int) -> Optional[DowntimeWindow]:
        return db.query(DowntimeWindow).filter(DowntimeWindow.id == downtime_id).first()

    @staticmethod
    def get_by_website(
        db: Session,
        website_id: int,
        skip: int = 0,
        limit: int = 100,
        include_ongoing: bool = True,
    ) -> Tuple[List[DowntimeWindow], int]:
        query = db.query(DowntimeWindow).filter(DowntimeWindow.website_id == website_id)
        
        if not include_ongoing:
            query = query.filter(DowntimeWindow.ended_at.isnot(None))
        
        total = query.count()
        items = query.order_by(DowntimeWindow.started_at.desc()).offset(skip).limit(limit).all()
        return items, total

    @staticmethod
    def get_ongoing_downtime(db: Session, website_id: int) -> Optional[DowntimeWindow]:
        """Get the current ongoing downtime window for a website"""
        return (
            db.query(DowntimeWindow)
            .filter(
                and_(
                    DowntimeWindow.website_id == website_id,
                    DowntimeWindow.ended_at.is_(None),
                )
            )
            .order_by(DowntimeWindow.started_at.desc())
            .first()
        )

    @staticmethod
    def update(
        db: Session, downtime_id: int, downtime_update: DowntimeWindowUpdate
    ) -> Optional[DowntimeWindow]:
        db_downtime = DowntimeWindowCRUD.get_by_id(db, downtime_id)
        if not db_downtime:
            return None
        
        update_data = downtime_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_downtime, field, value)
        
        # Calculate duration if both start and end are set
        if db_downtime.ended_at and db_downtime.started_at:
            delta = db_downtime.ended_at - db_downtime.started_at
            db_downtime.duration_seconds = int(delta.total_seconds())
        
        db_downtime.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_downtime)
        return db_downtime

    @staticmethod
    def delete(db: Session, downtime_id: int) -> bool:
        db_downtime = DowntimeWindowCRUD.get_by_id(db, downtime_id)
        if not db_downtime:
            return False
        
        db.delete(db_downtime)
        db.commit()
        return True


class DebugSessionCRUD:
    """CRUD operations for DebugSession model"""

    @staticmethod
    def create(db: Session, session: DebugSessionCreate) -> DebugSession:
        db_session = DebugSession(
            **session.model_dump(),
            started_at=datetime.utcnow()
        )
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        return db_session

    @staticmethod
    def get_by_id(db: Session, session_id: int) -> Optional[DebugSession]:
        return db.query(DebugSession).filter(DebugSession.id == session_id).first()

    @staticmethod
    def get_by_session_key(db: Session, session_key: str) -> Optional[DebugSession]:
        return (
            db.query(DebugSession)
            .filter(DebugSession.session_key == session_key)
            .first()
        )

    @staticmethod
    def get_by_website(
        db: Session,
        website_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[DebugSession], int]:
        query = db.query(DebugSession).filter(DebugSession.website_id == website_id)
        
        total = query.count()
        items = query.order_by(DebugSession.started_at.desc()).offset(skip).limit(limit).all()
        return items, total

    @staticmethod
    def update(
        db: Session, session_id: int, session_update: DebugSessionUpdate
    ) -> Optional[DebugSession]:
        db_session = DebugSessionCRUD.get_by_id(db, session_id)
        if not db_session:
            return None
        
        update_data = session_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_session, field, value)
        
        db_session.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_session)
        return db_session

    @staticmethod
    def delete(db: Session, session_id: int) -> bool:
        db_session = DebugSessionCRUD.get_by_id(db, session_id)
        if not db_session:
            return False
        
        db.delete(db_session)
        db.commit()
        return True


class NetworkEventCRUD:
    """CRUD operations for NetworkEvent model"""

    @staticmethod
    def create(db: Session, event: NetworkEventCreate) -> NetworkEvent:
        event_data = event.model_dump()
        if event_data.get("timestamp") is None:
            event_data["timestamp"] = datetime.utcnow()
        
        db_event = NetworkEvent(**event_data)
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        return db_event

    @staticmethod
    def bulk_create(db: Session, events: List[NetworkEventCreate]) -> List[NetworkEvent]:
        """Bulk create network events for efficiency"""
        db_events = []
        for event in events:
            event_data = event.model_dump()
            if event_data.get("timestamp") is None:
                event_data["timestamp"] = datetime.utcnow()
            db_events.append(NetworkEvent(**event_data))
        
        db.add_all(db_events)
        db.commit()
        for db_event in db_events:
            db.refresh(db_event)
        return db_events

    @staticmethod
    def get_by_id(db: Session, event_id: int) -> Optional[NetworkEvent]:
        return db.query(NetworkEvent).filter(NetworkEvent.id == event_id).first()

    @staticmethod
    def get_by_session(
        db: Session,
        session_id: int,
        skip: int = 0,
        limit: int = 1000,
    ) -> Tuple[List[NetworkEvent], int]:
        query = db.query(NetworkEvent).filter(NetworkEvent.debug_session_id == session_id)
        
        total = query.count()
        items = query.order_by(NetworkEvent.timestamp.asc()).offset(skip).limit(limit).all()
        return items, total

    @staticmethod
    def get_by_time_range(
        db: Session,
        session_id: int,
        start_time: datetime,
        end_time: datetime,
    ) -> List[NetworkEvent]:
        """Get network events within a specific time range"""
        return (
            db.query(NetworkEvent)
            .filter(
                and_(
                    NetworkEvent.debug_session_id == session_id,
                    NetworkEvent.timestamp >= start_time,
                    NetworkEvent.timestamp <= end_time,
                )
            )
            .order_by(NetworkEvent.timestamp.asc())
            .all()
        )

    @staticmethod
    def delete(db: Session, event_id: int) -> bool:
        db_event = NetworkEventCRUD.get_by_id(db, event_id)
        if not db_event:
            return False
        
        db.delete(db_event)
        db.commit()
        return True
