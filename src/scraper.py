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
            valid_emails.append(email)
    return list(set(valid_emails))

def get_soup(url):
    """Helper to get BeautifulSoup object with safety headers."""
    try:
        headers = {'User-Agent': config.USER_AGENT}
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
