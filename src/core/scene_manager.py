"""
Scene Manager - Manages scenes and animations.
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
    Manages scene state and animations.
    """
    
    def __init__(self):
        self.scenes: Dict[int, Scene] = {}
        self.active_scene_id: Optional[int] = None
        self.last_update_time = time.time()
        
        self._lock = threading.RLock()
    
    async def initialize(self):
        """
        Initialize the scene manager.
        """
        logger.info("Initializing Scene Manager...")    
        logger.info("Scene Manager is ready - waiting for OSC signal to load scenes.")
    
    def _load_default_scenes(self):
        """
        Load default scenes from data 
        """
        pass
    
    def _load_scenes_from_directory(self, scenes_dir: Path):
        """
        Load all scenes from a directory
        """
        pass
    
    def load_scene_from_new_format(self, file_path: str, scene_id: int = 1) -> bool:
        """
        Load a scene from a JSON file with the new format
        """
        try:
            with self._lock:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                scene_data = {
                    "scene_ID": scene_id,
                    "current_effect_ID": 1,
                    "current_palette": "A",
                    "palettes": {
                        "A": []
                    },
                    "effects": {}
                }
                
                if "effects" in data:
                    for i, effect_data in enumerate(data["effects"], 1):
                        palette_colors = []
                        for segment in effect_data.get("segments", []):
                            if "color" in segment:
                                palette_colors.append(segment["color"])
                            elif "color_start" in segment:
                                palette_colors.append(segment["color_start"])
                            elif "color_end" in segment:
                                palette_colors.append(segment["color_end"])
                        
                        if palette_colors:
                            scene_data["palettes"]["A"] = palette_colors
                        
                        effect = {
                            "effect_ID": i,
                            "led_count": 225,
                            "fps": 60,
                            "time": 0.0,
                            "current_palette": "A",
                            "segments": {}
                        }
                        
                        for j, segment_data in enumerate(effect_data.get("segments", []), 1):
                            segment = {
                                "segment_ID": j,
                                "color": [0],
                                "transparency": [1.0],
                                "length": [segment_data.get("end", 224) - segment_data.get("start", 0)],
                                "move_speed": 0.0,
                                "move_range": [segment_data.get("start", 0), segment_data.get("end", 224)],
                                "initial_position": segment_data.get("start", 0),
                                "current_position": float(segment_data.get("start", 0)),
                                "is_edge_reflect": False,
                                "dimmer_time": [0, 100, 200, 100, 0],
                                "dimmer_time_ratio": 1.0,
                                "gradient": False,
                                "fade": False,
                                "gradient_colors": [0, -1, -1]
                            }
                            effect["segments"][str(j)] = segment
                        
                        scene_data["effects"][str(i)] = effect
                
                scene = Scene.from_dict(scene_data)
                self.scenes[scene.scene_id] = scene
                
                if self.active_scene_id is None:
                    self.active_scene_id = scene.scene_id
                
                logger.info(f"Loaded scene {scene.scene_id} from {file_path}")
                return True
                
        except Exception as e:
            logger.error(f"Error loading scene from {file_path}: {e}")
            return False
    

    def load_scene_from_file(self, file_path: str) -> bool:
        """
        Load a scene from a JSON file.
        """
        try:
            with self._lock:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                scene = Scene.from_dict(data)
                self.scenes[scene.scene_id] = scene
                
                if self.active_scene_id is None:
                    self.active_scene_id = scene.scene_id
                
                logger.info(f"Loaded scene {scene.scene_id} from {file_path}")
                return True
                
        except Exception as e:
            logger.error(f"Error loading scene from {file_path}: {e}")
            return False
    
    def load_multiple_scenes_from_file(self, file_path: str) -> bool:
        """
        Load multiple scenes from a JSON file.
        """
        try:
            with self._lock:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                scenes_data = data.get("scenes", [])
                loaded_count = 0
                
                for scene_data in scenes_data:
                    scene = Scene.from_dict(scene_data)
                    self.scenes[scene.scene_id] = scene
                    loaded_count += 1
                    
                    if self.active_scene_id is None:
                        self.active_scene_id = scene.scene_id
                
                logger.info(f"Loaded {loaded_count} scenes from {file_path}")
                return True
                
        except Exception as e:
            logger.error(f"Error loading multiple scenes from {file_path}: {e}")
            return False
    
    def switch_scene(self, scene_id: int) -> bool:
        """
        Switch scenes.
        """
        try:
            with self._lock:
                if scene_id not in self.scenes:
                    logger.warning(f"Scene {scene_id} does not exist.")
                    return False
                
                self.active_scene_id = scene_id
                logger.info(f"Switched to scene {scene_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error switching scene: {e}")
            return False
    
    def set_effect(self, effect_id: int) -> bool:
        """
        Set the effect for the current scene.
        """
        try:
            with self._lock:
                if not self.active_scene_id or self.active_scene_id not in self.scenes:
                    return False
                
                scene = self.scenes[self.active_scene_id]
                if str(effect_id) not in scene.effects:
                    logger.warning(f"Effect {effect_id} does not exist in scene {self.active_scene_id}")
                    return False
                
                scene.current_effect_id = effect_id
                logger.info(f"Set effect {effect_id} for scene {self.active_scene_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error setting effect: {e}")
            return False
    
    def set_palette(self, palette_id: str) -> bool:
        """
        Set the palette for the current scene.
        """
        try:
            with self._lock:
                if not self.active_scene_id or self.active_scene_id not in self.scenes:
                    return False
                
                scene = self.scenes[self.active_scene_id]
                if palette_id not in scene.palettes:
                    logger.warning(f"Palette {palette_id} does not exist in scene {self.active_scene_id}")
                    return False
                
                scene.current_palette = palette_id
                logger.info(f"Set palette {palette_id} for scene {self.active_scene_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error setting palette: {e}")
            return False
    
    def update_palette_color(self, palette_id: str, color_id: int, rgb: List[int]) -> bool:
        """
        Update a color in the palette.
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
        Update the animation frame.
        """
        with self._lock:
            for scene in self.scenes.values():
                for effect in scene.effects.values():
                    effect.update_animation(delta_time)
    
    def get_led_output(self) -> List[List[int]]:
        """
        Get the LED output for the current scene.
        """
        with self._lock:
            if self.active_scene_id and self.active_scene_id in self.scenes:
                return self.scenes[self.active_scene_id].get_led_output()
            
            return [[0, 0, 0] for _ in range(EngineSettings.ANIMATION.led_count)]
    
    def get_current_scene_info(self) -> Dict[str, Any]:
        """
        Get information about the current scene.
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
        Get information about all scenes.
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
