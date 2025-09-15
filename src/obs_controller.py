"""
OBS Controller for WebSocket API integration

Handles communication with OBS Studio via WebSocket API to control streaming.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
try:
    from obswebsocket import obsws, requests as obs_requests
    OBS_AVAILABLE = True
except ImportError:
    # Fallback for environments where obs-websocket-py is not available
    obsws = None
    obs_requests = None
    OBS_AVAILABLE = False

class OBSController:
    """Controller for OBS Studio WebSocket API."""
    
    def __init__(self, config_manager):
        """Initialize OBS controller.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        self.ws_client = None
        self.connected = False
        
        # OBS configuration
        obs_config = self.config.get('obs', {})
        self.host = obs_config.get('websocket_host', 'localhost')
        self.port = obs_config.get('websocket_port', 4455)
        self.password = obs_config.get('websocket_password', '')
        
    async def connect(self) -> bool:
        """Connect to OBS WebSocket.
        
        Returns:
            True if connection successful, False otherwise
        """
        if not OBS_AVAILABLE:
            self.logger.warning("obs-websocket-py not available. OBS control will be simulated.")
            self.connected = True
            return True
            
        try:
            self.logger.info(f"Connecting to OBS WebSocket at {self.host}:{self.port}")
            
            # Create WebSocket client
            self.ws_client = obsws(
                host=self.host,
                port=self.port,
                password=self.password
            )
            
            # Connect to OBS
            self.ws_client.connect()
            
            # Test connection by getting version
            version_response = self.ws_client.call(obs_requests.GetVersion())
            self.logger.info(f"Connected to OBS {version_response.getObsVersion()}")
            
            self.connected = True
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to OBS: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from OBS WebSocket."""
        if self.ws_client:
            try:
                self.ws_client.disconnect()
                self.logger.info("Disconnected from OBS WebSocket")
            except Exception as e:
                self.logger.error(f"Error disconnecting from OBS: {e}")
        
        self.connected = False
        self.ws_client = None
    
    async def start_streaming(self) -> bool:
        """Start streaming in OBS.
        
        Returns:
            True if streaming started successfully, False otherwise
        """
        if not self.connected:
            self.logger.error("Not connected to OBS")
            return False
            
        if not OBS_AVAILABLE:
            self.logger.info("Simulating OBS streaming start")
            return True
            
        try:
            # Check if already streaming
            status_response = self.ws_client.call(obs_requests.GetStreamStatus())
            if status_response.getOutputActive():
                self.logger.info("OBS is already streaming")
                return True
            
            # Start streaming
            self.ws_client.call(obs_requests.StartStream())
            self.logger.info("Started streaming in OBS")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start streaming: {e}")
            return False
    
    async def stop_streaming(self) -> bool:
        """Stop streaming in OBS.
        
        Returns:
            True if streaming stopped successfully, False otherwise
        """
        if not self.connected:
            self.logger.error("Not connected to OBS")
            return False
            
        if not OBS_AVAILABLE:
            self.logger.info("Simulating OBS streaming stop")
            return True
            
        try:
            # Check if streaming
            status_response = self.ws_client.call(obs_requests.GetStreamStatus())
            if not status_response.getOutputActive():
                self.logger.info("OBS is not streaming")
                return True
            
            # Stop streaming
            self.ws_client.call(obs_requests.StopStream())
            self.logger.info("Stopped streaming in OBS")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop streaming: {e}")
            return False
    
    async def set_video_source(self, video_url: str, source_name: str = "VideoSource") -> bool:
        """Set up a video source in OBS.
        
        Args:
            video_url: URL of the video to play
            source_name: Name of the source in OBS
            
        Returns:
            True if source set successfully, False otherwise
        """
        if not OBS_AVAILABLE:
            self.logger.info(f"Simulating setting video source: {video_url}")
            return True
            
        if not self.connected:
            self.logger.warning("Not connected to OBS - simulating video source setup")
            self.logger.info(f"Would set video source '{source_name}' to: {video_url}")
            return True
            
        try:
            # Create or update media source
            source_settings = {
                "local_file": False,
                "input": video_url,
                "input_format": "",
                "buffering_mb": 2,
                "speed_percent": 100,
                "is_local_file": False
            }
            
            # Check if source exists
            try:
                # Try to get existing input settings
                self.ws_client.call(obs_requests.GetInputSettings(source_name))
                # Source exists, update it
                self.ws_client.call(obs_requests.SetInputSettings(source_name, source_settings, True))
                self.logger.info(f"Updated video source '{source_name}' with URL: {video_url}")
                
            except:
                # Source doesn't exist, create it
                current_scene = self._get_current_scene()
                self.ws_client.call(obs_requests.CreateInput(
                    sceneName=current_scene,
                    inputName=source_name,
                    inputKind="ffmpeg_source",
                    inputSettings=source_settings
                ))
                self.logger.info(f"Created video source '{source_name}' with URL: {video_url}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set video source: {e}")
            return False
    
    async def set_stream_settings(self, platform_config: Dict[str, Any]) -> bool:
        """Configure OBS streaming settings for a platform.
        
        Args:
            platform_config: Platform configuration including RTMP URL and stream key
            
        Returns:
            True if settings applied successfully, False otherwise
        """
        if not self.connected:
            self.logger.error("Not connected to OBS")
            return False
            
        if not OBS_AVAILABLE:
            self.logger.info(f"Simulating stream settings for {platform_config}")
            return True
            
        try:
            rtmp_url = platform_config.get('rtmp_url', '')
            stream_key = platform_config.get('stream_key', '')
            
            if not rtmp_url or not stream_key:
                self.logger.error("Missing RTMP URL or stream key")
                return False
            
            # Configure stream settings
            stream_settings = {
                "server": rtmp_url,
                "key": stream_key
            }
            
            self.ws_client.call(obs_requests.SetStreamServiceSettings(
                streamServiceType="rtmp_common",
                streamServiceSettings=stream_settings
            ))
            
            self.logger.info(f"Set stream settings for {rtmp_url}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set stream settings: {e}")
            return False
    
    def _get_current_scene(self) -> str:
        """Get the current active scene name.
        
        Returns:
            Current scene name
        """
        if not OBS_AVAILABLE:
            return "Scene"
            
        try:
            scene_response = self.ws_client.call(obs_requests.GetCurrentProgramScene())
            return scene_response.getCurrentProgramSceneName()
        except:
            return "Scene"  # Default fallback
    
    async def create_scene(self, scene_name: str) -> bool:
        """Create a new scene in OBS.
        
        Args:
            scene_name: Name of the scene to create
            
        Returns:
            True if scene created successfully, False otherwise
        """
        if not self.connected:
            self.logger.error("Not connected to OBS")
            return False
            
        if not OBS_AVAILABLE:
            self.logger.info(f"Simulating scene creation: {scene_name}")
            return True
            
        try:
            self.ws_client.call(obs_requests.CreateScene(scene_name))
            self.logger.info(f"Created scene: {scene_name}")
            return True
            
        except Exception as e:
            if "already exists" in str(e).lower():
                self.logger.info(f"Scene '{scene_name}' already exists")
                return True
            else:
                self.logger.error(f"Failed to create scene: {e}")
                return False
    
    async def switch_scene(self, scene_name: str) -> bool:
        """Switch to a different scene.
        
        Args:
            scene_name: Name of the scene to switch to
            
        Returns:
            True if scene switched successfully, False otherwise
        """
        if not self.connected:
            self.logger.error("Not connected to OBS")
            return False
            
        if not OBS_AVAILABLE:
            self.logger.info(f"Simulating scene switch to: {scene_name}")
            return True
            
        try:
            self.ws_client.call(obs_requests.SetCurrentProgramScene(scene_name))
            self.logger.info(f"Switched to scene: {scene_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to switch scene: {e}")
            return False