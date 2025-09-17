# Cloud Drive Integration Guide

This guide explains how to set up and use cloud drive integration in the Live Stream Bot, allowing you to stream videos directly from cloud storage services instead of or in addition to Odysee playlists.

## Supported Cloud Providers

The Live Stream Bot supports the following cloud storage providers:

### Google Drive
- **Share URL Format**: `https://drive.google.com/file/d/FILE_ID/view`
- **Alternative Format**: `https://drive.google.com/open?id=FILE_ID`
- **How to get shareable link**: 
  1. Right-click your video file in Google Drive
  2. Select "Get link"
  3. Set permissions to "Anyone with the link"
  4. Copy the provided URL

### Dropbox
- **Share URL Format**: `https://www.dropbox.com/s/FILE_ID/filename.mp4?dl=0`
- **How to get shareable link**:
  1. Right-click your video file in Dropbox
  2. Select "Copy link"
  3. The URL will be automatically converted for direct download

### OneDrive
- **Share URL Format**: `https://1drv.ms/v/s!SHORT_URL` or SharePoint URLs
- **How to get shareable link**:
  1. Right-click your video file in OneDrive
  2. Select "Share" → "Copy link"
  3. Set permissions to "Anyone with the link can view"

### Direct URLs
- Any direct video file URL (e.g., `https://example.com/video.mp4`)
- Self-hosted video files
- CDN-hosted content

## Configuration

### Basic Configuration

Add cloud drive configuration to your `config.json`:

```json
{
  "video_sources": {
    "odysee": {
      "enabled": true,
      "playlist_urls": [
        "https://odysee.com/$/playlist/your-playlist-id"
      ]
    },
    "cloud_drive": {
      "enabled": true,
      "files": [
        "https://drive.google.com/file/d/YOUR_FILE_ID/view",
        "https://www.dropbox.com/s/YOUR_FILE_ID/video.mp4?dl=0",
        "https://example.com/direct-video.mp4"
      ]
    }
  }
}
```

### Advanced Configuration

You can provide detailed metadata for each video file:

```json
{
  "video_sources": {
    "cloud_drive": {
      "enabled": true,
      "files": [
        {
          "url": "https://drive.google.com/file/d/YOUR_FILE_ID/view",
          "title": "My Awesome Video",
          "duration": 600,
          "description": "A description of my video",
          "channel": "My Channel",
          "thumbnail": "https://example.com/thumbnail.jpg"
        },
        {
          "url": "https://www.dropbox.com/s/FILE_ID/presentation.mp4?dl=0",
          "title": "Educational Content",
          "duration": 1800,
          "description": "Educational video content"
        }
      ]
    }
  }
}
```

### Configuration Options

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `enabled` | boolean | Yes | Enable/disable cloud drive integration |
| `files` | array | Yes | List of video files (URLs or objects) |
| `url` | string | Yes | Cloud storage share URL or direct URL |
| `title` | string | No | Custom video title (defaults to filename) |
| `duration` | number | No | Video duration in seconds (default: 300) |
| `description` | string | No | Video description |
| `channel` | string | No | Channel/creator name (default: "Cloud Storage") |
| `thumbnail` | string | No | Thumbnail image URL |

## Usage Examples

### Cloud Drive Only

Disable Odysee and use only cloud drive files:

```json
{
  "video_sources": {
    "odysee": {
      "enabled": false
    },
    "cloud_drive": {
      "enabled": true,
      "files": [
        "https://drive.google.com/file/d/FILE_ID_1/view",
        "https://drive.google.com/file/d/FILE_ID_2/view"
      ]
    }
  }
}
```

### Mixed Sources

Use both Odysee playlists and cloud drive files:

```json
{
  "video_sources": {
    "odysee": {
      "enabled": true,
      "playlist_urls": [
        "https://odysee.com/$/playlist/playlist-1",
        "https://odysee.com/$/playlist/playlist-2"
      ]
    },
    "cloud_drive": {
      "enabled": true,
      "files": [
        "https://drive.google.com/file/d/FILE_ID/view",
        "https://www.dropbox.com/s/FILE_ID/video.mp4?dl=0"
      ]
    }
  }
}
```

### Running the Example

Use the cloud drive example to test your setup:

```bash
# Run the cloud drive example
python cloud_drive_example.py
```

This will create a sample configuration and demonstrate how cloud drive integration works.

## File Format Support

The bot supports any video format that:
- Can be streamed via HTTP/HTTPS
- Is compatible with OBS's media source
- Common formats: MP4, AVI, MOV, MKV, WebM

## Troubleshooting

### Common Issues

1. **"Could not get direct download URL"**
   - Ensure the share URL is public (anyone with link can view)
   - Check that the file hasn't been moved or deleted
   - Verify the URL format is correct for your cloud provider

2. **"File not accessible"**
   - The file may require authentication
   - Check sharing permissions in your cloud storage
   - Try opening the URL in a browser to verify access

3. **Video won't play in OBS**
   - Ensure the video format is supported by OBS
   - Check that the direct download URL is working
   - Verify network connectivity

### Testing File Access

You can test if your cloud files are accessible:

```python
import asyncio
from src.cloud_drive_client import CloudDriveClient
from src.config_manager import ConfigManager

async def test_file():
    config = ConfigManager("config.json")
    client = CloudDriveClient(config)
    
    url = "https://drive.google.com/file/d/YOUR_FILE_ID/view"
    accessible = await client.validate_file_access(url)
    print(f"File accessible: {accessible}")
    
    await client.close()

asyncio.run(test_file())
```

## Best Practices

1. **File Organization**: Organize your cloud files in folders for easy management
2. **Naming Convention**: Use descriptive filenames that will make good default titles
3. **File Size**: Consider file sizes for streaming - very large files may cause buffering
4. **Backup**: Keep backups of your video files in case of cloud storage issues
5. **Permissions**: Regularly check that your share links haven't expired or changed permissions

## Security Considerations

- Share URLs are included in configuration files - don't commit sensitive URLs to public repositories
- Consider using environment variables for sensitive share URLs
- Regularly audit shared file permissions
- Be aware that anyone with share URLs can access your files

## Migration from Odysee

To migrate from Odysee-only to cloud drive:

1. Upload your videos to your preferred cloud storage
2. Get share URLs for each video
3. Update your configuration to use cloud drive
4. Test with the cloud drive example
5. Gradually transition by enabling both sources initially

This allows for a smooth transition while maintaining your existing setup.