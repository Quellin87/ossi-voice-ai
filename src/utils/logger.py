"""
Structured logging configuration for Ossi Voice AI.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import logging
from pythonjsonlogger import jsonlogger
from src.utils.config import get_settings

settings = get_settings()


def setup_logger(name: str) -> logging.Logger:
    """Creates a configured logger instance."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    if logger.hasHandlers():
        logger.handlers.clear()
    
    handler = logging.StreamHandler(sys.stdout)
    
    if settings.ENVIRONMENT == "production":
        formatter = jsonlogger.JsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s',
            rename_fields={"levelname": "level", "asctime": "timestamp"}
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


if __name__ == "__main__":
    logger = setup_logger(__name__)
    
    print("\n" + "=" * 60)
    print("Testing Ossi Voice AI Logging System")
    print("=" * 60 + "\n")
    
    logger.debug("This is a DEBUG message")
    logger.info("This is an INFO message")
    logger.warning("This is a WARNING message")
    logger.error("This is an ERROR message")
    
    print("\n" + "-" * 60)
    print("Testing structured logging:")
    print("-" * 60 + "\n")
    
    logger.info("User initiated call", extra={"call_id": "call_123", "user_id": "user_456"})
    logger.info("LLM request sent", extra={"call_id": "call_123", "tokens": 150})
    
    print("\n" + "=" * 60)
    print("✅ Logging system test complete!")
    print("=" * 60 + "\n")
