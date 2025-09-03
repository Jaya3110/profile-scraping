import asyncio
import httpx
import time
import random
from typing import Optional, Dict, Any, List
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import os
from datetime import datetime, timedelta

class ImprovedLinkedInScraper:
    def __init__(self):
        self.session_cookies = {}
        self.request_delay = (5, 10)  # Longer delays to avoid rate limiting
        self.last_request_time = 0
        self.rate_limit_delay = 60  # Wait 60 seconds if rate limited
        
    def get_stealth_headers(self, referer: Optional[str] = None) -> Dict[str, str]:
        """Get stealth headers that better avoid detection"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin' if referer else 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
        }
        
        if referer:
            headers['Referer'] = referer
            
        return headers
    
    async def respect_rate_limits(self):
        """Implement proper rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # Ensure minimum delay between requests
        min_delay = random.uniform(*self.request_delay)
        if time_since_last < min_delay:
            wait_time = min_delay - time_since_last
            print(f"⏳ Waiting {wait_time:.1f}s to respect rate limits...")
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    async def handle_rate_limit_response(self, response: httpx.Response) -> bool:
        """Handle rate limit responses"""
        if response.status_code == 429:
            print(f"⚠️  Rate limited! Waiting {self.rate_limit_delay}s before retry...")
            await asyncio.sleep(self.rate_limit_delay)
            return True
        return False
    
    async def try_alternative_linkedin_approaches(self, profile_url: str) -> Dict[str, Any]:
        """Try alternative approaches for LinkedIn scraping"""
        results = {}
        
        # Approach 1: Use Google Cache
        print("🔍 Trying Google Cache approach...")
        google_result = await self.try_google_cache(profile_url)
        results['google_cache'] = google_result
        
        # Approach 2: Use Archive.org
        print("🔍 Trying Archive.org approach...")
        archive_result = await self.try_archive_org(profile_url)
        results['archive_org'] = archive_result
        
        # Approach 3: Use LinkedIn API alternatives
        print("🔍 Trying LinkedIn alternatives...")
        alternatives_result = await self.try_linkedin_alternatives(profile_url)
        results['alternatives'] = alternatives_result
        
        # Approach 4: Proxy rotation approach
        print("🔍 Trying with different request patterns...")
        proxy_result = await self.try_different_patterns(profile_url)
        results['different_patterns'] = proxy_result
        
        return results
    
    async def try_google_cache(self, url: str) -> Dict[str, Any]:
        """Try to get LinkedIn profile from Google Cache"""
        try:
            # Google Cache URL format
            cache_url = f"https://webcache.googleusercontent.com/search?q=cache:{url}"
            
            await self.respect_rate_limits()
            
            headers = self.get_stealth_headers()
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(cache_url, headers=headers)
                
                return {
                    'status_code': response.status_code,
                    'final_url': str(response.url),
                    'content_length': len(response.text),
                    'has_profile_content': self.check_profile_content(response.text),
                    'method': 'google_cache',
                    'success': response.status_code == 200 and self.check_profile_content(response.text)
                }
        except Exception as e:
            return {'error': str(e), 'method': 'google_cache', 'success': False}
    
    async def try_archive_org(self, url: str) -> Dict[str, Any]:
        """Try to get LinkedIn profile from Archive.org"""
        try:
            # Archive.org Wayback Machine API
            api_url = f"https://archive.org/wayback/available?url={url}"
            
            await self.respect_rate_limits()
            
            headers = self.get_stealth_headers()
            async with httpx.AsyncClient(timeout=30.0) as client:
                # First, check if archived version exists
                api_response = await client.get(api_url, headers=headers)
                
                if api_response.status_code == 200:
                    data = api_response.json()
                    if data.get('archived_snapshots', {}).get('closest', {}).get('available'):
                        archived_url = data['archived_snapshots']['closest']['url']
                        
                        # Get the archived page
                        await self.respect_rate_limits()
                        archived_response = await client.get(archived_url, headers=headers)
                        
                        return {
                            'status_code': archived_response.status_code,
                            'archived_url': archived_url,
                            'content_length': len(archived_response.text),
                            'has_profile_content': self.check_profile_content(archived_response.text),
                            'method': 'archive_org',
                            'success': archived_response.status_code == 200 and self.check_profile_content(archived_response.text)
                        }
                
                return {
                    'status_code': 404,
                    'message': 'No archived version found',
                    'method': 'archive_org',
                    'success': False
                }
                
        except Exception as e:
            return {'error': str(e), 'method': 'archive_org', 'success': False}
    
    async def try_linkedin_alternatives(self, url: str) -> Dict[str, Any]:
        """Try alternative LinkedIn-like services or APIs"""
        try:
            # Extract username from LinkedIn URL
            username = self.extract_linkedin_username(url)
            if not username:
                return {'error': 'Could not extract username', 'method': 'alternatives', 'success': False}
            
            # Try different LinkedIn URL formats
            alternative_urls = [
                f"https://www.linkedin.com/pub/{username}",
                f"https://linkedin.com/in/{username}",
                f"https://www.linkedin.com/profile/view?id={username}",
            ]
            
            await self.respect_rate_limits()
            
            headers = self.get_stealth_headers()
            async with httpx.AsyncClient(timeout=30.0) as client:
                for alt_url in alternative_urls:
                    try:
                        response = await client.get(alt_url, headers=headers)
                        if response.status_code == 200 and self.check_profile_content(response.text):
                            return {
                                'status_code': response.status_code,
                                'successful_url': alt_url,
                                'content_length': len(response.text),
                                'has_profile_content': True,
                                'method': 'alternatives',
                                'success': True
                            }
                        await asyncio.sleep(2)  # Small delay between attempts
                    except:
                        continue
                
                return {
                    'message': 'No alternative URLs worked',
                    'method': 'alternatives',
                    'success': False
                }
                
        except Exception as e:
            return {'error': str(e), 'method': 'alternatives', 'success': False}
    
    async def try_different_patterns(self, url: str) -> Dict[str, Any]:
        """Try different request patterns to avoid detection"""
        try:
            patterns = [
                # Pattern 1: Simulate coming from Google
                {
                    'headers': self.get_stealth_headers('https://www.google.com/'),
                    'name': 'google_referrer'
                },
                # Pattern 2: Simulate coming from LinkedIn search
                {
                    'headers': self.get_stealth_headers('https://www.linkedin.com/search/'),
                    'name': 'linkedin_search_referrer'
                },
                # Pattern 3: Use different user agent
                {
                    'headers': {
                        **self.get_stealth_headers(),
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    },
                    'name': 'mac_user_agent'
                }
            ]
            
            for pattern in patterns:
                await self.respect_rate_limits()
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(url, headers=pattern['headers'])
                    
                    if response.status_code == 200:
                        return {
                            'status_code': response.status_code,
                            'pattern_used': pattern['name'],
                            'content_length': len(response.text),
                            'has_profile_content': self.check_profile_content(response.text),
                            'method': 'different_patterns',
                            'success': response.status_code == 200 and self.check_profile_content(response.text)
                        }
                    elif response.status_code != 429:  # Don't retry if rate limited
                        continue
                    else:
                        await self.handle_rate_limit_response(response)
            
            return {
                'message': 'No patterns worked',
                'method': 'different_patterns',
                'success': False
            }
            
        except Exception as e:
            return {'error': str(e), 'method': 'different_patterns', 'success': False}
    
    def extract_linkedin_username(self, url: str) -> Optional[str]:
        """Extract username from LinkedIn URL"""
        try:
            parsed = urlparse(url)
            path_parts = parsed.path.strip('/').split('/')
            
            if 'in' in path_parts:
                idx = path_parts.index('in')
                if idx + 1 < len(path_parts):
                    return path_parts[idx + 1]
            
            return None
        except:
            return None
    
    def check_profile_content(self, html: str) -> bool:
        """Check if HTML contains actual profile content"""
        if not html or len(html) < 1000:
            return False
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # Look for profile indicators
        profile_indicators = [
            'pv-text-details',
            'text-heading-xlarge',
            'profile-picture',
            'pv-top-card',
            'experience-section',
            'education-section',
            'profile-section',
            'pv-profile-section'
        ]
        
        for indicator in profile_indicators:
            if soup.find(class_=lambda x: x and indicator in x):
                return True
        
        # Check for profile-like content in text
        text = soup.get_text().lower()
        profile_text_indicators = [
            'experience at',
            'education at',
            'connections',
            'followers',
            'years of experience',
            'current position',
            'works at',
            'studied at'
        ]
        
        indicator_count = 0
        for indicator in profile_text_indicators:
            if indicator in text:
                indicator_count += 1
        
        return indicator_count >= 2  # Need at least 2 indicators
    
    async def get_working_linkedin_method(self, profile_url: str) -> Optional[Dict[str, Any]]:
        """Find a working method to scrape LinkedIn profiles"""
        print(f"🔍 Testing alternative LinkedIn scraping methods for: {profile_url}")
        print("=" * 70)
        
        results = await self.try_alternative_linkedin_approaches(profile_url)
        
        # Find the first successful method
        for method_name, result in results.items():
            if result.get('success', False):
                print(f"✅ SUCCESS: {method_name} method worked!")
                return result
        
        print("❌ No working methods found")
        return None

async def main():
    """Test improved LinkedIn scraping methods"""
    scraper = ImprovedLinkedInScraper()
    
    # Test with Bill Gates profile
    test_url = 'https://www.linkedin.com/in/billgates/'
    
    # Try to find a working method
    working_method = await scraper.get_working_linkedin_method(test_url)
    
    if working_method:
        print(f"\n🎉 Found working method: {working_method.get('method', 'unknown')}")
        print(f"📊 Content length: {working_method.get('content_length', 0)} characters")
        print(f"✅ Has profile content: {working_method.get('has_profile_content', False)}")
    else:
        print("\n💡 Recommendations:")
        print("1. LinkedIn has strong anti-bot measures")
        print("2. Consider using official LinkedIn API")
        print("3. Try scraping with longer delays (hours between requests)")
        print("4. Use residential proxies if available")
        print("5. Focus on other social platforms that are more scraping-friendly")

if __name__ == "__main__":
    asyncio.run(main())
