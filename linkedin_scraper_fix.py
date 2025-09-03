import asyncio
import httpx
import time
import random
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

class LinkedInScraperFix:
    def __init__(self):
        self.session_cookies = {}
        self.request_delay = (2, 5)  # Random delay between requests
        
    def get_enhanced_headers(self) -> Dict[str, str]:
        """Get enhanced headers that better mimic a real browser"""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }
    
    async def test_linkedin_access_methods(self, profile_url: str) -> Dict[str, Any]:
        """Test different methods to access LinkedIn profiles"""
        results = {}
        
        # Method 1: Direct request with enhanced headers
        print("Testing Method 1: Enhanced headers...")
        result1 = await self.test_direct_request(profile_url)
        results['direct_enhanced'] = result1
        
        # Method 2: Request with session simulation
        print("Testing Method 2: Session simulation...")
        result2 = await self.test_session_request(profile_url)
        results['session_simulation'] = result2
        
        # Method 3: Public profile URL approach
        print("Testing Method 3: Public profile URL...")
        result3 = await self.test_public_profile(profile_url)
        results['public_profile'] = result3
        
        # Method 4: Mobile LinkedIn approach
        print("Testing Method 4: Mobile LinkedIn...")
        result4 = await self.test_mobile_linkedin(profile_url)
        results['mobile_linkedin'] = result4
        
        return results
    
    async def test_direct_request(self, url: str) -> Dict[str, Any]:
        """Test direct request with enhanced headers"""
        try:
            headers = self.get_enhanced_headers()
            
            async with httpx.AsyncClient(
                follow_redirects=True, 
                timeout=30.0,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            ) as client:
                # Add random delay to mimic human behavior
                await asyncio.sleep(random.uniform(*self.request_delay))
                
                response = await client.get(url, headers=headers)
                
                return {
                    'status_code': response.status_code,
                    'final_url': str(response.url),
                    'content_type': response.headers.get('content-type', ''),
                    'content_length': len(response.text),
                    'has_profile_content': self.check_profile_content(response.text),
                    'is_login_page': self.is_login_page(response.text),
                    'method': 'direct_enhanced'
                }
        except Exception as e:
            return {'error': str(e), 'method': 'direct_enhanced'}
    
    async def test_session_request(self, url: str) -> Dict[str, Any]:
        """Test request with session cookies and referrer"""
        try:
            headers = self.get_enhanced_headers()
            headers['Referer'] = 'https://www.linkedin.com/'
            
            # Simulate visiting LinkedIn homepage first
            async with httpx.AsyncClient(
                follow_redirects=True, 
                timeout=30.0,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            ) as client:
                
                # First, visit LinkedIn homepage to get session cookies
                await asyncio.sleep(random.uniform(1, 3))
                homepage_response = await client.get('https://www.linkedin.com/', headers=headers)
                
                # Extract cookies from homepage
                cookies = dict(homepage_response.cookies)
                
                # Now visit the profile with session cookies
                await asyncio.sleep(random.uniform(*self.request_delay))
                response = await client.get(url, headers=headers, cookies=cookies)
                
                return {
                    'status_code': response.status_code,
                    'final_url': str(response.url),
                    'content_type': response.headers.get('content-type', ''),
                    'content_length': len(response.text),
                    'has_profile_content': self.check_profile_content(response.text),
                    'is_login_page': self.is_login_page(response.text),
                    'cookies_count': len(cookies),
                    'method': 'session_simulation'
                }
        except Exception as e:
            return {'error': str(e), 'method': 'session_simulation'}
    
    async def test_public_profile(self, url: str) -> Dict[str, Any]:
        """Test using LinkedIn public profile URL format"""
        try:
            # Convert regular LinkedIn URL to public profile format
            # Example: /in/username/ -> /pub/username/
            public_url = url.replace('/in/', '/pub/')
            if public_url == url:
                # Try adding /public-profile/ path
                parsed = urlparse(url)
                if '/in/' in parsed.path:
                    username = parsed.path.split('/in/')[-1].strip('/')
                    public_url = f"https://www.linkedin.com/pub/{username}/public-profile/"
            
            headers = self.get_enhanced_headers()
            
            async with httpx.AsyncClient(
                follow_redirects=True, 
                timeout=30.0
            ) as client:
                await asyncio.sleep(random.uniform(*self.request_delay))
                response = await client.get(public_url, headers=headers)
                
                return {
                    'status_code': response.status_code,
                    'final_url': str(response.url),
                    'public_url_tried': public_url,
                    'content_type': response.headers.get('content-type', ''),
                    'content_length': len(response.text),
                    'has_profile_content': self.check_profile_content(response.text),
                    'is_login_page': self.is_login_page(response.text),
                    'method': 'public_profile'
                }
        except Exception as e:
            return {'error': str(e), 'method': 'public_profile'}
    
    async def test_mobile_linkedin(self, url: str) -> Dict[str, Any]:
        """Test using mobile LinkedIn"""
        try:
            # Convert to mobile LinkedIn URL
            mobile_url = url.replace('www.linkedin.com', 'm.linkedin.com')
            
            # Mobile headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            async with httpx.AsyncClient(
                follow_redirects=True, 
                timeout=30.0
            ) as client:
                await asyncio.sleep(random.uniform(*self.request_delay))
                response = await client.get(mobile_url, headers=headers)
                
                return {
                    'status_code': response.status_code,
                    'final_url': str(response.url),
                    'mobile_url_tried': mobile_url,
                    'content_type': response.headers.get('content-type', ''),
                    'content_length': len(response.text),
                    'has_profile_content': self.check_profile_content(response.text),
                    'is_login_page': self.is_login_page(response.text),
                    'method': 'mobile_linkedin'
                }
        except Exception as e:
            return {'error': str(e), 'method': 'mobile_linkedin'}
    
    def check_profile_content(self, html: str) -> bool:
        """Check if HTML contains actual profile content"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Look for profile indicators
        profile_indicators = [
            'pv-text-details',
            'text-heading-xlarge',
            'profile-picture',
            'pv-top-card',
            'experience-section',
            'education-section'
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
            'years of experience'
        ]
        
        for indicator in profile_text_indicators:
            if indicator in text:
                return True
        
        return False
    
    def is_login_page(self, html: str) -> bool:
        """Check if page is a login/sign-in page"""
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text().lower()
        
        login_indicators = [
            'sign in to view',
            'join linkedin to view',
            'log in to linkedin',
            'welcome back',
            'forgot password',
            'create account'
        ]
        
        for indicator in login_indicators:
            if indicator in text:
                return True
        
        return False

async def main():
    """Test LinkedIn scraping methods"""
    scraper = LinkedInScraperFix()
    
    # Test with Bill Gates profile
    test_url = 'https://www.linkedin.com/in/billgates/'
    
    print(f"Testing LinkedIn access methods for: {test_url}")
    print("=" * 60)
    
    results = await scraper.test_linkedin_access_methods(test_url)
    
    print("\nResults Summary:")
    print("=" * 60)
    
    for method, result in results.items():
        print(f"\n{method.upper()}:")
        if 'error' in result:
            print(f"  ❌ Error: {result['error']}")
        else:
            status = result['status_code']
            has_content = result.get('has_profile_content', False)
            is_login = result.get('is_login_page', False)
            
            status_emoji = "✅" if status == 200 else "❌"
            content_emoji = "✅" if has_content else "❌"
            login_emoji = "❌" if is_login else "✅"
            
            print(f"  {status_emoji} Status: {status}")
            print(f"  {content_emoji} Has Profile Content: {has_content}")
            print(f"  {login_emoji} Not Login Page: {not is_login}")
            print(f"  📄 Content Length: {result.get('content_length', 0)} chars")
            
            if result.get('final_url') != test_url:
                print(f"  🔄 Redirected to: {result.get('final_url')}")

if __name__ == "__main__":
    asyncio.run(main())
