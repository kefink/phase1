"""
Database utilities for multi-tenant MySQL support.
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import TenantConfig

class DatabaseManager:
    """Manage database connections for multi-tenant architecture."""
    
    def __init__(self):
        self.engines = {}
        self.sessions = {}
    
    def get_tenant_engine(self, tenant_code):
        """Get or create database engine for a tenant."""
        if tenant_code not in self.engines:
            database_uri = TenantConfig.get_tenant_database_uri(tenant_code)
            self.engines[tenant_code] = create_engine(
                database_uri,
                pool_size=10,
                pool_timeout=20,
                pool_recycle=3600,
                pool_pre_ping=True
            )
        return self.engines[tenant_code]
    
    def get_master_engine(self):
        """Get master database engine."""
        if 'master' not in self.engines:
            database_uri = TenantConfig.get_master_database_uri()
            self.engines['master'] = create_engine(database_uri)
        return self.engines['master']
    
    def get_tenant_session(self, tenant_code):
        """Get database session for a tenant."""
        if tenant_code not in self.sessions:
            engine = self.get_tenant_engine(tenant_code)
            Session = sessionmaker(bind=engine)
            self.sessions[tenant_code] = Session()
        return self.sessions[tenant_code]
    
    def close_all_sessions(self):
        """Close all database sessions."""
        for session in self.sessions.values():
            session.close()
        self.sessions.clear()

# Global database manager instance
db_manager = DatabaseManager()

def get_current_tenant():
    """Get current tenant code from environment or request context."""
    return os.environ.get('TENANT_CODE', 'DEMO001')

def with_tenant_db(tenant_code=None):
    """Decorator to execute function with tenant database context."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            tenant = tenant_code or get_current_tenant()
            # Set up tenant database context
            return func(*args, **kwargs)
        return wrapper
    return decorator
