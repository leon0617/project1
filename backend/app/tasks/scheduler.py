"""
Scheduler management for periodic tasks using APScheduler.

This module provides functionality to:
- Initialize and configure the APScheduler
- Schedule periodic website monitoring tasks
- Manage scheduler lifecycle (start/stop)
"""

import logging
import asyncio
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings
from app.tasks.monitoring_task import MonitoringTask

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Manages scheduled tasks using APScheduler."""

    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self._initialized = False

    def initialize(self):
        """Initialize the scheduler with configured settings."""
        if self._initialized:
            logger.warning("Scheduler already initialized")
            return

        if not settings.scheduler_enabled:
            logger.info("Scheduler is disabled in configuration")
            return

        logger.info("Initializing APScheduler")

        self.scheduler = AsyncIOScheduler(
            timezone=settings.scheduler_timezone,
            job_defaults={
                'coalesce': True,  # Combine multiple pending executions into one
                'max_instances': 1,  # Only one instance of each job runs at a time
                'misfire_grace_time': 300,  # 5 minutes grace period for missed jobs
            }
        )

        # Add the main monitoring task
        # This will check all enabled websites periodically
        self.scheduler.add_job(
            func=self._run_monitoring_task,
            trigger=IntervalTrigger(seconds=60),  # Check every 60 seconds
            id='website_monitoring',
            name='Website Monitoring Task',
            replace_existing=True,
        )

        self._initialized = True
        logger.info("Scheduler initialized successfully")

    async def _run_monitoring_task(self):
        """Wrapper to run the async monitoring task."""
        try:
            await MonitoringTask.check_all_enabled_websites()
        except Exception as e:
            logger.error(f"Error in monitoring task: {e}", exc_info=True)

    def start(self):
        """Start the scheduler."""
        if not self._initialized:
            logger.warning("Cannot start scheduler: not initialized")
            return

        if self.scheduler and not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")
            logger.info(f"Scheduled jobs: {[job.id for job in self.scheduler.get_jobs()]}")
        else:
            logger.warning("Scheduler already running or not initialized")

    def stop(self):
        """Stop the scheduler."""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("Scheduler stopped")
        else:
            logger.warning("Scheduler not running")

    def get_jobs(self):
        """Get list of scheduled jobs."""
        if self.scheduler:
            return self.scheduler.get_jobs()
        return []

    async def cleanup(self):
        """Clean up resources."""
        self.stop()
        await MonitoringTask.close_browser()
        logger.info("Scheduler cleanup completed")


# Global scheduler instance
task_scheduler = TaskScheduler()
