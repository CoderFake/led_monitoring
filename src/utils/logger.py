"""
Logging system - Logging system for engine
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler
import colorama
from colorama import Fore, Back, Style

from config.settings import EngineSettings

colorama.init()


class ColoredFormatter(logging.Formatter):
    """
    Formatter with color for console output
    """
    
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Back.WHITE
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{log_color}{record.levelname}{Style.RESET_ALL}"
        record.name = f"{Fore.BLUE}{record.name}{Style.RESET_ALL}"
        return super().format(record)


def setup_logger(name: str) -> logging.Logger:
    """
    Setup logger with configuration from settings
    """
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    level = getattr(logging, EngineSettings.LOGGING.level.upper(), logging.INFO)
    logger.setLevel(level)
    
    if EngineSettings.LOGGING.console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        console_formatter = ColoredFormatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        console_handler.flush = lambda: sys.stdout.flush()
    
    if EngineSettings.LOGGING.file_output:
        log_dir = Path(EngineSettings.LOGGING.log_directory)
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / "led_engine.log"
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,
            backupCount=EngineSettings.LOGGING.max_log_files
        )
        file_handler.setLevel(level)
        
        file_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    logger.propagate = (name != "root")
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get logger that has been setup
    """
    return logging.getLogger(name)


class OSCLogger:
    """
    Logger specialized for OSC messages
    """
    
    def __init__(self):
        self.logger = setup_logger("OSC")
        self.message_count = 0
    
    def log_message(self, address: str, args: tuple):
        """
        Log OSC message with standard format
        """
        self.message_count += 1
        args_str = ' '.join(str(arg) for arg in args) if args else ''
        self.logger.info(f"{address} {args_str}")
    
    def log_error(self, message: str):
        """
        Log OSC error
        """
        self.logger.error(message)
    
    def get_stats(self) -> dict:
        """
        Get OSC logging statistics
        """
        return {
            "message_count": self.message_count
        }