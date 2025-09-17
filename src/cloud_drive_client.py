"""
Cloud Drive Client for fetching video files from cloud storage

Supports multiple cloud storage providers like Google Drive, Dropbox, OneDrive, etc.
"""

import logging
import aiohttp
import asyncio
import re
from typing import List, Dict, Any, Optional, Union
from urllib.parse import urlparse, parse_qs
from abc import ABC, abstractmethod


class CloudProvider(ABC):
    """Abstract base class for cloud storage providers."""
    
    @abstractmethod
    async def get_direct_download_url(self, session: aiohttp.ClientSession, share_url: str) -> Optional[str]:
        """Convert a share URL to a direct download URL."""
        pass
    
    @abstractmethod
    def extract_file_id(self, share_url: str) -> Optional[str]:
        """Extract file ID from a share URL."""
        pass


class GoogleDriveProvider(CloudProvider):
    """Google Drive provider for handling Google Drive share links."""
    
    def extract_file_id(self, share_url: str) -> Optional[str]:
        """Extract file ID from Google Drive share URL.
        
        Supports formats:
        - https://drive.google.com/file/d/FILE_ID/view
        - https://drive.google.com/open?id=FILE_ID
        """
        try:
            if '/file/d/' in share_url:
                # Format: https://drive.google.com/file/d/FILE_ID/view
                return share_url.split('/file/d/')[1].split('/')[0]
            elif 'id=' in share_url:
                # Format: https://drive.google.com/open?id=FILE_ID
                parsed = urlparse(share_url)
                query_params = parse_qs(parsed.query)
                return query_params.get('id', [None])[0]
            return None
        except Exception:
            return None
    
    async def get_direct_download_url(self, session: aiohttp.ClientSession, share_url: str) -> Optional[str]:
        """Convert Google Drive share URL to direct download URL."""
        file_id = self.extract_file_id(share_url)
        if not file_id:
            return None
        
        # Google Drive direct download URL format
        return f"https://drive.google.com/uc?export=download&id={file_id}"


class DropboxProvider(CloudProvider):
    """Dropbox provider for handling Dropbox share links."""
    
    def extract_file_id(self, share_url: str) -> Optional[str]:
        """Extract file info from Dropbox share URL."""
        # For Dropbox, we can modify the URL directly
        return share_url if 'dropbox.com' in share_url else None
    
    async def get_direct_download_url(self, session: aiohttp.ClientSession, share_url: str) -> Optional[str]:
        """Convert Dropbox share URL to direct download URL."""
        if 'dropbox.com' in share_url:
            # Replace ?dl=0 with ?dl=1 for direct download
            if '?dl=0' in share_url:
                return share_url.replace('?dl=0', '?dl=1')
            elif '?dl=' not in share_url:
                return share_url + ('&' if '?' in share_url else '?') + 'dl=1'
        return share_url


class OneDriveProvider(CloudProvider):
    """OneDrive provider for handling OneDrive share links."""
    
    def extract_file_id(self, share_url: str) -> Optional[str]:
        """Extract file info from OneDrive share URL."""
        return share_url if '1drv.ms' in share_url or 'sharepoint.com' in share_url else None
    
    async def get_direct_download_url(self, session: aiohttp.ClientSession, share_url: str) -> Optional[str]:
        """Convert OneDrive share URL to direct download URL."""
        if '1drv.ms' in share_url or 'sharepoint.com' in share_url:
            # OneDrive direct download can be achieved by appending download=1
            if '?' in share_url:
                return share_url + '&download=1'
            else:
                return share_url + '?download=1'
        return share_url


class DirectUrlProvider(CloudProvider):
    """Provider for direct download URLs."""
    
    def extract_file_id(self, share_url: str) -> Optional[str]:
        """For direct URLs, return the URL itself."""
        return share_url
    
    async def get_direct_download_url(self, session: aiohttp.ClientSession, share_url: str) -> Optional[str]:
        """Return the URL as-is for direct downloads."""
        return share_url


class CloudDriveClient:
    """Client for fetching videos from cloud storage services."""
    
    def __init__(self, config_manager):
        """Initialize cloud drive client.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        self.session = None
        
        # Initialize providers
        self.providers = {
            'google_drive': GoogleDriveProvider(),
            'dropbox': DropboxProvider(),
            'onedrive': OneDriveProvider(),
            'direct': DirectUrlProvider()
        }
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def _detect_provider(self, url: str) -> CloudProvider:
        """Detect which cloud provider based on URL.
        
        Args:
            url: The share or download URL
            
        Returns:
            Appropriate cloud provider instance
        """
        url_lower = url.lower()
        
        if 'drive.google.com' in url_lower:
            return self.providers['google_drive']
        elif 'dropbox.com' in url_lower:
            return self.providers['dropbox']
        elif '1drv.ms' in url_lower or 'sharepoint.com' in url_lower:
            return self.providers['onedrive']
        else:
            # Assume direct URL
            return self.providers['direct']
    
    async def get_video_files(self, file_list: List[Union[str, Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Fetch video files from cloud storage.
        
        Args:
            file_list: List of file URLs or file configuration dictionaries
            
        Returns:
            List of video information dictionaries
        """
        videos = []
        session = await self._get_session()
        
        for i, file_info in enumerate(file_list):
            try:
                if isinstance(file_info, str):
                    # Simple URL string
                    video_data = await self._process_file_url(session, file_info, i + 1)
                elif isinstance(file_info, dict):
                    # Detailed file configuration
                    video_data = await self._process_file_config(session, file_info, i + 1)
                else:
                    self.logger.warning(f"Invalid file info format: {file_info}")
                    continue
                
                if video_data:
                    videos.append(video_data)
                    
            except Exception as e:
                self.logger.error(f"Error processing file {file_info}: {e}")
                continue
        
        self.logger.info(f"Successfully processed {len(videos)} video files from cloud storage")
        return videos
    
    async def _process_file_url(self, session: aiohttp.ClientSession, url: str, index: int) -> Optional[Dict[str, Any]]:
        """Process a simple file URL.
        
        Args:
            session: aiohttp session
            url: File URL
            index: Index for generating default metadata
            
        Returns:
            Video data dictionary or None
        """
        provider = self._detect_provider(url)
        direct_url = await provider.get_direct_download_url(session, url)
        
        if not direct_url:
            self.logger.error(f"Could not get direct download URL for: {url}")
            return None
        
        # Generate default metadata
        filename = self._extract_filename_from_url(url)
        
        return {
            'id': f'cloud_video_{index}',
            'title': filename or f'Cloud Video {index}',
            'url': direct_url,
            'duration': 300,  # Default 5 minutes
            'thumbnail': '',
            'description': f'Video file from cloud storage: {filename}',
            'channel': 'Cloud Storage',
            'published_at': '',
            'original_url': url,
            'provider': provider.__class__.__name__
        }
    
    async def _process_file_config(self, session: aiohttp.ClientSession, file_config: Dict[str, Any], index: int) -> Optional[Dict[str, Any]]:
        """Process a detailed file configuration.
        
        Args:
            session: aiohttp session
            file_config: File configuration dictionary
            index: Index for generating default metadata
            
        Returns:
            Video data dictionary or None
        """
        url = file_config.get('url')
        if not url:
            self.logger.error(f"No URL found in file config: {file_config}")
            return None
        
        provider = self._detect_provider(url)
        direct_url = await provider.get_direct_download_url(session, url)
        
        if not direct_url:
            self.logger.error(f"Could not get direct download URL for: {url}")
            return None
        
        # Use provided metadata or generate defaults
        filename = self._extract_filename_from_url(url)
        
        return {
            'id': file_config.get('id', f'cloud_video_{index}'),
            'title': file_config.get('title', filename or f'Cloud Video {index}'),
            'url': direct_url,
            'duration': file_config.get('duration', 300),
            'thumbnail': file_config.get('thumbnail', ''),
            'description': file_config.get('description', f'Video file from cloud storage: {filename}'),
            'channel': file_config.get('channel', 'Cloud Storage'),
            'published_at': file_config.get('published_at', ''),
            'original_url': url,
            'provider': provider.__class__.__name__
        }
    
    def _extract_filename_from_url(self, url: str) -> Optional[str]:
        """Extract filename from URL.
        
        Args:
            url: File URL
            
        Returns:
            Filename or None
        """
        try:
            # Try to extract filename from URL path
            path = urlparse(url).path
            if path:
                filename = path.split('/')[-1]
                if filename and '.' in filename:
                    return filename
            
            # For cloud storage URLs, try to extract from query parameters
            if 'drive.google.com' in url:
                # Google Drive doesn't expose filename in URL
                return None
            elif 'dropbox.com' in url:
                # Extract from Dropbox URL path
                if '/s/' in url:
                    return url.split('/s/')[-1].split('?')[0]
            
            return None
        except Exception:
            return None
    
    async def validate_file_access(self, url: str) -> bool:
        """Validate that a file URL is accessible.
        
        Args:
            url: File URL to validate
            
        Returns:
            True if accessible, False otherwise
        """
        try:
            provider = self._detect_provider(url)
            session = await self._get_session()
            direct_url = await provider.get_direct_download_url(session, url)
            
            if not direct_url:
                return False
            
            # Test access with HEAD request
            async with session.head(direct_url, allow_redirects=True) as response:
                return response.status == 200
                
        except Exception as e:
            self.logger.error(f"Error validating file access for {url}: {e}")
            return False
    
    def get_sample_files(self) -> List[Dict[str, Any]]:
        """Get sample cloud files for testing.
        
        Returns:
            List of sample file dictionaries
        """
        return [
            {
                'id': 'sample_cloud_video_1',
                'title': 'Sample Cloud Video 1',
                'url': 'https://example.com/sample1.mp4',
                'duration': 300,
                'thumbnail': 'https://example.com/thumb1.jpg',
                'description': 'Sample video 1 from cloud storage',
                'channel': 'Cloud Storage',
                'published_at': '2023-01-01T00:00:00Z',
                'original_url': 'https://drive.google.com/file/d/sample_file_id_1/view',
                'provider': 'GoogleDriveProvider'
            },
            {
                'id': 'sample_cloud_video_2',
                'title': 'Sample Cloud Video 2',
                'url': 'https://example.com/sample2.mp4',
                'duration': 420,
                'thumbnail': 'https://example.com/thumb2.jpg',
                'description': 'Sample video 2 from cloud storage',
                'channel': 'Cloud Storage',
                'published_at': '2023-01-01T00:00:00Z',
                'original_url': 'https://www.dropbox.com/s/sample_file_id_2/video.mp4?dl=0',
                'provider': 'DropboxProvider'
            }
        ]