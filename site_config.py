# Site Configuration for Advanced Web Scraping
# This file contains configurations for different types of websites

SITE_CONFIGURATIONS = {
    # Social Media Platforms
    "social_media": {
        "linkedin.com": {
            "extraction_priority": 1,
            "rate_limit": 2,
            "requires_js": True,
            "special_headers": {
                "x-requested-with": "XMLHttpRequest",
                "x-li-lang": "en_US",
                "x-li-track": '{"clientVersion":"1.10.*"}'
            },
            "selectors": {
                "name": ["h1.text-heading-xlarge", ".text-heading-xlarge", "[data-testid='hero-title']"],
                "title": [".text-body-medium", "[data-testid='hero-subtitle']"],
                "company": [".pv-text-details__right-panel .text-body-medium"],
                "location": [".pv-text-details__left-panel .text-body-small"],
                "bio": [".pv-shared-text-with-see-more", ".about__summary"]
            }
        },
        "github.com": {
            "extraction_priority": 1,
            "rate_limit": 1,
            "requires_js": False,
            "selectors": {
                "name": [".vcard-names .p-name", ".vcard-names .p-nickname"],
                "bio": [".user-profile-bio", ".vcard-details .p-note"],
                "company": [".vcard-details .p-org"],
                "location": [".vcard-details .p-label"]
            }
        },
        "twitter.com": {
            "extraction_priority": 2,
            "rate_limit": 3,
            "requires_js": True,
            "special_headers": {
                "x-twitter-active-user": "yes",
                "x-twitter-auth-type": "OAuth2Session"
            },
            "selectors": {
                "name": ["[data-testid='UserName']", ".css-1rynq56"],
                "bio": ["[data-testid='UserDescription']"],
                "location": ["[data-testid='UserLocation']"]
            }
        },
        "facebook.com": {
            "extraction_priority": 3,
            "rate_limit": 5,
            "requires_js": True,
            "special_headers": {
                "x-fb-lsd": "random_string",
                "x-fb-connection-quality": "EXCELLENT"
            },
            "selectors": {
                "name": ["h1[data-testid='profile_name']"],
                "bio": ["[data-testid='profile_bio']"]
            }
        },
        "instagram.com": {
            "extraction_priority": 3,
            "rate_limit": 4,
            "requires_js": True,
            "selectors": {
                "name": ["h1[data-testid='profile_name']"],
                "bio": ["[data-testid='profile_bio']"]
            }
        }
    },
    
    # Professional Platforms
    "professional": {
        "medium.com": {
            "extraction_priority": 2,
            "rate_limit": 2,
            "requires_js": False,
            "selectors": {
                "name": ["h1[data-testid='profile_name']"],
                "bio": ["[data-testid='profile_bio']"]
            }
        },
        "dev.to": {
            "extraction_priority": 2,
            "rate_limit": 2,
            "requires_js": False,
            "selectors": {
                "name": [".profile-header__name"],
                "title": [".profile-header__title"],
                "bio": [".profile-header__bio"],
                "location": [".profile-header__location"]
            }
        },
        "stackoverflow.com": {
            "extraction_priority": 2,
            "rate_limit": 2,
            "requires_js": False,
            "selectors": {
                "name": [".profile-user--name"],
                "title": [".profile-user--title"],
                "location": [".profile-user--location"],
                "bio": [".profile-user--bio"]
            }
        },
        "reddit.com": {
            "extraction_priority": 3,
            "rate_limit": 3,
            "requires_js": False,
            "selectors": {
                "name": [".profile-name", ".username"],
                "bio": [".profile-bio", ".user-description"]
            }
        }
    },
    
    # Creative Platforms
    "creative": {
        "behance.net": {
            "extraction_priority": 2,
            "rate_limit": 2,
            "requires_js": False,
            "selectors": {
                "name": [".profile-name", ".user-name"],
                "title": [".profile-title", ".user-title"],
                "location": [".profile-location", ".user-location"],
                "bio": [".profile-bio", ".user-bio"]
            }
        },
        "dribbble.com": {
            "extraction_priority": 2,
            "rate_limit": 2,
            "requires_js": False,
            "selectors": {
                "name": [".profile-name", ".user-name"],
                "title": [".profile-title", ".user-title"],
                "location": [".profile-location", ".user-location"],
                "bio": [".profile-bio", ".user-bio"]
            }
        }
    },
    
    # Freelancing Platforms
    "freelancing": {
        "fiverr.com": {
            "extraction_priority": 2,
            "rate_limit": 2,
            "requires_js": False,
            "selectors": {
                "name": [".profile-name", ".seller-name"],
                "title": [".profile-title", ".seller-title"],
                "location": [".profile-location", ".seller-location"],
                "bio": [".profile-bio", ".seller-description"]
            }
        },
        "upwork.com": {
            "extraction_priority": 2,
            "rate_limit": 2,
            "requires_js": False,
            "selectors": {
                "name": [".profile-name", ".freelancer-name"],
                "title": [".profile-title", ".freelancer-title"],
                "location": [".profile-location", ".freelancer-location"],
                "bio": [".profile-bio", ".freelancer-description"]
            }
        }
    },
    
    # Business Platforms
    "business": {
        "producthunt.com": {
            "extraction_priority": 2,
            "rate_limit": 2,
            "requires_js": False,
            "selectors": {
                "name": [".profile-name", ".maker-name"],
                "title": [".profile-title", ".maker-title"],
                "bio": [".profile-bio", ".maker-bio"]
            }
        },
        "angel.co": {
            "extraction_priority": 2,
            "rate_limit": 2,
            "requires_js": False,
            "selectors": {
                "name": [".profile-name", ".founder-name"],
                "title": [".profile-title", ".founder-title"],
                "company": [".profile-company", ".founder-company"],
                "bio": [".profile-bio", ".founder-bio"]
            }
        },
        "crunchbase.com": {
            "extraction_priority": 2,
            "rate_limit": 2,
            "requires_js": False,
            "selectors": {
                "name": [".profile-name", ".person-name"],
                "title": [".profile-title", ".person-title"],
                "company": [".profile-company", ".person-company"],
                "bio": [".profile-bio", ".person-bio"]
            }
        }
    }
}

# Universal extraction patterns for unknown sites
UNIVERSAL_PATTERNS = {
    "name": [
        "h1", "h2", ".name", ".full-name", ".user-name", ".profile-name",
        ".author-name", ".person-name", ".member-name", ".title",
        "[itemprop='name']", "[class*='name']", "[id*='name']"
    ],
    "title": [
        ".title", ".job-title", ".position", ".role", ".occupation",
        ".designation", ".job-role", ".profile-title", ".subtitle",
        "[itemprop='jobTitle']", "[class*='title']", "[class*='position']"
    ],
    "email": [
        "[href^='mailto:']", "a[href*='mailto']", ".email", ".contact-email",
        ".mail", ".contact-mail", "[itemprop='email']", "[class*='email']"
    ],
    "phone": [
        "[href^='tel:']", "a[href*='tel']", ".phone", ".contact-phone",
        ".tel", ".contact-tel", "[itemprop='telephone']", "[class*='phone']"
    ],
    "bio": [
        ".bio", ".about", ".description", ".summary", ".introduction",
        ".profile-bio", ".person-description", ".overview",
        "[itemprop='description']", "[class*='bio']", "[class*='about']"
    ],
    "company": [
        ".company", ".organization", ".employer", ".workplace",
        ".institution", ".firm", ".agency", ".studio",
        "[itemprop='affiliation']", "[class*='company']", "[class*='org']"
    ],
    "location": [
        ".location", ".address", ".city", ".country", ".place",
        ".region", ".area", ".state", ".province",
        "[itemprop='address']", "[class*='location']", "[class*='address']"
    ],
    "image": [
        ".profile-image", ".avatar", ".user-photo", ".profile-pic",
        ".person-image", ".member-photo", ".user-avatar",
        "[itemprop='image']", "img[alt*='profile']", "img[alt*='avatar']"
    ]
}

# Social media platform patterns
SOCIAL_PLATFORMS = {
    "linkedin": {
        "patterns": [
            r"linkedin\.com/in/[\w\-]+",
            r"linkedin\.com/company/[\w\-]+",
            r"linked\.in/in/[\w\-]+"
        ],
        "extract_username": lambda url: url.split('/in/')[-1].split('/')[0] if '/in/' in url else None
    },
    "github": {
        "patterns": [
            r"github\.com/[\w\-]+",
            r"github\.com/[\w\-]+/[\w\-]+"
        ],
        "extract_username": lambda url: url.split('github.com/')[-1].split('/')[0]
    },
    "twitter": {
        "patterns": [
            r"twitter\.com/[\w\-]+",
            r"x\.com/[\w\-]+"
        ],
        "extract_username": lambda url: url.split('/')[-1] if url.endswith('/') else url.split('/')[-1]
    },
    "facebook": {
        "patterns": [
            r"facebook\.com/[\w\-\.]+",
            r"fb\.com/[\w\-]+"
        ],
        "extract_username": lambda url: url.split('facebook.com/')[-1].split('/')[0]
    },
    "instagram": {
        "patterns": [
            r"instagram\.com/[\w\-\.]+"
        ],
        "extract_username": lambda url: url.split('instagram.com/')[-1].split('/')[0]
    },
    "medium": {
        "patterns": [
            r"medium\.com/@[\w\-]+"
        ],
        "extract_username": lambda url: url.split('@')[-1].split('/')[0] if '@' in url else None
    },
    "dev_to": {
        "patterns": [
            r"dev\.to/[\w\-]+"
        ],
        "extract_username": lambda url: url.split('dev.to/')[-1].split('/')[0]
    },
    "stack_overflow": {
        "patterns": [
            r"stackoverflow\.com/users/[\w\-]+"
        ],
        "extract_username": lambda url: url.split('users/')[-1].split('/')[0]
    },
    "reddit": {
        "patterns": [
            r"reddit\.com/user/[\w\-]+"
        ],
        "extract_username": lambda url: url.split('user/')[-1].split('/')[0]
    },
    "behance": {
        "patterns": [
            r"behance\.net/[\w\-]+"
        ],
        "extract_username": lambda url: url.split('behance.net/')[-1].split('/')[0]
    },
    "dribbble": {
        "patterns": [
            r"dribbble\.com/[\w\-]+"
        ],
        "extract_username": lambda url: url.split('dribbble.com/')[-1].split('/')[0]
    }
}

# Anti-detection configurations
ANTI_DETECTION_CONFIG = {
    "browser_profiles": {
        "chrome": {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "accept_language": "en-US,en;q=0.9",
            "accept_encoding": "gzip, deflate, br",
            "sec_fetch_dest": "document",
            "sec_fetch_mode": "navigate",
            "sec_fetch_site": "none",
            "sec_fetch_user": "?1",
            "upgrade_insecure_requests": "1",
            "cache_control": "max-age=0",
            "dnt": "1"
        },
        "firefox": {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "accept_language": "en-US,en;q=0.5",
            "accept_encoding": "gzip, deflate",
            "connection": "keep-alive",
            "upgrade_insecure_requests": "1",
            "sec_fetch_dest": "document",
            "sec_fetch_mode": "navigate",
            "sec_fetch_site": "none"
        },
        "safari": {
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "accept_language": "en-US,en;q=0.9",
            "accept_encoding": "gzip, deflate, br",
            "connection": "keep-alive",
            "upgrade_insecure_requests": "1"
        }
    },
    "request_delays": {
        "min_delay": 1,
        "max_delay": 5,
        "jitter": 0.5
    },
    "retry_config": {
        "max_retries": 3,
        "retry_delays": [2, 5, 10]
    }
}

# Site type detection patterns
SITE_TYPE_PATTERNS = {
    "social_media": [
        "profile", "user", "member", "follow", "following", "follower",
        "post", "tweet", "status", "timeline", "feed"
    ],
    "company_website": [
        "about", "team", "company", "organization", "corporate",
        "leadership", "executives", "founders", "staff"
    ],
    "portfolio": [
        "portfolio", "work", "projects", "case studies", "gallery",
        "showcase", "design", "creative", "art"
    ],
    "blog": [
        "blog", "post", "article", "published", "author", "writer",
        "content", "story", "news"
    ],
    "ecommerce": [
        "buy", "shop", "cart", "checkout", "price", "sale", "product",
        "store", "marketplace", "vendor"
    ],
    "forum": [
        "forum", "discussion", "thread", "reply", "comment", "community",
        "board", "message", "topic"
    ],
    "news": [
        "news", "breaking", "latest", "headlines", "journalism",
        "report", "coverage", "media"
    ]
}
