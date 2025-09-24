"""
API wrapper for the Legit Social platform.
"""

import aiohttp
import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..utils.logger import get_logger
from config.settings import settings

class LegitSocialAPI:
    """
    Async API wrapper for interacting with the Legit Social platform.
    """
    
    def __init__(self):
        """Initialize the API client."""
        self.base_url = settings.api.platform_url
        self.api_url = settings.api.api_base_url
        self.session = None
        self.auth_token = None
        self.user_info = None
        
        self.logger = get_logger("legit_social_api")
        
        # API endpoints
        self.endpoints = {
            'login': '/auth/login',
            'logout': '/auth/logout',
            'post': '/posts',
            'like': '/posts/{post_id}/like',
            'unlike': '/posts/{post_id}/unlike',
            'repost': '/posts/{post_id}/repost',
            'unrepost': '/posts/{post_id}/unrepost',
            'reply': '/posts',
            'search': '/search',
            'trending': '/trending',
            'feed_home': '/feed/home',
            'feed_explore': '/feed/explore',
            'feed_latest': '/feed/latest',
            'notifications': '/notifications',
            'follow': '/users/{username}/follow',
            'unfollow': '/users/{username}/unfollow',
            'user_profile': '/users/{username}',
            'user_posts': '/users/{username}/posts'
        }
        
        # Request headers
        self.default_headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'LegitSocialBot/1.0'
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_session()
    
    async def _ensure_session(self):
        """Ensure we have an active session."""
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=self.default_headers
            )
    
    async def close_session(self):
        """Close the HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def login(self, username: str, password: str) -> bool:
        """
        Authenticate with the platform.
        
        Args:
            username: Account username
            password: Account password
            
        Returns:
            bool: True if login successful
        """
        await self._ensure_session()
        
        login_data = {
            'username': username,
            'password': password
        }
        
        try:
            url = f"{self.api_url}{self.endpoints['login']}"
            async with self.session.post(url, json=login_data) as response:
                
                if response.status == 200:
                    result = await response.json()
                    
                    # Extract authentication token
                    self.auth_token = result.get('token') or result.get('access_token')
                    self.user_info = result.get('user', {})
                    
                    if self.auth_token:
                        # Update session headers with auth token
                        self.session.headers.update({
                            'Authorization': f'Bearer {self.auth_token}'
                        })
                        
                        self.logger.info(f"Successfully logged in as {username}")
                        return True
                    else:
                        self.logger.error(f"No token in login response for {username}")
                        return False
                
                elif response.status == 401:
                    self.logger.error(f"Invalid credentials for {username}")
                    return False
                elif response.status == 429:
                    self.logger.warning(f"Rate limit hit during login for {username}")
                    return False
                else:
                    self.logger.error(f"Login failed for {username}: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Login request failed for {username}: {e}")
            return False
    
    async def post(self, content: str, parent_id: Optional[str] = None) -> Optional[Dict]:
        """
        Create a post or reply.
        
        Args:
            content: Post content
            parent_id: ID of parent post if this is a reply
            
        Returns:
            Dict: Post data if successful, None otherwise
        """
        if not self.auth_token:
            self.logger.error("Not authenticated - cannot post")
            return None
        
        post_data = {
            'content': content
        }
        
        if parent_id:
            post_data['parent_id'] = parent_id
        
        try:
            url = f"{self.api_url}{self.endpoints['post']}"
            async with self.session.post(url, json=post_data) as response:
                
                # Handle rate limiting
                if response.status == 429:
                    self.logger.warning("Rate limit hit on posting")
                    return None
                
                if response.status in [200, 201]:
                    result = await response.json()
                    post_type = "reply" if parent_id else "post"
                    self.logger.debug(f"Successfully created {post_type}: {content[:50]}...")
                    return result
                else:
                    self.logger.error(f"Post creation failed: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Post request failed: {e}")
            return None
    
    async def like(self, post_id: str) -> bool:
        """
        Like a post.
        
        Args:
            post_id: ID of the post to like
            
        Returns:
            bool: True if successful
        """
        return await self._post_action('like', post_id)
    
    async def unlike(self, post_id: str) -> bool:
        """
        Unlike a post.
        
        Args:
            post_id: ID of the post to unlike
            
        Returns:
            bool: True if successful
        """
        return await self._post_action('unlike', post_id)
    
    async def repost(self, post_id: str) -> bool:
        """
        Repost content.
        
        Args:
            post_id: ID of the post to repost
            
        Returns:
            bool: True if successful
        """
        return await self._post_action('repost', post_id)
    
    async def unrepost(self, post_id: str) -> bool:
        """
        Remove a repost.
        
        Args:
            post_id: ID of the post to unrepost
            
        Returns:
            bool: True if successful
        """
        return await self._post_action('unrepost', post_id)
    
    async def _post_action(self, action: str, post_id: str) -> bool:
        """
        Perform a post action (like, repost, etc.).
        
        Args:
            action: Action to perform
            post_id: Target post ID
            
        Returns:
            bool: True if successful
        """
        if not self.auth_token:
            self.logger.error(f"Not authenticated - cannot {action}")
            return False
        
        try:
            endpoint = self.endpoints[action].format(post_id=post_id)
            url = f"{self.api_url}{endpoint}"
            
            async with self.session.post(url) as response:
                if response.status == 429:
                    self.logger.warning(f"Rate limit hit on {action}")
                    return False
                
                if response.status in [200, 201, 204]:
                    self.logger.debug(f"Successfully {action}ed post {post_id}")
                    return True
                elif response.status == 409:
                    # Already performed this action
                    self.logger.debug(f"Action {action} already performed on {post_id}")
                    return True
                else:
                    self.logger.error(f"{action} failed: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"{action} request failed: {e}")
            return False
    
    async def search(self, query: str, limit: int = 20) -> Optional[List[Dict]]:
        """
        Search for posts.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of post dictionaries or None if failed
        """
        if not self.auth_token:
            self.logger.error("Not authenticated - cannot search")
            return None
        
        try:
            params = {
                'q': query,
                'limit': limit
            }
            
            url = f"{self.api_url}{self.endpoints['search']}"
            async with self.session.get(url, params=params) as response:
                
                if response.status == 200:
                    result = await response.json()
                    posts = result.get('posts', result) if isinstance(result, dict) else result
                    self.logger.debug(f"Search for '{query}' returned {len(posts)} results")
                    return posts
                else:
                    self.logger.error(f"Search failed: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Search request failed: {e}")
            return None
    
    async def get_trending(self) -> Optional[List[str]]:
        """
        Get trending topics.
        
        Returns:
            List of trending topic strings or None if failed
        """
        if not self.auth_token:
            return None
        
        try:
            url = f"{self.api_url}{self.endpoints['trending']}"
            async with self.session.get(url) as response:
                
                if response.status == 200:
                    result = await response.json()
                    # Handle different possible response formats
                    if isinstance(result, list):
                        trending = result
                    elif isinstance(result, dict) and 'trending' in result:
                        trending = result['trending']
                    elif isinstance(result, dict) and 'topics' in result:
                        trending = result['topics']
                    else:
                        trending = []
                    
                    # Extract just the topic names if they're objects
                    if trending and isinstance(trending[0], dict):
                        trending = [item.get('name', item.get('topic', str(item))) for item in trending]
                    
                    self.logger.debug(f"Retrieved {len(trending)} trending topics")
                    return trending
                else:
                    self.logger.error(f"Trending request failed: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Trending request failed: {e}")
            return None
    
    async def get_feed(self, feed_type: str = 'home', limit: int = 50) -> Optional[List[Dict]]:
        """
        Get feed posts.
        
        Args:
            feed_type: Type of feed ('home', 'explore', 'latest')
            limit: Maximum number of posts
            
        Returns:
            List of post dictionaries or None if failed
        """
        if not self.auth_token:
            return None
        
        feed_endpoint = f'feed_{feed_type}'
        if feed_endpoint not in self.endpoints:
            self.logger.error(f"Unknown feed type: {feed_type}")
            return None
        
        try:
            params = {'limit': limit}
            url = f"{self.api_url}{self.endpoints[feed_endpoint]}"
            
            async with self.session.get(url, params=params) as response:
                
                if response.status == 200:
                    result = await response.json()
                    posts = result.get('posts', result) if isinstance(result, dict) else result
                    self.logger.debug(f"Retrieved {len(posts)} posts from {feed_type} feed")
                    return posts
                else:
                    self.logger.error(f"Feed request failed: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Feed request failed: {e}")
            return None
    
    async def get_notifications(self) -> Optional[List[Dict]]:
        """
        Get user notifications.
        
        Returns:
            List of notification dictionaries or None if failed
        """
        if not self.auth_token:
            return None
        
        try:
            url = f"{self.api_url}{self.endpoints['notifications']}"
            async with self.session.get(url) as response:
                
                if response.status == 200:
                    result = await response.json()
                    notifications = result.get('notifications', result) if isinstance(result, dict) else result
                    self.logger.debug(f"Retrieved {len(notifications)} notifications")
                    return notifications
                else:
                    self.logger.error(f"Notifications request failed: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Notifications request failed: {e}")
            return None
    
    async def follow_user(self, username: str) -> bool:
        """
        Follow a user.
        
        Args:
            username: Username to follow
            
        Returns:
            bool: True if successful
        """
        return await self._user_action('follow', username)
    
    async def unfollow_user(self, username: str) -> bool:
        """
        Unfollow a user.
        
        Args:
            username: Username to unfollow
            
        Returns:
            bool: True if successful
        """
        return await self._user_action('unfollow', username)
    
    async def _user_action(self, action: str, username: str) -> bool:
        """
        Perform a user action (follow/unfollow).
        
        Args:
            action: Action to perform
            username: Target username
            
        Returns:
            bool: True if successful
        """
        if not self.auth_token:
            self.logger.error(f"Not authenticated - cannot {action}")
            return False
        
        try:
            endpoint = self.endpoints[action].format(username=username)
            url = f"{self.api_url}{endpoint}"
            
            async with self.session.post(url) as response:
                if response.status in [200, 201, 204]:
                    self.logger.debug(f"Successfully {action}ed {username}")
                    return True
                else:
                    self.logger.error(f"{action} failed: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"{action} request failed: {e}")
            return False
    
    async def get_user_profile(self, username: str) -> Optional[Dict]:
        """
        Get user profile information.
        
        Args:
            username: Username to look up
            
        Returns:
            Dict: User profile data or None if failed
        """
        if not self.auth_token:
            return None
        
        try:
            endpoint = self.endpoints['user_profile'].format(username=username)
            url = f"{self.api_url}{endpoint}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    result = await response.json()
                    self.logger.debug(f"Retrieved profile for {username}")
                    return result
                else:
                    self.logger.error(f"Profile request failed: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Profile request failed: {e}")
            return None
    
    async def get_user_posts(self, username: str, limit: int = 20) -> Optional[List[Dict]]:
        """
        Get posts by a specific user.
        
        Args:
            username: Username to get posts from
            limit: Maximum number of posts
            
        Returns:
            List of post dictionaries or None if failed
        """
        if not self.auth_token:
            return None
        
        try:
            endpoint = self.endpoints['user_posts'].format(username=username)
            params = {'limit': limit}
            url = f"{self.api_url}{endpoint}"
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    posts = result.get('posts', result) if isinstance(result, dict) else result
                    self.logger.debug(f"Retrieved {len(posts)} posts from {username}")
                    return posts
                else:
                    self.logger.error(f"User posts request failed: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"User posts request failed: {e}")
            return None
    
    def is_authenticated(self) -> bool:
        """Check if the client is authenticated."""
        return self.auth_token is not None
    
    def get_current_user(self) -> Optional[Dict]:
        """Get current user information."""
        return self.user_info
    
    async def logout(self) -> bool:
        """
        Logout and clear authentication.
        
        Returns:
            bool: True if successful
        """
        if not self.auth_token:
            return True
        
        try:
            url = f"{self.api_url}{self.endpoints['logout']}"
            async with self.session.post(url) as response:
                # Clear auth regardless of response
                self.auth_token = None
                self.user_info = None
                
                if 'Authorization' in self.session.headers:
                    del self.session.headers['Authorization']
                
                self.logger.info("Logged out successfully")
                return response.status in [200, 201, 204]
                
        except Exception as e:
            self.logger.error(f"Logout request failed: {e}")
            # Clear auth anyway
            self.auth_token = None
            self.user_info = None
            return False