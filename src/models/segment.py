"""
Segment model - Defines the Segment data structure.
"""

from typing import List, Any, Dict
from dataclasses import dataclass, field


@dataclass
class Segment:
    """
    LED Segment model representing a moving light segment.
    """
    
    segment_id: int
    color: List[int] = field(default_factory=lambda: [0, 0, 0, 0])
    transparency: List[float] = field(default_factory=lambda: [1.0, 1.0, 1.0, 1.0])
    length: List[int] = field(default_factory=lambda: [10, 10, 10])
    move_speed: float = 0.0
    move_range: List[int] = field(default_factory=lambda: [0, 224])
    initial_position: int = 0
    current_position: float = 0.0
    is_edge_reflect: bool = True
    dimmer_time: List[int] = field(default_factory=lambda: [0, 100, 200, 100, 0])
    dimmer_time_ratio: float = 1.0
    gradient: bool = False
    fade: bool = False
    gradient_colors: List[int] = field(default_factory=lambda: [0, -1, -1])
    
    def update_position(self, delta_time: float):
        """
        Update the position of the segment based on movement speed and time.
        """
        if self.move_speed == 0:
            return
            
        self.current_position += self.move_speed * delta_time
        
        if self.is_edge_reflect:
            min_pos, max_pos = self.move_range
            if self.current_position <= min_pos:
                self.current_position = min_pos
                self.move_speed = abs(self.move_speed)
            elif self.current_position >= max_pos:
                self.current_position = max_pos
                self.move_speed = -abs(self.move_speed)
                
    def get_led_colors(self, palette: List[List[int]]) -> List[List[int]]:
        """
        Calculate the LED colors for this segment - CORRECT PATTERN
        
        Pattern: length[i] corresponds to color[i]
        - length[0] LEDs first use color[0]
        - length[1] LEDs next use color[1] 
        - length[2] LEDs next use color[2]
        - If color has more elements than length, add 1 LED for each extra color
        """ 
        colors = []
        
        if not self.color:
            return colors
        
        current_led_index = 0
        for part_index in range(len(self.length)):
            part_length = self.length[part_index]
            
            if part_length <= 0:
                continue
                
            color_index = self.color[part_index] if part_index < len(self.color) else 0
            
            transparency = 1.0
            if part_index < len(self.transparency):
                transparency = self.transparency[part_index]
            
            for led_in_part in range(part_length):
                if 0 <= color_index < len(palette):
                    base_color = palette[color_index].copy()
                    
                    brightness = 1.0
                    if self.fade:
                        brightness = self.get_brightness_at_position(current_led_index)
                    
                    final_color = [
                        int(c * transparency * brightness) 
                        for c in base_color
                    ]
                    colors.append(final_color)
                else:
                    colors.append([0, 0, 0])
                
                current_led_index += 1
        
        if len(self.color) > len(self.length):
            for extra_index in range(len(self.length), len(self.color)):
                color_index = self.color[extra_index]
                
                transparency = 1.0
                if extra_index < len(self.transparency):
                    transparency = self.transparency[extra_index]
                
                if 0 <= color_index < len(palette):
                    base_color = palette[color_index].copy()
                    
                    brightness = 1.0
                    if self.fade:
                        brightness = self.get_brightness_at_position(current_led_index)
                    
                    final_color = [
                        int(c * transparency * brightness) 
                        for c in base_color
                    ]
                    colors.append(final_color)
                else:
                    colors.append([0, 0, 0])
                
                current_led_index += 1
                
        return colors
    
    def get_brightness_at_position(self, relative_pos: int) -> float:
        """
        Calculate the brightness at a relative position in the segment.
        """
        if not self.fade or not self.dimmer_time:
            return 1.0
            
        total_length = sum(self.length)
        if total_length == 0:
            return 1.0
            
        dimmer_length = len(self.dimmer_time)
        if dimmer_length <= 1:
            return 1.0
            
        progress = relative_pos / total_length
        dimmer_pos = progress * (dimmer_length - 1)
        
        index = int(dimmer_pos)
        fraction = dimmer_pos - index
        
        if index >= dimmer_length - 1:
            return self.dimmer_time[-1] / 100.0
            
        current_value = self.dimmer_time[index]
        next_value = self.dimmer_time[index + 1]
        
        interpolated = current_value + (next_value - current_value) * fraction
        return interpolated / 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the segment to a dictionary for JSON serialization.
        """
        return {
            "segment_ID": self.segment_id,
            "color": self.color,
            "transparency": self.transparency,
            "length": self.length,
            "move_speed": self.move_speed,
            "move_range": self.move_range,
            "initial_position": self.initial_position,
            "current_position": self.current_position,
            "is_edge_reflect": self.is_edge_reflect,
            "dimmer_time": self.dimmer_time,
            "dimmer_time_ratio": self.dimmer_time_ratio,
            "gradient": self.gradient,
            "fade": self.fade,
            "gradient_colors": self.gradient_colors
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Segment':
        """
        Create a segment from a dictionary.
        """
        return cls(
            segment_id=data["segment_ID"],
            color=data["color"],
            transparency=data["transparency"],
            length=data["length"],
            move_speed=data["move_speed"],
            move_range=data["move_range"],
            initial_position=data["initial_position"],
            current_position=data["current_position"],
            is_edge_reflect=data["is_edge_reflect"],
            dimmer_time=data["dimmer_time"],
            dimmer_time_ratio=data["dimmer_time_ratio"],
            gradient=data["gradient"],
            fade=data["fade"],
            gradient_colors=data["gradient_colors"]
        )
    
    def reset_position(self):
        """
        Reset the position to the initial position.
        """
        self.current_position = float(self.initial_position)
    
    def is_active(self) -> bool:
        """
        Check if the segment is active.
        """
        return any(c > 0 for c in self.color) and sum(self.length) > 0