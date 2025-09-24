#!/usr/bin/env python3
"""
Real-time monitoring dashboard for the bot system.
"""

import asyncio
import json
import time
import sys
from datetime import datetime, timedelta
from pathlib import Path
import argparse
from collections import defaultdict, deque

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.logger import get_logger
from config.settings import settings

class BotMonitor:
    """
    Real-time monitoring system for bot performance and health.
    """
    
    def __init__(self):
        self.logger = get_logger("monitor")
        self.start_time = datetime.now()
        self.metrics_history = deque(maxlen=100)
        self.alert_thresholds = {
            'error_rate': 0.1,  # 10% error rate
            'inactive_bots': 0.3,  # 30% inactive bots
            'low_engagement': 0.05  # 5% engagement rate
        }
        
        # Monitoring state
        self.last_metrics = {}
        self.alerts_sent = set()
        
    async def start_monitoring(self, refresh_interval: int = 30):
        """
        Start the monitoring loop.
        
        Args:
            refresh_interval: Seconds between updates
        """
        self.logger.info(f"Starting bot monitoring (refresh: {refresh_interval}s)")
        
        try:
            while True:
                await self.update_dashboard()
                await asyncio.sleep(refresh_interval)
                
        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
        except Exception as e:
            self.logger.error(f"Monitoring error: {e}")
    
    async def update_dashboard(self):
        """Update and display the monitoring dashboard."""
        # Clear screen
        print("\033[2J\033[H", end="")
        
        # Collect current metrics
        metrics = await self.collect_metrics()
        
        # Display dashboard
        self.display_header()
        self.display_system_status(metrics)
        self.display_bot_status(metrics)
        self.display_performance_metrics(metrics)
        self.display_recent_alerts(metrics)
        
        # Store metrics for trend analysis
        self.metrics_history.append({
            'timestamp': datetime.now(),
            'metrics': metrics
        })
        self.last_metrics = metrics
        
        # Check for alerts
        await self.check_alerts(metrics)
    
    async def collect_metrics(self) -> dict:
        """Collect current system metrics."""
        metrics = {
            'timestamp': datetime.now(),
            'system': await self.collect_system_metrics(),
            'bots': await self.collect_bot_metrics(),
            'api': await self.collect_api_metrics(),
            'content': await self.collect_content_metrics()
        }
        
        return metrics
    
    async def collect_system_metrics(self) -> dict:
        """Collect system-level metrics."""
        log_file = Path(settings.logging.log_file)
        
        system_metrics = {
            'uptime': (datetime.now() - self.start_time).total_seconds(),
            'log_file_size': log_file.stat().st_size if log_file.exists() else 0,
            'memory_usage': 0,  # Could integrate psutil here
            'active_processes': 1
        }
        
        return system_metrics
    
    async def collect_bot_metrics(self) -> dict:
        """Collect bot-specific metrics from log files."""
        bot_metrics = {
            'total_bots': 0,
            'active_bots': 0,
            'inactive_bots': 0,
            'banned_bots': 0,
            'bot_stats': {}
        }
        
        # Parse log files for bot metrics
        log_file = Path(settings.logging.log_file)
        if log_file.exists():
            try:
                # Read recent log entries
                recent_entries = self.get_recent_log_entries(log_file, hours=1)
                
                # Parse bot activity
                bot_activity = defaultdict(list)
                
                for entry in recent_entries:
                    if 'bot_username' in entry:
                        username = entry['bot_username']
                        bot_activity[username].append(entry)
                
                bot_metrics['total_bots'] = len(bot_activity)
                
                # Analyze each bot
                for username, activities in bot_activity.items():
                    last_activity = max(activities, key=lambda x: x.get('timestamp', ''))
                    last_time = datetime.fromisoformat(last_activity.get('timestamp', datetime.now().isoformat()))
                    
                    minutes_since_activity = (datetime.now() - last_time).total_seconds() / 60
                    
                    bot_status = {
                        'last_activity': minutes_since_activity,
                        'recent_actions': len(activities),
                        'status': 'active' if minutes_since_activity < 30 else 'inactive'
                    }
                    
                    # Count error rates
                    errors = [a for a in activities if a.get('level') == 'ERROR']
                    bot_status['error_rate'] = len(errors) / max(1, len(activities))
                    
                    bot_metrics['bot_stats'][username] = bot_status
                    
                    if bot_status['status'] == 'active':
                        bot_metrics['active_bots'] += 1
                    else:
                        bot_metrics['inactive_bots'] += 1
                
            except Exception as e:
                self.logger.error(f"Error collecting bot metrics: {e}")
        
        return bot_metrics
    
    async def collect_api_metrics(self) -> dict:
        """Collect API performance metrics."""
        api_metrics = {
            'total_requests': 0,
            'success_requests': 0,
            'failed_requests': 0,
            'avg_response_time': 0,
            'rate_limit_hits': 0
        }
        
        # Parse API-related log entries
        log_file = Path(settings.logging.log_file)
        if log_file.exists():
            recent_entries = self.get_recent_log_entries(log_file, hours=1)
            
            api_entries = [e for e in recent_entries if 'request_method' in e or 'api' in e.get('component', '')]
            
            response_times = []
            
            for entry in api_entries:
                api_metrics['total_requests'] += 1
                
                if entry.get('response_status'):
                    status = entry['response_status']
                    if 200 <= status < 400:
                        api_metrics['success_requests'] += 1
                    else:
                        api_metrics['failed_requests'] += 1
                    
                    if status == 429:
                        api_metrics['rate_limit_hits'] += 1
                
                if 'response_time' in entry:
                    response_times.append(entry['response_time'])
            
            if response_times:
                api_metrics['avg_response_time'] = sum(response_times) / len(response_times)
        
        return api_metrics
    
    async def collect_content_metrics(self) -> dict:
        """Collect content generation metrics."""
        content_metrics = {
            'posts_created': 0,
            'replies_made': 0,
            'likes_given': 0,
            'reposts_made': 0,
            'content_generation_failures': 0
        }
        
        # Parse content-related log entries
        log_file = Path(settings.logging.log_file)
        if log_file.exists():
            recent_entries = self.get_recent_log_entries(log_file, hours=1)
            
            for entry in recent_entries:
                action_type = entry.get('action_type', '')
                
                if action_type == 'post' and entry.get('action_success'):
                    if entry.get('parent_id'):
                        content_metrics['replies_made'] += 1
                    else:
                        content_metrics['posts_created'] += 1
                elif action_type == 'like' and entry.get('action_success'):
                    content_metrics['likes_given'] += 1
                elif action_type == 'repost' and entry.get('action_success'):
                    content_metrics['reposts_made'] += 1
                
                if 'content_generator' in entry.get('component', '') and entry.get('level') == 'ERROR':
                    content_metrics['content_generation_failures'] += 1
        
        return content_metrics
    
    def get_recent_log_entries(self, log_file: Path, hours: int = 1) -> list:
        """Get recent log entries from the log file."""
        entries = []
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entry_time = datetime.fromisoformat(entry.get('timestamp', ''))
                        
                        if entry_time >= cutoff_time:
                            entries.append(entry)
                    except (json.JSONDecodeError, ValueError):
                        continue
        except Exception as e:
            self.logger.error(f"Error reading log file: {e}")
        
        return entries
    
    def display_header(self):
        """Display dashboard header."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        uptime = datetime.now() - self.start_time
        
        print("=" * 80)
        print(f"🤖 CAPTURE THE NARRATIVE BOT MONITOR")
        print(f"   Time: {now} | Uptime: {self.format_timedelta(uptime)}")
        print("=" * 80)
    
    def display_system_status(self, metrics: dict):
        """Display system status section."""
        system = metrics.get('system', {})
        
        print("\n📊 SYSTEM STATUS")
        print("-" * 40)
        
        uptime_str = self.format_timedelta(timedelta(seconds=system.get('uptime', 0)))
        log_size = self.format_bytes(system.get('log_file_size', 0))
        
        print(f"Uptime:        {uptime_str}")
        print(f"Log Size:      {log_size}")
        print(f"Processes:     {system.get('active_processes', 0)}")
    
    def display_bot_status(self, metrics: dict):
        """Display bot status section."""
        bots = metrics.get('bots', {})
        
        print(f"\n🤖 BOT STATUS")
        print("-" * 40)
        
        total = bots.get('total_bots', 0)
        active = bots.get('active_bots', 0)
        inactive = bots.get('inactive_bots', 0)
        
        print(f"Total Bots:    {total}")
        print(f"Active:        {active} ({self.percentage(active, total)})")
        print(f"Inactive:      {inactive} ({self.percentage(inactive, total)})")
        
        # Show individual bot status
        bot_stats = bots.get('bot_stats', {})
        if bot_stats:
            print(f"\nRecent Activity:")
            for username, stats in list(bot_stats.items())[:5]:  # Show top 5
                status_icon = "✅" if stats['status'] == 'active' else "❌"
                last_activity = stats['last_activity']
                error_rate = stats['error_rate']
                
                print(f"  {status_icon} {username:<15} | "
                      f"Last: {last_activity:4.0f}m | "
                      f"Errors: {error_rate:5.1%}")
    
    def display_performance_metrics(self, metrics: dict):
        """Display performance metrics section."""
        api = metrics.get('api', {})
        content = metrics.get('content', {})
        
        print(f"\n📈 PERFORMANCE METRICS")
        print("-" * 40)
        
        # API metrics
        total_requests = api.get('total_requests', 0)
        success_requests = api.get('success_requests', 0)
        failed_requests = api.get('failed_requests', 0)
        avg_response_time = api.get('avg_response_time', 0)
        rate_limit_hits = api.get('rate_limit_hits', 0)
        
        success_rate = self.percentage(success_requests, total_requests)
        
        print(f"API Requests:  {total_requests}")
        print(f"Success Rate:  {success_rate}")
        print(f"Avg Response:  {avg_response_time:.2f}s")
        print(f"Rate Limits:   {rate_limit_hits}")
        
        # Content metrics
        posts = content.get('posts_created', 0)
        replies = content.get('replies_made', 0)
        likes = content.get('likes_given', 0)
        reposts = content.get('reposts_made', 0)
        
        print(f"\nContent Activity:")
        print(f"Posts:         {posts}")
        print(f"Replies:       {replies}")
        print(f"Likes:         {likes}")
        print(f"Reposts:       {reposts}")
    
    def display_recent_alerts(self, metrics: dict):
        """Display recent alerts and warnings."""
        print(f"\n⚠️  ALERTS & STATUS")
        print("-" * 40)
        
        alerts = []
        
        # Check error rates
        bots = metrics.get('bots', {})
        if bots.get('total_bots', 0) > 0:
            inactive_rate = bots.get('inactive_bots', 0) / bots.get('total_bots', 1)
            if inactive_rate > self.alert_thresholds['inactive_bots']:
                alerts.append(f"High inactive bot rate: {inactive_rate:.1%}")
        
        # Check API performance
        api = metrics.get('api', {})
        if api.get('total_requests', 0) > 10:  # Only if we have meaningful data
            error_rate = api.get('failed_requests', 0) / api.get('total_requests', 1)
            if error_rate > self.alert_thresholds['error_rate']:
                alerts.append(f"High API error rate: {error_rate:.1%}")
        
        # Check rate limiting
        if api.get('rate_limit_hits', 0) > 5:
            alerts.append(f"Frequent rate limiting: {api.get('rate_limit_hits')} hits")
        
        # Display alerts or all-clear
        if alerts:
            for alert in alerts:
                print(f"⚠️  {alert}")
        else:
            print("✅ No alerts - system operating normally")
        
        # Show trends if available
        if len(self.metrics_history) > 1:
            self.display_trends()
    
    def display_trends(self):
        """Display performance trends."""
        if len(self.metrics_history) < 2:
            return
        
        current = self.metrics_history[-1]['metrics']
        previous = self.metrics_history[-2]['metrics']
        
        print(f"\n📊 TRENDS (vs previous check)")
        print("-" * 40)
        
        # Bot activity trend
        current_active = current.get('bots', {}).get('active_bots', 0)
        previous_active = previous.get('bots', {}).get('active_bots', 0)
        
        trend_icon = self.get_trend_icon(current_active, previous_active)
        print(f"Active Bots:   {current_active} {trend_icon}")
        
        # API success rate trend
        current_success = current.get('api', {}).get('success_requests', 0)
        current_total = current.get('api', {}).get('total_requests', 0)
        previous_success = previous.get('api', {}).get('success_requests', 0)
        previous_total = previous.get('api', {}).get('total_requests', 0)
        
        current_rate = current_success / max(1, current_total)
        previous_rate = previous_success / max(1, previous_total)
        
        trend_icon = self.get_trend_icon(current_rate, previous_rate)
        print(f"Success Rate:  {current_rate:.1%} {trend_icon}")
    
    def get_trend_icon(self, current: float, previous: float) -> str:
        """Get trend icon based on comparison."""
        if current > previous:
            return "📈"
        elif current < previous:
            return "📉"
        else:
            return "➡️"
    
    async def check_alerts(self, metrics: dict):
        """Check for alert conditions and log them."""
        # This would integrate with alerting systems
        # For now, just log significant issues
        
        bots = metrics.get('bots', {})
        total_bots = bots.get('total_bots', 0)
        
        if total_bots == 0:
            self.logger.warning("No bot activity detected")
        
        inactive_rate = bots.get('inactive_bots', 0) / max(1, total_bots)
        if inactive_rate > 0.5:  # More than 50% inactive
            self.logger.error(f"High bot inactivity: {inactive_rate:.1%}")
    
    @staticmethod
    def format_timedelta(td: timedelta) -> str:
        """Format timedelta as human-readable string."""
        total_seconds = int(td.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    @staticmethod
    def format_bytes(bytes_count: int) -> str:
        """Format bytes as human-readable string."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_count < 1024.0:
                return f"{bytes_count:.1f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.1f} TB"
    
    @staticmethod
    def percentage(part: int, total: int) -> str:
        """Calculate percentage as string."""
        if total == 0:
            return "0.0%"
        return f"{100 * part / total:.1f}%"

async def main():
    """Main monitoring function."""
    parser = argparse.ArgumentParser(description='Monitor bot system performance')
    parser.add_argument('--interval', type=int, default=30,
                       help='Refresh interval in seconds (default: 30)')
    parser.add_argument('--once', action='store_true',
                       help='Run once and exit')
    
    args = parser.parse_args()
    
    monitor = BotMonitor()
    
    if args.once:
        await monitor.update_dashboard()
    else:
        await monitor.start_monitoring(args.interval)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
    except Exception as e:
        print(f"Monitor error: {e}")
        sys.exit(1)