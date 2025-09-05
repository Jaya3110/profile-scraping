import asyncio
import httpx
import time
import random
from typing import List, Optional, Dict, Any
from bs4 import BeautifulSoup
import re
import json
import os
from urllib.parse import urljoin, urlparse
from fake_useragent import UserAgent
import google.generativeai as genai
from datetime import datetime, timedelta
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time as _time

from models import Profile, SocialLinks, CacheEntry
from extractors.css_extractor import CSSProfileExtractor
from extractors.ai_extractor import AIProfileExtractor
from extractors.site_specific import SiteSpecificExtractor
from extractors.universal_extractor import UniversalProfileExtractor
from extractors.extended_site_specific import ExtendedSiteSpecificExtractor


class FreshworksLeadershipScraper:
    def __init__(self):
        self.chrome_options = Options()
        # Headless mode (more compatible across Chrome versions)
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        # Speed tweaks: load strategy and disable images
        try:
            self.chrome_options.page_load_strategy = 'eager'
            self.chrome_options.add_experimental_option(
                "prefs",
                {"profile.managed_default_content_settings.images": 2}
            )
        except Exception:
            pass
        self.universal_extractor = UniversalProfileExtractor()

    async def scrape_freshworks_leadership(self, url: str) -> List[Profile]:
        profiles: List[Profile] = []
        driver = None
        try:
            driver = webdriver.Chrome(options=self.chrome_options)
            driver.get(url)
            wait = WebDriverWait(driver, 12)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "main")))
            # Attempt to accept cookie banner to avoid overlays
            try:
                for xp in [
                    "//button[contains(translate(., 'ACEPTLl ', 'aceptll '), 'accept')]",
                    "//button[contains(translate(., 'AGREE', 'agree'), 'agree')]",
                    "//button[contains(translate(., 'ACCEPT ALL', 'accept all'), 'accept all')]",
                    "//button[contains(translate(., 'COOKIES', 'cookies'), 'cookies') and contains(translate(., 'ACCEPT', 'accept'), 'accept')]",
                ]:
                    try:
                        btn = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.XPATH, xp)))
                        if btn:
                            btn.click()
                            break
                    except Exception:
                        continue
            except Exception:
                pass
            # Scroll to bottom to trigger lazy loading
            try:
                last_height = driver.execute_script("return document.body.scrollHeight")
                for _ in range(6):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    _time.sleep(0.8)
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height
            except Exception:
                pass
            # Try clicking any visible load more/see all buttons
            try:
                for xp in [
                    "//button[contains(translate(., 'LOAD MORE', 'load more'), 'load more')]",
                    "//a[contains(translate(., 'SEE ALL', 'see all'), 'see all')]",
                ]:
                    for el in driver.find_elements(By.XPATH, xp):
                        try:
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                            _time.sleep(0.3)
                            if el.is_displayed() and el.is_enabled():
                                el.click()
                                _time.sleep(1.0)
                        except Exception:
                            continue
            except Exception:
                pass
            _time.sleep(1.0)
            html_content = driver.page_source
        except Exception as e:
            print(f"❌ Selenium error: {e}")
            html_content = None
        finally:
            try:
                if driver:
                    driver.quit()
            except Exception:
                pass

        if not html_content:
            return []

        soup = BeautifulSoup(html_content, 'html.parser')
        # Combine strategies on rendered HTML
        def combine_once(soup_obj):
            combined_local: List[Profile] = []
            u = self.universal_extractor.extract_profiles(soup_obj, url) or []
            combined_local.extend(u)
            l = self.universal_extractor.extract_leadership_sections(soup_obj, url) or []
            combined_local.extend(l)
            h = self.universal_extractor.extract_profiles_from_headings(soup_obj, url) or []
            combined_local.extend(h)
            combined_local = self._filter_cookie_privacy(combined_local)
            return self._dedupe_by_name_title(combined_local)

        deduped = combine_once(soup)
        if len(deduped) < 12:
            try:
                # attempt additional progressive scroll emulation by re-parsing
                html2 = html_content
                soup2 = BeautifulSoup(html2, 'html.parser')
                more = combine_once(soup2)
                deduped = self._dedupe_by_name_title(deduped + more)
            except Exception:
                pass
        return deduped

    def _filter_cookie_privacy(self, profiles: List[Profile]) -> List[Profile]:
        deny_terms = {
            "privacy preference", "your privacy", "cookies", "cookie",
            "strictly necessary cookies", "functional cookies", "performance cookies",
            "targeting cookies", "advertising cookies"
        }
        filtered: List[Profile] = []
        for p in profiles:
            nm = (p.name or "").strip().lower()
            tt = (p.title or "").strip().lower()
            if any(term in nm for term in deny_terms):
                continue
            if any(term in tt for term in deny_terms):
                continue
            filtered.append(p)
        return filtered

    def _dedupe_by_name_title(self, profiles: List[Profile]) -> List[Profile]:
        seen = {}
        for p in profiles:
            key = (p.name or '').strip().lower(), (p.title or '').strip().lower()
            if key not in seen or (p.confidence or 0) > (seen[key].confidence or 0):
                seen[key] = p
        return list(seen.values())

# NOTE: anti_detection is intentionally NOT used in the default path anymore
# from anti_detection import AdvancedAntiDetection


class ProfileScrapingService:
    def __init__(self):
        self.cache: Dict[str, CacheEntry] = {}
        self.cache_ttl_hours = 24
        self.user_agent = UserAgent()
        self.ai_enabled = False

        # connection pool (fast!)
        self.client: Optional[httpx.AsyncClient] = None
        self._client_opts = dict(
            timeout=httpx.Timeout(5.0, connect=3.0, read=5.0, write=5.0, pool=5.0),
            follow_redirects=True,
            http2=False,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                              'AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10, keepalive_expiry=30.0),
            verify=True,
        )
        
        # Initialize extractors
        self.css_extractor = CSSProfileExtractor()
        self.ai_extractor = AIProfileExtractor()
        self.site_extractor = SiteSpecificExtractor()
        self.universal_extractor = UniversalProfileExtractor()
        self.extended_site_extractor = ExtendedSiteSpecificExtractor()
        
        # anti-detection kept available but not used by default
        # self.anti_detection = AdvancedAntiDetection()
        
        # Configure AI (Gemini 2.0 Flash)
        self.setup_ai()
    
        # Common generic headings to filter out from noisy extractions
        self._generic_headings = {
            "leadership",
            "executive team",
            "board of directors",
            "see what we’re all about",
            "see what we're all about",
            "our team",
            "management",
            "team",
            "leaders"
        }
    
    async def scrape_with_selenium(self, url: str) -> List[Profile]:
        """Use Selenium-backed scraper for JS-rendered pages like Freshworks leadership."""
        scraper = FreshworksLeadershipScraper()
        return await scraper.scrape_freshworks_leadership(url)

    async def _ensure_client(self):
        if self.client is None:
            self.client = httpx.AsyncClient(**self._client_opts)

    async def aclose(self):
        """Call this when shutting down your app to close the pool cleanly."""
        if self.client is not None:
            await self.client.aclose()
            self.client = None

    def setup_ai(self):
        """Setup AI extraction with Gemini 2.0 Flash"""
        load_dotenv()
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key and api_key != 'your_gemini_api_key_here':
            try:
                genai.configure(api_key=api_key)
                gemini_model = genai.GenerativeModel('gemini-2.0-flash')
                self.ai_extractor = AIProfileExtractor(gemini_model)
                print("✅ AI extraction enabled with Gemini 2.0 Flash")
                self.ai_enabled = True
            except Exception as e:
                print(f"❌ Failed to configure Gemini AI: {e}")
                print("⚠️  AI extraction will be disabled")
                self.ai_enabled = False
        else:
            print("⚠️  GEMINI_API_KEY not found or not configured")
            print("⚠️  AI extraction will be disabled")
            self.ai_enabled = False
    
    async def validate_url(self, url) -> bool:
        """Validate if URL is accessible and returns HTML/text-like content"""
        try:
            url_str = str(url)
            await self._ensure_client()
            resp = await self.client.get(url_str)
            if resp.status_code == 200:
                ct = resp.headers.get('content-type', '').lower()
                return ('html' in ct) or ('text' in ct)
            elif resp.status_code in (401, 403, 429):
                # could still be a page we can parse
                return True
            elif resp.status_code == 404:
                return False
            else:
                return True
        except Exception as e:
            print(f"URL validation error: {e}")
            return False
    
    async def scrape_profiles(self, url, max_profiles: int = 10) -> List[Profile]:
        """Main method to scrape profiles using multiple strategies — FAST & SIMPLE PATH"""
        url_str = str(url)
        
        # Cache
        cached_result = self.get_cached_result(url_str)
        if cached_result:
            return cached_result[:max_profiles]
        
        try:
            print(f"🚀 Starting scrape (simple path) for: {url_str}")

            # Special-case: Use Selenium for Freshworks leadership page (JS-rendered)
            if 'freshworks.com/company/leadership' in url_str:
                print("🔧 Using Selenium for Freshworks leadership page")
                selenium_profiles = await self.scrape_with_selenium(url_str)
                if selenium_profiles:
                    final_profiles = selenium_profiles[:max_profiles]
                    self.cache_result(url_str, final_profiles)
                    print(f"🎯 Total profiles found via Selenium: {len(final_profiles)}")
                    return final_profiles

            # ✅ SIMPLE fetch only — no anti-detection
            html_content = await self.fetch_html_simple(url_str)
            if not html_content:
                print("❌ No HTML content received (simple path)")
                return []
            
            soup = BeautifulSoup(html_content, 'html.parser')
            print(f"📄 Parsed HTML with {len(soup.find_all())} elements")

            profiles: List[Profile] = []
            strategies_used: List[str] = []

            # Strategy 1: Universal extraction (fast, structured)
            print("🔍 Trying universal extraction...")
            universal_profiles = self.universal_extractor.extract_profiles(soup, url)
            if universal_profiles:
                profiles.extend(universal_profiles)
                strategies_used.append("universal_extractor")
                print(f"✅ Universal extraction found {len(universal_profiles)} profiles")
            
            # Strategy 1.5: Company team extraction (structured for team pages)
            print("🔍 Trying company team extraction...")
            company_team_profiles = await self.universal_extractor.extract_company_team_profiles(soup, url)
            if company_team_profiles:
                profiles.extend(company_team_profiles)
                strategies_used.append("company_team_extraction")
                print(f"✅ Company team extraction found {len(company_team_profiles)} profiles")

            # Strategy 1.7: Leadership sections (headings + cards in sections)
            print("🔍 Trying leadership sections extraction...")
            leadership_profiles = self.universal_extractor.extract_leadership_sections(soup, url)
            if leadership_profiles:
                profiles.extend(leadership_profiles)
                strategies_used.append("leadership_section")
                print(f"✅ Leadership sections extraction found {len(leadership_profiles)} profiles")

            # Strategy 1.9: Heading-based extraction (names in headings)
            print("🔍 Trying heading-based extraction...")
            heading_profiles = self.universal_extractor.extract_profiles_from_headings(soup, url)
            if heading_profiles:
                profiles.extend(heading_profiles)
                strategies_used.append("heading_based")
                print(f"✅ Heading-based extraction found {len(heading_profiles)} profiles")

            # Strategy 2: CSS selector extraction (fallback for simple patterns)
            print("🔍 Trying CSS extraction...")
            css_profiles = self.css_extractor.extract(soup, url)
            if css_profiles:
                css_profiles = self._filter_noisy_profiles(css_profiles)
            if css_profiles:
                profiles.extend(css_profiles)
                strategies_used.append("css_selectors")
                print(f"✅ CSS extraction found {len(css_profiles)} profiles")
            
            # Strategy 3: Company team extraction (leadership/about/team pages)
            if any(k in url_str.lower() for k in ('leadership', 'team', 'about')):
                print("🔍 Trying company team extraction...")
                company_team_profiles = await self.universal_extractor.extract_company_team_profiles(soup, url)
                if company_team_profiles:
                    profiles.extend(company_team_profiles)
                    strategies_used.append("company_team_extraction")
                    print(f"✅ Company team extraction found {len(company_team_profiles)} profiles")

            # Optional fallback to AI (only if nothing found and AI is enabled)
            if len(profiles) == 0 and self.ai_enabled:
                print("🔍 Trying AI extraction as fallback...")
                ai_profiles = await self.ai_extractor.extract(soup, url)
                if ai_profiles:
                    profiles.extend(ai_profiles)
                    strategies_used.append("ai_extraction")
                    print(f"✅ AI extraction found {len(ai_profiles)} profiles")
            
            # De-dup & limit
            unique_profiles = self.remove_duplicates(profiles)
            final_profiles = unique_profiles[:max_profiles]
            
            # Cache
            self.cache_result(url_str, final_profiles)
            
            print(f"🎯 Total profiles found: {len(final_profiles)} using strategies: {', '.join(strategies_used) or 'none'}")
            return final_profiles
            
        except Exception as e:
            print(f"❌ Scraping error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    # ---------------------------
    # Fetchers (Simple / Robust)
    # ---------------------------

    async def fetch_html_simple(self, url: str) -> Optional[str]:
        """Fetch HTML content — SIMPLE VERSION (bypasses all anti-detection)"""
        try:
            await self._ensure_client()
            # Slightly longer timeout for known anti-bot page
            if "freshworks.com/company/leadership" in url:
                self.client.timeout = httpx.Timeout(10.0, connect=5.0, read=10.0, write=10.0, pool=10.0)
            print(f"🟢 [SIMPLE] GET {url}")
            resp = await self._retry_get(url, max_retries=2, initial_backoff=0.5)
            if resp is None:
                print("❌ [SIMPLE] request failed after retries")
                return None

            if resp.status_code == 200:
                print(f"✅ [SIMPLE] success: {len(resp.text)} chars")
                return resp.text
            if resp.status_code in (401, 403, 429):
                # Some sites block but still return content
                if resp.text and len(resp.text) > 500:
                    print(f"⚠️ [SIMPLE] HTTP {resp.status_code} but has content, returning")
                    return resp.text
                print(f"❌ [SIMPLE] blocked: HTTP {resp.status_code}")
                return None

            print(f"❌ [SIMPLE] HTTP {resp.status_code}")
            return None
        except Exception as e:
            print(f"❌ [SIMPLE] error: {e}")
            return None
    
    async def fetch_html(self, url: str) -> Optional[str]:
        """Legacy API — now explicitly uses SIMPLE path to avoid anti-detection."""
        return await self.fetch_html_simple(url)

    async def fetch_html_robust(self, url: str) -> Optional[str]:
        """
        Optional robust path (disabled by default): slightly longer timeouts + more retries.
        NOTE: This still avoids the AdvancedAntiDetection to prevent loops unless you re-enable it.
        """
        try:
            await self._ensure_client()
            print(f"🟠 [ROBUST] GET {url}")
            resp = await self._retry_get(url, max_retries=4, initial_backoff=1.0)
            if resp and resp.status_code == 200:
                print(f"✅ [ROBUST] success: {len(resp.text)} chars")
                return resp.text
            if resp and resp.text and resp.status_code in (401, 403, 429):
                print(f"⚠️ [ROBUST] HTTP {resp.status_code} with content")
                return resp.text
            print(f"❌ [ROBUST] failed")
            return None
        except Exception as e:
            print(f"❌ [ROBUST] error: {e}")
            return None

    async def _retry_get(self, url: str, max_retries: int = 2, initial_backoff: float = 0.5) -> Optional[httpx.Response]:
        """
        Bounded retries with exponential backoff + jitter.
        No infinite loops. Uses the pooled client.
        """
        await self._ensure_client()
        attempt = 0
        backoff = initial_backoff
        last_exc = None

        while attempt <= max_retries:
            try:
                resp = await self.client.get(url)
                # quick accept for 2xx
                if 200 <= resp.status_code < 300:
                    return resp
                # retry on 408/429/5xx
                if resp.status_code in (408, 429) or 500 <= resp.status_code < 600:
                    attempt += 1
                    if attempt > max_retries:
                        return resp
                    await asyncio.sleep(backoff + random.uniform(0, 0.25))
                    backoff *= 2
                    continue
                # otherwise return as-is
                return resp
            except Exception as e:
                last_exc = e
                attempt += 1
                if attempt > max_retries:
                    print(f"❌ GET {url} failed after {attempt} attempts: {e}")
                    return None
                await asyncio.sleep(backoff + random.uniform(0, 0.25))
                backoff *= 2

        if last_exc:
            print(f"❌ GET {url} final error: {last_exc}")
            return None
    
    # ---------------------------
    # LinkedIn helpers (unchanged; not in default path)
    # ---------------------------
    
    async def fetch_linkedin_html(self, url: str) -> Optional[str]:
        """Special handling for LinkedIn (kept here but not called in simple flow)"""
        try:
            await self._ensure_client()
            headers = self.client.headers.copy()
            approaches = [
                ('direct', url),
                ('google_cache', f"https://webcache.googleusercontent.com/search?q=cache:{url}"),
            ]
            # Try archive.org lookup in a guarded way
            try:
                arch = await self.get_archive_url(url)
                if arch:
                    approaches.append(('archive_org', arch))
            except Exception:
                pass

            for approach_name, approach_url in approaches:
                try:
                    print(f"🔍 Trying LinkedIn {approach_name} approach...")
                    await asyncio.sleep(random.uniform(1.0, 2.0))
                    resp = await self.client.get(approach_url, headers=headers)
                    if resp.status_code == 200:
                        content = resp.text
                        if self.has_linkedin_profile_content(content):
                            print(f"✅ LinkedIn {approach_name} approach successful!")
                            return content
                    elif resp.status_code == 429:
                        print(f"⚠️ Rate limited on {approach_name}, trying next approach...")
                        continue
                except Exception as e:
                    print(f"❌ LinkedIn {approach_name} approach failed: {e}")
                    continue
            
            print("❌ All LinkedIn approaches failed")
            return None
            
        except Exception as e:
            print(f"Error fetching LinkedIn HTML: {e}")
            return None
    
    async def get_archive_url(self, url: str) -> Optional[str]:
        """Get archived version URL from Archive.org (best-effort)"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"https://archive.org/wayback/available?url={url}")
                if resp.status_code == 200:
                    data = resp.json()
                    closest = data.get('archived_snapshots', {}).get('closest', {})
                    if closest.get('available'):
                        return closest.get('url')
        except Exception:
            pass
        return None
    
    def has_linkedin_profile_content(self, html: str) -> bool:
        if not html or len(html) < 1000:
            return False
        soup = BeautifulSoup(html, 'html.parser')
        profile_indicators = [
            'pv-text-details', 'text-heading-xlarge', 'profile-picture',
            'pv-top-card', 'experience-section', 'education-section'
        ]
        for indicator in profile_indicators:
            if soup.find(class_=lambda x: x and indicator in x):
                return True
        text = soup.get_text().lower()
        profile_text_indicators = [
            'experience at', 'education at', 'connections', 'followers', 'years of experience'
        ]
        return sum(1 for ind in profile_text_indicators if ind in text) >= 2

    # ---------------------------
    # De-duplication & Cache
    # ---------------------------
    
    def remove_duplicates(self, profiles: List[Profile]) -> List[Profile]:
        seen = set()
        unique_profiles = []
        sorted_profiles = sorted(profiles, key=lambda x: x.confidence, reverse=True)
        for profile in sorted_profiles:
            identifier = f"{profile.name or 'unknown'}_{profile.company or 'no-company'}"
            if self.is_similar_profile(profile, unique_profiles):
                continue
            if identifier not in seen:
                seen.add(identifier)
                unique_profiles.append(profile)
        return unique_profiles
    
    def is_similar_profile(self, profile: Profile, existing_profiles: List[Profile]) -> bool:
        if not profile.name:
            return False
        for existing in existing_profiles:
            if not existing.name:
                continue
            if self.names_are_similar(profile.name, existing.name):
                if profile.company and existing.company and profile.company == existing.company:
                    return True
                if profile.title and existing.title and self.titles_are_similar(profile.title, existing.title):
                    return True
        return False
    
    def names_are_similar(self, name1: str, name2: str) -> bool:
        if not name1 or not name2:
            return False
        a = ' '.join(name1.lower().split())
        b = ' '.join(name2.lower().split())
        if a == b:
            return True
        if a.replace(' ', '') == b.replace(' ', ''):
            return True
        return self.is_initials_vs_full_name(a, b)

    def is_initials_vs_full_name(self, n1: str, n2: str) -> bool:
        p1, p2 = n1.split(), n2.split()
        if len(p1) == 1 and len(p2) > 1 and len(p1[0]) == 1 and p1[0].isalpha():
            return p1[0][0].upper() == p2[0][0].upper()
        if len(p2) == 1 and len(p1) > 1 and len(p2[0]) == 1 and p2[0].isalpha():
            return p2[0][0].upper() == p1[0][0].upper()
        return False
    
    def titles_are_similar(self, t1: str, t2: str) -> bool:
        if not t1 or not t2:
            return False
        a = ' '.join(t1.lower().split())
        b = ' '.join(t2.lower().split())
        return a == b or a.replace(' ', '') == b.replace(' ', '')

    # ---------------------------
    # Noise filtering helpers
    # ---------------------------

    def _filter_noisy_profiles(self, items: List[Profile]) -> List[Profile]:
        filtered: List[Profile] = []
        for p in items:
            name = (p.name or '').strip().lower()
            title = (p.title or '').strip().lower()
            # Reject generic headings as names, or items with neither title nor image
            if name in self._generic_headings:
                continue
            if not p.name:
                continue
            if not p.title and not p.image:
                continue
            filtered.append(p)
        return filtered
    
    def get_cached_result(self, url: str) -> Optional[List[Profile]]:
        if url in self.cache:
            entry = self.cache[url]
            if datetime.now() < entry.expires_at:
                return entry.profiles
            del self.cache[url]
        return None
    
    def cache_result(self, url: str, profiles: List[Profile]):
        expires_at = datetime.now() + timedelta(hours=self.cache_ttl_hours)
        self.cache[url] = CacheEntry(
            url=url,
            profiles=profiles,
            cached_at=datetime.now(),
            expires_at=expires_at
        )
        self.cleanup_cache()
    
    def cleanup_cache(self):
        now = datetime.now()
        for url in [u for u, e in self.cache.items() if now > e.expires_at]:
            del self.cache[url]
    
    def get_cached_profiles(self) -> List[Profile]:
        all_profiles = []
        for entry in self.cache.values():
            all_profiles.extend(entry.profiles)
        return all_profiles
    
    def get_cache_stats(self) -> Dict[str, Any]:
        return {
            "total_cached_urls": len(self.cache),
            "total_cached_profiles": sum(len(entry.profiles) for entry in self.cache.values()),
            "cache_size_mb": sum(len(str(entry)) for entry in self.cache.values()) / (1024 * 1024),
        }

def is_render_environment():
    return os.getenv("RENDER") == "true"

# In scrape_profiles method:
if 'freshworks.com/company/leadership' in url_str and not is_render_environment():
    # Use Selenium only if not on Render
    selenium_profiles = await self.scrape_with_selenium(url_str)
