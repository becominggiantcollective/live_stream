"""
AI Agents package for Live Stream Bot

This package contains AI-powered agents that enhance the streaming experience
through intelligent automation and optimization.
"""

__version__ = "1.0.0"
__author__ = "Live Stream Bot AI Team"

from .base_agent import BaseAgent
from .content_curation_agent import ContentCurationAgent
from .stream_quality_agent import StreamQualityAgent
from .coordinator import AIAgentCoordinator

__all__ = [
    'BaseAgent',
    'ContentCurationAgent', 
    'StreamQualityAgent',
    'AIAgentCoordinator'
]