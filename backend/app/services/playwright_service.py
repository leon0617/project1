import logging
from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from app.core.config import settings

logger = logging.getLogger(__name__)


class PlaywrightService:
    """Manages Playwright browser lifecycle"""
    
    def __init__(self):
        self._playwright = None
        self._browser: Optional[Browser] = None
        
    async def start(self):
        """Initialize Playwright and launch browser"""
        if self._browser:
            logger.warning("Browser already running")
            return
            
        logger.info(f"Starting {settings.playwright_browser} browser (headless={settings.playwright_headless})")
        self._playwright = await async_playwright().start()
        
        browser_type = getattr(self._playwright, settings.playwright_browser)
        launch_options = {
            "headless": settings.playwright_headless,
        }
        
        if settings.playwright_executable_path:
            launch_options["executable_path"] = settings.playwright_executable_path
            
        self._browser = await browser_type.launch(**launch_options)
        logger.info("Browser started successfully")
        
    async def stop(self):
        """Close browser and cleanup"""
        if self._browser:
            await self._browser.close()
            self._browser = None
            logger.info("Browser closed")
            
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
            logger.info("Playwright stopped")
            
    async def create_context(self) -> BrowserContext:
        """Create a new browser context"""
        if not self._browser:
            await self.start()
            
        context = await self._browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        
        return context
        
    @property
    def is_running(self) -> bool:
        """Check if browser is running"""
        return self._browser is not None


# Global instance
playwright_service = PlaywrightService()
