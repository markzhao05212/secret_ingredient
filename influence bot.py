"""
Main influence bot implementation for the Capture the Narrative competition.
"""

import asyncio
import random
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from .base_bot import BaseBot
from ..intelligence.scanner import EnvironmentalScanner
from ..intelligence.strategy import StrategyEngine
from config.settings import settings

class InfluenceBot(BaseBot):
    """
    Specialized bot for influencing NPCs on the Legit Social platform.
    """
    
    def __init__(self, username: str, password: str, persona_name: str, 
                 campaign_objective: str = None, bot_id: str = None):
        """
        Initialize the influence bot.
        
        Args:
            username: Bot account username
            password: Bot account password
            persona_name: Persona configuration name
            campaign_objective: 'support_victor', 'support_marina', or 'voter_disillusionment'
            bot_id: Unique bot identifier
        """
        super().__init__(username, password, persona_name, bot_id)
        
        self.campaign_objective = campaign_objective or settings.get_campaign_objective()
        self.scanner = EnvironmentalScanner(self.api)
        self.strategy = StrategyEngine(self.campaign_objective, persona_name)
        
        # Influence-specific tracking
        self.influence_stats = {
            'npc_interactions': 0,
            'political_posts': 0,
            'neutral_posts': 0,
            'trending_engagements': 0,
            'strategic_replies': 0
        }
        
        # Target tracking
        self.engaged_npcs = set()  # NPCs we've interacted with
        self.followed_accounts = set()  # Accounts we're following
        self.monitored_hashtags = set()  # Hashtags we're tracking
        
        self.logger.info(f"Initialized InfluenceBot {username} with objective: {campaign_objective}")
    
    async def _activity_cycle(self):
        """
        Main activity cycle for the influence bot.
        """
        current_phase = self.get_current_phase()
        
        self.logger.debug(f"Starting activity cycle in {current_phase} phase")
        
        # Scan environment for opportunities
        opportunities = await self.scanner.scan_environment()
        
        # Update strategy based on current conditions
        self.strategy.update_context(opportunities)
        
        # Decide on action based on current phase and opportunities
        action = await self.strategy.get_next_action(current_phase, self.get_runtime_stats())
        
        # Execute the chosen action
        await self._execute_action(action)
        
        # Post-action analysis and learning
        await self._update_intelligence(action, opportunities)
    
    async def _execute_action(self, action: Dict):
        """
        Execute a strategic action.
        
        Args:
            action: Action dictionary from strategy engine
        """
        action_type = action.get('type', 'post')
        
        if action_type == 'post':
            await self._execute_post_action(action)
        elif action_type == 'engage':
            await self._execute_engagement_action(action)
        elif action_type == 'follow':
            await self._execute_follow_action(action)
        elif action_type == 'search_and_engage':
            await self._execute_search_and_engage_action(action)
        else:
            self.logger.warning(f"Unknown action type: {action_type}")
    
    async def _execute_post_action(self, action: Dict):
        """
        Execute a post creation action.
        
        Args:
            action: Action configuration
        """
        content_type = action.get('content_type', 'neutral')
        context = action.get('context', {})
        
        # Generate content based on current phase and objective
        content = await self.content_generator.generate_content(
            content_type=content_type,
            persona=self.persona_name,
            objective=self.campaign_objective,
            context=context
        )
        
        if content:
            response = await self.post_content(content)
            if response:
                # Track the type of content posted
                if content_type in ['political', 'campaign']:
                    self.influence_stats['political_posts'] += 1
                else:
                    self.influence_stats['neutral_posts'] += 1
                
                self.logger.info(f"Posted {content_type} content successfully")
            else:
                self.logger.error("Failed to post content")
        else:
            self.logger.error("Failed to generate content")
    
    async def _execute_engagement_action(self, action: Dict):
        """
        Execute an engagement action (like, reply, repost).
        
        Args:
            action: Action configuration
        """
        target_post = action.get('target_post')
        engagement_type = action.get('engagement_type', 'like')
        
        if not target_post:
            self.logger.warning("No target post for engagement action")
            return
        
        post_id = target_post.get('id')
        post_author = target_post.get('username', 'unknown')
        
        if engagement_type == 'like':
            success = await self.like_post(post_id)
            if success:
                self.logger.debug(f"Liked post by {post_author}")
        
        elif engagement_type == 'repost':
            success = await self.repost(post_id)
            if success:
                self.logger.debug(f"Reposted content from {post_author}")
        
        elif engagement_type == 'reply':
            reply_content = await self.content_generator.generate_reply(
                target_post=target_post,
                persona=self.persona_name,
                objective=self.campaign_objective
            )
            
            if reply_content:
                response = await self.post_content(reply_content, parent_id=post_id)
                if response:
                    self.influence_stats['strategic_replies'] += 1
                    self.logger.info(f"Replied to {post_author} strategically")
        
        # Track NPC interactions
        if post_author != self.username and '@' not in post_author:  # Assume NPCs don't have @ in names
            self.engaged_npcs.add(post_author)
            self.influence_stats['npc_interactions'] += 1
    
    async def _execute_follow_action(self, action: Dict):
        """
        Execute a follow action.
        
        Args:
            action: Action configuration
        """
        target_user = action.get('target_user')
        if target_user and target_user not in self.followed_accounts:
            success = await self.api.follow_user(target_user)
            if success:
                self.followed_accounts.add(target_user)
                self.logger.debug(f"Followed user: {target_user}")
    
    async def _execute_search_and_engage_action(self, action: Dict):
        """
        Execute a search and engage action.
        
        Args:
            action: Action configuration
        """
        search_query = action.get('query')
        engagement_limit = action.get('limit', 3)
        
        if search_query:
            posts = await self.search_posts(search_query, limit=engagement_limit * 2)
            
            engaged_count = 0
            for post in posts:
                if engaged_count >= engagement_limit:
                    break
                
                if self.should_engage_with_post(post):
                    # Randomly choose engagement type
                    engagement_types = ['like', 'reply']
                    if random.random() < 0.3:  # 30% chance to repost
                        engagement_types.append('repost')
                    
                    engagement_type = random.choice(engagement_types)
                    
                    await self._execute_engagement_action({
                        'target_post': post,
                        'engagement_type': engagement_type
                    })
                    
                    engaged_count += 1
                    
                    # Small delay between engagements
                    await asyncio.sleep(random.randint(5, 15))
            
            self.influence_stats['trending_engagements'] += engaged_count
    
    async def _update_intelligence(self, action: Dict, opportunities: Dict):
        """
        Update intelligence based on action results and opportunities.
        
        Args:
            action: The action that was executed
            opportunities: Current environmental opportunities
        """
        # Update strategy engine with results
        await self.strategy.update_from_action_results(action, opportunities)
        
        # Update scanner with new information
        self.scanner.update_tracking_data({
            'last_action': action,
            'engaged_npcs': list(self.engaged_npcs),
            'followed_accounts': list(self.followed_accounts)
        })
    
    async def handle_notifications(self):
        """
        Handle incoming notifications strategically.
        """
        notifications = await self.get_notifications()
        
        for notification in notifications:
            notification_type = notification.get('type')
            
            if notification_type == 'mention':
                await self._handle_mention(notification)
            elif notification_type == 'reply':
                await self._handle_reply(notification)
            elif notification_type == 'like':
                await self._handle_like_notification(notification)
            elif notification_type == 'follow':
                await self._handle_follow_notification(notification)
    
    async def _handle_mention(self, notification: Dict):
        """Handle being mentioned in a post."""
        post = notification.get('post')
        if post and self.should_engage_with_post(post):
            # Generate a strategic reply
            reply = await self.content_generator.generate_reply(
                target_post=post,
                persona=self.persona_name,
                objective=self.campaign_objective,
                is_mention_response=True
            )
            
            if reply:
                await self.post_content(reply, parent_id=post.get('id'))
    
    async def _handle_reply(self, notification: Dict):
        """Handle someone replying to our post."""
        reply_post = notification.get('post')
        if reply_post:
            # Consider engaging further if it's strategic
            if random.random() < 0.4:  # 40% chance to continue conversation
                counter_reply = await self.content_generator.generate_reply(
                    target_post=reply_post,
                    persona=self.persona_name,
                    objective=self.campaign_objective,
                    is_conversation_continuation=True
                )
                
                if counter_reply:
                    await self.post_content(counter_reply, parent_id=reply_post.get('id'))
    
    async def _handle_like_notification(self, notification: Dict):
        """Handle someone liking our post."""
        liker = notification.get('username')
        if liker and liker not in self.followed_accounts:
            # Consider following back if strategic
            if random.random() < 0.2:  # 20% chance to follow back
                await self.api.follow_user(liker)
                self.followed_accounts.add(liker)
    
    async def _handle_follow_notification(self, notification: Dict):
        """Handle someone following us."""
        follower = notification.get('username')
        if follower and follower not in self.followed_accounts:
            # Consider following back
            if random.random() < 0.6:  # 60% chance to follow back
                await self.api.follow_user(follower)
                self.followed_accounts.add(follower)
    
    def get_influence_stats(self) -> Dict:
        """Get detailed influence statistics."""
        base_stats = self.get_runtime_stats()
        base_stats.update({
            'campaign_objective': self.campaign_objective,
            'current_phase': self.get_current_phase(),
            'unique_npc_interactions': len(self.engaged_npcs),
            'accounts_followed': len(self.followed_accounts),
            **self.influence_stats
        })
        return base_stats
    
    def should_engage_with_post(self, post: Dict) -> bool:
        """
        Enhanced engagement decision making for influence bots.
        
        Args:
            post: Post dictionary
            
        Returns:
            bool: True if should engage
        """
        # Use parent class base logic first
        base_decision = super().should_engage_with_post(post)
        if not base_decision:
            return False
        
        # Additional strategic considerations
        post_content = post.get('content', '').lower()
        post_author = post.get('username', '')
        
        # Higher engagement with political content during political phase
        if self.get_current_phase() == 'political_influence':
            political_keywords = ['vote', 'election', 'candidate', 'policy', 'politics']
            if any(keyword in post_content for keyword in political_keywords):
                return True
        
        # Engage more with NPCs we haven't interacted with yet
        if post_author not in self.engaged_npcs and '@' not in post_author:
            return random.random() < 0.5  # 50% chance with new NPCs
        
        return base_decision