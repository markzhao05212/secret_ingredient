"""
Rate limiting utilities for API calls and bot actions.
"""

import asyncio
import time
from collections import deque
from datetime import datetime, timedelta
from typing import Optional, Union

class RateLimiter:
    """
    Async rate limiter that controls request frequency.
    """
    
    def __init__(self, max_requests: int, time_window: int):
        """
        Initialize the rate limiter.
        
        Args:
            max_requests: Maximum number of requests allowed
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
        self._lock = asyncio.Lock()
        
        # Burst handling
        self.burst_allowance = max(1, max_requests // 3)  # Allow small bursts
        self.burst_window = max(1, time_window // 6)  # Short burst window
    
    async def __aenter__(self):
        """Async context manager entry - wait if rate limited."""
        await self.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass
    
    async def acquire(self):
        """Wait until a request can be made."""
        async with self._lock:
            now = time.time()
            
            # Remove old requests outside the time window
            while self.requests and (now - self.requests[0]) > self.time_window:
                self.requests.popleft()
            
            # Check if we need to wait
            if len(self.requests) >= self.max_requests:
                # Calculate how long to wait
                oldest_request = self.requests[0]
                wait_time = self.time_window - (now - oldest_request)
                
                if wait_time > 0:
                    await asyncio.sleep(wait_time + 0.1)  # Small buffer
                    # Re-clean after waiting
                    now = time.time()
                    while self.requests and (now - self.requests[0]) > self.time_window:
                        self.requests.popleft()
            
            # Record this request
            self.requests.append(now)
    
    def can_make_request(self) -> bool:
        """
        Check if a request can be made without waiting.
        
        Returns:
            bool: True if request can be made immediately
        """
        now = time.time()
        
        # Remove old requests
        while self.requests and (now - self.requests[0]) > self.time_window:
            self.requests.popleft()
        
        return len(self.requests) < self.max_requests
    
    def can_make_burst(self, burst_size: int = None) -> bool:
        """
        Check if a burst of requests can be made.
        
        Args:
            burst_size: Size of the burst (default: self.burst_allowance)
            
        Returns:
            bool: True if burst can be made
        """
        if burst_size is None:
            burst_size = self.burst_allowance
        
        now = time.time()
        
        # Check burst window
        recent_requests = [req for req in self.requests if (now - req) <= self.burst_window]
        
        return len(recent_requests) + burst_size <= self.burst_allowance
    
    def requests_remaining(self) -> int:
        """
        Get number of requests remaining in current window.
        
        Returns:
            int: Number of requests that can be made
        """
        now = time.time()
        
        # Remove old requests
        while self.requests and (now - self.requests[0]) > self.time_window:
            self.requests.popleft()
        
        return max(0, self.max_requests - len(self.requests))
    
    def reset_time(self) -> Optional[datetime]:
        """
        Get the time when the rate limit will reset.
        
        Returns:
            datetime: When the oldest request will expire, or None if not rate limited
        """
        if not self.requests:
            return None
        
        oldest_request_time = self.requests[0]
        reset_time = oldest_request_time + self.time_window
        
        return datetime.fromtimestamp(reset_time)
    
    def is_rate_limited(self) -> bool:
        """
        Check if currently rate limited.
        
        Returns:
            bool: True if rate limited
        """
        return not self.can_make_request()
    
    def get_status(self) -> dict:
        """
        Get current rate limiter status.
        
        Returns:
            dict: Status information
        """
        now = time.time()
        
        # Clean old requests
        while self.requests and (now - self.requests[0]) > self.time_window:
            self.requests.popleft()
        
        return {
            'max_requests': self.max_requests,
            'time_window': self.time_window,
            'current_requests': len(self.requests),
            'requests_remaining': self.requests_remaining(),
            'is_rate_limited': self.is_rate_limited(),
            'reset_time': self.reset_time().isoformat() if self.reset_time() else None,
            'window_start': datetime.fromtimestamp(self.requests[0]).isoformat() if self.requests else None
        }


class AdaptiveRateLimiter(RateLimiter):
    """
    Rate limiter that adapts to server responses and rate limit headers.
    """
    
    def __init__(self, max_requests: int, time_window: int, adaptation_factor: float = 0.8):
        """
        Initialize adaptive rate limiter.
        
        Args:
            max_requests: Initial maximum requests
            time_window: Time window in seconds
            adaptation_factor: Factor to reduce limits when hitting rate limits (0.5-0.9)
        """
        super().__init__(max_requests, time_window)
        
        self.original_max_requests = max_requests
        self.adaptation_factor = max(0.1, min(1.0, adaptation_factor))
        self.consecutive_successes = 0
        self.consecutive_rate_limits = 0
        
        # Recovery settings
        self.recovery_threshold = 10  # Successful requests before trying to increase limit
        self.max_recovery_attempts = 3
        self.recovery_attempts = 0
    
    async def handle_rate_limit_response(self, status_code: int, headers: dict = None):
        """
        Handle a rate limit response and adapt accordingly.
        
        Args:
            status_code: HTTP status code
            headers: Response headers (may contain rate limit info)
        """
        async with self._lock:
            if status_code == 429:  # Rate limited
                self.consecutive_rate_limits += 1
                self.consecutive_successes = 0
                
                # Adapt rate limit downward
                if self.consecutive_rate_limits >= 2:
                    new_max = max(1, int(self.max_requests * self.adaptation_factor))
                    if new_max < self.max_requests:
                        self.max_requests = new_max
                        print(f"Reduced rate limit to {self.max_requests} requests per {self.time_window}s")
                
                # Parse rate limit headers if available
                if headers:
                    await self._parse_rate_limit_headers(headers)
                
            elif 200 <= status_code < 300:  # Success
                self.consecutive_successes += 1
                self.consecutive_rate_limits = 0
                
                # Try to recover rate limit after sustained success
                if (self.consecutive_successes >= self.recovery_threshold and
                    self.max_requests < self.original_max_requests and
                    self.recovery_attempts < self.max_recovery_attempts):
                    
                    self.max_requests = min(
                        self.original_max_requests,
                        int(self.max_requests * 1.2)  # Increase by 20%
                    )
                    self.consecutive_successes = 0
                    self.recovery_attempts += 1
                    print(f"Recovered rate limit to {self.max_requests} requests per {self.time_window}s")
    
    async def _parse_rate_limit_headers(self, headers: dict):
        """
        Parse standard rate limit headers and adjust accordingly.
        
        Args:
            headers: HTTP response headers
        """
        # Common rate limit header names
        limit_headers = ['x-ratelimit-limit', 'x-rate-limit-limit', 'ratelimit-limit']
        remaining_headers = ['x-ratelimit-remaining', 'x-rate-limit-remaining', 'ratelimit-remaining']
        reset_headers = ['x-ratelimit-reset', 'x-rate-limit-reset', 'ratelimit-reset']
        
        # Find rate limit info
        limit = None
        remaining = None
        reset_time = None
        
        for header in limit_headers:
            if header in headers:
                try:
                    limit = int(headers[header])
                    break
                except (ValueError, TypeError):
                    continue
        
        for header in remaining_headers:
            if header in headers:
                try:
                    remaining = int(headers[header])
                    break
                except (ValueError, TypeError):
                    continue
        
        for header in reset_headers:
            if header in headers:
                try:
                    reset_time = int(headers[header])
                    break
                except (ValueError, TypeError):
                    continue
        
        # Adjust based on server-provided info
        if limit and limit < self.max_requests:
            self.max_requests = limit
            print(f"Adjusted rate limit to server limit: {limit}")
        
        if remaining is not None and remaining == 0 and reset_time:
            # We've hit the limit, wait until reset
            now = time.time()
            wait_time = reset_time - now
            if 0 < wait_time <= 3600:  # Don't wait more than 1 hour
                await asyncio.sleep(wait_time + 1)


class BotActionLimiter:
    """
    Specialized rate limiter for bot actions with different limits per action type.
    """
    
    def __init__(self):
        """Initialize bot action limiter with platform-specific limits."""
        # Platform limits (approximately 3 actions per 60 seconds with burst)
        self.limiters = {
            'post': RateLimiter(max_requests=2, time_window=60),
            'like': RateLimiter(max_requests=5, time_window=60),
            'repost': RateLimiter(max_requests=2, time_window=60),
            'follow': RateLimiter(max_requests=2, time_window=120),  # More conservative
            'search': RateLimiter(max_requests=10, time_window=60)
        }
        
        # Overall action limiter
        self.overall_limiter = AdaptiveRateLimiter(max_requests=8, time_window=60)
    
    async def acquire(self, action_type: str):
        """
        Acquire permission for a specific action type.
        
        Args:
            action_type: Type of action ('post', 'like', 'repost', 'follow', 'search')
        """
        # Wait for overall limit first
        await self.overall_limiter.acquire()
        
        # Then wait for specific action limit
        limiter = self.limiters.get(action_type)
        if limiter:
            await limiter.acquire()
    
    async def __aenter__(self):
        """Not directly usable as context manager - use acquire() instead."""
        raise NotImplementedError("Use acquire(action_type) instead")
    
    def can_perform_action(self, action_type: str) -> bool:
        """
        Check if an action can be performed immediately.
        
        Args:
            action_type: Type of action
            
        Returns:
            bool: True if action can be performed
        """
        if not self.overall_limiter.can_make_request():
            return False
        
        limiter = self.limiters.get(action_type)
        return limiter.can_make_request() if limiter else True
    
    async def handle_response(self, action_type: str, status_code: int, headers: dict = None):
        """
        Handle API response and adapt rate limits.
        
        Args:
            action_type: Type of action that was performed
            status_code: HTTP response status
            headers: Response headers
        """
        await self.overall_limiter.handle_rate_limit_response(status_code, headers)
        
        limiter = self.limiters.get(action_type)
        if limiter and isinstance(limiter, AdaptiveRateLimiter):
            await limiter.handle_rate_limit_response(status_code, headers)
    
    def get_status_report(self) -> dict:
        """
        Get comprehensive status report for all limiters.
        
        Returns:
            dict: Status report
        """
        report = {
            'overall': self.overall_limiter.get_status(),
            'by_action': {}
        }
        
        for action_type, limiter in self.limiters.items():
            report['by_action'][action_type] = limiter.get_status()
        
        return report