from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class Monitor(Base):
    __tablename__ = "monitors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    check_interval_seconds = Column(Integer, default=60)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    checks = relationship("MonitorCheck", back_populates="monitor", cascade="all, delete-orphan")
    downtime_windows = relationship("DowntimeWindow", back_populates="monitor", cascade="all, delete-orphan")


class MonitorCheck(Base):
    __tablename__ = "monitor_checks"

    id = Column(Integer, primary_key=True, index=True)
    monitor_id = Column(Integer, ForeignKey("monitors.id"), nullable=False)
    checked_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    response_time_ms = Column(Float, nullable=True)
    status_code = Column(Integer, nullable=True)
    is_up = Column(Boolean, nullable=False)
    error_message = Column(String, nullable=True)

    monitor = relationship("Monitor", back_populates="checks")

    __table_args__ = (
        Index("ix_monitor_checks_monitor_checked", "monitor_id", "checked_at"),
    )


class DowntimeWindow(Base):
    __tablename__ = "downtime_windows"

    id = Column(Integer, primary_key=True, index=True)
    monitor_id = Column(Integer, ForeignKey("monitors.id"), nullable=False)
    started_at = Column(DateTime, nullable=False, index=True)
    ended_at = Column(DateTime, nullable=True, index=True)
    failure_count = Column(Integer, default=0)
    
    monitor = relationship("Monitor", back_populates="downtime_windows")

    __table_args__ = (
        Index("ix_downtime_windows_monitor_started", "monitor_id", "started_at"),
    )
