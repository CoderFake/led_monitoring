"""
Theme configuration for monitor UI
"""

import flet as ft
from typing import Dict, Any


class ThemeColors:
    """
    Define theme colors
    """
    
    PRIMARY = "#00e676"
    PRIMARY_DARK = "#00c853" 
    SECONDARY = "#03dac6"
    BACKGROUND = "#0a0a0a"
    SURFACE = "#1a1a1a"
    SURFACE_VARIANT = "#2a2a2a"
    ERROR = "#ff5252"
    WARNING = "#ff9800"
    SUCCESS = "#4caf50"
    INFO = "#2196f3"
    
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#b0b0b0"
    TEXT_DISABLED = "#606060"
    
    LED_OFF = "#1a1a1a"
    LED_ACTIVE = "#00e676"
    LED_SHADOW = "#00e67640"


class ThemeStyles:
    """
    Define styles components
    """
    
    @staticmethod
    def card_style() -> Dict[str, Any]:
        return {
            "bgcolor": ThemeColors.SURFACE,
            "border_radius": 12,
            "padding": 16,
            "border": ft.border.all(1, ThemeColors.SURFACE_VARIANT)
        }
    
    @staticmethod
    def button_primary_style() -> Dict[str, Any]:
        return {
            "bgcolor": ThemeColors.PRIMARY,
            "color": ThemeColors.BACKGROUND,
            "style": ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                elevation=2
            )
        }
    
    @staticmethod
    def button_secondary_style() -> Dict[str, Any]:
        return {
            "bgcolor": ThemeColors.SURFACE_VARIANT,
            "color": ThemeColors.TEXT_PRIMARY,
            "style": ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                elevation=1
            )
        }
    
    @staticmethod
    def text_field_style() -> Dict[str, Any]:
        return {
            "bgcolor": ThemeColors.SURFACE_VARIANT,
            "border_color": ThemeColors.PRIMARY,
            "focused_border_color": ThemeColors.PRIMARY_DARK,
            "color": ThemeColors.TEXT_PRIMARY,
            "border_radius": 8
        }
    
    @staticmethod
    def header_text_style() -> Dict[str, Any]:
        return {
            "size": 24,
            "weight": ft.FontWeight.BOLD,
            "color": ThemeColors.TEXT_PRIMARY
        }
    
    @staticmethod
    def subheader_text_style() -> Dict[str, Any]:
        return {
            "size": 16,
            "weight": ft.FontWeight.W_500,
            "color": ThemeColors.TEXT_SECONDARY
        }
    
    @staticmethod
    def body_text_style() -> Dict[str, Any]:
        return {
            "size": 14,
            "color": ThemeColors.TEXT_PRIMARY
        }
    
    @staticmethod
    def status_indicator_style(status: str) -> Dict[str, Any]:
        color_map = {
            "active": ThemeColors.SUCCESS,
            "inactive": ThemeColors.ERROR,
            "warning": ThemeColors.WARNING,
            "info": ThemeColors.INFO
        }
        
        return {
            "width": 12,
            "height": 12,
            "bgcolor": color_map.get(status, ThemeColors.TEXT_DISABLED),
            "border_radius": 6
        }


class MonitorTheme:
    """
    Theme chính cho monitor UI
    """
    
    @staticmethod
    def get_page_theme() -> ft.Theme:
        """
        Tạo theme cho page
        """
        return ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=ThemeColors.PRIMARY,
                on_primary=ThemeColors.BACKGROUND,
                secondary=ThemeColors.SECONDARY,
                surface=ThemeColors.SURFACE,
                background=ThemeColors.BACKGROUND,
                error=ThemeColors.ERROR
            )
        )
    
    @staticmethod
    def configure_page(page: ft.Page):
        """
        Configure page with theme
        """
        page.theme_mode = ft.ThemeMode.DARK
        page.theme = MonitorTheme.get_page_theme()
        page.bgcolor = ThemeColors.BACKGROUND
        page.title = "LED Animation Monitor"
        page.window.width = 1200
        page.window.height = 800
        page.window.resizable = True
        page.window.center()
    
    @staticmethod
    def create_led_indicator(active: bool = False, brightness: float = 1.0) -> ft.Container:
        """
        Create LED indicator with theme
        """
        if active:
            color = ThemeColors.LED_ACTIVE
            shadow = ft.BoxShadow(
                spread_radius=1,
                blur_radius=int(4 * brightness),
                color=ThemeColors.LED_SHADOW
            )
        else:
            color = ThemeColors.LED_OFF
            shadow = None
            
        return ft.Container(
            width=8,
            height=8,
            bgcolor=color,
            border_radius=4,
            shadow=shadow
        )
    
    @staticmethod
    def create_gradient_background() -> str:
        """
        Create gradient background
        """
        return f"linear-gradient(135deg, {ThemeColors.BACKGROUND} 0%, {ThemeColors.SURFACE} 100%)"