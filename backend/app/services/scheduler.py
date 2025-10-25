import asyncio
import logging
from typing import Dict, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from datetime import datetime, timezone

from app.core.config import settings
from app.core.database import SessionLocal
from app.models import Website
from app.services.monitoring import monitoring_service
from app.services.website_crud import get_active_websites

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Simple circuit breaker to handle repeated failures."""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 300):
        self.failure_threshold = failure_threshold
        self.timeout = timeout  # seconds
        self.failures: Dict[int, int] = {}
        self.blocked_until: Dict[int, datetime] = {}
    
    def record_failure(self, website_id: int) -> None:
        """Record a failure for a website."""
        self.failures[website_id] = self.failures.get(website_id, 0) + 1
        
        if self.failures[website_id] >= self.failure_threshold:
            self.blocked_until[website_id] = datetime.now(timezone.utc).timestamp() + self.timeout
            logger.warning(
                f"Circuit breaker opened for website {website_id}. "
                f"Blocked for {self.timeout}s after {self.failures[website_id]} failures."
            )
    
    def record_success(self, website_id: int) -> None:
        """Record a successful check."""
        if website_id in self.failures:
            del self.failures[website_id]
        if website_id in self.blocked_until:
            del self.blocked_until[website_id]
    
    def is_blocked(self, website_id: int) -> bool:
        """Check if a website is currently blocked."""
        if website_id not in self.blocked_until:
            return False
        
        if datetime.now(timezone.utc).timestamp() >= self.blocked_until[website_id]:
            # Timeout expired, reset
            del self.blocked_until[website_id]
            self.failures[website_id] = 0
            logger.info(f"Circuit breaker closed for website {website_id}")
            return False
        
        return True


class SchedulerService:
    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.circuit_breaker = CircuitBreaker()
        self.job_ids: Dict[int, str] = {}  # website_id -> job_id mapping
    
    def start(self) -> None:
        """Initialize and start the scheduler."""
        if not settings.scheduler_enabled:
            logger.info("Scheduler is disabled in settings")
            return
        
        logger.info("Initializing APScheduler...")
        
        self.scheduler = AsyncIOScheduler(timezone=settings.scheduler_timezone)
        
        # Add event listeners
        self.scheduler.add_listener(
            self._job_executed_listener,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
        )
        
        self.scheduler.start()
        logger.info("APScheduler started successfully")
        
        # Schedule initial sync of all active websites
        self.sync_jobs()
    
    def stop(self) -> None:
        """Stop the scheduler."""
        if self.scheduler:
            logger.info("Shutting down APScheduler...")
            self.scheduler.shutdown()
            logger.info("APScheduler shut down successfully")
    
    def sync_jobs(self) -> None:
        """Sync scheduler jobs with active websites in the database."""
        if not self.scheduler:
            return
        
        logger.info("Syncing scheduler jobs with database...")
        
        db = SessionLocal()
        try:
            active_websites = get_active_websites(db)
            active_website_ids = {w.id for w in active_websites}
            
            # Remove jobs for websites that are no longer active
            for website_id in list(self.job_ids.keys()):
                if website_id not in active_website_ids:
                    self.remove_job(website_id)
            
            # Add or update jobs for active websites
            for website in active_websites:
                self.add_or_update_job(website)
            
            logger.info(
                f"Sync completed: {len(active_websites)} active websites, "
                f"{len(self.job_ids)} scheduled jobs"
            )
        finally:
            db.close()
    
    def add_or_update_job(self, website: Website) -> None:
        """Add or update a monitoring job for a website."""
        if not self.scheduler:
            return
        
        job_id = f"monitor_{website.id}"
        
        # Remove existing job if it exists
        if website.id in self.job_ids:
            self.scheduler.remove_job(job_id)
        
        # Add new job with current interval
        self.scheduler.add_job(
            func=self._check_website_wrapper,
            trigger=IntervalTrigger(seconds=website.check_interval),
            id=job_id,
            name=f"Monitor {website.name}",
            args=[website.id],
            replace_existing=True,
        )
        
        self.job_ids[website.id] = job_id
        logger.info(
            f"Scheduled job for {website.name} (ID: {website.id}) "
            f"with {website.check_interval}s interval"
        )
    
    def remove_job(self, website_id: int) -> None:
        """Remove a monitoring job for a website."""
        if not self.scheduler or website_id not in self.job_ids:
            return
        
        job_id = self.job_ids[website_id]
        try:
            self.scheduler.remove_job(job_id)
            del self.job_ids[website_id]
            logger.info(f"Removed job for website {website_id}")
        except Exception as e:
            logger.error(f"Error removing job {job_id}: {e}")
    
    async def _check_website_wrapper(self, website_id: int) -> None:
        """
        Wrapper function to check a website with error handling and circuit breaker.
        """
        # Check circuit breaker
        if self.circuit_breaker.is_blocked(website_id):
            logger.debug(f"Skipping check for website {website_id} (circuit breaker open)")
            return
        
        db = SessionLocal()
        try:
            # Get website from database
            website = db.query(Website).filter(Website.id == website_id).first()
            
            if not website:
                logger.warning(f"Website {website_id} not found, removing job")
                self.remove_job(website_id)
                return
            
            if not website.enabled:
                logger.info(f"Website {website.name} is disabled, removing job")
                self.remove_job(website_id)
                return
            
            # Perform the check
            logger.debug(f"Executing check for website: {website.name}")
            await monitoring_service.perform_check(db, website)
            
            # Record success in circuit breaker
            self.circuit_breaker.record_success(website_id)
            
        except Exception as e:
            logger.error(
                f"Error checking website {website_id}: {e}",
                exc_info=True
            )
            # Record failure in circuit breaker
            self.circuit_breaker.record_failure(website_id)
            db.rollback()
        finally:
            db.close()
    
    def _job_executed_listener(self, event):
        """Listen to job execution events for logging."""
        if event.exception:
            logger.error(
                f"Job {event.job_id} failed: {event.exception}",
                exc_info=True
            )
        else:
            logger.debug(f"Job {event.job_id} completed successfully")


scheduler_service = SchedulerService()
