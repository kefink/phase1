"""
Scalability Initialization for Hillview School Management System
Centralizes initialization of all scalability features
"""

import os
import logging
from typing import Dict, Any, Optional
from flask import Flask

# Import scalability modules
from .cache_manager import cache, warm_cache
from .background_tasks import task_queue, start_periodic_cleanup
from .session_manager import initialize_session_manager
from .enhanced_logging import setup_enhanced_logging, get_performance_stats
from .rate_limiter import initialize_rate_limiter

logger = logging.getLogger(__name__)

class ScalabilityManager:
    """
    Centralized manager for all scalability features
    """
    
    def __init__(self):
        self.initialized_features = {}
        self.config = {}
        self.redis_client = None
        
    def initialize_all(self, app: Flask, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Initialize all scalability features (db_pool removed)."""
        self.config = config or {}
        results = {'success': True, 'initialized': [], 'failed': [], 'warnings': []}
        logger.info("🚀 Initializing scalability features...")

        # Enhanced Logging
        try:
            setup_enhanced_logging(app, self.config.get('LOG_LEVEL', 'INFO'))
            self.initialized_features['logging'] = True
            results['initialized'].append('Enhanced Logging')
        except Exception as e:
            results['failed'].append(f'Enhanced Logging: {e}')

        # Redis
        try:
            self._initialize_redis()
            if self.redis_client:
                results['initialized'].append('Redis Connection')
            else:
                results['warnings'].append('Redis not available (fallback)')
        except Exception as e:
            results['warnings'].append(f'Redis initialization warning: {e}')

        # Database pool removed
        results['warnings'].append('Database pool skipped (managed by SQLAlchemy)')

        # Caching
        try:
            warm_cache()
            self.initialized_features['caching'] = True
            results['initialized'].append('Caching System')
        except Exception as e:
            results['failed'].append(f'Caching: {e}')

        # Session Management
        try:
            initialize_session_manager(
                redis_client=self.redis_client,
                session_dir=self.config.get('SESSION_DIR', 'sessions'),
                session_timeout=self.config.get('SESSION_TIMEOUT', 3600)
            )
            self.initialized_features['session_management'] = True
            results['initialized'].append('Session Management')
        except Exception as e:
            results['failed'].append(f'Session Management: {e}')

        # Rate Limiting
        try:
            initialize_rate_limiter(
                requests_per_minute=self.config.get('RATE_LIMIT_PER_MINUTE', 60),
                requests_per_hour=self.config.get('RATE_LIMIT_PER_HOUR', 1000),
                burst_capacity=self.config.get('RATE_LIMIT_BURST', 10)
            )
            self.initialized_features['rate_limiting'] = True
            results['initialized'].append('Rate Limiting')
        except Exception as e:
            results['failed'].append(f'Rate Limiting: {e}')

        # Background Tasks
        try:
            start_periodic_cleanup()
            self.initialized_features['background_tasks'] = True
            results['initialized'].append('Background Tasks')
        except Exception as e:
            results['failed'].append(f'Background Tasks: {e}')

        results['success'] = len(results['failed']) == 0
        return results
    
    def _initialize_redis(self):
        """Initialize Redis connection if available"""
        try:
            import redis
            
            redis_host = self.config.get('REDIS_HOST', 'localhost')
            redis_port = self.config.get('REDIS_PORT', 6379)
            redis_password = self.config.get('REDIS_PASSWORD')
            redis_db = self.config.get('REDIS_DB', 0)
            
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                password=redis_password,
                db=redis_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # Test connection
            self.redis_client.ping()
            
        except ImportError:
            logger.warning("Redis package not installed, using fallback storage")
            self.redis_client = None
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            self.redis_client = None
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of all scalability features
        
        Returns:
            Dictionary with health status
        """
        health = {
            'overall_status': 'healthy',
            'features': {},
            'performance': {},
            'recommendations': []
        }
        
        # Check each feature
        for feature, initialized in self.initialized_features.items():
            if not initialized:
                health['features'][feature] = 'not_initialized'
                health['overall_status'] = 'degraded'
                continue
            
            # Feature-specific health checks
            if feature == 'caching':
                try:
                    cache.get('health_check')
                    health['features'][feature] = 'healthy'
                except Exception:
                    health['features'][feature] = 'unhealthy'
                    health['overall_status'] = 'degraded'
            
            elif feature == 'db_pool':
                # Legacy placeholder
                health['features'][feature] = 'deprecated'
            
            elif feature == 'rate_limiting':
                try:
                    from .rate_limiter import get_rate_limiter
                    limiter = get_rate_limiter()
                    if limiter and limiter.enabled:
                        health['features'][feature] = 'healthy'
                    else:
                        health['features'][feature] = 'disabled'
                except Exception:
                    health['features'][feature] = 'unhealthy'
                    health['overall_status'] = 'degraded'
            
            else:
                health['features'][feature] = 'healthy'
        
        # Get performance metrics
        try:
            health['performance'] = get_performance_stats()
        except Exception as e:
            health['performance'] = {'error': str(e)}
        
        # Generate recommendations
        if health['overall_status'] == 'degraded':
            health['recommendations'].append('Some scalability features are not functioning properly')
        
        if not self.redis_client:
            health['recommendations'].append('Consider setting up Redis for improved performance')
        
        return health
    
    def optimize_performance(self) -> Dict[str, Any]:
        """
        Apply performance optimizations
        
        Returns:
            Dictionary with optimization results
        """
        results = {
            'applied': [],
            'failed': [],
            'recommendations': []
        }
        
        # Database optimizations
        try:
            from .database_utils import optimize_database_performance
            db_results = optimize_database_performance()
            if db_results.get('success'):
                results['applied'].extend(db_results.get('applied', []))
            results['failed'].extend(db_results.get('failed', []))
        except Exception as e:
            results['failed'].append(f'Database optimization: {str(e)}')
        
        # Cache warming
        try:
            warm_cache()
            results['applied'].append('Cache warming completed')
        except Exception as e:
            results['failed'].append(f'Cache warming: {str(e)}')
        
        # Cleanup old data
        try:
            from .background_tasks import cleanup_old_tasks
            cleanup_old_tasks()
            results['applied'].append('Background task cleanup completed')
        except Exception as e:
            results['failed'].append(f'Task cleanup: {str(e)}')
        
        return results
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive metrics for all scalability features
        
        Returns:
            Dictionary with metrics
        """
        metrics = {'timestamp': os.times(), 'features': {}}
        try:
            metrics['performance'] = get_performance_stats()
        except Exception as e:  # pragma: no cover
            metrics['performance'] = {'error': str(e)}
        metrics['features']['database_pool'] = {'status': 'removed'}
        try:
            from .rate_limiter import get_rate_limiter
            limiter = get_rate_limiter()
            if limiter:
                metrics['features']['rate_limiter'] = limiter.get_stats()
        except Exception as e:  # pragma: no cover
            metrics['features']['rate_limiter'] = {'error': str(e)}
        try:
            from .session_manager import get_session_manager
            session_mgr = get_session_manager()
            if session_mgr:
                metrics['features']['session_manager'] = session_mgr.get_session_stats()
        except Exception as e:  # pragma: no cover
            metrics['features']['session_manager'] = {'error': str(e)}
        return metrics

# Global scalability manager instance
scalability_manager = ScalabilityManager()

def initialize_scalability(app: Flask, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Initialize all scalability features for the application
    
    Args:
        app: Flask application instance
        config: Configuration dictionary
        
    Returns:
        Initialization results
    """
    return scalability_manager.initialize_all(app, config)

def get_scalability_health() -> Dict[str, Any]:
    """Get health status of scalability features"""
    return scalability_manager.get_health_status()

def optimize_application_performance() -> Dict[str, Any]:
    """Apply performance optimizations"""
    return scalability_manager.optimize_performance()

def get_scalability_metrics() -> Dict[str, Any]:
    """Get comprehensive scalability metrics"""
    return scalability_manager.get_metrics()

if __name__ == "__main__":
    # Test scalability initialization
    print("Testing scalability initialization...")
    
    # Create a mock Flask app
    class MockApp:
        def __init__(self):
            self.logger = logging.getLogger('test_app')
    
    app = MockApp()
    
    # Test configuration
    test_config = {
        'LOG_LEVEL': 'DEBUG',
        'REDIS_HOST': 'localhost',
        'REDIS_PORT': 6379,
        'DB_MIN_CONNECTIONS': 3,
        'DB_MAX_CONNECTIONS': 10,
        'RATE_LIMIT_PER_MINUTE': 30
    }
    
    # Initialize scalability features
    results = initialize_scalability(app, test_config)
    print(f"Initialization results: {results}")
    
    # Get health status
    health = get_scalability_health()
    print(f"Health status: {health}")
    
    # Get metrics
    metrics = get_scalability_metrics()
    print(f"Metrics: {metrics}")
    
    print("Scalability test completed")
