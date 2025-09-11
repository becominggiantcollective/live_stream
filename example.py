#!/usr/bin/env python3
"""
Live Stream Bot Example

This example shows how to use the live streaming bot with custom settings.
"""

import asyncio
import json
import logging
from pathlib import Path

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config_manager import ConfigManager
from obs_controller import OBSController
from stream_manager import StreamManager
from video_queue import VideoQueue

async def run_example():
    """Run a simple example of the live streaming bot."""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Live Stream Bot Example")
    
    try:
        # Load configuration
        config = ConfigManager("config.json")
        
        # Create video queue with some example videos
        video_queue = VideoQueue(shuffle=True)
        
        # Add some sample videos
        sample_videos = [
            {
                'id': 'video_1',
                'title': 'Example Video 1',
                'url': 'https://example.com/video1.mp4',
                'duration': 180,
                'channel': 'Example Channel',
                'thumbnail': 'https://example.com/thumb1.jpg'
            },
            {
                'id': 'video_2', 
                'title': 'Example Video 2',
                'url': 'https://example.com/video2.mp4',
                'duration': 240,
                'channel': 'Example Channel',
                'thumbnail': 'https://example.com/thumb2.jpg'
            }
        ]
        
        video_queue.add_videos(sample_videos)
        logger.info(f"Added {video_queue.size()} videos to queue")
        
        # Initialize OBS controller
        obs_controller = OBSController(config)
        if await obs_controller.connect():
            logger.info("Connected to OBS (or simulated)")
        else:
            logger.error("Failed to connect to OBS")
            return
        
        # Initialize stream manager
        stream_manager = StreamManager(config)
        logger.info("Stream manager initialized")
        
        # Show stream status
        status = stream_manager.get_stream_status()
        logger.info("Platform status:")
        for platform, info in status.items():
            logger.info(f"  {platform}: {info['status']} (enabled: {info['enabled']})")
        
        # Start streaming to enabled platforms
        logger.info("Starting streams...")
        success = await stream_manager.start_streams()
        
        if success:
            logger.info("Streams started successfully")
            
            # Simulate playing videos
            while not video_queue.is_empty():
                video = video_queue.get_next_video()
                if video:
                    logger.info(f"Now playing: {video['title']}")
                    
                    # Set video source in OBS
                    await obs_controller.set_video_source(video['url'])
                    
                    # Simulate video duration (shortened for demo)
                    await asyncio.sleep(5)  # Play for 5 seconds instead of full duration
                    
                else:
                    break
            
            logger.info("Finished playing all videos")
            
        else:
            logger.error("Failed to start streams")
        
        # Stop streams
        await stream_manager.stop_streams()
        await obs_controller.disconnect()
        
        logger.info("Example completed successfully")
        
    except Exception as e:
        logger.error(f"Example failed: {e}")

def main():
    """Main entry point for the example."""
    if not Path("config.json").exists():
        print("Config file not found. Please run 'python setup.py' first.")
        return
        
    asyncio.run(run_example())

if __name__ == "__main__":
    main()