# src/account_manager.py
from datetime import datetime
from src.data_manager import get_db, SMTPAccount
import config

def add_account(email, smtp_server, smtp_port, username, password, daily_limit=50):
    """Adds a new SMTP account to the pool."""
    db = next(get_db())
    try:
        # Check duplicate
        existing = db.query(SMTPAccount).filter_by(email=email).first()
        if existing:
            return "Account with this email already exists."
            
        account = SMTPAccount(
            email=email,
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            username=username,
            password=password,
            daily_limit=daily_limit,
            status="Active"
        )
        db.add(account)
        db.commit()
        return "Account added successfully."
    except Exception as e:
        return f"Error adding account: {e}"
    finally:
        db.close()

def get_next_available_account():
    """
    Returns the best SMTP account to use (Round Robin + Limit Check).
    """
    db = next(get_db())
    try:
        # 1. Reset counters if new day? (Naive check: if last_used not today)
        # Ideally this is a separate background job, but lazy check works for MVP
        
        # 2. Find Active accounts not over limit
        # Order by last_used_at ASC to rotate (pick the one used longest ago)
        candidate = db.query(SMTPAccount).filter(
            SMTPAccount.status == "Active",
            SMTPAccount.sent_today < SMTPAccount.daily_limit
        ).order_by(SMTPAccount.last_used_at.asc()).first()
        
        if not candidate:
            return None
            
        return candidate
    finally:
        db.close()

def increment_usage(account_id):
    """Updates usage stats for an account."""
    db = next(get_db())
    try:
        account = db.query(SMTPAccount).filter_by(id=account_id).first()
        if account:
            account.sent_today += 1
            account.last_used_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()

def mark_error(account_id):
    """Marks an account as having an error (optional: disable it)."""
    db = next(get_db())
    try:
        account = db.query(SMTPAccount).filter_by(id=account_id).first()
        if account:
            account.status = "Error"
            db.commit()
    finally:
        db.close()

def sync_config_account():
    """
    Ensures the account in config.py/.env exists in DB.
    Call this on startup.
    """
    if config.SMTP_USER and config.SMTP_PASSWORD:
        add_account(
            email=config.EMAIL_FROM or config.SMTP_USER,
            smtp_server=config.SMTP_SERVER,
            smtp_port=config.SMTP_PORT,
            username=config.SMTP_USER,
            password=config.SMTP_PASSWORD,
            daily_limit=config.MAX_EMAILS_PER_DAY
        )
