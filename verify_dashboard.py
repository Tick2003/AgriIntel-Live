
import sys
import os
import pandas as pd

# Setup path
sys.path.append(os.getcwd())
import database.db_manager as db_manager

def test_dashboard_data():
    print("--- Testing Dashboard Data Sources ---")
    
    # 1. Test Aggregation
    print("\nFetching State Aggregation...")
    state_df = db_manager.get_state_level_aggregation()
    print(f"✅ Records Found: {len(state_df)}")
    if not state_df.empty:
        print(state_df.head())
        
    # 2. Test Coordinates
    print("\nFetching Mandi Coordinates...")
    coords = db_manager.get_mandi_coordinates()
    print(f"✅ Mandis Mapped: {len(coords)}")
    
    # Verify plotting data preparation
    map_data = []
    for mandi, val in coords.items():
        map_data.append({"lat": val['lat'], "lon": val['lon'], "mandi": mandi, "state": val['state']})
    
    map_df = pd.DataFrame(map_data)
    print("\n✅ Map Data Frame Prepared:")
    print(map_df.head())
    
    if len(map_df) > 0 and 'lat' in map_df.columns:
        print("✅ Ready for Plotly Scatter Mapbox")
    else:
        print("❌ Map Data issues.")

if __name__ == "__main__":
    test_dashboard_data()
