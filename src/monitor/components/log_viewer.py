"""
Log Viewer - Component to view logs in realtime
"""

import flet as ft
import logging
import threading
from typing import List, Dict, Any
from collections import deque

from config.theme import ThemeColors, ThemeStyles


class LogEntry:
    """
    Log entry data
    """
    def __init__(self, level: str, message: str, timestamp: str):
        self.level = level
        self.message = message
        self.timestamp = timestamp


class LogHandler(logging.Handler):
    """
    Custom log handler to capture logs
    """
    
    def __init__(self, log_viewer):
        super().__init__()
        self.log_viewer = log_viewer
        self.setLevel(logging.INFO)
    
    def emit(self, record):
        try:
            msg = self.format(record)
            timestamp = self.formatter.formatTime(record, '%H:%M:%S')
            
            entry = LogEntry(
                level=record.levelname,
                message=msg,
                timestamp=timestamp
            )
            
            self.log_viewer.add_log_entry(entry)
            
        except Exception as e:
            print(f"[LOG ERROR] {e}", flush=True)


class LogViewer(ft.Container):
    """
    Component to view logs in realtime
    """
    
    def __init__(self):
        super().__init__()
        
        self._lock = threading.Lock()
        
        self.log_entries: deque = deque(maxlen=1000)
        self.log_display = ft.ListView(
            auto_scroll=True,
            spacing=2,
            expand=True,
            adaptive=True
        )
        
        self.filter_level = "ALL"
        self.filter_text = ""
        self.page = None
        self.needs_update = False
        
        self._setup_log_handler()
        self._build_ui()
    
    def _setup_log_handler(self):
        """
        Setup log handler to capture logs
        """
        self.log_handler = LogHandler(self)
        self.log_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(name)s: %(message)s')
        self.log_handler.setFormatter(formatter)
        
        root_logger = logging.getLogger()
        root_logger.addHandler(self.log_handler)
        
        loggers_to_monitor = [
            'src.core.osc_handler',
            'src.core.animation_engine', 
            'src.core.scene_manager',
            'src.core.led_output',
            'OSC',
            '__main__'
        ]
        
        for logger_name in loggers_to_monitor:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.INFO)
            logger.propagate = True 
    
    def _build_ui(self):
        """
        Build UI component 
        """
        title = ft.Text(
            "System Logs",
            **ThemeStyles.subheader_text_style()
        )
        
        controls_row = ft.Row([
            ft.Dropdown(
                label="Level",
                value=self.filter_level,
                options=[
                    ft.dropdown.Option("ALL"),
                    ft.dropdown.Option("INFO"),
                    ft.dropdown.Option("WARNING"),
                    ft.dropdown.Option("ERROR")
                ],
                width=120,
                on_change=self._on_filter_change,
                **ThemeStyles.text_field_style()
            ),
            ft.TextField(
                label="Filter",
                hint_text="Search logs...",
                width=200,
                on_change=self._on_search_change,
                **ThemeStyles.text_field_style()
            ),
            ft.IconButton(
                icon=ft.Icons.CLEAR,
                tooltip="Clear logs",
                on_click=self._on_clear_logs,
                icon_color=ThemeColors.TEXT_SECONDARY
            )
        ], spacing=12)
        
        card_style = ThemeStyles.card_style()
        card_style["padding"] = 8
        log_container = ft.Container(
            content=self.log_display,
            **card_style,
            expand=True
        )
        
        self.content = ft.Column([
            title,
            controls_row,
            log_container
        ], spacing=16, expand=True)
        
        self.padding = 0
        self.expand = True
    
    def add_log_entry(self, entry: LogEntry):
        """
        Add new log entry
        """
        with self._lock:
            self.log_entries.append(entry)
            self.needs_update = True
    
    def set_page(self, page):
        """
        Set page reference to update UI
        """
        self.page = page
    
    def _update_display_sync(self):
        """
        Update display synchronously
        """
        try:
            filtered_entries = self._filter_logs()
            self._rebuild_log_display(filtered_entries)
            
            if self.page:
                try:
                    self.page.update()
                except Exception as update_error:
                    print(f"[LOG VIEWER UPDATE ERROR] {update_error}", flush=True)
                    
        except Exception as e:
            print(f"[LOG VIEWER ERROR] {e}", flush=True)
    
    async def update(self):
        """
        Update log display
        """
        try:
            with self._lock:
                if not self.needs_update:
                    return
                    
                filtered_entries = self._filter_logs()
                self._rebuild_log_display(filtered_entries)
                self.needs_update = False
                
        except Exception as e:
            print(f"[LOG VIEWER UPDATE] Error: {e}", flush=True)
    

    
    def _filter_logs(self) -> List[LogEntry]:
        """
        Filter logs according to filter criteria
        """
        filtered = []
        
        level_priority = {
            "INFO": 1,
            "WARNING": 2,
            "ERROR": 3
        }
        
        if self.filter_level == "ALL":
            min_priority = -1  
        else:
            min_priority = level_priority.get(self.filter_level, 1)
        
        for entry in self.log_entries:
            entry_priority = level_priority.get(entry.level, 1)
            
            if self.filter_level != "ALL" and entry_priority < min_priority:
                continue
                
            if self.filter_text and self.filter_text.lower() not in entry.message.lower():
                continue
                
            filtered.append(entry)
        
        return filtered[-100:]
    
    def _rebuild_log_display(self, entries: List[LogEntry]):
        """
        Rebuild log display with new entries
        """
        self.log_display.controls.clear()
        
        for entry in entries:
            log_row = self._create_log_row(entry)
            self.log_display.controls.append(log_row)
    
    def _create_log_row(self, entry: LogEntry) -> ft.Container:
        """
        Create row for a log entry
        """
        level_colors = {
            "INFO": ThemeColors.INFO,
            "WARNING": ThemeColors.WARNING,
            "ERROR": ThemeColors.ERROR
        }
        
        level_color = level_colors.get(entry.level, ThemeColors.TEXT_PRIMARY)
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(
                        entry.timestamp,
                        size=10,
                        color=ThemeColors.TEXT_DISABLED,
                        width=60
                    ),
                    ft.Text(
                        entry.level,
                        size=10,
                        color=level_color,
                        width=70,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Text(
                        entry.message,
                        size=11,
                        color=ThemeColors.TEXT_PRIMARY,
                        expand=True,
                        no_wrap=False,
                        overflow=ft.TextOverflow.VISIBLE
                    )
                ], spacing=8, alignment=ft.MainAxisAlignment.START)
            ], spacing=0, tight=True),
            padding=ft.padding.symmetric(horizontal=8, vertical=2),
            bgcolor=ThemeColors.SURFACE_VARIANT if entry.level == "ERROR" else None,
            border_radius=4
        )
    
    def _on_filter_change(self, e):
        """
        Handle filter level change
        """
        self.filter_level = e.control.value
        with self._lock:
            self.needs_update = True
        self._update_display_sync()
    
    def _on_search_change(self, e):
        """
        Handle search text change
        """
        self.filter_text = e.control.value
        with self._lock:
            self.needs_update = True
        self._update_display_sync()
    
    def _on_clear_logs(self, e):
        """
        Handle clear logs
        """
        with self._lock:
            self.log_entries.clear()
            self.log_display.controls.clear()
            self.needs_update = True
        self._update_display_sync()