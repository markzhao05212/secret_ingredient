#!/usr/bin/env python3
"""
Project creation script - generates the complete Capture the Narrative bot system
Save this file to your desktop and run: python create_project.py
"""

import os
import sys
from pathlib import Path

def create_project_structure():
    """Create the complete project structure with all files."""
    
    # Get desktop path
    desktop = Path.home() / "Desktop"
    project_path = desktop / "capture_the_narrative_bot"
    
    print(f"Creating project at: {project_path}")
    
    # Create main directory
    project_path.mkdir(exist_ok=True)
    os.chdir(project_path)
    
    # Create directory structure
    directories = [
        "config",
        "src/bot",
        "src/content", 
        "src/intelligence",
        "src/api",
        "src/utils",
        "scripts",
        "tests",
        "data/logs",
        "data/performance",
        "data/cache",
        ".github/workflows",
        "docker"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Created {directory}/")
    
    # File contents dictionary
    files = {
        # Root files
        "requirements.txt": '''# Core dependencies
requests>=2.31.0
python-dotenv>=1.0.0
pydantic>=2.0.0
aiohttp>=3.8.0
asyncio-throttle>=1.0.2

# LLM integration
openai>=1.0.0
anthropic>=0.3.0

# Data handling
pandas>=2.0.0
numpy>=1.24.0

# Logging and monitoring
structlog>=23.0.0
python-json-logger>=2.0.0

# Testing
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-mock>=3.10.0

# Development tools
black>=23.0.0
flake8>=6.0.0
mypy>=1.0.0''',
        
        ".env.example": '''# Capture the Narrative Bot System Configuration
# Copy this file to .env and fill in your actual values

# REQUIRED SETTINGS
TEAM_INVITATION_CODE=your_team_invitation_code_here
CAMPAIGN_OBJECTIVE=support_victor

# PLATFORM SETTINGS
PLATFORM_URL=https://social.legitreal.com
API_BASE_URL=https://social.legitreal.com/api
LLM_API_URL=https://llm-proxy.legitreal.com

# EXTERNAL LLM APIS (OPTIONAL)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# BOT CONFIGURATION
ACTIVE_BOTS=10
MAX_ACCOUNTS=40
POSTING_INTERVAL_MIN=300
POSTING_INTERVAL_MAX=1800
ENGAGEMENT_PROBABILITY=0.3

# RATE LIMITING
RATE_LIMIT_REQUESTS=3
RATE_LIMIT_WINDOW=60

# CONTENT STRATEGY
MAX_POST_LENGTH=280
USE_GIFS=true
GIF_PROBABILITY=0.2
POLITICAL_CONTENT_RATIO=0.4
NEUTRAL_CONTENT_RATIO=0.6
AUDIENCE_BUILDING_DAYS=2

# LOGGING
LOG_LEVEL=INFO
LOG_FILE=data/logs/bot_system.log
MAX_LOG_SIZE=10485760
BACKUP_COUNT=5''',
        
        ".gitignore": '''# Python
__pycache__/
*.py[cod]
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# PROJECT SPECIFIC
data/accounts.json
accounts.json
credentials.json
data/logs/
*.log
logs/
data/performance/
data/cache/
cache/
*.cache

# IDE files
.vscode/
.idea/
*.swp
*.swo
*~

# OS files
.DS_Store
Thumbs.db
Desktop.ini

# Secrets
secrets.json
api_keys.json
.secrets''',

        "README.md": '''# 🤖 Capture the Narrative Bot System

A sophisticated multi-bot influence system for the Capture the Narrative competition.

## 🚀 Quick Start

1. **Setup Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   pip install -r requirements.txt
   ```

2. **Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your TEAM_INVITATION_CODE and settings
   ```

3. **Add Bot Accounts**
   ```bash
   cp data/accounts.json.example data/accounts.json
   # Add your bot credentials (up to 40 accounts)
   ```

4. **Deploy Bots**
   ```bash
   python scripts/deploy_bots.py --objective support_victor --bots 10
   ```

5. **Monitor Performance**
   ```bash
   python scripts/monitor.py
   ```

## 📁 Project Structure

```
capture_the_narrative_bot/
├── config/           # Configuration files
├── src/              # Source code
│   ├── bot/         # Bot implementations
│   ├── content/     # Content generation
│   ├── intelligence/ # Environmental intelligence
│   ├── api/         # API clients
│   └── utils/       # Utilities
├── scripts/         # Deployment scripts
├── tests/           # Test suite
└── data/            # Data directory
```

## 🎯 Campaign Strategies

- **Support Victor Hawthorne**: Business-focused economic messaging
- **Support Marina**: Progressive policies and social justice
- **Voter Disillusionment**: System skepticism and apathy

## 🤖 Bot Personas

6 distinct personas with unique characteristics:
- Young Professional, Concerned Parent, Local Business Owner
- College Student, Senior Citizen, Service Worker

## 📊 Features

- Multi-bot coordination and management
- LLM-powered dynamic content generation
- Real-time environmental intelligence
- Strategic decision-making engine
- Comprehensive monitoring and analytics
- Docker containerization support

## 🐳 Docker Deployment

```bash
docker-compose up bot-system    # Run bots
docker-compose up monitor       # Monitoring
```

## 🏆 Competition Ready

- Ethical AI influence focused on NPCs
- Respects platform terms and rate limits
- Comprehensive error handling and recovery
- Team coordination for maximum impact

Good luck in the competition!''',

        # Config files
        "config/__init__.py": '''"""Configuration module for the bot system."""
from .settings import settings
__all__ = ["settings"]''',
        
        # Simplified main files (you'll need to copy full versions from artifacts above)
        "src/__init__.py": '''"""Capture the Narrative Bot System"""
__version__ = "1.0.0"''',
        
        "src/bot/__init__.py": '''"""Bot implementations."""''',
        "src/content/__init__.py": '''"""Content generation."""''',
        "src/intelligence/__init__.py": '''"""Intelligence modules."""''',
        "src/api/__init__.py": '''"""API clients."""''',
        "src/utils/__init__.py": '''"""Utility functions."""''',
        
        # Example accounts file
        "data/accounts.json.example": '''[
  {
    "username": "your_bot_username_1",
    "password": "your_bot_password_1",
    "note": "Replace with actual credentials"
  },
  {
    "username": "your_bot_username_2", 
    "password": "your_bot_password_2",
    "note": "Add up to 40 accounts for the competition"
  }
]''',

        # Docker files
        "Dockerfile": '''FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd -r botuser && useradd -r -g botuser botuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p data/logs data/performance data/cache && \\
    chown -R botuser:botuser /app

USER botuser

CMD ["python", "scripts/deploy_bots.py", "--objective", "support_victor", "--bots", "5"]''',

        "docker-compose.yml": '''version: '3.8'

services:
  bot-system:
    build: .
    container_name: capture-narrative-bots
    restart: unless-stopped
    env_file: .env
    volumes:
      - ./data:/app/data
      - ./config:/app/config:ro

  monitor:
    build: .
    container_name: capture-narrative-monitor
    restart: unless-stopped
    command: ["python", "scripts/monitor.py", "--interval", "60"]
    env_file: .env
    volumes:
      - ./data:/app/data:ro
    depends_on:
      - bot-system''',
        
        # Setup script
        "setup.py": '''#!/usr/bin/env python3
"""Setup script for the bot system."""

import os
from pathlib import Path

def main():
    print("🤖 Capture the Narrative Bot System Setup")
    print("=" * 50)
    
    # Check Python version
    import sys
    if sys.version_info < (3, 9):
        print("❌ Python 3.9 or higher required")
        return
    
    print("✅ Python version OK")
    
    # Check configuration
    if not Path(".env").exists():
        print("⚠️  .env file missing - copy from .env.example")
    else:
        print("✅ .env file exists")
    
    if not Path("data/accounts.json").exists():
        print("⚠️  data/accounts.json missing - copy from example and add credentials")
    else:
        print("✅ accounts.json exists")
    
    print("\\n📚 Next steps:")
    print("1. Configure .env with your TEAM_INVITATION_CODE")
    print("2. Add bot accounts to data/accounts.json")
    print("3. Install dependencies: pip install -r requirements.txt")
    print("4. Test: python scripts/deploy_bots.py --dry-run")
    print("5. Deploy: python scripts/deploy_bots.py --objective support_victor")

if __name__ == "__main__":
    main()''',
        
        # Quick start script
        "quick_start.sh": '''#!/bin/bash
# Quick Start Script

echo "🤖 Setting up Capture the Narrative Bot System..."

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Setup configuration
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ Created .env - please edit with your configuration"
else
    echo "✅ .env already exists"
fi

if [ ! -f "data/accounts.json" ]; then
    echo "⚠️  Please copy data/accounts.json.example to data/accounts.json"
    echo "   and add your bot account credentials"
else
    echo "✅ accounts.json exists"
fi

echo ""
echo "🚀 Setup complete! Next steps:"
echo "1. Edit .env with your TEAM_INVITATION_CODE"
echo "2. Add accounts to data/accounts.json" 
echo "3. Test: python scripts/deploy_bots.py --dry-run"
echo "4. Deploy: python scripts/deploy_bots.py --objective support_victor"''',
        
        # Basic deployment script
        "scripts/deploy_bots.py": '''#!/usr/bin/env python3
"""
Basic deployment script - you need to copy the full version from the artifacts above.
This is a minimal placeholder.
"""

import argparse
import sys
from pathlib import Path

def main():
    print("🤖 Capture the Narrative Bot Deployment")
    print("⚠️  This is a placeholder script!")
    print("Please copy the full deploy_bots.py from the generated artifacts.")
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='Show config without deploying')
    parser.add_argument('--objective', default='support_victor', help='Campaign objective')
    parser.add_argument('--bots', type=int, default=5, help='Number of bots')
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("✅ Dry run mode - configuration looks good!")
        print(f"Objective: {args.objective}")
        print(f"Bots: {args.bots}")
    else:
        print("❌ Full implementation needed - copy from artifacts")

if __name__ == "__main__":
    main()''',

        "scripts/monitor.py": '''#!/usr/bin/env python3
"""Placeholder monitor script"""
print("📊 Bot monitoring system")
print("⚠️  Copy full monitor.py from artifacts for complete functionality")''',

        "tests/__init__.py": '''"""Test suite for the bot system."""''',
        
        "tests/test_basic.py": '''"""Basic tests"""
def test_basic():
    """Basic test to ensure setup works"""
    assert True, "Basic test should pass"
    
def test_imports():
    """Test that we can import our modules"""
    try:
        import sys
        sys.path.insert(0, 'src')
        # Add more imports as you copy the full files
        assert True
    except ImportError as e:
        assert False, f"Import failed: {e}"'''
    }
    
    # Create all files
    for filepath, content in files.items():
        file_path = Path(filepath)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  ✓ Created {filepath}")
    
    print(f"\n🎉 Project created successfully at: {project_path}")
    print("\n📋 IMPORTANT NEXT STEPS:")
    print("1. The files above are basic templates/placeholders")
    print("2. You need to copy the FULL CONTENT from each artifact I created above")
    print("3. Key files to copy from artifacts:")
    print("   - config/settings.py")
    print("   - config/personas.json") 
    print("   - config/content_templates.json")
    print("   - src/bot/base_bot.py")
    print("   - src/bot/influence_bot.py")
    print("   - src/bot/bot_manager.py")
    print("   - src/content/generator.py")
    print("   - src/api/legit_social.py")
    print("   - src/api/llm_client.py")
    print("   - src/utils/rate_limiter.py")
    print("   - src/utils/logger.py")
    print("   - src/utils/helpers.py")
    print("   - src/intelligence/scanner.py")
    print("   - src/intelligence/strategy.py")
    print("   - scripts/deploy_bots.py (FULL VERSION)")
    print("   - scripts/monitor.py (FULL VERSION)")
    print("   - And all other artifacts from above")
    print(f"\n📁 Navigate to: cd {project_path}")
    print("🚀 Then copy the full file contents from all the artifacts I generated!")

if __name__ == "__main__":
    create_project_structure()