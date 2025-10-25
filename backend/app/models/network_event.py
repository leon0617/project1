from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class NetworkEvent(Base):
    __tablename__ = "network_events"

    id = Column(Integer, primary_key=True, index=True)
    debug_session_id = Column(Integer, ForeignKey("debug_sessions.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    method = Column(String, nullable=False)
    url = Column(String, nullable=False)
    status_code = Column(Integer, nullable=True)
    headers = Column(Text, nullable=True)
    request_body = Column(Text, nullable=True)
    response_body = Column(Text, nullable=True)
    duration = Column(Integer, nullable=True)

    debug_session = relationship("DebugSession", back_populates="network_events")
