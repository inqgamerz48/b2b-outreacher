# src/scraper.py
import time
import requests
import random
import sys
import os
from bs4 import BeautifulSoup
from googlesearch import search
from urllib.parse import urljoin

# Add parent to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from src import utils

def google_search_leads(query, num_results=10):
    """
    Searches Google for the query and returns a list of result URLs.
    """
    print(f"[INFO] Searching Google for: {query}")
    results = []
    try:
        # pause=2.0 helps avoid getting 429 Too Many Requests
        for url in search(query, num=num_results, stop=num_results, pause=3.0):
            results.append(url)
    except Exception as e:
        print(f"[ERROR] Google Search failed: {e}")
    return results

def scrape_website_info(url):
    """
    Visits a URL and attempts to extract: title, meta description, and emails.
    """
    info = {
        "Website": url,
        "Name": "", # Hard to guess name from generic site, will try from title
        "Company": "",
        "Email": "",
        "LinkedIn": "",
        "Description": ""
    }
    
    clean_target_url = utils.clean_url(url)
    print(f"[INFO] Scraping {clean_target_url}...")
    
    try:
        headers = {'User-Agent': config.USER_AGENT}
        response = requests.get(clean_target_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"[WARN] Failed to load {url} (Status: {response.status_code})")
            return info
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Title / Company Name
        if soup.title:
            title_text = soup.title.string.strip()
            # Heuristic: usually "Company Name - tagline" or "Page | Company"
            info["Company"] = title_text.split("-")[0].split("|")[0].strip()
            info["Name"] = "Founder" # Placeholder, very hard to scrape specific founder name reliably from generic Home page
            
        # 2. Meta Description
        meta_desc = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
        if meta_desc:
            info["Description"] = meta_desc.get('content', '').strip()
            
        # 3. Email Extraction (mailto:)
        mailtos = soup.select('a[href^=mailto]')
        for link in mailtos:
            email = link['href'].replace('mailto:', '').split('?')[0].strip()
            if utils.validate_email(email) and utils.is_business_email(email):
                info["Email"] = email
                break # Take the first valid business email
        
        # 4. LinkedIn Extraction
        linkedin_links = soup.select('a[href*="linkedin.com/in/"], a[href*="linkedin.com/company/"]')
        for link in linkedin_links:
            href = link['href']
            info["LinkedIn"] = href
            # If we find a personal linkedin, it might be the founder
            if "/in/" in href:
                break
                
    except Exception as e:
        print(f"[ERROR] Error scraping {url}: {e}")
        
    # Polite delay
    time.sleep(random.uniform(1, 3))
    return info

def run_discovery(queries):
    """
    Main entry for discovery.
    queries: list of search strings
    """
    all_leads = []
    for q in queries:
        urls = google_search_leads(q, num_results=5) # kept low for safety/testing
        for url in urls:
            # Skip common social media or irrelevant sites if needed
            if "linkedin.com" in url or "twitter.com" in url or "facebook.com" in url:
                continue
                
            lead_data = scrape_website_info(url)
            if lead_data["Email"]: # Only keep if we found an email
                all_leads.append(lead_data)
            else:
                print(f"[SKIP] No email found for {url}")
                
    return all_leads
