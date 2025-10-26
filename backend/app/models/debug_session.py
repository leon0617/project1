from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


def utc_now():
    """Get current UTC time with timezone info"""
    return datetime.now(timezone.utc)


class DebugSession(Base):
    __tablename__ = "debug_sessions"

    id = Column(Integer, primary_key=True, index=True)
    target_url = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")  # pending, active, stopped, failed
    started_at = Column(DateTime, nullable=True)
    stopped_at = Column(DateTime, nullable=True)
    duration_limit = Column(Integer, nullable=True)  # in seconds
    created_at = Column(DateTime, default=utc_now, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    network_events = relationship("NetworkEvent", back_populates="debug_session", cascade="all, delete-orphan")
    console_errors = relationship("ConsoleError", back_populates="debug_session", cascade="all, delete-orphan")


class NetworkEvent(Base):
    __tablename__ = "network_events"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("debug_sessions.id"), nullable=False, index=True)
    event_type = Column(String, nullable=False)  # request, response
    url = Column(Text, nullable=False)
    method = Column(String, nullable=True)
    status_code = Column(Integer, nullable=True)
    request_headers = Column(Text, nullable=True)  # JSON string
    response_headers = Column(Text, nullable=True)  # JSON string
    request_body = Column(Text, nullable=True)
    response_body = Column(Text, nullable=True)
    timing = Column(Float, nullable=True)  # in milliseconds
    timestamp = Column(DateTime, default=utc_now, nullable=False)
    resource_type = Column(String, nullable=True)  # document, stylesheet, image, script, etc.
    
    # Relationships
    debug_session = relationship("DebugSession", back_populates="network_events")


class ConsoleError(Base):
    __tablename__ = "console_errors"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("debug_sessions.id"), nullable=False, index=True)
    level = Column(String, nullable=False)  # error, warning, log, etc.
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=utc_now, nullable=False)
    
    # Relationships
    debug_session = relationship("DebugSession", back_populates="console_errors")
