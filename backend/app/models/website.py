from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship

from app.core.database import Base


class Website(Base):
    __tablename__ = "websites"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    check_interval = Column(Integer, default=300)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    monitoring_results = relationship("MonitoringResult", back_populates="website", cascade="all, delete-orphan")
    debug_sessions = relationship("DebugSession", back_populates="website", cascade="all, delete-orphan")
