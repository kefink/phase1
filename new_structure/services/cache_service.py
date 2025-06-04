"""
Cache service for storing and retrieving cached data.
This module provides functions for caching reports, marksheets, and other data.
"""
import os
import json
import time
import hashlib
from flask import current_app
import pickle

# Cache directory
CACHE_DIR = 'cache'
REPORT_CACHE_DIR = os.path.join(CACHE_DIR, 'reports')
MARKSHEET_CACHE_DIR = os.path.join(CACHE_DIR, 'marksheets')
PDF_CACHE_DIR = os.path.join(CACHE_DIR, 'pdfs')
ANALYTICS_CACHE_DIR = os.path.join(CACHE_DIR, 'analytics')

# In-memory cache for frequently accessed data
_memory_cache = {}

def _ensure_cache_dirs():
    """Ensure all cache directories exist."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    os.makedirs(REPORT_CACHE_DIR, exist_ok=True)
    os.makedirs(MARKSHEET_CACHE_DIR, exist_ok=True)
    os.makedirs(PDF_CACHE_DIR, exist_ok=True)
    os.makedirs(ANALYTICS_CACHE_DIR, exist_ok=True)

def _generate_cache_key(*args, **kwargs):
    """Generate a unique cache key based on arguments."""
    # Convert all arguments to strings and join them
    key_parts = [str(arg) for arg in args]
    key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
    key_string = "_".join(key_parts)
    
    # Create a hash of the key string to ensure it's a valid filename
    return hashlib.md5(key_string.encode()).hexdigest()

def cache_marksheet(grade, stream, term, assessment_type, marksheet_data, expiry=3600):
    """
    Cache marksheet data.
    
    Args:
        grade: Grade level
        stream: Stream name
        term: Term name
        assessment_type: Assessment type name
        marksheet_data: The marksheet data to cache
        expiry: Cache expiry time in seconds (default: 1 hour)
    """
    _ensure_cache_dirs()
    
    # Generate cache key
    cache_key = _generate_cache_key(grade, stream, term, assessment_type)
    
    # Store in memory cache
    _memory_cache[cache_key] = {
        'data': marksheet_data,
        'timestamp': time.time(),
        'expiry': expiry
    }
    
    # Store in file cache
    cache_file = os.path.join(MARKSHEET_CACHE_DIR, f"{cache_key}.json")
    with open(cache_file, 'w') as f:
        json.dump({
            'data': marksheet_data,
            'timestamp': time.time(),
            'expiry': expiry
        }, f)

def get_cached_marksheet(grade, stream, term, assessment_type):
    """
    Get cached marksheet data if available and not expired.
    
    Args:
        grade: Grade level
        stream: Stream name
        term: Term name
        assessment_type: Assessment type name
        
    Returns:
        The cached marksheet data if available and not expired, None otherwise.
    """
    # Generate cache key
    cache_key = _generate_cache_key(grade, stream, term, assessment_type)
    
    # Check memory cache first
    if cache_key in _memory_cache:
        cache_entry = _memory_cache[cache_key]
        if time.time() - cache_entry['timestamp'] < cache_entry['expiry']:
            return cache_entry['data']
    
    # Check file cache
    cache_file = os.path.join(MARKSHEET_CACHE_DIR, f"{cache_key}.json")
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            try:
                cache_entry = json.load(f)
                if time.time() - cache_entry['timestamp'] < cache_entry['expiry']:
                    # Update memory cache
                    _memory_cache[cache_key] = cache_entry
                    return cache_entry['data']
            except (json.JSONDecodeError, KeyError):
                # Invalid cache file, ignore
                pass
    
    return None

def cache_report(grade, stream, term, assessment_type, report_data, expiry=3600):
    """
    Cache report data.
    
    Args:
        grade: Grade level
        stream: Stream name
        term: Term name
        assessment_type: Assessment type name
        report_data: The report data to cache
        expiry: Cache expiry time in seconds (default: 1 hour)
    """
    _ensure_cache_dirs()
    
    # Generate cache key
    cache_key = _generate_cache_key(grade, stream, term, assessment_type)
    
    # Store in memory cache
    _memory_cache[f"report_{cache_key}"] = {
        'data': report_data,
        'timestamp': time.time(),
        'expiry': expiry
    }
    
    # Store in file cache
    cache_file = os.path.join(REPORT_CACHE_DIR, f"{cache_key}.pickle")
    with open(cache_file, 'wb') as f:
        pickle.dump({
            'data': report_data,
            'timestamp': time.time(),
            'expiry': expiry
        }, f)

def get_cached_report(grade, stream, term, assessment_type):
    """
    Get cached report data if available and not expired.
    
    Args:
        grade: Grade level
        stream: Stream name
        term: Term name
        assessment_type: Assessment type name
        
    Returns:
        The cached report data if available and not expired, None otherwise.
    """
    # Generate cache key
    cache_key = _generate_cache_key(grade, stream, term, assessment_type)
    memory_key = f"report_{cache_key}"
    
    # Check memory cache first
    if memory_key in _memory_cache:
        cache_entry = _memory_cache[memory_key]
        if time.time() - cache_entry['timestamp'] < cache_entry['expiry']:
            return cache_entry['data']
    
    # Check file cache
    cache_file = os.path.join(REPORT_CACHE_DIR, f"{cache_key}.pickle")
    if os.path.exists(cache_file):
        with open(cache_file, 'rb') as f:
            try:
                cache_entry = pickle.load(f)
                if time.time() - cache_entry['timestamp'] < cache_entry['expiry']:
                    # Update memory cache
                    _memory_cache[memory_key] = cache_entry
                    return cache_entry['data']
            except (pickle.PickleError, KeyError):
                # Invalid cache file, ignore
                pass
    
    return None

def cache_pdf(grade, stream, term, assessment_type, pdf_type, pdf_data, expiry=86400):
    """
    Cache PDF data.
    
    Args:
        grade: Grade level
        stream: Stream name
        term: Term name
        assessment_type: Assessment type name
        pdf_type: Type of PDF (e.g., 'marksheet', 'report')
        pdf_data: The PDF data to cache
        expiry: Cache expiry time in seconds (default: 24 hours)
    """
    _ensure_cache_dirs()
    
    # Generate cache key
    cache_key = _generate_cache_key(grade, stream, term, assessment_type, pdf_type)
    
    # Store in file cache
    cache_file = os.path.join(PDF_CACHE_DIR, f"{cache_key}.pdf")
    with open(cache_file, 'wb') as f:
        f.write(pdf_data)
    
    # Store metadata
    meta_file = os.path.join(PDF_CACHE_DIR, f"{cache_key}.meta")
    with open(meta_file, 'w') as f:
        json.dump({
            'timestamp': time.time(),
            'expiry': expiry
        }, f)
    
    return cache_file

def get_cached_pdf(grade, stream, term, assessment_type, pdf_type):
    """
    Get cached PDF file path if available and not expired.
    
    Args:
        grade: Grade level
        stream: Stream name
        term: Term name
        assessment_type: Assessment type name
        pdf_type: Type of PDF (e.g., 'marksheet', 'report')
        
    Returns:
        The path to the cached PDF file if available and not expired, None otherwise.
    """
    # Generate cache key
    cache_key = _generate_cache_key(grade, stream, term, assessment_type, pdf_type)
    
    # Check file cache
    cache_file = os.path.join(PDF_CACHE_DIR, f"{cache_key}.pdf")
    meta_file = os.path.join(PDF_CACHE_DIR, f"{cache_key}.meta")
    
    if os.path.exists(cache_file) and os.path.exists(meta_file):
        with open(meta_file, 'r') as f:
            try:
                meta = json.load(f)
                if time.time() - meta['timestamp'] < meta['expiry']:
                    return cache_file
            except (json.JSONDecodeError, KeyError):
                # Invalid meta file, ignore
                pass
    
    return None

def invalidate_cache(grade, stream, term, assessment_type):
    """
    Invalidate all caches for a specific grade, stream, term, and assessment type.
    
    Args:
        grade: Grade level
        stream: Stream name
        term: Term name
        assessment_type: Assessment type name
    """
    # Generate cache key
    cache_key = _generate_cache_key(grade, stream, term, assessment_type)
    
    # Clear memory cache
    memory_keys = [cache_key, f"report_{cache_key}"]
    for key in memory_keys:
        if key in _memory_cache:
            del _memory_cache[key]
    
    # Clear file caches
    cache_files = [
        os.path.join(MARKSHEET_CACHE_DIR, f"{cache_key}.json"),
        os.path.join(REPORT_CACHE_DIR, f"{cache_key}.pickle")
    ]
    
    # Clear PDF caches
    pdf_types = ['marksheet', 'report']
    for pdf_type in pdf_types:
        pdf_key = _generate_cache_key(grade, stream, term, assessment_type, pdf_type)
        cache_files.extend([
            os.path.join(PDF_CACHE_DIR, f"{pdf_key}.pdf"),
            os.path.join(PDF_CACHE_DIR, f"{pdf_key}.meta")
        ])
    
    # Delete all cache files
    for file_path in cache_files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                # Ignore errors when deleting cache files
                pass


def cache_analytics(cache_key, analytics_data, expiry=1800):
    """
    Cache analytics data.

    Args:
        cache_key: Unique cache key for the analytics data
        analytics_data: The analytics data to cache
        expiry: Cache expiry time in seconds (default: 30 minutes)
    """
    _ensure_cache_dirs()

    # Store in memory cache
    _memory_cache[f"analytics_{cache_key}"] = {
        'data': analytics_data,
        'timestamp': time.time(),
        'expiry': expiry
    }

    # Store in file cache
    cache_file = os.path.join(ANALYTICS_CACHE_DIR, f"{cache_key}.pickle")
    with open(cache_file, 'wb') as f:
        pickle.dump({
            'data': analytics_data,
            'timestamp': time.time(),
            'expiry': expiry
        }, f)


def get_cached_analytics(cache_key):
    """
    Get cached analytics data if available and not expired.

    Args:
        cache_key: Unique cache key for the analytics data

    Returns:
        The cached analytics data if available and not expired, None otherwise.
    """
    memory_key = f"analytics_{cache_key}"

    # Check memory cache first
    if memory_key in _memory_cache:
        cache_entry = _memory_cache[memory_key]
        if time.time() - cache_entry['timestamp'] < cache_entry['expiry']:
            return cache_entry['data']

    # Check file cache
    cache_file = os.path.join(ANALYTICS_CACHE_DIR, f"{cache_key}.pickle")
    if os.path.exists(cache_file):
        with open(cache_file, 'rb') as f:
            try:
                cache_entry = pickle.load(f)
                if time.time() - cache_entry['timestamp'] < cache_entry['expiry']:
                    # Update memory cache
                    _memory_cache[memory_key] = cache_entry
                    return cache_entry['data']
            except (pickle.PickleError, KeyError):
                # Invalid cache file, ignore
                pass

    return None


def invalidate_analytics_cache(cache_key=None):
    """
    Invalidate analytics cache.

    Args:
        cache_key: Specific cache key to invalidate (None to clear all analytics cache)
    """
    if cache_key:
        # Clear specific cache entry
        memory_key = f"analytics_{cache_key}"
        if memory_key in _memory_cache:
            del _memory_cache[memory_key]

        cache_file = os.path.join(ANALYTICS_CACHE_DIR, f"{cache_key}.pickle")
        if os.path.exists(cache_file):
            try:
                os.remove(cache_file)
            except OSError:
                pass
    else:
        # Clear all analytics cache
        analytics_keys = [key for key in _memory_cache.keys() if key.startswith('analytics_')]
        for key in analytics_keys:
            del _memory_cache[key]

        # Clear all analytics cache files
        if os.path.exists(ANALYTICS_CACHE_DIR):
            for filename in os.listdir(ANALYTICS_CACHE_DIR):
                if filename.endswith('.pickle'):
                    try:
                        os.remove(os.path.join(ANALYTICS_CACHE_DIR, filename))
                    except OSError:
                        pass
