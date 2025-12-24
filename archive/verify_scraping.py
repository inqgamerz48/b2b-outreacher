from src import scraper

def test_deep_scraper():
    print("[*] Testing Deep Scraper...")
    
    # Example URL (Ideally one with a contact page)
    # Using a generic tech site or similar that usually has contact info might be risky if they block bots.
    # Let's ask the user to input one or try a safe one.
    
    target_url = input("Enter a URL to scrape (e.g. https://example.com): ")
    if not target_url:
        target_url = "https://www.google.com" # Fallback, though google blocks scraping usually
        
    print(f"[*] Starting Deep Scrape on {target_url}...")
    result = scraper.scrape_deep(target_url)
    
    print("-" * 30)
    print(f"Company: {result.get('Company')}")
    print(f"Email:   {result.get('Email')}")
    print(f"Source:  {result.get('Website')}")
    print("-" * 30)
    
    if result.get('Email'):
        print("[SUCCESS] Found an email!")
    else:
        print("[INFO] No email found (this might be expected for some sites).")

if __name__ == "__main__":
    test_deep_scraper()
