"""
Session Management for Hillview School Management System
Implements scalable session storage with Redis fallback to filesystem
"""

import os
import json
import time
import hashlib
import logging
from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta
from flask import session, request, current_app
import pickle
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SessionStore:
    """Base class for session storage backends"""
    
    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data by ID"""
        raise NotImplementedError
    
    def set(self, session_id: str, data: Dict[str, Any], ttl: int = 3600) -> bool:
        """Set session data with TTL"""
        raise NotImplementedError
    
    def delete(self, session_id: str) -> bool:
        """Delete session by ID"""
        raise NotImplementedError
    
    def cleanup_expired(self) -> int:
        """Clean up expired sessions"""
        raise NotImplementedError

class RedisSessionStore(SessionStore):
    """Redis-based session storage"""
    
    def __init__(self, redis_client, key_prefix: str = 'session:'):
        self.redis = redis_client
        self.key_prefix = key_prefix
        self.is_available = True
        
        try:
            self.redis.ping()
            logger.info("✅ Redis session store initialized")
        except Exception as e:
            logger.warning(f"⚠️ Redis session store unavailable: {e}")
            self.is_available = False
    
    def _make_key(self, session_id: str) -> str:
        """Generate Redis key for session"""
        return f"{self.key_prefix}{session_id}"
    
    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data from Redis"""
        if not self.is_available:
            return None
        
        try:
            key = self._make_key(session_id)
            data = self.redis.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error(f"Redis session get error: {e}")
        return None
    
    def set(self, session_id: str, data: Dict[str, Any], ttl: int = 3600) -> bool:
        """Set session data in Redis"""
        if not self.is_available:
            return False
        
        try:
            key = self._make_key(session_id)
            serialized_data = json.dumps(data, default=str)
            return self.redis.setex(key, ttl, serialized_data)
        except Exception as e:
            logger.error(f"Redis session set error: {e}")
            return False
    
    def delete(self, session_id: str) -> bool:
        """Delete session from Redis"""
        if not self.is_available:
            return False
        
        try:
            key = self._make_key(session_id)
            return bool(self.redis.delete(key))
        except Exception as e:
            logger.error(f"Redis session delete error: {e}")
            return False
    
    def cleanup_expired(self) -> int:
        """Redis handles expiration automatically"""
        return 0

class FileSystemSessionStore(SessionStore):
    """Filesystem-based session storage"""
    
    def __init__(self, session_dir: str = 'sessions'):
        self.session_dir = session_dir
        os.makedirs(session_dir, exist_ok=True)
        self.lock = threading.RLock()
        logger.info(f"✅ Filesystem session store initialized: {session_dir}")
    
    def _get_session_file(self, session_id: str) -> str:
        """Get session file path"""
        # Hash session ID for security
        hashed_id = hashlib.sha256(session_id.encode()).hexdigest()
        return os.path.join(self.session_dir, f"sess_{hashed_id}.json")
    
    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data from file"""
        session_file = self._get_session_file(session_id)
        
        with self.lock:
            try:
                if os.path.exists(session_file):
                    with open(session_file, 'r') as f:
                        data = json.load(f)
                    
                    # Check if session has expired
                    if data.get('expires_at', 0) > time.time():
                        return data.get('data', {})
                    else:
                        # Session expired, delete it
                        os.remove(session_file)
            except Exception as e:
                logger.error(f"Filesystem session get error: {e}")
        
        return None
    
    def set(self, session_id: str, data: Dict[str, Any], ttl: int = 3600) -> bool:
        """Set session data to file"""
        session_file = self._get_session_file(session_id)
        
        with self.lock:
            try:
                session_data = {
                    'data': data,
                    'created_at': time.time(),
                    'expires_at': time.time() + ttl
                }
                
                with open(session_file, 'w') as f:
                    json.dump(session_data, f, default=str)
                
                return True
            except Exception as e:
                logger.error(f"Filesystem session set error: {e}")
                return False
    
    def delete(self, session_id: str) -> bool:
        """Delete session file"""
        session_file = self._get_session_file(session_id)
        
        with self.lock:
            try:
                if os.path.exists(session_file):
                    os.remove(session_file)
                return True
            except Exception as e:
                logger.error(f"Filesystem session delete error: {e}")
                return False
    
    def cleanup_expired(self) -> int:
        """Clean up expired session files"""
        cleaned_count = 0
        current_time = time.time()
        
        with self.lock:
            try:
                for filename in os.listdir(self.session_dir):
                    if filename.startswith('sess_') and filename.endswith('.json'):
                        filepath = os.path.join(self.session_dir, filename)
                        try:
                            with open(filepath, 'r') as f:
                                data = json.load(f)
                            
                            if data.get('expires_at', 0) <= current_time:
                                os.remove(filepath)
                                cleaned_count += 1
                        except Exception:
                            # If we can't read the file, it's probably corrupted
                            try:
                                os.remove(filepath)
                                cleaned_count += 1
                            except Exception:
                                pass
            except Exception as e:
                logger.error(f"Session cleanup error: {e}")
        
        if cleaned_count > 0:
            logger.info(f"🧹 Cleaned up {cleaned_count} expired sessions")
        
        return cleaned_count

class SessionManager:
    """
    Centralized session management with multiple storage backends
    Provides stateless session handling for scalability
    """
    
    def __init__(self, primary_store: SessionStore, fallback_store: SessionStore = None):
        self.primary_store = primary_store
        self.fallback_store = fallback_store
        self.session_timeout = 3600  # 1 hour default
        
        # Start cleanup thread
        self._start_cleanup_thread()
        
        logger.info("✅ Session manager initialized")
    
    def _generate_session_id(self) -> str:
        """Generate a secure session ID"""
        timestamp = str(time.time())
        random_data = os.urandom(32)
        user_agent = request.headers.get('User-Agent', '')
        remote_addr = request.remote_addr or ''
        
        data = f"{timestamp}{random_data}{user_agent}{remote_addr}".encode()
        return hashlib.sha256(data).hexdigest()
    
    def create_session(self, user_data: Dict[str, Any], ttl: int = None) -> str:
        """
        Create a new session
        
        Args:
            user_data: User session data
            ttl: Time to live in seconds
            
        Returns:
            Session ID
        """
        if ttl is None:
            ttl = self.session_timeout
        
        session_id = self._generate_session_id()
        
        session_data = {
            'user_data': user_data,
            'created_at': datetime.now().isoformat(),
            'last_accessed': datetime.now().isoformat(),
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
            'csrf_token': self._generate_csrf_token()
        }
        
        # Try primary store first
        if self.primary_store.set(session_id, session_data, ttl):
            logger.debug(f"Session created in primary store: {session_id[:8]}...")
        elif self.fallback_store and self.fallback_store.set(session_id, session_data, ttl):
            logger.debug(f"Session created in fallback store: {session_id[:8]}...")
        else:
            logger.error("Failed to create session in any store")
            return None
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data by ID
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data or None if not found
        """
        if not session_id:
            return None
        
        # Try primary store first
        session_data = self.primary_store.get(session_id)
        
        # Try fallback store if primary fails
        if not session_data and self.fallback_store:
            session_data = self.fallback_store.get(session_id)
        
        if session_data:
            # Update last accessed time
            session_data['last_accessed'] = datetime.now().isoformat()
            self.update_session(session_id, session_data)
            
            logger.debug(f"Session retrieved: {session_id[:8]}...")
            return session_data
        
        return None
    
    def update_session(self, session_id: str, data: Dict[str, Any], ttl: int = None) -> bool:
        """
        Update session data
        
        Args:
            session_id: Session identifier
            data: Updated session data
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        if ttl is None:
            ttl = self.session_timeout
        
        # Try primary store first
        if self.primary_store.set(session_id, data, ttl):
            return True
        elif self.fallback_store and self.fallback_store.set(session_id, data, ttl):
            return True
        
        logger.error(f"Failed to update session: {session_id[:8]}...")
        return False
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete session
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful, False otherwise
        """
        if not session_id:
            return False
        
        # Delete from both stores
        primary_deleted = self.primary_store.delete(session_id)
        fallback_deleted = True
        
        if self.fallback_store:
            fallback_deleted = self.fallback_store.delete(session_id)
        
        logger.debug(f"Session deleted: {session_id[:8]}...")
        return primary_deleted or fallback_deleted
    
    def _generate_csrf_token(self) -> str:
        """Generate CSRF token for session"""
        return hashlib.sha256(os.urandom(32)).hexdigest()
    
    def validate_csrf_token(self, session_id: str, token: str) -> bool:
        """Validate CSRF token"""
        session_data = self.get_session(session_id)
        if session_data:
            return session_data.get('csrf_token') == token
        return False
    
    def _start_cleanup_thread(self):
        """Start background cleanup thread"""
        def cleanup_worker():
            while True:
                try:
                    time.sleep(3600)  # Run every hour
                    self.cleanup_expired_sessions()
                except Exception as e:
                    logger.error(f"Session cleanup thread error: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        logger.info("🧹 Started session cleanup thread")
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions from all stores"""
        try:
            primary_cleaned = self.primary_store.cleanup_expired()
            fallback_cleaned = 0
            
            if self.fallback_store:
                fallback_cleaned = self.fallback_store.cleanup_expired()
            
            total_cleaned = primary_cleaned + fallback_cleaned
            if total_cleaned > 0:
                logger.info(f"🧹 Cleaned up {total_cleaned} expired sessions")
        except Exception as e:
            logger.error(f"Session cleanup error: {e}")
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session management statistics"""
        return {
            'primary_store': type(self.primary_store).__name__,
            'fallback_store': type(self.fallback_store).__name__ if self.fallback_store else None,
            'session_timeout': self.session_timeout,
            'cleanup_enabled': True
        }

# Global session manager instance
_session_manager: Optional[SessionManager] = None

def initialize_session_manager(redis_client=None, session_dir: str = 'sessions', 
                             session_timeout: int = 3600):
    """
    Initialize global session manager
    
    Args:
        redis_client: Redis client instance (optional)
        session_dir: Directory for filesystem sessions
        session_timeout: Session timeout in seconds
    """
    global _session_manager
    
    # Create stores
    if redis_client:
        primary_store = RedisSessionStore(redis_client)
        fallback_store = FileSystemSessionStore(session_dir)
    else:
        primary_store = FileSystemSessionStore(session_dir)
        fallback_store = None
    
    _session_manager = SessionManager(primary_store, fallback_store)
    _session_manager.session_timeout = session_timeout
    
    logger.info("✅ Global session manager initialized")

def get_session_manager() -> Optional[SessionManager]:
    """Get global session manager instance"""
    return _session_manager

# Flask integration helpers
def create_user_session(user_data: Dict[str, Any]) -> str:
    """Create session for Flask integration"""
    if not _session_manager:
        raise RuntimeError("Session manager not initialized")
    return _session_manager.create_session(user_data)

def get_current_session() -> Optional[Dict[str, Any]]:
    """Get current session data for Flask integration"""
    if not _session_manager:
        return None
    
    session_id = session.get('session_id')
    if session_id:
        return _session_manager.get_session(session_id)
    return None

def destroy_current_session() -> bool:
    """Destroy current session for Flask integration"""
    if not _session_manager:
        return False
    
    session_id = session.get('session_id')
    if session_id:
        result = _session_manager.delete_session(session_id)
        session.clear()
        return result
    return False

if __name__ == "__main__":
    # Test session management
    print("Testing session management...")
    
    # Initialize with filesystem store
    initialize_session_manager(session_timeout=300)  # 5 minutes
    
    # Create test session
    user_data = {
        'user_id': 123,
        'username': 'test_user',
        'role': 'teacher'
    }
    
    session_id = _session_manager.create_session(user_data)
    print(f"Created session: {session_id[:8]}...")
    
    # Retrieve session
    retrieved_data = _session_manager.get_session(session_id)
    print(f"Retrieved session: {retrieved_data}")
    
    # Update session
    retrieved_data['last_login'] = datetime.now().isoformat()
    _session_manager.update_session(session_id, retrieved_data)
    
    # Get stats
    stats = _session_manager.get_session_stats()
    print(f"Session stats: {stats}")
    
    # Clean up
    _session_manager.delete_session(session_id)
    print("Session deleted")
