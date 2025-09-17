#!/usr/bin/env python3
"""
Cloud Drive Integration Example

This example shows how to use the live streaming bot with cloud drive files
instead of or in addition to Odysee playlists.
"""

import asyncio
import json
import logging
import os
from pathlib import Path

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config_manager import ConfigManager
from cloud_drive_client import CloudDriveClient
from obs_controller import OBSController
from stream_manager import StreamManager
from video_queue import VideoQueue

async def run_cloud_drive_example():
    """Run an example using cloud drive files."""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Cloud Drive Live Stream Example")
    
    try:
        # Create or load configuration
        config_path = "cloud_drive_config.json"
        create_example_config(config_path)
        
        config = ConfigManager(config_path)
        
        # Create video queue
        video_queue = VideoQueue(shuffle=True)
        
        # Initialize cloud drive client
        cloud_drive_client = CloudDriveClient(config)
        
        # Load cloud drive files
        cloud_config = config.get('video_sources', {}).get('cloud_drive', {})
        files = cloud_config.get('files', [])
        
        if files:
            logger.info("Loading videos from cloud drive...")
            videos = await cloud_drive_client.get_video_files(files)
            
            for video in videos:
                video_queue.add_video(video)
                
            logger.info(f"Loaded {len(videos)} videos from cloud drive")
        else:
            logger.info("No cloud drive files configured, using sample videos...")
            sample_videos = cloud_drive_client.get_sample_files()
            for video in sample_videos:
                video_queue.add_video(video)
            logger.info(f"Added {len(sample_videos)} sample videos")
        
        # Initialize OBS controller
        obs_controller = OBSController(config)
        connected = await obs_controller.connect()
        if connected:
            logger.info("Connected to OBS")
        else:
            logger.warning("Could not connect to OBS - will run in simulation mode")
        
        # Initialize stream manager
        stream_manager = StreamManager(config, obs_controller)
        logger.info("Stream manager initialized")
        
        # Show configuration summary
        logger.info("=== Configuration Summary ===")
        logger.info(f"Total videos in queue: {video_queue.size()}")
        
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
            videos_played = 0
            max_videos = 3  # Limit for demo
            
            while not video_queue.is_empty() and videos_played < max_videos:
                video = video_queue.get_next_video()
                if video:
                    logger.info(f"Now playing: {video['title']}")
                    logger.info(f"  Source: {video.get('provider', 'Unknown')}")
                    logger.info(f"  Original URL: {video.get('original_url', 'N/A')}")
                    logger.info(f"  Stream URL: {video['url']}")
                    
                    # Set video source in OBS
                    await obs_controller.set_video_source(video['url'])
                    
                    # Simulate video duration (shortened for demo)
                    await asyncio.sleep(3)  # Play for 3 seconds instead of full duration
                    videos_played += 1
                    
                else:
                    break
            
            logger.info(f"Demo completed - played {videos_played} videos")
            
        else:
            logger.error("Failed to start streams")
        
        # Stop streams and cleanup
        await stream_manager.stop_streams()
        await obs_controller.disconnect()
        await cloud_drive_client.close()
        
        logger.info("Example completed successfully")
        
    except Exception as e:
        logger.error(f"Example failed: {e}")
        raise

def create_example_config(config_path: str):
    """Create an example configuration file for cloud drive usage."""
    
    if os.path.exists(config_path):
        return  # Don't overwrite existing config
    
    example_config = {
        "video_sources": {
            "odysee": {
                "enabled": False,
                "playlist_urls": [],
                "api_base_url": "https://api.odysee.com"
            },
            "cloud_drive": {
                "enabled": True,
                "files": [
                    {
                        "url": "https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/view",
                        "title": "Sample Google Drive Video",
                        "duration": 300,
                        "description": "Example video from Google Drive"
                    },
                    {
                        "url": "https://www.dropbox.com/s/samplefileid/video.mp4?dl=0",
                        "title": "Sample Dropbox Video",
                        "duration": 420,
                        "description": "Example video from Dropbox"
                    },
                    "https://onedrive.live.com/download?cid=SAMPLE&resid=SAMPLE",
                    "https://example.com/direct-video-url.mp4"
                ]
            }
        },
        "obs": {
            "websocket_host": "localhost",
            "websocket_port": 4455,
            "websocket_password": ""
        },
        "streaming": {
            "platforms": {
                "rumble": {
                    "enabled": False,
                    "rtmp_url": "rtmp://ingest.rumble.com/live/",
                    "stream_key": "YOUR_RUMBLE_STREAM_KEY"
                },
                "youtube": {
                    "enabled": False,
                    "rtmp_url": "rtmp://a.rtmp.youtube.com/live2/",
                    "stream_key": "YOUR_YOUTUBE_STREAM_KEY"
                },
                "twitch": {
                    "enabled": False,
                    "rtmp_url": "rtmp://live.twitch.tv/live/",
                    "stream_key": "YOUR_TWITCH_STREAM_KEY"
                }
            },
            "reconnect_attempts": 5,
            "reconnect_delay": 30,
            "video_transition_delay": 2
        },
        "logging": {
            "level": "INFO",
            "file": "cloud_drive_example.log"
        }
    }
    
    with open(config_path, 'w') as f:
        json.dump(example_config, f, indent=2)
    
    print(f"Created example configuration: {config_path}")

def main():
    """Main entry point for the cloud drive example."""
    print("Cloud Drive Live Stream Example")
    print("=" * 50)
    print()
    print("This example demonstrates how to use cloud drive files")
    print("as video sources instead of Odysee playlists.")
    print()
    print("Supported cloud providers:")
    print("- Google Drive")
    print("- Dropbox")
    print("- OneDrive")
    print("- Direct URLs")
    print()
    
    try:
        asyncio.run(run_cloud_drive_example())
    except KeyboardInterrupt:
        print("\nExample interrupted by user")
    except Exception as e:
        print(f"\nExample failed: {e}")

if __name__ == "__main__":
    main()