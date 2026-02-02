import time
import streamlit as st

class NotificationService:
    """
    AGENT 7 — NOTIFICATION SERVICE
    Role: Alert Manager
    Goal: Send proactive alerts (Email/WhatsApp) on critical events.
    """
    def __init__(self):
        self.channels = ["Email", "WhatsApp"]
        
    def send_alert(self, title, message, channel="Email"):
        """
        Simulate sending an alert. 
        In a real app, this would call SMTP or Twilio API.
        """
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        alert_log = f"[{timestamp}] [{channel.upper()}] {title}: {message}"
        
        # In Streamlit, we simulate this with a Toast or Sidebar log
        if "alerts" not in st.session_state:
            st.session_state["alerts"] = []
            
        st.session_state["alerts"].insert(0, alert_log)
        
        # Show Toast
        st.toast(f"🔔 {title}\n{message}", icon="⚠️")
        
        return True

    def check_triggers(self, shock_info, risk_info, commodity, mandi):
        """
        Check if any alerts need to be fired based on current state.
        """
        # Trigger 1: Shock Detected
        if shock_info.get('is_shock'):
            msg = f"Shock detected for {commodity} in {mandi}. Severity: {shock_info['severity']}. Check dashboard."
            self.send_alert("SHOCK ALERT", msg)
            
        # Trigger 2: High Risk
        if risk_info.get('risk_level') == 'High':
            # Avoid spamming: Check if we alerted recently (omitted for simple demo)
            # self.send_alert("HIGH RISK WARNING", f"{commodity} market is in Crisis regime.", "WhatsApp")
            pass
            
        return True
