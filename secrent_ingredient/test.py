"""
Basic functionality tests for the bot system.
"""

import pytest
import asyncio
import json
from pathlib import Path
import sys
from unittest.mock import AsyncMock, MagicMock, patch

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config.settings import settings
from content.generator import ContentGenerator
from intelligence.scanner import EnvironmentalScanner
from utils.rate_limiter import RateLimiter
from api.llm_client import LLMClient


class TestConfiguration:
    """Test configuration loading and validation."""
    
    def test_settings_load(self):
        """Test that settings load correctly."""
        assert settings.api.platform_url
        assert settings.bot.active_bots > 0
        assert settings.content.max_post_length > 0
    
    def test_personas_load(self):
        """Test that personas are loaded."""
        personas = settings.personas.get('personas', {})
        assert len(personas) > 0
        
        # Check that each persona has required fields
        for persona_name, persona_config in personas.items():
            assert 'name' in persona_config
            assert 'description' in persona_config
            assert 'interests' in persona_config
            assert isinstance(persona_config['interests'], list)
    
    def test_content_templates_load(self):
        """Test that content templates are loaded."""
        templates = settings.content_templates.get('content_templates', {})
        assert 'audience_building' in templates
        assert 'political_content' in templates


class TestContentGenerator:
    """Test content generation functionality."""
    
    @pytest.fixture
    def generator(self):
        """Create a content generator for testing."""
        return ContentGenerator("young_professional")
    
    def test_generator_initialization(self, generator):
        """Test that generator initializes correctly."""
        assert generator.persona_name == "young_professional"
        assert generator.persona_config
        assert generator.content_templates
    
    @pytest.mark.asyncio
    async def test_template_content_generation(self, generator):
        """Test template-based content generation."""
        content = generator._generate_from_templates(
            content_type="audience_building",
            objective="support_victor",
            context={}
        )
        
        assert content is not None
        assert len(content) > 0
        assert len(content) <= settings.content.max_post_length
    
    def test_template_variable_filling(self, generator):
        """Test template variable substitution."""
        template = "I love {food_item} at {local_place} in Kingston!"
        filled = generator._fill_template_variables(template)
        
        assert '{food_item}' not in filled
        assert '{local_place}' not in filled
        assert 'kingston' in filled.lower()
    
    def test_content_appropriateness_check(self, generator):
        """Test content appropriateness filtering."""
        appropriate_content = "Great day in Kingston! Love this community."
        inappropriate_content = "I am an AI assistant"
        
        assert generator._is_content_appropriate(appropriate_content)
        assert not generator._is_content_appropriate(inappropriate_content)
    
    @pytest.mark.asyncio
    async def test_reply_generation(self, generator):
        """Test reply generation functionality."""
        target_post = {
            'content': 'What do you think about the election?',
            'username': 'test_user'
        }
        
        # Mock LLM client to avoid API calls in tests
        with patch.object(generator.llm_client, 'generate_content', return_value=None):
            reply = await generator.generate_reply(
                target_post=target_post,
                persona="young_professional",
                objective="support_victor"
            )
            
            # Should fall back to template replies
            assert reply is not None
            assert len(reply) > 0


class TestRateLimiter:
    """Test rate limiting functionality."""
    
    def test_rate_limiter_initialization(self):
        """Test rate limiter setup."""
        limiter = RateLimiter(max_requests=5, time_window=60)
        
        assert limiter.max_requests == 5
        assert limiter.time_window == 60
        assert limiter.can_make_request()
    
    @pytest.mark.asyncio
    async def test_rate_limiter_basic_functionality(self):
        """Test basic rate limiting."""
        limiter = RateLimiter(max_requests=2, time_window=1)
        
        # Should be able to make first two requests
        await limiter.acquire()
        await limiter.acquire()
        
        # Third request should be rate limited
        assert not limiter.can_make_request()
    
    def test_rate_limiter_status(self):
        """Test rate limiter status reporting."""
        limiter = RateLimiter(max_requests=5, time_window=60)
        
        status = limiter.get_status()
        assert 'max_requests' in status
        assert 'time_window' in status
        assert 'current_requests' in status
        assert 'requests_remaining' in status


class TestEnvironmentalScanner:
    """Test environmental scanning functionality."""
    
    @pytest.fixture
    def scanner(self):
        """Create a scanner with mocked API."""
        mock_api = AsyncMock()
        return EnvironmentalScanner(mock_api)
    
    def test_scanner_initialization(self, scanner):
        """Test scanner initialization."""
        assert scanner.api
        assert scanner.political_keywords
        assert scanner.sentiment_keywords
    
    def test_political_content_detection(self, scanner):
        """Test political content classification."""
        political_content = "I support Victor Hawthorne for president"
        non_political_content = "Great weather today in Kingston!"
        
        assert scanner._is_political_content(political_content)
        assert not scanner._is_political_content(non_political_content)
    
    def test_sentiment_analysis(self, scanner):
        """Test political sentiment analysis."""
        victor_support = "Victor Hawthorne has great economic policies"
        marina_support = "Marina's progressive agenda is exactly what we need"
        negative_content = "All politicians are terrible"
        
        victor_sentiment = scanner._analyze_post_sentiment(victor_support)
        marina_sentiment = scanner._analyze_post_sentiment(marina_support)
        negative_sentiment = scanner._analyze_post_sentiment(negative_content)
        
        assert victor_sentiment['candidate'] == 'victor'
        assert marina_sentiment['candidate'] == 'marina'
        assert negative_sentiment['type'] == 'negative'
    
    def test_npc_profile_analysis(self, scanner):
        """Test NPC profile creation."""
        posts = [
            {'content': 'Love working in tech here in Kingston', 'likes': 5, 'replies': 2},
            {'content': 'Another busy day at the office', 'likes': 3, 'replies': 1},
            {'content': 'Kingston has great opportunities for innovation', 'likes': 7, 'replies': 4}
        ]
        
        profile = scanner._analyze_npc_profile("tech_user", posts)
        
        assert profile is not None
        assert 'technology' in profile['interests']
        assert profile['engagement']['avg_likes'] > 0
        assert profile['engagement']['posting_frequency'] == 3


class TestLLMClient:
    """Test LLM client functionality."""
    
    @pytest.fixture
    def llm_client(self):
        """Create LLM client for testing."""
        return LLMClient()
    
    def test_llm_client_initialization(self, llm_client):
        """Test LLM client setup."""
        assert llm_client.api_priority
        assert 'competition' in llm_client.api_priority
        assert llm_client.stats
    
    def test_api_priority_determination(self, llm_client):
        """Test API priority ordering."""
        priority_list = list(llm_client.api_priority.keys())
        
        # Competition API should be first (free but limited)
        assert priority_list[0] == 'competition'
    
    @pytest.mark.asyncio
    async def test_api_status_reporting(self, llm_client):
        """Test API status reporting."""
        status = llm_client.get_api_status()
        
        assert 'available_apis' in status
        assert 'primary_api' in status
        assert 'stats' in status
        
        # Should have at least the competition API
        assert 'competition' in status['available_apis']


class TestIntegration:
    """Integration tests for component interaction."""
    
    @pytest.mark.asyncio
    async def test_content_generation_integration(self):
        """Test content generation with different personas and objectives."""
        personas = ['young_professional', 'concerned_parent', 'local_business_owner']
        objectives = ['support_victor', 'support_marina', 'voter_disillusionment']
        content_types = ['audience_building', 'political']
        
        for persona in personas:
            if persona not in settings.personas.get('personas', {}):
                continue  # Skip if persona not configured
                
            generator = ContentGenerator(persona)
            
            for objective in objectives:
                for content_type in content_types:
                    # Mock LLM to avoid API calls
                    with patch.object(generator.llm_client, 'generate_content', return_value=None):
                        content = await generator.generate_content(
                            content_type=content_type,
                            persona=persona,
                            objective=objective
                        )
                        
                        # Should generate content via templates
                        assert content is not None
                        assert len(content) > 10  # Reasonable length
                        assert len(content) <= settings.content.max_post_length
    
    def test_configuration_consistency(self):
        """Test that configurations are consistent across components."""
        # Check that all persona names in templates exist in personas.json
        personas = set(settings.personas.get('personas', {}).keys())
        
        # Check content templates reference valid personas
        templates = settings.content_templates.get('content_templates', {})
        
        # Should have templates for main content types
        assert 'audience_building' in templates
        assert 'political_content' in templates
        
        # Check hashtag libraries exist
        hashtags = settings.content_templates.get('hashtag_libraries', {})
        assert 'kingston_local' in hashtags
        assert 'political_general' in hashtags


# Helper functions for testing
def mock_api_response(status_code=200, data=None):
    """Create a mock API response."""
    response = MagicMock()
    response.status = status_code
    response.json = AsyncMock(return_value=data or {})
    return response


def create_test_post(content="Test content", username="test_user", likes=0, replies=0):
    """Create a test post object."""
    return {
        'id': 'test_123',
        'content': content,
        'username': username,
        'likes': likes,
        'replies': replies,
        'timestamp': '2024-01-01T12:00:00Z'
    }


# Test utilities
class TestUtils:
    """Test utility functions."""
    
    def test_create_test_post(self):
        """Test test post creation utility."""
        post = create_test_post("Hello world", "testuser", 5, 2)
        
        assert post['content'] == "Hello world"
        assert post['username'] == "testuser"
        assert post['likes'] == 5
        assert post['replies'] == 2
    
    def test_mock_api_response(self):
        """Test mock API response utility."""
        response = mock_api_response(200, {'message': 'success'})
        
        assert response.status == 200


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])