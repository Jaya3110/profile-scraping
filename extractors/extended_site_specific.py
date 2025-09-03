from bs4 import BeautifulSoup, Tag
from typing import List, Optional, Dict, Any
import re
from urllib.parse import urljoin, urlparse
import json

from models import Profile, SocialLinks

class ExtendedSiteSpecificExtractor:
    def __init__(self):
        # Extended site-specific extraction patterns
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
            'facebook': {
                'domain': 'facebook.com',
                'extractor': self.extract_facebook_profile
            },
            'instagram': {
                'domain': 'instagram.com',
                'extractor': self.extract_instagram_profile
            },
            'medium': {
                'domain': 'medium.com',
                'extractor': self.extract_medium_profile
            },
            'dev_to': {
                'domain': 'dev.to',
                'extractor': self.extract_devto_profile
            },
            'stack_overflow': {
                'domain': 'stackoverflow.com',
                'extractor': self.extract_stackoverflow_profile
            },
            'reddit': {
                'domain': 'reddit.com',
                'extractor': self.extract_reddit_profile
            },
            'behance': {
                'domain': 'behance.net',
                'extractor': self.extract_behance_profile
            },
            'dribbble': {
                'domain': 'dribbble.com',
                'extractor': self.extract_dribbble_profile
            },
            'fiverr': {
                'domain': 'fiverr.com',
                'extractor': self.extract_fiverr_profile
            },
            'upwork': {
                'domain': 'upwork.com',
                'extractor': self.extract_upwork_profile
            },
            'producthunt': {
                'domain': 'producthunt.com',
                'extractor': self.extract_producthunt_profile
            },
            'angel_list': {
                'domain': 'angel.co',
                'extractor': self.extract_angellist_profile
            },
            'crunchbase': {
                'domain': 'crunchbase.com',
                'extractor': self.extract_crunchbase_profile
            }
        }
    
    async def extract(self, soup: BeautifulSoup, url: str) -> List[Profile]:
        """Extract profiles using site-specific strategies"""
        url_domain = urlparse(url).netloc.lower()
        
        # Try site-specific extraction
        for site_name, site_info in self.site_patterns.items():
            if site_info['domain'] in url_domain:
                return await site_info['extractor'](soup, url)
        
        # Try company team page extraction
        if self.is_company_team_page(soup, url):
            return await self.extract_company_team(soup, url)
        
        return []
    
    async def extract_linkedin_profile(self, soup: BeautifulSoup, url: str) -> List[Profile]:
        """Extract profile from LinkedIn profile page"""
        try:
            # LinkedIn profile selectors (updated for current LinkedIn)
            name = self.extract_text(soup, [
                'h1.text-heading-xlarge',
                '.text-heading-xlarge',
                'h1[class*="text-heading"]',
                '.pv-text-details__left-panel h1',
                '[data-testid="hero-title"]',
                '.hero-title'
            ])
            
            title = self.extract_text(soup, [
                '.text-body-medium',
                '.pv-text-details__left-panel .text-body-medium',
                '[data-testid="hero-subtitle"]',
                '.hero-subtitle',
                '.top-card__headline'
            ])
            
            company = self.extract_text(soup, [
                '.pv-text-details__right-panel .text-body-medium',
                '[data-testid="experience-company-name"]',
                '.experience__company-name'
            ])
            
            location = self.extract_text(soup, [
                '.pv-text-details__left-panel .text-body-small',
                '[data-testid="hero-location"]',
                '.hero-location'
            ])
            
            bio = self.extract_text(soup, [
                '.pv-shared-text-with-see-more',
                '.text-body-medium',
                '.about__summary',
                '[data-testid="about"]'
            ])
            
            # Extract social links
            social_links = self.extract_social_links(soup, url)
            
            if self.is_valid_linkedin_profile(name, title, bio):
                return [Profile(
                    name=name,
                    title=title,
                    company=company,
                    location=location,
                    bio=bio,
                    social_links=social_links,
                    extracted_from=url,
                    confidence=0.9,
                    extraction_strategy="linkedin_specific"
                )]
        
        except Exception as e:
            print(f"LinkedIn extraction error: {e}")
        
        return []
    
    async def extract_github_profile(self, soup: BeautifulSoup, url: str) -> List[Profile]:
        """Extract profile from GitHub profile page"""
        try:
            name = self.extract_text(soup, [
                '.vcard-names .p-name',
                '.vcard-names .p-nickname',
                '.profile-names .p-name'
            ])
            
            bio = self.extract_text(soup, [
                '.user-profile-bio',
                '.vcard-details .p-note',
                '.profile-bio'
            ])
            
            company = self.extract_text(soup, [
                '.vcard-details .p-org',
                '.profile-company'
            ])
            
            location = self.extract_text(soup, [
                '.vcard-details .p-label',
                '.profile-location'
            ])
            
            # Extract social links
            social_links = self.extract_social_links(soup, url)
            
            if name:
                return [Profile(
                    name=name,
                    bio=bio,
                    company=company,
                    location=location,
                    social_links=social_links,
                    extracted_from=url,
                    confidence=0.9,
                    extraction_strategy="github_specific"
                )]
        
        except Exception as e:
            print(f"GitHub extraction error: {e}")
        
        return []
    
    async def extract_twitter_profile(self, soup: BeautifulSoup, url: str) -> List[Profile]:
        """Extract profile from Twitter/X profile page"""
        try:
            name = self.extract_text(soup, [
                '[data-testid="UserName"]',
                '.css-1rynq56',
                '.css-1dbjc4n',
                '.profile-name'
            ])
            
            bio = self.extract_text(soup, [
                '[data-testid="UserDescription"]',
                '.css-1rynq56',
                '.profile-bio'
            ])
            
            location = self.extract_text(soup, [
                '[data-testid="UserLocation"]',
                '.profile-location'
            ])
            
            # Extract social links
            social_links = self.extract_social_links(soup, url)
            
            if name:
                return [Profile(
                    name=name,
                    bio=bio,
                    location=location,
                    social_links=social_links,
                    extracted_from=url,
                    confidence=0.8,
                    extraction_strategy="twitter_specific"
                )]
        
        except Exception as e:
            print(f"Twitter extraction error: {e}")
        
        return []
    
    async def extract_facebook_profile(self, soup: BeautifulSoup, url: str) -> List[Profile]:
        """Extract profile from Facebook profile page"""
        try:
            name = self.extract_text(soup, [
                'h1[data-testid="profile_name"]',
                '.profile-name',
                'h1'
            ])
            
            bio = self.extract_text(soup, [
                '[data-testid="profile_bio"]',
                '.profile-bio',
                '.about-me'
            ])
            
            # Extract social links
            social_links = self.extract_social_links(soup, url)
            
            if name:
                return [Profile(
                    name=name,
                    bio=bio,
                    social_links=social_links,
                    extracted_from=url,
                    confidence=0.7,
                    extraction_strategy="facebook_specific"
                )]
        
        except Exception as e:
            print(f"Facebook extraction error: {e}")
        
        return []
    
    async def extract_instagram_profile(self, soup: BeautifulSoup, url: str) -> List[Profile]:
        """Extract profile from Instagram profile page"""
        try:
            name = self.extract_text(soup, [
                'h1[data-testid="profile_name"]',
                '.profile-name',
                'h1'
            ])
            
            bio = self.extract_text(soup, [
                '[data-testid="profile_bio"]',
                '.profile-bio',
                '.biography'
            ])
            
            # Extract social links
            social_links = self.extract_social_links(soup, url)
            
            if name:
                return [Profile(
                    name=name,
                    bio=bio,
                    social_links=social_links,
                    extracted_from=url,
                    confidence=0.7,
                    extraction_strategy="instagram_specific"
                )]
        
        except Exception as e:
            print(f"Instagram extraction error: {e}")
        
        return []
    
    async def extract_medium_profile(self, soup: BeautifulSoup, url: str) -> List[Profile]:
        """Extract profile from Medium profile page"""
        try:
            # Updated Medium selectors for current version
            name = self.extract_text(soup, [
                'h1[data-testid="profile_name"]',
                'h1[data-testid="profileName"]',
                '.profile-name',
                '.profileName',
                'h1',
                '[data-testid="profileName"]',
                '.profile-header h1',
                '.profile-header-name'
            ])
            
            bio = self.extract_text(soup, [
                '[data-testid="profile_bio"]',
                '[data-testid="profileBio"]',
                '.profile-bio',
                '.profileBio',
                '.bio',
                '.profile-description',
                '.profile-header-bio',
                '[data-testid="profileDescription"]'
            ])
            
            # Extract additional profile information
            title = self.extract_text(soup, [
                '.profile-title',
                '.profile-header-title',
                '[data-testid="profileTitle"]',
                '.profile-subtitle'
            ])
            
            location = self.extract_text(soup, [
                '.profile-location',
                '.profile-header-location',
                '[data-testid="profileLocation"]',
                '.location'
            ])
            
            # Extract social links with more comprehensive selectors
            social_links = self.extract_social_links(soup, url)
            
            # Try to extract follower count
            followers = self.extract_text(soup, [
                '[data-testid="profileFollowers"]',
                '.profile-followers',
                '.followers-count',
                '.profile-stats .followers'
            ])
            
            if name:
                return [Profile(
                    name=name,
                    title=title,
                    bio=bio,
                    location=location,
                    social_links=social_links,
                    extracted_from=url,
                    confidence=0.8,
                    extraction_strategy="medium_specific"
                )]
        
        except Exception as e:
            print(f"Medium extraction error: {e}")
        
        return []
    
    async def extract_devto_profile(self, soup: BeautifulSoup, url: str) -> List[Profile]:
        """Extract profile from Dev.to profile page"""
        try:
            name = self.extract_text(soup, [
                '.profile-header__name',
                '.profile-name',
                'h1'
            ])
            
            title = self.extract_text(soup, [
                '.profile-header__title',
                '.profile-title'
            ])
            
            bio = self.extract_text(soup, [
                '.profile-header__bio',
                '.profile-bio'
            ])
            
            location = self.extract_text(soup, [
                '.profile-header__location',
                '.profile-location'
            ])
            
            # Extract social links
            social_links = self.extract_social_links(soup, url)
            
            if name:
                return [Profile(
                    name=name,
                    title=title,
                    bio=bio,
                    location=location,
                    social_links=social_links,
                    extracted_from=url,
                    confidence=0.8,
                    extraction_strategy="devto_specific"
                )]
        
        except Exception as e:
            print(f"Dev.to extraction error: {e}")
        
        return []
    
    async def extract_stackoverflow_profile(self, soup: BeautifulSoup, url: str) -> List[Profile]:
        """Extract profile from Stack Overflow profile page"""
        try:
            name = self.extract_text(soup, [
                '.profile-user--name',
                '.profile-name',
                'h1'
            ])
            
            title = self.extract_text(soup, [
                '.profile-user--title',
                '.profile-title'
            ])
            
            location = self.extract_text(soup, [
                '.profile-user--location',
                '.profile-location'
            ])
            
            bio = self.extract_text(soup, [
                '.profile-user--bio',
                '.profile-bio'
            ])
            
            # Extract social links
            social_links = self.extract_social_links(soup, url)
            
            if name:
                return [Profile(
                    name=name,
                    title=title,
                    location=location,
                    bio=bio,
                    social_links=social_links,
                    extracted_from=url,
                    confidence=0.8,
                    extraction_strategy="stackoverflow_specific"
                )]
        
        except Exception as e:
            print(f"Stack Overflow extraction error: {e}")
        
        return []
    
    async def extract_reddit_profile(self, soup: BeautifulSoup, url: str) -> List[Profile]:
        """Extract profile from Reddit profile page"""
        try:
            name = self.extract_text(soup, [
                '.profile-name',
                'h1',
                '.username'
            ])
            
            bio = self.extract_text(soup, [
                '.profile-bio',
                '.user-description'
            ])
            
            # Extract social links
            social_links = self.extract_social_links(soup, url)
            
            if name:
                return [Profile(
                    name=name,
                    bio=bio,
                    social_links=social_links,
                    extracted_from=url,
                    confidence=0.7,
                    extraction_strategy="reddit_specific"
                )]
        
        except Exception as e:
            print(f"Reddit extraction error: {e}")
        
        return []
    
    async def extract_behance_profile(self, soup: BeautifulSoup, url: str) -> List[Profile]:
        """Extract profile from Behance profile page"""
        try:
            name = self.extract_text(soup, [
                '.profile-name',
                'h1',
                '.user-name'
            ])
            
            title = self.extract_text(soup, [
                '.profile-title',
                '.user-title'
            ])
            
            location = self.extract_text(soup, [
                '.profile-location',
                '.user-location'
            ])
            
            bio = self.extract_text(soup, [
                '.profile-bio',
                '.user-bio'
            ])
            
            # Extract social links
            social_links = self.extract_social_links(soup, url)
            
            if name:
                return [Profile(
                    name=name,
                    title=title,
                    location=location,
                    bio=bio,
                    social_links=social_links,
                    extracted_from=url,
                    confidence=0.8,
                    extraction_strategy="behance_specific"
                )]
        
        except Exception as e:
            print(f"Behance extraction error: {e}")
        
        return []
    
    async def extract_dribbble_profile(self, soup: BeautifulSoup, url: str) -> List[Profile]:
        """Extract profile from Dribbble profile page"""
        try:
            name = self.extract_text(soup, [
                '.profile-name',
                'h1',
                '.user-name'
            ])
            
            title = self.extract_text(soup, [
                '.profile-title',
                '.user-title'
            ])
            
            location = self.extract_text(soup, [
                '.profile-location',
                '.user-location'
            ])
            
            bio = self.extract_text(soup, [
                '.profile-bio',
                '.user-bio'
            ])
            
            # Extract social links
            social_links = self.extract_social_links(soup, url)
            
            if name:
                return [Profile(
                    name=name,
                    title=title,
                    location=location,
                    bio=bio,
                    social_links=social_links,
                    extracted_from=url,
                    confidence=0.8,
                    extraction_strategy="dribbble_specific"
                )]
        
        except Exception as e:
            print(f"Dribbble extraction error: {e}")
        
        return []
    
    async def extract_fiverr_profile(self, soup: BeautifulSoup, url: str) -> List[Profile]:
        """Extract profile from Fiverr profile page"""
        try:
            name = self.extract_text(soup, [
                '.profile-name',
                'h1',
                '.seller-name'
            ])
            
            title = self.extract_text(soup, [
                '.profile-title',
                '.seller-title'
            ])
            
            location = self.extract_text(soup, [
                '.profile-location',
                '.seller-location'
            ])
            
            bio = self.extract_text(soup, [
                '.profile-bio',
                '.seller-description'
            ])
            
            # Extract social links
            social_links = self.extract_social_links(soup, url)
            
            if name:
                return [Profile(
                    name=name,
                    title=title,
                    location=location,
                    bio=bio,
                    social_links=social_links,
                    extracted_from=url,
                    confidence=0.8,
                    extraction_strategy="fiverr_specific"
                )]
        
        except Exception as e:
            print(f"Fiverr extraction error: {e}")
        
        return []
    
    async def extract_upwork_profile(self, soup: BeautifulSoup, url: str) -> List[Profile]:
        """Extract profile from Upwork profile page"""
        try:
            name = self.extract_text(soup, [
                '.profile-name',
                'h1',
                '.freelancer-name'
            ])
            
            title = self.extract_text(soup, [
                '.profile-title',
                '.freelancer-title'
            ])
            
            location = self.extract_text(soup, [
                '.profile-location',
                '.freelancer-location'
            ])
            
            bio = self.extract_text(soup, [
                '.profile-bio',
                '.freelancer-description'
            ])
            
            # Extract social links
            social_links = self.extract_social_links(soup, url)
            
            if name:
                return [Profile(
                    name=name,
                    title=title,
                    location=location,
                    bio=bio,
                    social_links=social_links,
                    extracted_from=url,
                    confidence=0.8,
                    extraction_strategy="upwork_specific"
                )]
        
        except Exception as e:
            print(f"Upwork extraction error: {e}")
        
        return []
    
    async def extract_producthunt_profile(self, soup: BeautifulSoup, url: str) -> List[Profile]:
        """Extract profile from Product Hunt profile page"""
        try:
            # Updated Product Hunt selectors for current version
            name = self.extract_text(soup, [
                '.profile-name',
                '.maker-name',
                'h1',
                '.profile-header h1',
                '[data-testid="profileName"]',
                '.profile-title',
                '.maker-title',
                '.profile-header-name'
            ])
            
            title = self.extract_text(soup, [
                '.profile-title',
                '.maker-title',
                '.profile-subtitle',
                '.maker-subtitle',
                '.profile-header-title',
                '[data-testid="profileTitle"]',
                '.profile-role',
                '.maker-role'
            ])
            
            bio = self.extract_text(soup, [
                '.profile-bio',
                '.maker-bio',
                '.profile-description',
                '.maker-description',
                '.profile-about',
                '.maker-about',
                '[data-testid="profileBio"]',
                '.profile-header-bio'
            ])
            
            # Extract additional information
            location = self.extract_text(soup, [
                '.profile-location',
                '.maker-location',
                '.profile-header-location',
                '[data-testid="profileLocation"]',
                '.location'
            ])
            
            company = self.extract_text(soup, [
                '.profile-company',
                '.maker-company',
                '.profile-header-company',
                '[data-testid="profileCompany"]',
                '.company'
            ])
            
            # Extract social links with more comprehensive selectors
            social_links = self.extract_social_links(soup, url)
            
            # Try to extract stats
            followers = self.extract_text(soup, [
                '.profile-followers',
                '.maker-followers',
                '.followers-count',
                '[data-testid="profileFollowers"]'
            ])
            
            if name:
                return [Profile(
                    name=name,
                    title=title,
                    bio=bio,
                    location=location,
                    company=company,
                    social_links=social_links,
                    extracted_from=url,
                    confidence=0.8,
                    extraction_strategy="producthunt_specific"
                )]
        
        except Exception as e:
            print(f"Product Hunt extraction error: {e}")
        
        return []
    
    async def extract_angellist_profile(self, soup: BeautifulSoup, url: str) -> List[Profile]:
        """Extract profile from AngelList profile page"""
        try:
            name = self.extract_text(soup, [
                '.profile-name',
                'h1',
                '.founder-name'
            ])
            
            title = self.extract_text(soup, [
                '.profile-title',
                '.founder-title'
            ])
            
            company = self.extract_text(soup, [
                '.profile-company',
                '.founder-company'
            ])
            
            bio = self.extract_text(soup, [
                '.profile-bio',
                '.founder-bio'
            ])
            
            # Extract social links
            social_links = self.extract_social_links(soup, url)
            
            if name:
                return [Profile(
                    name=name,
                    title=title,
                    company=company,
                    bio=bio,
                    social_links=social_links,
                    extracted_from=url,
                    confidence=0.8,
                    extraction_strategy="angellist_specific"
                )]
        
        except Exception as e:
            print(f"AngelList extraction error: {e}")
        
        return []
    
    async def extract_crunchbase_profile(self, soup: BeautifulSoup, url: str) -> List[Profile]:
        """Extract profile from Crunchbase profile page"""
        try:
            name = self.extract_text(soup, [
                '.profile-name',
                'h1',
                '.person-name'
            ])
            
            title = self.extract_text(soup, [
                '.profile-title',
                '.person-title'
            ])
            
            company = self.extract_text(soup, [
                '.profile-company',
                '.person-company'
            ])
            
            bio = self.extract_text(soup, [
                '.profile-bio',
                '.person-bio'
            ])
            
            # Extract social links
            social_links = self.extract_social_links(soup, url)
            
            if name:
                return [Profile(
                    name=name,
                    title=title,
                    company=company,
                    bio=bio,
                    social_links=social_links,
                    extracted_from=url,
                    confidence=0.8,
                    extraction_strategy="crunchbase_specific"
                )]
        
        except Exception as e:
            print(f"Crunchbase extraction error: {e}")
        
        return []
    
    async def extract_company_team(self, soup: BeautifulSoup, url: str) -> List[Profile]:
        """Extract team member profiles from company pages"""
        profiles = []
        
        # Common team member selectors
        team_selectors = [
            '.team-member', '.employee', '.staff', '.person',
            '.about-person', '.team', '.leadership',
            '.founder', '.co-founder', '.executive',
            '.board-member', '.advisor', '.consultant'
        ]
        
        for selector in team_selectors:
            team_elements = soup.select(selector)
            for element in team_elements:
                profile = self.extract_team_member(element, url)
                if profile:
                    profiles.append(profile)
        
        return profiles
    
    def extract_team_member(self, element: Tag, url: str) -> Optional[Profile]:
        """Extract a single team member profile"""
        try:
            name = self.extract_text(element, [
                '.name', '.full-name', '.person-name',
                'h3', 'h4', '.title', '.heading'
            ])
            
            title = self.extract_text(element, [
                '.title', '.job-title', '.position', '.role',
                '.occupation', '.designation'
            ])
            
            bio = self.extract_text(element, [
                '.bio', '.description', '.about', '.summary',
                'p', '.text'
            ])
            
            image = self.extract_image(element, [
                'img', '.image', '.photo', '.avatar'
            ])
            
            if name:
                return Profile(
                    name=name,
                    title=title,
                    bio=bio,
                    image=image,
                    extracted_from=url,
                    confidence=0.7,
                    extraction_strategy="company_team"
                )
        
        except Exception as e:
            print(f"Team member extraction error: {e}")
        
        return None
    
    def extract_text(self, soup: BeautifulSoup, selectors: List[str]) -> Optional[str]:
        """Extract text using multiple selectors"""
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text().strip()
                if text:
                    return text
        return None
    
    def extract_image(self, soup: BeautifulSoup, selectors: List[str]) -> Optional[str]:
        """Extract image URL using multiple selectors"""
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'img':
                    src = element.get('src')
                    if src:
                        return src
                else:
                    img = element.find('img')
                    if img:
                        src = img.get('src')
                        if src:
                            return src
        return None
    
    def extract_social_links(self, soup: BeautifulSoup, base_url: str) -> SocialLinks:
        """Extract social media links"""
        social_links = SocialLinks()
        
        # LinkedIn
        linkedin_link = soup.find('a', href=re.compile(r'linkedin\.com'))
        if linkedin_link:
            social_links.linkedin = linkedin_link['href']
        
        # Twitter
        twitter_link = soup.find('a', href=re.compile(r'twitter\.com|x\.com'))
        if twitter_link:
            social_links.twitter = twitter_link['href']
        
        # GitHub
        github_link = soup.find('a', href=re.compile(r'github\.com'))
        if github_link:
            social_links.github = github_link['href']
        
        # Website
        website_links = soup.find_all('a', href=re.compile(r'^https?://'))
        for link in website_links:
            href = link['href']
            if not any(domain in href for domain in ['linkedin.com', 'twitter.com', 'github.com', 'facebook.com', 'instagram.com']):
                social_links.website = href
                break
        
        return social_links
    
    def is_company_team_page(self, soup: BeautifulSoup, url: str) -> bool:
        """Check if this is a company team page"""
        text_content = soup.get_text().lower()
        team_indicators = [
            'team', 'about us', 'our team', 'leadership',
            'founders', 'executives', 'staff', 'employees'
        ]
        
        return any(indicator in text_content for indicator in team_indicators)
    
    def is_valid_linkedin_profile(self, name: str, title: str, bio: str) -> bool:
        """Check if LinkedIn profile data is valid"""
        if not name:
            return False
        
        # Filter out common login prompts and low-quality text
        invalid_patterns = [
            'sign in to view', 'welcome back', 'log in', 'login',
            'join linkedin', 'create account', 'forgot password',
            'reset password', 'public profile', 'top-card_title',
            'contextual-sign-in', 'sign-in-modal'
        ]
        
        text_to_check = f"{name} {title or ''} {bio or ''}".lower()
        
        for pattern in invalid_patterns:
            if pattern in text_to_check:
                return False
        
        return len(name.strip()) >= 3
