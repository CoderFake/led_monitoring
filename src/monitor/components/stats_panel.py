"""
Stats Panel - Component to display detailed statistics - Correct layout
"""

import flet as ft
from config.theme import ThemeColors, ThemeStyles
from src.utils.logger import get_logger

logger = get_logger(__name__)


class StatsPanel(ft.Container):
    """
    Component to display detailed engine statistics
    """
    
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        
        self.led_count_text = ft.Text("225", size=18, weight=ft.FontWeight.BOLD, color=ThemeColors.PRIMARY, text_align=ft.TextAlign.CENTER)
        self.active_leds_text = ft.Text("0", size=18, weight=ft.FontWeight.BOLD, color=ThemeColors.SUCCESS, text_align=ft.TextAlign.CENTER)
        self.frame_count_text = ft.Text("0", size=18, weight=ft.FontWeight.BOLD, color=ThemeColors.INFO, text_align=ft.TextAlign.CENTER)
        self.animation_time_text = ft.Text("0.0s", size=18, weight=ft.FontWeight.BOLD, color=ThemeColors.SECONDARY, text_align=ft.TextAlign.CENTER)
        self.segments_count_text = ft.Text("0", size=18, weight=ft.FontWeight.BOLD, color=ThemeColors.WARNING, text_align=ft.TextAlign.CENTER)
        self.effects_count_text = ft.Text("0", size=18, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_PRIMARY, text_align=ft.TextAlign.CENTER)
        
        self._build_ui()
    
    def _build_ui(self):
        """
        Build UI component with 2x2 layout
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
                self._create_stat_card("Runtime", self.animation_time_text, ThemeColors.SECONDARY)
            ], spacing=12),
            
            ft.Row([
                self._create_stat_card("Segments", self.segments_count_text, ThemeColors.WARNING),
                self._create_stat_card("Effects", self.effects_count_text, ThemeColors.TEXT_PRIMARY)
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
        Update stats display 
        """
        try:
            stats = self.engine.get_stats()
            scene_info = self.engine.get_scene_info()
            
            logger.info(f"[STATS DEBUG] Frame count: {stats.frame_count}, FPS: {stats.actual_fps:.1f}, Animation time: {stats.animation_time:.1f}s")
            
            self.led_count_text.value = str(stats.total_leds)
            self.active_leds_text.value = str(stats.active_leds)
            
            self.frame_count_text.value = str(stats.frame_count)
            self.animation_time_text.value = f"{stats.animation_time:.1f}s"
            
            self.segments_count_text.value = str(scene_info.get('total_segments', 0))
            self.effects_count_text.value = str(scene_info.get('total_effects', 0))
            
            if stats.active_leds > 0:
                self.active_leds_text.color = ThemeColors.SUCCESS
            else:
                self.active_leds_text.color = ThemeColors.TEXT_DISABLED
                
        except Exception as e:
            logger.error(f"Error updating stats panel: {e}")
            
            self.led_count_text.value = "0"
            self.active_leds_text.value = "0"
            self.frame_count_text.value = "0"
            self.animation_time_text.value = "0.0s"
            self.segments_count_text.value = "0"
            self.effects_count_text.value = "0"