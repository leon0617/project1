from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class DebugSessionCreate(BaseModel):
    website_id: int = Field(..., description="Website ID to debug")


class DebugSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    website_id: int
    start_time: datetime
    end_time: Optional[datetime]
    status: str


class NetworkEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    debug_session_id: int
    timestamp: datetime
    method: str
    url: str
    status_code: Optional[int]
    headers: Optional[str]
    request_body: Optional[str]
    response_body: Optional[str]
    duration: Optional[int]


class NetworkEventFilter(BaseModel):
    debug_session_id: Optional[int] = Field(None, description="Filter by debug session ID")
    start_time: Optional[datetime] = Field(None, description="Start time for filtering")
    end_time: Optional[datetime] = Field(None, description="End time for filtering")
    method: Optional[str] = Field(None, description="Filter by HTTP method")
