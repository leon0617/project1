from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class MonitoringResult(Base):
    __tablename__ = "monitoring_results"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    status_code = Column(Integer, nullable=True)
    response_time = Column(Float, nullable=True)
    success = Column(Integer, default=1)
    error_message = Column(Text, nullable=True)

    website = relationship("Website", back_populates="monitoring_results")
