#!/usr/bin/env python3
"""
AI-Enhanced Live Stream Bot Example

This example demonstrates how the live streaming bot can be enhanced with AI agents
for intelligent content curation, quality monitoring, and optimization.
"""

import asyncio
import json
import logging
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config_manager import ConfigManager
from obs_controller import OBSController
from stream_manager import StreamManager
from video_queue import VideoQueue

# Import AI agents
from ai_agents import AIAgentCoordinator, ContentCurationAgent, StreamQualityAgent

class AIEnhancedLiveStreamBot:
    """AI-enhanced version of the Live Stream Bot with intelligent automation."""
    
    def __init__(self, config_path="config.json", enable_ai=True):
        """Initialize the AI-enhanced streaming bot."""
        self.config = ConfigManager(config_path)
        self.enable_ai = enable_ai
        
        # Setup logging
        self.setup_logging()
        
        # Core components
        self.obs_controller = OBSController(self.config)
        self.stream_manager = StreamManager(self.config)
        self.video_queue = VideoQueue()
        
        # AI components
        if self.enable_ai:
            self.ai_coordinator = AIAgentCoordinator(self.config)
        else:
            self.ai_coordinator = None
        
        self.running = False
        
    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Initialize all components including AI agents."""
        try:
            self.logger.info("Initializing AI-Enhanced Live Stream Bot...")
            
            # Initialize core components
            await self.obs_controller.connect()
            
            # Initialize AI coordinator and agents
            if self.ai_coordinator:
                await self.ai_coordinator.initialize()
                self.logger.info("AI agents initialized successfully")
            
            # Load initial content
            await self.load_sample_content()
            
            self.logger.info("AI-Enhanced Live Stream Bot initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AI-Enhanced Live Stream Bot: {e}")
            return False
    
    async def load_sample_content(self):
        """Load sample content for demonstration."""
        sample_videos = [
            {
                'id': 'tech_tutorial_1',
                'title': 'Python Programming Tutorial: Advanced Concepts',
                'url': 'https://example.com/python_tutorial.mp4',
                'duration': 420,  # 7 minutes
                'channel': 'TechChannel',
                'thumbnail': 'https://example.com/thumb1.jpg',
                'category': 'educational'
            },
            {
                'id': 'entertainment_1',
                'title': 'Funny Coding Moments Compilation',
                'url': 'https://example.com/funny_coding.mp4',
                'duration': 180,  # 3 minutes
                'channel': 'EntertainmentHub',
                'thumbnail': 'https://example.com/thumb2.jpg',
                'category': 'entertainment'
            },
            {
                'id': 'tech_review_1',
                'title': 'Latest AI Technology Review 2024',
                'url': 'https://example.com/ai_review.mp4',
                'duration': 300,  # 5 minutes
                'channel': 'TechReviewer',
                'thumbnail': 'https://example.com/thumb3.jpg',
                'category': 'tech_content'
            },
            {
                'id': 'educational_1',
                'title': 'How Machine Learning Works: Complete Guide',
                'url': 'https://example.com/ml_guide.mp4',
                'duration': 600,  # 10 minutes
                'channel': 'EduTech',
                'thumbnail': 'https://example.com/thumb4.jpg',
                'category': 'educational'
            },
            {
                'id': 'entertainment_2',
                'title': 'Amazing Developer Stories',
                'url': 'https://example.com/dev_stories.mp4',
                'duration': 240,  # 4 minutes
                'channel': 'DevStories',
                'thumbnail': 'https://example.com/thumb5.jpg',
                'category': 'entertainment'
            }
        ]
        
        # Add videos to queue
        self.video_queue.add_videos(sample_videos)
        self.logger.info(f"Loaded {len(sample_videos)} sample videos")
        
        # If AI is enabled, get content curation recommendations
        if self.ai_coordinator:
            content_agent = self.ai_coordinator.get_agent('content_curation')
            if content_agent:
                # Analyze all videos
                for video in sample_videos:
                    analysis = await content_agent.analyze_video(video)
                    self.logger.info(f"AI Analysis for '{video['title']}': Quality={analysis['quality_score']:.2f}, Engagement={analysis['engagement_prediction']:.2f}")
                
                # Optimize playlist order
                optimized_videos = await content_agent.optimize_playlist(sample_videos)
                
                # Update video queue with optimized order
                self.video_queue.clear()
                self.video_queue.add_videos(optimized_videos)
                
                self.logger.info("Playlist optimized by AI content curation agent")
    
    async def start_ai_enhanced_streaming(self):
        """Start the AI-enhanced streaming process."""
        if not await self.initialize():
            return False
        
        self.running = True
        self.logger.info("Starting AI-enhanced live streaming...")
        
        try:
            # Start streaming to configured platforms
            await self.stream_manager.start_streams()
            
            # Show AI agent status
            if self.ai_coordinator:
                status = self.ai_coordinator.get_agent_status()
                self.logger.info(f"AI Agents Status: {len(status['agents'])} agents running")
                
                for agent_name, agent_status in status['agents'].items():
                    self.logger.info(f"  {agent_name}: {'enabled' if agent_status['enabled'] else 'disabled'}")
            
            # Main streaming loop with AI enhancements
            video_count = 0
            while self.running and not self.video_queue.is_empty():
                video = self.video_queue.get_next_video()
                if video:
                    video_count += 1
                    await self.play_video_with_ai_enhancements(video, video_count)
                else:
                    break
            
            self.logger.info("Finished playing all videos")
            
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal. Stopping...")
        except Exception as e:
            self.logger.error(f"Streaming error: {e}")
        finally:
            await self.stop_streaming()
    
    async def play_video_with_ai_enhancements(self, video, video_number):
        """Play a video with AI-powered enhancements."""
        self.logger.info(f"Playing video {video_number}: {video.get('title', 'Unknown')}")
        
        try:
            # Get AI recommendations before playing
            if self.ai_coordinator:
                await self.get_ai_recommendations_for_video(video)
            
            # Set up the video source in OBS
            await self.obs_controller.set_video_source(video['url'])
            
            # Simulate video playback with AI monitoring
            duration = min(video.get('duration', 300), 10)  # Cap at 10 seconds for demo
            monitoring_interval = 2  # Check every 2 seconds
            
            elapsed_time = 0
            while elapsed_time < duration:
                # AI quality monitoring during playback
                if self.ai_coordinator and elapsed_time % monitoring_interval == 0:
                    await self.monitor_stream_quality()
                
                await asyncio.sleep(1)
                elapsed_time += 1
            
            # Post-video AI analysis
            if self.ai_coordinator:
                await self.update_ai_performance_data(video, elapsed_time)
            
        except Exception as e:
            self.logger.error(f"Error playing video {video.get('title', 'Unknown')}: {e}")
    
    async def get_ai_recommendations_for_video(self, video):
        """Get AI recommendations before playing a video."""
        try:
            # Get content insights
            content_agent = self.ai_coordinator.get_agent('content_curation')
            if content_agent:
                insights = content_agent.get_content_insights()
                if insights['recent_recommendations'] > 0:
                    self.logger.info(f"AI Content Insights: {insights['recent_recommendations']} recent recommendations")
            
            # Get quality status
            quality_agent = self.ai_coordinator.get_agent('stream_quality')
            if quality_agent:
                quality_status = quality_agent.get_current_quality()
                platform_count = len(quality_status['platforms'])
                if platform_count > 0:
                    self.logger.info(f"AI Quality Monitor: Monitoring {platform_count} platforms")
            
        except Exception as e:
            self.logger.error(f"Error getting AI recommendations: {e}")
    
    async def monitor_stream_quality(self):
        """Monitor stream quality using AI during playback."""
        try:
            quality_agent = self.ai_coordinator.get_agent('stream_quality')
            if quality_agent:
                # Get current quality metrics
                quality_data = quality_agent.get_current_quality()
                
                # Check for any quality issues
                for platform, metrics in quality_data['platforms'].items():
                    if metrics['dropped_frames'] > 200:
                        self.logger.warning(f"AI Quality Alert: {platform} has {metrics['dropped_frames']} dropped frames")
                    
                    if metrics['network_latency'] > 500:
                        self.logger.warning(f"AI Quality Alert: {platform} high latency ({metrics['network_latency']}ms)")
                
        except Exception as e:
            self.logger.error(f"Error in AI quality monitoring: {e}")
    
    async def update_ai_performance_data(self, video, actual_duration):
        """Update AI agents with performance data after video playback."""
        try:
            # Simulate performance metrics
            engagement_score = 0.7 + (hash(video['id']) % 100) / 333  # Simulated engagement
            watch_time = actual_duration
            
            performance_data = {
                'video_id': video['id'],
                'engagement': engagement_score,
                'duration_watched': watch_time,
                'total_duration': video.get('duration', 300),
                'completion_rate': watch_time / max(video.get('duration', 300), 1)
            }
            
            # Send to content curation agent
            content_agent = self.ai_coordinator.get_agent('content_curation')
            if content_agent:
                # Use the message system to update performance
                from ai_agents.base_agent import AgentMessage
                from datetime import datetime
                
                message = AgentMessage(
                    sender="streaming_bot",
                    recipient="content_curation",
                    message_type="update_performance",
                    data=performance_data,
                    timestamp=datetime.now(),
                    priority=1
                )
                
                await content_agent.receive_message(message)
                
                self.logger.info(f"Updated AI performance data: engagement={engagement_score:.2f}")
            
        except Exception as e:
            self.logger.error(f"Error updating AI performance data: {e}")
    
    async def stop_streaming(self):
        """Stop streaming and cleanup."""
        self.running = False
        self.logger.info("Stopping AI-enhanced live streaming...")
        
        try:
            # Stop streaming
            await self.stream_manager.stop_streams()
            await self.obs_controller.disconnect()
            
            # Shutdown AI agents
            if self.ai_coordinator:
                await self.ai_coordinator.shutdown()
                self.logger.info("AI agents shutdown complete")
            
            self.logger.info("AI-enhanced live streaming stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping stream: {e}")
    
    def get_ai_status(self):
        """Get comprehensive AI status information."""
        if not self.ai_coordinator:
            return {"ai_enabled": False}
        
        status = self.ai_coordinator.get_agent_status()
        recommendations = self.ai_coordinator.get_recommendations(include_applied=True)
        
        return {
            "ai_enabled": True,
            "coordinator_status": status,
            "recommendations": recommendations,
            "agent_details": {
                name: agent.get_status() for name, agent in self.ai_coordinator.agents.items()
            }
        }

async def run_ai_enhanced_example():
    """Run the AI-enhanced streaming bot example."""
    
    print("🤖 AI-Enhanced Live Stream Bot Example")
    print("=" * 50)
    
    try:
        # Create AI-enhanced bot
        bot = AIEnhancedLiveStreamBot(enable_ai=True)
        
        # Start streaming
        await bot.start_ai_enhanced_streaming()
        
        # Show final AI status
        print("\n" + "=" * 50)
        print("🤖 Final AI Status Report")
        
        ai_status = bot.get_ai_status()
        if ai_status["ai_enabled"]:
            print(f"✓ AI Coordinator: {'Running' if ai_status['coordinator_status']['coordinator_running'] else 'Stopped'}")
            print(f"✓ Active Agents: {ai_status['coordinator_status']['agent_count']}")
            print(f"✓ Total Recommendations: {ai_status['coordinator_status']['active_recommendations']}")
            
            for agent_name, agent_status in ai_status['agent_details'].items():
                print(f"  - {agent_name}: {'✓' if agent_status['enabled'] else '✗'} "
                      f"({agent_status['recommendations_count']} recommendations)")
        else:
            print("✗ AI agents were disabled")
        
        print("\n🎯 AI Enhancement Benefits Demonstrated:")
        print("  • Content analysis and quality scoring")
        print("  • Intelligent playlist optimization") 
        print("  • Real-time stream quality monitoring")
        print("  • Automated performance tracking")
        print("  • Predictive issue detection")
        
    except Exception as e:
        print(f"❌ Error running AI-enhanced example: {e}")

def main():
    """Main entry point for the AI-enhanced example."""
    if not Path("config.json").exists():
        print("Config file not found. Please run 'python setup.py' first.")
        return
    
    print("\n🚀 Starting AI-Enhanced Live Stream Bot...")
    print("This example demonstrates how AI agents can enhance streaming:")
    print("  - Content Curation Agent: Optimizes video selection and ordering")
    print("  - Stream Quality Agent: Monitors and optimizes stream performance")
    print("  - AI Coordinator: Manages agent interactions and recommendations")
    print()
    
    asyncio.run(run_ai_enhanced_example())

if __name__ == "__main__":
    main()