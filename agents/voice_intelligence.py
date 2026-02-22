import speech_recognition as sr
from gtts import gTTS
import os
import json
import requests
from agents.chatbot_engine import ChatbotEngine
from agents.session_manager import VoiceSessionManager
from utils.telecom_mapper import TelecomMapper
import database.db_manager as db_manager
from datetime import datetime

class VoiceIntelligenceAgent:
    """
    Orchestrates the voice interaction flow:
    Voice -> STT -> Intent -> API calls -> Response -> TTS -> Voice
    """
    def __init__(self, api_base_url="http://localhost:8000"):
        self.chatbot = ChatbotEngine(db_manager)
        self.sessions = VoiceSessionManager()
        self.telecom = TelecomMapper()
        self.api_base_url = api_base_url
        self.api_key = "agriintel-secret-key-123"

    def handle_call_start(self, phone_number):
        """Initializes call, detects region/lang, and returns welcome message."""
        region, lang_code = self.telecom.detect_region_and_language(phone_number)
        session_id, context = self.sessions.start_session(phone_number, lang_code, region)
        
        # Initial greeting logic
        greeting = self._get_greeting(lang_code, region)
        
        return session_id, greeting, lang_code

    def handle_interaction(self, session_id, audio_data=None, text_input=None):
        """Processes a single turn in the conversation."""
        context = self.sessions.get_session(session_id)
        if not context:
            return "Session expired", "en"

        lang_code = context.get('language', 'en')
        
        # 1. Speech to Text
        query_text = text_input
        if audio_data:
            query_text = self._stt(audio_data, lang_code)
        
        if not query_text:
            return "I couldn't hear you clearly. Could you repeat?", lang_code

        # 2. Intent & Entity Extraction (using enhanced chatbot engine)
        result = self.chatbot.process_query_structured(query_text, context)
        response_text = result['response_text']
        
        # 3. Update context with new entities
        self.sessions.update_context(
            session_id, 
            crop=result['entities']['commodity'], 
            mandi=result['entities']['mandi']
        )
        
        # 4. Save Transcript & Log to DB
        self._log_interaction(session_id, context, query_text, result)
        
        return response_text, lang_code

    def _stt(self, audio, lang):
        """Mock/Wrapper for Speech Recognition."""
        return "stubbed text"

    def _get_greeting(self, lang, region):
        greetings = {
            "en": "Welcome to AgriIntel. How can I help you today?",
            "hi": "AgriIntel में आपका स्वागत है। मैं आपकी क्या मदद कर सकता हूँ?",
            "mr": "AgriIntel मध्ये आपले स्वागत आहे. मी तुम्हाला कशी मदत करू शकतो?",
            "or": "AgriIntel କୁ ସ୍ୱାଗତ । ମୁଁ ଆପଣଙ୍କୁ କିପରି ସାହାଯ୍ୟ କରିପାରିବି?"
        }
        return greetings.get(lang, greetings["en"])

    def _log_interaction(self, session_id, context, query, result):
        """Logs the interaction to the voice_call_logs table."""
        conn = db_manager.sqlite3.connect(db_manager.DB_NAME)
        c = conn.cursor()
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute('''
                INSERT INTO voice_call_logs (
                    call_sid, phone_number, timestamp, language, region, 
                    transcript, intent, entities, response_text, confidence_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id, context.get('phone_number'), timestamp, context.get('language'), context.get('region'),
                query, result['intent'], json.dumps(result['entities']), result['response_text'], 0.95
            ))
            conn.commit()
        except Exception as e:
            print(f"Logging error: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    agent = VoiceIntelligenceAgent()
    sid, greeting, lang = agent.handle_call_start("9820012345")
    print(f"[{lang}] {greeting}")
    resp, l = agent.handle_interaction(sid, text_input="Price of Onion in Nasik")
    print(f"[{l}] {resp}")
