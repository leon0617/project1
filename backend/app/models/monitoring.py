from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Float,
    Text,
    ForeignKey,
    Index,
    UniqueConstraint,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class MonitorStatus(str, enum.Enum):
    UP = "up"
    DOWN = "down"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class HTTPMethod(str, enum.Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class NetworkEventType(str, enum.Enum):
    REQUEST = "request"
    RESPONSE = "response"
    ERROR = "error"
    REDIRECT = "redirect"
    TIMEOUT = "timeout"


class Website(Base):
    __tablename__ = "websites"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(2048), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    check_interval = Column(Integer, nullable=False, default=300)
    timeout = Column(Integer, nullable=False, default=30)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    
    # Audit timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    monitor_checks = relationship(
        "MonitorCheck",
        back_populates="website",
        cascade="all, delete-orphan",
        order_by="MonitorCheck.checked_at.desc()"
    )
    downtime_windows = relationship(
        "DowntimeWindow",
        back_populates="website",
        cascade="all, delete-orphan",
        order_by="DowntimeWindow.started_at.desc()"
    )
    debug_sessions = relationship(
        "DebugSession",
        back_populates="website",
        cascade="all, delete-orphan",
        order_by="DebugSession.started_at.desc()"
    )

    __table_args__ = (
        Index("ix_websites_active_url", "is_active", "url"),
    )


class MonitorCheck(Base):
    __tablename__ = "monitor_checks"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(SQLEnum(MonitorStatus), nullable=False, default=MonitorStatus.UNKNOWN)
    
    # HTTP details
    http_status_code = Column(Integer, nullable=True)
    http_method = Column(SQLEnum(HTTPMethod), nullable=False, default=HTTPMethod.GET)
    
    # Timing details
    response_time_ms = Column(Float, nullable=True)
    dns_time_ms = Column(Float, nullable=True)
    connect_time_ms = Column(Float, nullable=True)
    tls_time_ms = Column(Float, nullable=True)
    ttfb_ms = Column(Float, nullable=True)
    
    # Error details
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    checked_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    website = relationship("Website", back_populates="monitor_checks")

    __table_args__ = (
        Index("ix_monitor_checks_website_checked", "website_id", "checked_at"),
        Index("ix_monitor_checks_status_checked", "status", "checked_at"),
    )


class DowntimeWindow(Base):
    __tablename__ = "downtime_windows"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Downtime period
    started_at = Column(DateTime, nullable=False, index=True)
    ended_at = Column(DateTime, nullable=True, index=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Downtime details
    initial_status = Column(SQLEnum(MonitorStatus), nullable=False)
    recovery_status = Column(SQLEnum(MonitorStatus), nullable=True)
    affected_checks_count = Column(Integer, nullable=False, default=0)
    
    # Root cause
    root_cause = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    website = relationship("Website", back_populates="downtime_windows")

    __table_args__ = (
        Index("ix_downtime_windows_website_started", "website_id", "started_at"),
        Index("ix_downtime_windows_ongoing", "website_id", "ended_at"),
    )


class DebugSession(Base):
    __tablename__ = "debug_sessions"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Session details
    session_key = Column(String(255), unique=True, nullable=False, index=True)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Debug results
    success = Column(Boolean, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Metadata
    user_agent = Column(String(512), nullable=True)
    browser_type = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    website = relationship("Website", back_populates="debug_sessions")
    network_events = relationship(
        "NetworkEvent",
        back_populates="debug_session",
        cascade="all, delete-orphan",
        order_by="NetworkEvent.timestamp.asc()"
    )

    __table_args__ = (
        Index("ix_debug_sessions_website_started", "website_id", "started_at"),
    )


class NetworkEvent(Base):
    __tablename__ = "network_events"

    id = Column(Integer, primary_key=True, index=True)
    debug_session_id = Column(
        Integer,
        ForeignKey("debug_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Event details
    event_type = Column(SQLEnum(NetworkEventType), nullable=False, index=True)
    url = Column(String(2048), nullable=False)
    method = Column(SQLEnum(HTTPMethod), nullable=True)
    
    # HTTP details
    status_code = Column(Integer, nullable=True)
    request_headers = Column(Text, nullable=True)
    response_headers = Column(Text, nullable=True)
    
    # Payload snippets (truncated for storage)
    request_payload = Column(Text, nullable=True)
    response_payload = Column(Text, nullable=True)
    
    # Timing
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    duration_ms = Column(Float, nullable=True)
    
    # Error details
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    debug_session = relationship("DebugSession", back_populates="network_events")

    __table_args__ = (
        Index("ix_network_events_session_timestamp", "debug_session_id", "timestamp"),
        Index("ix_network_events_type_timestamp", "event_type", "timestamp"),
    )
