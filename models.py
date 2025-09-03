from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

class SocialLinks(BaseModel):
    linkedin: Optional[str] = None
    twitter: Optional[str] = None
    github: Optional[str] = None
    website: Optional[str] = None
    instagram: Optional[str] = None
    facebook: Optional[str] = None

class Profile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: Optional[str] = None
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    image: Optional[str] = None
    bio: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    social_links: SocialLinks = Field(default_factory=SocialLinks)
    extracted_from: str
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0")
    extraction_strategy: str = "unknown"
    raw_data: Optional[Dict[str, Any]] = None

class ScrapingRequest(BaseModel):
    url: HttpUrl
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)
    max_profiles: Optional[int] = Field(default=10, ge=1, le=100)
    timeout: Optional[int] = Field(default=30, ge=10, le=120)

class ScrapingMetadata(BaseModel):
    url: str
    scraped_at: float
    processing_time: float
    profiles_found: int
    extraction_strategies_used: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

class ScrapingResponse(BaseModel):
    success: bool
    profiles: List[Profile]
    metadata: ScrapingMetadata
    error: Optional[str] = None

class ValidationResponse(BaseModel):
    valid: bool
    url: str
    message: str
    status_code: Optional[int] = None
    content_type: Optional[str] = None

class CacheEntry(BaseModel):
    url: str
    profiles: List[Profile]
    cached_at: datetime
    expires_at: datetime
    version: str = "1.0.0"

class ScrapingSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    url: str
    user_agent: str
    profiles_found: int
    processing_time: float
    strategies: List[str]
    created_at: datetime = Field(default_factory=datetime.now)
    status: str = "completed"  # pending, processing, completed, failed
    error: Optional[str] = None
