import secrets
import logging
from database import Database

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, database: Database):
        self.db = database
    
    def generate_api_key(self) -> str:
        """Generate a new API key"""
        key = secrets.token_urlsafe(32)
        while not self.db.insert_api_key(key):
            key = secrets.token_urlsafe(32)
        
        logger.info(f"Generated new API key: {key[:8]}...")
        return key
    
    def validate_api_key(self, key: str) -> bool:
        """Validate an API key"""
        if not key:
            return False
        
        is_valid = self.db.validate_api_key(key)
        if is_valid:
            self.db.increment_usage(key)
        
        return is_valid
    
    def get_api_keys(self) -> list:
        """Get all API keys"""
        return self.db.get_api_keys()
    
    def revoke_api_key(self, key: str) -> bool:
        """Revoke an API key"""
        affected = self.db.execute_update(
            "UPDATE api_keys SET is_active = 0 WHERE key = ?",
            (key,)
        )
        return affected > 0
    
    def activate_api_key(self, key: str) -> bool:
        """Activate an API key"""
        affected = self.db.execute_update(
            "UPDATE api_keys SET is_active = 1 WHERE key = ?",
            (key,)
        )
        return affected > 0
