"""
General utility functions and helpers for the bot system.
"""

import re
import random
import hashlib
import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union, Callable
from pathlib import Path
from urllib.parse import urlparse

def sanitize_username(username: str) -> str:
    """
    Sanitize username for logging and display.
    
    Args:
        username: Original username
        
    Returns:
        str: Sanitized username
    """
    if not username:
        return "unknown_user"
    
    # Remove any potentially sensitive information
    sanitized = re.sub(r'[^\w\-_]', '_', username)
    
    # Truncate if too long
    if len(sanitized) > 20:
        sanitized = sanitized[:17] + "..."
    
    return sanitized

def extract_hashtags(text: str) -> List[str]:
    """
    Extract hashtags from text.
    
    Args:
        text: Text to extract hashtags from
        
    Returns:
        List of hashtags (without # symbol)
    """
    if not text:
        return []
    
    hashtag_pattern = r'#(\w+)'
    hashtags = re.findall(hashtag_pattern, text, re.IGNORECASE)
    
    return [tag.lower() for tag in hashtags]

def extract_mentions(text: str) -> List[str]:
    """
    Extract user mentions from text.
    
    Args:
        text: Text to extract mentions from
        
    Returns:
        List of mentioned usernames (without @ symbol)
    """
    if not text:
        return []
    
    mention_pattern = r'@(\w+)'
    mentions = re.findall(mention_pattern, text, re.IGNORECASE)
    
    return [mention.lower() for mention in mentions]

def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        str: Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def clean_text(text: str) -> str:
    """
    Clean and normalize text content.
    
    Args:
        text: Text to clean
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    cleaned = re.sub(r'\s+', ' ', text.strip())
    
    # Remove control characters
    cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', cleaned)
    
    # Normalize quotes
    cleaned = cleaned.replace('"', '"').replace('"', '"')
    cleaned = cleaned.replace(''', "'").replace(''', "'")
    
    return cleaned

def generate_random_delay(min_seconds: int = 1, max_seconds: int = 10) -> float:
    """
    Generate random delay for humanizing bot behavior.
    
    Args:
        min_seconds: Minimum delay
        max_seconds: Maximum delay
        
    Returns:
        float: Random delay in seconds
    """
    return random.uniform(min_seconds, max_seconds)

def weighted_choice(choices: List[tuple], random_state: Optional[int] = None) -> Any:
    """
    Make a weighted random choice.
    
    Args:
        choices: List of (item, weight) tuples
        random_state: Optional random seed
        
    Returns:
        Chosen item
    """
    if random_state is not None:
        random.seed(random_state)
    
    if not choices:
        return None
    
    total_weight = sum(weight for _, weight in choices)
    if total_weight <= 0:
        return random.choice([item for item, _ in choices])
    
    r = random.uniform(0, total_weight)
    current_weight = 0
    
    for item, weight in choices:
        current_weight += weight
        if r <= current_weight:
            return item
    
    return choices[-1][0]  # Fallback

def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two texts using simple word overlap.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        float: Similarity score between 0 and 1
    """
    if not text1 or not text2:
        return 0.0
    
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union)

def hash_content(content: str) -> str:
    """
    Generate hash for content deduplication.
    
    Args:
        content: Content to hash
        
    Returns:
        str: Content hash
    """
    if not content:
        return ""
    
    # Normalize content for hashing
    normalized = clean_text(content).lower()
    
    return hashlib.md5(normalized.encode('utf-8')).hexdigest()

def parse_time_string(time_str: str) -> Optional[datetime]:
    """
    Parse various time string formats.
    
    Args:
        time_str: Time string to parse
        
    Returns:
        datetime object or None if parsing fails
    """
    if not time_str:
        return None
    
    # Common formats to try
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%dT%H:%M:%S.%fZ',
        '%Y-%m-%d',
        '%m/%d/%Y %H:%M:%S',
        '%m/%d/%Y'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(time_str, fmt)
        except ValueError:
            continue
    
    return None

def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        str: Formatted duration
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f}h"
    else:
        days = seconds / 86400
        return f"{days:.1f}d"

def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    Safely parse JSON string with fallback.
    
    Args:
        json_str: JSON string to parse
        default: Default value if parsing fails
        
    Returns:
        Parsed JSON or default value
    """
    if not json_str:
        return default
    
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default

def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """
    Safely serialize object to JSON with fallback.
    
    Args:
        obj: Object to serialize
        default: Default value if serialization fails
        
    Returns:
        JSON string or default value
    """
    try:
        return json.dumps(obj, default=str, ensure_ascii=False)
    except (TypeError, ValueError):
        return default

def batch_items(items: List[Any], batch_size: int) -> List[List[Any]]:
    """
    Split items into batches of specified size.
    
    Args:
        items: Items to batch
        batch_size: Size of each batch
        
    Returns:
        List of batches
    """
    if batch_size <= 0:
        return [items] if items else []
    
    batches = []
    for i in range(0, len(items), batch_size):
        batches.append(items[i:i + batch_size])
    
    return batches

def retry_async(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator for retrying async functions.
    
    Args:
        max_attempts: Maximum retry attempts
        delay: Initial delay between attempts
        backoff: Delay multiplier for each attempt
    """
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        break
                    
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
            
            raise last_exception
        
        return wrapper
    return decorator

def validate_url(url: str) -> bool:
    """
    Validate if a string is a valid URL.
    
    Args:
        url: URL to validate
        
    Returns:
        bool: True if valid URL
    """
    if not url:
        return False
    
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def extract_domain(url: str) -> Optional[str]:
    """
    Extract domain from URL.
    
    Args:
        url: URL to extract domain from
        
    Returns:
        str: Domain or None if invalid
    """
    if not url:
        return None
    
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except Exception:
        return None

def is_likely_npc(username: str) -> bool:
    """
    Heuristic to determine if username is likely an NPC.
    
    Args:
        username: Username to check
        
    Returns:
        bool: True if likely an NPC
    """
    if not username:
        return False
    
    # NPCs likely don't have @ symbols or special characters
    if '@' in username or '+' in username:
        return False
    
    # NPCs likely have human-sounding names
    if '_bot' in username.lower() or 'api' in username.lower():
        return False
    
    # NPCs likely don't have very long usernames
    if len(username) > 25:
        return False
    
    return True

def calculate_engagement_score(likes: int, replies: int, reposts: int, 
                              age_hours: float = 1.0) -> float:
    """
    Calculate engagement score for content.
    
    Args:
        likes: Number of likes
        replies: Number of replies
        reposts: Number of reposts
        age_hours: Age of content in hours
        
    Returns:
        float: Engagement score
    """
    # Weight different types of engagement
    weighted_engagement = (likes * 1.0) + (replies * 2.0) + (reposts * 1.5)
    
    # Adjust for age (newer content gets higher scores)
    age_factor = 1.0 / max(0.1, age_hours)
    
    return weighted_engagement * age_factor

def normalize_score(score: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """
    Normalize score to specified range.
    
    Args:
        score: Score to normalize
        min_val: Minimum value in range
        max_val: Maximum value in range
        
    Returns:
        float: Normalized score
    """
    if score < min_val:
        return min_val
    elif score > max_val:
        return max_val
    else:
        return score

def get_time_of_day_category(dt: datetime) -> str:
    """
    Categorize time of day.
    
    Args:
        dt: Datetime object
        
    Returns:
        str: Time category
    """
    hour = dt.hour
    
    if 6 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 21:
        return "evening"
    else:
        return "night"

def is_business_hours(dt: datetime) -> bool:
    """
    Check if datetime falls within business hours.
    
    Args:
        dt: Datetime to check
        
    Returns:
        bool: True if business hours
    """
    # Monday = 0, Sunday = 6
    if dt.weekday() >= 5:  # Weekend
        return False
    
    hour = dt.hour
    return 9 <= hour < 17  # 9 AM to 5 PM

def generate_unique_id(prefix: str = "", length: int = 8) -> str:
    """
    Generate unique identifier.
    
    Args:
        prefix: Optional prefix
        length: Length of random part
        
    Returns:
        str: Unique identifier
    """
    import uuid
    
    unique_part = str(uuid.uuid4()).replace('-', '')[:length]
    
    if prefix:
        return f"{prefix}_{unique_part}"
    
    return unique_part

class MemoryCache:
    """Simple in-memory cache with expiration."""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self.cache: Dict[str, Dict] = {}
        self.default_ttl = default_ttl
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set cache value."""
        expiry_time = datetime.now() + timedelta(seconds=ttl or self.default_ttl)
        self.cache[key] = {
            'value': value,
            'expires_at': expiry_time
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get cache value."""
        if key not in self.cache:
            return default
        
        entry = self.cache[key]
        
        if datetime.now() > entry['expires_at']:
            del self.cache[key]
            return default
        
        return entry['value']
    
    def delete(self, key: str) -> None:
        """Delete cache entry."""
        self.cache.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count removed."""
        now = datetime.now()
        expired_keys = [
            key for key, entry in self.cache.items()
            if now > entry['expires_at']
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        return len(expired_keys)

class CircularBuffer:
    """Fixed-size circular buffer for storing recent items."""
    
    def __init__(self, max_size: int):
        self.max_size = max_size
        self.buffer: List[Any] = []
        self.index = 0
    
    def add(self, item: Any) -> None:
        """Add item to buffer."""
        if len(self.buffer) < self.max_size:
            self.buffer.append(item)
        else:
            self.buffer[self.index] = item
            self.index = (self.index + 1) % self.max_size
    
    def get_all(self) -> List[Any]:
        """Get all items in chronological order."""
        if len(self.buffer) < self.max_size:
            return self.buffer[:]
        
        return self.buffer[self.index:] + self.buffer[:self.index]
    
    def get_recent(self, count: int) -> List[Any]:
        """Get most recent items."""
        all_items = self.get_all()
        return all_items[-count:] if count > 0 else []
    
    def clear(self) -> None:
        """Clear buffer."""
        self.buffer.clear()
        self.index = 0
    
    def size(self) -> int:
        """Get current buffer size."""
        return len(self.buffer)
    
    def is_full(self) -> bool:
        """Check if buffer is full."""
        return len(self.buffer) >= self.max_size