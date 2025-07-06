"""
Status Display - Debug version with detailed logging
"""

import flet as ft
from config.theme import ThemeColors, ThemeStyles
from src.utils.logger import get_logger

logger = get_logger(__name__)

class StatusDisplay(ft.Container):
    """
    Component to display engine status
    """
    
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        
        body_style = ThemeStyles.body_text_style()
        body_style["text_align"] = ft.TextAlign.CENTER
        
        self.scene_text = ft.Text("--", **body_style)
        self.effect_text = ft.Text("--", **body_style)
        self.palette_text = ft.Text("--", **body_style)
        
        self.fps_text = ft.Text("--", **body_style)
        self.brightness_text = ft.Text("--", **body_style)
        self.speed_text = ft.Text("--", **body_style)
        
        self._build_ui()
    
    def _build_ui(self):
        """
        Build UI component
        """
        title = ft.Text(
            "Engine Status",
            **ThemeStyles.subheader_text_style()
        )
        
        status_grid = ft.Column([
            ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Text("Scene", size=12, color=ThemeColors.TEXT_DISABLED, text_align=ft.TextAlign.CENTER),
                        self.scene_text
                    ], spacing=4, alignment=ft.MainAxisAlignment.CENTER,
                       horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    **ThemeStyles.card_style(),
                    expand=True,
                    height=60,
                    alignment=ft.alignment.center
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Effect", size=12, color=ThemeColors.TEXT_DISABLED, text_align=ft.TextAlign.CENTER),
                        self.effect_text
                    ], spacing=4, alignment=ft.MainAxisAlignment.CENTER,
                       horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    **ThemeStyles.card_style(),
                    expand=True,
                    height=60,
                    alignment=ft.alignment.center
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Palette", size=12, color=ThemeColors.TEXT_DISABLED, text_align=ft.TextAlign.CENTER),
                        self.palette_text
                    ], spacing=4, alignment=ft.MainAxisAlignment.CENTER,
                       horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    **ThemeStyles.card_style(),
                    expand=True,
                    height=60,
                    alignment=ft.alignment.center
                )
            ], spacing=12),
            
            ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Text("FPS", size=12, color=ThemeColors.TEXT_DISABLED, text_align=ft.TextAlign.CENTER),
                        self.fps_text
                    ], spacing=4, alignment=ft.MainAxisAlignment.CENTER,
                       horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    **ThemeStyles.card_style(),
                    expand=True,
                    height=60,
                    alignment=ft.alignment.center
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Brightness", size=12, color=ThemeColors.TEXT_DISABLED, text_align=ft.TextAlign.CENTER),
                        self.brightness_text
                    ], spacing=4, alignment=ft.MainAxisAlignment.CENTER,
                       horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    **ThemeStyles.card_style(),
                    expand=True,
                    height=60,
                    alignment=ft.alignment.center
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Speed", size=12, color=ThemeColors.TEXT_DISABLED, text_align=ft.TextAlign.CENTER),
                        self.speed_text
                    ], spacing=4, alignment=ft.MainAxisAlignment.CENTER,
                       horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    **ThemeStyles.card_style(),
                    expand=True,
                    height=60,
                    alignment=ft.alignment.center
                )
            ], spacing=12)
        ], spacing=12)
        
        self.content = ft.Column([
            title,
            status_grid
        ], spacing=16)
        
        self.padding = 0
    
    async def update(self):
        """
        Update status display with DEBUG logging
        """
        try:
            stats = self.engine.get_stats()
            scene_info = self.engine.get_scene_info()
            
            logger.info(f"[STATUS DEBUG] Scene Manager Info: {scene_info}")
            logger.info(f"[STATUS DEBUG] Engine Stats: frame={stats.frame_count}, fps={stats.actual_fps:.1f}")
            logger.info(f"[STATUS DEBUG] Active scene ID: {self.engine.scene_manager.active_scene_id}")
            logger.info(f"[STATUS DEBUG] Available scenes: {list(self.engine.scene_manager.scenes.keys())}")
            
            self.scene_text.value = str(scene_info.get('scene_id', '--'))
            self.effect_text.value = str(scene_info.get('effect_id', '--'))
            self.palette_text.value = str(scene_info.get('palette_id', '--'))
            
            self.fps_text.value = f"{stats.actual_fps:.1f}"
            self.brightness_text.value = f"{stats.master_brightness}"
            self.speed_text.value = f"{stats.speed_percent}%"
            
            if stats.actual_fps >= stats.target_fps * 0.9:
                self.fps_text.color = ThemeColors.SUCCESS
            elif stats.actual_fps >= stats.target_fps * 0.7:
                self.fps_text.color = ThemeColors.WARNING
            else:
                self.fps_text.color = ThemeColors.ERROR
            
        except Exception as e:
            logger.error(f"Error updating status display: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            self.scene_text.value = "ERR"
            self.effect_text.value = "ERR"
            self.palette_text.value = "ERR"
            self.fps_text.value = "ERR"
            self.brightness_text.value = "ERR"
            self.speed_text.value = "ERR"