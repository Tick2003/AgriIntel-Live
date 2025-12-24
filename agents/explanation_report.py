class AIExplanationAgent:
    """
    AGENT 5 — EXPLANATION AGENT
    Role: Generates natural language insights.
    Goal: Generate clear, policy-friendly explanations for observed price movements and forecasts.
    """
    def __init__(self):
        pass

    def generate_explanation(self, commodity: str, risk_data: dict, shock_data: dict, forecast_data) -> dict:
        """
        Generates a plain-language explanation.
        Real implementation would construct a prompt and call Gemini API.
        """
        
        # Mock Response
        risk_level = risk_data.get('risk_level', 'Unknown')
        shock_text = "detected" if shock_data.get('is_shock') else "not detected"
        
        explanation = (
            f"### Market Report for {commodity}\n\n"
            f"**Observation**: Market risk is currently assessed as **{risk_level}**. "
            f"Abnormal price movements were **{shock_text}** in the recent period.\n\n"
            f"**Forecast**: Prices are expected to trend {'upwards' if forecast_data['forecast_price'].iloc[-1] > forecast_data['forecast_price'].iloc[0] else 'downwards'} over the next 30 days.\n\n"
            f"**Guidance**: Monitor arrival volumes in major mandis as volatility remains a key factor."
        )
        
        return {
            "explanation": explanation,
            "confidence": "High",
            "next_steps": "Check weather reports for impact on supply."
        }
