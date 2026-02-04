import sys
import os

# Add root to path
sys.path.append(os.getcwd())

from agents.language_manager import LanguageManager
from agents.chatbot_engine import ChatbotEngine

def test_language_manager():
    print("\n--- Testing Language Manager ---")
    lm = LanguageManager()
    
    # Test English (Default)
    en_title = lm.get_text("market_overview", "en")
    print(f"EN: {en_title}")
    
    # Test Hindi
    hi_title = lm.get_text("market_overview", "hi")
    print(f"HI: {hi_title}")
    
    # Test Odia
    or_title = lm.get_text("market_overview", "or")
    print(f"OR: {or_title}")
    
    if hi_title != en_title and or_title != en_title:
        print("✅ Translation lookup successful.")
    else:
        print("❌ Translation lookup failed.")

def test_chatbot_engine():
    print("\n--- Testing Chatbot Engine ---")
    # Mock DB Manager for now as extracting price is simulated
    chat = ChatbotEngine(None)
    
    # Test 1: Price Query
    q1 = "What is the price of Onion in Cuttack?"
    res1 = chat.process_query(q1)
    print(f"Q: {q1}\nA: {res1}\n")
    
    # Test 2: Invalid Query
    q2 = "Hello"
    res2 = chat.process_query(q2)
    print(f"Q: {q2}\nA: {res2}\n")
    
    if "Onion" in res1 and "Cuttack" in res1:
        print("✅ Chatbot logic successful.")
    else:
        print("❌ Chatbot logic failed.")

if __name__ == "__main__":
    test_language_manager()
    test_chatbot_engine()
