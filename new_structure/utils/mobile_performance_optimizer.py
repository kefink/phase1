"""
Mobile Performance Optimizer for Hillview School Management System
Comprehensive mobile device performance optimization utilities
"""

import os
import time
import gzip
import json
from typing import Dict, List, Any, Optional
from functools import wraps
from flask import request, current_app, g
import logging
from datetime import datetime, timedelta

class MobilePerformanceOptimizer:
    """Mobile-specific performance optimization utilities"""
    
    def __init__(self):
        self.performance_metrics = {}
        self.mobile_cache = {}
        self.optimization_config = {
            'enable_compression': True,
            'enable_mobile_cache': True,
            'enable_lazy_loading': True,
            'enable_image_optimization': True,
            'enable_css_minification': True,
            'enable_js_minification': True,
            'mobile_cache_duration': 3600,  # 1 hour
            'performance_threshold': 0.5,   # 500ms
        }
        
    def is_mobile_device(self, user_agent: str = None) -> bool:
        """
        Detect if the request is from a mobile device
        
        Args:
            user_agent: User agent string
            
        Returns:
            bool: True if mobile device
        """
        if not user_agent:
            user_agent = request.headers.get('User-Agent', '').lower()
        
        mobile_indicators = [
            'mobile', 'android', 'iphone', 'ipad', 'ipod',
            'blackberry', 'windows phone', 'opera mini',
            'palm', 'symbian', 'webos'
        ]
        
        return any(indicator in user_agent for indicator in mobile_indicators)
    
    def get_device_type(self, user_agent: str = None) -> str:
        """
        Get specific device type for optimization
        
        Args:
            user_agent: User agent string
            
        Returns:
            str: Device type (mobile, tablet, desktop)
        """
        if not user_agent:
            user_agent = request.headers.get('User-Agent', '').lower()
        
        if 'ipad' in user_agent or 'tablet' in user_agent:
            return 'tablet'
        elif self.is_mobile_device(user_agent):
            return 'mobile'
        else:
            return 'desktop'
    
    def optimize_css_for_mobile(self, css_content: str, device_type: str) -> str:
        """
        Optimize CSS content for mobile devices
        
        Args:
            css_content: Original CSS content
            device_type: Type of device
            
        Returns:
            str: Optimized CSS content
        """
        if device_type == 'mobile':
            # Remove desktop-only styles for mobile
            optimizations = [
                # Remove hover effects for mobile (touch devices)
                r':hover\s*{[^}]*}',
                # Remove large font sizes
                r'font-size:\s*[2-9]\d+px',
                # Remove complex animations for performance
                r'animation:\s*[^;]*complex[^;]*;',
            ]
            
            for pattern in optimizations:
                import re
                css_content = re.sub(pattern, '', css_content, flags=re.IGNORECASE)
        
        return css_content
    
    def compress_response(self, response_data: str) -> bytes:
        """
        Compress response data for mobile networks
        
        Args:
            response_data: Response content
            
        Returns:
            bytes: Compressed content
        """
        if self.optimization_config['enable_compression']:
            return gzip.compress(response_data.encode('utf-8'))
        return response_data.encode('utf-8')
    
    def cache_mobile_response(self, cache_key: str, data: Any, duration: int = None) -> None:
        """
        Cache response data for mobile devices
        
        Args:
            cache_key: Unique cache key
            data: Data to cache
            duration: Cache duration in seconds
        """
        if not self.optimization_config['enable_mobile_cache']:
            return
        
        duration = duration or self.optimization_config['mobile_cache_duration']
        expiry = datetime.now() + timedelta(seconds=duration)
        
        self.mobile_cache[cache_key] = {
            'data': data,
            'expiry': expiry,
            'device_type': self.get_device_type()
        }
    
    def get_cached_mobile_response(self, cache_key: str) -> Optional[Any]:
        """
        Get cached response for mobile devices
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached data or None
        """
        if not self.optimization_config['enable_mobile_cache']:
            return None
        
        cached_item = self.mobile_cache.get(cache_key)
        if cached_item and cached_item['expiry'] > datetime.now():
            return cached_item['data']
        
        # Clean expired cache
        if cached_item:
            del self.mobile_cache[cache_key]
        
        return None
    
    def optimize_images_for_mobile(self, image_path: str, device_type: str) -> str:
        """
        Optimize images for mobile devices
        
        Args:
            image_path: Path to image
            device_type: Type of device
            
        Returns:
            str: Optimized image path or original path
        """
        if not self.optimization_config['enable_image_optimization']:
            return image_path
        
        try:
            from PIL import Image
            
            # Define mobile-specific image sizes
            mobile_sizes = {
                'mobile': (400, 400),
                'tablet': (600, 600),
                'desktop': (800, 800)
            }
            
            max_size = mobile_sizes.get(device_type, (400, 400))
            
            # Generate optimized image path
            base_name, ext = os.path.splitext(image_path)
            optimized_path = f"{base_name}_mobile_{device_type}{ext}"
            
            # Check if optimized version already exists
            if os.path.exists(optimized_path):
                return optimized_path
            
            # Create optimized version
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Resize maintaining aspect ratio
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Save with mobile optimization
                quality = 75 if device_type == 'mobile' else 85
                img.save(optimized_path, 'JPEG', quality=quality, optimize=True)
                
                return optimized_path
                
        except Exception as e:
            logging.warning(f"Image optimization failed: {e}")
            return image_path
        
        return image_path
    
    def record_performance_metric(self, endpoint: str, duration: float, device_type: str) -> None:
        """
        Record performance metrics for mobile optimization
        
        Args:
            endpoint: API endpoint
            duration: Request duration
            device_type: Type of device
        """
        if endpoint not in self.performance_metrics:
            self.performance_metrics[endpoint] = {
                'mobile': [],
                'tablet': [],
                'desktop': []
            }
        
        self.performance_metrics[endpoint][device_type].append({
            'duration': duration,
            'timestamp': datetime.now()
        })
        
        # Keep only recent metrics (last 100 requests per device type)
        if len(self.performance_metrics[endpoint][device_type]) > 100:
            self.performance_metrics[endpoint][device_type] = \
                self.performance_metrics[endpoint][device_type][-100:]
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        Generate performance report for mobile optimization
        
        Returns:
            Dict with performance metrics
        """
        report = {
            'endpoints': {},
            'summary': {
                'total_requests': 0,
                'slow_requests': 0,
                'average_mobile_time': 0,
                'average_desktop_time': 0
            }
        }
        
        threshold = self.optimization_config['performance_threshold']
        total_mobile_time = 0
        total_desktop_time = 0
        mobile_count = 0
        desktop_count = 0
        
        for endpoint, metrics in self.performance_metrics.items():
            endpoint_data = {
                'mobile': {'avg': 0, 'count': 0, 'slow': 0},
                'tablet': {'avg': 0, 'count': 0, 'slow': 0},
                'desktop': {'avg': 0, 'count': 0, 'slow': 0}
            }
            
            for device_type, requests in metrics.items():
                if requests:
                    durations = [r['duration'] for r in requests]
                    endpoint_data[device_type]['avg'] = sum(durations) / len(durations)
                    endpoint_data[device_type]['count'] = len(durations)
                    endpoint_data[device_type]['slow'] = len([d for d in durations if d > threshold])
                    
                    # Update summary
                    report['summary']['total_requests'] += len(durations)
                    report['summary']['slow_requests'] += endpoint_data[device_type]['slow']
                    
                    if device_type == 'mobile':
                        total_mobile_time += sum(durations)
                        mobile_count += len(durations)
                    elif device_type == 'desktop':
                        total_desktop_time += sum(durations)
                        desktop_count += len(durations)
            
            report['endpoints'][endpoint] = endpoint_data
        
        # Calculate averages
        if mobile_count > 0:
            report['summary']['average_mobile_time'] = total_mobile_time / mobile_count
        if desktop_count > 0:
            report['summary']['average_desktop_time'] = total_desktop_time / desktop_count
        
        return report
    
    def clear_expired_cache(self) -> int:
        """
        Clear expired cache entries
        
        Returns:
            int: Number of entries cleared
        """
        now = datetime.now()
        expired_keys = [
            key for key, value in self.mobile_cache.items()
            if value['expiry'] <= now
        ]
        
        for key in expired_keys:
            del self.mobile_cache[key]
        
        return len(expired_keys)

# Global optimizer instance
mobile_optimizer = MobilePerformanceOptimizer()

def mobile_performance_decorator(cache_duration: int = None):
    """
    Decorator for mobile performance optimization
    
    Args:
        cache_duration: Cache duration in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            device_type = mobile_optimizer.get_device_type()
            endpoint = func.__name__
            
            # Check cache for mobile devices
            if device_type in ['mobile', 'tablet']:
                cache_key = f"{endpoint}_{device_type}_{hash(str(args) + str(kwargs))}"
                cached_response = mobile_optimizer.get_cached_mobile_response(cache_key)
                if cached_response:
                    return cached_response
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result for mobile devices
            if device_type in ['mobile', 'tablet']:
                mobile_optimizer.cache_mobile_response(cache_key, result, cache_duration)
            
            # Record performance metrics
            duration = time.time() - start_time
            mobile_optimizer.record_performance_metric(endpoint, duration, device_type)
            
            return result
        
        return wrapper
    return decorator

def optimize_for_mobile_network():
    """Apply mobile network optimizations"""
    optimizations = []
    
    # Enable compression
    if mobile_optimizer.optimization_config['enable_compression']:
        optimizations.append('Response compression enabled')
    
    # Clear expired cache
    cleared = mobile_optimizer.clear_expired_cache()
    if cleared > 0:
        optimizations.append(f'Cleared {cleared} expired cache entries')
    
    return optimizations
