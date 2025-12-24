# src/utils.py
import re
from urllib.parse import urlparse

def clean_url(url):
    """Ensures URL has http/https schema."""
    if not url:
        return ""
    if not url.startswith("http"):
        return "https://" + url
    return url

def extract_domain(url):
    """Extracts domain from URL (not perfect, but good for filtering)."""
    try:
        domain = urlparse(url).netloc
        return domain.replace("www.", "")
    except:
        return ""

def is_business_email(email):
    """
    Basic check to see if email is likely a business email.
    Filters out common public providers.
    """
    if not email:
        return False
        
    public_domains = [
        "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com", 
        "icloud.com", "protonmail.com"
    ]
    
    domain = email.split("@")[-1].lower()
    if domain in public_domains:
        return False
    return True

def validate_email(email):
    """Regex validation for email format."""
    email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    return bool(re.match(email_regex, email))
