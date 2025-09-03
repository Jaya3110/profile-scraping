import asyncio
import httpx
import json
import time
import traceback

async def test_scraping():
    # Test with multiple URLs, starting with simpler ones that don't have Cloudflare
    test_urls = [
        "https://github.com/torvalds",  # Simple GitHub profile (no Cloudflare)
        "https://stackoverflow.com/users/22656/jon-skeet",  # Stack Overflow profile
        "https://www.freshworks.com/company/leadership/",  # Freshworks leadership (has Cloudflare)
    ]
    
    api_url = "http://localhost:8000/api/scrape"
    
    for url in test_urls:
        print(f"\n🧪 Testing API with: {url}")
        print(f"=" * 60)
        
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:  # Reduced timeout
                print("📡 Sending request to API...")
                response = await client.post(api_url, json={
                    "url": url,
                    "max_profiles": 3,  # Reduced for faster results
                    "timeout": 15  # Reduced timeout
                })
                
                processing_time = time.time() - start_time
                print(f"⏱️  Total time: {processing_time:.2f}s")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Success! Found {len(data['profiles'])} profiles")
                    print(f"📊 Processing time: {data['metadata']['processing_time']}s")
                    
                    for i, profile in enumerate(data['profiles'], 1):
                        print(f"\n👤 Profile {i}:")
                        print(f"   Name: {profile.get('name', 'N/A')}")
                        print(f"   Title: {profile.get('title', 'N/A')}")
                        print(f"   Company: {profile.get('company', 'N/A')}")
                        print(f"   Strategy: {profile.get('extraction_strategy', 'N/A')}")
                        print(f"   Confidence: {profile.get('confidence', 'N/A')}")
                        
                else:
                    print(f"❌ Error: {response.status_code}")
                    print(f"Response: {response.text}")
                    
        except httpx.TimeoutException:
            print(f"⏰ Timeout after {time.time() - start_time:.2f}s")
        except Exception as e:
            print(f"❌ Exception: {e}")
            print(f"Exception type: {type(e)}")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_scraping())
