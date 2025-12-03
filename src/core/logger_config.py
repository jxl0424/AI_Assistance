"""
Centralized Logging Configuration for JARVIS
Provides consistent logging across all modules
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Add color to level name
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


def setup_logging(
    log_dir="logs",
    log_file="jarvis.log",
    level=logging.INFO,
    console_level=logging.INFO,
    max_bytes=10*1024*1024,  # 10MB
    backup_count=5
):
    """
    Setup centralized logging for JARVIS
    
    Args:
        log_dir: Directory for log files
        log_file: Name of log file
        level: Logging level for file
        console_level: Logging level for console
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
        
    Returns:
        logging.Logger: Configured root logger
    """
    
    # Create logs directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Capture everything, filter at handler level
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_path / log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    
    # File format: detailed with timestamp
    file_format = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    
    # Console format: simpler, with colors
    console_format = ColoredFormatter(
        '%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Log startup
    logger.info("="*70)
    logger.info(f"JARVIS Logging System Initialized - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Log file: {log_path / log_file}")
    logger.info(f"Log level (file): {logging.getLevelName(level)}")
    logger.info(f"Log level (console): {logging.getLevelName(console_level)}")
    logger.info("="*70)
    
    return logger


def get_logger(name):
    """
    Get a logger for a specific module
    
    Args:
        name: Name of the module (usually __name__)
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)


# Convenience function for quick setup
def init_jarvis_logging(debug=False):
    """
    Initialize JARVIS logging with default settings
    
    Args:
        debug: If True, set console to DEBUG level
        
    Returns:
        logging.Logger: Root logger
    """
    console_level = logging.DEBUG if debug else logging.INFO
    
    return setup_logging(
        log_dir="logs",
        log_file="jarvis.log",
        level=logging.DEBUG,  # File always gets DEBUG
        console_level=console_level,
        max_bytes=10*1024*1024,  # 10MB
        backup_count=5
    )


if __name__ == "__main__":
    # Test the logging system
    print("Testing JARVIS Logging System...\n")
    
    # Initialize logging
    init_jarvis_logging(debug=True)
    
    # Get loggers for different modules
    main_logger = get_logger("main")
    llm_logger = get_logger("llm_core")
    stt_logger = get_logger("speech_to_text")
    
    # Test different log levels
    main_logger.debug("This is a DEBUG message")
    main_logger.info("This is an INFO message")
    main_logger.warning("This is a WARNING message")
    main_logger.error("This is an ERROR message")
    main_logger.critical("This is a CRITICAL message")
    
    # Test with different modules
    llm_logger.info("LLM processing user input")
    stt_logger.info("Transcribing audio")
    
    # Test exception logging
    try:
        result = 1 / 0
    except Exception as e:
        main_logger.error("Error in calculation", exc_info=True)
    
    print("\nLogging test complete!")
    print("Check logs/jarvis.log for detailed output")
