from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class Website(Base):
    __tablename__ = "websites"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    check_interval = Column(Integer, default=300, nullable=False)  # seconds, default 5 minutes
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    monitor_checks = relationship("MonitorCheck", back_populates="website", cascade="all, delete-orphan")
    downtime_windows = relationship("DowntimeWindow", back_populates="website", cascade="all, delete-orphan")


class MonitorCheck(Base):
    __tablename__ = "monitor_checks"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    status_code = Column(Integer, nullable=True)  # None if request failed
    response_time = Column(Float, nullable=True)  # seconds
    is_available = Column(Boolean, nullable=False)
    error_message = Column(String, nullable=True)

    website = relationship("Website", back_populates="monitor_checks")


class DowntimeWindow(Base):
    __tablename__ = "downtime_windows"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True)
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    website = relationship("Website", back_populates="downtime_windows")
