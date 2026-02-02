import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import pandas as pd

class SentimentAgent:
    """
    AGENT 8 — SENTIMENT ANALYSIS AGENT
    Role: News Interpreter
    Goal: Analyze text sentiment to determine market mood (Bullish/Bearish).
    """
    def __init__(self):
        # robust downloader
        try:
            nltk.data.find('sentiment/vader_lexicon.zip')
        except LookupError:
            nltk.download('vader_lexicon')
            
        self.sia = SentimentIntensityAnalyzer()

    def analyze(self, text):
        """
        Returns sentiment score compound (-1 to 1) and label.
        """
        if not text:
            return {'score': 0, 'label': 'Neutral', 'color': 'gray'}
            
        score = self.sia.polarity_scores(text)['compound']
        
        # Agri-Specific Context: 
        # "High prices" -> Positive for Farmer (Bullish), Negative for Consumer.
        # "Export Ban" -> Negative for Price (Bearish).
        # We assume "Bullish" means Price UP.
        
        if score > 0.05:
            return {'score': score, 'label': 'Bullish (Positive)', 'color': 'green'}
        elif score < -0.05:
            return {'score': score, 'label': 'Bearish (Negative)', 'color': 'red'}
        else:
            return {'score': score, 'label': 'Neutral', 'color': 'gray'}

    def analyze_feed(self, df):
        """
        Apply analysis to a whole dataframe.
        """
        if df.empty or 'title' not in df.columns:
            return df
            
        results = df['title'].apply(self.analyze)
        df['sentiment_score'] = results.apply(lambda x: x['score'])
        df['sentiment_label'] = results.apply(lambda x: x['label'])
        df['sentiment_color'] = results.apply(lambda x: x['color'])
        return df
