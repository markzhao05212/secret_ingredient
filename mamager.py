"""
Bot Manager for coordinating multiple influence bots.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from .influence_bot import InfluenceBot
from ..utils.logger import get_logger
from config.settings import settings

class BotManager:
    """
    Manages multiple influence bots and coordinates their activities.
    """
    
    def __init__(self, campaign_objective: str = None):
        """
        Initialize the bot manager.
        
        Args:
            campaign_objective: Overall campaign objective
        """
        self.campaign_objective = campaign_objective or settings.get_campaign_objective()
        self.bots: List[InfluenceBot] = []
        self.active_bots: Dict[str, InfluenceBot] = {}
        self.bot_tasks: Dict[str, asyncio.Task] = {}
        
        self.logger = get_logger("bot_manager")
        
        # Manager state
        self.is_running = False
        self.start_time = None
        self.coordination_interval = 300  # 5 minutes between coordination cycles
        
        # Team statistics
        self.team_stats = {
            'total_posts': 0,
            'total_engagements': 0,
            'unique_npcs_reached': set(),
            'campaign_start_time': None,
            'accounts_used': 0,
            'accounts_banned': 0
        }
        
        # Load account credentials
        self.account_credentials = self._load_account_credentials()
        
        self.logger.info(f"BotManager initialized with objective: {self.campaign_objective}")
    
    def _load_account_credentials(self) -> List[Dict]:
        """Load account credentials from file."""
        credentials_file = Path("data/accounts.json")
        
        if credentials_file.exists():
            try:
                with open(credentials_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load account credentials: {e}")
                return []
        else:
            self.logger.warning("No account credentials file found")
            return []
    
    def create_bot_fleet(self, num_bots: int = None) -> bool:
        """
        Create a fleet of bots with different personas.
        
        Args:
            num_bots: Number of bots to create (default from settings)
            
        Returns:
            bool: True if fleet created successfully
        """
        if num_bots is None:
            num_bots = settings.bot.active_bots
        
        if len(self.account_credentials) < num_bots:
            self.logger.error(f"Not enough account credentials for {num_bots} bots")
            return False
        
        # Available personas
        available_personas = list(settings.personas.get('personas', {}).keys())
        if not available_personas:
            self.logger.error("No personas configured")
            return False
        
        self.logger.info(f"Creating fleet of {num_bots} bots")
        
        for i in range(num_bots):
            if i >= len(self.account_credentials):
                break
                
            credentials = self.account_credentials[i]
            username = credentials.get('username')
            password = credentials.get('password')
            
            if not username or not password:
                self.logger.warning(f"Invalid credentials for bot {i}")
                continue
            
            # Assign persona (distribute evenly across available personas)
            persona = available_personas[i % len(available_personas)]
            
            # Create bot
            bot = InfluenceBot(
                username=username,
                password=password,
                persona_name=persona,
                campaign_objective=self.campaign_objective,
                bot_id=f"bot_{i:03d}_{persona}"
            )
            
            self.bots.append(bot)
            self.team_stats['accounts_used'] += 1
            
            self.logger.info(f"Created bot {i+1}/{num_bots}: {username} ({persona})")
        
        self.logger.info(f"Successfully created {len(self.bots)} bots")
        return len(self.bots) > 0
    
    async def start_campaign(self):
        """Start the coordinated bot campaign."""
        if not self.bots:
            raise Exception("No bots available. Create bot fleet first.")
        
        self.is_running = True
        self.start_time = datetime.now()
        self.team_stats['campaign_start_time'] = self.start_time.isoformat()
        
        self.logger.info(f"Starting campaign with {len(self.bots)} bots")
        
        # Authenticate all bots first
        successful_auths = await self._authenticate_all_bots()
        self.logger.info(f"Successfully authenticated {successful_auths}/{len(self.bots)} bots")
        
        # Start bot tasks
        for bot in self.bots:
            if bot.is_authenticated:
                task = asyncio.create_task(self._run_bot_with_error_handling(bot))
                self.bot_tasks[bot.bot_id] = task
                self.active_bots[bot.bot_id] = bot
        
        # Start coordination task
        coordination_task = asyncio.create_task(self._coordination_loop())
        
        try:
            # Wait for all tasks
            await asyncio.gather(*self.bot_tasks.values(), coordination_task)
        except Exception as e:
            self.logger.error(f"Campaign error: {e}")
        finally:
            await self.stop_campaign()
    
    async def _authenticate_all_bots(self) -> int:
        """Authenticate all bots concurrently."""
        auth_tasks = [bot.authenticate() for bot in self.bots]
        results = await asyncio.gather(*auth_tasks, return_exceptions=True)
        
        successful_count = 0
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Bot {self.bots[i].username} auth failed: {result}")
            elif result:
                successful_count += 1
            else:
                self.logger.warning(f"Bot {self.bots[i].username} authentication returned False")
        
        return successful_count
    
    async def _run_bot_with_error_handling(self, bot: InfluenceBot):
        """Run a single bot with error handling and recovery."""
        max_retries = 3
        retry_count = 0
        
        while self.is_running and retry_count < max_retries:
            try:
                await bot.start()
                break  # Bot completed normally
            except Exception as e:
                retry_count += 1
                self.logger.error(f"Bot {bot.username} error (attempt {retry_count}): {e}")
                
                if retry_count < max_retries:
                    # Wait before retry
                    await asyncio.sleep(60 * retry_count)  # Exponential backoff
                    
                    # Try to re-authenticate
                    try:
                        await bot.authenticate()
                    except:
                        pass
        
        # Remove from active bots if failed permanently
        if retry_count >= max_retries:
            self.logger.warning(f"Bot {bot.username} permanently failed after {max_retries} retries")
            self.active_bots.pop(bot.bot_id, None)
            self.team_stats['accounts_banned'] += 1
    
    async def _coordination_loop(self):
        """Main coordination loop for team strategy."""
        while self.is_running:
            try:
                await self._coordinate_team_strategy()
                await asyncio.sleep(self.coordination_interval)
            except Exception as e:
                self.logger.error(f"Coordination error: {e}")
                await asyncio.sleep(60)  # Shorter retry interval
    
    async def _coordinate_team_strategy(self):
        """Coordinate strategy across all active bots."""
        if not self.active_bots:
            self.logger.warning("No active bots for coordination")
            return
        
        self.logger.debug(f"Coordinating strategy for {len(self.active_bots)} active bots")
        
        # Gather intelligence from all bots
        team_intelligence = await self._gather_team_intelligence()
        
        # Update team statistics
        await self._update_team_statistics()
        
        # Identify coordination opportunities
        opportunities = self._identify_coordination_opportunities(team_intelligence)
        
        # Distribute coordination tasks
        if opportunities:
            await self._distribute_coordination_tasks(opportunities)
        
        # Log team status
        self._log_team_status()
    
    async def _gather_team_intelligence(self) -> Dict:
        """Gather intelligence from all active bots."""
        intelligence = {
            'trending_topics': set(),
            'high_engagement_posts': [],
            'influential_npcs': {},
            'campaign_momentum': {},
            'team_coverage': {}
        }
        
        for bot_id, bot in self.active_bots.items():
            try:
                # Get trending topics from each bot's perspective
                trending = await bot.get_trending_topics()
                intelligence['trending_topics'].update(trending)
                
                # Get bot's influence stats
                bot_stats = bot.get_influence_stats()
                intelligence['campaign_momentum'][bot_id] = bot_stats
                
                # Get environmental intelligence from bot's scanner
                env_data = await bot.scanner.get_intelligence_summary()
                intelligence['team_coverage'][bot_id] = env_data
                
            except Exception as e:
                self.logger.error(f"Failed to gather intelligence from {bot_id}: {e}")
        
        return intelligence
    
    async def _update_team_statistics(self):
        """Update overall team performance statistics."""
        total_posts = 0
        total_engagements = 0
        all_npcs = set()
        
        for bot in self.active_bots.values():
            stats = bot.get_influence_stats()
            total_posts += stats.get('posts_created', 0) + stats.get('replies_made', 0)
            total_engagements += stats.get('likes_given', 0) + stats.get('reposts_made', 0)
            
            # Collect unique NPCs reached
            if hasattr(bot, 'engaged_npcs'):
                all_npcs.update(bot.engaged_npcs)
        
        self.team_stats.update({
            'total_posts': total_posts,
            'total_engagements': total_engagements,
            'unique_npcs_reached': all_npcs,
            'active_bots_count': len(self.active_bots)
        })
    
    def _identify_coordination_opportunities(self, intelligence: Dict) -> List[Dict]:
        """Identify opportunities for coordinated action."""
        opportunities = []
        
        # Trending topic amplification opportunity
        trending_topics = list(intelligence['trending_topics'])
        if trending_topics:
            opportunities.append({
                'type': 'amplify_trending',
                'targets': trending_topics[:3],  # Top 3 trending topics
                'priority': 'high',
                'bot_count': min(3, len(self.active_bots))
            })
        
        # High-impact NPC engagement opportunity
        influential_npcs = intelligence.get('influential_npcs', {})
        if influential_npcs:
            opportunities.append({
                'type': 'coordinated_npc_engagement',
                'targets': list(influential_npcs.keys())[:5],
                'priority': 'medium',
                'bot_count': 2
            })
        
        # Campaign momentum opportunity (if we're in political phase)
        current_phase = self._get_team_current_phase()
        if current_phase == 'political_influence':
            opportunities.append({
                'type': 'campaign_push',
                'objective': self.campaign_objective,
                'priority': 'high',
                'bot_count': len(self.active_bots)
            })
        
        return opportunities
    
    async def _distribute_coordination_tasks(self, opportunities: List[Dict]):
        """Distribute coordination tasks to appropriate bots."""
        available_bots = list(self.active_bots.values())
        
        for opportunity in opportunities:
            opportunity_type = opportunity['type']
            bot_count = min(opportunity['bot_count'], len(available_bots))
            
            if bot_count == 0:
                continue
            
            # Select bots for this opportunity (round-robin style)
            selected_bots = available_bots[:bot_count]
            available_bots = available_bots[bot_count:] + available_bots[:bot_count]
            
            # Send coordination signal to selected bots
            for bot in selected_bots:
                await self._send_coordination_signal(bot, opportunity)
    
    async def _send_coordination_signal(self, bot: InfluenceBot, opportunity: Dict):
        """Send a coordination signal to a specific bot."""
        try:
            # Update the bot's strategy with coordination opportunity
            await bot.strategy.add_coordination_objective(opportunity)
            self.logger.debug(f"Sent coordination signal to {bot.username}: {opportunity['type']}")
        except Exception as e:
            self.logger.error(f"Failed to send coordination signal to {bot.username}: {e}")
    
    def _get_team_current_phase(self) -> str:
        """Get the current phase for the team."""
        if not self.start_time:
            return 'audience_building'
        
        runtime_days = (datetime.now() - self.start_time).days
        
        if runtime_days < settings.bot.audience_building_days:
            return 'audience_building'
        else:
            return 'political_influence'
    
    def _log_team_status(self):
        """Log current team status."""
        runtime = datetime.now() - self.start_time if self.start_time else timedelta(0)
        
        status = {
            'runtime_hours': runtime.total_seconds() / 3600,
            'active_bots': len(self.active_bots),
            'total_bots_created': len(self.bots),
            'accounts_banned': self.team_stats['accounts_banned'],
            'current_phase': self._get_team_current_phase(),
            **{k: v for k, v in self.team_stats.items() if k != 'unique_npcs_reached'}
        }
        status['unique_npcs_count'] = len(self.team_stats['unique_npcs_reached'])
        
        self.logger.info(f"Team Status: {status}")
    
    async def stop_campaign(self):
        """Stop all bot activities gracefully."""
        self.logger.info("Stopping campaign...")
        self.is_running = False
        
        # Stop all bot tasks
        for bot_id, task in self.bot_tasks.items():
            if not task.done():
                task.cancel()
        
        # Stop all bots
        for bot in self.active_bots.values():
            try:
                await bot.stop()
            except Exception as e:
                self.logger.error(f"Error stopping bot {bot.username}: {e}")
        
        # Wait for tasks to complete
        if self.bot_tasks:
            await asyncio.gather(*self.bot_tasks.values(), return_exceptions=True)
        
        self.logger.info("Campaign stopped successfully")
    
    def get_team_performance_report(self) -> Dict:
        """Generate a comprehensive team performance report."""
        runtime = datetime.now() - self.start_time if self.start_time else timedelta(0)
        
        # Individual bot stats
        bot_reports = {}
        for bot in self.bots:
            bot_reports[bot.username] = bot.get_influence_stats()
        
        return {
            'campaign_objective': self.campaign_objective,
            'campaign_runtime_hours': runtime.total_seconds() / 3600,
            'team_summary': {
                **self.team_stats,
                'unique_npcs_count': len(self.team_stats['unique_npcs_reached']),
                'success_rate': len(self.active_bots) / len(self.bots) if self.bots else 0
            },
            'individual_bot_stats': bot_reports,
            'current_phase': self._get_team_current_phase()
        }