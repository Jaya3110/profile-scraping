from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import os
import asyncio
from dotenv import load_dotenv
from typing import List, Optional
import uvicorn

from models import Profile, ScrapingRequest, ScrapingResponse, ScrapingMetadata
from scraping_service import ProfileScrapingService
from rate_limiter import RateLimiter

# Load environment variables
load_dotenv()

app = FastAPI(
    title="User Profile Scraper API",
    description="AI-powered web scraping service for extracting user profiles",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
scraping_service = ProfileScrapingService()
rate_limiter = RateLimiter(max_requests=10, window_seconds=60)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    if not rate_limiter.is_allowed(client_ip):
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded. Please try again later."}
        )
    
    response = await call_next(request)
    return response

@app.get("/")
async def root():
    return {"message": "User Profile Scraper API", "status": "running"}

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "profile-scraper"
    }

@app.post("/api/validate-url")
async def validate_url(request: ScrapingRequest):
    """Validate URL format and check if it's accessible"""
    try:
        is_valid = await scraping_service.validate_url(request.url)
        return {
            "valid": is_valid,
            "url": request.url,
            "message": "URL is valid and accessible" if is_valid else "URL is invalid or not accessible"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/scrape", response_model=ScrapingResponse)
async def scrape_profiles(request: ScrapingRequest):
    """Main endpoint for scraping user profiles from a website - OPTIMIZED FOR SPEED"""
    try:
        print(f"🔍 API: Starting scrape for URL: {request.url}")
        start_time = time.time()
        
        # Validate URL first
        print(f"🔍 API: Validating URL...")
        url_str = str(request.url)
        if not await scraping_service.validate_url(url_str):
            print(f"❌ API: URL validation failed")
            raise HTTPException(status_code=400, detail="Invalid or inaccessible URL")
        print(f"✅ API: URL validation passed")
        
        # Scrape profiles with optimized settings
        print(f"🔍 API: Calling scraping service...")
        url_str = str(request.url)
        print(f"🔍 API: URL converted to string: {url_str}")
        
        # Use shorter timeout for faster response
        profiles = await asyncio.wait_for(
            scraping_service.scrape_profiles(url_str), 
            timeout=25.0  # Reduced from 30s to 25s
        )
        
        print(f"🎯 API: Scraping service returned: {len(profiles)} profiles")
        
        # Debug: Show profile details
        for i, profile in enumerate(profiles):
            print(f"  API Profile {i+1}: {profile.name} | {profile.title} | {profile.company}")
        
        processing_time = time.time() - start_time
        
        metadata = ScrapingMetadata(
            url=str(request.url),
            scraped_at=time.time(),
            processing_time=round(processing_time, 2),
            profiles_found=len(profiles)
        )
        
        print(f"📤 API: Sending response with {len(profiles)} profiles")
        
        return ScrapingResponse(
            success=True,
            profiles=profiles,
            metadata=metadata
        )
        
    except asyncio.TimeoutError:
        print(f"⏰ API: Request timed out")
        raise HTTPException(status_code=408, detail="Request timed out. Please try again.")
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ API: Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

@app.get("/api/profiles")
async def get_cached_profiles():
    """Get recently scraped profiles from cache"""
    profiles = scraping_service.get_cached_profiles()
    return {
        "success": True,
        "profiles": profiles,
        "count": len(profiles)
    }

   if __name__ == "__main__":
       import uvicorn
       port = int(os.getenv("PORT", 8000))
       uvicorn.run(app, host="0.0.0.0", port=port)
