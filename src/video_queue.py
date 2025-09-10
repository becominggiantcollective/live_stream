"""
Video Queue Manager

Manages the queue of videos to be streamed, including shuffling and replay logic.
"""

import logging
import random
from typing import List, Dict, Any, Optional
from collections import deque

class VideoQueue:
    """Manages video queue for streaming."""
    
    def __init__(self, shuffle: bool = True):
        """Initialize video queue.
        
        Args:
            shuffle: Whether to shuffle videos when queue is refilled
        """
        self.queue = deque()
        self.played_videos = []
        self.shuffle = shuffle
        self.logger = logging.getLogger(__name__)
    
    def add_video(self, video: Dict[str, Any]):
        """Add a video to the queue.
        
        Args:
            video: Video information dictionary
        """
        self.queue.append(video)
        self.logger.debug(f"Added video to queue: {video.get('title', 'Unknown')}")
    
    def add_videos(self, videos: List[Dict[str, Any]]):
        """Add multiple videos to the queue.
        
        Args:
            videos: List of video information dictionaries
        """
        for video in videos:
            self.add_video(video)
        
        if self.shuffle:
            self.shuffle_queue()
        
        self.logger.info(f"Added {len(videos)} videos to queue")
    
    def get_next_video(self) -> Optional[Dict[str, Any]]:
        """Get the next video from the queue.
        
        Returns:
            Next video dictionary or None if queue is empty
        """
        if not self.queue:
            return None
        
        video = self.queue.popleft()
        self.played_videos.append(video)
        
        self.logger.debug(f"Got next video: {video.get('title', 'Unknown')}")
        return video
    
    def peek_next_video(self) -> Optional[Dict[str, Any]]:
        """Peek at the next video without removing it from queue.
        
        Returns:
            Next video dictionary or None if queue is empty
        """
        if not self.queue:
            return None
        return self.queue[0]
    
    def shuffle_queue(self):
        """Shuffle the current queue."""
        if len(self.queue) > 1:
            queue_list = list(self.queue)
            random.shuffle(queue_list)
            self.queue = deque(queue_list)
            self.logger.info("Shuffled video queue")
    
    def is_empty(self) -> bool:
        """Check if the queue is empty.
        
        Returns:
            True if queue is empty, False otherwise
        """
        return len(self.queue) == 0
    
    def size(self) -> int:
        """Get the current queue size.
        
        Returns:
            Number of videos in the queue
        """
        return len(self.queue)
    
    def clear(self):
        """Clear the queue and played videos."""
        self.queue.clear()
        self.played_videos.clear()
        self.logger.info("Cleared video queue")
    
    def reset_played(self):
        """Reset the played videos list and refill queue."""
        if self.played_videos:
            # Add played videos back to queue
            if self.shuffle:
                random.shuffle(self.played_videos)
            
            for video in self.played_videos:
                self.queue.append(video)
            
            self.played_videos.clear()
            self.logger.info(f"Reset played videos, queue size: {len(self.queue)}")
    
    def get_queue_info(self) -> Dict[str, Any]:
        """Get information about the current queue state.
        
        Returns:
            Dictionary with queue statistics
        """
        return {
            'queue_size': len(self.queue),
            'played_count': len(self.played_videos),
            'total_videos': len(self.queue) + len(self.played_videos),
            'shuffle_enabled': self.shuffle,
            'next_video': self.queue[0].get('title', 'Unknown') if self.queue else None
        }
    
    def remove_video(self, video_id: str) -> bool:
        """Remove a specific video from the queue.
        
        Args:
            video_id: ID of the video to remove
            
        Returns:
            True if video was removed, False if not found
        """
        # Remove from queue
        original_size = len(self.queue)
        self.queue = deque([v for v in self.queue if v.get('id') != video_id])
        
        # Remove from played videos
        self.played_videos = [v for v in self.played_videos if v.get('id') != video_id]
        
        removed = len(self.queue) < original_size
        if removed:
            self.logger.info(f"Removed video with ID: {video_id}")
        
        return removed
    
    def prioritize_video(self, video_id: str) -> bool:
        """Move a video to the front of the queue.
        
        Args:
            video_id: ID of the video to prioritize
            
        Returns:
            True if video was prioritized, False if not found
        """
        for i, video in enumerate(self.queue):
            if video.get('id') == video_id:
                # Remove from current position
                video = self.queue[i]
                del self.queue[i]
                
                # Add to front
                self.queue.appendleft(video)
                
                self.logger.info(f"Prioritized video: {video.get('title', 'Unknown')}")
                return True
        
        return False
    
    def get_videos_by_channel(self, channel_name: str) -> List[Dict[str, Any]]:
        """Get all videos from a specific channel.
        
        Args:
            channel_name: Name of the channel
            
        Returns:
            List of videos from the specified channel
        """
        channel_videos = []
        
        # Check queue
        for video in self.queue:
            if video.get('channel', '').lower() == channel_name.lower():
                channel_videos.append(video)
        
        # Check played videos
        for video in self.played_videos:
            if video.get('channel', '').lower() == channel_name.lower():
                channel_videos.append(video)
        
        return channel_videos
    
    def filter_videos_by_duration(self, min_duration: int = None, max_duration: int = None):
        """Filter videos in queue by duration.
        
        Args:
            min_duration: Minimum duration in seconds
            max_duration: Maximum duration in seconds
        """
        original_size = len(self.queue)
        
        filtered_queue = deque()
        for video in self.queue:
            duration = video.get('duration', 0)
            
            if min_duration is not None and duration < min_duration:
                continue
            if max_duration is not None and duration > max_duration:
                continue
                
            filtered_queue.append(video)
        
        self.queue = filtered_queue
        removed_count = original_size - len(self.queue)
        
        if removed_count > 0:
            self.logger.info(f"Filtered {removed_count} videos by duration")
    
    def get_total_duration(self) -> int:
        """Get total duration of all videos in queue.
        
        Returns:
            Total duration in seconds
        """
        total = 0
        for video in self.queue:
            total += video.get('duration', 0)
        return total