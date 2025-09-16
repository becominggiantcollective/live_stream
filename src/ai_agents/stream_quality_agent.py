"""
Stream Quality Agent

Monitors stream health and automatically optimizes streaming parameters for
optimal performance across all platforms.
"""

import logging
import asyncio
import random
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from .base_agent import BaseAgent, AgentMessage

class StreamMetrics:
    """Container for stream performance metrics."""
    
    def __init__(self):
        self.bitrate = 0.0
        self.fps = 0.0
        self.resolution = (0, 0)
        self.dropped_frames = 0
        self.network_latency = 0.0
        self.buffer_health = 1.0
        self.cpu_usage = 0.0
        self.memory_usage = 0.0
        self.timestamp = datetime.now()

class StreamQualityAgent(BaseAgent):
    """AI agent for monitoring and optimizing stream quality."""
    
    def __init__(self, config_manager, enabled: bool = True):
        """Initialize the Stream Quality Agent."""
        super().__init__("stream_quality", config_manager, enabled)
        
        # Quality monitoring settings
        self.monitoring_interval = self.agent_config.get('monitoring_interval', 30)
        self.quality_threshold = self.agent_config.get('quality_threshold', 0.8)
        self.auto_adjust = self.agent_config.get('auto_adjust', True)
        
        # Quality metrics tracking
        self.platform_metrics = {}
        self.quality_history = []
        self.current_settings = {}
        
        # Optimization strategies
        self.optimization_strategies = {
            'conservative': {'bitrate_step': 0.1, 'resolution_step': 0.05},
            'aggressive': {'bitrate_step': 0.2, 'resolution_step': 0.1},
            'adaptive': {'bitrate_step': 0.15, 'resolution_step': 0.08}
        }
        
        self.current_strategy = 'adaptive'
        
    async def initialize(self):
        """Initialize the agent-specific components."""
        self.logger.info("Initializing Stream Quality Agent...")
        
        # Initialize platform metrics
        enabled_platforms = self.config.get_enabled_platforms()
        for platform_name in enabled_platforms.keys():
            self.platform_metrics[platform_name] = StreamMetrics()
            self.current_settings[platform_name] = {
                'bitrate': 2500,  # kbps
                'resolution': (1920, 1080),
                'fps': 30,
                'encoder': 'x264'
            }
        
        self.logger.info(f"Monitoring {len(enabled_platforms)} platforms")
        
    async def cleanup(self):
        """Cleanup agent resources."""
        self.logger.info("Cleaning up Stream Quality Agent...")
        # Save optimization data, close connections, etc.
    
    async def process(self):
        """Main processing logic - monitor and optimize stream quality."""
        try:
            # Collect current metrics from all platforms
            await self._collect_metrics()
            
            # Analyze quality and detect issues
            quality_issues = await self._analyze_quality()
            
            # Generate optimization recommendations
            if quality_issues:
                await self._generate_optimizations(quality_issues)
            
            # Update quality history
            await self._update_quality_history()
            
        except Exception as e:
            self.logger.error(f"Error in quality monitoring: {e}")
    
    async def handle_message(self, message: AgentMessage):
        """Handle messages from other agents or coordinator."""
        try:
            if message.message_type == "quality_report_request":
                await self._send_quality_report(message.data)
            elif message.message_type == "adjust_settings":
                await self._apply_settings_adjustment(message.data)
            elif message.message_type == "platform_status_update":
                await self._update_platform_status(message.data)
            else:
                self.logger.warning(f"Unknown message type: {message.message_type}")
                
        except Exception as e:
            self.logger.error(f"Error handling message {message.message_type}: {e}")
    
    async def _collect_metrics(self):
        """Collect performance metrics from all streaming platforms."""
        for platform_name in self.platform_metrics.keys():
            # Simulate metric collection (in real implementation, get from OBS/platform APIs)
            metrics = await self._simulate_platform_metrics(platform_name)
            self.platform_metrics[platform_name] = metrics
            
            # Log significant changes
            if metrics.dropped_frames > 100:
                self.logger.warning(f"{platform_name}: High dropped frames detected ({metrics.dropped_frames})")
            
            if metrics.network_latency > 1000:  # >1 second
                self.logger.warning(f"{platform_name}: High network latency ({metrics.network_latency}ms)")
    
    async def _simulate_platform_metrics(self, platform_name: str) -> StreamMetrics:
        """Simulate collecting real metrics from a platform (mock implementation)."""
        metrics = StreamMetrics()
        
        # Simulate realistic streaming metrics with some variability
        base_quality = random.uniform(0.7, 0.95)
        
        # Bitrate simulation
        target_bitrate = self.current_settings[platform_name]['bitrate']
        metrics.bitrate = target_bitrate * random.uniform(0.9, 1.1)
        
        # FPS simulation
        target_fps = self.current_settings[platform_name]['fps']
        metrics.fps = target_fps * random.uniform(0.95, 1.0)
        
        # Resolution
        metrics.resolution = self.current_settings[platform_name]['resolution']
        
        # Network-dependent metrics
        if base_quality > 0.85:
            metrics.dropped_frames = random.randint(0, 50)
            metrics.network_latency = random.uniform(50, 200)
            metrics.buffer_health = random.uniform(0.8, 1.0)
        else:
            metrics.dropped_frames = random.randint(100, 500)
            metrics.network_latency = random.uniform(300, 1500)
            metrics.buffer_health = random.uniform(0.3, 0.7)
        
        # System resource usage
        metrics.cpu_usage = random.uniform(30, 85)
        metrics.memory_usage = random.uniform(40, 75)
        
        return metrics
    
    async def _analyze_quality(self) -> List[Dict[str, Any]]:
        """Analyze current quality metrics and identify issues."""
        quality_issues = []
        
        for platform_name, metrics in self.platform_metrics.items():
            platform_issues = []
            
            # Check dropped frames
            if metrics.dropped_frames > 200:
                platform_issues.append({
                    'type': 'dropped_frames',
                    'severity': 'high' if metrics.dropped_frames > 500 else 'medium',
                    'value': metrics.dropped_frames,
                    'threshold': 200,
                    'message': f'High dropped frames detected: {metrics.dropped_frames}'
                })
            
            # Check network latency
            if metrics.network_latency > 500:
                platform_issues.append({
                    'type': 'network_latency',
                    'severity': 'high' if metrics.network_latency > 1000 else 'medium',
                    'value': metrics.network_latency,
                    'threshold': 500,
                    'message': f'High network latency: {metrics.network_latency}ms'
                })
            
            # Check buffer health
            if metrics.buffer_health < 0.5:
                platform_issues.append({
                    'type': 'buffer_health',
                    'severity': 'high' if metrics.buffer_health < 0.3 else 'medium',
                    'value': metrics.buffer_health,
                    'threshold': 0.5,
                    'message': f'Low buffer health: {metrics.buffer_health:.2f}'
                })
            
            # Check system resources
            if metrics.cpu_usage > 80:
                platform_issues.append({
                    'type': 'cpu_usage',
                    'severity': 'high' if metrics.cpu_usage > 90 else 'medium',
                    'value': metrics.cpu_usage,
                    'threshold': 80,
                    'message': f'High CPU usage: {metrics.cpu_usage}%'
                })
            
            if platform_issues:
                quality_issues.append({
                    'platform': platform_name,
                    'issues': platform_issues,
                    'overall_severity': max(issue['severity'] for issue in platform_issues)
                })
        
        return quality_issues
    
    async def _generate_optimizations(self, quality_issues: List[Dict[str, Any]]):
        """Generate optimization recommendations based on quality issues."""
        for platform_issue in quality_issues:
            platform_name = platform_issue['platform']
            issues = platform_issue['issues']
            severity = platform_issue['overall_severity']
            
            optimizations = []
            
            for issue in issues:
                if issue['type'] == 'dropped_frames':
                    # Reduce bitrate to help with dropped frames
                    optimizations.append({
                        'action': 'reduce_bitrate',
                        'percentage': 15 if issue['severity'] == 'high' else 10,
                        'reason': 'Reduce encoding load to prevent frame drops'
                    })
                
                elif issue['type'] == 'network_latency':
                    # Reduce bitrate and possibly resolution
                    optimizations.append({
                        'action': 'reduce_bitrate',
                        'percentage': 20 if issue['severity'] == 'high' else 15,
                        'reason': 'Reduce bandwidth usage due to network issues'
                    })
                    
                    if issue['severity'] == 'high':
                        optimizations.append({
                            'action': 'reduce_resolution',
                            'target': (1280, 720),  # Drop to 720p
                            'reason': 'Severe network issues require resolution reduction'
                        })
                
                elif issue['type'] == 'buffer_health':
                    # Conservative bitrate reduction and encoder optimization
                    optimizations.append({
                        'action': 'reduce_bitrate',
                        'percentage': 10,
                        'reason': 'Improve buffer stability'
                    })
                    
                    optimizations.append({
                        'action': 'optimize_encoder',
                        'preset': 'faster',
                        'reason': 'Reduce encoding latency'
                    })
                
                elif issue['type'] == 'cpu_usage':
                    # Encoder optimization and possible resolution reduction
                    optimizations.append({
                        'action': 'optimize_encoder',
                        'preset': 'veryfast',
                        'reason': 'Reduce CPU load'
                    })
                    
                    if issue['severity'] == 'high':
                        optimizations.append({
                            'action': 'reduce_fps',
                            'target': 24,
                            'reason': 'Severe CPU load requires FPS reduction'
                        })
            
            # Create recommendation
            if optimizations:
                recommendation = self.create_recommendation(
                    recommendation_type="quality_optimization",
                    confidence=0.85,
                    data={
                        'platform': platform_name,
                        'optimizations': optimizations,
                        'issues_detected': issues,
                        'severity': severity,
                        'auto_apply': self.auto_adjust and severity != 'high'  # Auto-apply only for medium issues
                    },
                    expires_in_seconds=300  # 5 minutes
                )
                
                await self.send_message(
                    "coordinator",
                    "quality_optimization_needed",
                    {"recommendation": recommendation.data},
                    priority=2 if severity == 'high' else 1
                )
                
                # Auto-apply if enabled and safe
                if self.auto_adjust and severity != 'high':
                    await self._apply_optimizations(platform_name, optimizations)
    
    async def _apply_optimizations(self, platform_name: str, optimizations: List[Dict[str, Any]]):
        """Apply optimization recommendations to platform settings."""
        current = self.current_settings[platform_name]
        new_settings = current.copy()
        
        for optimization in optimizations:
            action = optimization['action']
            
            if action == 'reduce_bitrate':
                percentage = optimization['percentage'] / 100
                new_settings['bitrate'] = int(current['bitrate'] * (1 - percentage))
                
            elif action == 'reduce_resolution':
                new_settings['resolution'] = optimization['target']
                
            elif action == 'reduce_fps':
                new_settings['fps'] = optimization['target']
                
            elif action == 'optimize_encoder':
                new_settings['encoder_preset'] = optimization['preset']
        
        # Apply settings (in real implementation, update OBS)
        self.current_settings[platform_name] = new_settings
        
        self.logger.info(f"Applied optimizations to {platform_name}: {optimizations}")
        
        # Send notification
        await self.send_message(
            "coordinator",
            "settings_applied",
            {
                'platform': platform_name,
                'old_settings': current,
                'new_settings': new_settings,
                'optimizations': optimizations
            },
            priority=1
        )
    
    async def _update_quality_history(self):
        """Update quality history for trend analysis."""
        current_time = datetime.now()
        
        # Calculate overall quality score
        total_score = 0
        platform_count = 0
        
        for platform_name, metrics in self.platform_metrics.items():
            # Simple quality scoring algorithm
            score = 1.0
            
            # Penalize dropped frames
            if metrics.dropped_frames > 0:
                score -= min(0.5, metrics.dropped_frames / 1000)
            
            # Penalize high latency
            if metrics.network_latency > 100:
                score -= min(0.3, (metrics.network_latency - 100) / 2000)
            
            # Penalize low buffer health
            score *= metrics.buffer_health
            
            # Penalize high CPU usage
            if metrics.cpu_usage > 70:
                score -= min(0.2, (metrics.cpu_usage - 70) / 100)
            
            total_score += max(0, score)
            platform_count += 1
        
        if platform_count > 0:
            overall_quality = total_score / platform_count
            
            self.quality_history.append({
                'timestamp': current_time,
                'overall_quality': overall_quality,
                'platform_details': {name: {
                    'dropped_frames': metrics.dropped_frames,
                    'latency': metrics.network_latency,
                    'buffer_health': metrics.buffer_health,
                    'cpu_usage': metrics.cpu_usage
                } for name, metrics in self.platform_metrics.items()}
            })
            
            # Keep only last hour of history
            cutoff_time = current_time - timedelta(hours=1)
            self.quality_history = [h for h in self.quality_history if h['timestamp'] > cutoff_time]
            
            # Check for quality trends
            if len(self.quality_history) > 5:
                await self._analyze_quality_trends()
    
    async def _analyze_quality_trends(self):
        """Analyze quality trends over time."""
        if len(self.quality_history) < 10:
            return
        
        recent_scores = [h['overall_quality'] for h in self.quality_history[-10:]]
        older_scores = [h['overall_quality'] for h in self.quality_history[-20:-10]] if len(self.quality_history) >= 20 else []
        
        if older_scores:
            recent_avg = sum(recent_scores) / len(recent_scores)
            older_avg = sum(older_scores) / len(older_scores)
            
            trend = recent_avg - older_avg
            
            if trend < -0.1:  # Declining quality
                recommendation = self.create_recommendation(
                    recommendation_type="quality_trend_alert",
                    confidence=0.9,
                    data={
                        'trend': 'declining',
                        'magnitude': abs(trend),
                        'recent_average': recent_avg,
                        'older_average': older_avg,
                        'recommendation': 'Review stream settings and consider conservative optimizations'
                    },
                    expires_in_seconds=1800  # 30 minutes
                )
                
                await self.send_message(
                    "coordinator",
                    "quality_trend_alert",
                    {"recommendation": recommendation.data},
                    priority=2
                )
            
            elif trend > 0.1:  # Improving quality
                self.logger.info(f"Quality trend improving: {trend:.3f}")
    
    async def _send_quality_report(self, request_data: Dict[str, Any]):
        """Send comprehensive quality report."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'platforms': {},
            'overall_health': 'good',
            'recommendations': len(self.get_recent_recommendations())
        }
        
        total_issues = 0
        for platform_name, metrics in self.platform_metrics.items():
            platform_health = 'good'
            
            if metrics.dropped_frames > 200 or metrics.network_latency > 500 or metrics.buffer_health < 0.5:
                platform_health = 'warning'
                total_issues += 1
            
            if metrics.dropped_frames > 500 or metrics.network_latency > 1000 or metrics.buffer_health < 0.3:
                platform_health = 'critical'
                total_issues += 2
            
            report['platforms'][platform_name] = {
                'health': platform_health,
                'bitrate': metrics.bitrate,
                'fps': metrics.fps,
                'resolution': metrics.resolution,
                'dropped_frames': metrics.dropped_frames,
                'network_latency': metrics.network_latency,
                'buffer_health': metrics.buffer_health,
                'cpu_usage': metrics.cpu_usage,
                'current_settings': self.current_settings[platform_name]
            }
        
        if total_issues >= 3:
            report['overall_health'] = 'critical'
        elif total_issues >= 1:
            report['overall_health'] = 'warning'
        
        await self.send_message(
            request_data.get('requester', 'coordinator'),
            "quality_report",
            report,
            priority=1
        )
    
    # Public interface methods
    
    def get_current_quality(self) -> Dict[str, Any]:
        """Get current quality status for all platforms."""
        return {
            'platforms': {
                name: {
                    'dropped_frames': metrics.dropped_frames,
                    'network_latency': metrics.network_latency,
                    'buffer_health': metrics.buffer_health,
                    'cpu_usage': metrics.cpu_usage,
                    'timestamp': metrics.timestamp.isoformat()
                } for name, metrics in self.platform_metrics.items()
            },
            'current_settings': self.current_settings
        }
    
    def get_quality_trends(self) -> List[Dict[str, Any]]:
        """Get quality trend data."""
        return self.quality_history[-20:]  # Last 20 data points
    
    async def manual_optimization(self, platform_name: str, optimization_type: str) -> bool:
        """Manually trigger optimization for a platform."""
        if platform_name not in self.platform_metrics:
            return False
        
        optimizations = []
        
        if optimization_type == 'conservative':
            optimizations.append({
                'action': 'reduce_bitrate',
                'percentage': 10,
                'reason': 'Manual conservative optimization'
            })
        elif optimization_type == 'aggressive':
            optimizations.append({
                'action': 'reduce_bitrate',
                'percentage': 20,
                'reason': 'Manual aggressive optimization'
            })
            optimizations.append({
                'action': 'reduce_resolution',
                'target': (1280, 720),
                'reason': 'Manual aggressive optimization'
            })
        
        if optimizations:
            await self._apply_optimizations(platform_name, optimizations)
            return True
        
        return False