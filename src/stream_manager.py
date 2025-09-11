"""
Stream Manager for Multi-Platform Broadcasting

Handles streaming to multiple platforms simultaneously with reconnection logic.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

class StreamStatus(Enum):
    """Stream status enumeration."""
    STOPPED = "stopped"
    STARTING = "starting"
    STREAMING = "streaming"
    RECONNECTING = "reconnecting"
    FAILED = "failed"

@dataclass
class StreamInfo:
    """Information about a streaming platform."""
    name: str
    rtmp_url: str
    stream_key: str
    enabled: bool
    status: StreamStatus = StreamStatus.STOPPED
    retry_count: int = 0
    last_error: Optional[str] = None

class StreamManager:
    """Manages streaming to multiple platforms."""
    
    def __init__(self, config_manager):
        """Initialize stream manager.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        
        # Stream configuration
        self.streams = {}
        self.load_stream_configs()
        
        # Reconnection settings
        streaming_config = self.config.get('streaming', {})
        self.max_retry_attempts = streaming_config.get('reconnect_attempts', 5)
        self.retry_delay = streaming_config.get('reconnect_delay', 30)
        
        # Track streaming tasks
        self.streaming_tasks = {}
        self.reconnect_tasks = {}
        
    def load_stream_configs(self):
        """Load streaming platform configurations."""
        platforms = self.config.get_enabled_platforms()
        
        for platform_name, platform_config in platforms.items():
            stream_info = StreamInfo(
                name=platform_name,
                rtmp_url=platform_config.get('rtmp_url', ''),
                stream_key=platform_config.get('stream_key', ''),
                enabled=platform_config.get('enabled', False)
            )
            
            self.streams[platform_name] = stream_info
            self.logger.info(f"Loaded stream config for {platform_name}")
    
    async def start_streams(self) -> bool:
        """Start streaming to all enabled platforms.
        
        Returns:
            True if at least one stream started successfully
        """
        self.logger.info("Starting streams to all enabled platforms...")
        
        successful_streams = 0
        
        for platform_name, stream_info in self.streams.items():
            if not stream_info.enabled:
                continue
                
            if await self.start_stream(platform_name):
                successful_streams += 1
        
        success = successful_streams > 0
        if success:
            self.logger.info(f"Successfully started {successful_streams} streams")
        else:
            self.logger.error("Failed to start any streams")
            
        return success
    
    async def start_stream(self, platform_name: str) -> bool:
        """Start streaming to a specific platform.
        
        Args:
            platform_name: Name of the platform to stream to
            
        Returns:
            True if stream started successfully
        """
        if platform_name not in self.streams:
            self.logger.error(f"Unknown platform: {platform_name}")
            return False
        
        stream_info = self.streams[platform_name]
        
        if stream_info.status == StreamStatus.STREAMING:
            self.logger.info(f"Stream to {platform_name} is already active")
            return True
        
        self.logger.info(f"Starting stream to {platform_name}...")
        stream_info.status = StreamStatus.STARTING
        
        try:
            # Validate stream configuration
            if not stream_info.rtmp_url or not stream_info.stream_key:
                raise ValueError(f"Missing RTMP URL or stream key for {platform_name}")
            
            # In a real implementation, this would configure OBS for this specific platform
            # and start the actual streaming process
            
            # For now, we simulate the streaming process
            success = await self._simulate_stream_start(stream_info)
            
            if success:
                stream_info.status = StreamStatus.STREAMING
                stream_info.retry_count = 0
                stream_info.last_error = None
                
                # Start monitoring task
                task = asyncio.create_task(self._monitor_stream(platform_name))
                self.streaming_tasks[platform_name] = task
                
                self.logger.info(f"Successfully started stream to {platform_name}")
                return True
            else:
                raise Exception(f"Failed to start stream to {platform_name}")
                
        except Exception as e:
            stream_info.status = StreamStatus.FAILED
            stream_info.last_error = str(e)
            self.logger.error(f"Failed to start stream to {platform_name}: {e}")
            
            # Schedule reconnection attempt
            await self._schedule_reconnect(platform_name)
            return False
    
    async def stop_streams(self):
        """Stop all active streams."""
        self.logger.info("Stopping all streams...")
        
        # Cancel all streaming tasks
        for platform_name in list(self.streaming_tasks.keys()):
            await self.stop_stream(platform_name)
        
        # Cancel all reconnection tasks
        for task in self.reconnect_tasks.values():
            if not task.done():
                task.cancel()
        self.reconnect_tasks.clear()
        
        self.logger.info("All streams stopped")
    
    async def stop_stream(self, platform_name: str) -> bool:
        """Stop streaming to a specific platform.
        
        Args:
            platform_name: Name of the platform to stop streaming to
            
        Returns:
            True if stream stopped successfully
        """
        if platform_name not in self.streams:
            self.logger.error(f"Unknown platform: {platform_name}")
            return False
        
        stream_info = self.streams[platform_name]
        
        if stream_info.status == StreamStatus.STOPPED:
            self.logger.info(f"Stream to {platform_name} is already stopped")
            return True
        
        self.logger.info(f"Stopping stream to {platform_name}...")
        
        try:
            # Cancel monitoring task
            if platform_name in self.streaming_tasks:
                task = self.streaming_tasks[platform_name]
                if not task.done():
                    task.cancel()
                del self.streaming_tasks[platform_name]
            
            # Cancel reconnection task if exists
            if platform_name in self.reconnect_tasks:
                task = self.reconnect_tasks[platform_name]
                if not task.done():
                    task.cancel()
                del self.reconnect_tasks[platform_name]
            
            # In a real implementation, this would stop the actual stream
            await self._simulate_stream_stop(stream_info)
            
            stream_info.status = StreamStatus.STOPPED
            stream_info.last_error = None
            
            self.logger.info(f"Successfully stopped stream to {platform_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping stream to {platform_name}: {e}")
            return False
    
    async def _monitor_stream(self, platform_name: str):
        """Monitor a stream for health and handle disconnections.
        
        Args:
            platform_name: Name of the platform to monitor
        """
        stream_info = self.streams[platform_name]
        
        try:
            while stream_info.status == StreamStatus.STREAMING:
                # Check stream health
                if await self._check_stream_health(stream_info):
                    # Stream is healthy, wait before next check
                    await asyncio.sleep(30)  # Check every 30 seconds
                else:
                    # Stream is unhealthy, attempt reconnection
                    self.logger.warning(f"Stream to {platform_name} is unhealthy")
                    stream_info.status = StreamStatus.RECONNECTING
                    await self._schedule_reconnect(platform_name)
                    break
                    
        except asyncio.CancelledError:
            self.logger.info(f"Stream monitoring for {platform_name} cancelled")
        except Exception as e:
            self.logger.error(f"Error monitoring stream to {platform_name}: {e}")
            stream_info.status = StreamStatus.FAILED
            await self._schedule_reconnect(platform_name)
    
    async def _check_stream_health(self, stream_info: StreamInfo) -> bool:
        """Check if a stream is healthy.
        
        Args:
            stream_info: Stream information
            
        Returns:
            True if stream is healthy, False otherwise
        """
        # In a real implementation, this would:
        # 1. Check OBS streaming status
        # 2. Monitor network connectivity
        # 3. Check RTMP connection status
        # 4. Monitor bitrate and dropped frames
        
        # For simulation, randomly return health status
        import random
        return random.random() > 0.1  # 90% chance of being healthy
    
    async def _schedule_reconnect(self, platform_name: str):
        """Schedule a reconnection attempt for a platform.
        
        Args:
            platform_name: Name of the platform to reconnect
        """
        stream_info = self.streams[platform_name]
        
        if stream_info.retry_count >= self.max_retry_attempts:
            self.logger.error(f"Max retry attempts reached for {platform_name}")
            stream_info.status = StreamStatus.FAILED
            return
        
        stream_info.retry_count += 1
        delay = self.retry_delay * stream_info.retry_count  # Exponential backoff
        
        self.logger.info(f"Scheduling reconnect for {platform_name} in {delay} seconds (attempt {stream_info.retry_count})")
        
        # Cancel existing reconnect task if any
        if platform_name in self.reconnect_tasks:
            task = self.reconnect_tasks[platform_name]
            if not task.done():
                task.cancel()
        
        # Schedule new reconnect task
        task = asyncio.create_task(self._reconnect_after_delay(platform_name, delay))
        self.reconnect_tasks[platform_name] = task
    
    async def _reconnect_after_delay(self, platform_name: str, delay: int):
        """Reconnect to a platform after a delay.
        
        Args:
            platform_name: Name of the platform to reconnect
            delay: Delay in seconds before reconnecting
        """
        try:
            await asyncio.sleep(delay)
            self.logger.info(f"Attempting to reconnect to {platform_name}")
            
            # Stop current stream if still running
            await self.stop_stream(platform_name)
            
            # Attempt to restart
            if await self.start_stream(platform_name):
                self.logger.info(f"Successfully reconnected to {platform_name}")
            else:
                self.logger.error(f"Failed to reconnect to {platform_name}")
                
        except asyncio.CancelledError:
            self.logger.info(f"Reconnect task for {platform_name} cancelled")
        except Exception as e:
            self.logger.error(f"Error during reconnect to {platform_name}: {e}")
    
    async def _simulate_stream_start(self, stream_info: StreamInfo) -> bool:
        """Simulate starting a stream (placeholder for actual implementation).
        
        Args:
            stream_info: Stream information
            
        Returns:
            True if stream started successfully
        """
        # Simulate some delay and potential failure
        await asyncio.sleep(2)
        
        # In a real implementation, this would:
        # 1. Configure OBS with the platform's RTMP settings
        # 2. Start the actual stream
        # 3. Verify the connection
        
        # Simulate 95% success rate
        import random
        return random.random() > 0.05
    
    async def _simulate_stream_stop(self, stream_info: StreamInfo):
        """Simulate stopping a stream (placeholder for actual implementation).
        
        Args:
            stream_info: Stream information
        """
        # Simulate some delay
        await asyncio.sleep(1)
        
        # In a real implementation, this would stop the actual stream
    
    def get_stream_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all streams.
        
        Returns:
            Dictionary with stream status information
        """
        status = {}
        
        for platform_name, stream_info in self.streams.items():
            status[platform_name] = {
                'enabled': stream_info.enabled,
                'status': stream_info.status.value,
                'retry_count': stream_info.retry_count,
                'last_error': stream_info.last_error,
                'rtmp_url': stream_info.rtmp_url[:50] + '...' if len(stream_info.rtmp_url) > 50 else stream_info.rtmp_url
            }
        
        return status
    
    def get_active_streams(self) -> List[str]:
        """Get list of currently active streams.
        
        Returns:
            List of platform names that are currently streaming
        """
        return [
            platform_name for platform_name, stream_info in self.streams.items()
            if stream_info.status == StreamStatus.STREAMING
        ]