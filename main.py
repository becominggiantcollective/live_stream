"""
Live Stream Automation Script

This script automates live streaming of videos from Odysee playlists
using OBS and streams to multiple platforms via RTMP.
"""

import asyncio
import logging
import json
import os
import argparse
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Any

from src.config_manager import ConfigManager
from src.odysee_client import OdyseeClient
from src.cloud_drive_client import CloudDriveClient
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
        self.cloud_drive_client = CloudDriveClient(self.config)
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
            
            # Load video sources
            await self.load_video_sources()
            
            self.logger.info("Live Stream Bot initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Live Stream Bot: {e}")
            return False
    
    async def load_video_sources(self):
        """Load videos from configured sources (Odysee playlists and/or cloud drive files)."""
        self.logger.info("Loading video sources...")
        
        total_videos_loaded = 0
        
        # Check video sources configuration (new format)
        video_sources = self.config.get('video_sources', {})
        
        # Load from Odysee if enabled
        odysee_config = video_sources.get('odysee', {}) if video_sources else self.config.get('odysee', {})
        odysee_enabled = odysee_config.get('enabled', True)  # Default true for backwards compatibility
        
        if odysee_enabled:
            total_videos_loaded += await self.load_odysee_playlists(odysee_config)
        
        # Load from cloud drive if enabled
        cloud_drive_config = video_sources.get('cloud_drive', {})
        cloud_drive_enabled = cloud_drive_config.get('enabled', False)
        
        if cloud_drive_enabled:
            total_videos_loaded += await self.load_cloud_drive_files(cloud_drive_config)
        
        self.logger.info(f"Total videos loaded from all sources: {total_videos_loaded}")
        
        # If no videos loaded, show helpful message
        if total_videos_loaded == 0:
            self.logger.warning("No videos loaded from any source. Please check your configuration.")
            self.logger.warning("Enable either Odysee playlists or cloud drive files in your config.")
    
    async def load_odysee_playlists(self, odysee_config: Dict[str, Any]) -> int:
        """Load videos from Odysee playlists.
        
        Args:
            odysee_config: Odysee configuration
            
        Returns:
            Number of videos loaded
        """
        self.logger.info("Loading videos from Odysee playlists...")
        videos_loaded = 0
        
        playlist_urls = odysee_config.get('playlist_urls', [])
        
        for playlist_url in playlist_urls:
            try:
                videos = await self.odysee_client.get_playlist_videos(playlist_url)
                for video in videos:
                    self.video_queue.add_video(video)
                    
                self.logger.info(f"Loaded {len(videos)} videos from playlist: {playlist_url}")
                videos_loaded += len(videos)
                
            except Exception as e:
                self.logger.error(f"Failed to load playlist {playlist_url}: {e}")
        
        return videos_loaded
    
    async def load_cloud_drive_files(self, cloud_drive_config: Dict[str, Any]) -> int:
        """Load videos from cloud drive files.
        
        Args:
            cloud_drive_config: Cloud drive configuration
            
        Returns:
            Number of videos loaded
        """
        self.logger.info("Loading videos from cloud drive...")
        videos_loaded = 0
        
        files = cloud_drive_config.get('files', [])
        
        try:
            videos = await self.cloud_drive_client.get_video_files(files)
            for video in videos:
                self.video_queue.add_video(video)
                
            self.logger.info(f"Loaded {len(videos)} videos from cloud drive")
            videos_loaded = len(videos)
            
        except Exception as e:
            self.logger.error(f"Failed to load cloud drive files: {e}")
        
        return videos_loaded
    
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
                    # No more videos, reload video sources
                    await self.load_video_sources()
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
            await self.odysee_client.close()
            await self.cloud_drive_client.close()
            self.logger.info("Live streaming stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping stream: {e}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Live Stream Automation Bot')
    parser.add_argument('--config', '-c', default='config.json', 
                        help='Path to configuration file (default: config.json)')
    parser.add_argument('--validate-only', action='store_true',
                        help='Only validate configuration and exit')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set up logging level
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    try:
        # Check if config file exists
        if not os.path.exists(args.config):
            print(f"Config file not found: {args.config}")
            print("Please copy config.json.example to config.json and configure it.")
            print("Run 'python setup.py' to help with initial setup.")
            return 1
        
        # Validate configuration before starting
        try:
            from src.config_manager import ConfigManager
            config = ConfigManager(args.config)
            is_valid, issues = config.validate_config()
            
            if not is_valid:
                print("Configuration validation failed:")
                for issue in issues:
                    print(f"  - {issue}")
                print("\nPlease fix these issues before running the live stream bot.")
                print("Run 'python setup.py' to validate your configuration.")
                return 1
            else:
                print("✓ Configuration is valid")
                
            if args.validate_only:
                print("Configuration validation completed successfully.")
                return 0
                
        except Exception as e:
            print(f"Error validating configuration: {e}")
            return 1
        
        # Start the bot
        print("Starting Live Stream Bot...")
        bot = LiveStreamBot(args.config)
        asyncio.run(bot.start_streaming())
        return 0
        
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
        return 0
    except Exception as e:
        print(f"Fatal error: {e}")
        logging.exception("Fatal error occurred")
        return 1

if __name__ == "__main__":
    exit(main())