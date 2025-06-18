"""
Enhanced logging and monitoring for Hillview School Management System
Provides structured logging, performance monitoring, and scalability insights
"""

import logging
import logging.handlers
import os
import json
import time
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List
from functools import wraps
from collections import defaultdict, deque

class PerformanceMonitor:
    """Monitor application performance metrics"""
    
    def __init__(self, max_samples: int = 1000):
        self.max_samples = max_samples
        self.request_times = deque(maxlen=max_samples)
        self.endpoint_stats = defaultdict(lambda: {'count': 0, 'total_time': 0, 'errors': 0})
        self.error_counts = defaultdict(int)
        self.lock = threading.RLock()
    
    def record_request(self, endpoint: str, duration: float, status_code: int = 200):
        """Record request performance data"""
        with self.lock:
            self.request_times.append(duration)
            stats = self.endpoint_stats[endpoint]
            stats['count'] += 1
            stats['total_time'] += duration
            
            if status_code >= 400:
                stats['errors'] += 1
                self.error_counts[status_code] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        with self.lock:
            if not self.request_times:
                return {'status': 'no_data'}
            
            avg_response_time = sum(self.request_times) / len(self.request_times)
            max_response_time = max(self.request_times)
            min_response_time = min(self.request_times)
            
            # Calculate percentiles
            sorted_times = sorted(self.request_times)
            p95_index = int(0.95 * len(sorted_times))
            p99_index = int(0.99 * len(sorted_times))
            
            endpoint_performance = {}
            for endpoint, stats in self.endpoint_stats.items():
                if stats['count'] > 0:
                    endpoint_performance[endpoint] = {
                        'requests': stats['count'],
                        'avg_time': stats['total_time'] / stats['count'],
                        'error_rate': stats['errors'] / stats['count'] * 100
                    }
            
            return {
                'status': 'healthy',
                'total_requests': len(self.request_times),
                'avg_response_time': round(avg_response_time, 3),
                'min_response_time': round(min_response_time, 3),
                'max_response_time': round(max_response_time, 3),
                'p95_response_time': round(sorted_times[p95_index], 3) if p95_index < len(sorted_times) else 0,
                'p99_response_time': round(sorted_times[p99_index], 3) if p99_index < len(sorted_times) else 0,
                'error_counts': dict(self.error_counts),
                'endpoint_performance': endpoint_performance
            }

class StructuredLogger:
    """Structured logging with JSON output"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.name = name
    
    def log_structured(self, level: int, message: str, **kwargs):
        """Log structured data as JSON"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'logger': self.name,
            'level': logging.getLevelName(level),
            'message': message,
            **kwargs
        }
        
        self.logger.log(level, json.dumps(log_data))
    
    def info(self, message: str, **kwargs):
        """Log info level structured message"""
        self.log_structured(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning level structured message"""
        self.log_structured(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error level structured message"""
        self.log_structured(logging.ERROR, message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug level structured message"""
        self.log_structured(logging.DEBUG, message, **kwargs)

# Global performance monitor
performance_monitor = PerformanceMonitor()

def setup_enhanced_logging(app, log_level: str = 'INFO'):
    """
    Set up enhanced logging configuration for the application.
    
    Args:
        app: Flask application instance
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    # Create logs directory if it doesn't exist
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Convert log level string to logging constant
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR
    }
    log_level_int = level_map.get(log_level.upper(), logging.INFO)
    
    # Create formatters
    standard_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    json_formatter = logging.Formatter(
        '%(message)s'  # For structured logs, message is already JSON
    )
    
    # Standard application log file
    app_log_file = os.path.join(log_dir, 'hillview.log')
    app_file_handler = logging.handlers.RotatingFileHandler(
        app_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    app_file_handler.setLevel(log_level_int)
    app_file_handler.setFormatter(standard_formatter)
    
    # Structured log file for analytics
    structured_log_file = os.path.join(log_dir, 'structured.log')
    structured_file_handler = logging.handlers.RotatingFileHandler(
        structured_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    structured_file_handler.setLevel(logging.INFO)
    structured_file_handler.setFormatter(json_formatter)
    
    # Performance log file
    performance_log_file = os.path.join(log_dir, 'performance.log')
    performance_file_handler = logging.handlers.RotatingFileHandler(
        performance_log_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    performance_file_handler.setLevel(logging.INFO)
    performance_file_handler.setFormatter(standard_formatter)
    
    # Error log file
    error_log_file = os.path.join(log_dir, 'errors.log')
    error_file_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(standard_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level_int)
    console_handler.setFormatter(standard_formatter)
    
    # Configure app logger
    app.logger.setLevel(log_level_int)
    app.logger.addHandler(app_file_handler)
    app.logger.addHandler(console_handler)
    
    # Configure structured logger
    structured_logger = logging.getLogger('structured')
    structured_logger.setLevel(logging.INFO)
    structured_logger.addHandler(structured_file_handler)
    
    # Configure performance logger
    performance_logger = logging.getLogger('performance')
    performance_logger.setLevel(logging.INFO)
    performance_logger.addHandler(performance_file_handler)
    
    # Configure error logger
    error_logger = logging.getLogger('errors')
    error_logger.setLevel(logging.ERROR)
    error_logger.addHandler(error_file_handler)
    
    # Configure werkzeug logger (Flask's built-in server)
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.WARNING)  # Reduce werkzeug verbosity
    
    app.logger.info(f"Enhanced logging configured - Level: {log_level}")
    app.logger.info(f"Log files: {app_log_file}, {structured_log_file}, {performance_log_file}, {error_log_file}")

def performance_monitor_decorator(endpoint_name: str = None):
    """Decorator to monitor function performance"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            endpoint = endpoint_name or func.__name__
            status_code = 200
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status_code = 500
                raise
            finally:
                duration = time.time() - start_time
                performance_monitor.record_request(endpoint, duration, status_code)
                
                # Log slow requests
                if duration > 1.0:  # Log requests taking more than 1 second
                    performance_logger = logging.getLogger('performance')
                    performance_logger.warning(
                        f"Slow request: {endpoint} took {duration:.3f}s"
                    )
        
        return wrapper
    return decorator

def log_user_action(username: str, action: str, details: Optional[Dict[str, Any]] = None, 
                   ip_address: str = None, user_agent: str = None):
    """
    Log user actions for audit purposes with structured data.
    
    Args:
        username: Username of the user performing the action
        action: Description of the action
        details: Additional details about the action
        ip_address: User's IP address
        user_agent: User's browser/client info
    """
    structured_logger = StructuredLogger('user_actions')
    
    log_data = {
        'event_type': 'user_action',
        'username': username,
        'action': action,
        'ip_address': ip_address,
        'user_agent': user_agent
    }
    
    if details:
        log_data['details'] = details
    
    structured_logger.info("User action logged", **log_data)

def log_system_event(event_type: str, message: str, level: int = logging.INFO, 
                    **additional_data):
    """
    Log system events with structured data.
    
    Args:
        event_type: Type of system event
        message: Event message
        level: Logging level (default: INFO)
        **additional_data: Additional structured data
    """
    structured_logger = StructuredLogger('system_events')
    
    log_data = {
        'event_type': event_type,
        'system_event': True,
        **additional_data
    }
    
    structured_logger.log_structured(level, message, **log_data)

def log_error(error: Exception, context: Optional[str] = None, 
             user_id: Optional[str] = None, request_data: Optional[Dict[str, Any]] = None):
    """
    Log errors with enhanced context information.
    
    Args:
        error: The error that occurred
        context: Additional context about when/where the error occurred
        user_id: ID of the user when error occurred
        request_data: Request data when error occurred
    """
    error_logger = logging.getLogger('errors')
    structured_logger = StructuredLogger('errors')
    
    error_message = f"Error: {str(error)}"
    if context:
        error_message = f"{context} - {error_message}"
    
    # Standard error log
    error_logger.error(error_message, exc_info=True)
    
    # Structured error log
    error_data = {
        'event_type': 'error',
        'error_type': type(error).__name__,
        'error_message': str(error),
        'context': context,
        'user_id': user_id
    }
    
    if request_data:
        error_data['request_data'] = request_data
    
    structured_logger.error("Application error occurred", **error_data)

def log_security_event(event_type: str, message: str, severity: str = 'medium',
                      user_id: Optional[str] = None, ip_address: Optional[str] = None,
                      **additional_data):
    """
    Log security-related events.
    
    Args:
        event_type: Type of security event
        message: Security event message
        severity: Event severity (low, medium, high, critical)
        user_id: User ID involved in the event
        ip_address: IP address involved
        **additional_data: Additional security context
    """
    structured_logger = StructuredLogger('security')
    
    log_data = {
        'event_type': 'security_event',
        'security_event_type': event_type,
        'severity': severity,
        'user_id': user_id,
        'ip_address': ip_address,
        **additional_data
    }
    
    # Determine log level based on severity
    level_map = {
        'low': logging.INFO,
        'medium': logging.WARNING,
        'high': logging.ERROR,
        'critical': logging.CRITICAL
    }
    
    level = level_map.get(severity, logging.WARNING)
    structured_logger.log_structured(level, message, **log_data)

def get_performance_stats() -> Dict[str, Any]:
    """Get current performance statistics"""
    return performance_monitor.get_stats()

def log_database_operation(operation: str, table: str, duration: float, 
                          record_count: int = None, user_id: str = None):
    """
    Log database operations for performance monitoring.
    
    Args:
        operation: Type of database operation (SELECT, INSERT, UPDATE, DELETE)
        table: Database table involved
        duration: Operation duration in seconds
        record_count: Number of records affected
        user_id: User performing the operation
    """
    structured_logger = StructuredLogger('database')
    
    log_data = {
        'event_type': 'database_operation',
        'operation': operation,
        'table': table,
        'duration': duration,
        'record_count': record_count,
        'user_id': user_id
    }
    
    # Log slow queries
    level = logging.WARNING if duration > 0.5 else logging.INFO
    
    structured_logger.log_structured(
        level, 
        f"Database {operation} on {table} took {duration:.3f}s", 
        **log_data
    )

if __name__ == "__main__":
    # Test enhanced logging
    print("Testing enhanced logging system...")
    
    # Create a mock Flask app for testing
    class MockApp:
        def __init__(self):
            self.logger = logging.getLogger('test_app')
    
    app = MockApp()
    setup_enhanced_logging(app, 'DEBUG')
    
    # Test structured logging
    log_user_action('test_user', 'login', {'method': 'password'}, '127.0.0.1', 'Test Browser')
    log_system_event('startup', 'Application started successfully', component='main')
    log_security_event('failed_login', 'Multiple failed login attempts', 'high', 'test_user', '127.0.0.1')
    
    # Test performance monitoring
    @performance_monitor_decorator('test_endpoint')
    def test_function():
        time.sleep(0.1)  # Simulate work
        return "test result"
    
    test_function()
    
    # Get performance stats
    stats = get_performance_stats()
    print(f"Performance stats: {stats}")
    
    print("Enhanced logging test completed")
