# src/email_sender.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
import os
import time

# Add parent to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from src import data_manager

def send_email(lead):
    """
    Sends a cold email to the lead.
    """
    recipient_email = lead["Email"]
    first_name = lead["Name"].split(" ")[0] if lead.get("Name") else "there"
    personalization = lead.get("Personalization_Line", "")
    
    subject = f"Question about {lead.get('Company', 'your business')}"
    
    body = f"""Hi {first_name},

{personalization}

I'm building a tool that helps agencies automate their backend workflows, and I thought it might be useful for what you're doing.

Any interest in a 15-min chat next week to see if we can save you time?

Best,
{config.SENDER_NAME}

P.S. Let me know if this isn’t relevant and I won’t follow up.
"""

    msg = MIMEMultipart()
    msg['From'] = f"{config.SENDER_NAME} <{config.SMTP_USER}>"
    msg['To'] = recipient_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        # Check credentials
        if not config.SMTP_USER or not config.SMTP_PASSWORD:
            print("[ERROR] SMTP Credentials missing in config.py / .env")
            return False
            
        server = smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT)
        server.starttls()
        server.login(config.SMTP_USER, config.SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(config.SMTP_USER, recipient_email, text)
        server.quit()
        
        print(f"[SUCCESS] Email sent to {recipient_email}")
        data_manager.mark_sent(recipient_email)
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to send to {recipient_email}: {e}")
        return False

def process_email_queue():
    """Reads unsent leads and sends emails up to the daily limit."""
    leads = data_manager.get_unsent_leads(limit=config.MAX_EMAILS_PER_DAY)
    
    if not leads:
        print("[INFO] No unsent leads found.")
        return

    print(f"[INFO] Found {len(leads)} unsent leads. Starting batch...")
    
    count = 0
    for lead in leads:
        if not lead.get("Email"):
            continue
            
        success = send_email(lead)
        if success:
            count += 1
            # Wait between emails to look human/avoid spam filters
            time.sleep(5) 
            
    print(f"[DONE] Sent {count} emails.")
