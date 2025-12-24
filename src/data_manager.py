# src/data_manager.py
import os
import sys
import config
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.sql import func

# Add parent path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

Base = declarative_base()

# --- Models ---
class Campaign(Base):
    __tablename__ = 'campaigns'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String, nullable=False)
    status = Column(String, default="Active") # Active, Paused, Completed
    created_at = Column(DateTime, default=datetime.utcnow)
    
    steps = relationship("CampaignStep", back_populates="campaign", cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="campaign")

class CampaignStep(Base):
    __tablename__ = 'campaign_steps'
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey('campaigns.id'))
    step_number = Column(Integer) # 1, 2, 3...
    day_delay = Column(Integer, default=0) # Days to wait after previous step
    template_subject = Column(String)
    template_body = Column(Text)
    
    campaign = relationship("Campaign", back_populates="steps")

class Lead(Base):
    __tablename__ = 'leads'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    email = Column(String, nullable=False) # Removed unique=True constraint globally, unique per user ideally but for simplicity keep it loose
    name = Column(String)
    company = Column(String)
    role = Column(String)
    website = Column(String)
    linkedin = Column(String)
    notes = Column(Text)
    personalization_line = Column(Text)
    
    # Status Tracking
    status = Column(String, default="New") # New, Contacted, Replied, Bounced, Completed
    email_sent = Column(String, default="No") # Legacy support
    replied = Column(String, default="No") # Legacy support
    
    # Reply Analysis
    reply_intent = Column(String, nullable=True) # Interested, Not Interested, OOO
    reply_sentiment = Column(String, nullable=True) # Positive, Negative, Neutral
    reply_summary = Column(Text, nullable=True)
    
    # Sequence Tracking
    campaign_id = Column(Integer, ForeignKey('campaigns.id'), nullable=True)
    current_step = Column(Integer, default=0) # 0 = Not started
    next_action_at = Column(DateTime, nullable=True) # When to send next email
    last_contacted_at = Column(DateTime, nullable=True)
    date_added = Column(DateTime, default=datetime.utcnow)

    campaign = relationship("Campaign", back_populates="leads")

class SMTPAccount(Base):
    __tablename__ = 'smtp_accounts'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    email = Column(String, unique=True)
    username = Column(String)
    password = Column(String)
    smtp_server = Column(String)
    smtp_port = Column(Integer)
    daily_limit = Column(Integer, default=50)
    sent_today = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)
    status = Column(String, default="Active") # Active, Error, Paused

class KnowledgeBase(Base):
    __tablename__ = 'knowledge_base'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True) # Null if Global
    is_global = Column(Boolean, default=False)
    category = Column(String, nullable=False) 
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)

# --- Database Setup ---
# Use SQLite by default, compatible with Heroku via DATABASE_URL if needed
DB_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(os.path.dirname(config.DATA_FILE), 'leads.db')}")
if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if "sqlite" in DB_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_knowledge_context():
    """Returns all knowledge base items formatted as a specific context string."""
    db = next(get_db())
    try:
        items = db.query(KnowledgeBase).all()
        if not items: return ""
        
        context = "### Custom Knowledge Base ###\n"
        for item in items:
            context += f"[{item.category}]: {item.content}\n"
        context += "#############################\n"
        return context
    finally:
        db.close()

def initialize_db(db_url=DB_URL):
    """Creates tables and migrates data if needed."""
    print("[INFO] Initializing Database...")
    Base.metadata.create_all(bind=engine)
    
    # Create Default Admin
    db = SessionLocal()
    from src.auth import get_password_hash
    if not db.query(User).filter_by(username="admin").first():
        print("[SECURITY] Creating default admin user...")
        admin = User(username="admin", password_hash=get_password_hash("password123"))
        db.add(admin)
        db.commit()
    db.close()
    
    # Check for legacy Excel file
    if os.path.exists(config.DATA_FILE):
        print("[INFO] Found legacy Excel file. Checking for migration...")
        migrate_excel_to_db()

def migrate_excel_to_db():
    """Migrates leads from old Excel file to new SQLite DB."""
    try:
        df = pd.read_excel(config.DATA_FILE)
        session = SessionLocal()
        
        count = 0
        for _, row in df.iterrows():
            email = row.get("Email")
            if not email or pd.isna(email):
                continue
                
            # Check existence
            exists = session.query(Lead).filter_by(email=email).first()
            if exists:
                continue
                
            lead = Lead(
                email=email,
                name=row.get("Name", ""),
                company=row.get("Company", ""),
                role=row.get("Role", ""),
                website=row.get("Website", ""),
                linkedin=row.get("LinkedIn", ""),
                notes=row.get("Notes", ""),
                personalization_line=row.get("Personalization_Line", ""),
                status="Contacted" if row.get("Email_Sent") == "Yes" else "New",
                email_sent=row.get("Email_Sent", "No"),
                replied=row.get("Replied", "No"),
                date_added=datetime.now() # Approximate
            )
            session.add(lead)
            count += 1
            
        session.commit()
        session.close()
        if count > 0:
            print(f"[SUCCESS] Migrated {count} leads from Excel to Database.")
            # Rename old file to avoid confusion? 
            # os.rename(config.DATA_FILE, config.DATA_FILE + ".bak")
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")

# --- Data Access Layer (Compatibility with old calls) ---

def load_data():
    """Returns all leads as a DataFrame for compatibility."""
    session = SessionLocal()
    query = session.query(Lead)
    df = pd.read_sql(query.statement, session.bind)
    session.close()
    
    # Map snake_case database columns back to Capitalized columns for frontend compat
    column_map = {
        "email": "Email", "name": "Name", "company": "Company", 
        "role": "Role", "website": "Website", "linkedin": "LinkedIn",
        "notes": "Notes", "personalization_line": "Personalization_Line",
        "status": "Status", "email_sent": "Email_Sent", "replied": "Replied",
        "date_added": "Date_Added"
    }
    df = df.rename(columns=column_map)
    return df

def save_data(df):
    """
    In the new DB model, we don't save the whole DF anymore.
    This function is kept to prevent breaking existing code that calls it.
    Ideally, we should update individual records.
    For MVP: We can iterate and update specific fields if needed, 
    but mostly we should rely on add_lead / update_lead.
    """
    pass # No-op for now, as we treat DB as source of truth

def add_lead(lead_dict):
    """Adds a single lead."""
    session = SessionLocal()
    try:
        email = lead_dict.get("Email")
        if session.query(Lead).filter_by(email=email).first():
            return False
            
        new_lead = Lead(
            email=email,
            name=lead_dict.get("Name", ""),
            company=lead_dict.get("Company", ""),
            role=lead_dict.get("Role", ""),
            website=lead_dict.get("Website", ""),
            linkedin=lead_dict.get("LinkedIn", ""),
            personalization_line=lead_dict.get("Personalization_Line", ""),
            # Default to Default Campaign if exists? N/A for now.
        )
        session.add(new_lead)
        session.commit()
        return True
    except Exception as e:
        print(f"[ERROR] Add Lead Failed: {e}")
        return False
    finally:
        session.close()

def get_unsent_leads(limit=50):
    """Gets leads that have not been sent (legacy check)."""
    session = SessionLocal()
    try:
        leads = session.query(Lead).filter(Lead.email_sent == "No").limit(limit).all()
        # Convert to dict list for compatibility
        return [
            {
                "Email": l.email, "Name": l.name, "Company": l.company, 
                "Personalization_Line": l.personalization_line,
                "current_step": l.current_step, "id": l.id
            } 
            for l in leads
        ]
    finally:
        session.close()

def mark_sent(email):
    """Updates lead status to Sent."""
    session = SessionLocal()
    try:
        lead = session.query(Lead).filter_by(email=email).first()
        if lead:
            lead.email_sent = "Yes"
            lead.status = "Contacted"
            lead.last_contacted_at = datetime.now()
            session.commit()
    finally:
        session.close()

def update_personalization(email, line):
    """Updates the AI line for a lead."""
    session = SessionLocal()
    try:
        lead = session.query(Lead).filter_by(email=email).first()
        if lead:
            lead.personalization_line = line
            session.commit()
    finally:
        session.close()
