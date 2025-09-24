#!/usr/bin/env python3
"""
Analytics and reporting system for bot performance analysis.
"""

import json
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import pandas as pd

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.logger import get_logger
from config.settings import settings

class BotAnalytics:
    """
    Analytics engine for bot performance analysis and reporting.
    """
    
    def __init__(self):
        self.logger = get_logger("analytics")
        self.data_dir = Path("data")
        self.logs_dir = self.data_dir / "logs"
        self.performance_dir = self.data_dir / "performance"
        
        # Ensure directories exist
        self.performance_dir.mkdir(parents=True, exist_ok=True)
        
        self.metrics_cache = {}
        
    def generate_comprehensive_report(self, hours: int = 24) -> Dict[str, Any]:
        """
        Generate comprehensive analytics report.
        
        Args:
            hours: Hours of data to analyze
            
        Returns:
            Dict: Comprehensive analytics report
        """
        self.logger.info(f"Generating analytics report for last {hours} hours")
        
        report = {
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'analysis_period_hours': hours,
                'data_sources': []
            },
            'executive_summary': {},
            'bot_performance': {},
            'content_analysis': {},
            'engagement_metrics': {},
            'api_performance': {},
            'strategic_insights': {},
            'recommendations': []
        }
        
        try:
            # Load and process data
            log_data = self.load_log_data(hours)
            report['report_metadata']['data_sources'].append(f"Logs: {len(log_data)} entries")
            
            # Generate each report section
            report['executive_summary'] = self.generate_executive_summary(log_data)
            report['bot_performance'] = self.analyze_bot_performance(log_data)
            report['content_analysis'] = self.analyze_content_performance(log_data)
            report['engagement_metrics'] = self.analyze_engagement_metrics(log_data)
            report['api_performance'] = self.analyze_api_performance(log_data)
            report['strategic_insights'] = self.generate_strategic_insights(log_data)
            report['recommendations'] = self.generate_recommendations(report)
            
            # Save report
            self.save_report(report)
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            return report
    
    def load_log_data(self, hours: int) -> List[Dict]:
        """Load and parse log data from the specified time period."""
        log_file = Path(settings.logging.log_file)
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        entries = []
        
        if not log_file.exists():
            self.logger.warning(f"Log file not found: {log_file}")
            return entries
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entry_time = datetime.fromisoformat(entry.get('timestamp', ''))
                        
                        if entry_time >= cutoff_time:
                            entries.append(entry)
                    except (json.JSONDecodeError, ValueError) as e:
                        continue
            
            self.logger.info(f"Loaded {len(entries)} log entries")
            
        except Exception as e:
            self.logger.error(f"Error loading log data: {e}")
        
        return entries
    
    def generate_executive_summary(self, log_data: List[Dict]) -> Dict:
        """Generate executive summary of bot performance."""
        summary = {
            'total_log_entries': len(log_data),
            'active_bots': set(),
            'total_actions': 0,
            'success_rate': 0.0,
            'content_created': 0,
            'engagements_made': 0,
            'api_calls': 0,
            'error_rate': 0.0,
            'top_performing_bots': [],
            'campaign_effectiveness': 'unknown'
        }
        
        successful_actions = 0
        total_actions = 0
        errors = 0
        
        bot_activity = defaultdict(int)
        
        for entry in log_data:
            # Track active bots
            if 'bot_username' in entry:
                summary['active_bots'].add(entry['bot_username'])
                bot_activity[entry['bot_username']] += 1
            
            # Count actions
            if 'action_type' in entry:
                total_actions += 1
                summary['total_actions'] += 1
                
                if entry.get('action_success', False):
                    successful_actions += 1
                    
                    action_type = entry['action_type']
                    if action_type in ['post', 'reply']:
                        summary['content_created'] += 1
                    elif action_type in ['like', 'repost', 'follow']:
                        summary['engagements_made'] += 1
            
            # Count API calls
            if 'request_method' in entry:
                summary['api_calls'] += 1
            
            # Count errors
            if entry.get('level') == 'ERROR':
                errors += 1
        
        # Calculate rates
        summary['active_bots'] = len(summary['active_bots'])
        summary['success_rate'] = successful_actions / max(1, total_actions)
        summary['error_rate'] = errors / max(1, len(log_data))
        
        # Top performing bots
        summary['top_performing_bots'] = [
            {'username': username, 'activity_count': count}
            for username, count in Counter(bot_activity).most_common(5)
        ]
        
        return summary
    
    def analyze_bot_performance(self, log_data: List[Dict]) -> Dict:
        """Analyze individual bot performance."""
        bot_stats = defaultdict(lambda: {
            'total_actions': 0,
            'successful_actions': 0,
            'posts_created': 0,
            'replies_made': 0,
            'likes_given': 0,
            'reposts_made': 0,
            'follows_made': 0,
            'errors': 0,
            'last_activity': None,
            'success_rate': 0.0,
            'error_rate': 0.0,
            'persona': 'unknown'
        })
        
        for entry in log_data:
            username = entry.get('bot_username')
            if not username:
                continue
            
            bot_stat = bot_stats[username]
            
            # Track persona
            if 'bot_persona' in entry:
                bot_stat['persona'] = entry['bot_persona']
            
            # Track activity timestamp
            timestamp = entry.get('timestamp')
            if timestamp:
                if not bot_stat['last_activity'] or timestamp > bot_stat['last_activity']:
                    bot_stat['last_activity'] = timestamp
            
            # Track actions
            if 'action_type' in entry:
                action_type = entry['action_type']
                bot_stat['total_actions'] += 1
                
                if entry.get('action_success', False):
                    bot_stat['successful_actions'] += 1
                    
                    if action_type == 'post':
                        if entry.get('parent_id'):
                            bot_stat['replies_made'] += 1
                        else:
                            bot_stat['posts_created'] += 1
                    elif action_type == 'like':
                        bot_stat['likes_given'] += 1
                    elif action_type == 'repost':
                        bot_stat['reposts_made'] += 1
                    elif action_type == 'follow':
                        bot_stat['follows_made'] += 1
            
            # Track errors
            if entry.get('level') == 'ERROR':
                bot_stat['errors'] += 1
        
        # Calculate rates for each bot
        for username, stats in bot_stats.items():
            stats['success_rate'] = stats['successful_actions'] / max(1, stats['total_actions'])
            stats['error_rate'] = stats['errors'] / max(1, stats['total_actions'])
        
        return dict(bot_stats)
    
    def analyze_content_performance(self, log_data: List[Dict]) -> Dict:
        """Analyze content generation and posting performance."""
        content_stats = {
            'total_posts': 0,
            'total_replies': 0,
            'political_posts': 0,
            'neutral_posts': 0,
            'content_generation_failures': 0,
            'average_post_length': 0,
            'content_types': Counter(),
            'persona_content_distribution': defaultdict(int),
            'objective_content_distribution': defaultdict(int),
            'posting_patterns': {
                'hourly_distribution': defaultdict(int),
                'daily_patterns': defaultdict(int)
            }
        }
        
        post_lengths = []
        
        for entry in log_data:
            # Track content generation
            if 'content_generator' in entry.get('component', ''):
                if entry.get('level') == 'ERROR':
                    content_stats['content_generation_failures'] += 1
            
            # Track posting actions
            if entry.get('action_type') == 'post' and entry.get('action_success'):
                if entry.get('parent_id'):
                    content_stats['total_replies'] += 1
                else:
                    content_stats['total_posts'] += 1
                
                # Track content by persona
                persona = entry.get('bot_persona', 'unknown')
                content_stats['persona_content_distribution'][persona] += 1
                
                # Track posting time patterns
                timestamp = entry.get('timestamp')
                if timestamp:
                    dt = datetime.fromisoformat(timestamp)
                    hour = dt.hour
                    day = dt.strftime('%A')
                    content_stats['posting_patterns']['hourly_distribution'][hour] += 1
                    content_stats['posting_patterns']['daily_patterns'][day] += 1
        
        # Calculate averages
        if post_lengths:
            content_stats['average_post_length'] = sum(post_lengths) / len(post_lengths)
        
        return content_stats
    
    def analyze_engagement_metrics(self, log_data: List[Dict]) -> Dict:
        """Analyze engagement activities and effectiveness."""
        engagement_stats = {
            'total_likes': 0,
            'total_reposts': 0,
            'total_follows': 0,
            'engagement_success_rate': 0.0,
            'npc_interactions': 0,
            'trending_engagements': 0,
            'engagement_by_persona': defaultdict(int),
            'target_analysis': {
                'unique_targets': set(),
                'repeat_targets': defaultdict(int)
            }
        }
        
        total_engagement_attempts = 0
        successful_engagements = 0
        
        for entry in log_data:
            action_type = entry.get('action_type')
            
            if action_type in ['like', 'repost', 'follow']:
                total_engagement_attempts += 1
                persona = entry.get('bot_persona', 'unknown')
                
                if entry.get('action_success'):
                    successful_engagements += 1
                    
                    if action_type == 'like':
                        engagement_stats['total_likes'] += 1
                    elif action_type == 'repost':
                        engagement_stats['total_reposts'] += 1
                    elif action_type == 'follow':
                        engagement_stats['total_follows'] += 1
                    
                    engagement_stats['engagement_by_persona'][persona] += 1
                    
                    # Track targets
                    target = entry.get('target')
                    if target:
                        engagement_stats['target_analysis']['unique_targets'].add(target)
                        engagement_stats['target_analysis']['repeat_targets'][target] += 1
        
        # Calculate success rate
        engagement_stats['engagement_success_rate'] = (
            successful_engagements / max(1, total_engagement_attempts)
        )
        
        # Convert sets to counts for JSON serialization
        engagement_stats['target_analysis']['unique_targets'] = len(
            engagement_stats['target_analysis']['unique_targets']
        )
        
        return engagement_stats
    
    def analyze_api_performance(self, log_data: List[Dict]) -> Dict:
        """Analyze API call performance and reliability."""
        api_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'rate_limit_hits': 0,
            'average_response_time': 0.0,
            'success_rate': 0.0,
            'response_time_distribution': {
                'fast': 0,     # < 1s
                'normal': 0,   # 1-3s
                'slow': 0,     # 3-10s
                'very_slow': 0 # > 10s
            },
            'endpoint_performance': defaultdict(lambda: {
                'requests': 0,
                'successes': 0,
                'failures': 0,
                'avg_response_time': 0.0
            }),
            'error_analysis': Counter()
        }
        
        response_times = []
        endpoint_response_times = defaultdict(list)
        
        for entry in log_data:
            if 'request_method' not in entry and 'api' not in entry.get('component', ''):
                continue
            
            api_stats['total_requests'] += 1
            
            # Track response status
            status_code = entry.get('response_status')
            if status_code:
                if 200 <= status_code < 400:
                    api_stats['successful_requests'] += 1
                else:
                    api_stats['failed_requests'] += 1
                    
                    if status_code == 429:
                        api_stats['rate_limit_hits'] += 1
                    
                    # Track error types
                    if status_code >= 400:
                        api_stats['error_analysis'][f"HTTP_{status_code}"] += 1
            
            # Track response times
            response_time = entry.get('response_time')
            if response_time:
                response_times.append(response_time)
                
                # Categorize response time
                if response_time < 1:
                    api_stats['response_time_distribution']['fast'] += 1
                elif response_time < 3:
                    api_stats['response_time_distribution']['normal'] += 1
                elif response_time < 10:
                    api_stats['response_time_distribution']['slow'] += 1
                else:
                    api_stats['response_time_distribution']['very_slow'] += 1
                
                # Track by endpoint
                endpoint = entry.get('request_url', 'unknown')
                endpoint_response_times[endpoint].append(response_time)
        
        # Calculate averages
        if response_times:
            api_stats['average_response_time'] = sum(response_times) / len(response_times)
        
        api_stats['success_rate'] = (
            api_stats['successful_requests'] / max(1, api_stats['total_requests'])
        )
        
        # Calculate endpoint averages
        for endpoint, times in endpoint_response_times.items():
            api_stats['endpoint_performance'][endpoint]['avg_response_time'] = (
                sum(times) / len(times)
            )
        
        return api_stats
    
    def generate_strategic_insights(self, log_data: List[Dict]) -> Dict:
        """Generate strategic insights and campaign analysis."""
        insights = {
            'campaign_momentum': 'stable',
            'most_effective_personas': [],
            'content_strategy_effectiveness': 'unknown',
            'engagement_opportunities': [],
            'risk_factors': [],
            'performance_trends': {}
        }
        
        # Analyze persona effectiveness
        persona_performance = defaultdict(lambda: {'actions': 0, 'successes': 0})
        
        for entry in log_data:
            persona = entry.get('bot_persona')
            if persona and 'action_type' in entry:
                persona_performance[persona]['actions'] += 1
                if entry.get('action_success'):
                    persona_performance[persona]['successes'] += 1
        
        # Calculate persona success rates
        persona_effectiveness = []
        for persona, stats in persona_performance.items():
            if stats['actions'] > 0:
                success_rate = stats['successes'] / stats['actions']
                persona_effectiveness.append({
                    'persona': persona,
                    'success_rate': success_rate,
                    'total_actions': stats['actions']
                })
        
        # Sort by effectiveness
        persona_effectiveness.sort(key=lambda x: x['success_rate'], reverse=True)
        insights['most_effective_personas'] = persona_effectiveness[:3]
        
        # Identify risk factors
        error_rate = len([e for e in log_data if e.get('level') == 'ERROR']) / max(1, len(log_data))
        if error_rate > 0.1:  # 10% error rate
            insights['risk_factors'].append(f"High error rate: {error_rate:.1%}")
        
        rate_limit_hits = len([e for e in log_data if e.get('response_status') == 429])
        if rate_limit_hits > 10:
            insights['risk_factors'].append(f"Frequent rate limiting: {rate_limit_hits} hits")
        
        return insights
    
    def generate_recommendations(self, report: Dict) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        summary = report.get('executive_summary', {})
        bot_performance = report.get('bot_performance', {})
        api_performance = report.get('api_performance', {})
        
        # Performance-based recommendations
        success_rate = summary.get('success_rate', 0)
        if success_rate < 0.7:  # Less than 70% success rate
            recommendations.append(
                f"Improve action success rate ({success_rate:.1%} currently). "
                "Review error logs and adjust bot strategies."
            )
        
        # Bot activity recommendations
        if summary.get('active_bots', 0) < settings.bot.active_bots * 0.8:
            recommendations.append(
                "Some bots appear inactive. Check authentication and network connectivity."
            )
        
        # API performance recommendations
        api_success_rate = api_performance.get('success_rate', 0)
        if api_success_rate < 0.9:  # Less than 90% API success
            recommendations.append(
                f"API reliability concerns ({api_success_rate:.1%} success rate). "
                "Consider implementing more robust retry logic."
            )
        
        # Rate limiting recommendations
        rate_limit_hits = api_performance.get('rate_limit_hits', 0)
        if rate_limit_hits > 20:
            recommendations.append(
                f"High rate limiting ({rate_limit_hits} hits). "
                "Reduce bot activity frequency or improve rate limiting logic."
            )
        
        # Content recommendations
        content_stats = report.get('content_analysis', {})
        if content_stats.get('content_generation_failures', 0) > 10:
            recommendations.append(
                "Multiple content generation failures detected. "
                "Check LLM API connectivity and template fallbacks."
            )
        
        return recommendations
    
    def save_report(self, report: Dict):
        """Save report to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.performance_dir / f"analytics_report_{timestamp}.json"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str)
            
            self.logger.info(f"Analytics report saved to: {report_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save report: {e}")
    
    def create_visualizations(self, report: Dict, output_dir: Path = None):
        """Create visualizations from report data."""
        if output_dir is None:
            output_dir = self.performance_dir / "charts"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Bot performance chart
            self.create_bot_performance_chart(report, output_dir)
            
            # API performance chart
            self.create_api_performance_chart(report, output_dir)
            
            # Content analysis chart
            self.create_content_analysis_chart(report, output_dir)
            
            self.logger.info(f"Visualizations saved to: {output_dir}")
            
        except ImportError:
            self.logger.warning("Matplotlib not available - skipping visualizations")
        except Exception as e:
            self.logger.error(f"Error creating visualizations: {e}")
    
    def create_bot_performance_chart(self, report: Dict, output_dir: Path):
        """Create bot performance visualization."""
        bot_performance = report.get('bot_performance', {})
        
        if not bot_performance:
            return
        
        usernames = []
        success_rates = []
        total_actions = []
        
        for username, stats in bot_performance.items():
            usernames.append(username[:10])  # Truncate long usernames
            success_rates.append(stats['success_rate'] * 100)
            total_actions.append(stats['total_actions'])
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Success rates
        ax1.bar(usernames, success_rates)
        ax1.set_title('Bot Success Rates')
        ax1.set_ylabel('Success Rate (%)')
        ax1.set_xticklabels(usernames, rotation=45)
        
        # Total actions
        ax2.bar(usernames, total_actions)
        ax2.set_title('Bot Activity Levels')
        ax2.set_ylabel('Total Actions')
        ax2.set_xticklabels(usernames, rotation=45)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'bot_performance.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_api_performance_chart(self, report: Dict, output_dir: Path):
        """Create API performance visualization."""
        api_performance = report.get('api_performance', {})
        
        response_dist = api_performance.get('response_time_distribution', {})
        
        if not response_dist:
            return
        
        labels = ['Fast (<1s)', 'Normal (1-3s)', 'Slow (3-10s)', 'Very Slow (>10s)']
        values = [
            response_dist.get('fast', 0),
            response_dist.get('normal', 0),
            response_dist.get('slow', 0),
            response_dist.get('very_slow', 0)
        ]
        
        plt.figure(figsize=(10, 6))
        plt.pie(values, labels=labels, autopct='%1.1f%%')
        plt.title('API Response Time Distribution')
        plt.savefig(output_dir / 'api_response_times.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_content_analysis_chart(self, report: Dict, output_dir: Path):
        """Create content analysis visualization."""
        content_stats = report.get('content_analysis', {})
        
        persona_dist = content_stats.get('persona_content_distribution', {})
        
        if not persona_dist:
            return
        
        personas = list(persona_dist.keys())
        counts = list(persona_dist.values())
        
        plt.figure(figsize=(12, 6))
        plt.bar(personas, counts)
        plt.title('Content Creation by Persona')
        plt.ylabel('Posts Created')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(output_dir / 'content_by_persona.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def print_summary_report(self, report: Dict):
        """Print a formatted summary report to console."""
        print("\n" + "=" * 80)
        print("🤖 BOT SYSTEM ANALYTICS REPORT")
        print("=" * 80)
        
        # Executive Summary
        summary = report.get('executive_summary', {})
        print(f"\n📊 EXECUTIVE SUMMARY")
        print(f"   Active Bots: {summary.get('active_bots', 0)}")
        print(f"   Total Actions: {summary.get('total_actions', 0)}")
        print(f"   Success Rate: {summary.get('success_rate', 0):.1%}")
        print(f"   Content Created: {summary.get('content_created', 0)}")
        print(f"   Engagements: {summary.get('engagements_made', 0)}")
        
        # Top Performers
        top_bots = summary.get('top_performing_bots', [])
        if top_bots:
            print(f"\n🏆 TOP PERFORMING BOTS")
            for i, bot in enumerate(top_bots[:3], 1):
                print(f"   {i}. {bot['username']}: {bot['activity_count']} actions")
        
        # API Performance
        api_perf = report.get('api_performance', {})
        print(f"\n🌐 API PERFORMANCE")
        print(f"   Total Requests: {api_perf.get('total_requests', 0)}")
        print(f"   Success Rate: {api_perf.get('success_rate', 0):.1%}")
        print(f"   Avg Response Time: {api_perf.get('average_response_time', 0):.2f}s")
        print(f"   Rate Limit Hits: {api_perf.get('rate_limit_hits', 0)}")
        
        # Recommendations
        recommendations = report.get('recommendations', [])
        if recommendations:
            print(f"\n💡 RECOMMENDATIONS")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        
        print("\n" + "=" * 80)


def main():
    """Main analytics function."""
    parser = argparse.ArgumentParser(description='Bot system analytics')
    parser.add_argument('--hours', type=int, default=24,
                       help='Hours of data to analyze (default: 24)')
    parser.add_argument('--output', type=str,
                       help='Output directory for reports and charts')
    parser.add_argument('--charts', action='store_true',
                       help='Generate visualization charts')
    parser.add_argument('--summary', action='store_true',
                       help='Print summary report to console')
    
    args = parser.parse_args()
    
    analytics = BotAnalytics()
    
    # Generate comprehensive report
    report = analytics.generate_comprehensive_report(args.hours)
    
    # Print summary if requested
    if args.summary:
        analytics.print_summary_report(report)
    
    # Generate charts if requested
    if args.charts:
        output_dir = Path(args.output) if args.output else None
        analytics.create_visualizations(report, output_dir)
    
    print(f"\nFull report saved to: data/performance/")


if __name__ == "__main__":
    main()