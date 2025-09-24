"""
Strategic decision-making engine for bot actions based on environmental intelligence.
"""

import random
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import deque, defaultdict

from ..utils.logger import get_logger
from config.settings import settings

class StrategyEngine:
    """
    Makes strategic decisions about bot actions based on campaign objectives and environmental data.
    """
    
    def __init__(self, campaign_objective: str, persona_name: str):
        """
        Initialize the strategy engine.
        
        Args:
            campaign_objective: 'support_victor', 'support_marina', or 'voter_disillusionment'
            persona_name: Bot persona name for context-aware decisions
        """
        self.campaign_objective = campaign_objective
        self.persona_name = persona_name
        self.logger = get_logger(f"strategy.{persona_name}")
        
        # Strategy state
        self.current_context = {}
        self.recent_actions = deque(maxlen=20)
        self.coordination_objectives = []
        self.performance_metrics = defaultdict(int)
        
        # Strategy parameters
        self.strategy_weights = self._initialize_strategy_weights()
        self.action_cooldowns = defaultdict(lambda: datetime.min)
        
        # Content strategy based on persona and objective
        self.persona_config = settings.personas.get('personas', {}).get(persona_name, {})
        self.content_strategy = self._build_content_strategy()
        
        self.logger.info(f"Strategy engine initialized for {persona_name} with objective: {campaign_objective}")
    
    def _initialize_strategy_weights(self) -> Dict[str, float]:
        """Initialize strategy weights based on campaign objective."""
        base_weights = {
            'post_creation': 0.4,
            'engagement': 0.3,
            'trending_participation': 0.2,
            'npc_targeting': 0.1
        }
        
        # Adjust weights based on objective
        if self.campaign_objective == 'support_victor':
            base_weights['post_creation'] = 0.5  # More content creation
            base_weights['engagement'] = 0.3
        elif self.campaign_objective == 'support_marina':
            base_weights['post_creation'] = 0.4
            base_weights['engagement'] = 0.4  # More engagement
        elif self.campaign_objective == 'voter_disillusionment':
            base_weights['engagement'] = 0.5  # More reactive engagement
            base_weights['post_creation'] = 0.3
        
        return base_weights
    
    def _build_content_strategy(self) -> Dict:
        """Build content strategy based on persona and objective."""
        strategy = {
            'audience_building_ratio': 0.8,  # Non-political content during audience building
            'political_ratio': 0.4,  # Political content during political phase
            'preferred_content_types': [],
            'engagement_style': 'moderate',
            'posting_times': 'varied'
        }
        
        # Persona-specific adjustments
        persona_interests = self.persona_config.get('interests', [])
        strategy['preferred_content_types'] = persona_interests
        
        persona_tone = self.persona_config.get('tone', '')
        if 'aggressive' in persona_tone.lower():
            strategy['engagement_style'] = 'aggressive'
        elif 'passive' in persona_tone.lower():
            strategy['engagement_style'] = 'passive'
        
        return strategy
    
    async def get_next_action(self, current_phase: str, bot_stats: Dict) -> Dict:
        """
        Determine the next strategic action for the bot.
        
        Args:
            current_phase: 'audience_building' or 'political_influence'
            bot_stats: Current bot performance statistics
            
        Returns:
            Dict: Action configuration
        """
        self.logger.debug(f"Determining next action for {current_phase} phase")
        
        # Update performance metrics
        self._update_performance_metrics(bot_stats)
        
        # Consider coordination objectives first
        coordination_action = self._check_coordination_objectives()
        if coordination_action:
            self.logger.debug("Executing coordination objective")
            return coordination_action
        
        # Phase-specific strategy
        if current_phase == 'audience_building':
            action = await self._get_audience_building_action()
        else:
            action = await self._get_political_influence_action()
        
        # Record action for learning
        self.recent_actions.append({
            'action': action,
            'timestamp': datetime.now(),
            'phase': current_phase,
            'context': self.current_context.copy()
        })
        
        return action
    
    async def _get_audience_building_action(self) -> Dict:
        """Get action for audience building phase."""
        # During audience building, focus on establishing persona and gaining followers
        
        # Weighted random selection based on strategy
        action_options = [
            ('post_personal', self.strategy_weights['post_creation'] * 1.2),
            ('engage_trending', self.strategy_weights['trending_participation'] * 1.5),
            ('community_engagement', self.strategy_weights['engagement'] * 1.1)
        ]
        
        action_type = self._weighted_random_choice(action_options)
        
        if action_type == 'post_personal':
            return {
                'type': 'post',
                'content_type': 'audience_building',
                'context': {
                    'focus': 'personal_story',
                    'interests': self.persona_config.get('interests', [])[:3],
                    'tone': self.persona_config.get('tone', 'casual')
                }
            }
        
        elif action_type == 'engage_trending':
            return {
                'type': 'search_and_engage',
                'query': self._get_trending_query(),
                'limit': 2,
                'engagement_types': ['like', 'reply']
            }
        
        else:  # community_engagement
            return {
                'type': 'search_and_engage',
                'query': self._get_community_query(),
                'limit': 3,
                'engagement_types': ['like', 'reply']
            }
    
    async def _get_political_influence_action(self) -> Dict:
        """Get action for political influence phase."""
        # During political phase, balance political content with maintaining audience
        
        # Check if we should post political content
        recent_political_posts = sum(1 for action in self.recent_actions 
                                   if action['action'].get('content_type') == 'political')
        
        recent_neutral_posts = sum(1 for action in self.recent_actions 
                                 if action['action'].get('content_type') in ['neutral', 'audience_building'])
        
        total_recent_posts = len([a for a in self.recent_actions if a['action'].get('type') == 'post'])
        
        # Calculate current political ratio
        current_political_ratio = recent_political_posts / max(1, total_recent_posts)
        target_political_ratio = self.content_strategy['political_ratio']
        
        if current_political_ratio < target_political_ratio:
            # Need more political content
            return self._get_political_content_action()
        else:
            # Balance with neutral content or engagement
            action_options = [
                ('post_neutral', 0.4),
                ('political_engagement', 0.3),
                ('npc_targeting', 0.2),
                ('trending_political', 0.1)
            ]
            
            action_type = self._weighted_random_choice(action_options)
            
            if action_type == 'post_neutral':
                return {
                    'type': 'post',
                    'content_type': 'neutral',
                    'context': self._get_neutral_context()
                }
            elif action_type == 'political_engagement':
                return {
                    'type': 'search_and_engage',
                    'query': self._get_political_query(),
                    'limit': 2,
                    'engagement_types': ['reply', 'like']
                }
            elif action_type == 'npc_targeting':
                return self._get_npc_targeting_action()
            else:  # trending_political
                return {
                    'type': 'search_and_engage',
                    'query': self._get_trending_political_query(),
                    'limit': 1,
                    'engagement_types': ['reply']
                }
    
    def _get_political_content_action(self) -> Dict:
        """Get political content creation action."""
        political_context = {
            'objective': self.campaign_objective,
            'persona_approach': self.persona_config.get('political_leanings', {}).get(self.campaign_objective, ''),
            'current_issues': self._get_relevant_issues()
        }
        
        # Add current context from environmental scan
        if 'political_sentiment' in self.current_context:
            political_context['sentiment_context'] = self.current_context['political_sentiment']
        
        if 'trending_topics' in self.current_context:
            political_context['trending_topics'] = self.current_context['trending_topics'][:3]
        
        return {
            'type': 'post',
            'content_type': 'political',
            'context': political_context
        }
    
    def _get_npc_targeting_action(self) -> Dict:
        """Get NPC targeting action."""
        # Look for NPCs we haven't engaged with recently
        npc_activity = self.current_context.get('npc_activity', {})
        active_npcs = npc_activity.get('active_npcs', [])
        
        if active_npcs:
            target_npc = random.choice(active_npcs)
            return {
                'type': 'search_and_engage',
                'query': f'from:{target_npc}',  # Search for posts from specific user
                'limit': 1,
                'engagement_types': ['reply', 'like']
            }
        
        # Fallback to general engagement
        return {
            'type': 'search_and_engage',
            'query': self._get_community_query(),
            'limit': 2,
            'engagement_types': ['like']
        }
    
    def _get_trending_query(self) -> str:
        """Get query for trending topic engagement."""
        trending_topics = self.current_context.get('trending_topics', [])
        
        if trending_topics:
            # Choose trending topic that matches persona interests
            persona_interests = self.persona_config.get('interests', [])
            
            for topic in trending_topics:
                for interest in persona_interests:
                    if interest.lower() in topic.lower():
                        return topic
            
            # If no match, use first trending topic
            return trending_topics[0]
        
        # Fallback to persona interests
        interests = self.persona_config.get('interests', ['community', 'local'])
        return random.choice(interests)
    
    def _get_political_query(self) -> str:
        """Get query for political engagement."""
        if self.campaign_objective == 'support_victor':
            queries = ['victor hawthorne', 'economy', 'business', 'jobs']
        elif self.campaign_objective == 'support_marina':
            queries = ['marina', 'progressive', 'climate', 'healthcare']
        else:  # voter_disillusionment
            queries = ['politics', 'election', 'disappointed', 'system']
        
        return random.choice(queries)
    
    def _get_community_query(self) -> str:
        """Get query for community engagement."""
        community_terms = ['kingston', 'local', 'community', 'downtown']
        persona_interests = self.persona_config.get('interests', [])
        
        # Mix community terms with persona interests
        all_terms = community_terms + persona_interests[:3]
        return random.choice(all_terms)
    
    def _get_trending_political_query(self) -> str:
        """Get query combining trending topics with political content."""
        trending = self.current_context.get('trending_topics', [])
        political_terms = ['vote', 'election', 'candidate', 'policy']
        
        if trending:
            # Try to combine trending topic with political term
            topic = trending[0]
            political_term = random.choice(political_terms)
            return f"{topic} {political_term}"
        
        return random.choice(political_terms)
    
    def _get_neutral_context(self) -> Dict:
        """Get context for neutral content."""
        return {
            'focus': 'community',
            'interests': self.persona_config.get('interests', [])[:2],
            'tone': 'friendly',
            'avoid_politics': True
        }
    
    def _get_relevant_issues(self) -> List[str]:
        """Get relevant political issues based on persona and objective."""
        all_issues = ['economy', 'healthcare', 'education', 'environment', 'jobs', 'housing']
        
        # Filter based on persona interests
        persona_interests = self.persona_config.get('interests', [])
        relevant_issues = []
        
        for issue in all_issues:
            if any(interest in issue or issue in interest for interest in persona_interests):
                relevant_issues.append(issue)
        
        # Add objective-specific issues
        if self.campaign_objective == 'support_victor':
            relevant_issues.extend(['economy', 'jobs', 'business'])
        elif self.campaign_objective == 'support_marina':
            relevant_issues.extend(['environment', 'healthcare', 'education'])
        
        return list(set(relevant_issues))[:3]  # Top 3 unique issues
    
    def _weighted_random_choice(self, options: List[Tuple[str, float]]) -> str:
        """Make weighted random choice from options."""
        total_weight = sum(weight for _, weight in options)
        if total_weight == 0:
            return options[0][0]
        
        r = random.uniform(0, total_weight)
        current_weight = 0
        
        for option, weight in options:
            current_weight += weight
            if r <= current_weight:
                return option
        
        return options[-1][0]
    
    def _check_coordination_objectives(self) -> Optional[Dict]:
        """Check if there are coordination objectives to execute."""
        if not self.coordination_objectives:
            return None
        
        # Get highest priority objective
        objective = max(self.coordination_objectives, 
                       key=lambda x: self._get_priority_score(x.get('priority', 'low')))
        
        # Check if we can execute this objective
        if self._can_execute_objective(objective):
            self.coordination_objectives.remove(objective)
            return self._convert_objective_to_action(objective)
        
        return None
    
    def _get_priority_score(self, priority: str) -> int:
        """Convert priority string to numeric score."""
        scores = {'low': 1, 'medium': 2, 'high': 3, 'urgent': 4}
        return scores.get(priority.lower(), 1)
    
    def _can_execute_objective(self, objective: Dict) -> bool:
        """Check if we can execute a coordination objective."""
        # Check cooldowns
        obj_type = objective.get('type', '')
        if self.action_cooldowns[obj_type] > datetime.now():
            return False
        
        # Check if we have required context
        if obj_type == 'amplify_trending':
            return bool(self.current_context.get('trending_topics'))
        
        return True
    
    def _convert_objective_to_action(self, objective: Dict) -> Dict:
        """Convert coordination objective to executable action."""
        obj_type = objective.get('type', '')
        
        if obj_type == 'amplify_trending':
            targets = objective.get('targets', [])
            return {
                'type': 'post',
                'content_type': 'trending_engagement',
                'context': {
                    'trending_topic': random.choice(targets) if targets else None,
                    'coordination': True
                }
            }
        
        elif obj_type == 'coordinated_npc_engagement':
            targets = objective.get('targets', [])
            return {
                'type': 'search_and_engage',
                'query': random.choice(targets) if targets else 'community',
                'limit': 2,
                'engagement_types': ['reply', 'like']
            }
        
        elif obj_type == 'campaign_push':
            return {
                'type': 'post',
                'content_type': 'political',
                'context': {
                    'objective': objective.get('objective', self.campaign_objective),
                    'coordination': True,
                    'intensity': 'high'
                }
            }
        
        # Default fallback
        return {
            'type': 'post',
            'content_type': 'neutral',
            'context': {'coordination': True}
        }
    
    def _update_performance_metrics(self, bot_stats: Dict):
        """Update performance metrics for strategy adjustment."""
        current_metrics = {
            'posts_created': bot_stats.get('posts_created', 0),
            'engagements': bot_stats.get('likes_given', 0) + bot_stats.get('reposts_made', 0),
            'npc_interactions': bot_stats.get('npc_interactions', 0),
            'political_posts': bot_stats.get('political_posts', 0)
        }
        
        # Calculate rates and adjust strategy weights if needed
        total_posts = max(1, current_metrics['posts_created'])
        political_ratio = current_metrics['political_posts'] / total_posts
        
        # Adjust strategy if political ratio is off target
        target_ratio = self.content_strategy.get('political_ratio', 0.4)
        if abs(political_ratio - target_ratio) > 0.2:  # 20% deviation
            if political_ratio < target_ratio:
                self.strategy_weights['post_creation'] *= 1.1
            else:
                self.strategy_weights['engagement'] *= 1.1
    
    async def add_coordination_objective(self, objective: Dict):
        """Add a coordination objective from the team manager."""
        self.coordination_objectives.append(objective)
        self.logger.debug(f"Added coordination objective: {objective.get('type', 'unknown')}")
    
    def update_context(self, environmental_intelligence: Dict):
        """Update strategy context with environmental intelligence."""
        self.current_context.update(environmental_intelligence)
        
        # Adjust strategy based on new intelligence
        self._adjust_strategy_from_intelligence(environmental_intelligence)
    
    def _adjust_strategy_from_intelligence(self, intelligence: Dict):
        """Adjust strategy weights based on environmental intelligence."""
        # Adjust based on political sentiment
        sentiment = intelligence.get('political_sentiment', {})
        
        if self.campaign_objective == 'support_victor':
            victor_support = sentiment.get('victor_support', 0)
            marina_support = sentiment.get('marina_support', 0)
            
            if marina_support > victor_support:
                # Marina is ahead, need more aggressive posting
                self.strategy_weights['post_creation'] *= 1.2
                self.strategy_weights['engagement'] *= 0.9
        
        elif self.campaign_objective == 'support_marina':
            victor_support = sentiment.get('victor_support', 0)
            marina_support = sentiment.get('marina_support', 0)
            
            if victor_support > marina_support:
                # Victor is ahead, need more aggressive posting
                self.strategy_weights['post_creation'] *= 1.2
        
        # Adjust based on trending opportunities
        trending_topics = intelligence.get('trending_topics', [])
        if len(trending_topics) > 3:
            # Many trending topics, increase trending participation
            self.strategy_weights['trending_participation'] *= 1.3
    
    async def update_from_action_results(self, action: Dict, environmental_data: Dict):
        """Update strategy based on action results and environmental feedback."""
        action_type = action.get('type', '')
        content_type = action.get('content_type', '')
        
        # Set cooldown for this action type
        self.action_cooldowns[action_type] = datetime.now() + timedelta(minutes=5)
        
        # Learn from action outcomes (this could be expanded with actual success metrics)
        self.performance_metrics[f"{action_type}_{content_type}"] += 1
        
        self.logger.debug(f"Updated strategy from action: {action_type} -> {content_type}")
    
    def get_strategy_status(self) -> Dict:
        """Get current strategy status for monitoring."""
        return {
            'campaign_objective': self.campaign_objective,
            'persona': self.persona_name,
            'strategy_weights': dict(self.strategy_weights),
            'recent_actions_count': len(self.recent_actions),
            'coordination_objectives_pending': len(self.coordination_objectives),
            'performance_metrics': dict(self.performance_metrics),
            'content_strategy': self.content_strategy
        }