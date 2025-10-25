from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class MonitoringResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    website_id: int
    timestamp: datetime
    status_code: Optional[int]
    response_time: Optional[float]
    success: int
    error_message: Optional[str]


class SLAMetrics(BaseModel):
    website_id: int
    website_name: str
    uptime_percentage: float = Field(..., description="Uptime percentage")
    total_checks: int = Field(..., description="Total number of checks")
    successful_checks: int = Field(..., description="Number of successful checks")
    failed_checks: int = Field(..., description="Number of failed checks")
    average_response_time: Optional[float] = Field(None, description="Average response time in seconds")
    start_date: datetime
    end_date: datetime


class SLAAnalyticsRequest(BaseModel):
    website_id: Optional[int] = Field(None, description="Filter by website ID")
    start_date: Optional[datetime] = Field(None, description="Start date for analytics")
    end_date: Optional[datetime] = Field(None, description="End date for analytics")
