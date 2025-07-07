"""
Engine settings configuration
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from pydantic import BaseModel


class OSCConfig(BaseModel):
    """
    OSC configuration
    """
    input_host: str = "127.0.0.1"
    input_port: int = 8000
    output_address: str = "/light/serial"


class AnimationConfig(BaseModel):
    """
    Animation configuration với LED destinations
    """
    target_fps: int = 60
    led_count: int = 225
    master_brightness: int = 255
    default_dissolve_time: int = 1000
    
    led_destinations: List[Dict[str, Any]] = [
        {"ip": "192.168.11.105", "port": 7000},
    ]


class MonitorConfig(BaseModel):
    """
    Monitor UI configuration
    """
    enabled: bool = True
    web_mode: bool = False
    auto_start: bool = False 
    window_width: int = 1200
    window_height: int = 800
    refresh_rate: int = 30


class LoggingConfig(BaseModel):
    """
    Logging configuration
    """
    level: str = "INFO"
    console_output: bool = True
    file_output: bool = True
    log_directory: str = "src/data/logs"
    max_log_files: int = 10


class EngineSettings:
    """
    Main engine configuration
    """
    
    OSC = OSCConfig()
    ANIMATION = AnimationConfig()
    MONITOR = MonitorConfig()
    LOGGING = LoggingConfig()
    
    DATA_DIRECTORY = Path("src/data")
    LOGS_DIRECTORY = DATA_DIRECTORY / "logs"
    
    @classmethod
    def ensure_directories(cls):
        cls.DATA_DIRECTORY.mkdir(exist_ok=True)
        cls.LOGS_DIRECTORY.mkdir(exist_ok=True)
    
EngineSettings.ensure_directories()