"""
Scene Manager - Fixed scene loading logic
"""

import time
import threading
import json
from typing import Dict, List, Optional, Any
from pathlib import Path

from src.models.scene import Scene
from config.settings import EngineSettings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SceneManager:
    """
    Manages scene state and animations with fixed loading
    """
    
    def __init__(self):
        self.scenes: Dict[int, Scene] = {}
        self.active_scene_id: Optional[int] = None
        self.last_update_time = time.time()
        
        self._lock = threading.RLock()
        self._debug_frame_count = 0
    
    async def initialize(self):
        """
        Initialize the scene manager
        """
        logger.info("Initializing Scene Manager...")    
        logger.info("Scene Manager is ready - waiting for OSC signal to load scenes.")
    
    def load_scene_from_file(self, file_path: str) -> bool:
        """
        Load a scene from a JSON file - STANDARD FORMAT
        """
        try:
            with self._lock:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if "scene_ID" in data:
                    scene = Scene.from_dict(data)
                    self.scenes[scene.scene_id] = scene
                    
                    if self.active_scene_id is None:
                        self.active_scene_id = scene.scene_id
                    
                    logger.info(f"Loaded scene {scene.scene_id} from {file_path} (standard format)")
                    self._log_scene_debug_info()
                    return True
                else:
                    logger.warning(f"File {file_path} does not contain scene_ID - not a standard scene format")
                    return False
                
        except Exception as e:
            logger.error(f"Error loading scene from {file_path}: {e}")
            return False
    
    def load_multiple_scenes_from_file(self, file_path: str) -> bool:
        """
        Load multiple scenes from a JSON file - MULTIPLE SCENES FORMAT
        """
        try:
            with self._lock:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if "scenes" not in data:
                    logger.warning(f"File {file_path} does not contain 'scenes' array")
                    return False
                
                scenes_data = data.get("scenes", [])
                loaded_count = 0
                
                for scene_data in scenes_data:
                    try:
                        scene = Scene.from_dict(scene_data)
                        self.scenes[scene.scene_id] = scene
                        loaded_count += 1
                        
                        if self.active_scene_id is None:
                            self.active_scene_id = scene.scene_id
                            
                    except Exception as e:
                        logger.error(f"Error loading individual scene: {e}")
                        continue
                
                if loaded_count > 0:
                    logger.info(f"Loaded {loaded_count} scenes from {file_path} (multiple scenes format)")
                    self._log_scene_debug_info()
                    return True
                else:
                    logger.error(f"No valid scenes loaded from {file_path}")
                    return False
                
        except Exception as e:
            logger.error(f"Error loading multiple scenes from {file_path}: {e}")
            return False
    
    def load_scene_from_new_format(self, file_path: str, scene_id: int = 1) -> bool:
        """
        Load scene from NEW FORMAT (effects array) - NOT USED FOR CURRENT JSON
        """
        logger.info(f"Attempting new format loading for {file_path} - this should NOT be used for current JSON files")
        return False
    
    def _log_scene_debug_info(self):
        """
        Log debug information about loaded scenes
        """
        logger.info(f"=== SCENE DEBUG INFO ===")
        logger.info(f"Total scenes loaded: {len(self.scenes)}")
        logger.info(f"Available scene IDs: {list(self.scenes.keys())}")
        logger.info(f"Active Scene ID: {self.active_scene_id}")
        
        if not self.active_scene_id or self.active_scene_id not in self.scenes:
            logger.warning("No active scene or active scene not found!")
            return
            
        scene = self.scenes[self.active_scene_id]
        current_effect = scene.get_current_effect()
        
        logger.info(f"Scene {scene.scene_id}:")
        logger.info(f"  - Effects: {len(scene.effects)} (IDs: {list(scene.effects.keys())})")
        logger.info(f"  - Palettes: {len(scene.palettes)} (IDs: {list(scene.palettes.keys())})")
        logger.info(f"  - Current Effect ID: {scene.current_effect_id}")
        logger.info(f"  - Current Palette: {scene.current_palette}")
        
        if current_effect:
            logger.info(f"Current Effect {current_effect.effect_id}:")
            logger.info(f"  - LED Count: {current_effect.led_count}")
            logger.info(f"  - FPS: {current_effect.fps}")
            logger.info(f"  - Segments: {len(current_effect.segments)} (IDs: {list(current_effect.segments.keys())})")
            
            total_expected_leds = 0
            for seg_id, segment in current_effect.segments.items():
                total_length = sum(segment.length) if segment.length else 0
                has_color = any(c > 0 for c in segment.color) if segment.color else False
                expected_leds = total_length if has_color else 0
                total_expected_leds += expected_leds
                
                logger.info(f"  Segment {seg_id}:")
                logger.info(f"    - Length: {segment.length} (total: {total_length})")
                logger.info(f"    - Position: {segment.current_position:.1f} (initial: {segment.initial_position})")
                logger.info(f"    - Speed: {segment.move_speed}")
                logger.info(f"    - Colors: {segment.color}")
                logger.info(f"    - Expected LEDs: {expected_leds}")
            
            logger.info(f"  Total expected active LEDs: {total_expected_leds}")
            
            try:
                led_output = scene.get_led_output()
                actual_active = sum(1 for color in led_output if any(c > 0 for c in color))
                logger.info(f"  Actual LED output: {len(led_output)} total, {actual_active} active")
            except Exception as e:
                logger.error(f"  Error getting LED output: {e}")
        else:
            logger.warning(f"  Current effect {scene.current_effect_id} not found!")
    
    def switch_scene(self, scene_id: int) -> bool:
        """
        Switch scenes
        """
        try:
            with self._lock:
                if scene_id not in self.scenes:
                    logger.warning(f"Scene {scene_id} does not exist. Available: {list(self.scenes.keys())}")
                    return False
                
                self.active_scene_id = scene_id
                logger.info(f"Switched to scene {scene_id}")
                self._log_scene_debug_info()
                return True
                
        except Exception as e:
            logger.error(f"Error switching scene: {e}")
            return False
    
    def set_effect(self, effect_id: int) -> bool:
        """
        Set the effect for the current scene
        """
        try:
            with self._lock:
                if not self.active_scene_id or self.active_scene_id not in self.scenes:
                    logger.warning("No active scene")
                    return False
                
                scene = self.scenes[self.active_scene_id]
                if str(effect_id) not in scene.effects:
                    logger.warning(f"Effect {effect_id} does not exist in scene {self.active_scene_id}. Available: {list(scene.effects.keys())}")
                    return False
                
                scene.current_effect_id = effect_id
                logger.info(f"Set effect {effect_id} for scene {self.active_scene_id}")
                self._log_scene_debug_info()
                return True
                
        except Exception as e:
            logger.error(f"Error setting effect: {e}")
            return False
    
    def set_palette(self, palette_id: str) -> bool:
        """
        Set the palette for the current scene
        """
        try:
            with self._lock:
                if not self.active_scene_id or self.active_scene_id not in self.scenes:
                    return False
                
                scene = self.scenes[self.active_scene_id]
                if palette_id not in scene.palettes:
                    logger.warning(f"Palette {palette_id} does not exist in scene {self.active_scene_id}. Available: {list(scene.palettes.keys())}")
                    return False
                
                scene.current_palette = palette_id
                logger.info(f"Set palette {palette_id} for scene {self.active_scene_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error setting palette: {e}")
            return False
    
    def update_palette_color(self, palette_id: str, color_id: int, rgb: List[int]) -> bool:
        """
        Update a color in the palette
        """
        try:
            with self._lock:
                if not self.active_scene_id or self.active_scene_id not in self.scenes:
                    return False
                
                scene = self.scenes[self.active_scene_id]
                if palette_id not in scene.palettes:
                    return False
                
                if 0 <= color_id < len(scene.palettes[palette_id]):
                    scene.palettes[palette_id][color_id] = rgb[:3]
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error updating palette color: {e}")
            return False
    
    def update_animation(self, delta_time: float):
        """
        Update the animation frame
        """
        with self._lock:
            self._debug_frame_count += 1
            
            if self._debug_frame_count % 600 == 0: 
                self._log_animation_debug_info()
            
            for scene in self.scenes.values():
                for effect in scene.effects.values():
                    effect.update_animation(delta_time)
    
    def _log_animation_debug_info(self):
        """
        Log animation debug information
        """
        if not self.active_scene_id or self.active_scene_id not in self.scenes:
            return
            
        scene = self.scenes[self.active_scene_id]
        current_effect = scene.get_current_effect()
        
        if current_effect:
            led_output = self.get_led_output()
            active_count = sum(1 for color in led_output if any(c > 0 for c in color))
            
            logger.info(f"Animation Frame {self._debug_frame_count}: Active LEDs = {active_count}/{len(led_output)}")
            
            for seg_id, segment in current_effect.segments.items():
                logger.info(f"  Segment {seg_id}: pos={segment.current_position:.1f}, speed={segment.move_speed}")
    
    def get_led_output(self) -> List[List[int]]:
        """
        Get the LED output for the current scene
        """
        with self._lock:
            if self.active_scene_id and self.active_scene_id in self.scenes:
                scene = self.scenes[self.active_scene_id]
                output = scene.get_led_output()
                return output
            
            return [[0, 0, 0] for _ in range(EngineSettings.ANIMATION.led_count)]
    
    def get_current_scene_info(self) -> Dict[str, Any]:
        """
        Get information about the current scene
        """
        with self._lock:
            if not self.active_scene_id or self.active_scene_id not in self.scenes:
                return {
                    "scene_id": None,
                    "effect_id": None,
                    "palette_id": None,
                    "total_scenes": len(self.scenes),
                    "total_effects": 0,
                    "total_segments": 0
                }
            
            scene = self.scenes[self.active_scene_id]
            current_effect = scene.get_current_effect()
            
            return {
                "scene_id": scene.scene_id,
                "effect_id": scene.current_effect_id,
                "palette_id": scene.current_palette,
                "total_scenes": len(self.scenes),
                "total_effects": len(scene.effects),
                "total_segments": len(current_effect.segments) if current_effect else 0,
                "available_scenes": list(self.scenes.keys()),
                "available_effects": list(scene.effects.keys()),
                "available_palettes": list(scene.palettes.keys())
            }
    
    def get_all_scenes_info(self) -> List[Dict[str, Any]]:
        """
        Get information about all scenes
        """
        with self._lock:
            scenes_info = []
            for scene_id, scene in self.scenes.items():
                scenes_info.append({
                    "scene_id": scene_id,
                    "effect_count": len(scene.effects),
                    "palette_count": len(scene.palettes),
                    "current_effect": scene.current_effect_id,
                    "current_palette": scene.current_palette,
                    "is_active": scene_id == self.active_scene_id
                })
            return scenes_info