"""
Logging system with headless and UI modes
"""

import logging
import sys
import os
from pathlib import Path
from typing import Optional, Callable
from logging.handlers import RotatingFileHandler
import colorama
from colorama import Fore, Back, Style

from config.settings import EngineSettings

colorama.init(autoreset=True)


class LoggerMode:
    """
    Logger mode configuration
    """
    HEADLESS = "headless"
    UI = "ui"
    
    _current_mode = HEADLESS
    _ui_callback = None
    
    @classmethod
    def set_mode(cls, mode: str, ui_callback: Optional[Callable] = None):
        """
        Set logger mode
        """
        cls._current_mode = mode
        if mode == cls.UI and ui_callback:
            cls._ui_callback = ui_callback
    
    @classmethod
    def get_mode(cls) -> str:
        """
        Get current mode
        """
        return cls._current_mode
    
    @classmethod
    def get_ui_callback(cls) -> Optional[Callable]:
        """
        Get UI callback
        """
        return cls._ui_callback
    
    @classmethod
    def is_headless(cls) -> bool:
        """
        Check if headless mode
        """
        return cls._current_mode == cls.HEADLESS


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
        if LoggerMode.is_headless():
            record.levelname = f"{log_color}{record.levelname}{Style.RESET_ALL}"
            record.name = f"{Fore.BLUE}{record.name}{Style.RESET_ALL}"
        return super().format(record)


class UILogHandler(logging.Handler):
    """
    Handler for sending logs to UI
    """
    
    def __init__(self):
        super().__init__()
        self.setLevel(logging.INFO)
    
    def emit(self, record):
        """
        Send log record to UI
        """
        try:
            ui_callback = LoggerMode.get_ui_callback()
            if ui_callback and not LoggerMode.is_headless():
                msg = self.format(record)
                timestamp = self.formatter.formatTime(record, '%H:%M:%S') if self.formatter else ''
                ui_callback(record.levelname, msg, timestamp)
        except Exception:
            pass


def setup_logger(name: str) -> logging.Logger:
    """
    Setup logger with configuration
    """
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    level = getattr(logging, EngineSettings.LOGGING.level.upper(), logging.INFO)
    logger.setLevel(level)
    
    mode = LoggerMode.get_mode()
    
    if mode == LoggerMode.HEADLESS:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        console_formatter = ColoredFormatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        def flush_stdout():
            try:
                sys.stdout.flush()
            except:
                pass
        console_handler.flush = flush_stdout
        
    elif mode == LoggerMode.UI:
        ui_handler = UILogHandler()
        ui_handler.setLevel(level)
        
        ui_formatter = logging.Formatter('%(name)s: %(message)s')
        ui_handler.setFormatter(ui_formatter)
        logger.addHandler(ui_handler)
    
    if EngineSettings.LOGGING.file_output:
        try:
            log_dir = Path(EngineSettings.LOGGING.log_directory)
            log_dir.mkdir(parents=True, exist_ok=True)
            
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
        except Exception as e:
            print(f"Warning: Could not setup file logging: {e}", file=sys.stderr)
    
    logger.propagate = False
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get configured logger
    """
    return setup_logger(name)


def set_headless_mode():
    """
    Set logger to headless mode
    """
    LoggerMode.set_mode(LoggerMode.HEADLESS)


def set_ui_mode(ui_callback: Callable):
    """
    Set logger to UI mode
    """
    LoggerMode.set_mode(LoggerMode.UI, ui_callback)


class OSCLogger:
    """
    Specialized logger for OSC messages with immediate output
    """
    
    def __init__(self):
        self.logger = setup_logger("OSC")
        self.message_count = 0
    
    def log_message(self, address: str, args: tuple):
        """
        Log OSC message with immediate flush
        """
        self.message_count += 1
        args_str = ' '.join(str(arg) for arg in args) if args else ''
        msg = f"OSC {address} {args_str}"
        
        if LoggerMode.is_headless():
            print(msg, flush=True)
        else:
            self.logger.info(msg)
    
    def log_error(self, message: str):
        """
        Log OSC error with immediate output
        """
        if LoggerMode.is_headless():
            print(f"OSC ERROR: {message}", flush=True)
        else:
            self.logger.error(message)
    
    def get_stats(self) -> dict:
        """
        Get OSC logging statistics
        """
        return {
            "message_count": self.message_count
        }