import google.generativeai as genai
from bs4 import BeautifulSoup
from typing import List, Optional, Dict, Any
import json
import re
from urllib.parse import urljoin

from models import Profile, SocialLinks

class AIProfileExtractor:
    def __init__(self, gemini_model=None):
        self.gemini_model = gemini_model
        self.max_retries = 3
        
        # AI extraction prompt template
        self.extraction_prompt = """
        Analyze this HTML content and extract any user profile information you can find. 
        Look for names, job titles, contact information, social media links, biographical information, and company details.
        
        Focus on:
        1. Person names (full names, first names, last names)
        2. Job titles, positions, or roles
        3. Email addresses
        4. Phone numbers
        5. Company or organization names
        6. Location information (city, country, etc.)
        7. Biographical descriptions or summaries
        8. Social media profiles (LinkedIn, Twitter, GitHub, etc.)
        9. Personal websites or portfolios
        10. Profile images or avatars
        
        Return the data in this exact JSON format:
        {
            "profiles": [
                {
                    "name": "string or null",
                    "title": "string or null", 
                    "email": "string or null",
                    "phone": "string or null",
                    "bio": "string or null",
                    "company": "string or null",
                    "location": "string or null",
                    "socialLinks": {
                        "linkedin": "string or null",
                        "twitter": "string or null",
                        "github": "string or null",
                        "website": "string or null",
                        "instagram": "string or null",
                        "facebook": "string or null"
                    },
                    "image": "string or null"
                }
            ]
        }
        
        Important rules:
        - Only include information you are confident about
        - If no profiles found, return empty profiles array
        - Clean and format the data (remove extra spaces, normalize)
        - For social links, extract the full URLs
        - For images, extract the full image URLs
        - Be conservative - quality over quantity
        - If unsure about a field, set it to null
        """
    
    async def extract(self, soup: BeautifulSoup, url: str) -> List[Profile]:
        """Extract profiles using AI analysis"""
        if not self.gemini_model:
            return []
        
        try:
            # Clean HTML for AI analysis
            cleaned_html = self.clean_html_for_ai(soup)
            
            # Extract profiles using AI
            ai_profiles = await self.extract_with_ai(cleaned_html, url)
            
            # Convert AI results to Profile objects
            profiles = []
            for ai_profile in ai_profiles:
                profile = self.convert_ai_profile(ai_profile, url)
                if profile:
                    profiles.append(profile)
            
            return profiles
            
        except Exception as e:
            print(f"AI extraction error: {e}")
            return []
    
    def clean_html_for_ai(self, soup: BeautifulSoup) -> str:
        """Clean HTML content for better AI analysis"""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Remove common noise elements
        noise_selectors = [
            '.advertisement', '.ads', '.banner', '.popup',
            '.cookie-notice', '.newsletter', '.sidebar',
            '.navigation', '.menu', '.breadcrumb'
        ]
        
        for selector in noise_selectors:
            for element in soup.select(selector):
                element.decompose()
        
        # Get text content with some structure
        text_content = []
        
        # Extract headings
        for heading in soup.find_all(['h1', 'h2', 'h3']):
            text_content.append(f"HEADING: {heading.get_text(strip=True)}")
        
        # Extract paragraphs and divs
        for element in soup.find_all(['p', 'div', 'span', 'a']):
            text = element.get_text(strip=True)
            if text and len(text) > 10:  # Only meaningful content
                text_content.append(text)
        
        # Extract links
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            text = link.get_text(strip=True)
            if text and href:
                text_content.append(f"LINK: {text} -> {href}")
        
        return "\n".join(text_content)
    
    async def extract_with_ai(self, html_content: str, url: str) -> List[Dict[str, Any]]:
        """Extract profiles using Gemini AI"""
        for attempt in range(self.max_retries):
            try:
                # Prepare the prompt
                full_prompt = f"{self.extraction_prompt}\n\nHTML Content:\n{html_content[:8000]}"  # Limit content length
                
                # Add delay between requests to avoid rate limiting (2-3 seconds)
                import asyncio
                if attempt == 0:
                    await asyncio.sleep(1)  # 1s delay for first request
                else:
                    await asyncio.sleep(2 + attempt)  # 2s, 3s, 4s delays for retries
                
                # Generate response
                response = await self.gemini_model.generate_content_async(full_prompt)
                
                # Parse the response
                if response.text:
                    # Try to extract JSON from the response
                    json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                    if json_match:
                        json_str = json_match.group()
                        result = json.loads(json_str)
                        
                        if 'profiles' in result and isinstance(result['profiles'], list):
                            return result['profiles']
                
                # If no valid JSON found, try to parse the text manually
                return self.parse_ai_response_manually(response.text)
                
            except json.JSONDecodeError as e:
                print(f"JSON parsing error (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    return []
                continue
                
            except Exception as e:
                print(f"AI extraction error (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    return []
                continue
        
        return []
    
    def parse_ai_response_manually(self, response_text: str) -> List[Dict[str, Any]]:
        """Manually parse AI response if JSON parsing fails"""
        profiles = []
        
        try:
            # Look for profile-like information in the text
            lines = response_text.split('\n')
            current_profile = {}
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Try to extract key-value pairs
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if key in ['name', 'title', 'email', 'phone', 'bio', 'company', 'location']:
                        current_profile[key] = value
                    elif key in ['linkedin', 'twitter', 'github', 'website', 'instagram', 'facebook']:
                        if 'socialLinks' not in current_profile:
                            current_profile['socialLinks'] = {}
                        current_profile['socialLinks'][key] = value
                    elif key == 'image':
                        current_profile['image'] = value
            
            # If we found any profile data, add it
            if current_profile:
                profiles.append(current_profile)
        
        except Exception as e:
            print(f"Manual parsing error: {e}")
        
        return profiles
    
    def convert_ai_profile(self, ai_profile: Dict[str, Any], url: str) -> Optional[Profile]:
        """Convert AI-extracted profile to Profile model"""
        try:
            # Extract social links
            social_links = SocialLinks()
            if 'socialLinks' in ai_profile:
                for platform, link in ai_profile['socialLinks'].items():
                    if link and hasattr(social_links, platform):
                        # Make URL absolute if needed
                        if link and not link.startswith(('http://', 'https://')):
                            link = urljoin(url, link)
                        setattr(social_links, platform, link)
            
            # Make image URL absolute
            image = ai_profile.get('image')
            if image and not image.startswith(('http://', 'https://')):
                image = urljoin(url, image)
            
            # Calculate confidence score
            confidence = self.calculate_ai_confidence(ai_profile)
            
            # Create profile
            profile = Profile(
                name=ai_profile.get('name'),
                title=ai_profile.get('title'),
                email=ai_profile.get('email'),
                phone=ai_profile.get('phone'),
                image=image,
                bio=ai_profile.get('bio'),
                company=ai_profile.get('company'),
                location=ai_profile.get('location'),
                social_links=social_links,
                extracted_from=url,
                confidence=confidence,
                extraction_strategy="ai_extraction",
                raw_data=ai_profile
            )
            
            # Only return if we have meaningful data
            if profile.name or profile.title or profile.email:
                return profile
            
        except Exception as e:
            print(f"Error converting AI profile: {e}")
        
        return None
    
    def calculate_ai_confidence(self, ai_profile: Dict[str, Any]) -> float:
        """Calculate confidence score for AI-extracted profile"""
        score = 0.0
        total_fields = 8
        
        # Basic information fields
        basic_fields = ['name', 'title', 'email', 'phone', 'bio', 'company', 'location', 'image']
        for field in basic_fields:
            if ai_profile.get(field):
                score += 0.1
        
        # Social links
        social_links = ai_profile.get('socialLinks', {})
        if social_links:
            for platform, link in social_links.items():
                if link:
                    score += 0.05
        
        # Bonus for having multiple fields
        filled_fields = sum(1 for field in basic_fields if ai_profile.get(field))
        if filled_fields >= 3:
            score += 0.1
        
        return min(score, 1.0)
