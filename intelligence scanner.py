"""
Environmental scanner for gathering intelligence about the platform state.
"""

import asyncio
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict, Counter

from ..utils.logger import get_logger
from ..api.legit_social import LegitSocialAPI

class EnvironmentalScanner:
    """
    Scans the platform environment to gather intelligence for strategic decision making.
    """
    
    def __init__(self, api: LegitSocialAPI):
        """
        Initialize the environmental scanner.
        
        Args:
            api: Legit Social API client
        """
        self.api = api
        self.logger = get_logger("intelligence.scanner")
        
        # Intelligence data storage
        self.trending_topics = []
        self.influential_users = {}
        self.npc_profiles = {}
        self.content_patterns = defaultdict(list)
        self.engagement_patterns = {}
        self.political_sentiment = {'victor': 0, 'marina': 0, 'neutral': 0, 'negative': 0}
        
        # Tracking data
        self.last_scan_time = None
        self.scan_history = []
        self.max_history = 10
        
        # Keywords for analysis
        self.political_keywords = {
            'victor': ['victor', 'hawthorne', 'victor hawthorne', 'economic growth', 'business friendly'],
            'marina': ['marina', 'progressive', 'social justice', 'climate action'],
            'election': ['vote', 'election', 'candidate', 'campaign', 'ballot'],
            'issues': ['economy', 'healthcare', 'education', 'environment', 'jobs']
        }
        
        self.sentiment_keywords = {
            'positive': ['great', 'excellent', 'amazing', 'support', 'endorse', 'love', 'fantastic'],
            'negative': ['terrible', 'awful', 'hate', 'disappointed', 'against', 'oppose'],
            'neutral': ['consider', 'think', 'maybe', 'perhaps', 'discuss', 'analyze']
        }
    
    async def scan_environment(self) -> Dict:
        """
        Perform comprehensive environmental scan.
        
        Returns:
            Dict: Intelligence gathered from the scan
        """
        self.logger.debug("Starting environmental scan")
        scan_start = datetime.now()
        
        intelligence = {
            'timestamp': scan_start.isoformat(),
            'trending_topics': [],
            'influential_posts': [],
            'npc_activity': {},
            'political_sentiment': {},
            'engagement_opportunities': [],
            'content_gaps': [],
            'strategic_recommendations': []
        }
        
        try:
            # Parallel scanning tasks
            tasks = [
                self._scan_trending_topics(),
                self._scan_feed_content(),
                self._scan_political_sentiment(),
                self._scan_npc_activity(),
                self._identify_influential_content()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(f"Scan task {i} failed: {result}")
                    continue
                
                if i == 0 and result:  # Trending topics
                    intelligence['trending_topics'] = result
                    self.trending_topics = result
                elif i == 1 and result:  # Feed content
                    intelligence['feed_analysis'] = result
                elif i == 2 and result:  # Political sentiment
                    intelligence['political_sentiment'] = result
                    self.political_sentiment = result
                elif i == 3 and result:  # NPC activity
                    intelligence['npc_activity'] = result
                elif i == 4 and result:  # Influential content
                    intelligence['influential_posts'] = result
            
            # Analyze and generate strategic insights
            intelligence['engagement_opportunities'] = self._identify_engagement_opportunities(intelligence)
            intelligence['content_gaps'] = self._identify_content_gaps(intelligence)
            intelligence['strategic_recommendations'] = self._generate_strategic_recommendations(intelligence)
            
            # Store scan results
            self.last_scan_time = scan_start
            self.scan_history.append(intelligence)
            if len(self.scan_history) > self.max_history:
                self.scan_history.pop(0)
            
            scan_duration = (datetime.now() - scan_start).total_seconds()
            self.logger.info(f"Environmental scan completed in {scan_duration:.2f}s")
            
            return intelligence
            
        except Exception as e:
            self.logger.error(f"Environmental scan failed: {e}")
            return intelligence
    
    async def _scan_trending_topics(self) -> List[str]:
        """Scan for trending topics on the platform."""
        try:
            trending = await self.api.get_trending()
            if trending:
                self.logger.debug(f"Found {len(trending)} trending topics")
                return trending[:10]  # Top 10 topics
            return []
        except Exception as e:
            self.logger.error(f"Failed to scan trending topics: {e}")
            return []
    
    async def _scan_feed_content(self) -> Dict:
        """Scan feed content for patterns and insights."""
        feed_analysis = {
            'total_posts': 0,
            'political_posts': 0,
            'engagement_levels': {},
            'content_types': defaultdict(int),
            'active_discussions': []
        }
        
        try:
            # Scan multiple feed types
            feeds = ['explore', 'latest', 'home']
            all_posts = []
            
            for feed_type in feeds:
                posts = await self.api.get_feed(feed_type, limit=20)
                if posts:
                    all_posts.extend(posts)
            
            # Analyze posts
            for post in all_posts:
                feed_analysis['total_posts'] += 1
                
                content = post.get('content', '').lower()
                author = post.get('username', '')
                likes = post.get('likes', 0)
                replies = post.get('replies', 0)
                
                # Classify content type
                if self._is_political_content(content):
                    feed_analysis['political_posts'] += 1
                    feed_analysis['content_types']['political'] += 1
                elif any(keyword in content for keyword in ['#', 'trending', 'news']):
                    feed_analysis['content_types']['trending'] += 1
                else:
                    feed_analysis['content_types']['personal'] += 1
                
                # Track engagement
                total_engagement = likes + replies
                if total_engagement > 0:
                    feed_analysis['engagement_levels'][author] = total_engagement
                
                # Identify active discussions
                if replies > 3:
                    feed_analysis['active_discussions'].append({
                        'post_id': post.get('id'),
                        'author': author,
                        'replies': replies,
                        'content_preview': content[:100]
                    })
            
            return feed_analysis
            
        except Exception as e:
            self.logger.error(f"Failed to scan feed content: {e}")
            return feed_analysis
    
    async def _scan_political_sentiment(self) -> Dict:
        """Analyze political sentiment across the platform."""
        sentiment_data = {
            'victor_support': 0,
            'marina_support': 0,
            'voter_disillusionment': 0,
            'neutral_political': 0,
            'sample_posts': {'victor': [], 'marina': [], 'negative': []}
        }
        
        try:
            # Search for political content
            political_queries = ['vote', 'election', 'candidate', 'victor', 'marina']
            
            for query in political_queries:
                posts = await self.api.search(query, limit=10)
                if not posts:
                    continue
                
                for post in posts:
                    content = post.get('content', '').lower()
                    sentiment = self._analyze_post_sentiment(content)
                    
                    if sentiment['candidate'] == 'victor':
                        sentiment_data['victor_support'] += sentiment['strength']
                        if sentiment['strength'] > 0.5:
                            sentiment_data['sample_posts']['victor'].append(content[:100])
                    elif sentiment['candidate'] == 'marina':
                        sentiment_data['marina_support'] += sentiment['strength']
                        if sentiment['strength'] > 0.5:
                            sentiment_data['sample_posts']['marina'].append(content[:100])
                    elif sentiment['type'] == 'negative':
                        sentiment_data['voter_disillusionment'] += sentiment['strength']
                        if sentiment['strength'] > 0.5:
                            sentiment_data['sample_posts']['negative'].append(content[:100])
                    else:
                        sentiment_data['neutral_political'] += 1
                
                # Small delay between searches
                await asyncio.sleep(1)
            
            return sentiment_data
            
        except Exception as e:
            self.logger.error(f"Failed to scan political sentiment: {e}")
            return sentiment_data
    
    async def _scan_npc_activity(self) -> Dict:
        """Identify and analyze NPC behavior patterns."""
        npc_data = {
            'active_npcs': [],
            'npc_interests': {},
            'engagement_patterns': {},
            'influence_network': {}
        }
        
        try:
            # Get feed content to identify NPCs
            posts = await self.api.get_feed('explore', limit=30)
            if not posts:
                return npc_data
            
            # Analyze posting patterns to identify NPCs
            user_activity = defaultdict(list)
            
            for post in posts:
                username = post.get('username', '')
                if username and '@' not in username:  # Assume NPCs don't have @ symbols
                    user_activity[username].append(post)
            
            # Analyze each potential NPC
            for username, user_posts in user_activity.items():
                if len(user_posts) >= 2:  # Active users
                    npc_profile = self._analyze_npc_profile(username, user_posts)
                    if npc_profile:
                        npc_data['active_npcs'].append(username)
                        npc_data['npc_interests'][username] = npc_profile['interests']
                        npc_data['engagement_patterns'][username] = npc_profile['engagement']
            
            return npc_data
            
        except Exception as e:
            self.logger.error(f"Failed to scan NPC activity: {e}")
            return npc_data
    
    async def _identify_influential_content(self) -> List[Dict]:
        """Identify content with high engagement potential."""
        influential_posts = []
        
        try:
            feeds = ['explore', 'latest']
            
            for feed_type in feeds:
                posts = await self.api.get_feed(feed_type, limit=15)
                if not posts:
                    continue
                
                for post in posts:
                    likes = post.get('likes', 0)
                    replies = post.get('replies', 0)
                    total_engagement = likes + replies
                    
                    # Consider posts with significant engagement
                    if total_engagement >= 3:
                        influential_posts.append({
                            'id': post.get('id'),
                            'author': post.get('username', ''),
                            'content': post.get('content', '')[:200],
                            'likes': likes,
                            'replies': replies,
                            'total_engagement': total_engagement,
                            'is_political': self._is_political_content(post.get('content', ''))
                        })
            
            # Sort by engagement
            influential_posts.sort(key=lambda x: x['total_engagement'], reverse=True)
            return influential_posts[:10]
            
        except Exception as e:
            self.logger.error(f"Failed to identify influential content: {e}")
            return []
    
    def _is_political_content(self, content: str) -> bool:
        """Check if content is political in nature."""
        content_lower = content.lower()
        
        # Check for political keywords
        all_political_keywords = []
        for keyword_list in self.political_keywords.values():
            all_political_keywords.extend(keyword_list)
        
        return any(keyword in content_lower for keyword in all_political_keywords)
    
    def _analyze_post_sentiment(self, content: str) -> Dict:
        """Analyze sentiment of a post."""
        sentiment = {
            'candidate': None,
            'type': 'neutral',
            'strength': 0.0
        }
        
        content_lower = content.lower()
        
        # Check for candidate mentions
        victor_score = sum(1 for keyword in self.political_keywords['victor'] if keyword in content_lower)
        marina_score = sum(1 for keyword in self.political_keywords['marina'] if keyword in content_lower)
        
        # Determine sentiment type
        positive_score = sum(1 for keyword in self.sentiment_keywords['positive'] if keyword in content_lower)
        negative_score = sum(1 for keyword in self.sentiment_keywords['negative'] if keyword in content_lower)
        
        if victor_score > marina_score and positive_score > negative_score:
            sentiment['candidate'] = 'victor'
            sentiment['type'] = 'positive'
            sentiment['strength'] = min(1.0, (victor_score + positive_score) / 5)
        elif marina_score > victor_score and positive_score > negative_score:
            sentiment['candidate'] = 'marina'
            sentiment['type'] = 'positive'
            sentiment['strength'] = min(1.0, (marina_score + positive_score) / 5)
        elif negative_score > positive_score:
            sentiment['type'] = 'negative'
            sentiment['strength'] = min(1.0, negative_score / 3)
        
        return sentiment
    
    def _analyze_npc_profile(self, username: str, posts: List[Dict]) -> Optional[Dict]:
        """Analyze NPC profile from their posts."""
        if not posts:
            return None
        
        profile = {
            'interests': [],
            'engagement': {
                'avg_likes': 0,
                'avg_replies': 0,
                'posting_frequency': 0
            },
            'content_themes': [],
            'political_leaning': 'unknown'
        }
        
        # Analyze content themes
        all_content = ' '.join([post.get('content', '') for post in posts]).lower()
        
        # Extract interests based on keywords
        interest_keywords = {
            'technology': ['tech', 'ai', 'computer', 'software', 'innovation'],
            'politics': ['vote', 'election', 'government', 'policy'],
            'sports': ['game', 'team', 'player', 'score', 'match'],
            'local': ['kingston', 'community', 'local', 'downtown'],
            'business': ['work', 'job', 'career', 'company', 'economy']
        }
        
        for interest, keywords in interest_keywords.items():
            if any(keyword in all_content for keyword in keywords):
                profile['interests'].append(interest)
        
        # Calculate engagement metrics
        total_likes = sum(post.get('likes', 0) for post in posts)
        total_replies = sum(post.get('replies', 0) for post in posts)
        
        profile['engagement']['avg_likes'] = total_likes / len(posts)
        profile['engagement']['avg_replies'] = total_replies / len(posts)
        profile['engagement']['posting_frequency'] = len(posts)
        
        # Analyze political leaning
        political_sentiment = self._analyze_post_sentiment(all_content)
        if political_sentiment['candidate']:
            profile['political_leaning'] = political_sentiment['candidate']
        
        return profile
    
    def _identify_engagement_opportunities(self, intelligence: Dict) -> List[Dict]:
        """Identify opportunities for strategic engagement."""
        opportunities = []
        
        # Trending topic opportunities
        for topic in intelligence.get('trending_topics', [])[:3]:
            opportunities.append({
                'type': 'trending_engagement',
                'target': topic,
                'priority': 'high',
                'action': 'create_content',
                'reason': f'High visibility opportunity with trending topic: {topic}'
            })
        
        # Influential post engagement
        for post in intelligence.get('influential_posts', [])[:2]:
            if not post.get('is_political', False):  # Non-political posts are safer
                opportunities.append({
                    'type': 'post_engagement',
                    'target': post['id'],
                    'target_author': post['author'],
                    'priority': 'medium',
                    'action': 'reply_or_like',
                    'reason': f"High engagement post ({post['total_engagement']} interactions)"
                })
        
        # NPC engagement opportunities
        for npc in intelligence.get('npc_activity', {}).get('active_npcs', [])[:3]:
            opportunities.append({
                'type': 'npc_engagement',
                'target': npc,
                'priority': 'medium',
                'action': 'targeted_interaction',
                'reason': f'Active NPC with engagement potential'
            })
        
        return opportunities
    
    def _identify_content_gaps(self, intelligence: Dict) -> List[Dict]:
        """Identify content gaps and opportunities."""
        gaps = []
        
        feed_analysis = intelligence.get('feed_analysis', {})
        content_types = feed_analysis.get('content_types', {})
        
        # Check political content balance
        political_ratio = content_types.get('political', 0) / max(1, feed_analysis.get('total_posts', 1))
        
        if political_ratio < 0.2:  # Less than 20% political content
            gaps.append({
                'type': 'content_gap',
                'gap': 'low_political_content',
                'priority': 'medium',
                'recommendation': 'Increase political content production',
                'details': f'Only {political_ratio:.1%} of content is political'
            })
        
        # Check trending engagement
        if len(intelligence.get('trending_topics', [])) > 0 and content_types.get('trending', 0) < 3:
            gaps.append({
                'type': 'content_gap',
                'gap': 'missed_trending',
                'priority': 'high',
                'recommendation': 'Create content around trending topics',
                'details': 'Low engagement with trending topics'
            })
        
        return gaps
    
    def _generate_strategic_recommendations(self, intelligence: Dict) -> List[str]:
        """Generate strategic recommendations based on intelligence."""
        recommendations = []
        
        # Sentiment-based recommendations
        sentiment = intelligence.get('political_sentiment', {})
        victor_support = sentiment.get('victor_support', 0)
        marina_support = sentiment.get('marina_support', 0)
        
        if victor_support > marina_support:
            recommendations.append("Victor Hawthorne appears to have stronger support - consider targeted counter-messaging if supporting Marina")
        elif marina_support > victor_support:
            recommendations.append("Marina appears to have stronger support - consider amplifying Victor's message if supporting him")
        
        # Engagement recommendations
        opportunities = intelligence.get('engagement_opportunities', [])
        high_priority_ops = [op for op in opportunities if op.get('priority') == 'high']
        
        if high_priority_ops:
            recommendations.append(f"Focus on {len(high_priority_ops)} high-priority engagement opportunities")
        
        # Content strategy recommendations
        gaps = intelligence.get('content_gaps', [])
        if gaps:
            recommendations.append(f"Address {len(gaps)} identified content gaps for better reach")
        
        return recommendations
    
    def get_intelligence_summary(self) -> Dict:
        """Get a summary of current intelligence."""
        return {
            'last_scan': self.last_scan_time.isoformat() if self.last_scan_time else None,
            'trending_topics': self.trending_topics,
            'political_sentiment': self.political_sentiment,
            'npc_count': len(self.npc_profiles),
            'scan_history_count': len(self.scan_history)
        }
    
    def update_tracking_data(self, data: Dict):
        """Update tracking data from bot activities."""
        # This can be called by bots to update scanner's knowledge
        if 'engaged_npcs' in data:
            for npc in data['engaged_npcs']:
                if npc not in self.npc_profiles:
                    self.npc_profiles[npc] = {'last_interaction': datetime.now()}
        
        if 'trending_engagements' in data:
            # Track which trending topics we've engaged with
            pass