#!/usr/bin/env python3
"""
Setup script for the Capture the Narrative Bot System.
"""

import os
import sys
import json
import shutil
from pathlib import Path
from typing import List, Dict

def create_directory_structure():
    """Create required directory structure."""
    directories = [
        "data",
        "data/logs", 
        "data/performance",
        "data/cache",
        "config",
        "src",
        "src/bot",
        "src/content", 
        "src/intelligence",
        "src/api",
        "src/utils",
        "tests",
        "scripts"
    ]
    
    print("Creating directory structure...")
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Created {directory}/")

def setup_configuration_files():
    """Setup configuration files if they don't exist."""
    print("\nSetting up configuration files...")
    
    # Create .env file if it doesn't exist
    if not Path(".env").exists():
        if Path(".env.example").exists():
            shutil.copy(".env.example", ".env")
            print("  ✓ Created .env from .env.example")
            print("    ⚠️  Please edit .env with your actual configuration values")
        else:
            print("  ⚠️  .env.example not found - please create .env manually")
    else:
        print("  ✓ .env already exists")
    
    # Create accounts.json example if it doesn't exist
    accounts_file = Path("data/accounts.json")
    accounts_example = Path("data/accounts.json.example")
    
    if not accounts_file.exists():
        if accounts_example.exists():
            print("  ✓ accounts.json.example available")
            print("    ⚠️  Please copy to data/accounts.json and add your bot credentials")
        else:
            # Create a basic example
            example_accounts = [
                {
                    "username": "your_bot_username_1",
                    "password": "your_bot_password_1",
                    "note": "Replace with actual credentials"
                },
                {
                    "username": "your_bot_username_2", 
                    "password": "your_bot_password_2",
                    "note": "Add as many accounts as you have (up to 40)"
                }
            ]
            
            with open("data/accounts.json.example", "w") as f:
                json.dump(example_accounts, f, indent=2)
            
            print("  ✓ Created data/accounts.json.example")
            print("    ⚠️  Please copy to data/accounts.json and add your actual credentials")

def check_dependencies():
    """Check if required dependencies are installed."""
    print("\nChecking dependencies...")
    
    required_packages = [
        "requests",
        "aiohttp", 
        "python-dotenv",
        "pydantic",
        "structlog",
        "python-json-logger"
    ]
    
    optional_packages = [
        ("matplotlib", "for analytics visualizations"),
        ("pandas", "for data analysis"),
        ("openai", "for OpenAI API integration"),
        ("anthropic", "for Anthropic API integration")
    ]
    
    missing_required = []
    missing_optional = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"  ✓ {package}")
        except ImportError:
            missing_required.append(package)
            print(f"  ❌ {package} (REQUIRED)")
    
    for package, description in optional_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"  ✓ {package} ({description})")
        except ImportError:
            missing_optional.append((package, description))
            print(f"  ⚠️  {package} (OPTIONAL - {description})")
    
    if missing_required:
        print(f"\n❌ Missing required packages: {', '.join(missing_required)}")
        print("   Install with: pip install " + " ".join(missing_required))
        return False
    
    if missing_optional:
        print(f"\n⚠️  Missing optional packages:")
        for package, description in missing_optional:
            print(f"   - {package}: {description}")
        print("   Install with: pip install " + " ".join([p[0] for p in missing_optional]))
    
    return True

def validate_environment():
    """Validate environment configuration."""
    print("\nValidating environment...")
    
    env_file = Path(".env")
    if not env_file.exists():
        print("  ❌ .env file not found")
        return False
    
    # Read .env file and check for required variables
    required_vars = [
        "TEAM_INVITATION_CODE",
        "CAMPAIGN_OBJECTIVE"
    ]
    
    env_vars = {}
    try:
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
    except Exception as e:
        print(f"  ❌ Error reading .env file: {e}")
        return False
    
    missing_vars = []
    for var in required_vars:
        if var not in env_vars or not env_vars[var] or env_vars[var] == f"your_{var.lower()}_here":
            missing_vars.append(var)
            print(f"  ❌ {var} not configured")
        else:
            # Don't print the actual values for security
            print(f"  ✓ {var} configured")
    
    if missing_vars:
        print(f"\n⚠️  Please configure these variables in .env:")
        for var in missing_vars:
            print(f"   - {var}")
        return False
    
    # Check campaign objective is valid
    campaign_obj = env_vars.get("CAMPAIGN_OBJECTIVE", "")
    valid_objectives = ["support_victor", "support_marina", "voter_disillusionment"]
    
    if campaign_obj not in valid_objectives:
        print(f"  ❌ CAMPAIGN_OBJECTIVE must be one of: {', '.join(valid_objectives)}")
        return False
    
    return True

def check_accounts():
    """Check if accounts are configured."""
    print("\nChecking bot accounts...")
    
    accounts_file = Path("data/accounts.json")
    if not accounts_file.exists():
        print("  ❌ data/accounts.json not found")
        print("     Please create this file with your bot account credentials")
        return False
    
    try:
        with open(accounts_file) as f:
            accounts = json.load(f)
        
        if not isinstance(accounts, list) or len(accounts) == 0:
            print("  ❌ accounts.json must contain a list of account objects")
            return False
        
        valid_accounts = 0
        for i, account in enumerate(accounts):
            if not isinstance(account, dict):
                print(f"  ❌ Account {i+1} is not a valid object")
                continue
            
            if "username" not in account or "password" not in account:
                print(f"  ❌ Account {i+1} missing username or password")
                continue
            
            if not account["username"] or not account["password"]:
                print(f"  ❌ Account {i+1} has empty username or password")
                continue
            
            if account["username"].startswith("your_bot_") or account["password"].startswith("your_bot_"):
                print(f"  ❌ Account {i+1} still has placeholder values")
                continue
            
            valid_accounts += 1
        
        print(f"  ✓ Found {valid_accounts} valid accounts out of {len(accounts)} total")
        
        if valid_accounts == 0:
            print("  ❌ No valid accounts found - please check data/accounts.json")
            return False
        
        if valid_accounts < 5:
            print("  ⚠️  Less than 5 accounts configured - you may want to add more for better performance")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"  ❌ Invalid JSON in accounts.json: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Error reading accounts.json: {e}")
        return False

def run_basic_tests():
    """Run basic system tests."""
    print("\nRunning basic tests...")
    
    try:
        # Test imports
        sys.path.insert(0, "src")
        
        from config.settings import settings
        print("  ✓ Settings module loaded")
        
        from content.generator import ContentGenerator
        print("  ✓ Content generator module loaded")
        
        from bot.influence_bot import InfluenceBot
        print("  ✓ Bot modules loaded")
        
        # Test configuration
        if not settings.personas.get('personas'):
            print("  ❌ No personas configured")
            return False
        
        print(f"  ✓ {len(settings.personas['personas'])} personas configured")
        
        if not settings.content_templates.get('content_templates'):
            print("  ❌ No content templates configured")
            return False
        
        print("  ✓ Content templates configured")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Test error: {e}")
        return False

def print_next_steps():
    """Print next steps for the user."""
    print("\n" + "=" * 60)
    print("🚀 SETUP COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Review and configure .env with your actual values")
    print("2. Add your bot account credentials to data/accounts.json")
    print("3. Test the system:")
    print("   python scripts/deploy_bots.py --test-apis --dry-run")
    print("4. Deploy your bots:")
    print("   python scripts/deploy_bots.py --objective support_victor --bots 10")
    print("5. Monitor performance:")
    print("   python scripts/monitor.py")
    print("6. Generate analytics:")
    print("   python scripts/analytics.py --summary")
    
    print("\n📚 Documentation:")
    print("- See README.md for detailed instructions")
    print("- Check config/personas.json for available bot personalities") 
    print("- Review config/content_templates.json for content strategies")
    
    print("\n🏆 Good luck in the competition!")
    print("=" * 60)

def main():
    """Main setup function."""
    print("🤖 Capture the Narrative Bot System Setup")
    print("=" * 50)
    
    # Step 1: Create directories
    create_directory_structure()
    
    # Step 2: Setup configuration files
    setup_configuration_files()
    
    # Step 3: Check dependencies
    deps_ok = check_dependencies()
    
    if not deps_ok:
        print("\n❌ Please install required dependencies before continuing")
        sys.exit(1)
    
    # Step 4: Validate environment (if .env exists)
    if Path(".env").exists():
        env_ok = validate_environment()
        if not env_ok:
            print("\n⚠️  Environment validation failed - please check .env file")
    
    # Step 5: Check accounts (if file exists)
    if Path("data/accounts.json").exists():
        accounts_ok = check_accounts()
        if not accounts_ok:
            print("\n⚠️  Account validation failed - please check data/accounts.json")
    
    # Step 6: Run basic tests
    tests_ok = run_basic_tests()
    if not tests_ok:
        print("\n⚠️  Basic tests failed - there may be configuration issues")
    
    # Step 7: Print next steps
    print_next_steps()

if __name__ == "__main__":
    main()