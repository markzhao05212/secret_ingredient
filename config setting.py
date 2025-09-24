"""
Configuration settings for the Capture the Narrative bot system.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseSettings, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class APISettings(BaseSettings):
    """API configuration settings."""
    
    # Legit Social Platform
    platform_url: str = Field(default="https://social.legitreal.com", env="PLATFORM_URL")
    api_base_url: str = Field(default="https://social.legitreal.com/api", env="API_BASE_URL")
    
    # LLM API
    llm_api_url: str = Field(default="https://llm-proxy.legitreal.com", env="LLM_API_URL")
    team_invitation_code: str = Field(..., env="TEAM_INVITATION_CODE")
    
    # External LLM APIs (optional)
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    
    # Rate limiting
    rate_limit_requests: int = Field(default=3, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW")  # seconds

class BotSettings(BaseSettings):
    """Bot configuration settings."""
    
    max_accounts: int = Field(default=40, env="MAX_ACCOUNTS")
    active_bots: int = Field(default=10, env="ACTIVE_BOTS")
    
    # Bot behavior
    posting_interval_min: int = Field(default=300, env="POSTING_INTERVAL_MIN")  # 5 minutes
    posting_interval_max: int = Field(default=1800, env="POSTING_INTERVAL_MAX")  # 30 minutes
    engagement_probability: float = Field(default=0.3, env="ENGAGEMENT_PROBABILITY")
    
    # Strategy phases
    audience_building_days: int = Field(default=2, env="AUDIENCE_BUILDING_DAYS")
    political_phase_start: int = Field(default=2, env="POLITICAL_PHASE_START")

class ContentSettings(BaseSettings):
    """Content generation settings."""
    
    max_post_length: int = Field(default=280, env="MAX_POST_LENGTH")
    use_gifs: bool = Field(default=True, env="USE_GIFS")
    gif_probability: float = Field(default=0.2, env="GIF_PROBABILITY")
    
    # Content mixing ratios during political phase
    political_content_ratio: float = Field(default=0.4, env="POLITICAL_CONTENT_RATIO")
    neutral_content_ratio: float = Field(default=0.6, env="NEUTRAL_CONTENT_RATIO")

class LoggingSettings(BaseSettings):
    """Logging configuration."""
    
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="data/logs/bot_system.log", env="LOG_FILE")
    max_log_size: int = Field(default=10485760, env="MAX_LOG_SIZE")  # 10MB
    backup_count: int = Field(default=5, env="BACKUP_COUNT")

class Settings:
    """Main settings class that combines all configuration."""
    
    def __init__(self):
        self.api = APISettings()
        self.bot = BotSettings()
        self.content = ContentSettings()
        self.logging = LoggingSettings()
        
        # Load additional configuration files
        self.config_dir = Path(__file__).parent
        self.personas = self._load_personas()
        self.content_templates = self._load_content_templates()
    
    def _load_personas(self) -> Dict:
        """Load persona configurations from JSON file."""
        personas_file = self.config_dir / "personas.json"
        if personas_file.exists():
            with open(personas_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _load_content_templates(self) -> Dict:
        """Load content templates from JSON file."""
        templates_file = self.config_dir / "content_templates.json"
        if templates_file.exists():
            with open(templates_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def get_campaign_objective(self) -> str:
        """Get the campaign objective from environment."""
        return os.getenv("CAMPAIGN_OBJECTIVE", "support_victor")  # support_victor, support_bina, voter_disillusionment
    
    def get_news_sources(self) -> List[str]:
        """Get list of news sources to monitor."""
        return [
            "https://kingston-herald.legitreal.com/",
            "https://daily-kingston.legitreal.com/"
        ]
    
    def get_candidate_websites(self) -> Dict[str, str]:
        """Get candidate website URLs."""
        return {
            "victor": "https://victor-for-president.legitreal.com/",
            "marina": "https://vote-marina.legitreal.com/"  # Note: docs show Marina, not Bina
        }

# Global settings instance
settings = Settings()