#!/usr/bin/env python3
"""
Live Stream Bot Setup Script

This script helps you set up the live streaming bot by creating
the necessary configuration files.
"""

import json
import os
import shutil
from pathlib import Path

def setup_config():
    """Set up configuration files."""
    print("Setting up Live Stream Bot configuration...")
    
    # Copy example config if config.json doesn't exist
    if not os.path.exists("config.json"):
        if os.path.exists("config.json.example"):
            shutil.copy("config.json.example", "config.json")
            print("✓ Created config.json from example")
        else:
            print("✗ config.json.example not found")
            return False
    else:
        print("✓ config.json already exists")
    
    # Copy example .env if .env doesn't exist
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            shutil.copy(".env.example", ".env")
            print("✓ Created .env from example")
        else:
            print("✗ .env.example not found")
    else:
        print("✓ .env already exists")
    
    return True

def validate_config():
    """Validate the configuration."""
    print("\nValidating configuration...")
    
    try:
        from src.config_manager import ConfigManager
        config = ConfigManager("config.json")
        
        is_valid, issues = config.validate_config()
        
        if is_valid:
            print("✓ Configuration is valid")
            
            # Show enabled platforms
            enabled_platforms = config.get_enabled_platforms()
            if enabled_platforms:
                print(f"✓ Enabled platforms: {', '.join(enabled_platforms.keys())}")
        else:
            print("✗ Configuration validation failed:")
            for issue in issues:
                print(f"  - {issue}")
        
        return is_valid
        
    except Exception as e:
        print(f"✗ Error validating config: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are available."""
    print("\nChecking dependencies...")
    
    required_packages = [
        "asyncio",
        "aiohttp", 
        "requests",
        "dotenv"  # python-dotenv imports as 'dotenv'
    ]
    
    optional_packages = [
        "obswebsocket"
    ]
    
    missing_required = []
    missing_optional = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} (required)")
            missing_required.append(package)
    
    for package in optional_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✓ {package}")
        except ImportError:
            print(f"⚠ {package} (optional - OBS control will be simulated)")
            missing_optional.append(package)
    
    if missing_required:
        print(f"\n⚠ Missing required packages: {', '.join(missing_required)}")
        print("Install them with: pip install -r requirements.txt")
        return False
    
    return True

def main():
    """Main setup function."""
    print("Live Stream Bot Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("main.py"):
        print("✗ Please run this script from the project root directory")
        return
    
    # Setup configuration
    if not setup_config():
        print("\n✗ Failed to setup configuration")
        return
    
    # Validate configuration
    if not validate_config():
        print("\n✗ Configuration validation failed")
        print("\nPlease edit config.json and .env with your actual settings:")
        print("1. Add your Odysee playlist URLs")
        print("2. Configure OBS WebSocket settings")
        print("3. Add your streaming platform keys in .env")
        return
    
    # Check dependencies
    if not check_dependencies():
        print("\n✗ Dependency check failed")
        return
    
    print("\n" + "=" * 50)
    print("✓ Setup completed successfully!")
    print("\nNext steps:")
    print("1. Edit config.json with your Odysee playlist URLs")
    print("2. Edit .env with your actual stream keys")
    print("3. Make sure OBS is running with WebSocket plugin enabled")
    print("4. Run the bot with: python main.py")

if __name__ == "__main__":
    main()