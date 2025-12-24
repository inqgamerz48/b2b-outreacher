import pytest
import sys
import os

def run_checks():
    print("========================================")
    print("   [+] B2B OUTREACH - SYSTEM CHECK")
    print("========================================")
    print("Running automated diagnostics...")
    print("")
    
    # Run Pytest programmatically
    # -x: stop on first failure
    # -v: verbose
    # -s: show print output
    exit_code = pytest.main(["-x", "-v", "-s", "tests/test_system.py"])
    
    print("\n========================================")
    if exit_code == 0:
        print("   [+] ALL SYSTEMS OPERATIONAL")
        print("   Ready for Deployment.")
    else:
        print("   [-] SYSTEM CHECKS FAILED")
        print("   Please review the errors above.")
    print("========================================")

if __name__ == "__main__":
    run_checks()
