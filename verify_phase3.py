import sys
import os

# Add root to path
sys.path.append(os.getcwd())

from agents.optimization_engine import OptimizationEngine

def test_optimization():
    print("\n--- Testing Optimization Engine ---")
    opt = OptimizationEngine()
    
    # 1. Test Crop Mix (Simplex/Heuristic)
    print("Testing Crop Mix Optimization...")
    land = 10.0 # Acres
    budget = 100000 # Rupees
    
    res = opt.optimize_crop_mix(land, budget)
    print(f"Status: {res['status']}")
    print(f"Allocations: {res['allocations']}")
    print(f"Total Profit: {res['total_profit']}")
    print(f"Used Land: {res['used_land']}")
    
    if res['used_land'] <= land and res['used_budget'] <= budget:
        print("✅ Constraints respected.")
    else:
        print("❌ Constraints violated.")
        
    # 2. Test EOQ
    print("\nTesting EOQ Calculation...")
    D = 1000
    S = 500
    H = 20
    # Expected: sqrt(2*1000*500 / 20) = sqrt(1000000/20) = sqrt(50000) approx 223.6
    eoq = opt.calculate_eoq(D, S, H)
    print(f"EOQ: {eoq}")
    
    if 223 < eoq < 224:
        print("✅ EOQ Calculation correct.")
    else:
        print("❌ EOQ Calculation incorrect.")

if __name__ == "__main__":
    test_optimization()
