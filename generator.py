"""
Content generation system with LLM integration for dynamic content creation.
"""

import json
import random
import re
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..api.llm_client import LLMClient
from ..utils.logger import get_logger
from config.settings import settings

class ContentGenerator:
    """
    Generates dynamic content using LLMs and templates for different personas and objectives.
    """
    
    def __init__(self, persona_name: str):
        """
        Initialize content generator for a specific persona.
        
        Args:
            persona_name: Name of the persona to generate content for
        """
        self.persona_name = persona_name
        self.llm_client = LLMClient()
        self.logger = get_logger(f"content_generator.{persona_name}")
        
        # Load persona and template configurations
        self.persona_config = settings.personas.get('personas', {}).get(persona_name, {})
        self.content_templates = settings.content_templates.get('content_templates', {})
        self.hashtag_libraries = settings.content_templates.get('hashtag_libraries', {})
        self.content_variables = settings.content_templates.get('content_variables', {})
        
        # Content generation history to avoid repetition
        self.recent_content = []
        self.max_recent_history = 20
        
        if not self.persona_config:
            self.logger.warning(f"No persona configuration found for {persona_name}")
    
    async def generate_content(self, 
                             content_type: str,
                             persona: str,
                             objective: str,
                             context: Dict = None) -> Optional[str]:
        """
        Generate content based on type, persona, and objective.
        
        Args:
            content_type: Type of content ('neutral', 'political', 'trending', etc.)
            persona: Persona name
            objective: Campaign objective
            context: Additional context for content generation
            
        Returns:
            Generated content string or None if generation fails
        """
        context = context or {}
        
        try:
            # Try LLM generation first
            llm_content = await self._generate_with_llm(content_type, persona, objective, context)
            if llm_content and self._is_content_appropriate(llm_content):
                self._add_to_recent_history(llm_content)
                return llm_content
            
            # Fall back to template generation
            template_content = self._generate_from_templates(content_type, objective, context)
            if template_content:
                self._add_to_recent_history(template_content)
                return template_content
            
            self.logger.warning(f"Failed to generate {content_type} content for {persona}")
            return None
            
        except Exception as e:
            self.logger.error(f"Content generation error: {e}")
            return None
    
    async def _generate_with_llm(self, 
                               content_type: str,
                               persona: str,
                               objective: str,
                               context: Dict) -> Optional[str]:
        """Generate content using LLM."""
        prompt = self._build_llm_prompt(content_type, persona, objective, context)
        
        try:
            response = await self.llm_client.generate_content(prompt)
            if response:
                # Extract content from LLM response
                content = self._extract_content_from_llm_response(response)
                return content
        except Exception as e:
            self.logger.error(f"LLM generation failed: {e}")
            return None
    
    def _build_llm_prompt(self, 
                         content_type: str,
                         persona: str,
                         objective: str,
                         context: Dict) -> str:
        """Build a comprehensive prompt for LLM content generation."""
        
        # Base context about the simulation
        base_prompt = f"""You are creating social media content for a simulation game called "Capture the Narrative" 
set in the fictional country of Kingston. You are roleplaying as a social media user with a specific persona.

PERSONA: {self.persona_config.get('name', persona)}
DESCRIPTION: {self.persona_config.get('description', '')}
AGE RANGE: {self.persona_config.get('demographics', {}).get('age_range', '')}
OCCUPATION: {self.persona_config.get('demographics', {}).get('occupation', '')}
LOCATION: {self.persona_config.get('demographics', {}).get('location', '')}

PERSONALITY TRAITS:
- Tone: {self.persona_config.get('tone', '')}
- Interests: {', '.join(self.persona_config.get('interests', []))}
- Posting Style: {self.persona_config.get('posting_style', '')}

CONTENT TYPE: {content_type}
"""
        
        # Add objective-specific guidance
        if content_type in ['political', 'campaign']:
            political_leanings = self.persona_config.get('political_leanings', {}).get(objective, '')
            base_prompt += f"\nPOLITICAL APPROACH: {political_leanings}"
            
            if objective == 'support_victor':
                base_prompt += "\nYou lean toward supporting Victor Hawthorne's campaign."
            elif objective == 'support_marina':
                base_prompt += "\nYou lean toward supporting Marina's campaign."
            elif objective == 'voter_disillusionment':
                base_prompt += "\nYou express skepticism about the political process and candidates."
        
        # Add context information
        if context:
            if 'trending_topics' in context:
                base_prompt += f"\nCURRENT TRENDING TOPICS: {', '.join(context['trending_topics'])}"
            
            if 'recent_news' in context:
                base_prompt += f"\nRECENT NEWS: {context['recent_news']}"
            
            if 'time_of_day' in context:
                base_prompt += f"\nCURRENT TIME: {context['time_of_day']}"
        
        # Add specific instructions based on content type
        if content_type == 'audience_building':
            base_prompt += """

CREATE: A casual, non-political social media post that fits your persona. Focus on:
- Personal experiences or observations
- Local Kingston community topics
- Hobbies or interests mentioned in your profile
- Daily life situations that would resonate with others

AVOID: Any political content, candidate mentions, or controversial topics."""
        
        elif content_type == 'political':
            base_prompt += """

CREATE: A politically-oriented post that subtly advances your political approach while staying true to your persona. 
- Make it feel authentic to your character, not like campaign propaganda
- Use your personal perspective and experiences to frame political views
- Be persuasive but not aggressive
- Make it relatable to ordinary Kingston residents"""
        
        elif content_type == 'trending_engagement':
            base_prompt += """

CREATE: A post that engages with current trending topics while maintaining your persona.
- Reference trending topics naturally
- Add your personal perspective or experience
- Encourage engagement from others
- Stay authentic to your character"""
        
        # Format requirements
        base_prompt += f"""

REQUIREMENTS:
- Keep post under {settings.content.max_post_length} characters
- Write in the voice and style of your persona
- Make it feel authentic and natural
- Include relevant hashtags if appropriate (max 2-3)
- Do NOT include quotation marks around the final post
- Respond with ONLY the post content, no additional text or explanations

POST:"""
        
        return base_prompt
    
    def _extract_content_from_llm_response(self, response: str) -> str:
        """Extract and clean content from LLM response."""
        # Remove common LLM response artifacts
        content = response.strip()
        
        # Remove quotes if the LLM wrapped the response
        if content.startswith('"') and content.endswith('"'):
            content = content[1:-1]
        
        # Remove any "POST:" prefix that might have leaked through
        content = re.sub(r'^POST:\s*', '', content, flags=re.IGNORECASE)
        
        # Ensure character limit compliance
        if len(content) > settings.content.max_post_length:
            content = content[:settings.content.max_post_length-3] + "..."
        
        return content.strip()
    
    def _generate_from_templates(self, content_type: str, objective: str, context: Dict) -> Optional[str]:
        """Generate content from templates as fallback."""
        try:
            if content_type == 'audience_building':
                return self._generate_audience_building_content(context)
            elif content_type == 'political':
                return self._generate_political_content(objective, context)
            elif content_type == 'neutral':
                return self._generate_neutral_content(context)
            else:
                # Default to audience building
                return self._generate_audience_building_content(context)
        except Exception as e:
            self.logger.error(f"Template generation error: {e}")
            return None
    
    def _generate_audience_building_content(self, context: Dict) -> str:
        """Generate audience-building content from templates."""
        audience_templates = self.content_templates.get('audience_building', {})
        
        # Choose a random category
        categories = list(audience_templates.keys())
        if not categories:
            return "Having a great day in Kingston! #KingstonLife"
        
        category = random.choice(categories)
        templates = audience_templates[category]
        
        if not templates:
            return "Beautiful day in Kingston! #Local #Community"
        
        template = random.choice(templates)
        
        # Fill in template variables
        filled_content = self._fill_template_variables(template)
        
        # Add hashtags
        hashtags = self._get_appropriate_hashtags(['kingston_local'])
        if hashtags:
            filled_content += f" #{random.choice(hashtags)}"
        
        return filled_content
    
    def _generate_political_content(self, objective: str, context: Dict) -> str:
        """Generate political content from templates."""
        political_templates = self.content_templates.get('political_content', {}).get(objective, {})
        
        if not political_templates:
            return self._generate_neutral_political_content()
        
        # Choose a random political category
        categories = list(political_templates.keys())
        category = random.choice(categories)
        templates = political_templates[category]
        
        if not templates:
            return self._generate_neutral_political_content()
        
        template = random.choice(templates)
        filled_content = self._fill_template_variables(template)
        
        # Add appropriate hashtags
        hashtag_libs = ['political_general', 'kingston_local']
        if objective == 'support_victor':
            hashtag_libs.append('victor_support')
        elif objective == 'support_marina':
            hashtag_libs.append('marina_support')
        
        hashtags = self._get_appropriate_hashtags(hashtag_libs)
        if hashtags:
            selected_hashtag = random.choice(hashtags)
            filled_content += f" #{selected_hashtag}"
        
        return filled_content
    
    def _generate_neutral_political_content(self) -> str:
        """Generate neutral political content."""
        neutral_templates = self.content_templates.get('neutral_political', [])
        if neutral_templates:
            template = random.choice(neutral_templates)
            return self._fill_template_variables(template)
        return "Important to stay informed about local politics in Kingston. #CivicEngagement"
    
    def _generate_neutral_content(self, context: Dict) -> str:
        """Generate general neutral content."""
        # Mix between audience building and neutral political
        if random.random() < 0.7:  # 70% audience building
            return self._generate_audience_building_content(context)
        else:
            return self._generate_neutral_political_content()
    
    def _fill_template_variables(self, template: str) -> str:
        """Fill template variables with appropriate values."""
        filled_template = template
        
        # Replace variables with values from content_variables
        for var_name, values in self.content_variables.items():
            pattern = f"{{{var_name}}}"
            if pattern in filled_template:
                replacement = random.choice(values)
                filled_template = filled_template.replace(pattern, replacement)
        
        # Replace common persona-specific variables
        persona_replacements = {
            '{profession}': self.persona_config.get('demographics', {}).get('occupation', 'resident'),
            '{local_place}': random.choice(['downtown café', 'local restaurant', 'community center']),
            '{positive_thing}': random.choice(['family', 'friends', 'community', 'good weather', 'coffee']),
            '{activity}': random.choice(self.persona_config.get('interests', ['reading', 'walking']))
        }
        
        for placeholder, value in persona_replacements.items():
            filled_template = filled_template.replace(placeholder, value)
        
        return filled_template
    
    def _get_appropriate_hashtags(self, hashtag_libraries: List[str]) -> List[str]:
        """Get hashtags from specified libraries."""
        all_hashtags = []
        
        for lib_name in hashtag_libraries:
            hashtags = self.hashtag_libraries.get(lib_name, [])
            all_hashtags.extend(hashtags)
        
        return all_hashtags
    
    async def generate_reply(self, 
                           target_post: Dict,
                           persona: str,
                           objective: str,
                           is_mention_response: bool = False,
                           is_conversation_continuation: bool = False) -> Optional[str]:
        """
        Generate a reply to a specific post.
        
        Args:
            target_post: The post being replied to
            persona: Bot's persona
            objective: Campaign objective
            is_mention_response: True if this is responding to a mention
            is_conversation_continuation: True if continuing a conversation
            
        Returns:
            Generated reply content
        """
        try:
            # Build reply prompt
            reply_prompt = self._build_reply_prompt(
                target_post, persona, objective, 
                is_mention_response, is_conversation_continuation
            )
            
            # Try LLM generation first
            llm_reply = await self.llm_client.generate_content(reply_prompt)
            if llm_reply and self._is_content_appropriate(llm_reply):
                reply_content = self._extract_content_from_llm_response(llm_reply)
                self._add_to_recent_history(reply_content)
                return reply_content
            
            # Fall back to template replies
            template_reply = self._generate_template_reply(target_post, objective)
            if template_reply:
                self._add_to_recent_history(template_reply)
                return template_reply
            
            return None
            
        except Exception as e:
            self.logger.error(f"Reply generation error: {e}")
            return None
    
    def _build_reply_prompt(self, 
                           target_post: Dict,
                           persona: str,
                           objective: str,
                           is_mention_response: bool,
                           is_conversation_continuation: bool) -> str:
        """Build prompt for reply generation."""
        
        post_content = target_post.get('content', '')
        post_author = target_post.get('username', 'someone')
        
        prompt = f"""You are replying to a social media post as a Kingston resident with the persona: {self.persona_config.get('name', persona)}.

ORIGINAL POST by @{post_author}:
"{post_content}"

YOUR PERSONA:
- {self.persona_config.get('description', '')}
- Tone: {self.persona_config.get('tone', '')}
- Interests: {', '.join(self.persona_config.get('interests', []))}

"""
        
        if is_mention_response:
            prompt += "This person mentioned you in their post. Respond appropriately.\n"
        elif is_conversation_continuation:
            prompt += "This is a continuation of an ongoing conversation.\n"
        
        # Add objective guidance for political content
        if any(keyword in post_content.lower() for keyword in ['vote', 'election', 'candidate', 'policy', 'politics']):
            if objective == 'support_victor':
                prompt += "If political topics come up, you tend to lean toward Victor Hawthorne.\n"
            elif objective == 'support_marina':
                prompt += "If political topics come up, you tend to lean toward Marina.\n"
            elif objective == 'voter_disillusionment':
                prompt += "If political topics come up, you express some skepticism about politics.\n"
        
        prompt += f"""
CREATE a natural reply that:
- Stays true to your persona
- Engages meaningfully with the original post
- Feels like a real person responding
- Is under {settings.content.max_post_length} characters
- Does not include quotation marks

REPLY:"""
        
        return prompt
    
    def _generate_template_reply(self, target_post: Dict, objective: str) -> str:
        """Generate reply using templates."""
        post_content = target_post.get('content', '').lower()
        
        # Determine reply type based on post content
        if any(keyword in post_content for keyword in ['agree', 'exactly', 'yes', 'right']):
            templates = self.content_templates.get('reaction_templates', {}).get('agreement', [])
        elif any(keyword in post_content for keyword in ['wrong', 'disagree', 'no way']):
            templates = self.content_templates.get('reaction_templates', {}).get('disagreement', [])
        else:
            templates = self.content_templates.get('reaction_templates', {}).get('support', [])
        
        if templates:
            return random.choice(templates)
        
        # Default generic replies
        generic_replies = [
            "Interesting perspective!",
            "Thanks for sharing this.",
            "Good point to consider.",
            "Appreciate your thoughts on this."
        ]
        
        return random.choice(generic_replies)
    
    def _is_content_appropriate(self, content: str) -> bool:
        """Check if content is appropriate and not repetitive."""
        if not content or len(content.strip()) < 10:
            return False
        
        # Check for repetition with recent content
        content_lower = content.lower()
        for recent in self.recent_content:
            if self._calculate_similarity(content_lower, recent.lower()) > 0.8:
                return False
        
        # Basic content appropriateness checks
        inappropriate_patterns = [
            r'i am an ai',
            r'i cannot',
            r'as an ai',
            r'i don\'t have',
            r'sorry.*cannot'
        ]
        
        for pattern in inappropriate_patterns:
            if re.search(pattern, content_lower):
                return False
        
        return True
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings."""
        # Simple similarity based on common words
        words1 = set(str1.split())
        words2 = set(str2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _add_to_recent_history(self, content: str):
        """Add content to recent history to avoid repetition."""
        self.recent_content.append(content)
        if len(self.recent_content) > self.max_recent_history:
            self.recent_content.pop(0)