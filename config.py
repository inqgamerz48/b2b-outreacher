import os
import json
from dotenv import load_dotenv

load_dotenv()

SECRETS_FILE = "secrets.json"

def load_secrets():
    """Loads secrets from the local JSON file if it exists."""
    if os.path.exists(SECRETS_FILE):
        try:
            with open(SECRETS_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] Failed to load secrets.json: {e}")
            return {}
    return {}

def save_secrets(new_secrets):
    """Updates secrets.json with new values."""
    current_secrets = load_secrets()
    current_secrets.update(new_secrets)
    try:
        with open(SECRETS_FILE, "w") as f:
            json.dump(current_secrets, f, indent=4)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save secrets: {e}")
        return False

# Load secrets
_secrets = load_secrets()

# General Config
MAX_EMAILS_PER_DAY = 30
DATA_FILE = os.path.join("data", "leads.xlsx")

# Helper to get config from secrets first, then env
def get_config(key, default=None):
    return _secrets.get(key, os.getenv(key, default))

# AI Config
AI_PROVIDER = get_config("AI_PROVIDER", "openai") # openai, anthropic, google, custom
AI_API_KEY = get_config("AI_API_KEY") 
# Backward compatibility lookup
if not AI_API_KEY:
    AI_API_KEY = get_config("OPENAI_API_KEY")

AI_MODEL = get_config("AI_MODEL") # e.g. gpt-4, claude-3-opus
AI_BASE_URL = get_config("AI_BASE_URL") # For custom compatible endpoints

# Email Config
SMTP_SERVER = get_config("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(get_config("SMTP_PORT", 587))
SMTP_USER = get_config("SMTP_USER")
SMTP_PASSWORD = get_config("SMTP_PASSWORD")
SENDER_NAME = get_config("SENDER_NAME", "B2B Outreach System")

# Scraping Config
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
