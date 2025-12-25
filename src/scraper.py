# src/scraper.py
import time
import requests
import re
import random
import sys
import os
from bs4 import BeautifulSoup
from googlesearch import search
from urllib.parse import urljoin, urlparse

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

def extract_emails_from_text(text):
    """Finds emails in raw text using Regex."""
    # Basic regex for email
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, text)
    valid_emails = []
    for email in emails:
        if utils.validate_email(email) and utils.is_business_email(email):
            if verify_email_with_eva(email):
                valid_emails.append(email)
            else:
                print(f"[SKIP] Email failed verification: {email}")
    return list(set(valid_emails))

def verify_email_with_eva(email):
    """
    Verifies email using Eva API (Free, No Auth).
    Returns True if deliverable or unknown (safe to try), False if strictly undeliverable/spam.
    """
    try:
        url = f"https://api.eva.pingutil.com/email?email={email}"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        
        # Eva returns: {"data": {"email_address": "...", "domain": "...", "deliverable": true, "spam": false, ...}, "success": true}
        if not data.get("success"):
            return True # Fail open if API issues
            
        result = data.get("data", {})
        if result.get("spam"):
            return False # Reject spam/disposable
            
        if not result.get("deliverable") and not result.get("catch_all"):
             # If strictly not deliverable AND not catch_all -> Reject
             # Note: catch_all often returns deliverable=false or unknown, so we usually keep catch_all
             return False
             
        return True
    except Exception as e:
        print(f"[WARN] Eva Verification failed for {email}: {e}")
        return True # Fail open

# Random User Agents to prevent blocking
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
]

def get_soup(url):
    """Helper to get BeautifulSoup object with safety headers and rotation."""
    try:
        # Rotate User Agent
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f"[WARN] Failed to load {url}: {e}")
    return None

def find_internal_pages(soup, base_url):
    """Finds 'Contact', 'About', 'Team' pages."""
    links = {"contact": [], "about": []}
    if not soup: return links
    
    for a in soup.find_all('a', href=True):
        href = a['href']
        full_url = urljoin(base_url, href)
        
        # Ensure it's internal
        if urlparse(base_url).netloc not in urlparse(full_url).netloc:
            continue
            
        lower_href = href.lower()
        lower_text = a.get_text().lower()
        
        if "contact" in lower_href or "contact" in lower_text:
            links["contact"].append(full_url)
        elif "about" in lower_href or "us" in lower_href or "team" in lower_href or "about" in lower_text:
            links["about"].append(full_url)
            
    # Deduplicate
    links["contact"] = list(set(links["contact"]))[:1] # Take max 1 contact page
    links["about"] = list(set(links["about"]))[:1] # Take max 1 about page
    return links

def scrape_deep(url):
    """
    Visits Homepage -> Contact -> About to find the best email.
    """
    info = {
        "Website": url,
        "Name": "Founder",
        "Company": "",
        "Email": "",
        "LinkedIn": "",
        "Description": ""
    }
    
    clean_url = utils.clean_url(url)
    print(f"[INFO] 🕵️ Deep Scraping {clean_url}...")
    
    # 1. Scrape Homepage
    soup = get_soup(clean_url)
    if not soup: return info
    
    # Title/Company
    if soup.title:
        title_text = soup.title.string.strip()
        info["Company"] = title_text.split("-")[0].split("|")[0].strip()
        
    # Meta Desc
    meta_desc = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
    if meta_desc:
        info["Description"] = meta_desc.get('content', '').strip()
        
    # LinkedIn
    linkedin_links = soup.select('a[href*="linkedin.com/in/"], a[href*="linkedin.com/company/"]')
    for link in linkedin_links:
        info["LinkedIn"] = link['href']
        if "/in/" in link['href']: break
    
    # Email Hunting Strategy
    found_emails = []
    
    # A. Check Homepage Mailtos & Text
    for link in soup.select('a[href^=mailto]'):
        found_emails.append(link['href'].replace('mailto:', '').split('?')[0])
    found_emails.extend(extract_emails_from_text(soup.get_text()))
    
    # If no email, dig deeper
    if not found_emails:
        pages = find_internal_pages(soup, clean_url)
        to_visit = pages["contact"] + pages["about"]
        
        for page_url in to_visit:
            print(f"   -> Visiting sub-page: {page_url}")
            sub_soup = get_soup(page_url)
            if sub_soup:
                for link in sub_soup.select('a[href^=mailto]'):
                    found_emails.append(link['href'].replace('mailto:', '').split('?')[0])
                found_emails.extend(extract_emails_from_text(sub_soup.get_text()))
                
            time.sleep(random.uniform(1, 2)) # Polite delay
            if found_emails: break # Found something? Good enough for now.
            
    # Process Emails (Validate & Prioritize)
    valid_emails = [e for e in list(set(found_emails)) if utils.validate_email(e) and utils.is_business_email(e)]
    
    if valid_emails:
        # Prioritize non-info emails (heuristic)
        best_email = valid_emails[0]
        for e in valid_emails:
            if not e.startswith('info') and not e.startswith('contact') and not e.startswith('hello'):
                best_email = e
                break
        info["Email"] = best_email
        print(f"   [+] Found Email: {best_email}")
    else:
        print("   [-] No email found.")
        
    return info

def run_discovery(queries):
    """
    Main entry for discovery.
    """
    all_leads = []
    for q in queries:
        urls = google_search_leads(q, num_results=5) 
        for url in urls:
            if "linkedin.com" in url or "twitter.com" in url or "facebook.com" in url:
                continue
                
            lead_data = scrape_deep(url) # Use Deep Scraper
            if lead_data["Email"]: 
                all_leads.append(lead_data)
            else:
                print(f"[SKIP] No email found for {url}")
                
    return all_leads
