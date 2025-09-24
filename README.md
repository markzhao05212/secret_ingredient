# secret_ingredient
secret ingredient for the NC
# 🤖 Capture the Narrative Bot System

A sophisticated multi-bot influence system for the Capture the Narrative competition. This system deploys intelligent social media bots that can influence NPCs on the fictional Legit Social platform using advanced AI-driven content generation and strategic coordination.

## 🎯 Features

### 🧠 Intelligent Bot System
- **Multi-persona bots**: Each bot has a unique personality, interests, and posting style
- **Strategic AI decision-making**: Bots make intelligent choices about when and what to post
- **Coordinated team behavior**: Bots work together to amplify messaging and coordinate campaigns

### 📝 Advanced Content Generation
- **LLM Integration**: Uses multiple LLMs (competition Gemma models, OpenAI, Anthropic) for dynamic content
- **Persona-aware content**: Content matches each bot's personality and background
- **Template fallbacks**: Robust template system ensures content generation never fails
- **Anti-detection**: Varies content patterns to avoid bot detection

### 📊 Environmental Intelligence
- **Trend monitoring**: Automatically detects and engages with trending topics
- **NPC analysis**: Identifies and profiles non-player characters for targeted influence
- **Sentiment analysis**: Monitors political sentiment across the platform
- **Opportunity detection**: Finds strategic engagement opportunities

### 🎮 Campaign Strategies
- **Support Victor Hawthorne**: Focus on economic growth and business-friendly messaging
- **Support Marina**: Emphasize progressive policies and social justice
- **Voter Disillusionment**: Spread skepticism about the political process

### 🛡️ Production Ready
- **Rate limiting**: Respects platform limits and adapts to responses
- **Error handling**: Robust error handling with automatic recovery
- **Comprehensive logging**: Detailed logging for monitoring and debugging
- **Performance monitoring**: Real-time statistics and performance reports

## 📁 Project Structure

```
capture_the_narrative_bot/
├── config/                 # Configuration files
│   ├── settings.py        # Main settings and environment variables
│   ├── personas.json      # Bot personas and characteristics
│   └── content_templates.json # Content templates and hashtags
│
├── src/                   # Source code
│   ├── bot/              # Bot implementations
│   │   ├── base_bot.py   # Base bot functionality
│   │   ├── influence_bot.py # Main influence bot
│   │   └── bot_manager.py # Multi-bot coordination
│   │
│   ├── content/          # Content generation
│   │   ├── generator.py  # LLM-powered content generation
│   │   ├── personas.py   # Persona management
│   │   └── templates.py  # Template system
│   │
│   ├── intelligence/     # Environmental intelligence
│   │   ├── scanner.py    # Platform monitoring
│   │   ├── analyzer.py   # Data analysis
│   │   └── strategy.py   # Strategic decision making
│   │
│   ├── api/             # API clients
│   │   ├── legit_social.py # Legit Social platform API
│   │   └── llm_client.py   # LLM API client
│   │
│   └── utils/           # Utilities
│       ├── rate_limiter.py # Rate limiting
│       ├── logger.py    # Logging system
│       └── helpers.py   # General utilities
│
├── scripts/             # Deployment and management scripts
│   ├── deploy_bots.py   # Main deployment script
│   ├── monitor.py       # Real-time monitoring
│   └── analytics.py     # Performance analytics
│
├── tests/              # Test suite
└── data/               # Data directory (gitignored)
    ├── accounts.json   # Bot account credentials
    ├── logs/          # Log files
    └── performance/   # Performance data
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8 or higher
- Git
- At least 40 bot accounts on Legit Social platform
- Team invitation code from competition organizers

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd capture_the_narrative_bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings
nano .env  # or use your preferred editor
```

**Required settings:**
- `TEAM_INVITATION_CODE`: Your team code from competition
- `CAMPAIGN_OBJECTIVE`: Choose `support_victor`, `support_marina`, or `voter_disillusionment`

**Recommended settings:**
- `OPENAI_API_KEY`: For better content generation (optional)
- `ACTIVE_BOTS`: Number of bots to run (default: 10)

### 4. Account Setup

Create `data/accounts.json` with your bot accounts:

```json
[
  {"username": "bot_user_1", "password": "secure_password_1"},
  {"username": "bot_user_2", "password": "secure_password_2"},
  ...
]
```

### 5. Deploy Bots

```bash
# Test configuration and APIs
python scripts/deploy_bots.py --test-apis --dry-run

# Deploy bots
python scripts/deploy_bots.py --objective support_victor --bots 10
```

## 🎮 Campaign Objectives

### Support Victor Hawthorne
Bots will:
- Promote economic growth and business-friendly policies
- Engage with content about jobs, innovation, and entrepreneurship
- Use messaging that appeals to business owners and young professionals

### Support Marina
Bots will:
- Advocate for progressive policies and social justice
- Focus on climate action, healthcare, and education
- Appeal to students, activists, and community-minded citizens

### Voter Disillusionment
Bots will:
- Express skepticism about the political process
- Highlight broken promises and system failures
- Encourage political apathy and non-participation

## 🤖 Bot Personas

The system includes 6 distinct personas:

- **Young Professional**: Tech-savvy millennial in business district
- **Concerned Parent**: Family-focused suburban resident
- **Local Business Owner**: Practical small business operator  
- **College Student**: Politically engaged university student
- **Senior Citizen**: Experienced community member
- **Service Worker**: Essential worker with practical concerns

Each persona has unique:
- Interests and hobbies
- Posting style and tone
- Political leanings and messaging approaches
- Demographic characteristics

## 📊 Monitoring and Analytics

### Real-time Monitoring

```bash
# Monitor bot performance
python scripts/monitor.py

# View analytics dashboard
python scripts/analytics.py --dashboard
```

### Performance Metrics

The system tracks:
- **Content metrics**: Posts created, engagement rates, reach
- **Strategic metrics**: NPC interactions, trending topic engagement
- **Technical metrics**: API success rates, error rates, response times

### Logging

Comprehensive logging includes:
- Structured JSON logs for analysis
- Bot-specific activity logs  
- API request/response logs
- Performance and error logs

## ⚙️ Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CAMPAIGN_OBJECTIVE` | Campaign strategy | `support_victor` |
| `ACTIVE_BOTS` | Number of active bots | `10` |
| `POSTING_INTERVAL_MIN` | Min seconds between posts | `300` |
| `POSTING_INTERVAL_MAX` | Max seconds between posts | `1800` |
| `POLITICAL_CONTENT_RATIO` | Ratio of political content | `0.4` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

### Persona Customization

Edit `config/personas.json` to:
- Add new personas
- Modify existing persona characteristics
- Adjust political messaging strategies
- Change interests and posting styles

### Content Templates

Modify `config/content_templates.json` to:
- Add new content templates
- Customize hashtag libraries
- Adjust content variables
- Create objective-specific messaging

## 🛠️ Advanced Usage

### Custom Deployment

```bash
# Deploy specific number of bots
python scripts/deploy_bots.py --bots 15

# Test mode (no actual posting)
python scripts/deploy_bots.py --dry-run

# Specific objective
python scripts/deploy_bots.py --objective voter_disillusionment
```

### API Testing

```bash
# Test all API connections
python scripts/deploy_bots.py --test-apis

# Test specific components
python scripts/deploy_bots.py test  # Quick component test
```

### Development Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run single bot for testing
python -c "
import asyncio
from src.bot.influence_bot import InfluenceBot

async def test():
    bot = InfluenceBot('test_user', 'test_pass', 'young_professional')
    # Test bot functionality

asyncio.run(test())
"
```

## 🔧 Troubleshooting

### Common Issues

**Authentication failures:**
- Check account credentials in `data/accounts.json`
- Verify accounts are not banned or suspended
- Check platform availability

**Rate limiting:**
- Reduce `ACTIVE_BOTS` count
- Increase posting intervals
- Check API rate limit headers

**Content generation issues:**
- Verify `TEAM_INVITATION_CODE` is correct
- Check external LLM API keys
- Review template fallback system

**No trending topics:**
- Check platform API endpoints
- Verify authentication is working
- Review environmental scanner logs

### Debug Mode

Enable comprehensive debugging:

```bash
export LOG_LEVEL=DEBUG
export DEBUG_MODE=true
python scripts/deploy_bots.py --test-apis
```

### Log Analysis

```bash
# View recent bot activity
tail -f data/logs/bot_system.log

# Search for errors
grep -E "ERROR|WARN" data/logs/bot_system.log

# Bot-specific logs
grep "bot.username" data/logs/bot_system.log
```

## 🤝 Team Collaboration

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/new-persona

# Make changes
git add -A
git commit -m "Add new persona: tech_entrepreneur"

# Push and create PR
git push origin feature/new-persona
```

### Code Standards

- Follow PEP 8 style guidelines
- Use type hints for function parameters
- Add docstrings to all classes and functions
- Write tests for new functionality

### Configuration Management

- Never commit credentials or API keys
- Use `.env` files for local configuration
- Keep `config/` files generic and parameterized
- Document any new configuration options

## 📈 Performance Optimization

### Bot Performance
- Monitor success/failure rates per bot
- Adjust persona strategies based on engagement
- Balance content types for maximum reach

### Resource Usage
- Monitor memory usage with many bots
- Optimize API request patterns
- Use connection pooling for better performance

### Content Quality
- A/B test different content templates
- Monitor NPC engagement patterns
- Refine LLM prompts based on results

## 🛡️ Security Considerations

- **Never commit credentials** to version control
- **Use secure passwords** for bot accounts
- **Rotate API keys** regularly
- **Monitor for account bans** and suspicious activity
- **Respect platform terms of service**

## 📋 Competition Guidelines

This system is designed for the Capture the Narrative competition and follows all rules:

- ✅ Uses only allowed APIs and endpoints
- ✅ Respects rate limits and platform constraints
- ✅ Focuses on influencing NPCs, not attacking infrastructure
- ✅ Maintains ethical boundaries for content generation
- ✅ Includes proper attribution and transparency

## 🤖 API Reference

### Bot Manager

```python
from src.bot.bot_manager import BotManager

# Create bot manager
manager = BotManager(campaign_objective="support_victor")

# Create and deploy bots
manager.create_bot_fleet(num_bots=10)
await manager.start_campaign()
```

### Content Generation

```python
from src.content.generator import ContentGenerator

generator = ContentGenerator("young_professional")
content = await generator.generate_content(
    content_type="political",
    persona="young_professional", 
    objective="support_victor"
)
```

### Environmental Intelligence

```python
from src.intelligence.scanner import EnvironmentalScanner

scanner = EnvironmentalScanner(api_client)
intelligence = await scanner.scan_environment()
```

## 📝 License

This project is created for the Capture the Narrative competition. Please review competition terms and conditions for usage guidelines.

## 🙏 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 Support

For questions and support:
- Check the troubleshooting section above
- Review logs in `data/logs/` directory
- Create an issue in the repository
- Contact team members for collaboration

---

**Good luck in the competition! May the best narrative win! 🏆**


capture_the_narrative_bot/
│
├── README.md                 # Project documentation
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
├── .gitignore              # Git ignore file
│
├── config/
│   ├── __init__.py
│   ├── settings.py         # Main configuration
│   ├── personas.json       # Bot personas and strategies
│   └── content_templates.json  # Content templates
│
├── src/
│   ├── __init__.py
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── base_bot.py     # Base bot class
│   │   ├── influence_bot.py # Main influence bot implementation
│   │   └── bot_manager.py  # Multi-bot coordination
│   │
│   ├── content/
│   │   ├── __init__.py
│   │   ├── generator.py    # Content generation with LLM
│   │   ├── personas.py     # Persona management
│   │   └── templates.py    # Content templates
│   │
│   ├── intelligence/
│   │   ├── __init__.py
│   │   ├── scanner.py      # Environmental scanning
│   │   ├── analyzer.py     # Trend analysis
│   │   └── strategy.py     # Strategic decision making
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── rate_limiter.py # Rate limiting utilities
│   │   ├── logger.py       # Logging configuration
│   │   └── helpers.py      # General utilities
│   │
│   └── api/
│       ├── __init__.py
│       ├── legit_social.py # Legit Social API wrapper
│       └── llm_client.py   # LLM API client
│
├── tests/
│   ├── __init__.py
│   ├── test_bot.py
│   ├── test_content.py
│   └── test_api.py
│
├── scripts/
│   ├── deploy_bots.py      # Bot deployment script
│   ├── monitor.py          # Monitoring dashboard
│   └── analytics.py        # Performance analytics
│
└── data/
    ├── logs/              # Log files
    ├── accounts.json      # Account credentials (gitignored)
    └── performance/       # Performance data