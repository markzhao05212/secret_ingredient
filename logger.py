"""
Logging configuration and utilities for the bot system.
"""

import logging
import logging.handlers
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import structlog
from pythonjsonlogger import jsonlogger

from config.settings import settings

# Global logger registry
_loggers: Dict[str, logging.Logger] = {}

class BotFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for bot logs."""
    
    def add_fields(self, log_record: Dict, record: logging.LogRecord, message_dict: Dict):
        """Add custom fields to log records."""
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp
        log_record['timestamp'] = datetime.utcnow().isoformat()
        
        # Add log level
        log_record['level'] = record.levelname
        
        # Add logger name components
        name_parts = record.name.split('.')
        log_record['component'] = name_parts[0] if name_parts else 'unknown'
        if len(name_parts) > 1:
            log_record['subcomponent'] = '.'.join(name_parts[1:])
        
        # Add process info if available
        log_record['process_id'] = record.process
        log_record['thread_id'] = record.thread

class ContextFilter(logging.Filter):
    """Filter to add context information to log records."""
    
    def __init__(self, context: Dict[str, Any] = None):
        """Initialize with context dictionary."""
        super().__init__()
        self.context = context or {}
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add context to log record."""
        for key, value in self.context.items():
            setattr(record, key, value)
        return True

def setup_logging() -> None:
    """Setup logging configuration for the entire application."""
    
    # Ensure log directory exists
    log_file_path = Path(settings.logging.log_file)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.logging.log_level.upper()))
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Console handler with structured logging
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.logging.log_level.upper()))
    
    # Use simple format for console in development
    if settings.logging.log_level.upper() == 'DEBUG':
        console_formatter = logging.Formatter(
            '%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
    else:
        console_formatter = BotFormatter()
    
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with JSON logging
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file_path,
        maxBytes=settings.logging.max_log_size,
        backupCount=settings.logging.backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)  # Always log debug to file
    
    file_formatter = BotFormatter()
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Configure specific loggers
    _configure_library_loggers()
    
    # Log startup message
    logger = get_logger("system")
    logger.info("Logging system initialized", extra={
        'log_level': settings.logging.log_level,
        'log_file': str(log_file_path)
    })

def _configure_library_loggers():
    """Configure logging for third-party libraries."""
    
    # Reduce verbosity of HTTP libraries
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    # Set asyncio to INFO to catch important async issues
    logging.getLogger('asyncio').setLevel(logging.INFO)

def get_logger(name: str, context: Dict[str, Any] = None) -> logging.Logger:
    """
    Get a logger instance with optional context.
    
    Args:
        name: Logger name (e.g., 'bot.username', 'content_generator')
        context: Additional context to include in all log messages
        
    Returns:
        logging.Logger: Configured logger instance
    """
    
    # Create or get logger
    if name not in _loggers:
        logger = logging.getLogger(name)
        
        # Add context filter if provided
        if context:
            context_filter = ContextFilter(context)
            logger.addFilter(context_filter)
        
        _loggers[name] = logger
    
    return _loggers[name]

def get_bot_logger(username: str, bot_id: str = None) -> logging.Logger:
    """
    Get a logger specifically configured for a bot.
    
    Args:
        username: Bot username
        bot_id: Bot identifier
        
    Returns:
        logging.Logger: Bot-specific logger
    """
    logger_name = f"bot.{username}"
    context = {
        'bot_username': username,
        'bot_id': bot_id or username
    }
    
    return get_logger(logger_name, context)

def log_bot_action(logger: logging.Logger, action: str, details: Dict[str, Any] = None, success: bool = True):
    """
    Log a bot action with consistent formatting.
    
    Args:
        logger: Logger to use
        action: Action performed ('post', 'like', 'reply', etc.)
        details: Additional details about the action
        success: Whether the action was successful
    """
    level = logging.INFO if success else logging.WARNING
    
    extra_data = {
        'action_type': action,
        'action_success': success,
        **(details or {})
    }
    
    message = f"{'Completed' if success else 'Failed'} {action}"
    if details and 'target' in details:
        message += f" (target: {details['target']})"
    
    logger.log(level, message, extra=extra_data)

def log_api_request(logger: logging.Logger, 
                   method: str, 
                   url: str, 
                   status_code: int = None, 
                   response_time: float = None,
                   error: str = None):
    """
    Log an API request with consistent formatting.
    
    Args:
        logger: Logger to use
        method: HTTP method
        url: Request URL (will be sanitized)
        status_code: HTTP status code
        response_time: Response time in seconds
        error: Error message if request failed
    """
    
    # Sanitize URL to remove sensitive info
    sanitized_url = _sanitize_url(url)
    
    extra_data = {
        'request_method': method,
        'request_url': sanitized_url,
        'response_status': status_code,
        'response_time': response_time
    }
    
    if error:
        extra_data['error'] = error
        logger.error(f"API request failed: {method} {sanitized_url}", extra=extra_data)
    elif status_code and status_code >= 400:
        logger.warning(f"API request error: {method} {sanitized_url} -> {status_code}", extra=extra_data)
    else:
        logger.debug(f"API request: {method} {sanitized_url} -> {status_code or 'pending'}", extra=extra_data)

def log_performance_metric(logger: logging.Logger, 
                          metric_name: str, 
                          value: float, 
                          unit: str = None,
                          tags: Dict[str, str] = None):
    """
    Log a performance metric.
    
    Args:
        logger: Logger to use
        metric_name: Name of the metric
        value: Metric value
        unit: Unit of measurement
        tags: Additional tags for the metric
    """
    extra_data = {
        'metric_name': metric_name,
        'metric_value': value,
        'metric_unit': unit,
        'metric_tags': tags or {}
    }
    
    message = f"Metric: {metric_name}={value}"
    if unit:
        message += f" {unit}"
    
    logger.info(message, extra=extra_data)

def log_bot_stats(logger: logging.Logger, stats: Dict[str, Any]):
    """
    Log bot statistics in a structured way.
    
    Args:
        logger: Logger to use
        stats: Statistics dictionary
    """
    extra_data = {
        'stats_type': 'bot_performance',
        **stats
    }
    
    # Create summary message
    summary_items = []
    if 'posts_created' in stats:
        summary_items.append(f"{stats['posts_created']} posts")
    if 'likes_given' in stats:
        summary_items.append(f"{stats['likes_given']} likes")
    if 'replies_made' in stats:
        summary_items.append(f"{stats['replies_made']} replies")
    
    summary = ", ".join(summary_items) if summary_items else "no activity"
    
    logger.info(f"Bot stats: {summary}", extra=extra_data)

def _sanitize_url(url: str) -> str:
    """
    Sanitize URL by removing sensitive information.
    
    Args:
        url: Original URL
        
    Returns:
        str: Sanitized URL
    """
    # Remove query parameters that might contain sensitive info
    if '?' in url:
        base_url = url.split('?')[0]
        return f"{base_url}?[params]"
    return url

class BotLoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that adds bot-specific context to all log messages.
    """
    
    def __init__(self, logger: logging.Logger, bot_info: Dict[str, Any]):
        """
        Initialize adapter with bot information.
        
        Args:
            logger: Base logger
            bot_info: Bot information to include in context
        """
        super().__init__(logger, bot_info)
        self.bot_info = bot_info
    
    def process(self, msg, kwargs):
        """Process log message and add bot context."""
        extra = kwargs.get('extra', {})
        extra.update(self.bot_info)
        kwargs['extra'] = extra
        return msg, kwargs
    
    def log_action(self, action: str, success: bool = True, **details):
        """Convenience method for logging bot actions."""
        log_bot_action(self, action, details, success)
    
    def log_api_call(self, method: str, url: str, status_code: int = None, **kwargs):
        """Convenience method for logging API calls."""
        log_api_request(self, method, url, status_code, **kwargs)

def create_bot_logger_adapter(username: str, persona: str, bot_id: str = None) -> BotLoggerAdapter:
    """
    Create a logger adapter for a specific bot.
    
    Args:
        username: Bot username
        persona: Bot persona
        bot_id: Bot identifier
        
    Returns:
        BotLoggerAdapter: Configured adapter
    """
    base_logger = get_bot_logger(username, bot_id)
    
    bot_info = {
        'bot_username': username,
        'bot_persona': persona,
        'bot_id': bot_id or username
    }
    
    return BotLoggerAdapter(base_logger, bot_info)

# Initialize logging on module import
setup_logging()