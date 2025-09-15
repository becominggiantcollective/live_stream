"""
Live Stream Automation Script

This script automates live streaming of videos from Odysee playlists
using OBS and streams to multiple platforms via RTMP.
"""

import asyncio
import logging
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Any

from src.config_manager import ConfigManager
from src.odysee_client import OdyseeClient
from src.obs_controller import OBSController
from src.stream_manager import StreamManager
from src.video_queue import VideoQueue

# Load environment variables
load_dotenv()

class LiveStreamBot:
    """Main orchestrator for the live streaming automation."""
    
    def __init__(self, config_path: str = "config.json"):
        self.config = ConfigManager(config_path)
        self.setup_logging()
        
        self.odysee_client = OdyseeClient(self.config)
        self.obs_controller = OBSController(self.config)
        self.stream_manager = StreamManager(self.config, self.obs_controller)
        self.video_queue = VideoQueue()
        
        self.running = False
        
    def setup_logging(self):
        """Setup logging configuration."""
        log_config = self.config.get('logging', {})
        level = getattr(logging, log_config.get('level', 'INFO'))
        log_file = log_config.get('file', 'livestream.log')
        
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self):
        """Initialize all components."""
        try:
            self.logger.info("Initializing Live Stream Bot...")
            
            # Connect to OBS (gracefully handle failure)
            connected = await self.obs_controller.connect()
            if not connected:
                self.logger.warning("Could not connect to OBS - streaming will be simulated")
            
            # Load playlists
            await self.load_playlists()
            
            self.logger.info("Live Stream Bot initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Live Stream Bot: {e}")
            return False
    
    async def load_playlists(self):
        """Load videos from configured Odysee playlists."""
        self.logger.info("Loading playlists from Odysee...")
        
        playlist_urls = self.config.get('odysee', {}).get('playlist_urls', [])
        
        for playlist_url in playlist_urls:
            try:
                videos = await self.odysee_client.get_playlist_videos(playlist_url)
                for video in videos:
                    self.video_queue.add_video(video)
                    
                self.logger.info(f"Loaded {len(videos)} videos from playlist: {playlist_url}")
                
            except Exception as e:
                self.logger.error(f"Failed to load playlist {playlist_url}: {e}")
        
        self.logger.info(f"Total videos in queue: {self.video_queue.size()}")
    
    async def start_streaming(self):
        """Start the live streaming process."""
        if not await self.initialize():
            return False
            
        self.running = True
        self.logger.info("Starting live streaming...")
        
        try:
            # Start streaming to configured platforms
            await self.stream_manager.start_streams()
            
            # Main streaming loop
            while self.running and not self.video_queue.is_empty():
                video = self.video_queue.get_next_video()
                if video:
                    await self.play_video(video)
                else:
                    # No more videos, reload playlists
                    await self.load_playlists()
                    if self.video_queue.is_empty():
                        self.logger.info("No more videos to stream. Stopping...")
                        break
                        
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal. Stopping...")
        except Exception as e:
            self.logger.error(f"Streaming error: {e}")
        finally:
            await self.stop_streaming()
            
    async def play_video(self, video: Dict[str, Any]):
        """Play a single video through OBS."""
        self.logger.info(f"Playing video: {video.get('title', 'Unknown')}")
        
        try:
            # Set up the video source in OBS
            await self.obs_controller.set_video_source(video['url'])
            
            # Wait for video duration (or a default time)
            duration = video.get('duration', 300)  # Default 5 minutes
            transition_delay = self.config.get('streaming', {}).get('video_transition_delay', 2)
            
            await asyncio.sleep(duration + transition_delay)
            
        except Exception as e:
            self.logger.error(f"Error playing video {video.get('title', 'Unknown')}: {e}")
    
    async def stop_streaming(self):
        """Stop streaming and cleanup."""
        self.running = False
        self.logger.info("Stopping live streaming...")
        
        try:
            await self.stream_manager.stop_streams()
            await self.obs_controller.disconnect()
            self.logger.info("Live streaming stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping stream: {e}")

def main():
    """Main entry point."""
    try:
        # Check if config file exists
        if not os.path.exists("config.json"):
            print("Config file not found. Please copy config.json.example to config.json and configure it.")
            return
            
        bot = LiveStreamBot()
        asyncio.run(bot.start_streaming())
        
    except Exception as e:
        print(f"Fatal error: {e}")

if __name__ == "__main__":
    main()