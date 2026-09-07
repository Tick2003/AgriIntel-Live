"""
AgriIntel Voice Intelligence Agent (v2.0 — Hardened)
=====================================================
Orchestrates voice interaction flow with graceful dependency handling.
"""

import json
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

# Graceful imports for optional dependencies
try:
    import speech_recognition as sr
    STT_AVAILABLE = True
except ImportError:
    STT_AVAILABLE = False
    logger.info("speech_recognition not installed — STT disabled")

try:
    from gtts import gTTS
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    logger.info("gTTS not installed — TTS disabled")

import database.db_manager as db_manager
from agents.chatbot_engine import ChatbotEngine
from agents.session_manager import VoiceSessionManager
from utils.telecom_mapper import TelecomMapper

# Load config safely
try:
    from config import settings
    DEFAULT_API_BASE_URL = settings.app.api_base_url
    DEFAULT_API_KEY = settings.security.api_key
except ImportError:
    DEFAULT_API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
    DEFAULT_API_KEY = os.environ.get("AGRIINTEL_API_KEY", "")


class VoiceIntelligenceAgent:
    """
    Orchestrates the voice interaction flow:
    Voice -> STT -> Intent -> API calls -> Response -> TTS -> Voice
    """
    def __init__(self, api_base_url=None):
        self.chatbot = ChatbotEngine(db_manager)
        self.sessions = VoiceSessionManager()
        self.telecom = TelecomMapper()
        self.api_base_url = api_base_url or DEFAULT_API_BASE_URL
        self.api_key = DEFAULT_API_KEY

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
        if audio_data and STT_AVAILABLE:
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
        """Speech Recognition wrapper."""
        if not STT_AVAILABLE:
            return None
        try:
            recognizer = sr.Recognizer()
            # Process audio data
            text = recognizer.recognize_google(audio, language=lang)
            return text
        except Exception as e:
            logger.error(f"STT failed: {e}")
            return None

    def _get_greeting(self, lang, region):
        greetings = {
            "en": "Welcome to AgriIntel.in. How can I help you today?",
            "hi": "AgriIntel.in में आपका स्वागत है। मैं आपकी क्या मदद कर सकता हूँ?",
            "mr": "AgriIntel.in मध्ये आपले स्वागत आहे. मी तुम्हाला कशी मदत करू शकतो?",
            "or": "AgriIntel.in କୁ ସ୍ୱାଗତ । ମୁଁ ଆପଣଙ୍କୁ କିପରି ସାହାଯ୍ୟ କରିପାରିବି?"
        }
        return greetings.get(lang, greetings["en"])

    def _log_interaction(self, session_id, context, query, result):
        """Logs the interaction to the voice_call_logs table."""
        try:
            import sqlite3
            conn = sqlite3.connect(db_manager.DB_NAME)
            c = conn.cursor()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute('''
                INSERT INTO voice_call_logs (
                    call_sid, phone_number, timestamp, language, region,
                    transcript, intent, entities, response_text, confidence_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id, context.get('phone_number'), timestamp, context.get('language'), context.get('region'),
                query, result.get('intent', ''), json.dumps(result.get('entities', {})), result.get('response_text', ''), 0.95
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Voice interaction logging error: {e}")

if __name__ == "__main__":
    agent = VoiceIntelligenceAgent()
    sid, greeting, lang = agent.handle_call_start("9820012345")
    print(f"[{lang}] {greeting}")
    resp, l = agent.handle_interaction(sid, text_input="Price of Onion in Nasik")
    print(f"[{l}] {resp}")
