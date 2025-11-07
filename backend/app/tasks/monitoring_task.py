"""
Website monitoring task implementation using Playwright.

This module provides functionality to:
- Check website availability and response time
- Record monitoring results to the database
- Support both regular monitoring and debug session modes
"""

import asyncio
import logging
import time
from typing import Optional
from datetime import datetime, timezone

from playwright.async_api import async_playwright, Browser, Page, Error as PlaywrightError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.website import Website
from app.models.monitoring_result import MonitoringResult
from app.services.debug_service import DebugService

logger = logging.getLogger(__name__)


class MonitoringTask:
    """Handles website monitoring using Playwright."""

    _browser: Optional[Browser] = None
    _lock = asyncio.Lock()

    @classmethod
    async def get_browser(cls) -> Browser:
        """Get or create a shared browser instance."""
        async with cls._lock:
            if cls._browser is None or not cls._browser.is_connected():
                logger.info(f"Launching {settings.playwright_browser} browser (headless={settings.playwright_headless})")
                playwright = await async_playwright().start()
                cls._browser = await playwright.chromium.launch(
                    headless=settings.playwright_headless,
                    executable_path=settings.playwright_executable_path,
                )
            return cls._browser

    @classmethod
    async def close_browser(cls):
        """Close the browser instance."""
        async with cls._lock:
            if cls._browser is not None:
                await cls._browser.close()
                cls._browser = None
                logger.info("Browser closed")

    @staticmethod
    async def check_website(
        website: Website,
        db: Session,
        debug_session_id: Optional[int] = None
    ) -> MonitoringResult:
        """
        Check a website and record the result.

        Args:
            website: Website object to check
            db: Database session
            debug_session_id: Optional debug session ID for capturing network events

        Returns:
            MonitoringResult object
        """
        logger.info(f"Checking website: {website.name} ({website.url})")

        start_time = time.time()
        status_code = None
        success = False
        error_message = None
        network_events = []

        try:
            browser = await MonitoringTask.get_browser()
            context = await browser.new_context(
                user_agent="Project1-Monitor/1.0",
                viewport={"width": 1920, "height": 1080},
            )

            page = await context.new_page()

            # Set up network event listener for debug sessions
            if debug_session_id:
                async def handle_response(response):
                    try:
                        # Capture network event
                        request = response.request
                        event_data = {
                            'method': request.method,
                            'url': request.url,
                            'status_code': response.status,
                            'headers': dict(response.headers),
                            'request_body': request.post_data if request.method in ['POST', 'PUT', 'PATCH'] else None,
                            'response_body': None,  # We'll skip body for performance
                            'duration': None,  # Will be calculated if needed
                        }
                        network_events.append(event_data)
                    except Exception as e:
                        logger.warning(f"Error capturing network event: {e}")

                page.on("response", handle_response)

            # Navigate to the website
            try:
                response = await page.goto(
                    website.url,
                    wait_until="domcontentloaded",
                    timeout=30000,  # 30 seconds timeout
                )

                if response:
                    status_code = response.status
                    success = 200 <= status_code < 400
                else:
                    error_message = "No response received"

            except PlaywrightError as e:
                error_message = f"Navigation error: {str(e)[:200]}"
                logger.warning(f"Failed to navigate to {website.url}: {e}")

            await context.close()

        except Exception as e:
            error_message = f"Monitoring error: {str(e)[:200]}"
            logger.error(f"Error checking website {website.url}: {e}")

        # Calculate response time
        response_time = time.time() - start_time

        # Create monitoring result
        monitoring_result = MonitoringResult(
            website_id=website.id,
            status_code=status_code,
            response_time=response_time,
            success=int(success),
            error_message=error_message,
        )

        db.add(monitoring_result)
        db.commit()
        db.refresh(monitoring_result)

        logger.info(
            f"Website check completed: {website.name} - "
            f"Status: {status_code or 'N/A'}, "
            f"Time: {response_time:.2f}s, "
            f"Success: {success}"
        )

        # Store network events if in debug mode
        if debug_session_id and network_events:
            logger.info(f"Captured {len(network_events)} network events for debug session {debug_session_id}")
            for event_data in network_events:
                try:
                    await DebugService.add_network_event(db, debug_session_id, event_data)
                except Exception as e:
                    logger.error(f"Failed to store network event: {e}")

        return monitoring_result

    @staticmethod
    async def check_all_enabled_websites():
        """
        Check all enabled websites.

        This is the main task that should be scheduled to run periodically.
        """
        logger.info("Starting periodic website monitoring check")

        db = SessionLocal()
        try:
            # Get all enabled websites
            websites = db.query(Website).filter(Website.enabled == True).all()

            if not websites:
                logger.info("No enabled websites to monitor")
                return

            logger.info(f"Monitoring {len(websites)} websites")

            # Check each website
            for website in websites:
                try:
                    # Check if there's an active debug session for this website
                    from app.models.debug_session import DebugSession
                    debug_session = db.query(DebugSession).filter(
                        DebugSession.website_id == website.id,
                        DebugSession.status == "active"
                    ).first()

                    debug_session_id = debug_session.id if debug_session else None

                    # Perform the check
                    await MonitoringTask.check_website(
                        website,
                        db,
                        debug_session_id=debug_session_id
                    )

                except Exception as e:
                    logger.error(f"Failed to check website {website.url}: {e}")

        finally:
            db.close()

        logger.info("Periodic website monitoring check completed")

    @staticmethod
    async def check_website_by_id(website_id: int):
        """
        Check a specific website by ID.

        Args:
            website_id: ID of the website to check
        """
        db = SessionLocal()
        try:
            website = db.query(Website).filter(Website.id == website_id).first()

            if not website:
                logger.warning(f"Website with ID {website_id} not found")
                return

            if not website.enabled:
                logger.warning(f"Website {website.name} is disabled")
                return

            # Check if there's an active debug session
            from app.models.debug_session import DebugSession
            debug_session = db.query(DebugSession).filter(
                DebugSession.website_id == website.id,
                DebugSession.status == "active"
            ).first()

            debug_session_id = debug_session.id if debug_session else None

            await MonitoringTask.check_website(
                website,
                db,
                debug_session_id=debug_session_id
            )

        finally:
            db.close()
