"""
Configuration Manager for Live Stream Bot

Handles loading and managing configuration from JSON files and environment variables.
"""

import json
import os
from typing import Dict, Any, Optional, List, Tuple
from dotenv import load_dotenv

class ConfigManager:
    """Manages configuration loading and access."""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize configuration manager.
        
        Args:
            config_path: Path to the JSON configuration file
        """
        self.config_path = config_path
        self.config_data = {}
        self.load_config()
        self.load_env_overrides()
    
    def load_config(self):
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                self.config_data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file {self.config_path} not found. "
                                  f"Please copy config.json.example to {self.config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
    
    def load_env_overrides(self):
        """Override configuration with environment variables."""
        load_dotenv()
        
        # Override stream keys from environment
        platforms = self.config_data.get('streaming', {}).get('platforms', {})
        
        if 'rumble' in platforms:
            rumble_key = os.getenv('RUMBLE_STREAM_KEY')
            if rumble_key:
                platforms['rumble']['stream_key'] = rumble_key
                
        if 'youtube' in platforms:
            youtube_key = os.getenv('YOUTUBE_STREAM_KEY')
            if youtube_key:
                platforms['youtube']['stream_key'] = youtube_key
                
        if 'twitch' in platforms:
            twitch_key = os.getenv('TWITCH_STREAM_KEY')
            if twitch_key:
                platforms['twitch']['stream_key'] = twitch_key
        
        # Override OBS WebSocket password
        obs_password = os.getenv('OBS_WEBSOCKET_PASSWORD')
        if obs_password:
            if 'obs' not in self.config_data:
                self.config_data['obs'] = {}
            self.config_data['obs']['websocket_password'] = obs_password
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation for nested keys)
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config_data
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """Set configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation for nested keys)
            value: Value to set
        """
        keys = key.split('.')
        config = self.config_data
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the final key
        config[keys[-1]] = value
    
    def get_enabled_platforms(self) -> Dict[str, Dict[str, Any]]:
        """Get all enabled streaming platforms.
        
        Returns:
            Dictionary of enabled platform configurations
        """
        platforms = self.get('streaming.platforms', {})
        return {name: config for name, config in platforms.items() 
                if config.get('enabled', False)}
    
    def validate_config(self) -> Tuple[bool, List[str]]:
        """Validate configuration completeness.
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check required sections
        required_sections = ['obs', 'streaming']
        for section in required_sections:
            if section not in self.config_data:
                issues.append(f"Missing required configuration section: {section}")
        
        # Check if we have either video_sources or the legacy odysee section
        has_video_sources = 'video_sources' in self.config_data
        has_legacy_odysee = 'odysee' in self.config_data
        
        if not has_video_sources and not has_legacy_odysee:
            issues.append("Missing video source configuration - need either 'video_sources' or 'odysee' section")
        
        # Check video source configuration
        video_sources = self.get('video_sources', {})
        odysee_config = video_sources.get('odysee', {}) if video_sources else self.get('odysee', {})
        cloud_drive_config = video_sources.get('cloud_drive', {}) if video_sources else {}
        
        # Check if at least one video source is enabled
        odysee_enabled = odysee_config.get('enabled', True)  # Default true for backwards compatibility
        cloud_drive_enabled = cloud_drive_config.get('enabled', False)
        
        if not odysee_enabled and not cloud_drive_enabled:
            issues.append("No video sources enabled - enable either Odysee or Cloud Drive")
        
        # Check Odysee configuration
        if odysee_enabled:
            playlist_urls = odysee_config.get('playlist_urls', [])
            if not playlist_urls:
                issues.append("No Odysee playlist URLs configured")
            else:
                for url in playlist_urls:
                    if url == "https://odysee.com/$/playlist/your-playlist-id":
                        issues.append("Please replace placeholder Odysee playlist URL with real URL")
        
        # Check Cloud Drive configuration
        if cloud_drive_enabled:
            files = cloud_drive_config.get('files', [])
            if not files:
                issues.append("No cloud drive files configured")
            else:
                for file_info in files:
                    if isinstance(file_info, str):
                        if 'YOUR_FILE_ID' in file_info or 'YOUR_CID' in file_info:
                            issues.append("Please replace placeholder cloud drive URLs with real URLs")
                    elif isinstance(file_info, dict):
                        url = file_info.get('url', '')
                        if 'YOUR_FILE_ID' in url or 'YOUR_CID' in url:
                            issues.append("Please replace placeholder cloud drive URLs with real URLs")
        
        # Check OBS configuration
        obs_config = self.get('obs', {})
        if not obs_config.get('websocket_host'):
            issues.append("OBS WebSocket host not configured")
        if not obs_config.get('websocket_port'):
            issues.append("OBS WebSocket port not configured")
        
        # Check streaming platforms
        enabled_platforms = self.get_enabled_platforms()
        if not enabled_platforms:
            issues.append("No streaming platforms enabled")
        else:
            for platform_name, platform_config in enabled_platforms.items():
                stream_key = platform_config.get('stream_key', '')
                if not stream_key:
                    issues.append(f"No stream key configured for {platform_name}")
                elif stream_key.startswith('YOUR_') or stream_key.endswith('_here') or stream_key == 'your_rumble_stream_key_here':
                    issues.append(f"Placeholder stream key found for {platform_name} - please set real stream key")
                
                rtmp_url = platform_config.get('rtmp_url', '')
                if not rtmp_url:
                    issues.append(f"No RTMP URL configured for {platform_name}")
        
        return len(issues) == 0, issues
    
    def validate_config_legacy(self) -> bool:
        """Legacy validation method for backward compatibility.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        is_valid, _ = self.validate_config()
        return is_valid