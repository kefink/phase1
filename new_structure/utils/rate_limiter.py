"""
Rate Limiting for Hillview School Management System
Implements API rate limiting to prevent abuse and ensure fair resource usage
"""

import time
import threading
import hashlib
import logging
from typing import Dict, Any, Optional, Tuple, List
from collections import defaultdict, deque
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded"""
    def __init__(self, message: str, retry_after: int = None):
        self.message = message
        self.retry_after = retry_after
        super().__init__(message)

class TokenBucket:
    """Token bucket algorithm for rate limiting"""
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket
        
        Args:
            capacity: Maximum number of tokens
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = threading.RLock()
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from bucket
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False otherwise
        """
        with self.lock:
            now = time.time()
            # Add tokens based on time elapsed
            time_passed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + time_passed * self.refill_rate)
            self.last_refill = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def get_wait_time(self, tokens: int = 1) -> float:
        """Get time to wait before tokens are available"""
        with self.lock:
            if self.tokens >= tokens:
                return 0
            needed_tokens = tokens - self.tokens
            return needed_tokens / self.refill_rate

class SlidingWindowCounter:
    """Sliding window counter for rate limiting"""
    
    def __init__(self, window_size: int, max_requests: int):
        """
        Initialize sliding window counter
        
        Args:
            window_size: Window size in seconds
            max_requests: Maximum requests in window
        """
        self.window_size = window_size
        self.max_requests = max_requests
        self.requests = deque()
        self.lock = threading.RLock()
    
    def is_allowed(self) -> Tuple[bool, int]:
        """
        Check if request is allowed
        
        Returns:
            Tuple of (is_allowed, requests_in_window)
        """
        with self.lock:
            now = time.time()
            # Remove old requests outside window
            while self.requests and self.requests[0] <= now - self.window_size:
                self.requests.popleft()
            
            current_requests = len(self.requests)
            
            if current_requests < self.max_requests:
                self.requests.append(now)
                return True, current_requests + 1
            
            return False, current_requests
    
    def get_reset_time(self) -> int:
        """Get time when window resets"""
        with self.lock:
            if not self.requests:
                return 0
            return int(self.requests[0] + self.window_size)

class InMemoryRateLimitStore:
    """In-memory storage for rate limiting data"""
    
    def __init__(self):
        self.buckets = {}
        self.counters = {}
        self.lock = threading.RLock()
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
    
    def get_bucket(self, key: str, capacity: int, refill_rate: float) -> TokenBucket:
        """Get or create token bucket for key"""
        with self.lock:
            if key not in self.buckets:
                self.buckets[key] = TokenBucket(capacity, refill_rate)
            return self.buckets[key]
    
    def get_counter(self, key: str, window_size: int, max_requests: int) -> SlidingWindowCounter:
        """Get or create sliding window counter for key"""
        with self.lock:
            if key not in self.counters:
                self.counters[key] = SlidingWindowCounter(window_size, max_requests)
            return self.counters[key]
    
    def cleanup_expired(self):
        """Clean up expired entries"""
        now = time.time()
        if now - self.last_cleanup < self.cleanup_interval:
            return
        
        with self.lock:
            # Clean up old counters
            expired_counters = []
            for key, counter in self.counters.items():
                if not counter.requests or counter.requests[-1] < now - counter.window_size * 2:
                    expired_counters.append(key)
            
            for key in expired_counters:
                del self.counters[key]
            
            # Clean up old buckets (keep them longer as they refill)
            expired_buckets = []
            for key, bucket in self.buckets.items():
                if now - bucket.last_refill > 3600:  # 1 hour
                    expired_buckets.append(key)
            
            for key in expired_buckets:
                del self.buckets[key]
            
            self.last_cleanup = now
            
            if expired_counters or expired_buckets:
                logger.info(f"🧹 Cleaned up {len(expired_counters)} counters and {len(expired_buckets)} buckets")

class RateLimiter:
    """
    Main rate limiter class with multiple algorithms and storage backends
    """
    
    def __init__(self, store=None):
        self.store = store or InMemoryRateLimitStore()
        self.enabled = True
        self.default_limits = {
            'requests_per_minute': 60,
            'requests_per_hour': 1000,
            'burst_capacity': 10
        }
        
        # Start cleanup thread
        self._start_cleanup_thread()
        
        logger.info("✅ Rate limiter initialized")
    
    def _start_cleanup_thread(self):
        """Start background cleanup thread"""
        def cleanup_worker():
            while True:
                try:
                    time.sleep(300)  # Run every 5 minutes
                    self.store.cleanup_expired()
                except Exception as e:
                    logger.error(f"Rate limiter cleanup error: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        logger.info("🧹 Started rate limiter cleanup thread")
    
    def _get_client_id(self, request_obj=None) -> str:
        """Get unique client identifier"""
        if request_obj is None:
            request_obj = request
        
        # Try to get user ID from session/auth
        user_id = getattr(g, 'user_id', None)
        if user_id:
            return f"user:{user_id}"
        
        # Fall back to IP address
        ip_address = request_obj.remote_addr or 'unknown'
        
        # Include user agent for better identification
        user_agent = request_obj.headers.get('User-Agent', '')
        client_hash = hashlib.md5(f"{ip_address}:{user_agent}".encode()).hexdigest()[:8]
        
        return f"ip:{ip_address}:{client_hash}"
    
    def check_rate_limit(self, key: str = None, limit_type: str = 'default', 
                        requests_per_minute: int = None, requests_per_hour: int = None,
                        burst_capacity: int = None) -> Dict[str, Any]:
        """
        Check if request is within rate limits
        
        Args:
            key: Custom key for rate limiting (optional)
            limit_type: Type of limit to apply
            requests_per_minute: Custom requests per minute limit
            requests_per_hour: Custom requests per hour limit
            burst_capacity: Custom burst capacity
            
        Returns:
            Dictionary with rate limit status
        """
        if not self.enabled:
            return {'allowed': True, 'reason': 'rate_limiting_disabled'}
        
        # Get client identifier
        client_id = key or self._get_client_id()
        
        # Get limits
        rpm = requests_per_minute or self.default_limits['requests_per_minute']
        rph = requests_per_hour or self.default_limits['requests_per_hour']
        burst = burst_capacity or self.default_limits['burst_capacity']
        
        # Check burst limit using token bucket
        burst_key = f"burst:{client_id}:{limit_type}"
        bucket = self.store.get_bucket(burst_key, burst, burst / 60.0)  # Refill over 1 minute
        
        if not bucket.consume():
            wait_time = bucket.get_wait_time()
            return {
                'allowed': False,
                'reason': 'burst_limit_exceeded',
                'retry_after': int(wait_time) + 1,
                'limit_type': 'burst',
                'limit': burst
            }
        
        # Check per-minute limit
        minute_key = f"minute:{client_id}:{limit_type}"
        minute_counter = self.store.get_counter(minute_key, 60, rpm)
        minute_allowed, minute_requests = minute_counter.is_allowed()
        
        if not minute_allowed:
            reset_time = minute_counter.get_reset_time()
            return {
                'allowed': False,
                'reason': 'minute_limit_exceeded',
                'retry_after': reset_time - int(time.time()),
                'limit_type': 'per_minute',
                'limit': rpm,
                'current': minute_requests
            }
        
        # Check per-hour limit
        hour_key = f"hour:{client_id}:{limit_type}"
        hour_counter = self.store.get_counter(hour_key, 3600, rph)
        hour_allowed, hour_requests = hour_counter.is_allowed()
        
        if not hour_allowed:
            reset_time = hour_counter.get_reset_time()
            return {
                'allowed': False,
                'reason': 'hour_limit_exceeded',
                'retry_after': reset_time - int(time.time()),
                'limit_type': 'per_hour',
                'limit': rph,
                'current': hour_requests
            }
        
        return {
            'allowed': True,
            'reason': 'within_limits',
            'minute_requests': minute_requests,
            'hour_requests': hour_requests,
            'burst_tokens_remaining': int(bucket.tokens)
        }
    
    def get_rate_limit_headers(self, result: Dict[str, Any]) -> Dict[str, str]:
        """Get HTTP headers for rate limiting"""
        headers = {}
        
        if result.get('allowed'):
            headers['X-RateLimit-Remaining-Minute'] = str(
                self.default_limits['requests_per_minute'] - result.get('minute_requests', 0)
            )
            headers['X-RateLimit-Remaining-Hour'] = str(
                self.default_limits['requests_per_hour'] - result.get('hour_requests', 0)
            )
            headers['X-RateLimit-Burst-Remaining'] = str(result.get('burst_tokens_remaining', 0))
        else:
            headers['X-RateLimit-Limit'] = str(result.get('limit', 0))
            headers['X-RateLimit-Remaining'] = '0'
            if result.get('retry_after'):
                headers['Retry-After'] = str(result['retry_after'])
        
        return headers
    
    def enable(self):
        """Enable rate limiting"""
        self.enabled = True
        logger.info("✅ Rate limiting enabled")
    
    def disable(self):
        """Disable rate limiting"""
        self.enabled = False
        logger.warning("⚠️ Rate limiting disabled")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        return {
            'enabled': self.enabled,
            'default_limits': self.default_limits,
            'active_buckets': len(self.store.buckets),
            'active_counters': len(self.store.counters),
            'store_type': type(self.store).__name__
        }

# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None

def initialize_rate_limiter(store=None, **default_limits):
    """
    Initialize global rate limiter
    
    Args:
        store: Storage backend for rate limiting data
        **default_limits: Default rate limits
    """
    global _rate_limiter
    _rate_limiter = RateLimiter(store)
    
    if default_limits:
        _rate_limiter.default_limits.update(default_limits)
    
    logger.info("✅ Global rate limiter initialized")

def get_rate_limiter() -> Optional[RateLimiter]:
    """Get global rate limiter instance"""
    return _rate_limiter

def rate_limit(limit_type: str = 'default', requests_per_minute: int = None, 
              requests_per_hour: int = None, burst_capacity: int = None,
              key_func=None):
    """
    Decorator for rate limiting Flask routes
    
    Args:
        limit_type: Type of limit to apply
        requests_per_minute: Custom requests per minute limit
        requests_per_hour: Custom requests per hour limit
        burst_capacity: Custom burst capacity
        key_func: Function to generate custom rate limit key
        
    Usage:
        @rate_limit('api', requests_per_minute=30)
        def api_endpoint():
            return jsonify({'status': 'ok'})
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not _rate_limiter:
                # Rate limiter not initialized, allow request
                return func(*args, **kwargs)
            
            # Generate custom key if function provided
            custom_key = None
            if key_func:
                try:
                    custom_key = key_func()
                except Exception as e:
                    logger.error(f"Rate limit key function error: {e}")
            
            # Check rate limit
            result = _rate_limiter.check_rate_limit(
                key=custom_key,
                limit_type=limit_type,
                requests_per_minute=requests_per_minute,
                requests_per_hour=requests_per_hour,
                burst_capacity=burst_capacity
            )
            
            # Get headers
            headers = _rate_limiter.get_rate_limit_headers(result)
            
            if not result['allowed']:
                # Rate limit exceeded
                response = jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f"Too many requests. Limit: {result.get('limit', 'unknown')} per {result.get('limit_type', 'unknown')}",
                    'retry_after': result.get('retry_after', 60)
                })
                response.status_code = 429
                
                # Add headers
                for header, value in headers.items():
                    response.headers[header] = value
                
                # Log rate limit violation
                from .enhanced_logging import log_security_event
                log_security_event(
                    'rate_limit_exceeded',
                    f"Rate limit exceeded for {limit_type}",
                    'medium',
                    ip_address=request.remote_addr,
                    limit_type=result.get('limit_type'),
                    limit=result.get('limit')
                )
                
                return response
            
            # Execute the function
            response = func(*args, **kwargs)
            
            # Add rate limit headers to successful responses
            if hasattr(response, 'headers'):
                for header, value in headers.items():
                    response.headers[header] = value
            
            return response
        
        return wrapper
    return decorator

# Predefined rate limit decorators for common use cases
def api_rate_limit(func):
    """Rate limit for API endpoints (30 requests/minute, 500/hour)"""
    return rate_limit('api', requests_per_minute=30, requests_per_hour=500, burst_capacity=5)(func)

def auth_rate_limit(func):
    """Rate limit for authentication endpoints (5 requests/minute, 20/hour)"""
    return rate_limit('auth', requests_per_minute=5, requests_per_hour=20, burst_capacity=3)(func)

def upload_rate_limit(func):
    """Rate limit for file upload endpoints (10 requests/minute, 100/hour)"""
    return rate_limit('upload', requests_per_minute=10, requests_per_hour=100, burst_capacity=2)(func)

if __name__ == "__main__":
    # Test rate limiting
    print("Testing rate limiting system...")
    
    # Initialize rate limiter
    initialize_rate_limiter(requests_per_minute=5, burst_capacity=3)
    
    # Simulate requests
    limiter = get_rate_limiter()
    
    for i in range(10):
        result = limiter.check_rate_limit(key=f"test_client", limit_type='test')
        print(f"Request {i+1}: {'ALLOWED' if result['allowed'] else 'BLOCKED'} - {result}")
        
        if not result['allowed']:
            print(f"  Retry after: {result.get('retry_after', 0)} seconds")
        
        time.sleep(0.1)
    
    # Get stats
    stats = limiter.get_stats()
    print(f"Rate limiter stats: {stats}")
    
    print("Rate limiting test completed")
