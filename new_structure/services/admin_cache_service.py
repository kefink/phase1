"""
Cache service for admin/headteacher dashboard statistics.
"""
import os
import json
import time
import hashlib
import pickle

# Cache directory
CACHE_DIR = 'cache'
ADMIN_CACHE_DIR = os.path.join(CACHE_DIR, 'admin')

# In-memory cache for frequently accessed data
_admin_memory_cache = {}

def _ensure_cache_dirs():
    """Ensure all cache directories exist."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    os.makedirs(ADMIN_CACHE_DIR, exist_ok=True)

def _generate_cache_key(*args, **kwargs):
    """Generate a unique cache key based on arguments."""
    # Convert all arguments to strings and join them
    key_parts = [str(arg) for arg in args]
    key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
    key_string = "_".join(key_parts)
    
    # Create a hash of the key string to ensure it's a valid filename
    return hashlib.md5(key_string.encode()).hexdigest()

def cache_dashboard_stats(stats_data, expiry=3600):
    """
    Cache dashboard statistics.
    
    Args:
        stats_data: The dashboard statistics to cache
        expiry: Cache expiry time in seconds (default: 1 hour)
    """
    _ensure_cache_dirs()
    
    # Generate cache key
    cache_key = _generate_cache_key("dashboard_stats")
    
    # Store in memory cache
    _admin_memory_cache[cache_key] = {
        'data': stats_data,
        'timestamp': time.time(),
        'expiry': expiry
    }
    
    # Store in file cache
    cache_file = os.path.join(ADMIN_CACHE_DIR, f"{cache_key}.pickle")
    with open(cache_file, 'wb') as f:
        pickle.dump({
            'data': stats_data,
            'timestamp': time.time(),
            'expiry': expiry
        }, f)

def get_cached_dashboard_stats():
    """
    Get cached dashboard statistics if available and not expired.
    
    Returns:
        The cached dashboard statistics if available and not expired, None otherwise.
    """
    # Generate cache key
    cache_key = _generate_cache_key("dashboard_stats")
    
    # Check memory cache first
    if cache_key in _admin_memory_cache:
        cache_entry = _admin_memory_cache[cache_key]
        if time.time() - cache_entry['timestamp'] < cache_entry['expiry']:
            return cache_entry['data']
    
    # Check file cache
    cache_file = os.path.join(ADMIN_CACHE_DIR, f"{cache_key}.pickle")
    if os.path.exists(cache_file):
        with open(cache_file, 'rb') as f:
            try:
                cache_entry = pickle.load(f)
                if time.time() - cache_entry['timestamp'] < cache_entry['expiry']:
                    # Update memory cache
                    _admin_memory_cache[cache_key] = cache_entry
                    return cache_entry['data']
            except (pickle.PickleError, KeyError):
                # Invalid cache file, ignore
                pass
    
    return None

def cache_subject_list(subjects_data, expiry=3600):
    """
    Cache subject list.
    
    Args:
        subjects_data: The subject list data to cache
        expiry: Cache expiry time in seconds (default: 1 hour)
    """
    _ensure_cache_dirs()
    
    # Generate cache key
    cache_key = _generate_cache_key("subject_list")
    
    # Store in memory cache
    _admin_memory_cache[cache_key] = {
        'data': subjects_data,
        'timestamp': time.time(),
        'expiry': expiry
    }
    
    # Store in file cache
    cache_file = os.path.join(ADMIN_CACHE_DIR, f"{cache_key}.pickle")
    with open(cache_file, 'wb') as f:
        pickle.dump({
            'data': subjects_data,
            'timestamp': time.time(),
            'expiry': expiry
        }, f)

def get_cached_subject_list():
    """
    Get cached subject list if available and not expired.
    
    Returns:
        The cached subject list if available and not expired, None otherwise.
    """
    # Generate cache key
    cache_key = _generate_cache_key("subject_list")
    
    # Check memory cache first
    if cache_key in _admin_memory_cache:
        cache_entry = _admin_memory_cache[cache_key]
        if time.time() - cache_entry['timestamp'] < cache_entry['expiry']:
            return cache_entry['data']
    
    # Check file cache
    cache_file = os.path.join(ADMIN_CACHE_DIR, f"{cache_key}.pickle")
    if os.path.exists(cache_file):
        with open(cache_file, 'rb') as f:
            try:
                cache_entry = pickle.load(f)
                if time.time() - cache_entry['timestamp'] < cache_entry['expiry']:
                    # Update memory cache
                    _admin_memory_cache[cache_key] = cache_entry
                    return cache_entry['data']
            except (pickle.PickleError, KeyError):
                # Invalid cache file, ignore
                pass
    
    return None

def invalidate_admin_cache():
    """Invalidate all admin caches."""
    # Clear memory cache
    _admin_memory_cache.clear()
    
    # Clear file caches
    for file_name in os.listdir(ADMIN_CACHE_DIR):
        file_path = os.path.join(ADMIN_CACHE_DIR, file_name)
        try:
            os.remove(file_path)
        except OSError:
            # Ignore errors when deleting cache files
            pass
