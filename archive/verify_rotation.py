from src import data_manager, account_manager, email_sender
from src.data_manager import SMTPAccount, Lead, Campaign, CampaignStep, get_db

def test_rotation():
    print("[*] Initializing DB...")
    data_manager.initialize_db()
    
    # 1. Clear existing accounts for test
    db = next(get_db())
    db.query(SMTPAccount).delete()
    db.commit()
    
    # 2. Add Test Accounts
    # Note: These won't work for real sending unless real creds, 
    # but we can test the LOGIC of "get_next_available_account"
    print("[*] Adding test accounts...")
    account_manager.add_account("sender1@test.com", "smtp.test.com", 587, "user1", "pass1", daily_limit=1)
    account_manager.add_account("sender2@test.com", "smtp.test.com", 587, "user2", "pass2", daily_limit=1)
    
    # 3. Test Rotation Logic
    print("[*] Testing Selection Logic...")
    
    # Round 1
    acc1 = account_manager.get_next_available_account()
    print(f"[-] Selected 1: {acc1.email} (Sent: {acc1.sent_today})")
    
    # Simulate send
    account_manager.increment_usage(acc1.id)
    
    # Round 2 (Should get the other one because first used recently or has hit limit)
    acc2 = account_manager.get_next_available_account()
    print(f"[-] Selected 2: {acc2.email} (Sent: {acc2.sent_today})")
    account_manager.increment_usage(acc2.id)
    
    # Round 3 (Both hit limit 1)
    acc3 = account_manager.get_next_available_account()
    if not acc3:
        print("[+] Correctly stopped: Both accounts hit limit.")
    else:
        print(f"[!] Warning: Still selected {acc3.email}")

if __name__ == "__main__":
    test_rotation()
