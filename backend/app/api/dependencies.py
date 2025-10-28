from typing import Optional
from fastapi import Query, Depends
from app.schemas.common import PaginationParams


def get_pagination_params(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of items to return")
) -> PaginationParams:
    return PaginationParams(skip=skip, limit=limit)


async def get_auth_stub():
    pass


class RateLimitDependency:
    def __init__(self, calls: int = 100, period: int = 60):
        self.calls = calls
        self.period = period
    
    async def __call__(self):
        pass
