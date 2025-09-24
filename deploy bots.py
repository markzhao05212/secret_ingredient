#!/usr/bin/env python3
"""
Main deployment script for the Capture the Narrative bot system.
"""

import asyncio
import argparse
import json
import sys
import signal
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from bot.bot_manager import BotManager
from utils.logger import get_logger, setup_logging
from config.settings import settings

# Global variables for cleanup
bot_manager = None
logger = None

async def main():
    """Main deployment function."""
    global bot_manager, logger
    
    # Setup argument parsing
    parser = argparse.ArgumentParser(description='Deploy Capture the Narrative bots')
    parser.add_argument('--objective', 
                       choices=['support_victor', 'support_marina', 'voter_disillusionment'],
                       default=settings.get_campaign_objective(),
                       help='Campaign objective')
    parser.add_argument('--bots', type=int, default=settings.bot.active_bots,
                       help='Number of bots to deploy')
    parser.add_argument('--test-apis', action='store_true',
                       help='Test API connections before deployment')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show configuration without starting bots')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    logger = get_logger("deployment")
    
    logger.info("=" * 60)
    logger.info("🤖 CAPTURE THE NARRATIVE BOT DEPLOYMENT 🤖")
    logger.info("=" * 60)
    
    # Display configuration
    await display_configuration(args)
    
    if args.dry_run:
        logger.info("Dry run completed. Exiting without starting bots.")
        return
    
    # Test APIs if requested
    if args.test_apis:
        await test_api_connections()
    
    # Validate accounts
    if not await validate_accounts(args.bots):
        return
    
    # Create and start bot manager
    try:
        bot_manager = BotManager(campaign_objective=args.objective)
        
        # Setup signal handlers for graceful shutdown
        setup_signal_handlers()
        
        # Create bot fleet
        logger.info(f"Creating fleet of {args.bots} bots...")
        if not bot_manager.create_bot_fleet(args.bots):
            logger.error("Failed to create bot fleet")
            return
        
        # Start the campaign
        logger.info(f"Starting campaign with objective: {args.objective}")
        logger.info("Press Ctrl+C to stop the campaign gracefully")
        
        await bot_manager.start_campaign()
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        raise
    finally:
        await cleanup()

async def display_configuration(args):
    """Display current configuration."""
    logger.info("Configuration:")
    logger.info(f"  Campaign Objective: {args.objective}")
    logger.info(f"  Number of Bots: {args.bots}")
    logger.info(f"  Platform URL: {settings.api.platform_url}")
    logger.info(f"  LLM API: {settings.api.llm_api_url}")
    logger.info(f"  Rate Limit: {settings.api.rate_limit_requests} requests per {settings.api.rate_limit_window}s")
    logger.info(f"  Log Level: {settings.logging.log_level}")
    
    # Display persona information
    personas = list(settings.personas.get('personas', {}).keys())
    logger.info(f"  Available Personas: {', '.join(personas) if personas else 'None configured'}")
    
    if not personas:
        logger.warning("⚠️  No personas configured! Check config/personas.json")
    
    # Check for required environment variables
    required_vars = ['TEAM_INVITATION_CODE']
    missing_vars = []
    
    for var in required_vars:
        if not getattr(settings.api, var.lower(), None):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")

async def test_api_connections():
    """Test API connections before deployment."""
    logger.info("Testing API connections...")
    
    # Test LLM APIs
    from api.llm_client import LLMClient
    
    llm_client = LLMClient()
    
    logger.info("Testing LLM APIs...")
    api_results = await llm_client.test_all_apis()
    
    for api_name, is_working in api_results.items():
        status = "✅ WORKING" if is_working else "❌ FAILED"
        logger.info(f"  {api_name.upper()}: {status}")
    
    if not any(api_results.values()):
        logger.error("❌ No working LLM APIs found!")
        return False
    
    # Test Legit Social platform (basic connectivity)
    logger.info("Testing Legit Social platform connectivity...")
    
    from api.legit_social import LegitSocialAPI
    
    api = LegitSocialAPI()
    
    try:
        # Just test if we can reach the platform
        async with api:
            # This will test basic connectivity
            trending = await api.get_trending()
            logger.info("✅ Legit Social platform: REACHABLE")
    except Exception as e:
        logger.error(f"❌ Legit Social platform: FAILED ({e})")
        return False
    
    logger.info("✅ All API tests completed")
    return True

async def validate_accounts(num_bots):
    """Validate that we have enough accounts configured."""
    accounts_file = Path("data/accounts.json")
    
    if not accounts_file.exists():
        logger.error("❌ No accounts file found at data/accounts.json")
        logger.info("Please create this file with your bot account credentials:")
        logger.info("""
[
    {"username": "bot1", "password": "password1"},
    {"username": "bot2", "password": "password2"},
    ...
]
""")
        return False
    
    try:
        with open(accounts_file, 'r') as f:
            accounts = json.load(f)
        
        if len(accounts) < num_bots:
            logger.error(f"❌ Need {num_bots} accounts but only {len(accounts)} configured")
            return False
        
        # Validate account structure
        for i, account in enumerate(accounts[:num_bots]):
            if not isinstance(account, dict) or 'username' not in account or 'password' not in account:
                logger.error(f"❌ Invalid account format at index {i}")
                return False
        
        logger.info(f"✅ {len(accounts)} accounts configured, {num_bots} will be used")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to validate accounts: {e}")
        return False

def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown."""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        # The actual cleanup will happen in the finally block of main()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

async def cleanup():
    """Clean up resources."""
    global bot_manager
    
    if bot_manager:
        logger.info("Shutting down bot manager...")
        try:
            await bot_manager.stop_campaign()
            
            # Generate final report
            report = bot_manager.get_team_performance_report()
            
            logger.info("=" * 50)
            logger.info("FINAL CAMPAIGN REPORT")
            logger.info("=" * 50)
            
            summary = report.get('team_summary', {})
            logger.info(f"Campaign Runtime: {summary.get('campaign_runtime_hours', 0):.2f} hours")
            logger.info(f"Total Posts Created: {summary.get('total_posts', 0)}")
            logger.info(f"Total Engagements: {summary.get('total_engagements', 0)}")
            logger.info(f"Unique NPCs Reached: {summary.get('unique_npcs_count', 0)}")
            logger.info(f"Success Rate: {summary.get('success_rate', 0):.1%}")
            
            # Save detailed report
            report_file = Path("data/logs") / f"campaign_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            report_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Detailed report saved to: {report_file}")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    logger.info("🏁 Deployment shutdown complete")

async def quick_test():
    """Quick test function for development."""
    logger.info("Running quick test...")
    
    # Test basic imports and configuration
    try:
        from bot.influence_bot import InfluenceBot
        from content.generator import ContentGenerator
        from intelligence.scanner import EnvironmentalScanner
        
        logger.info("✅ All imports successful")
        
        # Test content generation
        generator = ContentGenerator("young_professional")
        content = await generator.generate_content(
            content_type="audience_building",
            persona="young_professional",
            objective="support_victor"
        )
        
        if content:
            logger.info(f"✅ Content generation test: '{content[:50]}...'")
        else:
            logger.warning("⚠️  Content generation returned None")
        
    except Exception as e:
        logger.error(f"❌ Quick test failed: {e}")
        raise

if __name__ == "__main__":
    # Check if this is a quick test
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        asyncio.run(quick_test())
    else:
        asyncio.run(main())