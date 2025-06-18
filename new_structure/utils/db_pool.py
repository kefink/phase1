"""
Database Connection Pooling for Hillview School Management System
Implements efficient database connection management for scalability
"""

import sqlite3
import threading
import time
import logging
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from queue import Queue, Empty, Full
from dataclasses import dataclass
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ConnectionStats:
    """Connection pool statistics"""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    created_connections: int = 0
    closed_connections: int = 0
    failed_connections: int = 0
    peak_connections: int = 0
    total_requests: int = 0
    failed_requests: int = 0

class PooledConnection:
    """Wrapper for pooled database connections"""
    
    def __init__(self, connection, pool, connection_id: str):
        self.connection = connection
        self.pool = pool
        self.connection_id = connection_id
        self.created_at = datetime.now()
        self.last_used = datetime.now()
        self.use_count = 0
        self.is_active = False
    
    def execute(self, query: str, params: tuple = ()):
        """Execute query with connection"""
        self.last_used = datetime.now()
        self.use_count += 1
        return self.connection.execute(query, params)
    
    def executemany(self, query: str, params_list: List[tuple]):
        """Execute many queries with connection"""
        self.last_used = datetime.now()
        self.use_count += 1
        return self.connection.executemany(query, params_list)
    
    def fetchall(self):
        """Fetch all results"""
        return self.connection.fetchall()
    
    def fetchone(self):
        """Fetch one result"""
        return self.connection.fetchone()
    
    def commit(self):
        """Commit transaction"""
        return self.connection.commit()
    
    def rollback(self):
        """Rollback transaction"""
        return self.connection.rollback()
    
    def close(self):
        """Return connection to pool"""
        if self.pool:
            self.pool.return_connection(self)
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()

class DatabaseConnectionPool:
    """
    Database connection pool for efficient connection management
    Supports SQLite with plans for MySQL/PostgreSQL
    """
    
    def __init__(self, database_path: str, min_connections: int = 5, 
                 max_connections: int = 20, max_idle_time: int = 300):
        """
        Initialize connection pool
        
        Args:
            database_path: Path to database file
            min_connections: Minimum connections to maintain
            max_connections: Maximum connections allowed
            max_idle_time: Maximum idle time before closing connection (seconds)
        """
        self.database_path = database_path
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.max_idle_time = max_idle_time
        
        self.pool = Queue(maxsize=max_connections)
        self.active_connections = {}
        self.stats = ConnectionStats()
        self.lock = threading.RLock()
        
        # Initialize minimum connections
        self._initialize_pool()
        
        # Start maintenance thread
        self._start_maintenance_thread()
        
        logger.info(f"✅ Database connection pool initialized: {database_path}")
        logger.info(f"   Min connections: {min_connections}, Max: {max_connections}")
    
    def _initialize_pool(self):
        """Initialize pool with minimum connections"""
        with self.lock:
            for i in range(self.min_connections):
                try:
                    conn = self._create_connection()
                    if conn:
                        self.pool.put(conn, block=False)
                        self.stats.idle_connections += 1
                except Full:
                    break
    
    def _create_connection(self) -> Optional[PooledConnection]:
        """Create a new database connection"""
        try:
            # Create SQLite connection with optimizations
            conn = sqlite3.connect(
                self.database_path,
                check_same_thread=False,
                timeout=30.0
            )
            
            # Enable row factory for dict-like access
            conn.row_factory = sqlite3.Row
            
            # SQLite optimizations
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA mmap_size=268435456")  # 256MB
            
            connection_id = f"conn_{int(time.time() * 1000)}_{id(conn)}"
            pooled_conn = PooledConnection(conn, self, connection_id)
            
            with self.lock:
                self.stats.created_connections += 1
                self.stats.total_connections += 1
                if self.stats.total_connections > self.stats.peak_connections:
                    self.stats.peak_connections = self.stats.total_connections
            
            logger.debug(f"Created new connection: {connection_id}")
            return pooled_conn
            
        except Exception as e:
            with self.lock:
                self.stats.failed_connections += 1
            logger.error(f"Failed to create connection: {e}")
            return None
    
    def get_connection(self, timeout: int = 30) -> Optional[PooledConnection]:
        """
        Get connection from pool
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Pooled connection or None if timeout
        """
        with self.lock:
            self.stats.total_requests += 1
        
        start_time = time.time()
        
        # Try to get existing connection from pool
        try:
            conn = self.pool.get(timeout=timeout)
            if conn and self._is_connection_valid(conn):
                with self.lock:
                    self.active_connections[conn.connection_id] = conn
                    conn.is_active = True
                    self.stats.active_connections += 1
                    self.stats.idle_connections -= 1
                
                logger.debug(f"Retrieved connection from pool: {conn.connection_id}")
                return conn
        except Empty:
            pass
        
        # Create new connection if pool is empty and under max limit
        with self.lock:
            if self.stats.total_connections < self.max_connections:
                conn = self._create_connection()
                if conn:
                    self.active_connections[conn.connection_id] = conn
                    conn.is_active = True
                    self.stats.active_connections += 1
                    return conn
        
        # If we reach here, pool is exhausted
        elapsed = time.time() - start_time
        if elapsed >= timeout:
            with self.lock:
                self.stats.failed_requests += 1
            logger.warning(f"Connection pool exhausted, timeout after {elapsed:.2f}s")
            return None
        
        # Wait a bit and try again
        time.sleep(0.1)
        return self.get_connection(timeout - elapsed)
    
    def return_connection(self, conn: PooledConnection):
        """Return connection to pool"""
        if not conn or conn.connection_id not in self.active_connections:
            return
        
        with self.lock:
            # Remove from active connections
            del self.active_connections[conn.connection_id]
            conn.is_active = False
            self.stats.active_connections -= 1
            
            # Check if connection is still valid
            if self._is_connection_valid(conn):
                try:
                    self.pool.put(conn, block=False)
                    self.stats.idle_connections += 1
                    logger.debug(f"Returned connection to pool: {conn.connection_id}")
                except Full:
                    # Pool is full, close the connection
                    self._close_connection(conn)
            else:
                # Connection is invalid, close it
                self._close_connection(conn)
    
    def _is_connection_valid(self, conn: PooledConnection) -> bool:
        """Check if connection is still valid"""
        try:
            # Simple query to test connection
            conn.connection.execute("SELECT 1")
            
            # Check if connection is too old
            age = datetime.now() - conn.created_at
            if age.total_seconds() > self.max_idle_time * 10:  # 10x idle time for max age
                return False
            
            return True
        except Exception:
            return False
    
    def _close_connection(self, conn: PooledConnection):
        """Close a connection"""
        try:
            conn.connection.close()
            with self.lock:
                self.stats.closed_connections += 1
                self.stats.total_connections -= 1
            logger.debug(f"Closed connection: {conn.connection_id}")
        except Exception as e:
            logger.error(f"Error closing connection {conn.connection_id}: {e}")
    
    def _start_maintenance_thread(self):
        """Start background maintenance thread"""
        def maintenance_worker():
            while True:
                try:
                    time.sleep(60)  # Run every minute
                    self._cleanup_idle_connections()
                    self._ensure_minimum_connections()
                except Exception as e:
                    logger.error(f"Maintenance thread error: {e}")
        
        maintenance_thread = threading.Thread(target=maintenance_worker, daemon=True)
        maintenance_thread.start()
        logger.info("🔧 Started connection pool maintenance thread")
    
    def _cleanup_idle_connections(self):
        """Clean up idle connections that have been idle too long"""
        cutoff_time = datetime.now() - timedelta(seconds=self.max_idle_time)
        connections_to_close = []
        
        # Collect idle connections to close
        try:
            while True:
                conn = self.pool.get(block=False)
                if conn.last_used < cutoff_time and self.stats.idle_connections > self.min_connections:
                    connections_to_close.append(conn)
                else:
                    self.pool.put(conn, block=False)
                    break
        except Empty:
            pass
        
        # Close collected connections
        for conn in connections_to_close:
            self._close_connection(conn)
            with self.lock:
                self.stats.idle_connections -= 1
        
        if connections_to_close:
            logger.info(f"🧹 Cleaned up {len(connections_to_close)} idle connections")
    
    def _ensure_minimum_connections(self):
        """Ensure minimum number of connections are available"""
        with self.lock:
            needed = self.min_connections - self.stats.idle_connections
            
        if needed > 0:
            for _ in range(needed):
                conn = self._create_connection()
                if conn:
                    try:
                        self.pool.put(conn, block=False)
                        with self.lock:
                            self.stats.idle_connections += 1
                    except Full:
                        self._close_connection(conn)
                        break
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        with self.lock:
            return {
                'total_connections': self.stats.total_connections,
                'active_connections': self.stats.active_connections,
                'idle_connections': self.stats.idle_connections,
                'created_connections': self.stats.created_connections,
                'closed_connections': self.stats.closed_connections,
                'failed_connections': self.stats.failed_connections,
                'peak_connections': self.stats.peak_connections,
                'total_requests': self.stats.total_requests,
                'failed_requests': self.stats.failed_requests,
                'pool_size': self.pool.qsize(),
                'max_connections': self.max_connections,
                'min_connections': self.min_connections
            }
    
    def close_all(self):
        """Close all connections in the pool"""
        logger.info("🔒 Closing all database connections...")
        
        # Close active connections
        with self.lock:
            for conn in list(self.active_connections.values()):
                self._close_connection(conn)
            self.active_connections.clear()
        
        # Close idle connections
        try:
            while True:
                conn = self.pool.get(block=False)
                self._close_connection(conn)
        except Empty:
            pass
        
        logger.info("✅ All database connections closed")

# Global connection pool instance
_connection_pool: Optional[DatabaseConnectionPool] = None

def initialize_pool(database_path: str, min_connections: int = 5, 
                   max_connections: int = 20, max_idle_time: int = 300):
    """Initialize global connection pool"""
    global _connection_pool
    _connection_pool = DatabaseConnectionPool(
        database_path, min_connections, max_connections, max_idle_time
    )

def get_db_connection(timeout: int = 30) -> Optional[PooledConnection]:
    """Get database connection from global pool"""
    if not _connection_pool:
        raise RuntimeError("Connection pool not initialized. Call initialize_pool() first.")
    return _connection_pool.get_connection(timeout)

@contextmanager
def get_db_cursor(timeout: int = 30):
    """Context manager for database operations"""
    conn = get_db_connection(timeout)
    if not conn:
        raise RuntimeError("Could not get database connection")
    
    try:
        yield conn
    finally:
        conn.close()

def get_pool_stats() -> Dict[str, Any]:
    """Get connection pool statistics"""
    if not _connection_pool:
        return {}
    return _connection_pool.get_stats()

def close_pool():
    """Close the global connection pool"""
    global _connection_pool
    if _connection_pool:
        _connection_pool.close_all()
        _connection_pool = None

if __name__ == "__main__":
    # Test connection pool
    print("Testing database connection pool...")
    
    # Initialize pool
    initialize_pool("test.db", min_connections=2, max_connections=5)
    
    # Test getting connections
    connections = []
    for i in range(3):
        conn = get_db_connection()
        if conn:
            print(f"Got connection {i+1}: {conn.connection_id}")
            connections.append(conn)
    
    # Test context manager
    with get_db_cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print(f"Query result: {result}")
    
    # Return connections
    for conn in connections:
        conn.close()
    
    # Print stats
    stats = get_pool_stats()
    print(f"Pool stats: {stats}")
    
    # Close pool
    close_pool()
