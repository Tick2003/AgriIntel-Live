import sys
import os
sys.path.append(os.getcwd())
from agents.voice_intelligence import VoiceIntelligenceAgent
import json

def test_voice_flow():
    agent = VoiceIntelligenceAgent()
    
    print("--- Starting Voice Session Test ---")
    phone = "9820012345"
    sid, greeting, lang = agent.handle_call_start(phone)
    print(f"Call Start: {phone} -> Session: {sid}")
    print(f"Detected Lang: {lang}")
    print(f"AI: {greeting}")

    # Turn 1: Price Query
    print("\nTurn 1: 'What is the price of Onion in Nasik?'")
    resp, _ = agent.handle_interaction(sid, text_input="What is the price of Onion in Nasik?")
    print(f"AI: {resp}")

    # Turn 2: Contextual Query (Follow-up)
    print("\nTurn 2: 'What about next week?' (Contextual)")
    resp, _ = agent.handle_interaction(sid, text_input="What about next week?")
    print(f"AI: {resp}")

    # Turn 3: Different Intent
    print("\nTurn 3: 'Is it risky to sell now?'")
    resp, _ = agent.handle_interaction(sid, text_input="Is it risky to sell now?")
    print(f"AI: {resp}")

    print("\n--- Session Context Check ---")
    from agents.session_manager import VoiceSessionManager
    sm = VoiceSessionManager()
    ctx = sm.get_session(sid)
    print(f"Final Session Context: {json.dumps(ctx, indent=2)}")

if __name__ == "__main__":
    test_voice_flow()
