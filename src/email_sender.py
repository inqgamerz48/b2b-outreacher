# src/email_sender.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
import os
import time
from jinja2 import Template

# Add parent to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from src import campaign_manager, account_manager

def render_template(template_str, lead_context):
    """Renders the email template with lead data."""
    try:
        t = Template(template_str)
        return t.render(**lead_context)
    except Exception as e:
        print(f"[ERROR] Template Render Failed: {e}")
        return template_str

def send_email_task(task_data):
    """
    Sends a cold email based on campaign task data.
    Uses Inbox Rotation to pick an account.
    """
    recipient_email = task_data["email"]
    
    # 1. Get Sending Account
    account = account_manager.get_next_available_account()
    if not account:
        print("[LIMIT] No active accounts with quota remaining.")
        return False

    # Prepare Context
    first_name = task_data["name"].split(" ")[0] if task_data.get("name") else "there"
    context = {
        "name": task_data["name"],
        "first_name": first_name,
        "company": task_data["company"],
        "personalization": task_data["personalization"] or "Hope you're doing well.",
        "sender_name": "Agencies" # Generic name or pull from account?
    }
    
    subject = render_template(task_data["subject"], context)
    body = render_template(task_data["body_template"], context)

    msg = MIMEMultipart()
    msg['From'] = f"{config.SENDER_NAME} <{account.email}>"
    msg['To'] = recipient_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(account.smtp_server, account.smtp_port)
        server.starttls()
        server.login(account.username, account.password)
        text = msg.as_string()
        server.sendmail(account.email, recipient_email, text)
        server.quit()
        
        print(f"[SUCCESS] Sent Step {task_data['step_number']} to {recipient_email} via {account.email}")
        
        # Update DB State
        campaign_manager.advance_lead(task_data["lead_obj"].id)
        account_manager.increment_usage(account.id)
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to send to {recipient_email} via {account.email}: {e}")
        # Automatically mark error or just retry? For now, log.
        # account_manager.mark_error(account.id) 
        return False

def process_email_queue():
    """Reads due leads from Campaign Manager and sends."""
    
    # Sync config account just in case it's fresh
    account_manager.sync_config_account()
    
    due_tasks = campaign_manager.get_due_leads()
    
    if not due_tasks:
        print("[INFO] No emails due for sending.")
        return

    print(f"[INFO] Found {len(due_tasks)} emails due. Starting batch...")
    
    count = 0
    for task in due_tasks:
        # Check global limit or just rely on account limits? 
        # Rely on account limits (get_next_available_account will return None)
        
        if send_email_task(task):
            count += 1
            time.sleep(5) # Safety delay
        else:
            # If failed (likely no accounts), stop batch
             if not account_manager.get_next_available_account():
                 print("[STOP] No accounts available.")
                 break
            
    print(f"[DONE] Processed {count} emails.")
