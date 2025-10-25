from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, HttpUrl

from app.models.monitoring import MonitorStatus, HTTPMethod, NetworkEventType


# Website Schemas
class WebsiteBase(BaseModel):
    url: str = Field(..., max_length=2048, description="Website URL to monitor")
    name: str = Field(..., max_length=255, description="Display name for the website")
    description: Optional[str] = Field(None, description="Optional description")
    check_interval: int = Field(300, ge=10, description="Check interval in seconds")
    timeout: int = Field(30, ge=1, le=300, description="Request timeout in seconds")
    is_active: bool = Field(True, description="Whether monitoring is active")


class WebsiteCreate(WebsiteBase):
    pass


class WebsiteUpdate(BaseModel):
    url: Optional[str] = Field(None, max_length=2048)
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    check_interval: Optional[int] = Field(None, ge=10)
    timeout: Optional[int] = Field(None, ge=1, le=300)
    is_active: Optional[bool] = None


class WebsiteRead(WebsiteBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WebsiteWithStats(WebsiteRead):
    total_checks: int = 0
    uptime_percentage: Optional[float] = None
    last_check_status: Optional[MonitorStatus] = None
    last_check_at: Optional[datetime] = None


# MonitorCheck Schemas
class MonitorCheckBase(BaseModel):
    website_id: int
    status: MonitorStatus
    http_status_code: Optional[int] = None
    http_method: HTTPMethod = HTTPMethod.GET
    response_time_ms: Optional[float] = None
    dns_time_ms: Optional[float] = None
    connect_time_ms: Optional[float] = None
    tls_time_ms: Optional[float] = None
    ttfb_ms: Optional[float] = None
    error_message: Optional[str] = None


class MonitorCheckCreate(MonitorCheckBase):
    checked_at: Optional[datetime] = None


class MonitorCheckRead(MonitorCheckBase):
    id: int
    checked_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# DowntimeWindow Schemas
class DowntimeWindowBase(BaseModel):
    website_id: int
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    initial_status: MonitorStatus
    recovery_status: Optional[MonitorStatus] = None
    affected_checks_count: int = 0
    root_cause: Optional[str] = None
    notes: Optional[str] = None


class DowntimeWindowCreate(BaseModel):
    website_id: int
    started_at: datetime
    initial_status: MonitorStatus
    notes: Optional[str] = None


class DowntimeWindowUpdate(BaseModel):
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    recovery_status: Optional[MonitorStatus] = None
    affected_checks_count: Optional[int] = None
    root_cause: Optional[str] = None
    notes: Optional[str] = None


class DowntimeWindowRead(DowntimeWindowBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# DebugSession Schemas
class DebugSessionBase(BaseModel):
    website_id: int
    session_key: str = Field(..., max_length=255)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    success: Optional[bool] = None
    error_message: Optional[str] = None
    user_agent: Optional[str] = Field(None, max_length=512)
    browser_type: Optional[str] = Field(None, max_length=50)


class DebugSessionCreate(BaseModel):
    website_id: int
    session_key: str = Field(..., max_length=255)
    user_agent: Optional[str] = Field(None, max_length=512)
    browser_type: Optional[str] = Field(None, max_length=50)


class DebugSessionUpdate(BaseModel):
    completed_at: Optional[datetime] = None
    success: Optional[bool] = None
    error_message: Optional[str] = None


class DebugSessionRead(DebugSessionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DebugSessionWithEvents(DebugSessionRead):
    network_events: List["NetworkEventRead"] = []


# NetworkEvent Schemas
class NetworkEventBase(BaseModel):
    debug_session_id: int
    event_type: NetworkEventType
    url: str = Field(..., max_length=2048)
    method: Optional[HTTPMethod] = None
    status_code: Optional[int] = None
    request_headers: Optional[str] = None
    response_headers: Optional[str] = None
    request_payload: Optional[str] = None
    response_payload: Optional[str] = None
    timestamp: Optional[datetime] = None
    duration_ms: Optional[float] = None
    error_message: Optional[str] = None


class NetworkEventCreate(NetworkEventBase):
    pass


class NetworkEventRead(NetworkEventBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Collection Response Schemas
class WebsiteListResponse(BaseModel):
    items: List[WebsiteRead]
    total: int
    page: int = 1
    page_size: int = 50


class MonitorCheckListResponse(BaseModel):
    items: List[MonitorCheckRead]
    total: int
    page: int = 1
    page_size: int = 50


class DowntimeWindowListResponse(BaseModel):
    items: List[DowntimeWindowRead]
    total: int
    page: int = 1
    page_size: int = 50


class DebugSessionListResponse(BaseModel):
    items: List[DebugSessionRead]
    total: int
    page: int = 1
    page_size: int = 50


class NetworkEventListResponse(BaseModel):
    items: List[NetworkEventRead]
    total: int
    page: int = 1
    page_size: int = 50
