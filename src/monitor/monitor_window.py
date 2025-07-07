"""
Monitor Window - Main window to monitor engine
"""

import asyncio
import flet as ft
from typing import Optional

from config.theme import MonitorTheme, ThemeColors, ThemeStyles
from config.settings import EngineSettings
from .components.status_display import StatusDisplay
from .components.log_viewer import LogViewer
from .components.stats_panel import StatsPanel
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MonitorWindow:
    """
    Main monitor window
    """
    
    def __init__(self, engine):
        self.engine = engine
        self.page: Optional[ft.Page] = None
        
        self.status_display = None
        self.log_viewer = None
        self.stats_panel = None
        
        self.main_content = None
        self.running = False
        self.update_task = None
        
    async def start(self):
        """
        Start monitor
        """
        logger.info("Starting Monitor Window...")
        self.running = True
        
    async def stop(self):
        """
        Stop monitor
        """
        logger.info("Stopping Monitor Window...")
        self.running = False
        
        if self.update_task:
            self.update_task.cancel()
            
    async def setup_page(self, page: ft.Page):
        """
        Setup page and components
        """
        self.page = page
        MonitorTheme.configure_page(page)
        
        self._create_components()
        self._build_layout()
        
        if self.log_viewer:
            self.log_viewer.set_page(page)
        
        page.add(self.main_content)
        page.update()
        
        self._start_update_loop()
        logger.info("Monitor UI is ready") 
    
    def _create_components(self):
        """
        Create components
        """
        self.status_display = StatusDisplay(self.engine)
        self.log_viewer = LogViewer()
        self.stats_panel = StatsPanel(self.engine)
    
    def _build_layout(self):
        """
        Build main layout
        """
        header = self._create_header()
        
        main_row = ft.Row([
            ft.Container(
                content=ft.Column([
                    self.status_display,
                    ft.Divider(height=1, color=ThemeColors.SURFACE_VARIANT),
                    self.stats_panel
                ], spacing=20),
                width=400,
                padding=20
            ),
            ft.VerticalDivider(width=1, color=ThemeColors.SURFACE_VARIANT),
            ft.Container(
                content=self.log_viewer,
                expand=True,
                padding=20
            )
        ], expand=True, spacing=0)
        
        self.main_content = ft.Column([
            header,
            ft.Divider(height=1, color=ThemeColors.SURFACE_VARIANT),
            main_row
        ], spacing=0, expand=True)
    
    def _create_header(self) -> ft.Container:
        """
        Create header bar
        """
        title_row = ft.Row([
            ft.Icon(
                ft.Icons.MONITOR,
                color=ThemeColors.PRIMARY,
                size=28
            ),
            ft.Text(
                "LED Animation Monitor",
                **ThemeStyles.header_text_style()
            )
        ], spacing=12)
        
        status_row = ft.Row([
            ft.Container(
                **ThemeStyles.status_indicator_style("active")
            ),
            ft.Text(
                "Engine Running",
                size=14,
                color=ThemeColors.SUCCESS
            ),
            ft.VerticalDivider(width=1),
            ft.Text(
                f"OSC: {EngineSettings.OSC.input_host}:{EngineSettings.OSC.input_port}",
                size=12,
                color=ThemeColors.TEXT_SECONDARY
            )
        ], spacing=8)
        
        header_content = ft.Row([
            title_row,
            status_row
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        return ft.Container(
            content=header_content,
            padding=20,
            bgcolor=ThemeColors.SURFACE,
            border=ft.border.only(bottom=ft.BorderSide(1, ThemeColors.PRIMARY))
        )
    
    def _start_update_loop(self):
        """
        Start update loop 
        """
        async def update_loop():
            while self.running and self.page:
                try:
                    await self._update_components()
                    await asyncio.sleep(1.0 / EngineSettings.MONITOR.refresh_rate)
                    
                except Exception as e:
                    logger.error(f"Error in monitor update loop: {e}")
                    await asyncio.sleep(1.0)
        
        self.update_task = asyncio.create_task(update_loop())
    
    async def _update_components(self):
        """
        Update all components
        """
        if not self.page or not self.running:
            return
            
        try:
            if self.status_display:
                await self.status_display.update()
                
            if self.log_viewer:
                await self.log_viewer.update()
                
            if self.stats_panel:
                await self.stats_panel.update()
            
            self.page.update()
            
        except Exception as e:
            logger.error(f"Lỗi cập nhật components: {e}")
    
    async def show_error_dialog(self, title: str, message: str):
        """
        Hiển thị dialog lỗi
        """
        if not self.page:
            return
            
        dialog = ft.AlertDialog(
            title=ft.Text(title, color=ThemeColors.ERROR),
            content=ft.Text(message, color=ThemeColors.TEXT_PRIMARY),
            actions=[
                ft.TextButton(
                    "OK",
                    on_click=lambda _: self._close_dialog(dialog)
                )
            ]
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _close_dialog(self, dialog):
        """
        Đóng dialog
        """
        dialog.open = False
        if self.page:
            self.page.update()