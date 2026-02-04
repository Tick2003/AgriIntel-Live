import numpy as np

# Try importing scipy, else fallback
try:
    from scipy.optimize import linprog
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    print("Warning: Scipy not found. Using Heuristic Optimization.")

class OptimizationEngine:
    def __init__(self):
        pass

    def optimize_crop_mix(self, total_land, total_budget, constraints=None):
        """
        Determines optimal crop mix to maximize profit.
        Crops: [Wheat, Rice, Pulses, Mustard]
        
        Args:
            total_land (float): Acres available.
            total_budget (float): Capital in Rupees.
            constraints (dict): Optional min/max per crop.
        """
        # Data per Acre (Mock Data for Indian Context)
        #                 Wheat,   Rice,    Pulses,  Mustard
        profit_per_acre = [25000,   30000,   20000,   28000] # Objective Function (Maximize)
        cost_per_acre   = [8000,    12000,   5000,    9000]  # Constraint 1: Budget
        # Constraint 2: Total Land <= total_land (Coeffs: 1, 1, 1, 1)
        
        crop_names = ["Wheat", "Rice", "Pulses", "Mustard"]
        
        if SCIPY_AVAILABLE:
            # Scipy linprog minimizes, so we negate profit
            c = [-p for p in profit_per_acre] 
            
            # Inequality constraints (Ax <= b)
            A = [
                cost_per_acre,       # Budget Constraint
                [1, 1, 1, 1]         # Land Constraint
            ]
            
            b = [total_budget, total_land]
            
            # Bounds (x >= 0)
            x_bounds = [(0, None) for _ in range(4)]
            
            res = linprog(c, A_ub=A, b_ub=b, bounds=x_bounds, method='highs')
            
            if res.success:
                return {
                    "status": "Optimal",
                    "allocations": {crop_names[i]: round(res.x[i], 2) for i in range(4)},
                    "total_profit": round(-res.fun, 2),
                    "used_land": round(sum(res.x), 2),
                    "used_budget": round(sum([res.x[i] * cost_per_acre[i] for i in range(4)]), 2)
                }
            else:
                return {"status": "Failed", "message": res.message}
                
        else:
            # Greedy Heuristic (Sort by Profit/Cost Ratio)
            # This is a simplification when Scipy isn't there
            ratios = [(profit_per_acre[i]/cost_per_acre[i], i) for i in range(4)]
            ratios.sort(reverse=True, key=lambda x: x[0])
            
            remaining_land = total_land
            remaining_budget = total_budget
            allocations = [0] * 4
            
            for ratio, idx in ratios:
                # Maximize this crop
                max_by_land = remaining_land
                max_by_budget = remaining_budget / cost_per_acre[idx]
                
                amount = min(max_by_land, max_by_budget)
                allocations[idx] = amount
                
                remaining_land -= amount
                remaining_budget -= amount * cost_per_acre[idx]
                
            total_profit = sum([allocations[i] * profit_per_acre[i] for i in range(4)])
            
            return {
                "status": "Heuristic (Approx)",
                "allocations": {crop_names[i]: round(allocations[i], 2) for i in range(4)},
                "total_profit": round(total_profit, 2),
                "used_land": round(total_land - remaining_land, 2),
                "used_budget": round(total_budget - remaining_budget, 2)
            }

    def calculate_eoq(self, annual_demand, ordering_cost, holding_cost_per_unit):
        """
        Calculate Economic Order Quantity (EOQ).
        Formula: sqrt(2 * D * S / H)
        """
        if holding_cost_per_unit <= 0: return 0
        
        eoq = np.sqrt((2 * annual_demand * ordering_cost) / holding_cost_per_unit)
        return round(eoq, 2)
