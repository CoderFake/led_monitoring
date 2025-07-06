"""
LED Animation Playback Engine
Entry point with logger mode configuration
"""

import asyncio
import sys
import argparse
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from src.core.animation_engine import AnimationEngine
from src.monitor.monitor_window import MonitorWindow
from config.settings import EngineSettings
from src.utils.logger import setup_logger, set_headless_mode

logger = setup_logger(__name__)


class LEDEngineApp:
    """
    Main application managing LED Animation Engine and Monitor UI
    """
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.engine = None
        self.monitor = None
        
        if self.headless:
            set_headless_mode()
            logger.info("Headless mode - Logger output to terminal + file")
        else:
            logger.info("UI mode - Logger output to UI + file")
    
    async def initialize(self):
        """
        Initialize engine and monitor
        """
        try:
            logger.info("Starting LED Animation Playback Engine...")
            
            logger.info("Creating AnimationEngine instance...")
            self.engine = AnimationEngine()
            
            logger.info("Starting AnimationEngine...")
            await self.engine.start()
            logger.info("AnimationEngine started successfully!")
            
            if not self.headless:
                logger.info("Starting Monitor UI...")
                self.monitor = MonitorWindow(self.engine)
                await self.monitor.start()
            
            logger.info("System ready")
            
        except Exception as e:
            logger.error(f"Initialization error: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            await self.cleanup()
            sys.exit(1)
    
    async def run(self):
        """
        Run engine in headless mode
        """
        if self.headless:
            logger.info("Running in headless mode...")
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("Received stop signal...")
                await self.cleanup()
    
    async def cleanup(self):
        """
        Cleanup resources
        """
        logger.info("Cleaning up resources...")
        
        if self.engine:
            await self.engine.stop()
            
        if self.monitor:
            await self.monitor.stop()


async def run_headless():
    """
    Run engine in headless mode
    """
    app = LEDEngineApp(headless=True)
    await app.initialize()
    await app.run()


def run_with_monitor():
    """
    Run engine with monitor UI
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
    Main entry point
    """
    parser = argparse.ArgumentParser(description='LED Animation Playback Engine')
    parser.add_argument('--headless', action='store_true', help='Run without monitor UI')
    
    args = parser.parse_args()
    
    if args.headless:
        logger.info("Running in headless mode - no Monitor UI")
        asyncio.run(run_headless())
    else:
        logger.info("Running with Monitor UI")
        run_with_monitor()


if __name__ == "__main__":
    main()