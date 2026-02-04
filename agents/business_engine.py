import random
import pandas as pd

class B2BMatcher:
    """
    Matches Farmers with Buyers (Traders, Millers, Exporters).
    """
    def __init__(self):
        # Mock Database of Buyers
        self.buyers = [
            {"id": "B001", "name": "Global Foods Export", "type": "Exporter", "location": "Mumbai", "rating": 4.8},
            {"id": "B002", "name": "Odisha Rice Mills", "type": "Miller", "location": "Cuttack", "rating": 4.5},
            {"id": "B003", "name": "Fresh Veggies Corp", "type": "Retail Chain", "location": "Bhubaneswar", "rating": 4.2},
            {"id": "B004", "name": "Kolkata Traders", "type": "Wholesaler", "location": "Kolkata", "rating": 3.9},
            {"id": "B005", "name": "Nasik Onion Depo", "type": "Aggregator", "location": "Nasik", "rating": 4.6},
        ]

    def find_buyers(self, commodity, quantity, mandi_location):
        """
        Returns a list of buyers interested in the deal.
        """
        matches = []
        
        # Simulation Logic: 
        # 1. Nearby buyers get higher match score
        # 2. Match logic is randomized for demo variety
        
        for buyer in self.buyers:
            score = random.randint(60, 99)
            
            # Boost score if location fuzzy matches
            if buyer['location'] in mandi_location or mandi_location in buyer['location']:
                score += 10
            
            # Cap at 100
            score = min(score, 100)
            
            # Generate a fake bid price
            market_price = 2500 # Base
            bid_price = market_price + random.randint(-100, 200)
            
            matches.append({
                "buyer_name": buyer['name'],
                "type": buyer['type'],
                "location": buyer['location'],
                "match_score": score,
                "bid_price": bid_price,
                "distance": random.randint(5, 500) # km
            })
            
        # Sort by match score
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        return matches

class FintechEngine:
    """
    Calculates Creditworthiness and Generates Loan Offers.
    """
    def __init__(self):
        pass

    def calculate_credit_score(self, yield_history, reliability_index):
        """
        Args:
            yield_history (list): List of yield values (e.g., tons/acre) for past seasons.
            reliability_index (float): 0-1 score of how consistent the farmer is.
        """
        # Base Score
        score = 650 
        
        # 1. Consistency Bonus
        score += int(reliability_index * 100)
        
        # 2. Yield Stability Bonus (Mock)
        # If yield_history is stable, add points
        if yield_history and len(yield_history) > 1:
            variance = max(yield_history) - min(yield_history)
            if variance < 2.0: # Low variance
                score += 50
        
        # Cap at 900
        score = min(score, 900)
        
        # Loan Eligibility
        # Logic: Score * 1000
        loan_limit = score * 500 
        
        offer = {
            "credit_score": score,
            "rating": self._get_rating(score),
            "max_loan": loan_limit,
            "interest_rate": self._get_interest_rate(score)
        }
        return offer

    def _get_rating(self, score):
        if score >= 800: return "Excellent"
        if score >= 750: return "Very Good"
        if score >= 700: return "Good"
        if score >= 650: return "Fair"
        return "Needs Improvement"

    def _get_interest_rate(self, score):
        if score >= 800: return 8.5
        if score >= 700: return 10.5
        return 12.0
