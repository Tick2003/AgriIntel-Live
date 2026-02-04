
import sys
import os
import pandas as pd

# Add root to path
sys.path.append(os.getcwd())

from utils.graph_algo import MandiGraph, get_demo_graph
from cv.grading_model import GradingModel
from etl.data_loader import fetch_real_weather, fetch_weather_owm

def test_graph_algo():
    print("\n--- Testing Graph Algorithm ---")
    mg = get_demo_graph()
    prices = {m: 2500 for m in mg.graph.keys()}
    prices['Cuttack'] = 3000 # High price here
    
    start = "Khurda"
    best, options = mg.find_best_profit_route(start, 5.0, prices)
    
    if best:
        print(f"✅ Route Found: {start} -> {best['mandi']}")
        print(f"   Net Profit: {best['net_profit']}")
        print(f"   Distance: {best['distance_km']} km")
    else:
        print("❌ No route found.")

def test_grading_model():
    print("\n--- Testing Grading Model ---")
    grader = GradingModel()
    # We don't have an image, but predict handles missing image file in mock mode?
    # Actually my mock code tries to open the image if TORCH is available. 
    # But since TORCH is likely not available in this env, it uses Mock.
    # The mock code in `predict` doesn't strictly require the file to exist if it just returns random.
    # Let's check `cv/grading_model.py` code.
    # Code:
    # if TORCH_AVAILABLE and self.model: ...
    # else: mock_grade = random.choice...
    # So checking strictly, it should work even with a dummy path if torch is missing.
    
    res = grader.predict("dummy_image.jpg")
    print(f"✅ Grading Result: {res}")

def test_weather_fetch():
    print("\n--- Testing Weather Fetch ---")
    # Test fallback since we don't have API key
    try:
        df = fetch_real_weather()
        if not df.empty and 'temperature' in df.columns:
            print("✅ Weather Data Fetched (DataFrame)")
            print(df.head(2))
        else:
            print("❌ Weather DataFrame empty or invalid.")
    except Exception as e:
        print(f"❌ Weather Fetch Failed: {e}")

if __name__ == "__main__":
    test_graph_algo()
    test_grading_model()
    test_weather_fetch()
