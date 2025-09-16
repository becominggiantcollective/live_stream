"""
AI Agent Coordinator

Central coordinator that manages all AI agents and facilitates communication
between them and the main streaming system.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base_agent import BaseAgent, AgentMessage, AgentRecommendation
from .content_curation_agent import ContentCurationAgent
from .stream_quality_agent import StreamQualityAgent

class AgentMessageBus:
    """Message bus for inter-agent communication."""
    
    def __init__(self):
        self.subscribers = {}
        self.message_history = []
        
    async def subscribe(self, agent_name: str, agent_instance: BaseAgent):
        """Subscribe an agent to the message bus."""
        self.subscribers[agent_name] = agent_instance
        
    async def publish(self, message: AgentMessage):
        """Publish a message to the appropriate recipient."""
        self.message_history.append(message)
        
        # Keep only last 1000 messages
        if len(self.message_history) > 1000:
            self.message_history = self.message_history[-1000:]
        
        if message.recipient in self.subscribers:
            await self.subscribers[message.recipient].receive_message(message)
        elif message.recipient == "all":
            # Broadcast to all agents except sender
            for name, agent in self.subscribers.items():
                if name != message.sender:
                    await agent.receive_message(message)

class AIAgentCoordinator:
    """Central coordinator for all AI agents."""
    
    def __init__(self, config_manager):
        """Initialize the AI Agent Coordinator."""
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        
        # Agent management
        self.agents = {}
        self.message_bus = AgentMessageBus()
        self.is_running = False
        
        # Coordination settings
        ai_config = self.config.get('ai_agents', {})
        self.enabled = ai_config.get('enabled', True)
        self.coordination_interval = ai_config.get('coordination_interval', 60)
        
        # Recommendation tracking
        self.active_recommendations = []
        self.applied_recommendations = []
        
        self.logger.info(f"AI Agent Coordinator initialized (enabled: {self.enabled})")
    
    async def initialize(self):
        """Initialize all AI agents."""
        if not self.enabled:
            self.logger.info("AI agents disabled, skipping initialization")
            return
        
        self.logger.info("Initializing AI agents...")
        
        try:
            # Initialize content curation agent
            content_agent = ContentCurationAgent(self.config)
            self.agents['content_curation'] = content_agent
            await self.message_bus.subscribe('content_curation', content_agent)
            
            # Initialize stream quality agent
            quality_agent = StreamQualityAgent(self.config)
            self.agents['stream_quality'] = quality_agent
            await self.message_bus.subscribe('stream_quality', quality_agent)
            
            # Subscribe coordinator to message bus
            await self.message_bus.subscribe('coordinator', self)
            
            # Start all agents
            for agent_name, agent in self.agents.items():
                if agent.is_enabled():
                    await agent.start()
                    self.logger.info(f"Started agent: {agent_name}")
                else:
                    self.logger.info(f"Agent {agent_name} is disabled")
            
            self.is_running = True
            
            # Start coordination loop
            asyncio.create_task(self._coordination_loop())
            
            self.logger.info(f"AI Agent Coordinator started with {len(self.agents)} agents")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AI agents: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown all AI agents."""
        self.is_running = False
        self.logger.info("Shutting down AI agents...")
        
        for agent_name, agent in self.agents.items():
            try:
                await agent.stop()
                self.logger.info(f"Stopped agent: {agent_name}")
            except Exception as e:
                self.logger.error(f"Error stopping agent {agent_name}: {e}")
        
        self.logger.info("AI Agent Coordinator shutdown complete")
    
    async def _coordination_loop(self):
        """Main coordination loop."""
        while self.is_running:
            try:
                # Collect recommendations from all agents
                await self._collect_recommendations()
                
                # Resolve conflicts between recommendations
                await self._resolve_recommendation_conflicts()
                
                # Apply high-priority recommendations
                await self._apply_priority_recommendations()
                
                # Send coordination messages
                await self._send_coordination_updates()
                
                await asyncio.sleep(self.coordination_interval)
                
            except Exception as e:
                self.logger.error(f"Error in coordination loop: {e}")
                await asyncio.sleep(5)  # Brief pause before retrying
    
    async def _collect_recommendations(self):
        """Collect recommendations from all agents."""
        new_recommendations = []
        
        for agent_name, agent in self.agents.items():
            try:
                recent_recs = agent.get_recent_recommendations()
                new_recommendations.extend(recent_recs)
            except Exception as e:
                self.logger.error(f"Error collecting recommendations from {agent_name}: {e}")
        
        # Add new recommendations to active list
        for rec in new_recommendations:
            if rec not in self.active_recommendations:
                self.active_recommendations.append(rec)
                self.logger.info(f"New recommendation from {rec.agent_name}: {rec.recommendation_type}")
        
        # Remove expired recommendations
        current_time = datetime.now()
        self.active_recommendations = [
            rec for rec in self.active_recommendations
            if rec.expires_at is None or rec.expires_at > current_time
        ]
    
    async def _resolve_recommendation_conflicts(self):
        """Resolve conflicts between agent recommendations."""
        # Group recommendations by type
        by_type = {}
        for rec in self.active_recommendations:
            rec_type = rec.recommendation_type
            if rec_type not in by_type:
                by_type[rec_type] = []
            by_type[rec_type].append(rec)
        
        # Resolve conflicts for each type
        for rec_type, recommendations in by_type.items():
            if len(recommendations) > 1:
                await self._resolve_type_conflict(rec_type, recommendations)
    
    async def _resolve_type_conflict(self, rec_type: str, recommendations: List[AgentRecommendation]):
        """Resolve conflicts for a specific recommendation type."""
        if rec_type == "quality_optimization":
            # For quality optimizations, prefer the most conservative approach
            best_rec = min(recommendations, key=lambda r: r.data.get('severity', 'low'))
            
        elif rec_type == "playlist_optimization":
            # For playlist optimizations, prefer the highest confidence
            best_rec = max(recommendations, key=lambda r: r.confidence)
            
        else:
            # Default: choose highest confidence
            best_rec = max(recommendations, key=lambda r: r.confidence)
        
        # Remove conflicting recommendations
        for rec in recommendations:
            if rec != best_rec and rec in self.active_recommendations:
                self.active_recommendations.remove(rec)
                
        self.logger.info(f"Resolved conflict for {rec_type}: chose {best_rec.agent_name} recommendation")
    
    async def _apply_priority_recommendations(self):
        """Apply high-priority recommendations automatically."""
        high_priority = [
            rec for rec in self.active_recommendations
            if rec.data.get('auto_apply', False) and rec.confidence > 0.8
        ]
        
        for rec in high_priority:
            try:
                await self._apply_recommendation(rec)
                self.active_recommendations.remove(rec)
                self.applied_recommendations.append(rec)
                
                self.logger.info(f"Auto-applied recommendation: {rec.recommendation_type} from {rec.agent_name}")
                
            except Exception as e:
                self.logger.error(f"Error applying recommendation {rec.recommendation_type}: {e}")
    
    async def _apply_recommendation(self, recommendation: AgentRecommendation):
        """Apply a specific recommendation."""
        rec_type = recommendation.recommendation_type
        data = recommendation.data
        
        if rec_type == "quality_optimization":
            await self._apply_quality_optimization(data)
            
        elif rec_type == "playlist_optimization":
            await self._apply_playlist_optimization(data)
            
        elif rec_type == "peak_hour_content":
            await self._apply_content_strategy(data)
            
        else:
            self.logger.warning(f"Unknown recommendation type: {rec_type}")
    
    async def _apply_quality_optimization(self, data: Dict[str, Any]):
        """Apply quality optimization recommendation."""
        platform = data.get('platform')
        optimizations = data.get('optimizations', [])
        
        # In real implementation, this would update OBS settings
        self.logger.info(f"Applying quality optimizations to {platform}: {len(optimizations)} changes")
        
        # Send message to stream quality agent
        message = AgentMessage(
            sender="coordinator",
            recipient="stream_quality",
            message_type="apply_optimizations",
            data=data,
            timestamp=datetime.now(),
            priority=2
        )
        await self.message_bus.publish(message)
    
    async def _apply_playlist_optimization(self, data: Dict[str, Any]):
        """Apply playlist optimization recommendation."""
        optimized_order = data.get('optimized_order', [])
        
        if optimized_order:
            self.logger.info(f"Applying playlist optimization: reordering {len(optimized_order)} videos")
            
            # In real implementation, this would update the video queue
            # For now, send notification
            message = AgentMessage(
                sender="coordinator",
                recipient="content_curation",
                message_type="playlist_updated",
                data={"status": "applied", "video_count": len(optimized_order)},
                timestamp=datetime.now(),
                priority=1
            )
            await self.message_bus.publish(message)
    
    async def _apply_content_strategy(self, data: Dict[str, Any]):
        """Apply content strategy recommendation."""
        strategy = data.get('strategy')
        
        self.logger.info(f"Applying content strategy: {strategy}")
        
        # Send message to content curation agent
        message = AgentMessage(
            sender="coordinator",
            recipient="content_curation",
            message_type="strategy_update",
            data=data,
            timestamp=datetime.now(),
            priority=1
        )
        await self.message_bus.publish(message)
    
    async def _send_coordination_updates(self):
        """Send periodic coordination updates to agents."""
        # Send status updates to all agents
        status_data = {
            'active_recommendations': len(self.active_recommendations),
            'applied_recommendations': len(self.applied_recommendations),
            'agent_count': len(self.agents)
        }
        
        message = AgentMessage(
            sender="coordinator",
            recipient="all",
            message_type="coordination_status",
            data=status_data,
            timestamp=datetime.now(),
            priority=0
        )
        await self.message_bus.publish(message)
    
    async def receive_message(self, message: AgentMessage):
        """Handle messages sent to the coordinator."""
        try:
            if message.message_type == "content_recommendation":
                await self._handle_content_recommendation(message)
                
            elif message.message_type == "quality_optimization_needed":
                await self._handle_quality_optimization(message)
                
            elif message.message_type == "agent_status_update":
                await self._handle_agent_status_update(message)
                
            else:
                self.logger.info(f"Received message from {message.sender}: {message.message_type}")
                
        except Exception as e:
            self.logger.error(f"Error handling message from {message.sender}: {e}")
    
    async def _handle_content_recommendation(self, message: AgentMessage):
        """Handle content recommendations from agents."""
        recommendation_data = message.data.get('recommendation', {})
        
        self.logger.info(f"Received content recommendation: {recommendation_data.get('type', 'unknown')}")
        
        # Add to active recommendations for processing
        # (already collected in _collect_recommendations, but could add immediate processing here)
    
    async def _handle_quality_optimization(self, message: AgentMessage):
        """Handle quality optimization requests."""
        recommendation_data = message.data.get('recommendation', {})
        severity = recommendation_data.get('severity', 'medium')
        
        self.logger.info(f"Received quality optimization request (severity: {severity})")
        
        # For high severity issues, apply immediately
        if severity == 'high':
            await self._apply_quality_optimization(recommendation_data)
    
    async def _handle_agent_status_update(self, message: AgentMessage):
        """Handle agent status updates."""
        status = message.data.get('status')
        self.logger.info(f"Agent {message.sender} status update: {status}")
    
    # Public interface methods
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents."""
        status = {
            'coordinator_running': self.is_running,
            'enabled': self.enabled,
            'agent_count': len(self.agents),
            'active_recommendations': len(self.active_recommendations),
            'applied_recommendations': len(self.applied_recommendations),
            'agents': {}
        }
        
        for name, agent in self.agents.items():
            status['agents'][name] = agent.get_status()
        
        return status
    
    def get_recommendations(self, include_applied: bool = False) -> List[Dict[str, Any]]:
        """Get current recommendations."""
        recommendations = []
        
        for rec in self.active_recommendations:
            recommendations.append({
                'agent': rec.agent_name,
                'type': rec.recommendation_type,
                'confidence': rec.confidence,
                'data': rec.data,
                'timestamp': rec.timestamp.isoformat(),
                'expires_at': rec.expires_at.isoformat() if rec.expires_at else None
            })
        
        if include_applied:
            for rec in self.applied_recommendations[-10:]:  # Last 10 applied
                recommendations.append({
                    'agent': rec.agent_name,
                    'type': rec.recommendation_type,
                    'confidence': rec.confidence,
                    'data': rec.data,
                    'timestamp': rec.timestamp.isoformat(),
                    'status': 'applied'
                })
        
        return recommendations
    
    async def manual_coordination(self, action: str, data: Dict[str, Any] = None) -> bool:
        """Manually trigger coordination actions."""
        try:
            if action == "collect_recommendations":
                await self._collect_recommendations()
                return True
                
            elif action == "apply_recommendation" and data:
                rec_id = data.get('recommendation_id')
                # Find and apply specific recommendation
                # Implementation would depend on how recommendations are identified
                return True
                
            elif action == "resolve_conflicts":
                await self._resolve_recommendation_conflicts()
                return True
                
            else:
                self.logger.warning(f"Unknown manual coordination action: {action}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error in manual coordination {action}: {e}")
            return False
    
    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """Get a specific agent instance."""
        return self.agents.get(agent_name)