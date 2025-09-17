#!/usr/bin/env python3
"""
Cloud Drive File Validator

Test script to validate that cloud drive files are accessible.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from cloud_drive_client import CloudDriveClient
from config_manager import ConfigManager

async def validate_cloud_files():
    """Validate cloud drive files in configuration."""
    
    try:
        config = ConfigManager("config.json")
        client = CloudDriveClient(config)
        
        # Get cloud drive configuration
        video_sources = config.get('video_sources', {})
        cloud_config = video_sources.get('cloud_drive', {})
        
        if not cloud_config.get('enabled', False):
            print("❌ Cloud drive is not enabled in configuration")
            return False
        
        files = cloud_config.get('files', [])
        if not files:
            print("❌ No cloud drive files configured")
            return False
        
        print(f"🔍 Validating {len(files)} cloud drive files...")
        print()
        
        valid_files = 0
        
        for i, file_info in enumerate(files, 1):
            if isinstance(file_info, str):
                url = file_info
                title = f"File {i}"
            elif isinstance(file_info, dict):
                url = file_info.get('url', '')
                title = file_info.get('title', f"File {i}")
            else:
                print(f"❌ {i}. Invalid file format: {file_info}")
                continue
            
            if not url:
                print(f"❌ {i}. No URL provided for {title}")
                continue
            
            print(f"🔄 {i}. Testing: {title}")
            print(f"   URL: {url}")
            
            # Detect provider
            provider = client._detect_provider(url)
            print(f"   Provider: {provider.__class__.__name__}")
            
            # Test access
            try:
                accessible = await client.validate_file_access(url)
                if accessible:
                    print(f"   ✅ Accessible")
                    valid_files += 1
                else:
                    print(f"   ❌ Not accessible")
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            print()
        
        print(f"📊 Results: {valid_files}/{len(files)} files are accessible")
        
        await client.close()
        return valid_files > 0
        
    except FileNotFoundError:
        print("❌ config.json not found. Run 'python setup.py' first.")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main function."""
    print("Cloud Drive File Validator")
    print("=" * 50)
    print()
    
    result = asyncio.run(validate_cloud_files())
    
    if result:
        print("🎉 Validation completed - some files are accessible")
        sys.exit(0)
    else:
        print("💥 Validation failed - no accessible files found")
        sys.exit(1)

if __name__ == "__main__":
    main()