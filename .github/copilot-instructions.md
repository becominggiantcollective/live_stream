# GitHub Copilot Instructions for Live Stream Automation Bot

## Project Overview

This is a **Live Stream Automation Bot** that fetches videos from Odysee playlists and streams them to multiple platforms (Rumble, YouTube, Twitch) using OBS Studio and RTMP. The project includes an AI agent system for intelligent content curation and stream quality monitoring.

### Key Technologies
- **Python 3.8+** with async/await patterns
- **OBS WebSocket API** for stream control
- **RTMP** for multi-platform streaming
- **Odysee/LBRY API** for content fetching
- **AI Agents** for autonomous decision-making

## Architecture Patterns

### 1. Configuration Management
- Use `ConfigManager` for all configuration access
- Store sensitive data (stream keys, passwords) in `.env` file
- Use `config.json` for application settings
- Always validate configuration before use

### 2. Async/Await Patterns
- All I/O operations must be async (OBS WebSocket, HTTP requests, streaming)
- Use `asyncio.create_task()` for concurrent operations
- Use `asyncio.Queue` for message passing between components
- Always handle exceptions in async functions

### 3. Error Handling
- Use try-except blocks with specific exception types
- Log errors with appropriate severity levels
- Implement graceful fallback (e.g., simulation mode if OBS unavailable)
- Add reconnection logic with exponential backoff for network operations

### 4. Logging
- Use Python's `logging` module, not print statements
- Create module-level loggers: `self.logger = logging.getLogger(__name__)`
- Use appropriate log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Include context in log messages (platform name, video ID, etc.)

### 5. AI Agent System
- All agents inherit from `BaseAgent` in `src/ai_agents/base_agent.py`
- Agents communicate via `AgentMessage` dataclass
- Use `AgentRecommendation` for decision outputs
- Coordinator resolves conflicts between agent recommendations
- Agents run in independent async loops with configurable update intervals

## Code Conventions

### Naming Conventions
- **Classes**: PascalCase (e.g., `StreamManager`, `OBSController`)
- **Functions/Methods**: snake_case (e.g., `load_config`, `start_streaming`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT`)
- **Private methods**: prefix with underscore (e.g., `_process_messages`)

### Type Hints
- Always use type hints for function parameters and return values
- Import from `typing` module: `Dict`, `List`, `Optional`, `Any`, etc.
- Use `Optional[Type]` for nullable parameters
- Example: `def get_video(self, video_id: str) -> Optional[Dict[str, Any]]:`

### Docstrings
- Use Google-style docstrings for all classes and public methods
- Include Args, Returns, and Raises sections
- Example:
  ```python
  def process_video(self, video: Dict[str, Any]) -> bool:
      """Process a video for streaming.
      
      Args:
          video: Video metadata dictionary
          
      Returns:
          True if processing succeeded, False otherwise
          
      Raises:
          ValueError: If video format is invalid
      """
  ```

### Data Classes
- Use `@dataclass` for data structures (see `AgentMessage`, `AgentRecommendation`, `StreamInfo`)
- Prefer dataclasses over dictionaries for structured data with known fields

## Testing Guidelines

### Current State
- No formal test infrastructure currently exists
- When adding tests, create a `tests/` directory at the root level
- Use `pytest` for testing framework
- Follow naming convention: `test_<module_name>.py`

### Test Patterns to Implement
- Mock external services (OBS WebSocket, Odysee API, RTMP streams)
- Test error handling and edge cases
- Test async operations with `pytest-asyncio`
- Test configuration validation thoroughly

## Common Pitfalls

### 1. OBS WebSocket Version
- Use `obs-websocket-py>=1.0.0` (not `obsws-python`)
- Default port is 4455 (was 4444 in older versions)
- Always implement fallback to simulation mode if OBS is unavailable

### 2. Stream Keys
- Never commit actual stream keys to the repository
- Always use environment variables or .env file
- Validate that stream keys are not placeholder values before starting

### 3. Async Context
- Don't mix async and sync code improperly
- Use `asyncio.run()` only at the top level
- Use `await` for all async function calls
- Don't block the event loop with synchronous I/O

### 4. Platform-Specific Issues
- Each platform has different RTMP requirements
- Implement platform-specific validation
- Handle platform-specific errors separately
- Test with each platform independently

### 5. AI Agent Coordination
- Agents can produce conflicting recommendations
- Always use the `AIAgentCoordinator` to resolve conflicts
- High severity issues require manual approval, don't auto-apply
- Set appropriate expiration times for recommendations

## Important Files

### Core Application
- `main.py` - Main entry point with CLI interface
- `src/config_manager.py` - Configuration loading and validation
- `src/obs_controller.py` - OBS WebSocket control
- `src/stream_manager.py` - Multi-platform streaming logic
- `src/video_queue.py` - Video queue management
- `src/odysee_client.py` - Odysee API integration

### AI Agent System
- `src/ai_agents/base_agent.py` - Base agent class and data structures
- `src/ai_agents/coordinator.py` - Central coordination and conflict resolution
- `src/ai_agents/content_curation_agent.py` - Content optimization
- `src/ai_agents/stream_quality_agent.py` - Quality monitoring

### Configuration
- `config.json` - Main configuration (not in repo, use `config.json.example`)
- `.env` - Environment variables for secrets (not in repo, use `.env.example`)
- `requirements.txt` - Python dependencies

### Documentation
- `README.md` - Main documentation
- `AI_BENEFITS_SUMMARY.md` - AI features overview
- `AI_AGENT_INTEGRATION.md` - AI integration details
- `QUICKSTART.md` - Quick start guide

## Development Workflow

### Adding New Features
1. Update configuration schema in `config.json.example` if needed
2. Add new classes/modules following existing patterns
3. Update `README.md` with new features
4. Test with simulation mode first
5. Test with actual services in development environment

### Adding New AI Agents
1. Inherit from `BaseAgent`
2. Implement required abstract methods: `initialize()`, `cleanup()`, `process()`, `handle_message()`
3. Register agent in `AIAgentCoordinator`
4. Add configuration in `config.json` under `ai_agents.agents.<agent_name>`
5. Document agent behavior and recommendation types

### Error Recovery
- Implement retry logic with exponential backoff
- Provide clear error messages to users
- Log detailed error information for debugging
- Always clean up resources (close connections, stop tasks)

## Dependencies

### Required Packages
- `obs-websocket-py>=1.0.0` - OBS WebSocket client
- `requests>=2.31.0` - HTTP requests
- `aiohttp>=3.8.0` - Async HTTP client
- `asyncio-throttle>=1.0.0` - Rate limiting
- `python-dotenv>=1.0.0` - Environment variable loading

### Adding Dependencies
- Add to `requirements.txt`
- Document why the dependency is needed
- Pin major version for stability
- Test that installation works on clean environment

## Security Considerations

1. **Never commit secrets** - Use `.env` file and `.gitignore`
2. **Validate all inputs** - Especially from configuration files
3. **Sanitize URLs** - Prevent injection attacks
4. **Rate limiting** - Respect API rate limits
5. **Connection security** - Use HTTPS where possible

## Performance Best Practices

1. **Use async operations** for all I/O
2. **Batch API requests** when possible
3. **Implement caching** for frequently accessed data
4. **Monitor resource usage** (CPU, memory, network)
5. **Use connection pooling** for HTTP requests
6. **Implement graceful shutdown** to clean up resources

## Debugging Tips

1. **Enable verbose logging**: Run with `--verbose` flag
2. **Check logs**: Review `livestream.log` for detailed errors
3. **Validate config**: Use `--validate-only` to check configuration
4. **Simulation mode**: Test without actual streaming using simulation mode
5. **OBS logs**: Check OBS Studio logs if WebSocket connection fails
6. **Network tools**: Use tools like `ffprobe` to test RTMP streams

## When to Ask for Clarification

- If requirements conflict with existing patterns
- If changes would break backward compatibility
- If new dependencies are needed
- If architectural changes are required
- If security implications are unclear
- If platform-specific behavior is ambiguous

## Code Review Checklist

- [ ] Type hints added for all new functions
- [ ] Docstrings provided for public methods
- [ ] Error handling implemented
- [ ] Logging added for important operations
- [ ] Configuration validation updated
- [ ] No secrets committed
- [ ] Async/await used correctly
- [ ] Resource cleanup implemented
- [ ] Documentation updated
- [ ] Compatible with Python 3.8+
