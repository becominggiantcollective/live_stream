#!/usr/bin/env python3
"""
Live Stream Monitor

A utility script to monitor the status of running streams.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config_manager import ConfigManager
from stream_manager import StreamManager

async def monitor_streams():
    """Monitor stream status."""
    try:
        config = ConfigManager()
        stream_manager = StreamManager(config)
        
        print("Live Stream Monitor")
        print("=" * 50)
        
        # Stream manager loads configs automatically on init
        # stream_manager.load_stream_configs()
        
        while True:
            # Get stream status
            status = stream_manager.get_stream_status()
            
            print(f"\nStream Status (Updated: {asyncio.get_event_loop().time():.0f})")
            print("-" * 50)
            
            for platform, info in status.items():
                status_symbol = {
                    'stopped': '⭕',
                    'starting': '🟡',
                    'streaming': '🟢',
                    'reconnecting': '🔄',
                    'failed': '🔴'
                }.get(info['status'], '❓')
                
                print(f"{status_symbol} {platform.upper():<10} | {info['status'].upper():<12} | Retries: {info['retry_count']}")
                
                if info['last_error']:
                    print(f"   └─ Error: {info['last_error']}")
            
            # Wait before next update
            await asyncio.sleep(10)
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(monitor_streams())