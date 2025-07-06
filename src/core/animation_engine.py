"""
LED Animation Playback Engine
"""

import asyncio
import time
import threading
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass

from .scene_manager import SceneManager
from .led_output import LEDOutput
from .osc_handler import OSCHandler
from config.settings import EngineSettings
from src.utils.logger import get_logger
from src.utils.performance import PerformanceMonitor

logger = get_logger(__name__)


@dataclass
class EngineStats:
    """
    Engine statistics
    """
    target_fps: int = 60
    actual_fps: float = 0.0
    frame_count: int = 0
    active_leds: int = 0
    total_leds: int = 225
    animation_time: float = 0.0
    master_brightness: int = 255
    speed_percent: int = 100
    dissolve_time: int = 1000


class AnimationEngine:
    """
    The main LED Animation Playback Engine
    """
    
    def __init__(self):
        self.scene_manager = SceneManager()
        self.led_output = LEDOutput()
        self.osc_handler = OSCHandler(self)
        
        self.performance_monitor = PerformanceMonitor()
        self.stats = EngineStats()
        
        self.running = False
        self.animation_thread = None
        self.last_frame_time = 0.0
        self.frame_interval = 1.0 / EngineSettings.ANIMATION.target_fps
        
        self.master_brightness = EngineSettings.ANIMATION.master_brightness
        self.speed_percent = 100
        self.dissolve_time = EngineSettings.ANIMATION.default_dissolve_time
        
        self.engine_start_time = time.time()
        
        self.state_callbacks: List[Callable] = []
        self._lock = threading.RLock()
        
        self.stats.total_leds = EngineSettings.ANIMATION.led_count
        self.stats.target_fps = EngineSettings.ANIMATION.target_fps
        self.stats.master_brightness = self.master_brightness
        self.stats.speed_percent = self.speed_percent
        self.stats.dissolve_time = self.dissolve_time
        
        self._setup_osc_handlers()
        
        logger.info(f"AnimationEngine initialized - LED count: {self.stats.total_leds}, Target FPS: {self.stats.target_fps}")
    
    def _setup_osc_handlers(self):
        """
        Set up OSC message handlers
        """
        handlers = {
            "/load_json": self.handle_load_json,
            "/change_scene": self.handle_change_scene,
            "/change_effect": self.handle_change_effect,
            "/change_palette": self.handle_change_palette,
            "/set_dissolve_time": self.handle_set_dissolve_time,
            "/set_speed_percent": self.handle_set_speed_percent,
            "/master_brightness": self.handle_master_brightness
        }
        
        for address, handler in handlers.items():
            self.osc_handler.add_handler(address, handler)
        
        self.osc_handler.add_palette_handler(self.handle_palette_color)
    
    async def start(self):
        """
        Start the engine
        """
        try:
            logger.info("Starting Animation Engine...")
            
            self.engine_start_time = time.time()
            
            logger.info("Initializing Scene Manager...")
            await self.scene_manager.initialize()
            
            logger.info("Initializing LED Output...")
            await self.led_output.start()
            
            logger.info("Initializing OSC Handler...")
            await self.osc_handler.start()
            
            logger.info("Starting Animation Loop...")
            self._start_animation_loop()
            
            self.running = True
            logger.info(f"Animation Engine started successfully - Target FPS: {EngineSettings.ANIMATION.target_fps}")
            
            await asyncio.sleep(0.1)
            if not self.scene_manager.scenes:
                logger.info("No scenes loaded, attempting to load test.json...")
                try:
                    success = self.scene_manager.load_scene_from_file("test.json")
                    if not success:
                        success = self.scene_manager.load_multiple_scenes_from_file("multiple_scenes.json")
                    if success:
                        logger.info("Test scenes loaded successfully")
                        self._log_engine_status()
                except Exception as e:
                    logger.warning(f"Could not load test scenes: {e}")
            
        except Exception as e:
            logger.error(f"Error starting engine: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def _log_engine_status(self):
        """
        Log current engine status for debugging
        """
        scene_info = self.get_scene_info()
        logger.info(f"=== ENGINE STATUS ===")
        logger.info(f"Active Scene: {scene_info.get('scene_id')}")
        logger.info(f"Current Effect: {scene_info.get('effect_id')}")
        logger.info(f"Current Palette: {scene_info.get('palette_id')}")
        logger.info(f"Total Effects: {scene_info.get('total_effects')}")
        logger.info(f"Total Segments: {scene_info.get('total_segments')}")
        logger.info(f"Master Brightness: {self.master_brightness}")
        logger.info(f"Speed Percent: {self.speed_percent}%")
    
    async def stop(self):
        """
        Stop the engine
        """
        logger.info("Stopping Animation Engine...")
        
        self.running = False
        
        if self.animation_thread:
            self.animation_thread.join(timeout=1.0)
            
        await self.osc_handler.stop()
        await self.led_output.stop()
        
        logger.info("Animation Engine stopped.")
    
    def _start_animation_loop(self):
        """
        Start the animation loop in a separate thread
        """
        if self.animation_thread and self.animation_thread.is_alive():
            return
            
        self.animation_thread = threading.Thread(
            target=self._animation_loop,
            daemon=True,
            name="AnimationLoop"
        )
        self.animation_thread.start()
        logger.info("Animation loop thread started")
    
    def _animation_loop(self):
        """
        Main animation loop - FIXED frame counting and FPS calculation
        """
        self.last_frame_time = time.time()
        fps_calculation_time = self.last_frame_time
        fps_frame_count = 0
        
        logger.info(f"Animation loop started - Target interval: {self.frame_interval:.3f}s")
        
        while self.running:
            frame_start = time.time()
            
            try:
                delta_time = frame_start - self.last_frame_time
                self.last_frame_time = frame_start
                
                self._update_frame(delta_time)
                
                with self._lock:
                    self.stats.frame_count += 1
                    self.stats.animation_time = time.time() - self.engine_start_time
                
                fps_frame_count += 1
                
                if fps_frame_count >= 60:
                    fps_time_diff = frame_start - fps_calculation_time
                    if fps_time_diff > 0:
                        actual_fps = fps_frame_count / fps_time_diff
                        with self._lock:
                            self.stats.actual_fps = actual_fps
                        
                        logger.info(f"Animation loop: Frame {self.stats.frame_count}, FPS: {actual_fps:.1f}, Active LEDs: {self.stats.active_leds}, Runtime: {self.stats.animation_time:.1f}s")
                    
                    fps_calculation_time = frame_start
                    fps_frame_count = 0
                    self._update_stats()
                
            except Exception as e:
                logger.error(f"Error in animation loop: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
            
            frame_time = time.time() - frame_start
            sleep_time = max(0, self.frame_interval - frame_time)
            
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        logger.info("Animation loop stopped.")
    
    def get_stats(self) -> EngineStats:
        """
        Get the current statistics
        """
        with self._lock:
            stats_copy = EngineStats()
            stats_copy.target_fps = self.stats.target_fps
            stats_copy.actual_fps = self.stats.actual_fps
            stats_copy.frame_count = self.stats.frame_count
            
            led_colors = self.scene_manager.get_led_output()
            active_leds = sum(1 for color in led_colors if any(c > 0 for c in color[:3]))
            stats_copy.active_leds = active_leds
            stats_copy.total_leds = self.stats.total_leds
            
            stats_copy.animation_time = time.time() - self.engine_start_time
            stats_copy.master_brightness = self.stats.master_brightness
            stats_copy.speed_percent = self.stats.speed_percent
            stats_copy.dissolve_time = self.stats.dissolve_time
            return stats_copy
    
    def _update_frame(self, delta_time: float):
        """
        Update one animation frame
        """
        try:
            with self._lock:
                speed_percent = self.speed_percent
                master_brightness = self.master_brightness
            
            adjusted_delta = delta_time * (speed_percent / 100.0)
            self.scene_manager.update_animation(adjusted_delta)
            
            led_colors = self.scene_manager.get_led_output()
            
            active_leds = 0
            for color in led_colors:
                if len(color) >= 3 and any(c > 0 for c in color[:3]):
                    active_leds += 1
            
            with self._lock:
                self.stats.active_leds = active_leds
            
            if master_brightness < 255:
                brightness_factor = master_brightness / 255.0
                led_colors = [
                    [int(c * brightness_factor) for c in color]
                    for color in led_colors
                ]
            
            self.led_output.send_led_data(led_colors)
                
        except Exception as e:
            logger.error(f"Error in _update_frame: {e}")
    
    def _update_stats(self):
        """
        Update engine statistics
        """
        with self._lock:
            self.stats.target_fps = EngineSettings.ANIMATION.target_fps
            self.stats.total_leds = EngineSettings.ANIMATION.led_count
            self.stats.master_brightness = self.master_brightness
            self.stats.speed_percent = self.speed_percent
            self.stats.dissolve_time = self.dissolve_time
        
        self._notify_state_change()
    
    def add_state_callback(self, callback: Callable):
        """
        Add a callback for state changes
        """
        self.state_callbacks.append(callback)
    
    def _notify_state_change(self):
        """
        Notify that the state has changed
        """
        for callback in self.state_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in state callback: {e}")
    
    def get_scene_info(self) -> Dict[str, Any]:
        """
        Get the current scene information
        """
        return self.scene_manager.get_current_scene_info()
    
    def handle_load_json(self, address: str, *args):
        """
        Handle OSC message to load a JSON file
        """
        try:
            if not args or len(args) == 0:
                logger.warning("Missing json path argument")
                return
            
            file_path = str(args[0])
            logger.info(f"Loading JSON from: {file_path}")
            
            success = False
            
            try:
                with self._lock:
                    if "multiple" in file_path.lower() or "scenes" in file_path.lower():
                        success = self.scene_manager.load_multiple_scenes_from_file(file_path)
                        
                    if not success:
                        success = self.scene_manager.load_scene_from_file(file_path)
                        
                    if not success:
                        success = self.scene_manager.load_multiple_scenes_from_file(file_path)
                        
                    if success:
                        self._notify_state_change()
                        self._log_engine_status()
                        
            except Exception as load_error:
                logger.error(f"Error loading JSON scenes: {load_error}")
                success = False
            
            else:
                logger.error(f"Failed to load scene from: {file_path}")
                
        except Exception as e:
            logger.error(f"Error in handle_load_json: {e}")
    
    def handle_change_scene(self, address: str, *args):
        """
        Handle OSC message to change the scene
        """
        try:
            if not args or len(args) == 0:
                logger.warning("Missing scene ID argument")
                return
            
            try:
                scene_id = int(args[0])
                
                with self._lock:
                    success = self.scene_manager.switch_scene(scene_id)
                    if success:
                        self._notify_state_change()
                        self._log_engine_status()
                
                if success:
                    logger.info(f"Scene changed to: {scene_id}")
                else:
                    logger.warning(f"Failed to switch to scene: {scene_id}")
                    
            except ValueError:
                logger.error(f"Invalid scene ID: {args[0]}")
                
        except Exception as e:
            logger.error(f"Error in handle_change_scene: {e}")
    
    def handle_change_effect(self, address: str, *args):
        """
        Handle OSC message to change the effect
        """
        try:
            if not args or len(args) == 0:
                logger.warning("Missing effect ID argument")
                return
            
            try:
                effect_id = int(args[0])
                
                with self._lock:
                    success = self.scene_manager.set_effect(effect_id)
                    if success:
                        self._notify_state_change()
                        self._log_engine_status()
                
                if success:
                    logger.info(f"Effect changed to: {effect_id}")
                else:
                    logger.warning(f"Failed to set effect: {effect_id}")
                    
            except ValueError:
                logger.error(f"Invalid effect ID: {args[0]}")
                
        except Exception as e:
            logger.error(f"Error in handle_change_effect: {e}")
    
    def handle_change_palette(self, address: str, *args):
        """
        Handle OSC message to change the palette
        """
        try:
            if not args or len(args) == 0:
                logger.warning("Missing palette ID argument")
                return
            
            palette_id = str(args[0])
            
            with self._lock:
                success = self.scene_manager.set_palette(palette_id)
                if success:
                    self._notify_state_change()
            
            if success:
                logger.info(f"Palette changed to: {palette_id}")
            else:
                logger.warning(f"Failed to set palette: {palette_id}")
                
        except Exception as e:
            logger.error(f"Error in handle_change_palette: {e}")
    
    def handle_palette_color(self, palette_id: str, color_id: int, rgb: List[int]):
        """
        Handle OSC message to update a palette color
        """
        try:
            with self._lock:
                success = self.scene_manager.update_palette_color(palette_id, color_id, rgb)
                if success:
                    self._notify_state_change()
            
            if success:
                logger.info(f"Palette {palette_id} color {color_id} updated to RGB({rgb[0]},{rgb[1]},{rgb[2]})")
            else:
                logger.warning(f"Failed to update palette {palette_id} color {color_id}")
                
        except Exception as e:
            logger.error(f"Error in handle_palette_color: {e}")
    
    def handle_set_dissolve_time(self, address: str, *args):
        """
        Handle OSC message to set the dissolve time
        """
        try:
            if not args or len(args) == 0:
                logger.warning("Missing dissolve time argument")
                return
            
            try:
                dissolve_time = int(args[0])
                with self._lock:
                    self.dissolve_time = max(0, dissolve_time)
                    self._notify_state_change()
                logger.info(f"Dissolve time set to: {self.dissolve_time}ms")
                
            except ValueError:
                logger.error(f"Invalid dissolve time: {args[0]}")
                
        except Exception as e:
            logger.error(f"Error in handle_set_dissolve_time: {e}")
    
    def handle_set_speed_percent(self, address: str, *args):
        """
        Handle OSC message to set the speed percentage
        """
        try:
            if not args or len(args) == 0:
                logger.warning("Missing speed percent argument")
                return
            
            try:
                speed_percent = int(args[0])
                with self._lock:
                    self.speed_percent = max(0, min(200, speed_percent))
                    self._notify_state_change()
                logger.info(f"Animation speed set to: {self.speed_percent}%")
                
            except ValueError:
                logger.error(f"Invalid speed percent: {args[0]}")
                
        except Exception as e:
            logger.error(f"Error in handle_set_speed_percent: {e}")
    
    def handle_master_brightness(self, address: str, *args):
        """
        Handle OSC message for master brightness
        """
        try:
            if not args or len(args) == 0:
                logger.warning("Missing brightness argument")
                return
            
            try:
                brightness = int(args[0])
                with self._lock:
                    self.master_brightness = max(0, min(255, brightness))
                    self._notify_state_change()
                logger.info(f"Master brightness set to: {self.master_brightness}")
                
            except ValueError:
                logger.error(f"Invalid brightness: {args[0]}")
                
        except Exception as e:
            logger.error(f"Error in handle_master_brightness: {e}")
    
    def get_led_colors(self) -> List[List[int]]:
        """
        Get the current LED colors for display
        """
        led_colors = self.scene_manager.get_led_output()
        
        if self.master_brightness < 255:
            brightness_factor = self.master_brightness / 255.0
            led_colors = [
                [int(c * brightness_factor) for c in color]
                for color in led_colors
            ]
        
        return led_colors