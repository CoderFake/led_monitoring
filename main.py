"""
LED Animation Playback Engine
"""

import asyncio
import sys
import argparse
import signal
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from src.core.animation_engine import AnimationEngine
from src.monitor.monitor_window import MonitorWindow
from config.settings import EngineSettings
from src.utils.logger import setup_logger, set_headless_mode

logger = None
app_instance = None


class LEDEngineApp:
    """
    Main application
    """
    
    def __init__(self, headless: bool = False):
        global logger
        
        self.headless = headless
        self.engine = None
        self.monitor = None
        self.running = False
        
        if self.headless:
            set_headless_mode()
        
        logger = setup_logger(__name__)
        
        if self.headless:
            logger.info("Headless mode activated - Logger configured for terminal output")
        else:
            logger.info("UI mode - Logger output to UI + file")
    
    async def initialize(self):
        """
        Initialize engine and monitor
        """
        global logger
        try:
            logger.info("Starting LED Animation Playback Engine...")
            
            self.engine = AnimationEngine()
            
            await self.engine.start()
            
            if not self.headless:
                logger.info("Starting Monitor UI...")
                self.monitor = MonitorWindow(self.engine)
                await self.monitor.start()
            
            self.running = True
            logger.info("System ready - LED Animation Playback Engine is running")
            
        except Exception as e:
            if logger:
                logger.error(f"Initialization error: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
            else:
                print(f"FATAL ERROR: {e}", file=sys.stderr, flush=True)
            await self.cleanup()
            sys.exit(1)
    
    async def run(self):
        """
        Run engine in headless mode
        """
        if self.headless:
            logger.info("Running in headless mode...")
            try:
                while self.running:
                    await asyncio.sleep(1)
                    
                    if hasattr(self.engine, 'get_stats'):
                        stats = self.engine.get_stats()
                        
                        if stats.frame_count % 3600 == 0 and stats.frame_count > 0:
                            logger.info(f"Engine Status: Frames={stats.frame_count}, FPS={stats.actual_fps:.1f}, LEDs={stats.active_leds}/{stats.total_leds}, Runtime={stats.animation_time:.1f}s")
                    
            except KeyboardInterrupt:
                logger.info("Received stop signal (Ctrl+C)...")
                self.running = False
            except Exception as e:
                logger.error(f"Error in run loop: {e}")
                self.running = False
            
            await self.cleanup()
    
    async def cleanup(self):
        """
        Cleanup resources
        """
        logger.info("Cleaning up resources...")
        
        self.running = False
        
        if self.engine:
            try:
                await self.engine.stop()
                logger.info("Animation Engine stopped")
            except Exception as e:
                logger.error(f"Error stopping engine: {e}")
            
        if self.monitor:
            try:
                await self.monitor.stop()
                logger.info("Monitor stopped")
            except Exception as e:
                logger.error(f"Error stopping monitor: {e}")
        
        logger.info("Cleanup completed")


def signal_handler(signum, frame):
    """
    Handle system signals for graceful shutdown
    """
    global app_instance
    print("\nReceived shutdown signal, stopping engine...", flush=True)
    if app_instance:
        app_instance.running = False


async def run_headless():
    """
    Run engine in headless mode
    """
    global app_instance
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    app_instance = LEDEngineApp(headless=True)
    await app_instance.initialize()
    await app_instance.run()


def run_with_monitor():
    """
    Run engine with monitor UI
    """
    global app_instance
    import flet as ft
    
    async def main(page: ft.Page):
        global app_instance
        app_instance = LEDEngineApp(headless=False)
        await app_instance.initialize()
        
        if app_instance.monitor:
            await app_instance.monitor.setup_page(page)
    
    try:
        ft.app(target=main, view=ft.WEB_BROWSER if EngineSettings.MONITOR.web_mode else ft.FLET_APP)
    except KeyboardInterrupt:
        print("Monitor UI interrupted", flush=True)
    except Exception as e:
        print(f"Monitor UI error: {e}", flush=True)


def main():
    """
    Main entry point
    """
    parser = argparse.ArgumentParser(description='LED Animation Playback Engine')
    parser.add_argument('--headless', action='store_true', help='Run without monitor UI')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        os.environ['LOG_LEVEL'] = 'DEBUG'
    
    if args.headless:
        try:
            asyncio.run(run_headless())
        except KeyboardInterrupt:
            print("Engine stopped by user", flush=True)
        except Exception as e:
            print(f"Fatal error: {e}", file=sys.stderr, flush=True)
            sys.exit(1)
    else:
        print("Starting LED Animation Playback Engine with Monitor UI...", flush=True)
        run_with_monitor()


if __name__ == "__main__":
    main()