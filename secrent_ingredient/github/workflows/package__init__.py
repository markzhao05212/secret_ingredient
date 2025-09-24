# src/bot/__init__.py
"""Bot implementations and management."""

from .base_bot import BaseBot
from .influence_bot import InfluenceBot
from .bot_manager import BotManager

__all__ = ["BaseBot", "InfluenceBot", "BotManager"]

# src/content/__init__.py
"""Content generation and management."""

from .generator import ContentGenerator

__all__ = ["ContentGenerator"]

# src/intelligence/__init__.py
"""Intelligence and analysis modules."""

from .scanner import EnvironmentalScanner
from .strategy import StrategyEngine

__all__ = ["EnvironmentalScanner", "StrategyEngine"]

# src/api/__init__.py
"""API clients and interfaces."""

from .legit_social import LegitSocialAPI
from .llm_client import LLMClient

__all__ = ["LegitSocialAPI", "LLMClient"]

# src/utils/__init__.py
"""Utility functions and classes."""

from .rate_limiter import RateLimiter, BotActionLimiter
from .logger import get_logger, get_bot_logger, setup_logging
from .helpers import (
    sanitize_username, extract_hashtags, extract_mentions,
    truncate_text, clean_text, calculate_engagement_score,
    MemoryCache, CircularBuffer
)

__all__ = [
    "RateLimiter", "BotActionLimiter",
    "get_logger", "get_bot_logger", "setup_logging",
    "sanitize_username", "extract_hashtags", "extract_mentions",
    "truncate_text", "clean_text", "calculate_engagement_score",
    "MemoryCache", "CircularBuffer"
]

# tests/__init__.py
"""Test suite for the bot system."""

# Empty file to make tests directory a package