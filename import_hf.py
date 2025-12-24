import sys
import os
import requests
import json
from src.data_manager import KnowledgeBase, get_db

# Datasets to pull from
DATASETS = [
    {
        "name": "marketeam/Marketing-Emails",
        "config": "default",
        "split": "train",
        "category": "Marketing Example"
    },
    {
        "name": "knkarthick/dialogsum", 
        "config": "default",
        "split": "train",
        "category": "Sales Dialogue"
    }
]

TARGET_TOTAL = 1000

def import_hf_data():
    print(f"[*] Starting GIGA-SCALE AI Training (Target: {TARGET_TOTAL} Examples)...")
    db = next(get_db())
    total_imported = 0
    
    # Calculate target per dataset
    target_per_ds = int(TARGET_TOTAL / len(DATASETS)) + 50 

    for ds in DATASETS:
        dataset_name = ds['name']
        print(f"\n[*] Processing Dataset: {dataset_name}...")
        
        imported_this_ds = 0
        offset = 0
        batch_size = 100
        
        while imported_this_ds < target_per_ds:
            api_url = f"https://datasets-server.huggingface.co/rows?dataset={dataset_name}&config={ds['config']}&split={ds['split']}&offset={offset}&length={batch_size}"
            
            try:
                response = requests.get(api_url)
                if response.status_code != 200:
                    print(f"   [WARN] Batch failed / End of stream (Status: {response.status_code})")
                    break

                data = response.json()
                rows = data.get("rows", [])
                
                if not rows:
                    print("   [*] No more rows found.")
                    break
                
                print(f"   [BATCH] Offset {offset}: Found {len(rows)} rows...")
                
                added_count = 0
                for row in rows:
                    item = row["row"]
                    
                    # Extract text flexibly
                    content = ""
                    if "subject" in item and "body" in item:
                        content = f"Subject: {item['subject']}\n\n{item['body']}"
                    elif "text" in item:
                        content = item["text"]
                    elif "dialogue" in item: # For dialogsum
                        content = item["dialogue"]
                    elif "email_body" in item:
                        content = item["email_body"]
                    else:
                        content = "\n".join([str(v) for k,v in item.items() if isinstance(v, str) and len(v) > 50])
                    
                    if not content or len(content) < 20: continue

                    # Deduplicate check (skip expensive query if possible, but safer to check)
                    # For speed on bulk, maybe we skip check or do it in memory? 
                    # Let's trust DB unique constraint or just check. Check is fine for 1000.
                    exists = db.query(KnowledgeBase).filter(KnowledgeBase.content == content).first()
                    if not exists:
                        kb = KnowledgeBase(
                            user_id=None, # System/Global Data
                            is_global=True,
                            category=ds['category'], 
                            content=content[:3000] 
                        )
                        db.add(kb)
                        added_count += 1
                        total_imported += 1
                        imported_this_ds += 1
                
                db.commit() # Commit after each batch
                print(f"      -> Added {added_count} new examples.")
                
                offset += batch_size
                
            except Exception as e:
                print(f"   [ERROR] Batch processing error: {e}")
                break

    db.close()
    print("-" * 40)
    print(f"[SUMMARY] Successfully TRAINED on {total_imported} NEW examples.")
    print(f"[*] Total Knowledge Base size is now massive.")

if __name__ == "__main__":
    import_hf_data()
