"""
Mobile Performance API for Hillview School Management System
API endpoints for mobile performance monitoring and optimization
"""

from flask import Blueprint, request, jsonify, render_template, current_app
from functools import wraps
import time
import json
from datetime import datetime, timedelta

from ..services.mobile_performance_service import mobile_performance_service
from ..utils.mobile_performance_optimizer import mobile_optimizer
from ..services.auth_service import is_authenticated, get_role

# Create blueprint for mobile performance API
mobile_performance_api = Blueprint('mobile_performance_api', __name__, url_prefix='/api/mobile-performance')

def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated() or get_role() not in ['headteacher', 'admin']:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

@mobile_performance_api.route('/dashboard')
@admin_required
def performance_dashboard():
    """Mobile performance dashboard page"""
    return render_template('mobile_performance_dashboard.html')

@mobile_performance_api.route('/metrics')
@admin_required
def get_performance_metrics():
    """
    Get mobile performance metrics
    
    Query Parameters:
        hours (int): Number of hours to analyze (default: 24)
    """
    try:
        hours = int(request.args.get('hours', 24))
        metrics = mobile_performance_service.get_mobile_performance_metrics(hours)
        
        return jsonify({
            'success': True,
            'data': metrics,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mobile_performance_api.route('/metrics/real-time')
@admin_required
def get_realtime_metrics():
    """Get real-time performance metrics"""
    try:
        # Get recent performance data (last hour)
        metrics = mobile_performance_service.get_mobile_performance_metrics(1)
        
        # Add real-time data
        current_time = datetime.now()
        realtime_data = {
            'current_time': current_time.isoformat(),
            'active_sessions': len(mobile_performance_service.performance_log),
            'recent_requests': len([
                entry for entry in mobile_performance_service.performance_log
                if datetime.fromisoformat(entry['timestamp']) > current_time - timedelta(minutes=5)
            ]),
            'system_status': 'healthy',
            'optimization_status': {
                'compression_enabled': mobile_optimizer.optimization_config['enable_compression'],
                'mobile_cache_enabled': mobile_optimizer.optimization_config['enable_mobile_cache'],
                'image_optimization_enabled': mobile_optimizer.optimization_config['enable_image_optimization']
            }
        }
        
        return jsonify({
            'success': True,
            'data': {
                'metrics': metrics,
                'realtime': realtime_data
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mobile_performance_api.route('/optimize', methods=['POST'])
@admin_required
def trigger_optimization():
    """Trigger mobile performance optimization"""
    try:
        optimization_type = request.json.get('type', 'all')
        
        results = {
            'applied': [],
            'failed': [],
            'timestamp': datetime.now().isoformat()
        }
        
        if optimization_type in ['all', 'cache']:
            # Clear expired cache
            cleared = mobile_optimizer.clear_expired_cache()
            if cleared > 0:
                results['applied'].append(f'Cleared {cleared} expired cache entries')
            else:
                results['applied'].append('Cache is already optimized')
        
        if optimization_type in ['all', 'compression']:
            # Enable compression
            mobile_optimizer.optimization_config['enable_compression'] = True
            results['applied'].append('Response compression enabled')
        
        if optimization_type in ['all', 'images']:
            # Enable image optimization
            mobile_optimizer.optimization_config['enable_image_optimization'] = True
            results['applied'].append('Image optimization enabled')
        
        if optimization_type in ['all', 'minification']:
            # Enable CSS/JS minification
            mobile_optimizer.optimization_config['enable_css_minification'] = True
            mobile_optimizer.optimization_config['enable_js_minification'] = True
            results['applied'].append('CSS/JS minification enabled')
        
        return jsonify({
            'success': True,
            'data': results
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mobile_performance_api.route('/device-stats')
@admin_required
def get_device_statistics():
    """Get device usage statistics"""
    try:
        # Analyze device types from performance log
        device_stats = {}
        total_requests = len(mobile_performance_service.performance_log)
        
        if total_requests == 0:
            return jsonify({
                'success': True,
                'data': {
                    'total_requests': 0,
                    'device_breakdown': {},
                    'mobile_percentage': 0
                }
            })
        
        for entry in mobile_performance_service.performance_log:
            device_type = entry['device_type']
            if device_type not in device_stats:
                device_stats[device_type] = {
                    'count': 0,
                    'avg_duration': 0,
                    'slow_requests': 0,
                    'durations': []
                }
            
            device_stats[device_type]['count'] += 1
            device_stats[device_type]['durations'].append(entry['duration'])
            if entry['is_slow']:
                device_stats[device_type]['slow_requests'] += 1
        
        # Calculate averages
        for device_type, stats in device_stats.items():
            if stats['durations']:
                stats['avg_duration'] = sum(stats['durations']) / len(stats['durations'])
                stats['percentage'] = (stats['count'] / total_requests) * 100
                stats['slow_percentage'] = (stats['slow_requests'] / stats['count']) * 100
            del stats['durations']  # Remove raw data
        
        mobile_requests = sum(
            stats['count'] for device_type, stats in device_stats.items()
            if device_type in ['mobile', 'tablet']
        )
        
        return jsonify({
            'success': True,
            'data': {
                'total_requests': total_requests,
                'device_breakdown': device_stats,
                'mobile_percentage': (mobile_requests / total_requests) * 100 if total_requests > 0 else 0
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mobile_performance_api.route('/slowest-endpoints')
@admin_required
def get_slowest_endpoints():
    """Get slowest endpoints for optimization"""
    try:
        limit = int(request.args.get('limit', 10))
        device_filter = request.args.get('device', 'all')  # all, mobile, tablet, desktop
        
        # Filter entries by device type if specified
        entries = mobile_performance_service.performance_log
        if device_filter != 'all':
            entries = [e for e in entries if e['device_type'] == device_filter]
        
        # Group by endpoint
        endpoint_stats = {}
        for entry in entries:
            endpoint = entry['endpoint']
            if endpoint not in endpoint_stats:
                endpoint_stats[endpoint] = {
                    'total_duration': 0,
                    'request_count': 0,
                    'slow_count': 0,
                    'mobile_count': 0,
                    'error_count': 0
                }
            
            stats = endpoint_stats[endpoint]
            stats['total_duration'] += entry['duration']
            stats['request_count'] += 1
            
            if entry['is_slow']:
                stats['slow_count'] += 1
            if entry['is_mobile']:
                stats['mobile_count'] += 1
            if entry['status_code'] != 200:
                stats['error_count'] += 1
        
        # Calculate averages and sort
        slowest_endpoints = []
        for endpoint, stats in endpoint_stats.items():
            if stats['request_count'] > 0:
                avg_duration = stats['total_duration'] / stats['request_count']
                slowest_endpoints.append({
                    'endpoint': endpoint,
                    'avg_duration': avg_duration,
                    'request_count': stats['request_count'],
                    'slow_percentage': (stats['slow_count'] / stats['request_count']) * 100,
                    'mobile_percentage': (stats['mobile_count'] / stats['request_count']) * 100,
                    'error_rate': (stats['error_count'] / stats['request_count']) * 100
                })
        
        # Sort by average duration and limit results
        slowest_endpoints.sort(key=lambda x: x['avg_duration'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': {
                'endpoints': slowest_endpoints[:limit],
                'filter': device_filter,
                'total_analyzed': len(entries)
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mobile_performance_api.route('/export', methods=['POST'])
@admin_required
def export_performance_data():
    """Export performance data to file"""
    try:
        export_format = request.json.get('format', 'json')  # json, csv
        hours = int(request.json.get('hours', 24))
        
        if export_format == 'json':
            # Export as JSON
            filepath = mobile_performance_service.export_performance_data()
            
            return jsonify({
                'success': True,
                'data': {
                    'filepath': filepath,
                    'format': 'json',
                    'exported_at': datetime.now().isoformat()
                }
            })
        
        else:
            return jsonify({
                'success': False,
                'error': f'Export format {export_format} not supported'
            }), 400
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mobile_performance_api.route('/config', methods=['GET', 'POST'])
@admin_required
def performance_configuration():
    """Get or update performance configuration"""
    if request.method == 'GET':
        return jsonify({
            'success': True,
            'data': {
                'optimization_config': mobile_optimizer.optimization_config,
                'service_rules': mobile_performance_service.optimization_rules
            }
        })
    
    elif request.method == 'POST':
        try:
            config_updates = request.json
            
            # Update optimization config
            if 'optimization_config' in config_updates:
                mobile_optimizer.optimization_config.update(config_updates['optimization_config'])
            
            # Update service rules
            if 'service_rules' in config_updates:
                mobile_performance_service.optimization_rules.update(config_updates['service_rules'])
            
            return jsonify({
                'success': True,
                'message': 'Configuration updated successfully',
                'data': {
                    'optimization_config': mobile_optimizer.optimization_config,
                    'service_rules': mobile_performance_service.optimization_rules
                }
            })
        
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

@mobile_performance_api.route('/health')
def performance_health_check():
    """Health check for performance monitoring system"""
    try:
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'performance_log_size': len(mobile_performance_service.performance_log),
            'cache_size': len(mobile_optimizer.mobile_cache),
            'optimization_enabled': {
                'compression': mobile_optimizer.optimization_config['enable_compression'],
                'mobile_cache': mobile_optimizer.optimization_config['enable_mobile_cache'],
                'image_optimization': mobile_optimizer.optimization_config['enable_image_optimization']
            }
        }
        
        return jsonify({
            'success': True,
            'data': health_data
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'status': 'unhealthy'
        }), 500
