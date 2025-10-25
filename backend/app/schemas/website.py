from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl, field_validator


class WebsiteBase(BaseModel):
    url: str
    name: str
    enabled: bool = True
    check_interval: int = Field(default=300, ge=60, le=3600)  # 1 minute to 1 hour


class WebsiteCreate(WebsiteBase):
    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class WebsiteUpdate(BaseModel):
    name: Optional[str] = None
    enabled: Optional[bool] = None
    check_interval: Optional[int] = Field(default=None, ge=60, le=3600)


class Website(WebsiteBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MonitorCheckBase(BaseModel):
    status_code: Optional[int] = None
    response_time: Optional[float] = None
    is_available: bool
    error_message: Optional[str] = None


class MonitorCheckCreate(MonitorCheckBase):
    website_id: int


class MonitorCheck(MonitorCheckBase):
    id: int
    website_id: int
    timestamp: datetime

    model_config = {"from_attributes": True}


class DowntimeWindowBase(BaseModel):
    start_time: datetime
    end_time: Optional[datetime] = None


class DowntimeWindowCreate(DowntimeWindowBase):
    website_id: int


class DowntimeWindow(DowntimeWindowBase):
    id: int
    website_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
