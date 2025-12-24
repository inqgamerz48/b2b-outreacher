# src/data_manager.py
import pandas as pd
import os
import sys
import config
from datetime import datetime

# Database Support
try:
    from sqlalchemy import create_engine, text
    import sqlalchemy
except ImportError:
    create_engine = None

EXPECTED_COLUMNS = [
    "Name", "Role", "Company", "Website", "Email", "LinkedIn", 
    "Notes", "Personalization_Line", "Email_Sent", "Replied", "Date_Added"
]

def get_db_engine():
    """Returns a SQLAlchemy engine if DATABASE_URL is set."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return None
        
    if not create_engine:
        return None

    # Fix Render/Heroku postgres:// -> postgresql://
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
    try:
        # SQLite needs 3 slashes for relative path, 4 for absolute
        # If user passes "sqlite:///leads.db", it works out of box
        return create_engine(db_url)
    except Exception as e:
        print(f"[ERROR] DB Connection Failed: {e}")
        return None

def initialize_db():
    """Creates the data storage (File or DB Table)."""
    engine = get_db_engine()
    
    if engine:
        # Cloud/DB Mode
        try:
            # Check if table exists
            with engine.connect() as conn:
                # Basic check, if fails we create
                conn.execute(text("SELECT 1 FROM leads LIMIT 1"))
            print(f"[INFO] Connected to Cloud Database.")
        except Exception:
            # Create table
            print(f"[INFO] Creating 'leads' table in database...")
            # We use an empty dataframe to create the schema easily
            df = pd.DataFrame(columns=EXPECTED_COLUMNS)
            df.to_sql('leads', engine, if_exists='fail', index=False)
    else:
        # Local Excel Mode
        if not os.path.exists(config.DATA_FILE):
            df = pd.DataFrame(columns=EXPECTED_COLUMNS)
            os.makedirs(os.path.dirname(config.DATA_FILE), exist_ok=True)
            df.to_excel(config.DATA_FILE, index=False)
            print(f"[INFO] Created new local database at {config.DATA_FILE}")
        else:
            print(f"[INFO] Local database exists at {config.DATA_FILE}")

def load_data():
    """Loads data from DB or Excel."""
    engine = get_db_engine()
    if engine:
        try:
            return pd.read_sql("SELECT * FROM leads", engine)
        except Exception as e:
            print(f"[ERROR] DB Read Failed: {e}")
            return pd.DataFrame(columns=EXPECTED_COLUMNS)
    else:
        if not os.path.exists(config.DATA_FILE):
            initialize_db()
        return pd.read_excel(config.DATA_FILE)

def save_data(df):
    """Saves data to DB or Excel."""
    engine = get_db_engine()
    if engine:
        # For SQL, replacing the whole table is inefficient but safe for this MVP size.
        # Ideally we would do upserts, but 'replace' ensures compatibility with the dataframe edits.
        df.to_sql('leads', engine, if_exists='replace', index=False)
    else:
        df.to_excel(config.DATA_FILE, index=False)

def add_lead(lead_dict):
    """Adds a new lead if email doesn't exist."""
    df = load_data()
    
    # Deduplication
    if lead_dict.get("Email") and lead_dict["Email"] in df["Email"].values:
        print(f"[SKIP] Lead with email {lead_dict['Email']} already exists.")
        return False
    
    # Fill defaults
    for col in EXPECTED_COLUMNS:
        if col not in lead_dict:
            lead_dict[col] = "" 
            
    lead_dict["Date_Added"] = datetime.now().strftime("%Y-%m-%d")
    lead_dict["Email_Sent"] = "No"
    lead_dict["Replied"] = "No"
    
    new_row = pd.DataFrame([lead_dict])
    df = pd.concat([df, new_row], ignore_index=True)
    save_data(df)
    return True

def get_unsent_leads(limit=config.MAX_EMAILS_PER_DAY):
    df = load_data()
    unsent = df[df["Email_Sent"] == "No"].head(limit)
    return unsent.to_dict('records')

def mark_sent(email):
    # This acts on the DF abstraction, so it works for both
    df = load_data()
    if email in df["Email"].values:
        df.loc[df["Email"] == email, "Email_Sent"] = "Yes"
        save_data(df)
