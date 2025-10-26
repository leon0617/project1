#!/usr/bin/env python3
"""
Script to install Playwright browser binaries.
Run this after installing dependencies to ensure browsers are available.
"""
import subprocess
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def install_playwright_browsers():
    """Install Playwright browser binaries"""
    try:
        logger.info("Installing Playwright browser binaries...")
        result = subprocess.run(
            ["python", "-m", "playwright", "install", "chromium"],
            check=True,
            capture_output=True,
            text=True,
        )
        logger.info(result.stdout)
        logger.info("Playwright browser binaries installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error installing Playwright browsers: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False


def install_system_dependencies():
    """Install system dependencies required by Playwright browsers"""
    try:
        logger.info("Installing system dependencies for Playwright...")
        result = subprocess.run(
            ["python", "-m", "playwright", "install-deps", "chromium"],
            check=True,
            capture_output=True,
            text=True,
        )
        logger.info(result.stdout)
        logger.info("System dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        logger.warning(f"Could not install system dependencies: {e.stderr}")
        logger.warning("You may need to run this with sudo or install manually")
        return False
    except Exception as e:
        logger.warning(f"Could not install system dependencies: {e}")
        return False


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Playwright Setup Script")
    logger.info("=" * 60)
    
    # Install browser binaries (required)
    if not install_playwright_browsers():
        logger.error("Failed to install Playwright browsers")
        sys.exit(1)
    
    # Try to install system dependencies (optional, may need sudo)
    logger.info("\n" + "=" * 60)
    install_system_dependencies()
    
    logger.info("\n" + "=" * 60)
    logger.info("Playwright setup complete!")
    logger.info("You can now run the application with: uvicorn app.main:app")
    logger.info("=" * 60)
