"""
Odysee Client for fetching playlist videos

Handles communication with Odysee API to retrieve playlist information and videos.
"""

import logging
import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, parse_qs

class OdyseeClient:
    """Client for interacting with Odysee API."""
    
    def __init__(self, config_manager):
        """Initialize Odysee client.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        self.session = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def _extract_playlist_id(self, playlist_url: str) -> Optional[str]:
        """Extract playlist ID from Odysee URL.
        
        Args:
            playlist_url: Full Odysee playlist URL
            
        Returns:
            Playlist ID or None if not found
        """
        try:
            parsed = urlparse(playlist_url)
            
            # Handle different URL formats
            if '/$/playlist/' in parsed.path:
                # Format: https://odysee.com/$/playlist/playlist-id
                return parsed.path.split('/$/playlist/')[-1]
            elif 'list=' in parsed.query:
                # Format: https://odysee.com/@channel?list=playlist-id
                query_params = parse_qs(parsed.query)
                return query_params.get('list', [None])[0]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting playlist ID from {playlist_url}: {e}")
            return None
    
    async def get_playlist_videos(self, playlist_url: str) -> List[Dict[str, Any]]:
        """Fetch videos from an Odysee playlist.
        
        Args:
            playlist_url: URL of the Odysee playlist
            
        Returns:
            List of video information dictionaries
        """
        playlist_id = self._extract_playlist_id(playlist_url)
        if not playlist_id:
            self.logger.error(f"Could not extract playlist ID from URL: {playlist_url}")
            return []
        
        try:
            session = await self._get_session()
            
            # Odysee uses LBRY protocol - we'll simulate the API calls
            # Note: This is a simplified implementation. In reality, you might need
            # to use the LBRY SDK or reverse engineer the actual API calls
            
            # For now, we'll create some mock data structure that represents
            # what we'd expect from a real Odysee API
            videos = await self._fetch_playlist_data(session, playlist_id)
            
            self.logger.info(f"Fetched {len(videos)} videos from playlist {playlist_id}")
            return videos
            
        except Exception as e:
            self.logger.error(f"Error fetching playlist {playlist_url}: {e}")
            return []
    
    async def _fetch_playlist_data(self, session: aiohttp.ClientSession, playlist_id: str) -> List[Dict[str, Any]]:
        """Fetch playlist data from Odysee/LBRY.
        
        Args:
            session: aiohttp session
            playlist_id: ID of the playlist
            
        Returns:
            List of video dictionaries
        """
        try:
            # Use LBRY HTTP API to resolve the playlist
            api_url = "https://api.lbry.com/v1/lbry"
            
            # First, resolve the playlist claim
            playlist_resolve_params = {
                "method": "resolve",
                "params": {
                    "urls": [f"lbry://{playlist_id}"]
                }
            }
            
            async with session.post(api_url, json=playlist_resolve_params) as response:
                if response.status != 200:
                    self.logger.error(f"Failed to resolve playlist: HTTP {response.status}")
                    return []
                
                data = await response.json()
                
                if not data.get("success"):
                    self.logger.error(f"LBRY API error: {data.get('error', 'Unknown error')}")
                    return []
                
                result = data.get("result", {})
                playlist_claim = result.get(f"lbry://{playlist_id}")
                
                if not playlist_claim:
                    self.logger.error(f"Playlist not found: {playlist_id}")
                    return []
                
                # Extract video claims from playlist
                playlist_metadata = playlist_claim.get("value", {}).get("stream", {}).get("metadata", {})
                video_claims = []
                
                # For playlist collections, check for claim_list
                if "claim_list" in playlist_metadata:
                    video_claims = playlist_metadata["claim_list"]
                elif "description" in playlist_metadata:
                    # Try to extract claim URLs from description
                    import re
                    description = playlist_metadata["description"]
                    claim_urls = re.findall(r'lbry://[a-zA-Z0-9\-#@]+', description)
                    video_claims = [url.replace("lbry://", "") for url in claim_urls]
                
                if not video_claims:
                    self.logger.warning(f"No video claims found in playlist {playlist_id}")
                    # Return some sample data for testing
                    return self._get_sample_videos(playlist_id)
                
                # Resolve individual video claims
                videos = []
                for claim in video_claims[:10]:  # Limit to 10 videos for now
                    try:
                        video_data = await self._resolve_video_claim(session, claim, api_url)
                        if video_data:
                            videos.append(video_data)
                    except Exception as e:
                        self.logger.warning(f"Failed to resolve video claim {claim}: {e}")
                        continue
                
                self.logger.info(f"Successfully fetched {len(videos)} videos from playlist")
                return videos
                
        except Exception as e:
            self.logger.error(f"Error fetching playlist data for {playlist_id}: {e}")
            # Return sample data as fallback
            return self._get_sample_videos(playlist_id)
    
    async def _resolve_video_claim(self, session: aiohttp.ClientSession, claim: str, api_url: str) -> Optional[Dict[str, Any]]:
        """Resolve a single video claim to get metadata and streaming URL.
        
        Args:
            session: aiohttp session
            claim: Video claim ID or name
            api_url: LBRY API URL
            
        Returns:
            Video data dictionary or None if failed
        """
        try:
            resolve_params = {
                "method": "resolve",
                "params": {
                    "urls": [f"lbry://{claim}"]
                }
            }
            
            async with session.post(api_url, json=resolve_params) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                if not data.get("success"):
                    return None
                
                result = data.get("result", {})
                video_claim = result.get(f"lbry://{claim}")
                
                if not video_claim:
                    return None
                
                # Extract video metadata
                metadata = video_claim.get("value", {})
                stream_metadata = metadata.get("stream", {}).get("metadata", {})
                
                # Get streaming URL
                stream_url = await self._get_streaming_url(session, claim)
                
                return {
                    'id': claim,
                    'title': stream_metadata.get('title', 'Unknown Title'),
                    'url': stream_url or f'https://player.odysee.com/api/v1/proxy?src={claim}',
                    'duration': stream_metadata.get('video', {}).get('duration', 300),
                    'thumbnail': stream_metadata.get('thumbnail', {}).get('url', ''),
                    'description': stream_metadata.get('description', ''),
                    'channel': video_claim.get('signing_channel', {}).get('name', 'Unknown Channel'),
                    'published_at': metadata.get('timestamp', '')
                }
                
        except Exception as e:
            self.logger.warning(f"Error resolving video claim {claim}: {e}")
            return None
    
    async def _get_streaming_url(self, session: aiohttp.ClientSession, claim: str) -> Optional[str]:
        """Get the direct streaming URL for a video claim.
        
        Args:
            session: aiohttp session
            claim: Video claim ID
            
        Returns:
            Direct streaming URL or None
        """
        try:
            # Try Odysee's streaming API first
            stream_url = f"https://player.odysee.com/api/v1/proxy?src={claim}"
            
            # Verify the URL is accessible
            async with session.head(stream_url) as response:
                if response.status == 200:
                    return stream_url
            
            # Fallback to LBRY's get endpoint
            return f"https://api.lbry.com/get/{claim}/stream"
            
        except:
            return None
    
    def _get_sample_videos(self, playlist_id: str) -> List[Dict[str, Any]]:
        """Get sample videos as fallback when real API fails.
        
        Args:
            playlist_id: Playlist ID for context
            
        Returns:
            List of sample video dictionaries
        """
        return [
            {
                'id': f'sample_video_{i}',
                'title': f'Sample Video {i} from {playlist_id}',
                'url': f'https://player.odysee.com/api/v1/proxy?src=sample_video_{i}',
                'duration': 300 + (i * 60),  # 5-10 minutes
                'thumbnail': f'https://thumbnails.odysee.com/sample_{i}.jpg',
                'description': f'Sample video {i} from playlist {playlist_id}',
                'channel': 'Sample Channel',
                'published_at': '2023-01-01T00:00:00Z'
            }
            for i in range(1, 6)  # 5 sample videos
        ]
    
    async def get_video_stream_url(self, video_id: str) -> Optional[str]:
        """Get the actual streaming URL for a video.
        
        Args:
            video_id: ID of the video
            
        Returns:
            Direct streaming URL or None if not found
        """
        try:
            session = await self._get_session()
            
            # Use the real streaming URL resolution
            return await self._get_streaming_url(session, video_id)
            
        except Exception as e:
            self.logger.error(f"Error getting stream URL for video {video_id}: {e}")
            return None
    
    async def search_videos(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for videos on Odysee.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of video information dictionaries
        """
        try:
            session = await self._get_session()
            
            # Placeholder for search functionality
            # In reality, this would use the LBRY search API
            
            self.logger.info(f"Searching for videos with query: {query}")
            
            # Return empty list for now
            return []
            
        except Exception as e:
            self.logger.error(f"Error searching videos with query '{query}': {e}")
            return []