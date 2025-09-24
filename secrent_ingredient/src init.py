"""
Capture the Narrative Bot System

A sophisticated multi-bot influence system for social media platforms.
"""

__version__ = "1.0.0"
__author__ = "Capture the Narrative Team"
__description__ = "AI-powered social media influence bot system"

# Package imports for easier access
from .bot.influence_bot import InfluenceBot
from .bot.bot_manager import BotManager
from .content.generator import ContentGenerator
from .intelligence.scanner import EnvironmentalScanner
from .intelligence.strategy import StrategyEngine
from .api.legit_social import LegitSocialAPI
from .api.llm_client import LLMClient

# Utility imports
from .utils.rate_limiter import RateLimiter, BotActionLimiter
from .utils.logger import get_logger, get_bot_logger
from .utils.helpers import (
    sanitize_username,
    extract_hashtags,
    extract_mentions,
    truncate_text,
    clean_text,
    calculate_engagement_score
)

__all__ = [
    # Core classes
    "InfluenceBot",
    "BotManager", 
    "ContentGenerator",
    "EnvironmentalScanner",
    "StrategyEngine",
    
    # API clients
    "LegitSocialAPI",
    "LLMClient",
    
    # Utilities
    "RateLimiter",
    "BotActionLimiter",
    "get_logger",
    "get_bot_logger",
    
    # Helper functions
    "sanitize_username",
    "extract_hashtags",
    "extract_mentions", 
    "truncate_text",
    "clean_text",
    "calculate_engagement_score"
]