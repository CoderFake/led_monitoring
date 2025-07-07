"""
LED Output - Sends LED data via OSC.
"""

import struct
import time
from typing import List
from pythonosc import udp_client

from config.settings import EngineSettings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class LEDOutput:
    """
    Handles sending LED data via OSC.
    """
    
    def __init__(self):
        self.clients = []
        self.output_enabled = True
        self.last_send_time = 0.0
        self.send_count = 0
        self.send_interval = 1.0 / 60.0 
        
    async def start(self):
        """
        Start the LED output clients.
        """
        try:
            from config.settings import EngineSettings
            
            self.clients.clear()
            
            for i, destination in enumerate(EngineSettings.ANIMATION.led_destinations):
                try:
                    client = udp_client.SimpleUDPClient(
                        destination["ip"], 
                        destination["port"]
                    )
                    self.clients.append({
                        "client": client,
                        "ip": destination["ip"],
                        "port": destination["port"],
                        "index": i
                    })
                    logger.info(f"LED Output Client {i} → {destination['ip']}:{destination['port']}")
                    
                except Exception as e:
                    logger.error(f"Error creating LED client {i}: {e}")
                    self.clients.append({
                        "client": None,
                        "ip": destination.get("ip", "unknown"),
                        "port": destination.get("port", 0),
                        "index": i
                    })
            
            logger.info(f"LED Output started - {len([c for c in self.clients if c['client']])} active clients")
            
        except Exception as e:
            logger.error(f"Error starting LED output: {e}")
            raise
    
    async def stop(self):
        """
        Stop LED output
        """
        self.output_enabled = False
        self.clients.clear()
        logger.info("LED Output stopped.")
    
    def send_led_data(self, led_colors: List[List[int]]):
        """
        Send LED serial array via OSC to all destinations
        """
        if not self.output_enabled or not led_colors:
            return
        
        current_time = time.time()
        if current_time - self.last_send_time < self.send_interval:
            return
            
        try:
            binary_data = self._convert_to_binary(led_colors)
            
            successful_sends = 0
            for client_info in self.clients:
                if client_info["client"]:
                    try:
                        client_info["client"].send_message(
                            EngineSettings.OSC.output_address, 
                            binary_data
                        )
                        successful_sends += 1
                    except Exception as e:
                        logger.error(f"Error sending to {client_info['ip']}:{client_info['port']}: {e}")
            
            self.send_count += 1
            self.last_send_time = current_time
            
            if successful_sends > 0:
                logger.debug(f"LED serial sent to {successful_sends}/{len(self.clients)} devices")
            
        except Exception as e:
            logger.error(f"Error sending LED data: {e}")
    
    def _convert_to_binary(self, led_colors: List[List[int]]) -> bytes:
        """
        Convert LED colors to binary serial format
        """
        binary_data = b""
        
        for color in led_colors:
            if len(color) >= 3:
                r = max(0, min(255, int(color[0])))
                g = max(0, min(255, int(color[1])))
                b = max(0, min(255, int(color[2])))
            else:
                r = g = b = 0
            
            binary_data += struct.pack("BBBB", r, g, b, 0)
        
        return binary_data
    
    def send_to_specific_device(self, device_index: int, led_colors: List[List[int]]):
        """
        Send LED data to specific device
        """
        if 0 <= device_index < len(self.clients):
            client_info = self.clients[device_index]
            if client_info["client"]:
                try:
                    binary_data = self._convert_to_binary(led_colors)
                    client_info["client"].send_message(
                        EngineSettings.OSC.output_address,
                        binary_data
                    )
                    logger.info(f"LED serial sent to device {device_index}")
                except Exception as e:
                    logger.error(f"Error sending to device {device_index}: {e}")
    
    def get_stats(self) -> dict:
        """
        Get output statistics
        """
        active_clients = len([c for c in self.clients if c["client"]])
        
        return {
            "enabled": self.output_enabled,
            "total_devices": len(self.clients),
            "active_devices": active_clients,
            "send_count": self.send_count,
            "last_send_time": self.last_send_time,
            "send_rate_fps": 60.0,
            "devices": [
                {
                    "index": c["index"],
                    "ip": c["ip"], 
                    "port": c["port"],
                    "connected": c["client"] is not None
                }
                for c in self.clients
            ]
        }