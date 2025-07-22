import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from typing import Optional

from database import Database
from tld_service import TLDService
from auth_service import AuthService
from models import (
    TLDValidationRequest, 
    TLDValidationResponse, 
    APIKeyGenerationResponse,
    CacheInfo
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "0.0.0.0")
TLD_URL = os.getenv("TLD_URL", "https://data.iana.org/TLD/tlds-alpha-by-domain.txt")
TLD_UPDATE_INTERVAL = int(os.getenv("TLD_UPDATE_INTERVAL_HOURS", 24))
DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/tld_cache.db")
API_KEY_HEADER = os.getenv("API_KEY_HEADER", "X-API-Key")

# Global instances
database = None
tld_service = None
auth_service = None
scheduler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global database, tld_service, auth_service, scheduler
    
    # Initialize services
    database = Database(DATABASE_PATH)
    tld_service = TLDService(database, TLD_URL, TLD_UPDATE_INTERVAL)
    auth_service = AuthService(database)
    
    # Initialize TLD service
    await tld_service.initialize()
    
    # Setup scheduler for periodic updates
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        tld_service.fetch_and_store_tlds,
        'interval',
        hours=TLD_UPDATE_INTERVAL,
        id='tld_update'
    )
    scheduler.start()
    
    logger.info("Application started successfully")
    yield
    
    # Cleanup
    if scheduler:
        scheduler.shutdown()

# Create FastAPI app
app = FastAPI(
    title="TLD Validator API",
    description="Validate Top Level Domains against the official IANA list",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get API key from header
async def get_api_key(api_key: str = Header(..., alias=API_KEY_HEADER)):
    if not auth_service.validate_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the frontend HTML"""
    frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    if os.path.exists(frontend_path):
        with open(frontend_path, "r") as f:
            return HTMLResponse(content=f.read())
    raise HTTPException(status_code=404, detail="Frontend not found")


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    cache_info = tld_service.get_cache_info()
    return {
        "status": "healthy",
        "cache": cache_info
    }

@app.post("/api/validate-tld", response_model=TLDValidationResponse)
async def validate_tld(
    request: TLDValidationRequest,
    api_key: str = Depends(get_api_key)
):
    """Validate a TLD"""
    try:
        # If domain is provided, extract TLD
        if request.domain and not request.tld:
            extracted_tld = tld_service.extract_tld(request.domain)
            if not extracted_tld:
                return TLDValidationResponse(
                    is_valid=False,
                    message="Could not extract TLD from domain",
                    tld="",
                    domain=request.domain
                )
            tld_to_check = extracted_tld
        else:
            tld_to_check = request.tld.upper().strip()
        
        # Validate the TLD
        is_valid, message = tld_service.validate_tld(tld_to_check)
        
        return TLDValidationResponse(
            is_valid=is_valid,
            message=message,
            tld=tld_to_check,
            domain=request.domain
        )
        
    except Exception as e:
        logger.error(f"Error validating TLD: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/validate-tld", response_model=TLDValidationResponse)
async def validate_tld_get(
    tld: str,
    domain: Optional[str] = None,
    api_key: str = Depends(get_api_key)
):
    """Validate TLD via GET request"""
    return await validate_tld(
        TLDValidationRequest(tld=tld, domain=domain),
        api_key
    )

@app.post("/api/generate-key", response_model=APIKeyGenerationResponse)
async def generate_api_key():
    """Generate a new API key"""
    try:
        key = auth_service.generate_api_key()
        return APIKeyGenerationResponse(
            key=key,
            message="API key generated successfully"
        )
    except Exception as e:
        logger.error(f"Error generating API key: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate API key")

@app.get("/api/keys")
async def list_api_keys(api_key: str = Depends(get_api_key)):
    """List all API keys (requires valid API key)"""
    try:
        keys = auth_service.get_api_keys()
        return [
            {
                "key": row["key"],
                "created_at": row["created_at"],
                "usage_count": row["usage_count"],
                "is_active": bool(row["is_active"])
            }
            for row in keys
        ]
    except Exception as e:
        logger.error(f"Error listing API keys: {e}")
        raise HTTPException(status_code=500, detail="Failed to list API keys")

@app.get("/api/cache-info", response_model=CacheInfo)
async def get_cache_info():
    """Get TLD cache information"""
    cache_info = tld_service.get_cache_info()
    return CacheInfo(
        last_updated=cache_info["last_update"],
        tld_count=cache_info["tld_count"],
        is_fresh=cache_info["is_fresh"]
    )

@app.post("/api/update-tlds")
async def update_tlds(api_key: str = Depends(get_api_key)):
    """Manually trigger TLD update"""
    try:
        success = await tld_service.fetch_and_store_tlds()
        if success:
            return {"message": "TLDs updated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update TLDs")
    except Exception as e:
        logger.error(f"Error updating TLDs: {e}")
        raise HTTPException(status_code=500, detail="Failed to update TLDs")

# Mount static files
static_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/static", StaticFiles(directory=static_path), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host=HOST, port=PORT, reload=True)
