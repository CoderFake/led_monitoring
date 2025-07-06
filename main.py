"""
LED Animation Playback Engine
Entry point chính của hệ thống
"""

import asyncio
import sys
import argparse
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from src.core.animation_engine import AnimationEngine
from src.monitor.monitor_window import MonitorWindow
from config.settings import EngineSettings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class LEDEngineApp:
    """
    Ứng dụng chính quản lý LED Animation Engine và Monitor UI
    """
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.engine = None
        self.monitor = None
        
    async def initialize(self):
        """
        Khởi tạo engine và monitor
        """
        try:
            logger.info("Khởi động LED Animation Playback Engine...")
            
            logger.info("Tạo AnimationEngine instance...")
            self.engine = AnimationEngine()
            
            logger.info("Đang khởi động AnimationEngine...")
            await self.engine.start()
            logger.info("AnimationEngine đã khởi động thành công!")
            
            if not self.headless:
                logger.info("Khởi động Monitor UI...")
                self.monitor = MonitorWindow(self.engine)
                await self.monitor.start()
            
            logger.info("Hệ thống đã sẵn sàng")
            
        except Exception as e:
            logger.error(f"Lỗi khởi tạo: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            await self.cleanup()
            sys.exit(1)
    
    async def run(self):
        """
        Chạy engine trong headless mode
        """
        if self.headless:
            logger.info("Chạy trong chế độ headless...")
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("Nhận tín hiệu dừng...")
                await self.cleanup()
    
    async def cleanup(self):
        """
        Dọn dẹp tài nguyên
        """
        logger.info("Đang dọn dẹp tài nguyên...")
        
        if self.engine:
            await self.engine.stop()
            
        if self.monitor:
            await self.monitor.stop()


async def run_headless():
    """
    Chạy engine trong chế độ headless
    """
    app = LEDEngineApp(headless=True)
    await app.initialize()
    await app.run()


def run_with_monitor():
    """
    Chạy engine với monitor UI
    """
    import flet as ft
    
    async def main(page: ft.Page):
        app = LEDEngineApp(headless=False)
        await app.initialize()
        
        if app.monitor:
            await app.monitor.setup_page(page)
    
    ft.app(target=main, view=ft.WEB_BROWSER if EngineSettings.MONITOR.web_mode else ft.FLET_APP)


def main():
    """
    Entry point chính
    """
    parser = argparse.ArgumentParser(description='LED Animation Playback Engine')
    parser.add_argument('--headless', action='store_true', 
                       help='Chạy không có monitor UI')
    parser.add_argument('--pure-headless', action='store_true',
                       help='Chạy hoàn toàn headless, không mở bất kỳ UI nào')
    parser.add_argument('--config', type=str, 
                       help='Đường dẫn file config tùy chỉnh')
    parser.add_argument('--no-monitor', action='store_true',
                       help='Tắt monitor UI (tương tự --headless)')
    
    args = parser.parse_args()
    
    if args.config:
        EngineSettings.load_from_file(args.config)
    
    # Kiểm tra các tùy chọn headless
    is_headless = args.headless or args.pure_headless or args.no_monitor
    
    if is_headless:
        logger.info("Chạy trong chế độ headless - không có Monitor UI")
        asyncio.run(run_headless())
    else:
        logger.info("Chạy với Monitor UI")
        run_with_monitor()


if __name__ == "__main__":
    main()