
import sys
import os
import sqlite3

# Setup path
sys.path.append(os.getcwd())
import database.db_manager as db_manager

def test_saas():
    print("--- Initializing DB (Idempotent) ---")
    db_manager.init_db()
    
    conn = sqlite3.connect("agri_intel.db")
    c = conn.cursor()
    
    # Check Org
    print("\n--- Checking Organizations ---")
    c.execute("SELECT * FROM organizations")
    orgs = c.fetchall()
    for o in orgs:
        print(o)
        
    # Check Users
    print("\n--- Checking Users ---")
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    for u in users:
        print(u)
        
    conn.close()
    
    # Test Auth Logic
    print("\n--- Testing Auth Retrieval ---")
    user = db_manager.get_user_by_email("admin@agriintel.in")
    if user:
        print("✅ User found:", user)
        if user['role'] == 'Admin':
            print("✅ Role is Admin")
        else:
            print("❌ Role Mismatch")
            
        org = db_manager.get_org_details(user['org_id'])
        print("✅ Org Details:", org)
    else:
        print("❌ Admin user not found.")

if __name__ == "__main__":
    test_saas()
