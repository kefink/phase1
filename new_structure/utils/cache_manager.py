"""
Cache Manager for Hillview School Management System
Implements Redis caching for improved performance and scalability
"""

import redis
import json
import pickle
import hashlib
from functools import wraps
from datetime import datetime, timedelta
from typing import Any, Optional, Union, Dict, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CacheManager:
    """
    Centralized cache management using Redis
    Provides caching for frequently accessed data to improve system performance
    """
    
    def __init__(self, host='localhost', port=6379, db=0, password=None):
        """
        Initialize Redis connection
        
        Args:
            host: Redis server host
            port: Redis server port
            db: Redis database number
            password: Redis password (if required)
        """
        try:
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # Test connection
            self.redis_client.ping()
            self.is_available = True
            logger.info("✅ Redis cache connection established successfully")
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(f"⚠️ Redis not available, falling back to in-memory cache: {e}")
            self.redis_client = None
            self.is_available = False
            self._memory_cache = {}
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate a unique cache key based on prefix and parameters
        
        Args:
            prefix: Cache key prefix
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Unique cache key string
        """
        # Create a string representation of all arguments
        key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
        # Hash for consistent key length
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"hillview:{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            if self.is_available:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            else:
                return self._memory_cache.get(key)
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        Set value in cache with TTL
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: 1 hour)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.is_available:
                return self.redis_client.setex(key, ttl, json.dumps(value, default=str))
            else:
                # Simple in-memory cache with expiration
                expiry = datetime.now() + timedelta(seconds=ttl)
                self._memory_cache[key] = {'value': value, 'expiry': expiry}
                return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
        return False
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.is_available:
                return bool(self.redis_client.delete(key))
            else:
                return self._memory_cache.pop(key, None) is not None
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
        return False
    
    def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching a pattern
        
        Args:
            pattern: Pattern to match (e.g., "hillview:students:*")
            
        Returns:
            Number of keys deleted
        """
        try:
            if self.is_available:
                keys = self.redis_client.keys(pattern)
                if keys:
                    return self.redis_client.delete(*keys)
            else:
                # Clear matching keys from memory cache
                keys_to_delete = [k for k in self._memory_cache.keys() if pattern.replace('*', '') in k]
                for key in keys_to_delete:
                    del self._memory_cache[key]
                return len(keys_to_delete)
        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {e}")
        return 0
    
    def cleanup_expired(self):
        """Clean up expired keys from memory cache"""
        if not self.is_available:
            now = datetime.now()
            expired_keys = [
                key for key, data in self._memory_cache.items()
                if data.get('expiry', now) < now
            ]
            for key in expired_keys:
                del self._memory_cache[key]
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

# Global cache instance
cache = CacheManager()

def cached(prefix: str, ttl: int = 3600):
    """
    Decorator for caching function results
    
    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds
        
    Usage:
        @cached('students', ttl=1800)
        def get_students_by_class(class_id):
            # Function implementation
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache._generate_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            logger.debug(f"Cache miss for {func.__name__}, result cached")
            return result
        
        # Add cache management methods to the function
        wrapper.cache_clear = lambda *args, **kwargs: cache.delete(
            cache._generate_key(prefix, *args, **kwargs)
        )
        wrapper.cache_clear_all = lambda: cache.clear_pattern(f"hillview:{prefix}:*")
        
        return wrapper
    return decorator

# Specific cache functions for common operations
class SchoolDataCache:
    """Specific caching functions for school data"""
    
    @staticmethod
    def get_students_by_class(class_id: str, stream: str = None) -> Optional[List[Dict]]:
        """Get cached students for a class"""
        key = cache._generate_key('students_class', class_id, stream)
        return cache.get(key)
    
    @staticmethod
    def set_students_by_class(class_id: str, students: List[Dict], stream: str = None, ttl: int = 1800):
        """Cache students for a class"""
        key = cache._generate_key('students_class', class_id, stream)
        cache.set(key, students, ttl)
    
    @staticmethod
    def get_class_analytics(class_id: str, assessment_type: str = None) -> Optional[Dict]:
        """Get cached analytics for a class"""
        key = cache._generate_key('analytics_class', class_id, assessment_type)
        return cache.get(key)
    
    @staticmethod
    def set_class_analytics(class_id: str, analytics: Dict, assessment_type: str = None, ttl: int = 900):
        """Cache analytics for a class (15 minutes TTL for fresh data)"""
        key = cache._generate_key('analytics_class', class_id, assessment_type)
        cache.set(key, analytics, ttl)
    
    @staticmethod
    def get_school_config() -> Optional[Dict]:
        """Get cached school configuration"""
        key = cache._generate_key('school_config')
        return cache.get(key)
    
    @staticmethod
    def set_school_config(config: Dict, ttl: int = 7200):
        """Cache school configuration (2 hours TTL)"""
        key = cache._generate_key('school_config')
        cache.set(key, config, ttl)
    
    @staticmethod
    def invalidate_class_data(class_id: str):
        """Invalidate all cached data for a specific class"""
        patterns = [
            f"hillview:students_class:*{class_id}*",
            f"hillview:analytics_class:*{class_id}*"
        ]
        for pattern in patterns:
            cache.clear_pattern(pattern)
    
    @staticmethod
    def invalidate_all_analytics():
        """Invalidate all cached analytics data"""
        cache.clear_pattern("hillview:analytics_*")

# Cache warming functions
def warm_cache():
    """Warm up cache with frequently accessed data"""
    logger.info("🔥 Starting cache warming process...")
    
    try:
        # Import here to avoid circular imports
        from database import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Cache all classes
        cursor.execute("SELECT DISTINCT class, stream FROM students WHERE class IS NOT NULL")
        classes = cursor.fetchall()
        
        for class_info in classes:
            class_name, stream = class_info
            # Cache students for each class
            cursor.execute(
                "SELECT * FROM students WHERE class = ? AND stream = ?",
                (class_name, stream)
            )
            students = [dict(row) for row in cursor.fetchall()]
            SchoolDataCache.set_students_by_class(class_name, students, stream)
        
        # Cache school configuration
        cursor.execute("SELECT * FROM school_info LIMIT 1")
        school_info = cursor.fetchone()
        if school_info:
            SchoolDataCache.set_school_config(dict(school_info))
        
        conn.close()
        logger.info(f"✅ Cache warmed with data for {len(classes)} classes")
        
    except Exception as e:
        logger.error(f"❌ Cache warming failed: {e}")

if __name__ == "__main__":
    # Test cache functionality
    print("Testing cache functionality...")
    
    # Test basic operations
    cache.set("test_key", {"message": "Hello, Cache!"}, 60)
    result = cache.get("test_key")
    print(f"Cache test result: {result}")
    
    # Test decorator
    @cached('test_function', ttl=300)
    def expensive_function(x, y):
        print(f"Executing expensive function with {x}, {y}")
        return x + y
    
    # First call - should execute function
    result1 = expensive_function(5, 10)
    print(f"First call result: {result1}")
    
    # Second call - should use cache
    result2 = expensive_function(5, 10)
    print(f"Second call result: {result2}")
