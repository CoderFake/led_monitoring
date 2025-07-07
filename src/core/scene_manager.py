import time
import threading
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from src.models.scene import Scene
from config.settings import EngineSettings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TransitionPhase(Enum):
    FADE_OUT = "fade_out"
    WAITING = "waiting" 
    FADE_IN = "fade_in"
    COMPLETED = "completed"


@dataclass
class PatternTransitionConfig:
    fade_in_ms: int = 100
    fade_out_ms: int = 100
    waiting_ms: int = 50


@dataclass  
class PatternTransition:
    is_active: bool = False
    phase: TransitionPhase = TransitionPhase.COMPLETED
    
    from_effect_id: int = None
    from_palette_id: str = None
    to_effect_id: int = None
    to_palette_id: str = None
    
    start_time: float = 0.0
    fade_in_ms: int = 100
    fade_out_ms: int = 100
    waiting_ms: int = 50
    
    phase_start_time: float = 0.0
    progress: float = 0.0


class SceneManager:
    def __init__(self):
        self.scenes: Dict[int, Scene] = {}
        self.active_scene_id: Optional[int] = None
        self.last_update_time = time.time()
        
        self._lock = threading.RLock()
        self._debug_frame_count = 0
        self._change_callbacks: List[callable] = []
        
        self.pattern_transition = PatternTransition()
        self.transition_config = PatternTransitionConfig(
            fade_in_ms=EngineSettings.PATTERN_TRANSITION.default_fade_in_ms,
            fade_out_ms=EngineSettings.PATTERN_TRANSITION.default_fade_out_ms,
            waiting_ms=EngineSettings.PATTERN_TRANSITION.default_waiting_ms
        )
    
    async def initialize(self):
        logger.info("Initializing Scene Manager...")    
        logger.info("Scene Manager is ready - waiting for OSC signal to load scenes.")
    
    def add_change_callback(self, callback: callable):
        with self._lock:
            self._change_callbacks.append(callback)
            
    def _notify_changes(self):
        for callback in self._change_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in change callback: {e}")
    
    def set_transition_config(self, fade_in_ms: int = None, fade_out_ms: int = None, waiting_ms: int = None):
        with self._lock:
            if fade_in_ms is not None:
                self.transition_config.fade_in_ms = max(0, fade_in_ms)
            if fade_out_ms is not None:
                self.transition_config.fade_out_ms = max(0, fade_out_ms)
            if waiting_ms is not None:
                self.transition_config.waiting_ms = max(0, waiting_ms)
        
        logger.info(f"Pattern transition config updated: fade_in={self.transition_config.fade_in_ms}ms, fade_out={self.transition_config.fade_out_ms}ms, waiting={self.transition_config.waiting_ms}ms")
    
    def start_pattern_transition(self, to_effect_id: int = None, to_palette_id: str = None):
        with self._lock:
            if not self.active_scene_id or self.active_scene_id not in self.scenes:
                return False
            
            current_scene = self.scenes[self.active_scene_id]
            
            self.pattern_transition.is_active = True
            self.pattern_transition.phase = TransitionPhase.FADE_OUT
            
            self.pattern_transition.from_effect_id = current_scene.current_effect_id
            self.pattern_transition.from_palette_id = current_scene.current_palette
            self.pattern_transition.to_effect_id = to_effect_id or current_scene.current_effect_id
            self.pattern_transition.to_palette_id = to_palette_id or current_scene.current_palette
            
            self.pattern_transition.fade_in_ms = self.transition_config.fade_in_ms
            self.pattern_transition.fade_out_ms = self.transition_config.fade_out_ms
            self.pattern_transition.waiting_ms = self.transition_config.waiting_ms
            
            self.pattern_transition.start_time = time.time()
            self.pattern_transition.phase_start_time = time.time()
            self.pattern_transition.progress = 0.0
            
            logger.info(f"Pattern transition started: Effect {self.pattern_transition.from_effect_id} → {self.pattern_transition.to_effect_id}, Palette {self.pattern_transition.from_palette_id} → {self.pattern_transition.to_palette_id}")
            return True
    
    def _update_pattern_transition(self, current_time: float):
        if not self.pattern_transition.is_active:
            return
            
        phase_elapsed = (current_time - self.pattern_transition.phase_start_time) * 1000
        
        if self.pattern_transition.phase == TransitionPhase.FADE_OUT:
            if phase_elapsed >= self.pattern_transition.fade_out_ms:
                self.pattern_transition.phase = TransitionPhase.WAITING
                self.pattern_transition.phase_start_time = current_time
                logger.debug("Transition phase: FADE_OUT → WAITING")
            else:
                self.pattern_transition.progress = 1.0 - (phase_elapsed / self.pattern_transition.fade_out_ms)
        
        elif self.pattern_transition.phase == TransitionPhase.WAITING:
            if phase_elapsed >= self.pattern_transition.waiting_ms:
                self.pattern_transition.phase = TransitionPhase.FADE_IN
                self.pattern_transition.phase_start_time = current_time
                logger.debug("Transition phase: WAITING → FADE_IN")
            else:
                self.pattern_transition.progress = 0.0
        
        elif self.pattern_transition.phase == TransitionPhase.FADE_IN:
            if phase_elapsed >= self.pattern_transition.fade_in_ms:
                self._complete_pattern_transition()
            else:
                self.pattern_transition.progress = phase_elapsed / self.pattern_transition.fade_in_ms
    
    def _complete_pattern_transition(self):
        if not self.active_scene_id or self.active_scene_id not in self.scenes:
            return
            
        scene = self.scenes[self.active_scene_id]
        scene.current_effect_id = self.pattern_transition.to_effect_id
        scene.current_palette = self.pattern_transition.to_palette_id
        
        self.pattern_transition.is_active = False
        self.pattern_transition.phase = TransitionPhase.COMPLETED
        
        logger.info(f"Pattern transition completed: Effect {self.pattern_transition.to_effect_id}, Palette {self.pattern_transition.to_palette_id}")
        self._notify_changes()
    
    def get_led_output(self) -> List[List[int]]:
        with self._lock:
            if not self.pattern_transition.is_active:
                if self.active_scene_id and self.active_scene_id in self.scenes:
                    scene = self.scenes[self.active_scene_id]
                    output = scene.get_led_output()
                    return output
                return [[0, 0, 0] for _ in range(EngineSettings.ANIMATION.led_count)]
            
            return self._get_transition_led_output()
    
    def _get_transition_led_output(self) -> List[List[int]]:
        if not self.active_scene_id or self.active_scene_id not in self.scenes:
            return [[0, 0, 0] for _ in range(EngineSettings.ANIMATION.led_count)]
        
        scene = self.scenes[self.active_scene_id]
        
        if self.pattern_transition.phase == TransitionPhase.FADE_OUT:
            scene.current_effect_id = self.pattern_transition.from_effect_id
            scene.current_palette = self.pattern_transition.from_palette_id
            output = scene.get_led_output()
            
            brightness = self.pattern_transition.progress
            return [
                [int(color[0] * brightness), int(color[1] * brightness), int(color[2] * brightness)]
                for color in output
            ]
        
        elif self.pattern_transition.phase == TransitionPhase.WAITING:
            return [[0, 0, 0] for _ in range(EngineSettings.ANIMATION.led_count)]
        
        elif self.pattern_transition.phase == TransitionPhase.FADE_IN:
            scene.current_effect_id = self.pattern_transition.to_effect_id
            scene.current_palette = self.pattern_transition.to_palette_id
            output = scene.get_led_output()
            
            brightness = self.pattern_transition.progress
            return [
                [int(color[0] * brightness), int(color[1] * brightness), int(color[2] * brightness)]
                for color in output
            ]
        
        return [[0, 0, 0] for _ in range(EngineSettings.ANIMATION.led_count)]
    
    def load_scene_from_file(self, file_path: str) -> bool:
        try:
            with self._lock:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if "scene_ID" in data:
                    scene = Scene.from_dict(data)
                    self.scenes[scene.scene_id] = scene
                    
                    if self.active_scene_id is None:
                        self.active_scene_id = scene.scene_id
                    
                    logger.info(f"Loaded single scene {scene.scene_id} from {file_path}")
                    self._log_scene_debug_info()
                    self._notify_changes()
                    return True
                else:
                    logger.warning(f"File {file_path} does not contain scene_ID at root - not a standard single scene format")
                    return False
                
        except Exception as e:
            logger.error(f"Error loading single scene from {file_path}: {e}")
            return False
    
    def load_multiple_scenes_from_file(self, file_path: str) -> bool:
        try:
            with self._lock:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if "scenes" not in data:
                    logger.warning(f"File {file_path} does not contain 'scenes'")
                    return False
                
                scenes_data = data.get("scenes", [])
                if not scenes_data:
                    logger.warning(f"File {file_path} has empty 'scenes' array")
                    return False
                
                loaded_count = 0
                
                for scene_data in scenes_data:
                    try:
                        if "scene_ID" not in scene_data:
                            logger.warning(f"Scene data missing scene_ID: {scene_data}")
                            continue
                            
                        scene = Scene.from_dict(scene_data)
                        self.scenes[scene.scene_id] = scene
                        loaded_count += 1
                        
                        if self.active_scene_id is None:
                            self.active_scene_id = scene.scene_id
                            
                    except Exception as e:
                        logger.error(f"Error loading individual scene: {e}")
                        continue
                
                if loaded_count > 0:
                    self._log_scene_debug_info()
                    self._notify_changes()
                    return True
                else:
                    logger.error(f"No valid scenes loaded from {file_path}")
                    return False
                
        except Exception as e:
            logger.error(f"Error loading multiple scenes from {file_path}: {e}")
            return False
    
    def load_scene(self, scene_data: Dict[str, Any]) -> bool:
        try:
            with self._lock:
                scene = Scene.from_dict(scene_data)
                self.scenes[scene.scene_id] = scene
                
                if self.active_scene_id is None:
                    self.active_scene_id = scene.scene_id
                    
                self._notify_changes()
                logger.info(f"Scene {scene.scene_id} has been loaded successfully")
                return True
                
        except Exception as e:
            logger.error(f"Error loading scene: {e}")
            return False
    
    def switch_scene(self, scene_id: int, fade_params: List[int] = None) -> bool:
        try:
            with self._lock:
                if scene_id not in self.scenes:
                    logger.warning(f"Scene {scene_id} does not exist. Available: {list(self.scenes.keys())}")
                    return False
                    
                self.active_scene_id = scene_id
                
                if fade_params:
                    self.scenes[scene_id].fade_params = fade_params
                    
                self._notify_changes()
                logger.info(f"Switched to scene {scene_id}")
                self._log_scene_debug_info()
                return True
                
        except Exception as e:
            logger.error(f"Error switching scene: {e}")
            return False
    
    def set_effect_palette(self, scene_id: int, effect_id: int, palette_id: str) -> bool:
        try:
            with self._lock:
                if scene_id not in self.scenes:
                    logger.warning(f"Scene {scene_id} does not exist")
                    return False
                    
                scene = self.scenes[scene_id]
                scene.switch_effect(effect_id, palette_id)
                
                self._notify_changes()
                logger.info(f"Scene {scene_id}: effect {effect_id}, palette {palette_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error setting effect/palette: {e}")
            return False
    
    def set_effect(self, effect_id: int) -> bool:
        try:
            with self._lock:
                if not self.active_scene_id or self.active_scene_id not in self.scenes:
                    logger.warning("No active scene")
                    return False
                
                scene = self.scenes[self.active_scene_id]
                if str(effect_id) not in scene.effects:
                    logger.warning(f"Effect {effect_id} does not exist in scene {self.active_scene_id}. Available: {list(scene.effects.keys())}")
                    return False
                
                if EngineSettings.PATTERN_TRANSITION.enabled:
                    return self.start_pattern_transition(to_effect_id=effect_id)
                else:
                    scene.current_effect_id = effect_id
                    logger.info(f"Set effect {effect_id} for scene {self.active_scene_id}")
                    self._log_scene_debug_info()
                    self._notify_changes()
                    return True
                
        except Exception as e:
            logger.error(f"Error setting effect: {e}")
            return False
    
    def set_palette(self, palette_id: str) -> bool:
        try:
            with self._lock:
                if not self.active_scene_id or self.active_scene_id not in self.scenes:
                    return False
                
                scene = self.scenes[self.active_scene_id]
                if palette_id not in scene.palettes:
                    logger.warning(f"Palette {palette_id} does not exist in scene {self.active_scene_id}. Available: {list(scene.palettes.keys())}")
                    return False
                
                if EngineSettings.PATTERN_TRANSITION.enabled:
                    return self.start_pattern_transition(to_palette_id=palette_id)
                else:
                    scene.current_palette = palette_id
                    logger.info(f"Set palette {palette_id} for scene {self.active_scene_id}")
                    self._notify_changes()
                    return True
                
        except Exception as e:
            logger.error(f"Error setting palette: {e}")
            return False
    
    def set_move_speed(self, scene_id: int, speed: float) -> bool:
        try:
            with self._lock:
                if scene_id not in self.scenes:
                    return False
                    
                scene = self.scenes[scene_id]
                current_effect = scene.get_current_effect()
                
                if current_effect:
                    for segment in current_effect.segments.values():
                        segment.move_speed = speed if segment.move_speed >= 0 else -speed
                        
                    self._notify_changes()
                    return True
                    
                return False
                
        except Exception as e:
            logger.error(f"Error setting move speed: {e}")
            return False
    
    def update_palette_color(self, palette_id: str, color_id: int, rgb: List[int]) -> bool:
        try:
            with self._lock:
                if not self.active_scene_id or self.active_scene_id not in self.scenes:
                    return False
                
                scene = self.scenes[self.active_scene_id]
                if palette_id not in scene.palettes:
                    return False
                
                if 0 <= color_id < len(scene.palettes[palette_id]):
                    scene.palettes[palette_id][color_id] = rgb[:3]
                    self._notify_changes()
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error updating palette color: {e}")
            return False
    
    def update_animation_frame(self):
        current_time = time.time()
        delta_time = current_time - self.last_update_time
        self.last_update_time = current_time
        
        with self._lock:
            for scene in self.scenes.values():
                for effect in scene.effects.values():
                    effect.update_animation(delta_time)
    
    def update_animation(self, delta_time: float):
        with self._lock:
            current_time = time.time()
            
            self._update_pattern_transition(current_time)
            
            self._debug_frame_count += 1
            
            if self._debug_frame_count % 600 == 0: 
                self._log_animation_debug_info()
            
            for scene in self.scenes.values():
                for effect in scene.effects.values():
                    effect.update_animation(delta_time)
    
    def _log_animation_debug_info(self):
        if not self.active_scene_id or self.active_scene_id not in self.scenes:
            return
            
        scene = self.scenes[self.active_scene_id]
        current_effect = scene.get_current_effect()
        
        if current_effect:
            led_output = self.get_led_output()
            active_count = sum(1 for color in led_output if any(c > 0 for c in color))
            
            logger.info(f"Animation Frame {self._debug_frame_count}: Active LEDs = {active_count}/{len(led_output)}")
            
            if self.pattern_transition.is_active:
                logger.info(f"Pattern Transition: {self.pattern_transition.phase.value}, Progress: {self.pattern_transition.progress:.2f}")
            
            for seg_id, segment in current_effect.segments.items():
                logger.info(f"  Segment {seg_id}: pos={segment.current_position:.1f}, speed={segment.move_speed}")
    
    def _log_scene_debug_info(self):
        logger.info(f"=== SCENE INFORMATION ===")
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
    
    def get_scene_stats(self) -> Dict[str, Any]:
        with self._lock:
            stats = {
                "total_scenes": len(self.scenes),
                "active_scene_id": self.active_scene_id,
                "total_effects": 0,
                "total_segments": 0,
                "current_palette": None,
                "current_fps": EngineSettings.ANIMATION.target_fps,
                "available_scenes": list(self.scenes.keys()),
                "pattern_transition_active": self.pattern_transition.is_active,
                "transition_phase": self.pattern_transition.phase.value if self.pattern_transition.is_active else None
            }
            
            if self.active_scene_id and self.active_scene_id in self.scenes:
                active_scene = self.scenes[self.active_scene_id]
                stats["total_effects"] = len(active_scene.effects)
                stats["current_palette"] = active_scene.current_palette
                
                for effect in active_scene.effects.values():
                    stats["total_segments"] += len(effect.segments)
                    stats["current_fps"] = effect.fps
                    
            return stats
    
    def get_current_scene_info(self) -> Dict[str, Any]:
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
    
    def get_all_scenes(self) -> Dict[int, str]:
        with self._lock:
            scenes_info = {}
            for scene_id, scene in self.scenes.items():
                scenes_info[scene_id] = f"Scene {scene_id}"
            return scenes_info
    
    def get_all_segments_data(self) -> List[Dict[str, Any]]:
        with self._lock:
            segments_data = []
            
            if self.active_scene_id and self.active_scene_id in self.scenes:
                scene = self.scenes[self.active_scene_id]
                current_effect = scene.get_current_effect()
                
                if current_effect:
                    for segment in current_effect.segments.values():
                        segments_data.append({
                            "id": segment.segment_id,
                            "position": segment.current_position,
                            "length": sum(segment.length),
                            "speed": segment.move_speed,
                            "colors": segment.get_led_colors(scene.get_current_palette())
                        })
                        
            return segments_data