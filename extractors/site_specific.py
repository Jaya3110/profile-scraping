from bs4 import BeautifulSoup, Tag
from typing import List, Optional, Dict, Any
import re
from urllib.parse import urljoin, urlparse

from models import Profile, SocialLinks

class SiteSpecificExtractor:
    def __init__(self):
        # Site-specific extraction patterns
        self.site_patterns = {
            'linkedin': {
                'domain': 'linkedin.com',
                'extractor': self.extract_linkedin_profile
            },
            'github': {
                'domain': 'github.com',
                'extractor': self.extract_github_profile
            },
            'twitter': {
                'domain': 'twitter.com',
                'extractor': self.extract_twitter_profile
            },
            'company_team': {
                'patterns': ['.team', '.about', '.company', '.organization'],
                'extractor': self.extract_company_team
            }
        }
    
    async def extract(self, soup: BeautifulSoup, url: str) -> List[Profile]:
        """Extract profiles using site-specific strategies"""
        url_domain = urlparse(url).netloc.lower()
        
        # Try LinkedIn profile extraction
        if 'linkedin.com' in url_domain and '/in/' in url:
            return await self.extract_linkedin_profile(soup, url)
        
        # Try GitHub profile extraction
        if 'github.com' in url_domain:
            return await self.extract_github_profile(soup, url)
        
        # Try Twitter profile extraction
        if 'twitter.com' in url_domain or 'x.com' in url_domain:
            return await self.extract_twitter_profile(soup, url)
        
        # Try company team page extraction
        if self.is_company_team_page(soup, url):
            return await self.extract_company_team(soup, url)
        
        return []
    
    def is_valid_linkedin_profile(self, name: str, title: str, bio: str) -> bool:
        """Check if LinkedIn profile data is valid (not login prompts or low-quality)"""
        if not name:
            return False
        
        # Filter out common login prompts and low-quality text
        invalid_patterns = [
            'sign in to view',
            'welcome back',
            'log in',
            'login',
            'join linkedin',
            'create account',
            'forgot password',
            'reset password',
            'public profile',
            'top-card_title',
            'contextual-sign-in',
            'sign-in-modal'
        ]
        
        # Check name, title, and bio for invalid patterns
        text_to_check = f"{name} {title or ''} {bio or ''}".lower()
        
        for pattern in invalid_patterns:
            if pattern in text_to_check:
                return False
        
        # Must have a meaningful name (not just generic text)
        if len(name.strip()) < 3:
            return False
        
        # Must not be just generic LinkedIn text
        if name.lower() in ['linkedin', 'profile', 'user', 'member']:
            return False
        
        return True

    async def extract_linkedin_profile(self, soup: BeautifulSoup, url: str) -> List[Profile]:
        """Extract profile from LinkedIn profile page"""
        try:
            # LinkedIn profile selectors
            name = self.extract_text(soup, [
                'h1.text-heading-xlarge',
                '.text-heading-xlarge',
                'h1[class*="text-heading"]',
                '.pv-text-details__left-panel h1'
            ])
            
            title = self.extract_text(soup, [
                '.text-body-medium.break-words',
                '.pv-text-details__left-panel .text-body-medium',
                '.pv-text-details__left-panel .text-body-medium.break-words',
                '[class*="text-body-medium"]'
            ])
            
            company = self.extract_text(soup, [
                '.pv-text-details__right-panel .text-body-medium',
                '.pv-text-details__right-panel .text-body-medium.break-words',
                '[class*="experience__company"]'
            ])
            
            location = self.extract_text(soup, [
                '.pv-text-details__left-panel .text-body-small',
                '.pv-text-details__left-panel .text-body-small.inline',
                '[class*="location"]'
            ])
            
            bio = self.extract_text(soup, [
                '.pv-shared-text-with-see-more .visually-hidden',
                '.pv-shared-text-with-see-more span',
                '.pv-shared-text-with-see-more',
                '[class*="summary"]'
            ])
            
            # Extract profile image
            image = self.extract_attribute(soup, [
                '.pv-top-card-profile-picture__image',
                '.profile-picture img',
                'img[alt*="profile"]'
            ], 'src')
            
            # Extract social links
            social_links = SocialLinks()
            social_links.linkedin = url
            
            # Look for other social media links
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if 'github.com' in href:
                    social_links.github = href
                elif 'twitter.com' in href or 'x.com' in href:
                    social_links.twitter = href
                elif 'instagram.com' in href:
                    social_links.instagram = href
            
            # Filter out low-quality profiles (login prompts, etc.)
            if name and self.is_valid_linkedin_profile(name, title, bio):
                confidence = self.calculate_linkedin_confidence(name, title, company, bio)
                
                return [Profile(
                    name=name,
                    title=title,
                    company=company,
                    location=location,
                    bio=bio,
                    image=image,
                    social_links=social_links,
                    extracted_from=url,
                    confidence=confidence,
                    extraction_strategy="linkedin_specific"
                )]
        
        except Exception as e:
            print(f"LinkedIn extraction error: {e}")
        
        return []
    
    async def extract_github_profile(self, soup: BeautifulSoup, url: str) -> List[Profile]:
        """Extract profile from GitHub profile page"""
        try:
            # GitHub profile selectors
            name = self.extract_text(soup, [
                '.vcard-names .p-name',
                '.vcard-names .p-nickname',
                '.vcard-names h1',
                '.vcard-names .p-realname'
            ])
            
            username = self.extract_text(soup, [
                '.vcard-names .p-nickname',
                '.vcard-names .p-realname + .p-nickname'
            ])
            
            bio = self.extract_text(soup, [
                '.vcard-details .p-note',
                '.vcard-details .p-bio',
                '.vcard-details .p-note .p-bio'
            ])
            
            company = self.extract_text(soup, [
                '.vcard-details .p-org',
                '.vcard-details .p-company'
            ])
            
            location = self.extract_text(soup, [
                '.vcard-details .p-label',
                '.vcard-details .p-location'
            ])
            
            # Extract profile image
            image = self.extract_attribute(soup, [
                '.vcard-names .avatar',
                '.vcard-names img.avatar',
                '.avatar img'
            ], 'src')
            
            # Extract social links
            social_links = SocialLinks()
            social_links.github = url
            
            # Look for website and other links
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if href.startswith('http') and 'github.com' not in href:
                    social_links.website = href
                elif 'linkedin.com' in href:
                    social_links.linkedin = href
                elif 'twitter.com' in href or 'x.com' in href:
                    social_links.twitter = href
            
            if name or username:
                confidence = self.calculate_github_confidence(name, username, bio, company)
                
                return [Profile(
                    name=name or username,
                    title=f"GitHub User: {username}" if username else None,
                    bio=bio,
                    company=company,
                    location=location,
                    image=image,
                    social_links=social_links,
                    extracted_from=url,
                    confidence=confidence,
                    extraction_strategy="github_specific"
                )]
        
        except Exception as e:
            print(f"GitHub extraction error: {e}")
        
        return []
    
    async def extract_twitter_profile(self, soup: BeautifulSoup, url: str) -> List[Profile]:
        """Extract profile from Twitter/X profile page"""
        try:
            # Twitter profile selectors (these may change frequently)
            name = self.extract_text(soup, [
                '[data-testid="UserName"] span',
                '[data-testid="UserName"]',
                'h1[role="heading"]',
                '.css-1dbjc4n h1'
            ])
            
            username = self.extract_text(soup, [
                '[data-testid="UserName"] + div',
                '[data-testid="UserName"] + span',
                '.css-1dbjc4n h1 + div'
            ])
            
            bio = self.extract_text(soup, [
                '[data-testid="UserDescription"]',
                '[data-testid="UserDescription"] span',
                '.css-1dbjc4n [data-testid="UserDescription"]'
            ])
            
            # Extract profile image
            image = self.extract_attribute(soup, [
                '[data-testid="UserAvatar-Container-"] img',
                '[data-testid="UserAvatar-Container-"]',
                '.css-1dbjc4n img[alt*="profile"]'
            ], 'src')
            
            # Extract social links
            social_links = SocialLinks()
            social_links.twitter = url
            
            if name or username:
                confidence = self.calculate_twitter_confidence(name, username, bio)
                
                return [Profile(
                    name=name or username,
                    title=f"Twitter User: {username}" if username else None,
                    bio=bio,
                    image=image,
                    social_links=social_links,
                    extracted_from=url,
                    confidence=confidence,
                    extraction_strategy="twitter_specific"
                )]
        
        except Exception as e:
            print(f"Twitter extraction error: {e}")
        
        return []
    
    async def extract_company_team(self, soup: BeautifulSoup, url: str) -> List[Profile]:
        """Extract team members from company team/leadership page"""
        profiles = []
        
        try:
            # Look for team member containers
            team_containers = self.find_team_containers(soup)
            
            for container in team_containers:
                profile = self.extract_team_member(container, url)
                if profile and self.is_valid_team_profile(profile):
                    profiles.append(profile)
            
            # If no team containers found, try alternative approaches
            if not profiles:
                profiles = self.extract_team_alternative(soup, url)
            
        except Exception as e:
            print(f"Company team extraction error: {e}")
        
        return profiles
    
    def is_valid_team_profile(self, profile: Profile) -> bool:
        """Check if team profile is valid and meaningful"""
        if not profile.name:
            return False
        
        # Must have a meaningful name
        if len(profile.name.strip()) < 3:
            return False
        
        # Must not be generic text
        if profile.name.lower() in ['team', 'member', 'profile', 'person', 'employee']:
            return False
        
        # Should have either title or company
        if not profile.title and not profile.company:
            return False
        
        return True
    
    def find_team_containers(self, soup: BeautifulSoup) -> List[Tag]:
        """Find containers that likely contain team member information"""
        containers = []
        
        # Common team container selectors
        selectors = [
            '[class*="team"]', '[class*="member"]', '[class*="profile"]',
            '[class*="card"]', '[class*="person"]', '[class*="employee"]',
            '[class*="leadership"]', '[class*="executive"]', '[class*="staff"]',
            'article', 'section', '.team-member', '.member', '.profile',
            '.card', '.person', '.employee', '.leader', '.executive'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                # Check if element contains profile-like information
                if self.looks_like_profile_container(element):
                    containers.append(element)
        
        # Also look for grid layouts that might contain team members
        grid_selectors = [
            '[class*="grid"]', '[class*="row"]', '[class*="column"]',
            '.grid', '.row', '.column', '.flex', '.flexbox'
        ]
        
        for selector in grid_selectors:
            elements = soup.select(selector)
            for element in elements:
                if self.looks_like_profile_grid(element):
                    containers.append(element)
        
        return containers
    
    def looks_like_profile_container(self, element: Tag) -> bool:
        """Check if an element looks like it contains profile information"""
        text = element.get_text().lower()
        
        # Look for profile indicators
        profile_indicators = [
            'name', 'title', 'position', 'role', 'job', 'bio', 'about',
            'experience', 'education', 'contact', 'email', 'phone'
        ]
        
        indicator_count = sum(1 for indicator in profile_indicators if indicator in text)
        return indicator_count >= 2  # At least 2 profile indicators
    
    def looks_like_profile_grid(self, element: Tag) -> bool:
        """Check if an element looks like a grid of profiles"""
        # Look for multiple profile-like elements
        profile_elements = element.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'div'], 
                                         class_=re.compile(r'name|title|position|role|bio', re.I))
        
        return len(profile_elements) >= 3  # At least 3 profile elements
    
    def extract_team_alternative(self, soup: BeautifulSoup, url: str) -> List[Profile]:
        """Alternative method to extract team information when containers aren't found"""
        profiles = []
        
        try:
            # Look for headings that might be names
            headings = soup.find_all(['h1', 'h2', 'h3', 'h4'])
            
            for heading in headings:
                text = heading.get_text(strip=True)
                if self.looks_like_name(text):
                    # Look for title/position in nearby elements
                    title = self.find_nearby_title(heading)
                    company = self.extract_company_from_context(heading, soup)
                    
                    if title or company:
                        profile = Profile(
                            name=text,
                            title=title,
                            company=company,
                            extracted_from=url,
                            confidence=0.6,
                            extraction_strategy="company_team_alternative"
                        )
                        profiles.append(profile)
        
        except Exception as e:
            print(f"Alternative team extraction error: {e}")
        
        return profiles
    
    def looks_like_name(self, text: str) -> bool:
        """Check if text looks like a person's name"""
        if not text or len(text) < 3:
            return False
        
        # Filter out common non-name text
        invalid_patterns = [
            'team', 'leadership', 'about', 'company', 'organization',
            'contact', 'careers', 'news', 'blog', 'products', 'services',
            'home', 'login', 'sign up', 'search', 'menu', 'navigation'
        ]
        
        text_lower = text.lower()
        for pattern in invalid_patterns:
            if pattern in text_lower:
                return False
        
        # Check if it looks like a name (has multiple words, reasonable length)
        words = text.split()
        if len(words) >= 2 and len(words) <= 4:
            return True
        
        return False
    
    def find_nearby_title(self, heading: Tag) -> Optional[str]:
        """Find job title in elements near the heading"""
        # Look in the same container
        parent = heading.parent
        if parent:
            # Look for title-like text
            title_elements = parent.find_all(['p', 'span', 'div'], 
                                           class_=re.compile(r'title|position|role|job', re.I))
            for element in title_elements:
                text = element.get_text(strip=True)
                if text and len(text) > 3 and text != heading.get_text(strip=True):
                    return text
        
        return None
    
    def extract_company_from_context(self, heading: Tag, soup: BeautifulSoup) -> Optional[str]:
        """Extract company name from page context"""
        # Look for company name in page title, headings, or common locations
        page_title = soup.find('title')
        if page_title:
            title_text = page_title.get_text()
            # Extract company name from title (often "Company Name - About" or similar)
            if ' - ' in title_text:
                company = title_text.split(' - ')[0].strip()
                return company
        
        # Look for company name in main headings
        main_headings = soup.find_all(['h1', 'h2'], class_=re.compile(r'main|primary|hero', re.I))
        for h in main_headings:
            text = h.get_text(strip=True)
            if text and len(text) < 50:  # Reasonable company name length
                return text
        
        return None
    
    def is_valid_team_profile(self, profile: Profile) -> bool:
        """Check if team profile is valid and meaningful"""
        if not profile.name:
            return False
        
        # Must have a meaningful name
        if len(profile.name.strip()) < 3:
            return False
        
        # Must not be generic text
        if profile.name.lower() in ['team', 'member', 'profile', 'person', 'employee']:
            return False
        
        # Should have either title or company
        if not profile.title and not profile.company:
            return False
        
        return True
    
    def extract_team_member(self, container: Tag, url: str) -> Optional[Profile]:
        """Extract individual team member profile"""
        try:
            name = self.extract_text(container, [
                'h3', 'h4', '.name', '.member-name', '.employee-name',
                '.profile-name', '.person-name', '[class*="name"]'
            ])
            
            title = self.extract_text(container, [
                '.title', '.position', '.role', '.job-title',
                '.member-title', '.employee-title', '[class*="title"]'
            ])
            
            bio = self.extract_text(container, [
                '.bio', '.description', '.about', '.summary',
                '.member-bio', '.employee-bio', '[class*="bio"]'
            ])
            
            image = self.extract_attribute(container, [
                'img', '.image img', '.photo img', '.avatar img',
                '.member-image img', '.employee-image img'
            ], 'src')
            
            # Extract social links
            social_links = SocialLinks()
            for link in container.find_all('a', href=True):
                href = link.get('href', '')
                if 'linkedin.com' in href:
                    social_links.linkedin = href
                elif 'twitter.com' in href or 'x.com' in href:
                    social_links.twitter = href
                elif 'github.com' in href:
                    social_links.github = href
            
            if name:
                confidence = self.calculate_team_confidence(name, title, bio)
                
                return Profile(
                    name=name,
                    title=title,
                    bio=bio,
                    image=image,
                    social_links=social_links,
                    extracted_from=url,
                    confidence=confidence,
                    extraction_strategy="company_team"
                )
        
        except Exception as e:
            print(f"Team member extraction error: {e}")
        
        return None
    
    def is_company_team_page(self, soup: BeautifulSoup, url: str) -> bool:
        """Check if this is likely a company team/about page"""
        # Look for team-related content
        team_indicators = [
            'team', 'about', 'company', 'organization',
            'employees', 'staff', 'members', 'people'
        ]
        
        page_text = soup.get_text().lower()
        url_lower = url.lower()
        
        # Check URL and page content for team indicators
        for indicator in team_indicators:
            if indicator in url_lower or indicator in page_text:
                return True
        
        # Check for team-related HTML elements
        team_elements = soup.find_all(['h1', 'h2', 'h3'], string=re.compile(r'team|about|company|people', re.I))
        if team_elements:
            return True
        
        return False
    
    def extract_text(self, soup: BeautifulSoup, selectors: List[str]) -> Optional[str]:
        """Extract text content using multiple selectors"""
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    if text and len(text) > 2:
                        return text
            except:
                continue
        return None
    
    def extract_attribute(self, soup: BeautifulSoup, selectors: List[str], attr: str) -> Optional[str]:
        """Extract attribute value using multiple selectors"""
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    value = element.get(attr)
                    if value:
                        return value
            except:
                continue
        return None
    
    def calculate_linkedin_confidence(self, name: str, title: str, company: str, bio: str) -> float:
        """Calculate confidence for LinkedIn profile"""
        score = 0.0
        if name:
            score += 0.4
        if title:
            score += 0.3
        if company:
            score += 0.2
        if bio:
            score += 0.1
        return min(score, 1.0)
    
    def calculate_github_confidence(self, name: str, username: str, bio: str, company: str) -> float:
        """Calculate confidence for GitHub profile"""
        score = 0.0
        if name or username:
            score += 0.5
        if bio:
            score += 0.3
        if company:
            score += 0.2
        return min(score, 1.0)
    
    def calculate_twitter_confidence(self, name: str, username: str, bio: str) -> float:
        """Calculate confidence for Twitter profile"""
        score = 0.0
        if name or username:
            score += 0.6
        if bio:
            score += 0.4
        return min(score, 1.0)
    
    def calculate_team_confidence(self, name: str, title: str, bio: str) -> float:
        """Calculate confidence for team member profile"""
        score = 0.0
        if name:
            score += 0.5
        if title:
            score += 0.3
        if bio:
            score += 0.2
        return min(score, 1.0)
