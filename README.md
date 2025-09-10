# Live Stream Automation Bot

An automated live streaming bot that fetches videos from Odysee playlists and streams them to multiple platforms (Rumble, YouTube, Twitch) using OBS Studio and RTMP.

## Features

- 🎬 **Odysee Integration**: Automatically fetch videos from Odysee playlists
- 🎮 **OBS WebSocket Control**: Full control over OBS Studio via WebSocket API
- 🌐 **Multi-Platform Streaming**: Stream to Rumble, YouTube, Twitch simultaneously
- 🔄 **Auto-Reconnection**: Intelligent reconnection handling with exponential backoff
- 📋 **Video Queue Management**: Smart queue with shuffle and replay functionality
- ⚙️ **Configurable**: Easy configuration via JSON files and environment variables
- 📊 **Monitoring**: Real-time stream status monitoring
- 🛡️ **Error Handling**: Comprehensive error handling and logging

## Quick Start

### Prerequisites

- Python 3.8+
- OBS Studio with WebSocket plugin enabled
- Stream keys for your target platforms

### Installation

1. Clone the repository:
```bash
git clone https://github.com/becominggiantcollective/live_stream.git
cd live_stream
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the setup script:
```bash
python setup.py
```

4. Configure your settings:
   - Edit `config.json` with your Odysee playlist URLs and OBS settings
   - Edit `.env` with your streaming platform keys

5. Start streaming:
```bash
python main.py
```

## Configuration

### config.json

The main configuration file contains:

- **Odysee settings**: Playlist URLs and API configuration
- **OBS settings**: WebSocket connection details
- **Streaming platforms**: RTMP URLs and platform-specific settings
- **Reconnection settings**: Retry attempts and delays

### .env

Environment file for sensitive data:

- `RUMBLE_STREAM_KEY`: Your Rumble stream key
- `YOUTUBE_STREAM_KEY`: Your YouTube stream key  
- `TWITCH_STREAM_KEY`: Your Twitch stream key
- `OBS_WEBSOCKET_PASSWORD`: OBS WebSocket password

## Usage

### Basic Streaming

```bash
# Start the streaming bot
python main.py
```

### Monitor Streams

```bash
# Monitor stream status in real-time
python monitor.py
```

### Setup and Validation

```bash
# Validate configuration and dependencies
python setup.py
```

## Architecture

The bot consists of several key components:

- **ConfigManager**: Handles configuration loading and environment variables
- **OdyseeClient**: Fetches videos from Odysee playlists
- **OBSController**: Controls OBS Studio via WebSocket API
- **StreamManager**: Manages multi-platform streaming with reconnection
- **VideoQueue**: Manages video queue with shuffle and replay logic

## Platform Support

### Rumble
- RTMP URL: `rtmp://ingest.rumble.com/live/`
- Requires stream key from Rumble Studio

### YouTube
- RTMP URL: `rtmp://a.rtmp.youtube.com/live2/`
- Requires stream key from YouTube Studio

### Twitch
- RTMP URL: `rtmp://live.twitch.tv/live/`
- Requires stream key from Twitch Dashboard

## OBS Setup

1. Install OBS Studio
2. Enable WebSocket plugin (usually enabled by default in newer versions)
3. Configure WebSocket settings:
   - Host: `localhost`
   - Port: `4455`
   - Password: (optional, set in config)
4. Create scenes and sources as needed

## Troubleshooting

### Common Issues

1. **OBS Connection Failed**
   - Ensure OBS is running
   - Check WebSocket plugin is enabled
   - Verify host/port/password in config

2. **Stream Connection Failed**
   - Verify stream keys are correct
   - Check network connectivity
   - Ensure RTMP URLs are correct for your region

3. **No Videos Found**
   - Verify Odysee playlist URLs are correct
   - Check playlist is public
   - Ensure internet connectivity

### Logs

Check `livestream.log` for detailed error messages and debugging information.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This software is for educational and personal use. Ensure you comply with the terms of service of all platforms you stream to. The authors are not responsible for any misuse of this software.
