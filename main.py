# main.py
import argparse
import sys
from src import scraper, data_manager, ai_engine, email_sender

def cmd_scrape(args):
    """Run the scraping process."""
    queries = [
        "indie hacker founder",
        "startup studio founder",
        "automation agency owner",
        "micro SaaS founder",
        "AI agency founder"
    ]
    
    print("[*] Starting Scraping Phase...")
    leads = scraper.run_discovery(queries)
    
    if not leads:
        print("[!] No leads found.")
        return

    print(f"[*] Found {len(leads)} potential leads. Saving to DB...")
    count = 0
    for lead in leads:
        if data_manager.add_lead(lead):
            count += 1
    print(f"[*] Successfully added {count} new leads.")

def cmd_enrich(args):
    """Run AI personalization on existing leads."""
    print("[*] Starting AI Enrichment...")
    df = data_manager.load_data()
    
    # Filter rows where Personalization_Line is empty but we have data
    mask = (df["Personalization_Line"].isna() | (df["Personalization_Line"] == "")) & \
           (df["Email_Sent"] == "No")
    
    pending_leads = df[mask]
    
    if pending_leads.empty:
        print("[!] No leads need enrichment.")
        return

    print(f"[*] Enriching {len(pending_leads)} leads...")
    
    for index, row in pending_leads.iterrows():
        lead_dict = row.to_dict()
        line = ai_engine.generate_personalization(lead_dict)
        print(f" -> Generated for {lead_dict.get('Company')}: {line}")
        
        # Update DataFrame immediately (safe) or batch it
        df.at[index, "Personalization_Line"] = line
        
    data_manager.save_data(df)
    print("[*] Enrichment complete.")

def cmd_send(args):
    """Run the email sender."""
    print("[*] Starting Email Sending Phase...")
    email_sender.process_email_queue()

def main():
    parser = argparse.ArgumentParser(description="B2B Cold Outreach Automation")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Scrape Command
    parser_scrape = subparsers.add_parser("scrape", help="Search and scrape leads")
    
    # Enrich Command
    parser_enrich = subparsers.add_parser("enrich", help="Generate AI personalization")
    
    # Send Command
    parser_send = subparsers.add_parser("send", help="Send emails to queue")
    
    args = parser.parse_args()
    
    if args.command == "scrape":
        cmd_scrape(args)
    elif args.command == "enrich":
        cmd_enrich(args)
    elif args.command == "send":
        cmd_send(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
