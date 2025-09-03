import asyncio
import httpx
import time
import random
from typing import Dict, List, Optional, Any
from fake_useragent import UserAgent
import json
import re
from urllib.parse import urlparse, urljoin
import ssl
import certifi

class AdvancedAntiDetection:
    def __init__(self):
        self.user_agent = UserAgent()
        self.session_data = {}
        self.proxy_rotation = []
        self.cookie_jar = {}
        self.request_delays = {
            'min_delay': 1,
            'max_delay': 5,
            'jitter': 0.5
        }
        
        # Browser fingerprinting evasion
        self.browser_profiles = {
            'chrome': {
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'accept_language': 'en-US,en;q=0.9',
                'accept_encoding': 'gzip, deflate, br',
                'sec_fetch_dest': 'document',
                'sec_fetch_mode': 'navigate',
                'sec_fetch_site': 'none',
                'sec_fetch_user': '?1',
                'upgrade_insecure_requests': '1',
                'cache_control': 'max-age=0',
                'dnt': '1'
            },
            'firefox': {
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'accept_language': 'en-US,en;q=0.5',
                'accept_encoding': 'gzip, deflate',
                'connection': 'keep-alive',
                'upgrade_insecure_requests': '1',
                'sec_fetch_dest': 'document',
                'sec_fetch_mode': 'navigate',
                'sec_fetch_site': 'none'
            },
            'safari': {
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'accept_language': 'en-US,en;q=0.9',
                'accept_encoding': 'gzip, deflate, br',
                'connection': 'keep-alive',
                'upgrade_insecure_requests': '1'
            }
        }
        
        # Site-specific configurations
        self.site_configs = {
            'linkedin.com': {
                'browser': 'chrome',
                'requires_js': True,
                'rate_limit': 2,
                'special_headers': {
                    'x-requested-with': 'XMLHttpRequest',
                    'x-li-lang': 'en_US',
                    'x-li-track': '{"clientVersion":"1.10.*"}'
                }
            },
            'github.com': {
                'browser': 'chrome',
                'requires_js': False,
                'rate_limit': 1,
                'special_headers': {
                    'x-requested-with': 'XMLHttpRequest'
                }
            },
            'twitter.com': {
                'browser': 'chrome',
                'requires_js': True,
                'rate_limit': 3,
                'special_headers': {
                    'x-twitter-active-user': 'yes',
                    'x-twitter-auth-type': 'OAuth2Session'
                }
            },
            'facebook.com': {
                'browser': 'chrome',
                'requires_js': True,
                'rate_limit': 5,
                'special_headers': {
                    'x-fb-lsd': 'random_string',
                    'x-fb-connection-quality': 'EXCELLENT'
                }
            },
            'google.com': {
                'browser': 'chrome',
                'requires_js': False,
                'rate_limit': 3,
                'special_headers': {
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'accept-language': 'en-US,en;q=0.9',
                    'cache-control': 'no-cache',
                    'pragma': 'no-cache',
                    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'document',
                    'sec-fetch-mode': 'navigate',
                    'sec-fetch-site': 'none',
                    'sec-fetch-user': '?1',
                    'upgrade-insecure-requests': '1'
                }
            },
            'about.google': {
                'browser': 'chrome',
                'requires_js': False,
                'rate_limit': 3,
                'special_headers': {
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'accept-language': 'en-US,en;q=0.9',
                    'cache-control': 'no-cache',
                    'pragma': 'no-cache',
                    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'document',
                    'sec-fetch-mode': 'navigate',
                    'sec-fetch-site': 'none',
                    'sec-fetch-user': '?1',
                    'upgrade-insecure-requests': '1'
                }
            }
        }
    
    def get_browser_headers(self, site_domain: str) -> Dict[str, str]:
        """Get appropriate browser headers for a specific site"""
        config = self.site_configs.get(site_domain, {})
        browser_type = config.get('browser', 'chrome')
        browser_profile = self.browser_profiles[browser_type]
        
        headers = browser_profile.copy()
        
        # Add site-specific headers
        special_headers = config.get('special_headers', {})
        headers.update(special_headers)
        
        # Add random user agent variation
        headers['user-agent'] = self.user_agent.random
        
        return headers
    
    async def create_client(self, site_domain: str) -> httpx.AsyncClient:
        """Create an HTTP client with anti-detection measures"""
        headers = self.get_browser_headers(site_domain)
        
        # SSL context with modern settings
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        ssl_context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20')
        ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
        
        # Client configuration
        client_config = {
            'headers': headers,
            'timeout': httpx.Timeout(30.0),
            'follow_redirects': True,
            'verify': ssl_context,
            'http2': False  # Disable HTTP/2 to avoid issues
        }
        
        # Add proxy if available
        if self.proxy_rotation:
            proxy = random.choice(self.proxy_rotation)
            client_config['proxies'] = proxy
        
        return httpx.AsyncClient(**client_config)
    
    async def fetch_with_retry(self, url: str, max_retries: int = 3) -> Optional[str]:
        """Fetch content with retry logic and anti-detection measures"""
        site_domain = urlparse(url).netloc
        
        for attempt in range(max_retries):
            try:
                # Random delay between requests
                delay = random.uniform(
                    self.request_delays['min_delay'],
                    self.request_delays['max_delay']
                )
                await asyncio.sleep(delay)
                
                async with await self.create_client(site_domain) as client:
                    # Add cookies if available
                    if site_domain in self.cookie_jar:
                        client.cookies.update(self.cookie_jar[site_domain])
                    
                    # Special handling for Google domains
                    if 'google.com' in site_domain or 'about.google' in site_domain:
                        # Add additional headers for Google
                        headers = client.headers.copy()
                        headers.update({
                            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                            'accept-language': 'en-US,en;q=0.9',
                            'cache-control': 'no-cache',
                            'pragma': 'no-cache',
                            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                            'sec-ch-ua-mobile': '?0',
                            'sec-ch-ua-platform': '"Windows"',
                            'sec-fetch-dest': 'document',
                            'sec-fetch-mode': 'navigate',
                            'sec-fetch-site': 'none',
                            'sec-fetch-user': '?1',
                            'upgrade-insecure-requests': '1'
                        })
                        response = await client.get(url, headers=headers)
                    else:
                        response = await client.get(url)
                    
                    # Store cookies for future requests
                    if response.cookies:
                        self.cookie_jar[site_domain] = response.cookies
                    
                    # Handle different response codes
                    if response.status_code == 200:
                        content = response.text
                        
                        # Check for bot protection
                        protection = self.detect_bot_protection(content)
                        if protection['cloudflare']:
                            print(f"Cloudflare protection detected on {url} - attempting to bypass")
                            return await self.handle_cloudflare(url)
                        elif protection['captcha']:
                            print(f"CAPTCHA detected on {url} - skipping")
                            return None
                        elif protection['rate_limit']:
                            print(f"Rate limit detected on {url} - waiting longer")
                            await asyncio.sleep(random.uniform(10, 20))
                            continue
                        
                        return content
                    elif response.status_code in [403, 429, 401]:
                        # Rate limited or blocked - wait longer
                        print(f"Access denied (status {response.status_code}) for {url} - waiting longer")
                        await asyncio.sleep(random.uniform(5, 15))
                        continue
                    elif response.status_code == 404:
                        print(f"Page not found (404) for {url}")
                        return None
                    else:
                        # Other status codes - try to get content anyway
                        print(f"Unexpected status code {response.status_code} for {url}")
                        return response.text
                        
            except Exception as e:
                print(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(random.uniform(2, 8))
                    continue
                else:
                    print(f"All attempts failed for {url}")
                    return None
        
        return None
    
    def add_proxy(self, proxy_url: str):
        """Add a proxy to the rotation"""
        self.proxy_rotation.append(proxy_url)
    
    def set_request_delays(self, min_delay: float, max_delay: float, jitter: float = 0.5):
        """Set custom request delays"""
        self.request_delays = {
            'min_delay': min_delay,
            'max_delay': max_delay,
            'jitter': jitter
        }
    
    def add_site_config(self, domain: str, config: Dict[str, Any]):
        """Add custom configuration for a specific site"""
        self.site_configs[domain] = config
    
    async def handle_cloudflare(self, url: str) -> Optional[str]:
        """Handle Cloudflare protection"""
        # This would require a more sophisticated approach with browser automation
        # For now, we'll use basic retry logic
        return await self.fetch_with_retry(url, max_retries=5)
    
    async def handle_captcha(self, url: str) -> Optional[str]:
        """Handle CAPTCHA challenges"""
        # This would require CAPTCHA solving services
        # For now, we'll skip CAPTCHA-protected pages
        print(f"CAPTCHA detected on {url} - skipping")
        return None
    
    def detect_bot_protection(self, response_text: str) -> Dict[str, bool]:
        """Detect various types of bot protection"""
        protection_types = {
            'cloudflare': any(phrase in response_text.lower() for phrase in [
                'cloudflare', 'checking your browser', 'ddos protection'
            ]),
            'captcha': any(phrase in response_text.lower() for phrase in [
                'captcha', 'verify you are human', 'robot check'
            ]),
            'rate_limit': any(phrase in response_text.lower() for phrase in [
                'rate limit', 'too many requests', 'please wait'
            ]),
            'geoblock': any(phrase in response_text.lower() for phrase in [
                'not available in your region', 'geoblocked', 'access denied'
            ])
        }
        
        return protection_types
