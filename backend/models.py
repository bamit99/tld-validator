from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class TLDValidationRequest(BaseModel):
    tld: Optional[str] = Field(None, description="The top-level domain to validate")
    domain: Optional[str] = Field(None, description="Full domain name for context")

class TLDValidationResponse(BaseModel):
    is_valid: bool
    message: str
    tld: str
    domain: Optional[str] = None

class APIKeyResponse(BaseModel):
    key: str
    created_at: datetime
    usage_count: int
    is_active: bool

class APIKeyGenerationResponse(BaseModel):
    key: str
    message: str

class CacheInfo(BaseModel):
    last_updated: Optional[datetime]
    tld_count: Optional[int]
    is_fresh: bool
