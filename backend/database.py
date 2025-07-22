import sqlite3
import os
from contextlib import contextmanager
from typing import Optional, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with self.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    key TEXT PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    usage_count INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1
                );
                
                CREATE TABLE IF NOT EXISTS tld_cache (
                    id INTEGER PRIMARY KEY,
                    last_updated TIMESTAMP,
                    tld_count INTEGER
                );
                
                CREATE TABLE IF NOT EXISTS tlds (
                    tld TEXT PRIMARY KEY,
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def execute_query(self, query: str, params: tuple = ()) -> list:
        """Execute a query and return results"""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute an update query and return affected rows"""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount
    
    def insert_api_key(self, key: str) -> bool:
        """Insert a new API key"""
        try:
            self.execute_update(
                "INSERT INTO api_keys (key) VALUES (?)",
                (key,)
            )
            return True
        except sqlite3.IntegrityError:
            return False
    
    def validate_api_key(self, key: str) -> bool:
        """Check if API key is valid"""
        result = self.execute_query(
            "SELECT 1 FROM api_keys WHERE key = ? AND is_active = 1",
            (key,)
        )
        return len(result) > 0
    
    def increment_usage(self, key: str) -> None:
        """Increment usage count for API key"""
        self.execute_update(
            "UPDATE api_keys SET usage_count = usage_count + 1 WHERE key = ?",
            (key,)
        )
    
    def get_api_keys(self) -> list:
        """Get all API keys"""
        return self.execute_query(
            "SELECT key, created_at, usage_count, is_active FROM api_keys ORDER BY created_at DESC"
        )
    
    def store_tlds(self, tlds: list) -> None:
        """Store TLDs in database"""
        with self.get_connection() as conn:
            conn.execute("DELETE FROM tlds")
            conn.executemany(
                "INSERT INTO tlds (tld) VALUES (?)",
                [(tld.upper(),) for tld in tlds]
            )
            conn.execute(
                "INSERT OR REPLACE INTO tld_cache (id, last_updated, tld_count) VALUES (1, ?, ?)",
                (datetime.now(), len(tlds))
            )
            conn.commit()
    
    def get_tlds(self) -> set:
        """Get all TLDs from database"""
        results = self.execute_query("SELECT tld FROM tlds")
        return {row['tld'].upper() for row in results}
    
    def get_cache_info(self) -> Optional[Dict[str, Any]]:
        """Get TLD cache information"""
        result = self.execute_query(
            "SELECT last_updated, tld_count FROM tld_cache WHERE id = 1"
        )
        if result:
            return dict(result[0])
        return None
