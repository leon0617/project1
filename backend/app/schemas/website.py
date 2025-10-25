from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl, field_validator, ConfigDict


class WebsiteBase(BaseModel):
    url: str = Field(..., description="Website URL to monitor")
    name: str = Field(..., description="Display name for the website")
    check_interval: int = Field(default=300, ge=60, description="Check interval in seconds")
    enabled: bool = Field(default=True, description="Whether monitoring is enabled")

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class WebsiteCreate(WebsiteBase):
    pass


class WebsiteUpdate(BaseModel):
    url: Optional[str] = Field(None, description="Website URL to monitor")
    name: Optional[str] = Field(None, description="Display name for the website")
    check_interval: Optional[int] = Field(None, ge=60, description="Check interval in seconds")
    enabled: Optional[bool] = Field(None, description="Whether monitoring is enabled")

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class WebsiteResponse(WebsiteBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime
