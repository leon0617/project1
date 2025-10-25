from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class DebugSession(Base):
    __tablename__ = "debug_sessions"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False, index=True)
    start_time = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    end_time = Column(DateTime, nullable=True)
    status = Column(String, default="active")

    website = relationship("Website", back_populates="debug_sessions")
    network_events = relationship("NetworkEvent", back_populates="debug_session", cascade="all, delete-orphan")
