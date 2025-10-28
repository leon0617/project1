from typing import Generic, TypeVar, List
from pydantic import BaseModel, Field, ConfigDict

T = TypeVar('T')


class PaginationParams(BaseModel):
    skip: int = Field(default=0, ge=0, description="Number of items to skip")
    limit: int = Field(default=50, ge=1, le=100, description="Number of items to return")


class PaginatedResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(from_attributes=True)
    
    items: List[T]
    total: int
    skip: int
    limit: int


class ErrorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    detail: str
    error_code: str = None
