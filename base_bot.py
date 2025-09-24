"""
Base bot class with core functionality for all bots in the system.
"""

import asyncio
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod

from ..utils.rate_limiter import RateLimiter
from ..utils.logger import get_logger
from ..api.legit_social import LegitSocialAPI
from ..content.generator import ContentGenerator
from config.settings import settings

class BaseBot(ABC):
    """
    Abstract base class for all bots with common functionality.
    """
    
    def __init__(self, 
                 username: str, 
                 password: str, 
                 persona_name: str,
                 bot_id: str = None):
        """
        Initialize the base bot.
        
        Args:
            username: Bot account username
            password: Bot account password  
            persona_name: Name of the persona from personas.json
            bot_id: Unique identifier for this bot instance
        """
        self.username = username
        self.password = password
        self.persona_name = persona_name
        self.bot_id = bot_id or f"{username}_{int(time.time())}"
        
        # Core components
        self.api = LegitSocialAPI()
        self.content_generator = ContentGenerator(persona_name)
        self.rate_limiter = RateLimiter(
            max_requests=settings.api.rate_limit_requests,
            time_window=settings.api.rate_limit_window
        )
        self.logger = get_logger(f"bot.{self.username}")
        
        # Bot state
        self.is_authenticated = False
        self.is_active = False
        self.last_action_time = 0
        self.action_count = 0
        self.start_time = datetime.now()
        
        # Performance tracking
        self.stats = {
            'posts_created': 0,
            'replies_made': 0,
            'likes_given': 0,
            'reposts_made': 0,
            'followers_gained': 0,
            'engagements_received': 0
        }
        
        # Get persona configuration
        self.persona_config = settings.personas.get('personas', {}).get(persona_name, {})
        if not self.persona_config:
            self.logger.warning(f"No persona configuration found for {persona_name}")
    
    async def authenticate(self) -> bool:
        """
        Authenticate with the Legit Social platform.
        
        Returns:
            bool: True if authentication successful
        """
        try:
            success = await self.api.login(self.username, self.password)
            if success:
                self.is_authenticated = True
                self.logger.info(f"Successfully authenticated as {self.username}")
                return True
            else:
                self.logger.error(f"Authentication failed for {self.username}")
                return False
        except Exception as e:
            self.logger.error(f"Authentication error for {self.username}: {e}")
            return False
    
    async def start(self):
        """Start the bot's main activity loop."""
        if not self.is_authenticated:
            if not await self.authenticate():
                raise Exception(f"Cannot start bot {self.username}: authentication failed")
        
        self.is_active = True
        self.logger.info(f"Bot {self.username} starting activity loop")
        
        try:
            while self.is_active:
                await self._activity_cycle()
                await self._wait_for_next_action()
        except Exception as e:
            self.logger.error(f"Bot {self.username} encountered error: {e}")
            self.is_active = False
    
    async def stop(self):
        """Stop the bot's activity."""
        self.is_active = False
        self.logger.info(f"Bot {self.username} stopped")
    
    @abstractmethod
    async def _activity_cycle(self):
        """
        Main activity cycle - to be implemented by subclasses.
        This method defines what the bot does in each activity cycle.
        """
        pass
    
    async def _wait_for_next_action(self):
        """Wait for the appropriate interval before the next action."""
        min_interval = settings.bot.posting_interval_min
        max_interval = settings.bot.posting_interval_max
        
        # Add some randomness to avoid detection
        wait_time = random.randint(min_interval, max_interval)
        
        # Add extra delay if we're hitting rate limits
        if self.rate_limiter.is_rate_limited():
            wait_time += 60  # Extra minute cooldown
        
        self.logger.debug(f"Waiting {wait_time} seconds until next action")
        await asyncio.sleep(wait_time)
    
    async def post_content(self, content: str, parent_id: Optional[str] = None) -> Optional[Dict]:
        """
        Post content to the platform.
        
        Args:
            content: Content to post
            parent_id: If provided, this will be a reply to that post
            
        Returns:
            Dict: Response from API if successful, None otherwise
        """
        async with self.rate_limiter:
            try:
                response = await self.api.post(content, parent_id=parent_id)
                if response:
                    if parent_id:
                        self.stats['replies_made'] += 1
                        self.logger.info(f"Replied to post {parent_id}")
                    else:
                        self.stats['posts_created'] += 1
                        self.logger.info(f"Created post: {content[:50]}...")
                    
                    self.action_count += 1
                    self.last_action_time = time.time()
                    return response
                else:
                    self.logger.error(f"Failed to post content")
                    return None
            except Exception as e:
                self.logger.error(f"Error posting content: {e}")
                return None
    
    async def like_post(self, post_id: str) -> bool:
        """
        Like a post.
        
        Args:
            post_id: ID of the post to like
            
        Returns:
            bool: True if successful
        """
        async with self.rate_limiter:
            try:
                success = await self.api.like(post_id)
                if success:
                    self.stats['likes_given'] += 1
                    self.action_count += 1
                    self.last_action_time = time.time()
                    self.logger.debug(f"Liked post {post_id}")
                return success
            except Exception as e:
                self.logger.error(f"Error liking post {post_id}: {e}")
                return False
    
    async def repost(self, post_id: str) -> bool:
        """
        Repost content.
        
        Args:
            post_id: ID of the post to repost
            
        Returns:
            bool: True if successful
        """
        async with self.rate_limiter:
            try:
                success = await self.api.repost(post_id)
                if success:
                    self.stats['reposts_made'] += 1
                    self.action_count += 1
                    self.last_action_time = time.time()
                    self.logger.debug(f"Reposted {post_id}")
                return success
            except Exception as e:
                self.logger.error(f"Error reposting {post_id}: {e}")
                return False
    
    async def get_trending_topics(self) -> List[str]:
        """
        Get current trending topics from the platform.
        
        Returns:
            List of trending topic strings
        """
        try:
            trending = await self.api.get_trending()
            return trending if trending else []
        except Exception as e:
            self.logger.error(f"Error getting trending topics: {e}")
            return []
    
    async def search_posts(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for posts matching a query.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of post dictionaries
        """
        try:
            results = await self.api.search(query, limit=limit)
            return results if results else []
        except Exception as e:
            self.logger.error(f"Error searching for '{query}': {e}")
            return []
    
    async def get_notifications(self) -> List[Dict]:
        """
        Get bot's notifications.
        
        Returns:
            List of notification dictionaries
        """
        try:
            notifications = await self.api.get_notifications()
            return notifications if notifications else []
        except Exception as e:
            self.logger.error(f"Error getting notifications: {e}")
            return []
    
    def get_runtime_stats(self) -> Dict:
        """Get runtime statistics for this bot."""
        runtime = datetime.now() - self.start_time
        
        return {
            'bot_id': self.bot_id,
            'username': self.username,
            'persona': self.persona_name,
            'runtime_minutes': int(runtime.total_seconds() / 60),
            'is_active': self.is_active,
            'action_count': self.action_count,
            'last_action_time': self.last_action_time,
            **self.stats
        }
    
    def should_engage_with_post(self, post: Dict) -> bool:
        """
        Determine if the bot should engage with a given post.
        
        Args:
            post: Post dictionary from API
            
        Returns:
            bool: True if bot should engage
        """
        # Base probability check
        if random.random() > settings.bot.engagement_probability:
            return False
        
        # Don't engage with own posts
        if post.get('username') == self.username:
            return False
        
        # Increase probability for posts matching persona interests
        post_content = post.get('content', '').lower()
        persona_interests = self.persona_config.get('interests', [])
        
        for interest in persona_interests:
            if interest.lower() in post_content:
                # Higher engagement probability for relevant content
                return random.random() < 0.6
        
        return True
    
    def get_current_phase(self) -> str:
        """
        Determine the current campaign phase based on runtime.
        
        Returns:
            str: 'audience_building' or 'political_influence'
        """
        runtime_days = (datetime.now() - self.start_time).days
        
        if runtime_days < settings.bot.audience_building_days:
            return 'audience_building'
        else:
            return 'political_influence'