import logging
import sys
from app.core.config import settings


def setup_logging() -> None:
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger("uvicorn.access")
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    logger = logging.getLogger("uvicorn.error")
    logger.setLevel(getattr(logging, settings.log_level.upper()))
