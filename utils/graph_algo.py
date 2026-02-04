import heapq

class MandiGraph:
    def __init__(self):
        # Adjacency list: {node: [(neighbor, distance_km), ...]}
        self.graph = {}
        # Transport cost per km (fixed for now, could be dynamic)
        self.transport_cost_per_km_ton = 15.0  # ₹15 per km per ton

    def add_mandi(self, mandi_name):
        if mandi_name not in self.graph:
            self.graph[mandi_name] = []

    def add_route(self, from_mandi, to_mandi, distance_km):
        self.add_mandi(from_mandi)
        self.add_mandi(to_mandi)
        # Assuming undirected roads for simplicity, or add both ways
        self.graph[from_mandi].append((to_mandi, distance_km))
        self.graph[to_mandi].append((from_mandi, distance_km))

    def _get_shortest_paths(self, start_node):
        """
        Dijkstra's Algorithm to find shortest distance from start_node to all other nodes.
        returns: distances_dict, previous_nodes_dict
        """
        distances = {node: float('inf') for node in self.graph}
        distances[start_node] = 0
        pq = [(0, start_node)]
        previous = {node: None for node in self.graph}

        while pq:
            current_dist, current_node = heapq.heappop(pq)

            if current_dist > distances[current_node]:
                continue

            for neighbor, weight in self.graph[current_node]:
                distance = current_dist + weight
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous[neighbor] = current_node
                    heapq.heappush(pq, (distance, neighbor))
        
        return distances, previous

    def find_best_profit_route(self, start_mandi, quantity_tons, commodity_prices):
        """
        Finds the best destination Mandi based on:
        (Price * Qty) - (Transport Cost)
        
        Args:
            start_mandi (str): Starting location name.
            quantity_tons (float): Amount of produce.
            commodity_prices (dict): {mandi_name: price_per_quintal}
                                     Note: 1 Ton = 10 Quintals.
        
        Returns:
            dict: Best option details {target_mandi, net_profit, distance, transport_cost}
            list: Ranked list of all options.
        """
        distances, _ = self._get_shortest_paths(start_mandi)
        
        options = []
        
        for mandi, price_per_quintal in commodity_prices.items():
            if mandi not in distances or distances[mandi] == float('inf'):
                continue
                
            dist_km = distances[mandi]
            transport_cost = dist_km * self.transport_cost_per_km_ton * quantity_tons
            
            # Revenue: Price (per quintal) * Quantity (tons * 10)
            gross_revenue = price_per_quintal * (quantity_tons * 10)
            
            net_profit = gross_revenue - transport_cost
            
            options.append({
                "mandi": mandi,
                "distance_km": dist_km,
                "transport_cost": round(transport_cost, 2),
                "gross_revenue": round(gross_revenue, 2),
                "net_profit": round(net_profit, 2),
                "price_per_q": price_per_quintal
            })
            
        # Sort by Net Profit descending
        options.sort(key=lambda x: x['net_profit'], reverse=True)
        
        if not options:
            return None, []
            
        return options[0], options

# --- Usage Example / Mock Setup ---
def get_demo_graph():
    mg = MandiGraph()
    # Adding Odia/nearby locations
    mg.add_route("Cuttack", "Bhubaneswar", 26)
    mg.add_route("Bhubaneswar", "Jatni", 23)
    mg.add_route("Bhubaneswar", "Khurda", 28)
    mg.add_route("Cuttack", "Dhenkanal", 55)
    mg.add_route("Bhubaneswar", "Puri", 60)
    mg.add_route("Jatni", "Khurda", 8)
    mg.add_route("Cuttack", "Jagatsinghpur", 40)
    return mg
