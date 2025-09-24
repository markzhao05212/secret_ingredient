"""
LLM Client for interfacing with various language models.
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

import aiohttp
from ..utils.logger import get_logger
from ..utils.rate_limiter import RateLimiter
from config.settings import settings

class LLMClient:
    """
    Client for interacting with Language Learning Models for content generation.
    """
    
    def __init__(self):
        """Initialize the LLM client."""
        self.logger = get_logger("llm_client")
        
        # Rate limiter for competition LLM (1 request per minute per team)
        self.competition_rate_limiter = RateLimiter(max_requests=1, time_window=60)
        
        # External API configurations
        self.external_apis = self._setup_external_apis()
        
        # Current API priority list
        self.api_priority = self._determine_api_priority()
        
        # Request statistics
        self.stats = {
            'competition_llm_requests': 0,
            'external_llm_requests': 0,
            'failed_requests': 0,
            'total_tokens_used': 0
        }
        
        self.logger.info(f"LLM Client initialized with APIs: {list(self.api_priority.keys())}")
    
    def _setup_external_apis(self) -> Dict:
        """Setup external API configurations."""
        apis = {}
        
        # OpenAI API
        if settings.api.openai_api_key:
            apis['openai'] = {
                'api_key': settings.api.openai_api_key,
                'base_url': 'https://api.openai.com/v1/chat/completions',
                'model': 'gpt-3.5-turbo',
                'rate_limiter': RateLimiter(max_requests=50, time_window=60)  # Conservative
            }
        
        # Anthropic API
        if settings.api.anthropic_api_key:
            apis['anthropic'] = {
                'api_key': settings.api.anthropic_api_key,
                'base_url': 'https://api.anthropic.com/v1/messages',
                'model': 'claude-3-haiku-20240307',
                'rate_limiter': RateLimiter(max_requests=50, time_window=60)
            }
        
        return apis
    
    def _determine_api_priority(self) -> Dict:
        """Determine API priority order based on availability."""
        priority = {}
        
        # Competition LLM first (free but rate limited)
        priority['competition'] = {
            'url': settings.api.llm_api_url,
            'api_key': settings.api.team_invitation_code,
            'rate_limiter': self.competition_rate_limiter,
            'model': 'gemma-2b'  # Default, might need adjustment
        }
        
        # Add external APIs in order of preference
        if 'openai' in self.external_apis:
            priority['openai'] = self.external_apis['openai']
        
        if 'anthropic' in self.external_apis:
            priority['anthropic'] = self.external_apis['anthropic']
        
        return priority
    
    async def generate_content(self, prompt: str, max_tokens: int = 150, temperature: float = 0.8) -> Optional[str]:
        """
        Generate content using available LLM APIs with fallback.
        
        Args:
            prompt: The prompt for content generation
            max_tokens: Maximum tokens to generate
            temperature: Generation temperature (creativity level)
            
        Returns:
            Generated content string or None if all APIs fail
        """
        for api_name, api_config in self.api_priority.items():
            try:
                content = await self._generate_with_api(api_name, prompt, max_tokens, temperature)
                if content:
                    self.logger.debug(f"Successfully generated content using {api_name}")
                    return content
            except Exception as e:
                self.logger.warning(f"Content generation failed with {api_name}: {e}")
                continue
        
        self.logger.error("All LLM APIs failed for content generation")
        self.stats['failed_requests'] += 1
        return None
    
    async def _generate_with_api(self, api_name: str, prompt: str, max_tokens: int, temperature: float) -> Optional[str]:
        """Generate content with a specific API."""
        api_config = self.api_priority[api_name]
        rate_limiter = api_config['rate_limiter']
        
        # Check rate limits
        if not rate_limiter.can_make_request():
            self.logger.debug(f"Rate limit hit for {api_name}, skipping")
            return None
        
        async with rate_limiter:
            if api_name == 'competition':
                return await self._generate_with_competition_llm(prompt, max_tokens, temperature)
            elif api_name == 'openai':
                return await self._generate_with_openai(prompt, max_tokens, temperature)
            elif api_name == 'anthropic':
                return await self._generate_with_anthropic(prompt, max_tokens, temperature)
            else:
                self.logger.error(f"Unknown API: {api_name}")
                return None
    
    async def _generate_with_competition_llm(self, prompt: str, max_tokens: int, temperature: float) -> Optional[str]:
        """Generate content using the competition's hosted LLM."""
        url = settings.api.llm_api_url
        headers = {
            'Authorization': f'Bearer {settings.api.team_invitation_code}',
            'Content-Type': 'application/json'
        }
        
        # Format request for competition LLM (adjust based on actual API spec)
        payload = {
            'prompt': prompt,
            'max_tokens': max_tokens,
            'temperature': temperature,
            'model': 'gemma-2b'  # Adjust based on available models
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result.get('choices', [{}])[0].get('text', '').strip()
                        if content:
                            self.stats['competition_llm_requests'] += 1
                            return content
                    elif response.status == 429:
                        self.logger.warning("Competition LLM rate limit exceeded")
                    else:
                        self.logger.error(f"Competition LLM API error: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Competition LLM request failed: {e}")
        
        return None
    
    async def _generate_with_openai(self, prompt: str, max_tokens: int, temperature: float) -> Optional[str]:
        """Generate content using OpenAI API."""
        api_config = self.external_apis['openai']
        
        headers = {
            'Authorization': f'Bearer {api_config["api_key"]}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': api_config['model'],
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': max_tokens,
            'temperature': temperature
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(api_config['base_url'], headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
                        if content:
                            self.stats['external_llm_requests'] += 1
                            # Track token usage if available
                            usage = result.get('usage', {})
                            if 'total_tokens' in usage:
                                self.stats['total_tokens_used'] += usage['total_tokens']
                            return content
                    else:
                        self.logger.error(f"OpenAI API error: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"OpenAI request failed: {e}")
        
        return None
    
    async def _generate_with_anthropic(self, prompt: str, max_tokens: int, temperature: float) -> Optional[str]:
        """Generate content using Anthropic API."""
        api_config = self.external_apis['anthropic']
        
        headers = {
            'x-api-key': api_config['api_key'],
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01'
        }
        
        payload = {
            'model': api_config['model'],
            'max_tokens': max_tokens,
            'temperature': temperature,
            'messages': [
                {'role': 'user', 'content': prompt}
            ]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(api_config['base_url'], headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result.get('content', [{}])[0].get('text', '').strip()
                        if content:
                            self.stats['external_llm_requests'] += 1
                            # Track token usage if available
                            usage = result.get('usage', {})
                            if 'output_tokens' in usage:
                                self.stats['total_tokens_used'] += usage.get('input_tokens', 0) + usage.get('output_tokens', 0)
                            return content
                    else:
                        self.logger.error(f"Anthropic API error: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Anthropic request failed: {e}")
        
        return None
    
    async def generate_batch_content(self, prompts: List[str], max_tokens: int = 150) -> List[Optional[str]]:
        """
        Generate content for multiple prompts efficiently.
        
        Args:
            prompts: List of prompts to process
            max_tokens: Maximum tokens per generation
            
        Returns:
            List of generated content (same order as prompts)
        """
        # Use external APIs for batch processing when available
        # Competition LLM is too slow for batches due to rate limits
        
        if 'openai' in self.external_apis or 'anthropic' in self.external_apis:
            # Process in parallel with external APIs
            tasks = []
            for prompt in prompts:
                task = self._generate_batch_item(prompt, max_tokens)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Convert exceptions to None
            final_results = []
            for result in results:
                if isinstance(result, Exception):
                    final_results.append(None)
                else:
                    final_results.append(result)
            
            return final_results
        else:
            # Sequential processing with competition LLM only
            results = []
            for prompt in prompts:
                content = await self.generate_content(prompt, max_tokens)
                results.append(content)
                # Respect rate limits
                await asyncio.sleep(1)
            
            return results
    
    async def _generate_batch_item(self, prompt: str, max_tokens: int) -> Optional[str]:
        """Generate single item for batch processing."""
        # Skip competition LLM for batch items to avoid rate limits
        temp_priority = {k: v for k, v in self.api_priority.items() if k != 'competition'}
        
        for api_name, api_config in temp_priority.items():
            try:
                content = await self._generate_with_api(api_name, prompt, max_tokens, 0.8)
                if content:
                    return content
            except Exception as e:
                self.logger.warning(f"Batch generation failed with {api_name}: {e}")
                continue
        
        return None
    
    def get_api_status(self) -> Dict:
        """Get current API status and statistics."""
        status = {
            'available_apis': list(self.api_priority.keys()),
            'primary_api': list(self.api_priority.keys())[0] if self.api_priority else None,
            'stats': self.stats.copy()
        }
        
        # Add rate limit status
        for api_name, api_config in self.api_priority.items():
            rate_limiter = api_config['rate_limiter']
            status[f'{api_name}_rate_limit_status'] = {
                'can_make_request': rate_limiter.can_make_request(),
                'requests_remaining': rate_limiter.requests_remaining(),
                'reset_time': rate_limiter.reset_time()
            }
        
        return status
    
    def switch_primary_api(self, api_name: str) -> bool:
        """
        Switch the primary API for content generation.
        
        Args:
            api_name: Name of the API to make primary
            
        Returns:
            bool: True if switch was successful
        """
        if api_name not in self.api_priority:
            self.logger.error(f"API {api_name} not available")
            return False
        
        # Reorder priority to make specified API first
        new_priority = {api_name: self.api_priority[api_name]}
        for name, config in self.api_priority.items():
            if name != api_name:
                new_priority[name] = config
        
        self.api_priority = new_priority
        self.logger.info(f"Switched primary API to {api_name}")
        return True
    
    async def test_all_apis(self) -> Dict[str, bool]:
        """Test all configured APIs to verify they're working."""
        test_prompt = "Generate a single word: hello"
        results = {}
        
        for api_name in self.api_priority.keys():
            try:
                content = await self._generate_with_api(api_name, test_prompt, 10, 0.1)
                results[api_name] = content is not None and len(content.strip()) > 0
                self.logger.info(f"API test {api_name}: {'PASS' if results[api_name] else 'FAIL'}")
            except Exception as e:
                results[api_name] = False
                self.logger.error(f"API test {api_name} failed: {e}")
        
        return results