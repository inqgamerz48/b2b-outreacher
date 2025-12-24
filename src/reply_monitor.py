# src/reply_monitor.py
import imaplib
import email
from email.header import decode_header
import time
from src import data_manager, account_manager, ai_engine, campaign_manager
from src.data_manager import SMTPAccount, Lead, get_db

def connect_imap(account):
    """Connects to IMAP server."""
    # Guess IMAP server from SMTP (usually smtp.gmail.com -> imap.gmail.com)
    # For MVP we assume Gmail or standard naming
    imap_server = "imap.gmail.com" 
    if "outlook" in account.smtp_server:
        imap_server = "outlook.office365.com"
        
    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(account.username, account.password)
        return mail
    except Exception as e:
        print(f"[ERROR] IMAP Login Failed for {account.email}: {e}")
        return None

def process_inbox(account):
    """Checks inbox for unread replies from leads."""
    mail = connect_imap(account)
    if not mail: return

    try:
        mail.select("inbox")
        # Search for all Unread emails
        status, messages = mail.search(None, 'UNSEEN')
        if status != "OK": return
        
        email_ids = messages[0].split()
        print(f"[INFO] Checking {len(email_ids)} unread emails for {account.email}...")
        
        for e_id in email_ids:
            # Fetch the basic structure
            _, msg_data = mail.fetch(e_id, '(RFC822)')
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    # Decode Subject and Sender
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else "utf-8")
                        
                    from_header = msg.get("From")
                    sender_email = email.utils.parseaddr(from_header)[1]
                    
                    # Check if this sender is a Lead in our DB
                    db = next(get_db())
                    lead = db.query(Lead).filter_by(email=sender_email).first()
                    db.close()
                    
                    if lead:
                        print(f"[REPLY] Detected reply from Lead: {lead.email}")
                        
                        # Extract Body
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    try:
                                        body = part.get_payload(decode=True).decode()
                                    except: pass
                        else:
                            try:
                                body = msg.get_payload(decode=True).decode()
                            except: pass
                            
                        # Analyze with AI
                        analysis = ai_engine.analyze_reply(body[:1000]) # Limit context
                        
                        # Update Lead Logic
                        update_lead_reply(lead.id, analysis)
                        
                        # Mark as seen (already done by fetching generally, but confirm)
                        # mail.store(e_id, '+FLAGS', '\\Seen')
                    else:
                        print(f"[INFO] Ignored email from non-lead: {sender_email}")
                        
        mail.close()
        mail.logout()
    except Exception as e:
        print(f"[ERROR] IMAP Processing Failed: {e}")

def update_lead_reply(lead_id, analysis):
    """Updates lead status and stops sequence."""
    db = next(get_db())
    try:
        lead = db.query(Lead).filter_by(id=lead_id).first()
        if lead:
            lead.status = "Replied"
            lead.reply_intent = analysis.get("intent", "Other")
            lead.reply_sentiment = analysis.get("sentiment", "Neutral")
            lead.reply_summary = analysis.get("summary", "")
            
            # STOP SEQUENCE
            lead.campaign_id = None 
            lead.next_action_at = None
            
            db.commit()
            print(f"[ACTION] Stopped sequence for {lead.email}. Intent: {lead.reply_intent}")
    finally:
        db.close()

def run_reply_monitor():
    """Main loop to check all accounts."""
    db = next(get_db())
    accounts = db.query(SMTPAccount).filter_by(status="Active").all()
    db.close()
    
    for acc in accounts:
        process_inbox(acc)
