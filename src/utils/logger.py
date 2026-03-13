"""
Production Logging System
Comprehensive logging for all FAIR-PATH components
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

# Create logs directory
Path("logs").mkdir(exist_ok=True)

def setup_logger(name, log_file=None, level=logging.INFO):
    """
    Setup logger with file and console handlers
    
    Args:
        name: Logger name (usually __name__)
        log_file: Log file path (optional)
        level: Logging level
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Format
    formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# Application-wide loggers
app_logger = setup_logger('fair_path', f'logs/fair_path_{datetime.now().strftime("%Y%m%d")}.log')
matching_logger = setup_logger('matching', f'logs/matching_{datetime.now().strftime("%Y%m%d")}.log')
extraction_logger = setup_logger('extraction', f'logs/extraction_{datetime.now().strftime("%Y%m%d")}.log')
error_logger = setup_logger('errors', f'logs/errors_{datetime.now().strftime("%Y%m%d")}.log', level=logging.ERROR)

def log_performance(func):
    """Decorator to log function execution time"""
    import time
    
    def wrapper(*args, **kwargs):
        start = time.time()
        logger = logging.getLogger(func.__module__)
        logger.info(f"Starting {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start
            logger.info(f"Completed {func.__name__} in {elapsed:.2f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start
            logger.error(f"Failed {func.__name__} after {elapsed:.2f}s: {str(e)}")
            raise
    
    return wrapper

if __name__ == "__main__":
    # Test logging
    app_logger.info("Logging system initialized")
    matching_logger.info("Matching module ready")
    extraction_logger.info("Extraction module ready")
    print("✅ Logging system configured - logs saved to logs/")
