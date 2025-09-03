import asyncio
from scraping_service import FreshworksLeadershipScraper

async def test_selenium():
    scraper = FreshworksLeadershipScraper()
    profiles = await scraper.scrape_freshworks_leadership("https://www.freshworks.com/company/leadership/")
    print(f"Found {len(profiles)} profiles")
    for p in profiles:
        print(f"- {p.name}: {p.title}")

if __name__ == "__main__":
    asyncio.run(test_selenium())
