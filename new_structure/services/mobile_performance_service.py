"""
Mobile Performance Service for Hillview School Management System
Real-time mobile performance monitoring and optimization
"""

import time
import json
import os
from typing import Dict, List, Any, Optional
from flask import request, current_app, g, jsonify
from datetime import datetime, timedelta
import logging
from functools import wraps

from ..utils.mobile_performance_optimizer import mobile_optimizer

class MobilePerformanceService:
    """Service for monitoring and optimizing mobile performance"""
    
    def __init__(self):
        self.performance_log = []
        self.optimization_rules = {
            'slow_threshold': 1.0,  # 1 second
            'very_slow_threshold': 3.0,  # 3 seconds
            'mobile_cache_enabled': True,
            'image_optimization_enabled': True,
            'css_minification_enabled': True,
            'js_compression_enabled': True
        }
        
    def monitor_request_performance(self, endpoint: str, method: str = 'GET'):
        """
        Monitor request performance for mobile optimization
        
        Args:
            endpoint: Request endpoint
            method: HTTP method
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                device_type = mobile_optimizer.get_device_type()
                is_mobile = mobile_optimizer.is_mobile_device()
                
                # Store request info in g for access throughout request
                g.mobile_performance = {
                    'start_time': start_time,
                    'endpoint': endpoint,
                    'method': method,
                    'device_type': device_type,
                    'is_mobile': is_mobile
                }
                
                try:
                    result = func(*args, **kwargs)
                    status_code = 200
                    return result
                except Exception as e:
                    status_code = 500
                    raise
                finally:
                    # Record performance metrics
                    duration = time.time() - start_time
                    self._record_performance_data(
                        endpoint, method, duration, device_type, 
                        is_mobile, status_code
                    )
                    
            return wrapper
        return decorator
    
    def _record_performance_data(self, endpoint: str, method: str, duration: float,
                                device_type: str, is_mobile: bool, status_code: int):
        """Record performance data for analysis"""
        performance_entry = {
            'timestamp': datetime.now().isoformat(),
            'endpoint': endpoint,
            'method': method,
            'duration': duration,
            'device_type': device_type,
            'is_mobile': is_mobile,
            'status_code': status_code,
            'is_slow': duration > self.optimization_rules['slow_threshold'],
            'is_very_slow': duration > self.optimization_rules['very_slow_threshold']
        }
        
        self.performance_log.append(performance_entry)
        
        # Keep only recent entries (last 1000)
        if len(self.performance_log) > 1000:
            self.performance_log = self.performance_log[-1000:]
        
        # Log slow requests
        if performance_entry['is_slow']:
            logging.warning(
                f"Slow mobile request: {endpoint} ({device_type}) took {duration:.3f}s"
            )
    
    def get_mobile_performance_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get mobile performance metrics for the specified time period
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            Dict with performance metrics
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Filter recent entries
        recent_entries = [
            entry for entry in self.performance_log
            if datetime.fromisoformat(entry['timestamp']) > cutoff_time
        ]
        
        if not recent_entries:
            return self._empty_metrics()
        
        # Separate mobile and desktop metrics
        mobile_entries = [e for e in recent_entries if e['is_mobile']]
        desktop_entries = [e for e in recent_entries if not e['is_mobile']]
        
        return {
            'summary': {
                'total_requests': len(recent_entries),
                'mobile_requests': len(mobile_entries),
                'desktop_requests': len(desktop_entries),
                'mobile_percentage': (len(mobile_entries) / len(recent_entries)) * 100,
                'time_period_hours': hours
            },
            'mobile_performance': self._calculate_device_metrics(mobile_entries),
            'desktop_performance': self._calculate_device_metrics(desktop_entries),
            'slowest_endpoints': self._get_slowest_endpoints(recent_entries),
            'device_breakdown': self._get_device_breakdown(recent_entries),
            'optimization_opportunities': self._identify_optimization_opportunities(recent_entries)
        }
    
    def _calculate_device_metrics(self, entries: List[Dict]) -> Dict[str, Any]:
        """Calculate performance metrics for device type"""
        if not entries:
            return {'avg_duration': 0, 'slow_requests': 0, 'very_slow_requests': 0}
        
        durations = [e['duration'] for e in entries]
        slow_count = len([e for e in entries if e['is_slow']])
        very_slow_count = len([e for e in entries if e['is_very_slow']])
        
        return {
            'avg_duration': sum(durations) / len(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'total_requests': len(entries),
            'slow_requests': slow_count,
            'very_slow_requests': very_slow_count,
            'slow_percentage': (slow_count / len(entries)) * 100,
            'success_rate': len([e for e in entries if e['status_code'] == 200]) / len(entries) * 100
        }
    
    def _get_slowest_endpoints(self, entries: List[Dict], limit: int = 10) -> List[Dict]:
        """Get slowest endpoints for optimization"""
        endpoint_metrics = {}
        
        for entry in entries:
            endpoint = entry['endpoint']
            if endpoint not in endpoint_metrics:
                endpoint_metrics[endpoint] = {
                    'total_duration': 0,
                    'request_count': 0,
                    'slow_count': 0,
                    'mobile_count': 0
                }
            
            metrics = endpoint_metrics[endpoint]
            metrics['total_duration'] += entry['duration']
            metrics['request_count'] += 1
            if entry['is_slow']:
                metrics['slow_count'] += 1
            if entry['is_mobile']:
                metrics['mobile_count'] += 1
        
        # Calculate averages and sort by average duration
        slowest = []
        for endpoint, metrics in endpoint_metrics.items():
            avg_duration = metrics['total_duration'] / metrics['request_count']
            slowest.append({
                'endpoint': endpoint,
                'avg_duration': avg_duration,
                'request_count': metrics['request_count'],
                'slow_percentage': (metrics['slow_count'] / metrics['request_count']) * 100,
                'mobile_percentage': (metrics['mobile_count'] / metrics['request_count']) * 100
            })
        
        return sorted(slowest, key=lambda x: x['avg_duration'], reverse=True)[:limit]
    
    def _get_device_breakdown(self, entries: List[Dict]) -> Dict[str, int]:
        """Get breakdown by device type"""
        breakdown = {}
        for entry in entries:
            device_type = entry['device_type']
            breakdown[device_type] = breakdown.get(device_type, 0) + 1
        return breakdown
    
    def _identify_optimization_opportunities(self, entries: List[Dict]) -> List[str]:
        """Identify optimization opportunities"""
        opportunities = []
        
        mobile_entries = [e for e in entries if e['is_mobile']]
        if not mobile_entries:
            return opportunities
        
        mobile_slow_rate = len([e for e in mobile_entries if e['is_slow']]) / len(mobile_entries)
        
        if mobile_slow_rate > 0.2:  # More than 20% slow requests
            opportunities.append("High mobile slow request rate - consider caching optimization")
        
        if mobile_slow_rate > 0.1:  # More than 10% slow requests
            opportunities.append("Mobile performance could be improved with image optimization")
        
        # Check for specific slow endpoints
        endpoint_performance = {}
        for entry in mobile_entries:
            endpoint = entry['endpoint']
            if endpoint not in endpoint_performance:
                endpoint_performance[endpoint] = []
            endpoint_performance[endpoint].append(entry['duration'])
        
        for endpoint, durations in endpoint_performance.items():
            avg_duration = sum(durations) / len(durations)
            if avg_duration > 2.0:  # Average over 2 seconds
                opportunities.append(f"Endpoint {endpoint} is consistently slow on mobile")
        
        return opportunities
    
    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure"""
        return {
            'summary': {
                'total_requests': 0,
                'mobile_requests': 0,
                'desktop_requests': 0,
                'mobile_percentage': 0,
                'time_period_hours': 0
            },
            'mobile_performance': {'avg_duration': 0, 'slow_requests': 0, 'very_slow_requests': 0},
            'desktop_performance': {'avg_duration': 0, 'slow_requests': 0, 'very_slow_requests': 0},
            'slowest_endpoints': [],
            'device_breakdown': {},
            'optimization_opportunities': []
        }
    
    def optimize_mobile_response(self, response_data: Any, endpoint: str) -> Any:
        """
        Optimize response for mobile devices
        
        Args:
            response_data: Response data
            endpoint: Request endpoint
            
        Returns:
            Optimized response data
        """
        if not hasattr(g, 'mobile_performance') or not g.mobile_performance['is_mobile']:
            return response_data
        
        device_type = g.mobile_performance['device_type']
        
        # Apply mobile-specific optimizations
        if isinstance(response_data, str):
            # Compress HTML/CSS/JS for mobile
            if self.optimization_rules['css_minification_enabled']:
                response_data = self._minify_css_in_html(response_data)
            
            if self.optimization_rules['js_compression_enabled']:
                response_data = self._compress_js_in_html(response_data)
        
        return response_data
    
    def _minify_css_in_html(self, html_content: str) -> str:
        """Basic CSS minification in HTML"""
        import re
        
        # Remove CSS comments
        html_content = re.sub(r'/\*.*?\*/', '', html_content, flags=re.DOTALL)
        
        # Remove extra whitespace in CSS
        css_pattern = r'<style[^>]*>(.*?)</style>'
        def minify_css_block(match):
            css = match.group(1)
            # Remove extra whitespace and newlines
            css = re.sub(r'\s+', ' ', css)
            css = re.sub(r';\s*}', '}', css)
            css = re.sub(r'{\s*', '{', css)
            return f'<style>{css}</style>'
        
        return re.sub(css_pattern, minify_css_block, html_content, flags=re.DOTALL)
    
    def _compress_js_in_html(self, html_content: str) -> str:
        """Basic JavaScript compression in HTML"""
        import re
        
        # Remove JavaScript comments (simple approach)
        js_pattern = r'<script[^>]*>(.*?)</script>'
        def compress_js_block(match):
            js = match.group(1)
            # Remove single-line comments
            js = re.sub(r'//.*$', '', js, flags=re.MULTILINE)
            # Remove extra whitespace
            js = re.sub(r'\s+', ' ', js)
            return f'<script>{js}</script>'
        
        return re.sub(js_pattern, compress_js_block, html_content, flags=re.DOTALL)
    
    def clear_performance_log(self):
        """Clear performance log"""
        self.performance_log.clear()
    
    def export_performance_data(self, filepath: str = None) -> str:
        """
        Export performance data to JSON file
        
        Args:
            filepath: Optional file path
            
        Returns:
            str: File path where data was saved
        """
        if not filepath:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = f'mobile_performance_{timestamp}.json'
        
        data = {
            'export_timestamp': datetime.now().isoformat(),
            'performance_log': self.performance_log,
            'optimization_rules': self.optimization_rules,
            'metrics': self.get_mobile_performance_metrics()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        return filepath

# Global service instance
mobile_performance_service = MobilePerformanceService()
