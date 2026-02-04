import sys
import os

# Add root to path
sys.path.append(os.getcwd())

from agents.business_engine import B2BMatcher, FintechEngine

def test_business_logic():
    print("\n--- Testing Business Engine ---")
    
    # 1. Test B2B Matcher
    print("Testing B2B Matching...")
    b2b = B2BMatcher()
    matches = b2b.find_buyers("Onion", 10, "Cuttack")
    
    print(f"Found {len(matches)} matches.")
    if len(matches) > 0:
        top = matches[0]
        print(f"Top Match: {top['buyer_name']} ({top['match_score']}%)")
        print("✅ Matching logic works.")
    else:
        print("❌ No matches found.")
        
    # 2. Test Fintech Engine
    print("\nTesting Fintech Engine...")
    fintech = FintechEngine()
    
    # Case A: Good Farmer
    yields = [4.5, 4.6, 4.5, 4.7]
    rel = 0.9
    offer = fintech.calculate_credit_score(yields, rel)
    print(f"Good Farmer Score: {offer['credit_score']} (Max Loan: {offer['max_loan']})")
    
    if offer['credit_score'] > 700:
        print("✅ Credit scoring logic (Good Case) correct.")
    else:
        print("❌ Credit scoring logic (Good Case) failed.")

if __name__ == "__main__":
    test_business_logic()
