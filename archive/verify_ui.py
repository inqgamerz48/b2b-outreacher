import requests
import subprocess
import time
import sys
import os

def verify_ui():
    print("[*] Starting UI Server...")
    # Start server in background
    proc = subprocess.Popen([sys.executable, "server.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    try:
        # Wait for startup
        time.sleep(5)
        
        print("[*] Checking Dashboard URL...")
        try:
            resp = requests.get("http://127.0.0.1:8000/")
            print(f"Status Code: {resp.status_code}")
            
            if resp.status_code == 200 and "Outreach Pro" in resp.text:
                print("[SUCCESS] Dashboard loaded successfully!")
                print("Title found: Outreach Pro")
            else:
                print(f"[FAIL] Dashboard content mismatch. Content snippet: {resp.text[:100]}")
                
        except Exception as e:
            print(f"[FAIL] Connection Error: {e}")
            
    finally:
        print("[*] Stopping Server...")
        proc.terminate()
        # Print stderr for debugging if needed
        _, stderr = proc.communicate()
        if stderr:
            print(f"Server Error Log:\n{stderr.decode()}")

if __name__ == "__main__":
    verify_ui()
