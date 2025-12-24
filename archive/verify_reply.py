from src import reply_monitor, data_manager, ai_engine
from src.data_manager import Lead, get_db

def test_reply_logic():
    print("[*] Initializing DB...")
    data_manager.initialize_db()
    
    # 1. Setup Mock Lead
    db = next(get_db())
    lead = db.query(Lead).filter_by(email="reply_test@example.com").first()
    if not lead:
        lead = Lead(email="reply_test@example.com", name="Reply Guy", campaign_id=999, status="Contacted")
        db.add(lead)
        db.commit()
    else:
        # Reset state
        lead.status = "Contacted"
        lead.campaign_id = 999
        lead.reply_intent = None
        db.commit()
    
    lead_id = lead.id
    db.close()
    
    print(f"[*] Lead {lead.email} is currently in Campaign {lead.campaign_id} with Status '{lead.status}'")
    
    # 2. Simulate AI Analysis
    print("[*] Simulating AI Analysis on 'Interested' reply...")
    fake_body = "Hi, this sounds interesting. Let's chat next Tuesday."
    
    # We bypass the actual IMAP connection and just test the logic pipeline
    # We manually call update_lead_reply with a mocked analysis result
    
    # (Optional: actually call AI if API key present, otherwise mock)
    analysis = {
        "intent": "Interested",
        "sentiment": "Positive",
        "summary": "Lead wants to chat next Tuesday."
    }
    
    reply_monitor.update_lead_reply(lead_id, analysis)
    
    # 3. Verify Database State
    db = next(get_db())
    updated_lead = db.query(Lead).filter_by(id=lead_id).first()
    
    print("-" * 30)
    print(f"New Status: {updated_lead.status}")
    print(f"Campaign ID: {updated_lead.campaign_id} (Should be None)")
    print(f"Intent: {updated_lead.reply_intent}")
    print(f"Sentiment: {updated_lead.reply_sentiment}")
    print("-" * 30)
    
    if updated_lead.status == "Replied" and updated_lead.campaign_id is None:
        print("[SUCCESS] Reply logic verified: Sequence stopped.")
    else:
        print("[FAIL] Sequence did not stop correctly.")
    db.close()

if __name__ == "__main__":
    test_reply_logic()
