from bs4 import BeautifulSoup, Tag
from typing import List, Optional, Dict, Any, Tuple
import re
import json
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass
from enum import Enum

from models import Profile, SocialLinks

class SiteType(Enum):
    SOCIAL_MEDIA = "social_media"
    COMPANY_WEBSITE = "company_website"
    PORTFOLIO = "portfolio"
    BLOG = "blog"
    ECOMMERCE = "ecommerce"
    FORUM = "forum"
    NEWS = "news"
    UNKNOWN = "unknown"

@dataclass
class ExtractionPattern:
    name: str
    selectors: List[str]
    regex_patterns: List[str]
    confidence: float
    site_types: List[SiteType]

class UniversalProfileExtractor:
    def __init__(self):
        self.site_patterns = self._initialize_site_patterns()
        self.extraction_patterns = self._initialize_extraction_patterns()
        self.social_platforms = self._initialize_social_platforms()
        # Generic section headings to ignore as names
        self.generic_headings = {
            "leadership",
            "executive team",
            "board of directors",
            "see what we’re all about",
            "see what we're all about",
            "our team",
            "management"
        }
        
    def _initialize_site_patterns(self) -> Dict[str, Dict]:
        """Initialize patterns for different site types"""
        return {
            'linkedin': {
                'domains': ['linkedin.com', 'linked.in'],
                'patterns': ['/in/', '/company/'],
                'type': SiteType.SOCIAL_MEDIA
            },
            'github': {
                'domains': ['github.com'],
                'patterns': ['/'],
                'type': SiteType.SOCIAL_MEDIA
            },
            'twitter': {
                'domains': ['twitter.com', 'x.com'],
                'patterns': ['/'],
                'type': SiteType.SOCIAL_MEDIA
            },
            'facebook': {
                'domains': ['facebook.com', 'fb.com'],
                'patterns': ['/profile.php', '/'],
                'type': SiteType.SOCIAL_MEDIA
            },
            'instagram': {
                'domains': ['instagram.com'],
                'patterns': ['/'],
                'type': SiteType.SOCIAL_MEDIA
            },
            'medium': {
                'domains': ['medium.com'],
                'patterns': ['/@', '/'],
                'type': SiteType.BLOG
            },
            'dev_to': {
                'domains': ['dev.to'],
                'patterns': ['/'],
                'type': SiteType.BLOG
            },
            'stack_overflow': {
                'domains': ['stackoverflow.com'],
                'patterns': ['/users/', '/'],
                'type': SiteType.FORUM
            },
            'reddit': {
                'domains': ['reddit.com'],
                'patterns': ['/user/', '/'],
                'type': SiteType.FORUM
            },
            'behance': {
                'domains': ['behance.net'],
                'patterns': ['/'],
                'type': SiteType.PORTFOLIO
            },
            'dribbble': {
                'domains': ['dribbble.com'],
                'patterns': ['/'],
                'type': SiteType.PORTFOLIO
            },
            'fiverr': {
                'domains': ['fiverr.com'],
                'patterns': ['/'],
                'type': SiteType.ECOMMERCE
            },
            'upwork': {
                'domains': ['upwork.com'],
                'patterns': ['/freelancers/', '/'],
                'type': SiteType.ECOMMERCE
            }
        }
    
    def _initialize_extraction_patterns(self) -> Dict[str, ExtractionPattern]:
        """Initialize extraction patterns for different profile elements"""
        return {
            'name': ExtractionPattern(
                name='name',
                selectors=[
                    # Generic name selectors
                    'h1', 'h2', '.name', '.full-name', '.user-name', '.profile-name',
                    '.author-name', '.person-name', '.member-name', '.title',
                    # Social media specific
                    '[data-testid="UserName"]', '.css-1rynq56', '.css-1dbjc4n',
                    # LinkedIn specific
                    '.text-heading-xlarge', '.pv-text-details__left-panel h1',
                    # GitHub specific
                    '.vcard-names .p-name', '.vcard-names .p-nickname',
                    # Common patterns
                    '[itemprop="name"]', '[class*="name"]', '[id*="name"]',
                    # Headers with name-like content
                    'h1:not([class*="logo"]):not([class*="brand"])',
                    'h2:not([class*="logo"]):not([class*="brand"])'
                ],
                regex_patterns=[
                    r'^[A-Z][a-z]+ [A-Z][a-z]+$',  # First Last
                    r'^[A-Z][a-z]+ [A-Z]\. [A-Z][a-z]+$',  # First M. Last
                    r'^[A-Z][a-z]+ [A-Z][a-z]+ [A-Z][a-z]+$'  # First Middle Last
                ],
                confidence=0.8,
                site_types=[SiteType.SOCIAL_MEDIA, SiteType.PORTFOLIO, SiteType.COMPANY_WEBSITE]
            ),
            'title': ExtractionPattern(
                name='title',
                selectors=[
                    # Generic title selectors
                    '.title', '.job-title', '.position', '.role', '.occupation',
                    '.designation', '.job-role', '.profile-title', '.subtitle',
                    # Social media specific
                    '[data-testid="UserDescription"]', '.css-1rynq56',
                    # LinkedIn specific
                    '.text-body-medium', '.pv-text-details__left-panel .text-body-medium',
                    # GitHub specific
                    '.vcard-details .p-org', '.vcard-details .p-role',
                    # Common patterns
                    '[itemprop="jobTitle"]', '[class*="title"]', '[class*="position"]',
                    # Description-like elements
                    '.description', '.bio', '.about', '.summary'
                ],
                regex_patterns=[
                    r'(?:Senior|Junior|Lead|Principal|Staff|Manager|Director|VP|CEO|CTO|CFO|COO|Founder|Co-founder|Developer|Engineer|Designer|Analyst|Consultant|Specialist|Coordinator|Assistant|Intern)',
                    r'(?:Software|Frontend|Backend|Full-stack|DevOps|Data|Machine Learning|AI|UX|UI|Product|Project|Business|Marketing|Sales|Customer|Technical|Creative|Content|Social Media|Digital|Web|Mobile|Cloud|Security|Quality|Test|QA)'
                ],
                confidence=0.7,
                site_types=[SiteType.SOCIAL_MEDIA, SiteType.PORTFOLIO, SiteType.COMPANY_WEBSITE]
            ),
            'email': ExtractionPattern(
                name='email',
                selectors=[
                    # Email link selectors
                    '[href^="mailto:"]', 'a[href*="mailto"]',
                    # Email text selectors
                    '.email', '.contact-email', '.mail', '.contact-mail',
                    # Common patterns
                    '[itemprop="email"]', '[class*="email"]', '[id*="email"]'
                ],
                regex_patterns=[
                    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                ],
                confidence=0.9,
                site_types=[SiteType.SOCIAL_MEDIA, SiteType.PORTFOLIO, SiteType.COMPANY_WEBSITE]
            ),
            'phone': ExtractionPattern(
                name='phone',
                selectors=[
                    # Phone link selectors
                    '[href^="tel:"]', 'a[href*="tel"]',
                    # Phone text selectors
                    '.phone', '.contact-phone', '.tel', '.contact-tel',
                    # Common patterns
                    '[itemprop="telephone"]', '[class*="phone"]', '[id*="phone"]'
                ],
                regex_patterns=[
                    r'\+?[\d\s\-\(\)]{10,}',  # International format
                    r'\(\d{3}\) \d{3}-\d{4}',  # US format
                    r'\d{3}-\d{3}-\d{4}'  # US format without parentheses
                ],
                confidence=0.8,
                site_types=[SiteType.SOCIAL_MEDIA, SiteType.PORTFOLIO, SiteType.COMPANY_WEBSITE]
            ),
            'bio': ExtractionPattern(
                name='bio',
                selectors=[
                    # Bio selectors
                    '.bio', '.about', '.description', '.summary', '.introduction',
                    '.profile-bio', '.person-description', '.overview',
                    # Social media specific
                    '[data-testid="UserDescription"]', '.css-1rynq56',
                    # LinkedIn specific
                    '.pv-shared-text-with-see-more', '.text-body-medium',
                    # GitHub specific
                    '.user-profile-bio', '.vcard-details .p-note',
                    # Common patterns
                    '[itemprop="description"]', '[class*="bio"]', '[class*="about"]',
                    # Paragraph content
                    'p:not([class*="footer"]):not([class*="header"]):not([class*="nav"])'
                ],
                regex_patterns=[],
                confidence=0.6,
                site_types=[SiteType.SOCIAL_MEDIA, SiteType.PORTFOLIO, SiteType.BLOG]
            ),
            'company': ExtractionPattern(
                name='company',
                selectors=[
                    # Company selectors
                    '.company', '.organization', '.employer', '.workplace',
                    '.institution', '.firm', '.agency', '.studio',
                    # LinkedIn specific
                    '.pv-text-details__right-panel .text-body-medium',
                    # GitHub specific
                    '.vcard-details .p-org',
                    # Common patterns
                    '[itemprop="affiliation"]', '[class*="company"]', '[class*="org"]'
                ],
                regex_patterns=[
                    r'(?:Inc\.|LLC|Ltd\.|Corp\.|Corporation|Company|Co\.|Studio|Agency|Group|Team|Solutions|Systems|Technologies|Software|Design|Consulting|Services|Partners|Ventures|Capital|Fund|Foundation|Institute|University|College|School)'
                ],
                confidence=0.7,
                site_types=[SiteType.SOCIAL_MEDIA, SiteType.PORTFOLIO, SiteType.COMPANY_WEBSITE]
            ),
            'location': ExtractionPattern(
                name='location',
                selectors=[
                    # Location selectors
                    '.location', '.address', '.city', '.country', '.place',
                    '.region', '.area', '.state', '.province',
                    # LinkedIn specific
                    '.pv-text-details__left-panel .text-body-small',
                    # GitHub specific
                    '.vcard-details .p-label',
                    # Common patterns
                    '[itemprop="address"]', '[class*="location"]', '[class*="address"]'
                ],
                regex_patterns=[
                    r'(?:San Francisco|New York|London|Berlin|Paris|Tokyo|Toronto|Sydney|Mumbai|Bangalore|Singapore|Amsterdam|Stockholm|Copenhagen|Vienna|Zurich|Dubai|Hong Kong|Seoul|Beijing|Shanghai|Moscow|São Paulo|Mexico City|Buenos Aires|Cairo|Nairobi|Lagos|Johannesburg)',
                    r'(?:CA|NY|TX|FL|IL|PA|OH|GA|NC|MI|NJ|VA|WA|AZ|CO|TN|OR|MN|WI|IN|MO|MD|LA|KY|SC|AL|CT|IA|OK|UT|NV|AR|MS|KS|NE|ID|HI|NH|ME|RI|MT|DE|SD|ND|AK|VT|WV|WY)'
                ],
                confidence=0.7,
                site_types=[SiteType.SOCIAL_MEDIA, SiteType.PORTFOLIO, SiteType.COMPANY_WEBSITE]
            ),
            'image': ExtractionPattern(
                name='image',
                selectors=[
                    # Image selectors
                    '.profile-image', '.avatar', '.user-photo', '.profile-pic',
                    '.person-image', '.member-photo', '.user-avatar',
                    # Social media specific
                    '[data-testid="UserAvatar"]', '.css-1rynq56 img',
                    # LinkedIn specific
                    '.pv-top-card-profile-picture__image',
                    # GitHub specific
                    '.vcard-names .avatar',
                    # Common patterns
                    '[itemprop="image"]', 'img[alt*="profile"]', 'img[alt*="avatar"]',
                    'img[alt*="photo"]', 'img[alt*="picture"]'
                ],
                regex_patterns=[],
                confidence=0.8,
                site_types=[SiteType.SOCIAL_MEDIA, SiteType.PORTFOLIO, SiteType.COMPANY_WEBSITE]
            )
        }
    
    def _initialize_social_platforms(self) -> Dict[str, Dict]:
        """Initialize social media platform patterns"""
        return {
            'linkedin': {
                'patterns': [
                    r'linkedin\.com/in/[\w\-]+',
                    r'linkedin\.com/company/[\w\-]+',
                    r'linked\.in/in/[\w\-]+'
                ],
                'extract_username': lambda url: url.split('/in/')[-1].split('/')[0] if '/in/' in url else None
            },
            'github': {
                'patterns': [
                    r'github\.com/[\w\-]+',
                    r'github\.com/[\w\-]+/[\w\-]+'
                ],
                'extract_username': lambda url: url.split('github.com/')[-1].split('/')[0]
            },
            'twitter': {
                'patterns': [
                    r'twitter\.com/[\w\-]+',
                    r'x\.com/[\w\-]+'
                ],
                'extract_username': lambda url: url.split('/')[-1] if url.endswith('/') else url.split('/')[-1]
            },
            'facebook': {
                'patterns': [
                    r'facebook\.com/[\w\-\.]+',
                    r'fb\.com/[\w\-]+'
                ],
                'extract_username': lambda url: url.split('facebook.com/')[-1].split('/')[0]
            },
            'instagram': {
                'patterns': [
                    r'instagram\.com/[\w\-\.]+'
                ],
                'extract_username': lambda url: url.split('instagram.com/')[-1].split('/')[0]
            },
            'medium': {
                'patterns': [
                    r'medium\.com/@[\w\-]+'
                ],
                'extract_username': lambda url: url.split('@')[-1].split('/')[0] if '@' in url else None
            },
            'dev_to': {
                'patterns': [
                    r'dev\.to/[\w\-]+'
                ],
                'extract_username': lambda url: url.split('dev.to/')[-1].split('/')[0]
            },
            'stack_overflow': {
                'patterns': [
                    r'stackoverflow\.com/users/[\w\-]+'
                ],
                'extract_username': lambda url: url.split('users/')[-1].split('/')[0]
            },
            'reddit': {
                'patterns': [
                    r'reddit\.com/user/[\w\-]+'
                ],
                'extract_username': lambda url: url.split('user/')[-1].split('/')[0]
            },
            'behance': {
                'patterns': [
                    r'behance\.net/[\w\-]+'
                ],
                'extract_username': lambda url: url.split('behance.net/')[-1].split('/')[0]
            },
            'dribbble': {
                'patterns': [
                    r'dribbble\.com/[\w\-]+'
                ],
                'extract_username': lambda url: url.split('dribbble.com/')[-1].split('/')[0]
            }
        }
    
    def detect_site_type(self, url: str, soup: BeautifulSoup) -> SiteType:
        """Detect the type of website based on URL and content"""
        url_domain = urlparse(url).netloc.lower()
        
        # Check against known site patterns
        for site_name, site_info in self.site_patterns.items():
            if any(domain in url_domain for domain in site_info['domains']):
                return site_info['type']
        
        # Analyze content to determine site type
        content_text = soup.get_text().lower()
        
        # Check for ecommerce indicators
        if any(word in content_text for word in ['buy', 'shop', 'cart', 'checkout', 'price', 'sale']):
            return SiteType.ECOMMERCE
        
        # Check for blog indicators
        if any(word in content_text for word in ['blog', 'post', 'article', 'published', 'author']):
            return SiteType.BLOG
        
        # Check for forum indicators
        if any(word in content_text for word in ['forum', 'discussion', 'thread', 'reply', 'comment']):
            return SiteType.FORUM
        
        # Check for news indicators
        if any(word in content_text for word in ['news', 'breaking', 'latest', 'headlines']):
            return SiteType.NEWS
        
        # Check for portfolio indicators
        if any(word in content_text for word in ['portfolio', 'work', 'projects', 'case studies']):
            return SiteType.PORTFOLIO
        
        # Default to company website
        return SiteType.COMPANY_WEBSITE
    
    def extract_profiles(self, soup: BeautifulSoup, url: str) -> List[Profile]:
        """Extract profiles using universal patterns"""
        site_type = self.detect_site_type(url, soup)
        profiles = []
        
        # Extract individual profiles
        profile_elements = self._find_profile_elements(soup, site_type)
        
        for element in profile_elements:
            profile = self._extract_single_profile(element, url, site_type)
            if profile and self._is_valid_profile(profile):
                profiles.append(profile)
        
        # Heading-based pass (names in headings; titles/images nearby)
        if True:
            try:
                heading_profiles = self._extract_profiles_from_headings_sync(soup, url)
                for p in heading_profiles:
                    if self._is_valid_profile(p):
                        profiles.append(p)
            except Exception:
                pass
        
        # If no individual profiles found, try to extract from the main page
        if not profiles:
            profile = self._extract_main_page_profile(soup, url, site_type)
            if profile and self._is_valid_profile(profile):
                profiles.append(profile)
        
        return profiles
    
    def _find_profile_elements(self, soup: BeautifulSoup, site_type: SiteType) -> List[Tag]:
        """Find elements that might contain profile information"""
        selectors = []
        
        if site_type == SiteType.SOCIAL_MEDIA:
            selectors = [
                '.profile', '.user-profile', '.member-profile',
                '[data-testid*="profile"]', '[class*="profile"]'
            ]
        elif site_type == SiteType.COMPANY_WEBSITE:
            selectors = [
                '.team-member', '.employee', '.staff', '.person',
                '.about-person', '.team', '.leadership',
                '.card', '[class*="card"]', '[class*="leader"]'
            ]
        elif site_type == SiteType.PORTFOLIO:
            selectors = [
                '.portfolio-item', '.project', '.work-item',
                '.case-study', '.gallery-item'
            ]
        
        elements = []
        for selector in selectors:
            elements.extend(soup.select(selector))
        
        # If no specific elements found, return the body
        if not elements:
            elements = [soup.find('body') or soup]
        
        return elements
    
    def _extract_single_profile(self, element: Tag, url: str, site_type: SiteType) -> Optional[Profile]:
        """Extract a single profile from an element"""
        profile_data = {}
        
        # Extract each field using patterns
        for field_name, pattern in self.extraction_patterns.items():
            if site_type in pattern.site_types:
                value = self._extract_field(element, pattern)
                if value:
                    profile_data[field_name] = value
        
        # If no image captured via patterns, try generic image extractor (handles background-image)
        if not profile_data.get('image'):
            generic_img = self._extract_image(element)
            if generic_img:
                profile_data['image'] = generic_img
        
        # Extract social links
        social_links = self._extract_social_links(element, url)
        if social_links:
            profile_data['social_links'] = social_links
        
        # Validate and reject generic headings
        name_val = profile_data.get('name')
        title_val = profile_data.get('title')

        # If we have a name but no title, try to read the next nearby text block
        if name_val and not title_val:
            heading = element.find(lambda t: t.name in ['h1','h2','h3','h4','h5','h6'] and name_val.strip() in t.get_text(strip=True))
            if heading:
                nxt = heading.find_next(lambda t: t.name in ['p','div','span'] and len(self._clean_text(t.get_text())) > 2)
                if nxt:
                    ttl = self._clean_text(nxt.get_text())
                    if ttl and ttl.lower() not in self.generic_headings:
                        title_val = ttl
                        profile_data['title'] = ttl
        image_val = profile_data.get('image')
        if name_val and name_val.strip().lower() in self.generic_headings:
            return None

        # Require name + (title or image)
        if not name_val:
            return None
        if not title_val and not image_val:
            return None

        # Confidence scoring
        confidence = 0.5
        if name_val and title_val:
            confidence += 0.3
        if image_val:
            confidence += 0.2

            return Profile(
            name=name_val,
            title=title_val,
                email=profile_data.get('email'),
                phone=profile_data.get('phone'),
                bio=profile_data.get('bio'),
                company=profile_data.get('company'),
                location=profile_data.get('location'),
                image=profile_data.get('image'),
                social_links=profile_data.get('social_links', SocialLinks()),
                extracted_from=url,
            confidence=min(max(confidence, 0.0), 1.0),
                extraction_strategy="universal_extractor"
            )
        
        return None
    
    def _extract_main_page_profile(self, soup: BeautifulSoup, url: str, site_type: SiteType) -> Optional[Profile]:
        """Extract profile information from the main page content"""
        profile_data = {}
        
        # Extract each field using patterns
        for field_name, pattern in self.extraction_patterns.items():
            if site_type in pattern.site_types:
                value = self._extract_field(soup, pattern)
                if value:
                    profile_data[field_name] = value
        
        # Extract social links
        social_links = self._extract_social_links(soup, url)
        if social_links:
            profile_data['social_links'] = social_links
        
        # Create profile if we have meaningful data
        if profile_data.get('name') or profile_data.get('title'):
            return Profile(
                name=profile_data.get('name'),
                title=profile_data.get('title'),
                email=profile_data.get('email'),
                phone=profile_data.get('phone'),
                bio=profile_data.get('bio'),
                company=profile_data.get('company'),
                location=profile_data.get('location'),
                image=profile_data.get('image'),
                social_links=profile_data.get('social_links', SocialLinks()),
                extracted_from=url,
                confidence=0.6,
                extraction_strategy="universal_extractor_main_page"
            )
        
        return None
    
    def _extract_field(self, element: Tag, pattern: ExtractionPattern) -> Optional[str]:
        """Extract a field using CSS selectors and regex patterns"""
        # Try CSS selectors first
        for selector in pattern.selectors:
            found = element.select_one(selector)
            if found:
                text = self._clean_text(found.get_text())
                if text and self._validate_field(text, pattern):
                    return text
        
        # Try regex patterns on all text
        text_content = element.get_text()
        for regex_pattern in pattern.regex_patterns:
            matches = re.findall(regex_pattern, text_content, re.IGNORECASE)
            if matches:
                return matches[0]
        
        return None
    
    def _extract_social_links(self, element: Tag, base_url: str) -> SocialLinks:
        """Extract social media links from an element"""
        social_links = SocialLinks()
        
        for platform, platform_info in self.social_platforms.items():
            # Look for links matching platform patterns
            for pattern in platform_info['patterns']:
                links = element.find_all('a', href=re.compile(pattern, re.IGNORECASE))
                for link in links:
                    href = link.get('href', '')
                    if href:
                        # Make relative URLs absolute
                        if href.startswith('/'):
                            href = urljoin(base_url, href)
                        elif not href.startswith('http'):
                            href = urljoin(base_url, href)
                        
                        # Set the social link
                        if hasattr(social_links, platform):
                            setattr(social_links, platform, href)
                            break
        
        return social_links
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common noise
        noise_patterns = [
            r'^\s*[•\-]\s*',  # Bullet points
            r'^\s*\d+\.\s*',  # Numbered lists
            r'^\s*[A-Z]\s*\.\s*',  # Single letters
        ]
        
        for pattern in noise_patterns:
            text = re.sub(pattern, '', text)
        
        return text.strip()
    
    def _validate_field(self, text: str, pattern: ExtractionPattern) -> bool:
        """Validate if extracted text is meaningful"""
        if not text or len(text.strip()) < 2:
            return False
        
        # Check against regex patterns if available
        if pattern.regex_patterns:
            for regex_pattern in pattern.regex_patterns:
                if re.match(regex_pattern, text, re.IGNORECASE):
                    return True
            return False
        
        # Basic validation
        return len(text.strip()) >= 2
    
    def _is_valid_profile(self, profile: Profile) -> bool:
        """Check if a profile is valid and meaningful"""
        if not profile.name and not profile.title:
            return False
        
        # Filter out common low-quality patterns
        invalid_patterns = [
            'sign in', 'login', 'join', 'create account',
            'forgot password', 'reset password', 'public profile',
            'welcome back', 'log in', 'sign up'
        ]
        
        text_to_check = f"{profile.name or ''} {profile.title or ''} {profile.bio or ''}".lower()
        
        for pattern in invalid_patterns:
            if pattern in text_to_check:
                return False
        
        return True

    async def extract_company_team_profiles(self, soup: BeautifulSoup, url: str) -> List[Profile]:
        """Extract multiple profiles from company team/leadership pages"""
        profiles = []
        
        # Common patterns for company team pages
        team_selectors = [
            '.team-member',
            '.leadership-member',
            '.executive',
            '.leadership',
            '.team',
            '.about-team',
            '.company-leadership',
            '.leadership-team',
            '.executive-team',
            '.management-team',
            '.board-member',
            '.director',
            '.officer',
            '.leadership-grid',
            '.team-grid',
            '.executives',
            '.management',
            '.board',
            '.leadership-list',
            '.team-list'
        ]
        
        # Find team member containers
        team_containers = []
        for selector in team_selectors:
            containers = soup.select(selector)
            if containers:
                team_containers.extend(containers)
                break
        
        # If no specific team containers found, look for common patterns
        if not team_containers:
            # Look for repeated patterns that might be team members
            potential_members = soup.find_all(['div', 'article', 'section'], class_=re.compile(r'(member|team|leadership|executive|director|officer)', re.I))
            team_containers = potential_members
        
        for container in team_containers:
            try:
                # Extract name
                name = self._extract_field_simple(container, [
                    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                    '.name', '.member-name', '.executive-name',
                    '.leader-name', '.director-name', '.officer-name',
                    '[data-testid*="name"]', '[class*="name"]'
                ])
                
                if not name:
                    continue
                
                # Extract title/role
                title = self._extract_field_simple(container, [
                    '.title', '.role', '.position', '.job-title',
                    '.member-title', '.executive-title', '.leader-title',
                    '.director-title', '.officer-title', '.position-title',
                    '[data-testid*="title"]', '[data-testid*="role"]',
                    '[class*="title"]', '[class*="role"]'
                ])
                
                # Extract bio/description
                bio = self._extract_field_simple(container, [
                    '.bio', '.description', '.about', '.summary',
                    '.member-bio', '.executive-bio', '.leader-bio',
                    '.director-bio', '.officer-bio', '.member-description',
                    '[data-testid*="bio"]', '[data-testid*="description"]',
                    '[class*="bio"]', '[class*="description"]'
                ])
                
                # Extract image
                image = self._extract_image(container)
                
                # Extract social links
                social_links = self._extract_social_links(container, url)
                
                # Extract company (if not already known from URL)
                company = self._extract_field_simple(container, [
                    '.company', '.organization', '.firm',
                    '.member-company', '.executive-company'
                ])
                
                # Extract location
                location = self._extract_field_simple(container, [
                    '.location', '.city', '.country',
                    '.member-location', '.executive-location'
                ])
                
                # Extract email
                email = self._extract_field_simple(container, [
                    'a[href^="mailto:"]',
                    '[data-testid*="email"]',
                    '.email', '.contact-email'
                ])
                
                # Clean and validate the profile
                name = self._clean_text(name)
                title = self._clean_text(title)
                bio = self._clean_text(bio)
                company = self._clean_text(company)
                location = self._clean_text(location)
                
                if self._is_valid_profile_simple(name, title, bio):
                    profile = Profile(
                        name=name,
                        title=title,
                        bio=bio,
                        company=company,
                        location=location,
                        email=email,
                        image_url=image,
                        social_links=social_links,
                        extracted_from=url,
                        confidence=0.7,
                        extraction_strategy="universal_company_team"
                    )
                    profiles.append(profile)
            
            except Exception as e:
                print(f"Error extracting profile from container: {e}")
                continue
        
        return profiles

    def _extract_field_simple(self, element: Tag, selectors: List[str]) -> Optional[str]:
        """Extract a field using CSS selectors"""
        for selector in selectors:
            found = element.select_one(selector)
            if found:
                text = self._clean_text(found.get_text())
                if text:
                    return text
        return None

    def _extract_image(self, element: Tag) -> Optional[str]:
        """Extract image URL from an element"""
        # <img> sources
        img = element.find('img')
        if img:
            src = img.get('src') or img.get('data-src') or img.get('data-original')
            if not src:
                # try srcset first candidate
                srcset = img.get('srcset')
                if srcset:
                    parts = [p.strip().split(' ')[0] for p in srcset.split(',') if p.strip()]
                    if parts:
                        src = parts[0]
            if src:
                return src
        # CSS background-image on the element or children
        style = element.get('style')
        if style:
            m = re.search(r"background-image\s*:\s*url\((['\"]?)(.*?)\1\)", style, re.IGNORECASE)
            if m:
                return m.group(2)
        for child in element.find_all(True, attrs={'style': True}):
            m = re.search(r"background-image\s*:\s*url\((['\"]?)(.*?)\1\)", child.get('style',''), re.IGNORECASE)
            if m:
                return m.group(2)
        return None

    # ---------------------------
    # Heading-based extraction helpers
    # ---------------------------

    def _looks_like_name(self, text: str) -> bool:
        if not text:
            return False
        t = text.strip()
        if t.lower() in self.generic_headings:
            return False
        # Heuristic: 2-4 tokens, start uppercase
        parts = t.split()
        if len(parts) < 2 or len(parts) > 4:
            return False
        caps = sum(1 for p in parts if p and p[0].isupper())
        return caps >= 2

    def _find_adjacent_text(self, heading: Tag) -> Optional[str]:
        # Check next siblings for a reasonable short text line (likely title)
        nxt = heading
        for _ in range(5):
            nxt = nxt.find_next_sibling()
            if not nxt:
                break
            if getattr(nxt, 'get_text', None):
                txt = self._clean_text(nxt.get_text())
                if txt and 2 < len(txt) < 120 and txt.lower() not in self.generic_headings:
                    return txt
        # Fallback: look downwards in parent
        parent = heading.find_parent()
        if parent:
            cand = parent.find(['p','span','div'])
            if cand:
                txt = self._clean_text(cand.get_text())
                if txt and 2 < len(txt) < 120 and txt.lower() not in self.generic_headings:
                    return txt
        return None

    def _extract_bio(self, container: Tag, heading: Tag) -> Optional[str]:
        # The longest paragraph near heading/container
        paras = container.find_all('p')
        if not paras:
            return None
        longest = max(paras, key=lambda p: len(self._clean_text(p.get_text() or '')))
        bio = self._clean_text(longest.get_text())
        return bio if bio and len(bio) > 40 else None

    def _extract_email(self, container: Tag) -> Optional[str]:
        text = container.get_text(" ", strip=True) if getattr(container, 'get_text', None) else ''
        m = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
        return m.group(0) if m else None

    def _score_profile(self, name: str, title: Optional[str], bio: Optional[str], image: Optional[str], social_links: SocialLinks) -> float:
        score = 0.5
        if name and title:
            score += 0.3
        if image:
            score += 0.15
        # any social link
        if any(getattr(social_links, k, None) for k in vars(social_links)):
            score += 0.05
        return min(score, 1.0)

    def _extract_image_with_base(self, element: Tag, base_url: str) -> Optional[str]:
        src = self._extract_image(element)
        if not src:
            return None
        if src.startswith('//'):
            return 'https:' + src
        if src.startswith('/'):
            return urljoin(base_url, src)
        if not src.startswith('http'):
            return urljoin(base_url, src)
        return src

    def _extract_profiles_from_headings_sync(self, soup: BeautifulSoup, url: str) -> List[Profile]:
        profiles: List[Profile] = []
        for heading in soup.find_all(["h2", "h3", "h4"]):
            name = self._clean_text(heading.get_text())
            if not self._looks_like_name(name):
                continue
            container = heading.find_parent(["div", "section"]) or heading
            title = self._find_adjacent_text(heading)
            bio = self._extract_bio(container, heading)
            image = self._extract_image_with_base(container, url)
            social_links = self._extract_social_links(container, url)
            email = self._extract_email(container)
            if not (title or bio or image or any(vars(social_links).values()) or email):
                continue
            profiles.append(Profile(
                name=name,
                title=title,
                bio=bio,
                email=email,
                image=image,
                social_links=social_links,
                extracted_from=url,
                confidence=self._score_profile(name, title, bio, image, social_links),
                extraction_strategy="heading_based"
            ))
        return profiles

    # ---------------------------
    # Leadership sections extraction
    # ---------------------------

    def extract_leadership_sections(self, soup: BeautifulSoup, url: str) -> List[Profile]:
        profiles: List[Profile] = []
        leadership_keywords = ["leadership", "executive team", "board of directors", "management", "our team"]

        for heading in soup.find_all(["h2", "h3", "h4"]):
            text = self._clean_text(heading.get_text()).lower()
            if any(k in text for k in leadership_keywords):
                section = heading.find_parent("section") or heading.parent
                if not section:
                    continue
                cards = section.find_all(["div", "article"], recursive=True)
                for card in cards:
                    profile = self._parse_leadership_card(card, url)
                    if profile:
                        profiles.append(profile)
        return profiles

    def _parse_leadership_card(self, card: Tag, url: str) -> Optional[Profile]:
        # Name: first h3/h4
        name_el = card.find(["h3", "h4"]) if hasattr(card, 'find') else None
        name = self._clean_text(name_el.get_text()) if name_el else None
        if not name or not self._looks_like_name(name):
            return None

        # Title: nearest p/span/div after name
        title = None
        if name_el:
            sib = name_el.find_next(["p", "span", "div"]) if hasattr(name_el, 'find_next') else None
            if sib:
                t = self._clean_text(sib.get_text())
                if t and t.lower() not in self.generic_headings and len(t) < 140:
                    title = t

        # Image: <img> or background-image
        image = self._extract_image_with_base(card, url)

        # Socials + email
        social_links = self._extract_social_links(card, url)
        email = self._extract_email(card)

        # Bio link (best-effort)
        bio = None
        try:
            link = card.find("a", string=re.compile(r"read more", re.I)) if hasattr(card, 'find') else None
            if link and link.get("href"):
                bio_url = urljoin(url, link["href"])
                bio = self._fetch_and_extract_bio_sync(bio_url)
        except Exception:
            pass

        # Relaxed acceptance rule for leadership cards
        if name and (title or image or bio):
            return Profile(
                name=name,
                title=title,
                email=email,
                bio=bio,
                image=image,
                social_links=social_links,
                extracted_from=url,
                confidence=0.9 if (image or title) else 0.7,
                extraction_strategy="leadership_section"
            )
        return None

    def _fetch_and_extract_bio_sync(self, bio_url: str) -> Optional[str]:
        try:
            import httpx
            r = httpx.get(bio_url, timeout=5.0, follow_redirects=True)
            if r.status_code != 200:
                return None
            bio_soup = BeautifulSoup(r.text, 'html.parser')
            paras = bio_soup.find_all('p')
            if not paras:
                return None
            longest = max(paras, key=lambda p: len(self._clean_text(p.get_text() or '')))
            bio = self._clean_text(longest.get_text())
            return bio if bio and len(bio) > 60 else None
        except Exception:
            return None

    # Public wrapper for heading-based extraction
    def extract_profiles_from_headings(self, soup: BeautifulSoup, url: str) -> List[Profile]:
        return self._extract_profiles_from_headings_sync(soup, url)

    def _is_valid_profile_simple(self, name: str, title: str, bio: str) -> bool:
        """Check if a profile is valid and meaningful"""
        if not name and not title:
            return False
        
        # Filter out common low-quality patterns
        invalid_patterns = [
            'sign in', 'login', 'join', 'create account',
            'forgot password', 'reset password', 'public profile',
            'welcome back', 'log in', 'sign up'
        ]
        
        text_to_check = f"{name or ''} {title or ''} {bio or ''}".lower()
        
        for pattern in invalid_patterns:
            if pattern in text_to_check:
                return False
        
        return True
