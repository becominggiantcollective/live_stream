"""
Base Agent class for AI agents in the Live Stream Bot

Provides common functionality and interface for all AI agents.
"""

import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class AgentMessage:
    """Message structure for inter-agent communication."""
    sender: str
    recipient: str
    message_type: str
    data: Dict[str, Any]
    timestamp: datetime
    priority: int = 0  # 0 = low, 1 = medium, 2 = high

@dataclass
class AgentRecommendation:
    """Recommendation structure from AI agents."""
    agent_name: str
    recommendation_type: str
    confidence: float  # 0.0 to 1.0
    data: Dict[str, Any]
    timestamp: datetime
    expires_at: Optional[datetime] = None

class BaseAgent(ABC):
    """Base class for all AI agents."""
    
    def __init__(self, name: str, config_manager, enabled: bool = True):
        """Initialize the base agent.
        
        Args:
            name: Agent name
            config_manager: Configuration manager instance
            enabled: Whether the agent is enabled
        """
        self.name = name
        self.config = config_manager
        self.enabled = enabled
        self.logger = logging.getLogger(f"ai_agent.{name}")
        
        # Agent state
        self.is_running = False
        self.message_queue = asyncio.Queue()
        self.recommendations = []
        
        # Configuration
        self.agent_config = self.config.get(f'ai_agents.agents.{name}', {})
        self.update_interval = self.agent_config.get('update_interval', 60)
        
        self.logger.info(f"AI Agent '{name}' initialized (enabled: {enabled})")
    
    async def start(self):
        """Start the agent."""
        if not self.enabled:
            self.logger.info(f"Agent '{self.name}' is disabled, skipping start")
            return
            
        self.is_running = True
        self.logger.info(f"Starting AI Agent '{self.name}'")
        
        # Start the main agent loop
        asyncio.create_task(self._agent_loop())
        
        # Call agent-specific initialization
        await self.initialize()
    
    async def stop(self):
        """Stop the agent."""
        self.is_running = False
        self.logger.info(f"Stopping AI Agent '{self.name}'")
        await self.cleanup()
    
    async def _agent_loop(self):
        """Main agent processing loop."""
        while self.is_running:
            try:
                # Process any pending messages
                await self._process_messages()
                
                # Run agent-specific processing
                await self.process()
                
                # Wait for next iteration
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                self.logger.error(f"Error in agent loop for '{self.name}': {e}")
                await asyncio.sleep(5)  # Brief pause before retrying
    
    async def _process_messages(self):
        """Process messages in the queue."""
        while not self.message_queue.empty():
            try:
                message = self.message_queue.get_nowait()
                await self.handle_message(message)
            except Exception as e:
                self.logger.error(f"Error processing message in '{self.name}': {e}")
    
    async def send_message(self, recipient: str, message_type: str, data: Dict[str, Any], priority: int = 0):
        """Send a message to another agent or coordinator.
        
        Args:
            recipient: Target agent name or 'coordinator'
            message_type: Type of message
            data: Message data
            priority: Message priority (0-2)
        """
        message = AgentMessage(
            sender=self.name,
            recipient=recipient,
            message_type=message_type,
            data=data,
            timestamp=datetime.now(),
            priority=priority
        )
        
        # For now, log the message (in full implementation, this would go through message bus)
        self.logger.info(f"Sending message to {recipient}: {message_type}")
        
        return message
    
    async def receive_message(self, message: AgentMessage):
        """Receive a message from another agent.
        
        Args:
            message: The received message
        """
        await self.message_queue.put(message)
    
    def create_recommendation(self, recommendation_type: str, confidence: float, data: Dict[str, Any], expires_in_seconds: Optional[int] = None) -> AgentRecommendation:
        """Create a recommendation.
        
        Args:
            recommendation_type: Type of recommendation
            confidence: Confidence level (0.0 to 1.0)
            data: Recommendation data
            expires_in_seconds: Optional expiration time
            
        Returns:
            AgentRecommendation instance
        """
        expires_at = None
        if expires_in_seconds:
            expires_at = datetime.now() + timedelta(seconds=expires_in_seconds)
        
        recommendation = AgentRecommendation(
            agent_name=self.name,
            recommendation_type=recommendation_type,
            confidence=confidence,
            data=data,
            timestamp=datetime.now(),
            expires_at=expires_at
        )
        
        self.recommendations.append(recommendation)
        self.logger.info(f"Created recommendation: {recommendation_type} (confidence: {confidence:.2f})")
        
        return recommendation
    
    def get_recent_recommendations(self, max_age_seconds: int = 300) -> List[AgentRecommendation]:
        """Get recommendations from the last N seconds.
        
        Args:
            max_age_seconds: Maximum age of recommendations to return
            
        Returns:
            List of recent recommendations
        """
        cutoff_time = datetime.now() - timedelta(seconds=max_age_seconds)
        
        return [rec for rec in self.recommendations 
                if rec.timestamp >= cutoff_time and 
                (rec.expires_at is None or rec.expires_at > datetime.now())]
    
    # Abstract methods that must be implemented by subclasses
    
    @abstractmethod
    async def initialize(self):
        """Initialize the agent (called after start)."""
        pass
    
    @abstractmethod
    async def cleanup(self):
        """Cleanup when stopping the agent."""
        pass
    
    @abstractmethod
    async def process(self):
        """Main processing logic for the agent."""
        pass
    
    @abstractmethod
    async def handle_message(self, message: AgentMessage):
        """Handle received messages."""
        pass
    
    # Utility methods
    
    def is_enabled(self) -> bool:
        """Check if the agent is enabled."""
        return self.enabled
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            'name': self.name,
            'enabled': self.enabled,
            'running': self.is_running,
            'recommendations_count': len(self.recommendations),
            'recent_recommendations': len(self.get_recent_recommendations()),
            'update_interval': self.update_interval
        }