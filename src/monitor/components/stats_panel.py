"""
Stats Panel - Complete fix with correct data sources
"""

import flet as ft
from config.theme import ThemeColors, ThemeStyles
from src.utils.logger import get_logger

logger = get_logger(__name__)


class StatsPanel(ft.Container):
    """
    Component to display detailed engine statistics - FIXED VERSION
    """
    
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        
        self.led_count_text = ft.Text("225", size=18, weight=ft.FontWeight.BOLD, color=ThemeColors.PRIMARY, text_align=ft.TextAlign.CENTER)
        self.active_leds_text = ft.Text("0", size=18, weight=ft.FontWeight.BOLD, color=ThemeColors.SUCCESS, text_align=ft.TextAlign.CENTER)
        self.frame_count_text = ft.Text("0", size=18, weight=ft.FontWeight.BOLD, color=ThemeColors.INFO, text_align=ft.TextAlign.CENTER)
        self.scenes_count_text = ft.Text("0", size=18, weight=ft.FontWeight.BOLD, color=ThemeColors.SECONDARY, text_align=ft.TextAlign.CENTER)
        self.effects_count_text = ft.Text("0", size=18, weight=ft.FontWeight.BOLD, color=ThemeColors.WARNING, text_align=ft.TextAlign.CENTER)
        self.segments_count_text = ft.Text("0", size=18, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_PRIMARY, text_align=ft.TextAlign.CENTER)
        
        self._build_ui()
    
    def _build_ui(self):
        """
        Build UI component with correct 3x2 layout
        """
        title = ft.Text(
            "Performance Stats",
            **ThemeStyles.subheader_text_style()
        )
        
        stats_grid = ft.Column([
            ft.Row([
                self._create_stat_card("Total LEDs", self.led_count_text, ThemeColors.PRIMARY),
                self._create_stat_card("Active LEDs", self.active_leds_text, ThemeColors.SUCCESS)
            ], spacing=12),
            
            ft.Row([
                self._create_stat_card("Frames", self.frame_count_text, ThemeColors.INFO),
                self._create_stat_card("Scenes", self.scenes_count_text, ThemeColors.SECONDARY)
            ], spacing=12),
            
            ft.Row([
                self._create_stat_card("Effects", self.effects_count_text, ThemeColors.WARNING),
                self._create_stat_card("Segments", self.segments_count_text, ThemeColors.TEXT_PRIMARY)
            ], spacing=12)
        ], spacing=12)
        
        self.content = ft.Column([
            title,
            stats_grid
        ], spacing=16)
        
        self.padding = 0
    
    def _create_stat_card(self, label: str, value_widget: ft.Text, accent_color: str) -> ft.Container:
        """
        Create stat card
        """
        card_style = ThemeStyles.card_style()
        card_style["border"] = ft.border.all(2, accent_color)
        
        return ft.Container(
            content=ft.Column([
                ft.Text(label, size=12, color=ThemeColors.TEXT_DISABLED, text_align=ft.TextAlign.CENTER),
                value_widget
            ], spacing=4, 
               alignment=ft.MainAxisAlignment.CENTER,
               horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            **card_style,
            expand=True,
            height=70,
            alignment=ft.alignment.center
        )
    
    async def update(self):
        """
        Update stats display with CORRECT data sources
        """
        try:
            stats = self.engine.get_stats()
            
            led_colors = self.engine.get_led_colors()
            actual_active_leds = sum(1 for color in led_colors if any(c > 0 for c in color[:3]))
            
            total_scenes = len(self.engine.scene_manager.scenes)
            
            current_effects = 0
            current_segments = 0
            if self.engine.scene_manager.active_scene_id:
                scene = self.engine.scene_manager.scenes.get(self.engine.scene_manager.active_scene_id)
                if scene:
                    current_effects = len(scene.effects)
                    current_effect = scene.get_current_effect()
                    if current_effect:
                        current_segments = len(current_effect.segments)
            
            self.led_count_text.value = str(stats.total_leds)
            self.active_leds_text.value = str(actual_active_leds)
            self.frame_count_text.value = str(stats.frame_count)
            self.scenes_count_text.value = str(total_scenes)
            self.effects_count_text.value = str(current_effects)
            self.segments_count_text.value = str(current_segments)
            
            if actual_active_leds > 0:
                self.active_leds_text.color = ThemeColors.SUCCESS
            else:
                self.active_leds_text.color = ThemeColors.TEXT_DISABLED
           
        except Exception as e:
            logger.error(f"Error updating stats panel: {e}")
            
            self.led_count_text.value = "ERR"
            self.active_leds_text.value = "ERR"
            self.frame_count_text.value = "ERR"
            self.scenes_count_text.value = "ERR"
            self.effects_count_text.value = "ERR"
            self.segments_count_text.value = "ERR"