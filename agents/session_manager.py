import redis
import json
import uuid

class VoiceSessionManager:
    """
    Manages conversational context across voice interaction turns using Redis.
    """
    def __init__(self, host='localhost', port=6379, db=0, expiry_seconds=3600):
        try:
            self.redis = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            self.redis.ping()
        except Exception:
            # Fallback to local memory if Redis is unavailable (for demo/dev)
            self.redis = None
            self.local_cache = {}
            print("Warning: Redis not connected. Using local memory for sessions.")
            
        self.expiry = expiry_seconds

    def get_session(self, session_id):
        """Retrieves session data associated with session_id."""
        if self.redis:
            data = self.redis.get(f"voice_session:{session_id}")
            return json.loads(data) if data else {}
        else:
            return self.local_cache.get(session_id, {})

    def save_session(self, session_id, data):
        """Saves session data."""
        if self.redis:
            self.redis.setex(f"voice_session:{session_id}", self.expiry, json.dumps(data))
        else:
            self.local_cache[session_id] = data

    def update_context(self, session_id, **kwargs):
        """Updates specific keys in the session context."""
        context = self.get_session(session_id)
        context.update(kwargs)
        self.save_session(session_id, context)
        return context

    def start_session(self, phone_number, initial_lang="en", region="Unknown"):
        """Initializes a new session."""
        session_id = str(uuid.uuid4())
        initial_data = {
            "phone_number": phone_number,
            "language": initial_lang,
            "region": region,
            "crop": None,
            "mandi": None,
            "history": []
        }
        self.save_session(session_id, initial_data)
        return session_id, initial_data

if __name__ == "__main__":
    # Test
    mgr = VoiceSessionManager()
    sid, data = mgr.start_session("9820012345", "hi", "Maharashtra")
    print(f"Started session: {sid}")
    mgr.update_context(sid, crop="Onion")
    print(mgr.get_session(sid))
