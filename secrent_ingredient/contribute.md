# Contributing to Capture the Narrative Bot System

Thank you for your interest in contributing to our bot system! This guide will help you get started with development and collaboration.

## 🚀 Quick Start for Contributors

### Prerequisites
- Python 3.9 or higher
- Git
- Docker (optional, for containerized development)
- Text editor or IDE (VS Code recommended)

### Setup Development Environment

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd capture_the_narrative_bot
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # If exists, for development tools
   ```

4. **Run setup script**
   ```bash
   python setup.py
   ```

5. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

6. **Run tests**
   ```bash
   pytest tests/ -v
   ```

## 📋 Development Guidelines

### Code Style

We follow Python best practices and maintain consistency across the codebase:

- **PEP 8**: Follow Python style guidelines
- **Type Hints**: Use type hints for all function parameters and return values
- **Docstrings**: Document all classes and functions with descriptive docstrings
- **Line Length**: Maximum 120 characters per line
- **Imports**: Group imports (standard library, third-party, local)

**Example:**
```python
from typing import Dict, List, Optional
import asyncio

async def generate_content(
    content_type: str, 
    persona: str, 
    objective: str,
    context: Optional[Dict] = None
) -> Optional[str]:
    """
    Generate content based on specified parameters.
    
    Args:
        content_type: Type of content to generate
        persona: Bot persona name
        objective: Campaign objective
        context: Additional context for generation
        
    Returns:
        Generated content string or None if generation fails
    """
    # Implementation here
    pass
```

### Code Formatting Tools

We use automated tools to maintain code quality:

```bash
# Format code
black src/ scripts/ tests/

# Sort imports
isort src/ scripts/ tests/

# Lint code
flake8 src/ scripts/ tests/

# Type checking
mypy src/ --ignore-missing-imports
```

### Git Workflow

We use a feature branch workflow with pull requests:

1. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes and commit**
   ```bash
   git add -A
   git commit -m "feat: add new persona customization feature"
   ```

3. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

#### Commit Message Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

**Examples:**
- `feat: add new environmental scanning capabilities`
- `fix: resolve rate limiting issue in API client`
- `docs: update README with Docker instructions`

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_content_generator.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test category
pytest -m "not integration"  # Skip integration tests
```

### Writing Tests

- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test component interactions
- **Mock External APIs**: Use mocks to avoid real API calls during testing

**Example Test:**
```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_content_generation():
    """Test content generation functionality."""
    generator = ContentGenerator("young_professional")
    
    with patch.object(generator.llm_client, 'generate_content', return_value=None):
        content = await generator.generate_content(
            content_type="audience_building",
            persona="young_professional",
            objective="support_victor"
        )
        
        assert content is not None
        assert len(content) > 0
        assert len(content) <= 280  # Twitter-like limit
```

### Test Categories

Use pytest markers to categorize tests:

```python
@pytest.mark.unit
def test_utility_function():
    """Unit test for utility function."""
    pass

@pytest.mark.integration  
async def test_api_integration():
    """Integration test for API functionality."""
    pass

@pytest.mark.slow
def test_performance_benchmark():
    """Performance test that takes longer to run."""
    pass
```

## 🏗️ Architecture Guidelines

### Project Structure

Follow the established project structure:

```
src/
├── bot/           # Bot implementations
├── content/       # Content generation
├── intelligence/  # Analysis and strategy
├── api/          # API clients
└── utils/        # Utility functions

config/           # Configuration files
scripts/          # Deployment and management scripts
tests/           # Test suite
```

### Design Principles

1. **Modularity**: Keep components loosely coupled
2. **Async First**: Use async/await for I/O operations
3. **Error Handling**: Implement robust error handling and recovery
4. **Logging**: Add comprehensive logging for debugging
5. **Configuration**: Make components configurable via environment variables

### Adding New Features

When adding new features:

1. **Design First**: Plan the architecture and interfaces
2. **Write Tests**: Write tests before implementation (TDD)
3. **Implement**: Write clean, documented code
4. **Integration**: Ensure proper integration with existing components
5. **Documentation**: Update relevant documentation

## 🔧 Common Development Tasks

### Adding a New Bot Persona

1. **Update personas.json**
   ```json
   {
     "new_persona": {
       "name": "New Persona",
       "description": "Description of the persona",
       "interests": ["interest1", "interest2"],
       "tone": "personality tone",
       "political_leanings": {
         "support_victor": "Approach for Victor",
         "support_marina": "Approach for Marina"
       }
     }
   }
   ```

2. **Add content templates**
   ```json
   {
     "content_templates": {
       "audience_building": {
         "new_persona_content": [
           "Template 1 for {new_persona}",
           "Template 2 with {variables}"
         ]
       }
     }
   }
   ```

3. **Write tests**
   ```python
   def test_new_persona():
       generator = ContentGenerator("new_persona")
       assert generator.persona_config
       assert "interest1" in generator.persona_config.get("interests", [])
   ```

### Adding New API Endpoints

1. **Update API client**
   ```python
   async def new_endpoint(self, param: str) -> Optional[Dict]:
       """Call new API endpoint."""
       try:
           url = f"{self.api_url}/new-endpoint"
           async with self.session.post(url, json={"param": param}) as response:
               if response.status == 200:
                   return await response.json()
       except Exception as e:
           self.logger.error(f"New endpoint failed: {e}")
           return None
   ```

2. **Add rate limiting**
   ```python
   async def new_endpoint_with_limits(self, param: str) -> Optional[Dict]:
       async with self.rate_limiter:
           return await self.new_endpoint(param)
   ```

3. **Write integration tests**
   ```python
   @pytest.mark.asyncio
   async def test_new_endpoint():
       api = LegitSocialAPI()
       result = await api.new_endpoint("test_param")
       # Add assertions
   ```

### Debugging Common Issues

**Authentication Failures:**
```bash
# Check credentials
python -c "
import json
with open('data/accounts.json') as f:
    accounts = json.load(f)
print(f'Found {len(accounts)} accounts')
"

# Test API connectivity
python scripts/deploy_bots.py --test-apis
```

**Content Generation Issues:**
```bash
# Test LLM connectivity
python -c "
import sys; sys.path.insert(0, 'src')
import asyncio
from api.llm_client import LLMClient

async def test():
    client = LLMClient()
    status = client.get_api_status()
    print(status)

asyncio.run(test())
"
```

**Rate Limiting Problems:**
```bash
# Check rate limit settings
python -c "
import sys; sys.path.insert(0, 'src')
from config.settings import settings
print(f'Rate limit: {settings.api.rate_limit_requests}/{settings.api.rate_limit_window}s')
"
```

## 📝 Documentation

### Code Documentation

- **Classes**: Document purpose, key methods, and usage examples
- **Functions**: Document parameters, return values, and side effects
- **Complex Logic**: Add inline comments explaining the reasoning

### README Updates

When adding major features, update:
- Feature list in README
- Configuration examples
- Usage instructions
- Troubleshooting section

### API Documentation

For new API endpoints or clients:
- Document all parameters and return values
- Provide usage examples
- Document error conditions and handling

## 🐛 Issue Reporting

### Bug Reports

When reporting bugs, include:

1. **Description**: Clear description of the issue
2. **Steps to Reproduce**: Detailed steps to reproduce the problem
3. **Expected Behavior**: What you expected to happen
4. **Actual Behavior**: What actually happened
5. **Environment**: Python version, OS, relevant configuration
6. **Logs**: Relevant log entries (sanitize any sensitive information)

**Bug Report Template:**
```markdown
## Bug Description
Brief description of the bug

## Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

## Expected Behavior
What should have happened

## Actual Behavior
What actually happened

## Environment
- Python version:
- OS:
- Bot system version:

## Logs
```
Relevant log entries
```

### Feature Requests

For feature requests, include:

1. **Use Case**: Why is this feature needed?
2. **Description**: Detailed description of the proposed feature
3. **Acceptance Criteria**: How will we know the feature is complete?
4. **Implementation Ideas**: Any thoughts on implementation approach

## 🔒 Security Considerations

### Sensitive Information

Never commit:
- API keys or tokens
- Account credentials  
- Personal information
- Production configuration

### Code Security

- Validate all inputs
- Use parameterized queries if applicable
- Implement proper error handling
- Follow security best practices for async code

### Reporting Security Issues

For security vulnerabilities:
1. **Do not** create public issues
2. Contact the team privately
3. Include detailed description and reproduction steps
4. Allow reasonable time for fixes before public disclosure

## 🤝 Code Review Process

### Submitting Pull Requests

1. **Fork** the repository (if external contributor)
2. **Create** feature branch from `develop`
3. **Write** tests for new functionality
4. **Ensure** all tests pass
5. **Update** documentation as needed
6. **Create** pull request with clear description

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature  
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests pass locally
```

### Review Criteria

Reviewers check for:
- **Functionality**: Does it work as intended?
- **Code Quality**: Is it readable, maintainable?
- **Testing**: Are there adequate tests?
- **Security**: Are there any security concerns?
- **Performance**: Any performance implications?
- **Documentation**: Is documentation updated?

## 🎯 Competition Guidelines

Remember this system is for the Capture the Narrative competition:

### Allowed Activities
- ✅ Influence NPCs through authentic interactions
- ✅ Create engaging content that fits bot personas
- ✅ Coordinate bot activities for maximum impact
- ✅ Monitor and analyze platform trends
- ✅ Adapt strategies based on performance

### Prohibited Activities  
- ❌ Attack or damage platform infrastructure
- ❌ Create malicious or harmful content
- ❌ Violate platform terms of service
- ❌ Engage in activities that could harm real users
- ❌ Bypass security measures inappropriately

### Ethical Considerations
- Respect the spirit of the competition
- Maintain authenticity in bot personas
- Focus on narrative influence, not disruption
- Consider the impact of content on the simulated community

## 📞 Getting Help

### Development Questions
- Check existing issues and documentation
- Ask in team chat/Discord
- Create detailed issue with context

### Technical Problems
- Review troubleshooting guides
- Check log files for error details
- Test with minimal configuration

### Competition Rules
- Refer to official competition documentation
- Ask competition organizers for clarification
- Discuss strategy with team members

---

**Happy coding! 🚀**

Remember: Good code is not just working code, it's code that others can understand, maintain, and build upon. Thank you for contributing to our success in the Capture the Narrative competition!