from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, HttpUrl, Field, ConfigDict


class DebugSessionCreate(BaseModel):
    target_url: str = Field(..., description="URL to debug")
    duration_limit: Optional[int] = Field(None, description="Session duration limit in seconds", ge=1, le=3600)


class DebugSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    target_url: str
    status: str
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    duration_limit: Optional[int] = None
    created_at: datetime
    error_message: Optional[str] = None


class NetworkEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    session_id: int
    event_type: str
    url: str
    method: Optional[str] = None
    status_code: Optional[int] = None
    request_headers: Optional[str] = None
    response_headers: Optional[str] = None
    request_body: Optional[str] = None
    response_body: Optional[str] = None
    timing: Optional[float] = None
    timestamp: datetime
    resource_type: Optional[str] = None


class ConsoleErrorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    session_id: int
    level: str
    message: str
    timestamp: datetime


class DebugSessionDetailResponse(DebugSessionResponse):
    network_events: List[NetworkEventResponse] = []
    console_errors: List[ConsoleErrorResponse] = []


class NetworkEventStreamMessage(BaseModel):
    type: str = "network_event"
    session_id: int
    event: NetworkEventResponse


class ConsoleErrorStreamMessage(BaseModel):
    type: str = "console_error"
    session_id: int
    error: ConsoleErrorResponse


class SessionStatusMessage(BaseModel):
    type: str = "status"
    session_id: int
    status: str
    message: Optional[str] = None
