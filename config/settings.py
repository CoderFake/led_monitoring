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
    output_host: str = "192.168.200.200" 
    output_port: int = 7000
    output_address: str = "/light/serial"


class AnimationConfig(BaseModel):
    """
    Animation configuration
    """
    target_fps: int = 60
    led_count: int = 225
    led_zones: List[int] = [50, 50, 50, 50, 25]
    master_brightness: int = 255
    default_dissolve_time: int = 1000


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
    SCENES_DIRECTORY = DATA_DIRECTORY / "scenes"
    LOGS_DIRECTORY = DATA_DIRECTORY / "logs"
    
    @classmethod
    def load_from_file(cls, config_path: str):
        """
        Load configuration from JSON file
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if 'osc' in data:
                cls.OSC = OSCConfig(**data['osc'])
            if 'animation' in data:
                cls.ANIMATION = AnimationConfig(**data['animation'])
            if 'monitor' in data:
                cls.MONITOR = MonitorConfig(**data['monitor'])
            if 'logging' in data:
                cls.LOGGING = LoggingConfig(**data['logging'])
                
        except Exception as e:
            print(f"Error loading config from {config_path}: {e}") 
    
    @classmethod
    def save_to_file(cls, config_path: str):
        """
        Save configuration to JSON file
        """
        data = {
            'osc': cls.OSC.model_dump(),
            'animation': cls.ANIMATION.model_dump(),
            'monitor': cls.MONITOR.model_dump(),
            'logging': cls.LOGGING.model_dump()
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def ensure_directories(cls):
        cls.DATA_DIRECTORY.mkdir(exist_ok=True)
        cls.SCENES_DIRECTORY.mkdir(exist_ok=True) 
        cls.LOGS_DIRECTORY.mkdir(exist_ok=True)


EngineSettings.ensure_directories()