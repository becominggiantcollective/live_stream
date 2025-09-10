# Live Stream Automation Bot

## Quick Test

To quickly test the system with example videos:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup configuration
python setup.py

# 3. Run example with sample videos
python example.py
```

## Features Demonstrated

The example shows:
- ✅ Configuration loading
- ✅ Video queue management with shuffle
- ✅ OBS WebSocket integration (simulated)
- ✅ Multi-platform stream management
- ✅ Video playback simulation
- ✅ Automatic cleanup and error handling

## Real Usage

For real streaming:
1. Configure actual Odysee playlist URLs in `config.json`
2. Add real stream keys in `.env` file
3. Ensure OBS is running with WebSocket enabled
4. Run `python main.py`

## Testing Notes

- The system works in simulation mode when OBS is not available
- Placeholder stream keys will show warnings but won't prevent testing
- Video playback duration is shortened in the example for quick demonstration