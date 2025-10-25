import logging
from datetime import datetime, timezone
from typing import Optional, Tuple
import httpx
from sqlalchemy.orm import Session

from app.models import Website, MonitorCheck, DowntimeWindow

logger = logging.getLogger(__name__)


class MonitoringService:
    def __init__(self, timeout: float = 30.0, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries

    async def check_website(
        self, db: Session, website: Website
    ) -> Tuple[bool, Optional[int], Optional[float], Optional[str]]:
        """
        Check a website's availability and response time.
        Returns: (is_available, status_code, response_time, error_message)
        """
        start_time = datetime.now(timezone.utc)
        
        transport = httpx.AsyncHTTPTransport(retries=self.max_retries)
        async with httpx.AsyncClient(
            timeout=self.timeout,
            transport=transport,
            follow_redirects=True
        ) as client:
            try:
                response = await client.get(website.url)
                end_time = datetime.now(timezone.utc)
                response_time = (end_time - start_time).total_seconds()
                
                is_available = 200 <= response.status_code < 400
                
                logger.info(
                    f"Check completed for {website.url}: "
                    f"status={response.status_code}, "
                    f"time={response_time:.3f}s, "
                    f"available={is_available}"
                )
                
                return is_available, response.status_code, response_time, None
                
            except httpx.TimeoutException as e:
                end_time = datetime.now(timezone.utc)
                response_time = (end_time - start_time).total_seconds()
                error_msg = f"Timeout after {response_time:.1f}s"
                logger.warning(f"Timeout checking {website.url}: {e}")
                return False, None, response_time, error_msg
                
            except httpx.ConnectError as e:
                end_time = datetime.now(timezone.utc)
                response_time = (end_time - start_time).total_seconds()
                error_msg = f"Connection error: {str(e)}"
                logger.warning(f"Connection error checking {website.url}: {e}")
                return False, None, response_time, error_msg
                
            except Exception as e:
                end_time = datetime.now(timezone.utc)
                response_time = (end_time - start_time).total_seconds()
                error_msg = f"Unexpected error: {str(e)}"
                logger.error(f"Unexpected error checking {website.url}: {e}", exc_info=True)
                return False, None, response_time, error_msg

    async def perform_check(self, db: Session, website: Website) -> MonitorCheck:
        """
        Perform a monitor check and persist the result.
        Also manages downtime windows.
        """
        logger.debug(f"Starting check for website: {website.name} ({website.url})")
        
        try:
            is_available, status_code, response_time, error_message = await self.check_website(
                db, website
            )
            
            # Create monitor check record
            monitor_check = MonitorCheck(
                website_id=website.id,
                timestamp=datetime.now(timezone.utc),
                status_code=status_code,
                response_time=response_time,
                is_available=is_available,
                error_message=error_message,
            )
            db.add(monitor_check)
            
            # Manage downtime windows
            await self._manage_downtime_window(db, website, is_available)
            
            db.commit()
            db.refresh(monitor_check)
            
            logger.info(
                f"Check persisted for {website.name}: "
                f"available={is_available}, status={status_code}"
            )
            
            return monitor_check
            
        except Exception as e:
            logger.error(
                f"Error persisting check for {website.name}: {e}",
                exc_info=True
            )
            db.rollback()
            raise

    async def _manage_downtime_window(
        self, db: Session, website: Website, is_available: bool
    ):
        """
        Open or close downtime windows based on availability state transitions.
        """
        # Get the most recent open downtime window
        open_window = (
            db.query(DowntimeWindow)
            .filter(
                DowntimeWindow.website_id == website.id,
                DowntimeWindow.end_time.is_(None)
            )
            .first()
        )
        
        if not is_available and open_window is None:
            # Website just went down, open a new downtime window
            downtime_window = DowntimeWindow(
                website_id=website.id,
                start_time=datetime.now(timezone.utc),
            )
            db.add(downtime_window)
            logger.warning(
                f"Downtime window opened for {website.name} at {downtime_window.start_time}"
            )
            
        elif is_available and open_window is not None:
            # Website just came back up, close the downtime window
            end_time = datetime.now(timezone.utc)
            open_window.end_time = end_time
            
            # Ensure start_time is timezone-aware (SQLite may strip timezone info)
            start_time = open_window.start_time
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)
            
            duration = (end_time - start_time).total_seconds()
            logger.info(
                f"Downtime window closed for {website.name}. "
                f"Duration: {duration:.1f}s"
            )


monitoring_service = MonitoringService()
