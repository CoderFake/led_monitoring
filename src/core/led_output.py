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
        self.led_zones = EngineSettings.ANIMATION.led_zones
        self.output_enabled = True
        self.last_send_time = 0.0
        self.send_count = 0
        
    async def start(self):
        """
        Start the LED output clients.
        """
        try:
            host = EngineSettings.OSC.output_host
            base_port = EngineSettings.OSC.output_port
            
            self.clients.clear()
            
            for i, zone_count in enumerate(self.led_zones):
                try:
                    client = udp_client.SimpleUDPClient(host, base_port + i)
                    self.clients.append(client)
                    logger.debug(f"LED Client {i} → {host}:{base_port + i} ({zone_count} LEDs)")
                    
                except Exception as e:
                    logger.error(f"Error creating LED client {i}: {e}")
                    self.clients.append(None)
            
            logger.info(f"LED Output started - {len([c for c in self.clients if c])} zones")
            
        except Exception as e:
            logger.error(f"Error starting LED output: {e}")
            raise
    
    async def stop(self):
        """
        Stop the LED output.
        """
        self.output_enabled = False
        self.clients.clear()
        logger.info("LED Output stopped.")
    
    def send_led_data(self, led_colors: List[List[int]]):
        """
        Send LED data via OSC.
        """
        if not self.output_enabled or not led_colors:
            return
        
        try:
            binary_data = self._convert_to_binary(led_colors)
            
            for i, (client, data) in enumerate(zip(self.clients, binary_data)):
                if client and data:
                    client.send_message(EngineSettings.OSC.output_address, data)
            
            self.send_count += 1
            self.last_send_time = time.time()
            
        except Exception as e:
            logger.error(f"Error sending LED data: {e}")
    
    def _convert_to_binary(self, led_colors: List[List[int]]) -> List[bytes]:
        """
        Convert LED colors to binary format.
        """
        binary_data_list = []
        led_index = 0
        
        for zone_count in self.led_zones:
            zone_colors = led_colors[led_index:led_index + zone_count]
            binary_data = b""
            
            for color in zone_colors:
                if len(color) >= 3:
                    r = max(0, min(255, int(color[0])))
                    g = max(0, min(255, int(color[1])))
                    b = max(0, min(255, int(color[2])))
                else:
                    r = g = b = 0
                
                binary_data += struct.pack("BBBB", r, g, b, 0)
            
            binary_data_list.append(binary_data)
            led_index += zone_count
        
        return binary_data_list
    
    def get_stats(self) -> dict:
        """
        Get output statistics.
        """
        return {
            "enabled": self.output_enabled,
            "clients_count": len([c for c in self.clients if c]),
            "zones": len(self.led_zones),
            "total_leds": sum(self.led_zones),
            "send_count": self.send_count,
            "last_send_time": self.last_send_time
        }
