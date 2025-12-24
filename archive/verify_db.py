import sys
import os
sys.path.append(os.getcwd())

from src import data_manager, campaign_manager
from src.data_manager import Lead, get_db

def test_system():
    # 1. Init DB
    print("[*] Initializing DB...")
    data_manager.initialize_db()
    
    # 2. Create Campaign
    print("[*] Creating Test Campaign...")
    steps = [
        {'day': 0, 'subject': 'Hello {{first_name}}', 'body': 'Intro body'},
        {'day': 2, 'subject': 'Followup', 'body': 'Just checking in'}
    ]
    campaign = campaign_manager.create_campaign("Test Campaign 1", steps)
    
    if not campaign:
        # Might fail if exists, try to get it
        print("[!] Campaign might already exist with this name (Unique Constraint).")
    else:
        print(f"[+] Created Campaign: {campaign.name}")

    # 3. Add Lead
    print("[*] Adding Test Lead...")
    data_manager.add_lead({
        "Email": "test_lead@example.com",
        "Name": "Test User",
        "Company": "Test Co",
        "Personalization_Line": "Nice website."
    })
    
    # 4. Enroll Lead (Assuming ID 1 is the test campaign, or recent one)
    # We need to find the campaign ID properly
    db = next(get_db())
    camp = db.query(data_manager.Campaign).first()
    db.close()
    
    if camp:
        print(f"[*] Enrolling into Campaign ID {camp.id}...")
        count = campaign_manager.enroll_leads(camp.id)
        print(f"[+] Enrolled {count} leads.")
        
    # 5. Check Due
    due = campaign_manager.get_due_leads()
    print(f"[*] Due Leads: {len(due)}")
    for d in due:
        print(f" -> Ready to send Step {d['step_number']} to {d['email']}")

if __name__ == "__main__":
    test_system()
