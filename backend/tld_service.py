import httpx
import logging
import re
from typing import Optional, Set, Tuple
from datetime import datetime, timedelta
from database import Database

logger = logging.getLogger(__name__)

class TLDService:
    def __init__(self, database: Database, tld_url: str, update_interval_hours: int = 24):
        self.db = database
        self.tld_url = tld_url
        self.update_interval = timedelta(hours=update_interval_hours)
        self._tlds: Set[str] = set()
        self._last_update: Optional[datetime] = None
    
    async def initialize(self):
        """Initialize the TLD service"""
        await self.load_tlds()
    
    async def load_tlds(self) -> bool:
        """Load TLDs from database or fetch from IANA"""
        cached_tlds = self.db.get_tlds()
        cache_info = self.db.get_cache_info()
        
        if cached_tlds and cache_info and cache_info.get('last_updated'):
            try:
                self._tlds = cached_tlds
                self._last_update = datetime.fromisoformat(cache_info['last_updated'])
                
                # Check if cache is fresh
                if datetime.now() - self._last_update < self.update_interval:
                    logger.info(f"Loaded {len(self._tlds)} TLDs from cache")
                    return True
            except (ValueError, TypeError):
                logger.warning("Could not parse last_updated from cache. Refetching.")

        # Fetch fresh TLDs
        return await self.fetch_and_store_tlds()
    
    async def fetch_and_store_tlds(self) -> bool:
        """Fetch TLDs from IANA and store in database"""
        logger.info(f"Fetching TLDs from {self.tld_url}")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.tld_url, timeout=30.0)
                response.raise_for_status()
                
                # Parse TLDs from response
                tlds = []
                for line in response.text.splitlines():
                    line = line.strip().lower()
                    if line and not line.startswith('#'):
                        tlds.append(line)
                
                # Store in database
                self.db.store_tlds(tlds)
                self._tlds = set(tld.upper() for tld in tlds)
                self._last_update = datetime.now()
                
                logger.info(f"Fetched and stored {len(self._tlds)} TLDs from IANA")
                return True
                
        except httpx.RequestError as e:
            logger.error(f"Failed to fetch TLDs due to network error: {e}")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching TLDs: {e}")
            return False
    
    def extract_tld(self, domain: str) -> Optional[str]:
        """Extract TLD from domain name"""
        if not domain:
            return None
        
        domain = str(domain).lower().strip()
        # Remove protocol if present
        domain = re.sub(r'^https?://', '', domain)
        domain = re.sub(r'^www\.', '', domain)
        
        # Split by dots
        parts = domain.split('.')
        
        if len(parts) < 2:
            return None
        
        # Handle multi-level TLDs (e.g., co.uk, com.au)
        # Try different combinations from right to left
        for i in range(len(parts) - 1, 0, -1):
            tld_candidate = '.'.join(parts[i:]).upper()
            if tld_candidate in self._tlds:
                return tld_candidate
        
        # Fallback to last part if no multi-level match
        return parts[-1].upper() if parts else None
    
    def validate_tld(self, tld: str) -> Tuple[bool, str]:
        """Validate a TLD"""
        if not tld:
            return False, "TLD cannot be empty"
        
        tld = tld.upper().strip()
        
        if not self._tlds:
            return False, "TLD list not available. Please try again later."
        
        is_valid = tld in self._tlds
        message = f"TLD '{tld}' is {'valid' if is_valid else 'invalid'}"
        
        return is_valid, message
    
    def get_cache_info(self) -> dict:
        """Get cache information"""
        is_fresh = self._last_update and (datetime.now() - self._last_update < self.update_interval)
        return {
            "tld_count": len(self._tlds),
            "last_update": self._last_update.isoformat() if self._last_update else None,
            "is_fresh": is_fresh
        }
    
    def get_all_tlds(self) -> Set[str]:
        """Get all available TLDs"""
        return self._tlds.copy()
