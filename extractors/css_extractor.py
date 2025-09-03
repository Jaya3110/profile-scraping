from bs4 import BeautifulSoup, Tag
from typing import List, Optional, Dict, Any
import re
from urllib.parse import urljoin, urlparse

from models import Profile, SocialLinks

class CSSProfileExtractor:
    def __init__(self):
        # Common CSS selectors for profile information
        self.selectors = {
            'name': [
                '.profile-name', '.user-name', '.full-name', 'h1.name',
                '.author-name', '.person-name', '.member-name',
                'h1', 'h2', '.title', '.heading',
                '[itemprop="name"]', '[class*="name"]'
            ],
            'title': [
                '.profile-title', '.job-title', '.position', '.role',
                '.job-role', '.designation', '.occupation',
                '[itemprop="jobTitle"]', '[class*="title"]',
                '.subtitle', '.description'
            ],
            'email': [
                '[href^="mailto:"]', '.email', '.contact-email',
                '[itemprop="email"]', '[class*="email"]',
                'a[href*="mailto"]'
            ],
            'phone': [
                '.phone', '.contact-phone', '.tel',
                '[itemprop="telephone"]', '[class*="phone"]',
                'a[href^="tel:"]'
            ],
            'image': [
                '.profile-image', '.avatar', '.user-photo', '.profile-pic',
                '.person-image', '.member-photo',
                '[itemprop="image"]', 'img[alt*="profile"]',
                'img[alt*="avatar"]', 'img[alt*="photo"]'
            ],
            'bio': [
                '.profile-bio', '.description', '.about', '.summary',
                '.bio', '.introduction', '.overview',
                '[itemprop="description"]', '[class*="bio"]',
                '.profile-text', '.person-description'
            ],
            'company': [
                '.company', '.organization', '.employer',
                '[itemprop="affiliation"]', '[class*="company"]',
                '.workplace', '.institution'
            ],
            'location': [
                '.location', '.address', '.city', '.country',
                '[itemprop="address"]', '[class*="location"]',
                '.place', '.region'
            ]
        }
        
        # Social media link patterns
        self.social_patterns = {
            'linkedin': [
                'a[href*="linkedin.com"]', 'a[href*="linked.in"]',
                '.linkedin', '[class*="linkedin"]'
            ],
            'twitter': [
                'a[href*="twitter.com"]', 'a[href*="x.com"]',
                '.twitter', '[class*="twitter"]'
            ],
            'github': [
                'a[href*="github.com"]', '.github', '[class*="github"]'
            ],
            'website': [
                'a[href*="http"]:not([href*="linkedin.com"]):not([href*="twitter.com"]):not([href*="github.com"]):not([href*="facebook.com"]):not([href*="instagram.com"])',
                '.website', '[class*="website"]'
            ],
            'instagram': [
                'a[href*="instagram.com"]', '.instagram', '[class*="instagram"]'
            ],
            'facebook': [
                'a[href*="facebook.com"]', '.facebook', '[class*="facebook"]'
            ]
        }
    
    def is_valid_profile(self, name: str, title: str, bio: str) -> bool:
        """Check if extracted profile data is valid and meaningful"""
        if not name:
            return False
        
        # Filter out common low-quality text patterns
        invalid_patterns = [
            'sign in to view',
            'welcome back',
            'log in',
            'login',
            'join',
            'create account',
            'forgot password',
            'reset password',
            'public profile',
            'top-card_title',
            'contextual-sign-in',
            'sign-in-modal',
            'block or report',
            'follow',
            'message',
            'connect',
            'view profile',
            'see more',
            'read more',
            'learn more'
        ]
        
        # Check name, title, and bio for invalid patterns
        text_to_check = f"{name} {title or ''} {bio or ''}".lower()
        
        for pattern in invalid_patterns:
            if pattern in text_to_check:
                return False
        
        # Must have a meaningful name (not just generic text)
        if len(name.strip()) < 3:
            return False
        
        # Must not be just generic text
        if name.lower() in ['profile', 'user', 'member', 'person', 'name', 'title']:
            return False
        
        return True

    def extract(self, soup: BeautifulSoup, url: str) -> List[Profile]:
        """Extract profiles using CSS selectors"""
        profiles = []
        
        # Find profile containers
        profile_containers = self.find_profile_containers(soup)
        
        for container in profile_containers:
            profile = self.extract_from_container(container, url)
            if profile and self.is_valid_profile(profile.name, profile.title, profile.bio):
                profiles.append(profile)
        
        return profiles

    def looks_like_profile_container(self, element: Tag) -> bool:
        """Check if an element looks like it contains profile information"""
        text = element.get_text().lower()
        
        # Look for profile indicators
        profile_indicators = [
            'name', 'title', 'position', 'role', 'job', 'bio', 'about',
            'experience', 'education', 'contact', 'email', 'phone'
        ]
        
        indicator_count = sum(1 for indicator in profile_indicators if indicator in text)
        
        # Must have at least 3 profile indicators for better quality
        if indicator_count < 3:
            return False
        
        # Must not be just generic text
        if len(text.strip()) < 30:
            return False
        
        # Must contain actual names (not just generic text)
        if not any(word in text for word in ['mr', 'ms', 'dr', 'prof', 'ceo', 'cto', 'founder', 'director']):
            # Check if text contains what looks like a person's name
            words = text.split()
            if len(words) < 4:  # Too short to be meaningful profile
                return False
        
        # Must not be navigation or footer content
        if any(word in text for word in ['menu', 'navigation', 'footer', 'header', 'sidebar']):
            return False
        
        return True

    def find_profile_containers(self, soup: BeautifulSoup) -> List[Tag]:
        """Find containers that might hold profile information"""
        containers = []
        
        # Common profile container selectors
        container_selectors = [
            '.profile', '.person', '.member', '.team-member',
            '.employee', '.staff', '.author', '.contributor',
            '[itemtype*="Person"]', '[itemtype*="Organization"]',
            '.card', '.profile-card', '.person-card',
            'article', 'section', '.content'
        ]
        
        for selector in container_selectors:
            containers.extend(soup.select(selector))
        
        # Remove duplicates while preserving order
        seen = set()
        unique_containers = []
        for container in containers:
            if container not in seen:
                seen.add(container)
                unique_containers.append(container)
        
        return unique_containers[:5]  # Limit to 5 containers
    
    def extract_from_container(self, container: Tag, url: str) -> Optional[Profile]:
        """Extract profile information from a specific container"""
        try:
            # Extract basic information
            name = self.extract_text(container, self.selectors['name'])
            title = self.extract_text(container, self.selectors['title'])
            email = self.extract_attribute(container, self.selectors['email'], 'href')
            phone = self.extract_attribute(container, self.selectors['phone'], 'href')
            image = self.extract_attribute(container, self.selectors['image'], 'src')
            bio = self.extract_text(container, self.selectors['bio'])
            company = self.extract_text(container, self.selectors['company'])
            location = self.extract_text(container, self.selectors['location'])
            
            # Extract social links
            social_links = self.extract_social_links(container)
            
            # Clean up email (remove mailto:)
            if email and email.startswith('mailto:'):
                email = email[7:]
            
            # Clean up phone (remove tel:)
            if phone and phone.startswith('tel:'):
                phone = phone[4:]
            
            # Make image URL absolute
            if image and not image.startswith(('http://', 'https://')):
                image = urljoin(url, image)
            
            # Calculate confidence score
            confidence = self.calculate_confidence(name, title, email, bio)
            
            # Only return profile if we have at least some basic information
            if name or title or email:
                return Profile(
                    name=name,
                    title=title,
                    email=email,
                    phone=phone,
                    image=image,
                    bio=bio,
                    company=company,
                    location=location,
                    social_links=social_links,
                    extracted_from=url,
                    confidence=confidence,
                    extraction_strategy="css_selectors"
                )
        
        except Exception as e:
            print(f"Error extracting from container: {e}")
        
        return None
    
    def extract_text(self, container: Tag, selectors: List[str]) -> Optional[str]:
        """Extract text content using multiple selectors"""
        for selector in selectors:
            try:
                element = container.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    if text and len(text) > 2:  # Minimum meaningful length
                        return text
            except:
                continue
        return None
    
    def extract_attribute(self, container: Tag, selectors: List[str], attr: str) -> Optional[str]:
        """Extract attribute value using multiple selectors"""
        for selector in selectors:
            try:
                element = container.select_one(selector)
                if element:
                    value = element.get(attr)
                    if value:
                        return value
            except:
                continue
        return None
    
    def extract_social_links(self, container: Tag) -> SocialLinks:
        """Extract social media links"""
        social_links = SocialLinks()
        
        for platform, patterns in self.social_patterns.items():
            for pattern in patterns:
                try:
                    element = container.select_one(pattern)
                    if element:
                        href = element.get('href')
                        if href:
                            # Make URL absolute
                            if not href.startswith(('http://', 'https://')):
                                href = urljoin(container.get('data-url', ''), href)
                            
                            setattr(social_links, platform, href)
                            break
                except:
                    continue
        
        return social_links
    
    def calculate_confidence(self, name: Optional[str], title: Optional[str], 
                           email: Optional[str], bio: Optional[str]) -> float:
        """Calculate confidence score for extracted information"""
        score = 0.0
        total_fields = 4
        
        if name and len(name.strip()) > 2:
            score += 0.3
        if title and len(title.strip()) > 3:
            score += 0.25
        if email and '@' in email:
            score += 0.25
        if bio and len(bio.strip()) > 10:
            score += 0.2
        
        return min(score, 1.0)
