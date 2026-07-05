import numpy as np
import pandas as pd

class OptimizationEngine:
    """
    Tier 3: Simulation & Optimization Core
    Performs stochastic Monte Carlo simulations of lead time delays and evaluates
    operational policies (Pricing & Safety Stock) to maximize the net profit function.
    """
    
    def __init__(self, random_seed=42):
        self.random_seed = random_seed

    def simulate_policy(self, product_metadata, forecast_df, price, safety_stock_days, 
                        port_congestion, weather_severity, num_trials=300):
        """
        Runs Monte Carlo simulation for a specific pricing and safety stock policy.
        Returns detailed logs of inventory level, stockouts, holding costs, and profit.
        """
        rng = np.random.default_rng(self.random_seed)
        
        mfg_cost = product_metadata["mfg_cost"]
        holding_cost = product_metadata["holding_cost"]
        stockout_penalty = product_metadata["stockout_penalty"]
        wh_capacity = product_metadata["warehouse_capacity"]
        initial_inv = product_metadata["initial_inventory"]
        base_lead_time = product_metadata["base_lead_time"]
        
        # Calculate safety stock in units
        # Average daily demand from forecast
        avg_daily_demand = forecast_df["forecasted_demand"].mean()
        safety_stock_units = safety_stock_days * avg_daily_demand
        
        # Lead time calculation adjusted by congestion and weather
        # Logistics Risk Index (0.0 to 1.0)
        logistics_risk_index = 0.6 * port_congestion + 0.4 * weather_severity
        
        # Mean delay scales with risk
        delay_mean = 2.0 * logistics_risk_index
        delay_std = 1.0 + 1.5 * logistics_risk_index
        
        # Precompute lognormal parameters for delays outside the loops
        sig2 = np.log(1.0 + (delay_std ** 2) / (max(0.5, delay_mean) ** 2))
        mu = np.log(max(0.5, delay_mean)) - 0.5 * sig2
        
        # Pre-extract forecast data to avoid Pandas index overhead inside loops
        forecasted_demands = forecast_df["forecasted_demand"].values
        demand_stds = np.maximum(2.0, forecasted_demands * 0.12)
        
        # Pre-allocate trial results
        trial_profits = np.zeros(num_trials)
        trial_holding_costs = np.zeros(num_trials)
        trial_stockout_costs = np.zeros(num_trials)
        trial_revenue = np.zeros(num_trials)
        trial_stockout_units = np.zeros(num_trials)
        
        # Trace dictionary to store average daily trajectories
        daily_inv_traces = np.zeros((num_trials, 14))
        daily_stockout_traces = np.zeros((num_trials, 14))
        daily_received_traces = np.zeros((num_trials, 14))
        
        # Expected lead time (including risk delay)
        expected_lead_time = base_lead_time + delay_mean
        # Reorder Point (ROP) = Lead Time Demand + Safety Stock
        reorder_point = (avg_daily_demand * expected_lead_time) + safety_stock_units
        order_qty = max(50, round(avg_daily_demand * 7))  # order a week's supply
        
        for trial in range(num_trials):
            # State variables for the trial
            inv = initial_inv
            # Queue of pending arrivals: list of dicts {"arrive_day": t, "qty": q}
            pending_orders = []
            
            # Tracking variables for 14 days
            profits_t = 0
            revenue_t = 0
            holding_t = 0
            stockout_t = 0
            stockout_qty_t = 0
            
            # Simple simulation: let's assume we start with no orders in transit for simplicity,
            # or one order already in transit to make it realistic.
            # Let's say there is a 50% chance an order is already arriving on day 2.
            if rng.random() < 0.5:
                pending_orders.append({"arrive_day": 2, "qty": order_qty})
                
            for t in range(14):
                forecasted_demand = forecasted_demands[t]
                
                # 1. Shipments Arrive
                received = 0
                # Filter pending orders arriving today
                arrived_orders = [o for o in pending_orders if o["arrive_day"] == t + 1]
                for o in arrived_orders:
                    received += o["qty"]
                # Keep only orders that haven't arrived yet
                pending_orders = [o for o in pending_orders if o["arrive_day"] != t + 1]
                
                daily_received_traces[trial, t] = received
                
                # Add received units to inventory
                inv += received
                
                # 2. Demand occurs (Stochastic demand centered around OLS forecast)
                # Demand variance scales with volume
                demand_std = demand_stds[t]
                actual_demand = max(0.0, rng.normal(forecasted_demand, demand_std))
                actual_demand = round(actual_demand)
                
                # 3. Fulfill demand & Calculate stockouts
                units_sold = min(inv, actual_demand)
                stockout_qty = max(0, actual_demand - inv)
                
                inv -= units_sold
                
                # Cap physical inventory at warehouse capacity; excess inventory gets stored
                # outside at double holding cost.
                excess_inv = max(0, inv - wh_capacity)
                physical_inv = min(inv, wh_capacity)
                
                # 4. Inventory control: Place new order if (inv + in-transit) < reorder_point
                in_transit_qty = sum(o["qty"] for o in pending_orders)
                total_position = inv + in_transit_qty
                
                if total_position < reorder_point:
                    # Determine lead time stochastically
                    # Delay is modelled using a lognormal distribution, so it's always positive
                    # Log-normal parameters to match mean delay and variance
                    sim_delay = rng.lognormal(mean=mu, sigma=np.sqrt(sig2))
                    sim_lead_time = round(base_lead_time + sim_delay)
                    
                    arrive_day = (t + 1) + sim_lead_time
                    pending_orders.append({"arrive_day": arrive_day, "qty": order_qty})
                
                # 5. Financial calculations for day t
                rev = units_sold * price
                mfg = units_sold * mfg_cost
                # Storage fee (normal storage fee + double fee for excess inventory)
                storage = (physical_inv * holding_cost) + (excess_inv * holding_cost * 2.0)
                stk_cost = stockout_qty * stockout_penalty
                
                revenue_t += rev
                holding_t += storage
                stockout_t += stk_cost
                stockout_qty_t += stockout_qty
                profits_t += (rev - mfg - storage - stk_cost)
                
                # Record trajectories
                daily_inv_traces[trial, t] = physical_inv
                daily_stockout_traces[trial, t] = stockout_qty
                
            trial_profits[trial] = profits_t
            trial_holding_costs[trial] = holding_t
            trial_stockout_costs[trial] = stockout_t
            trial_revenue[trial] = revenue_t
            trial_stockout_units[trial] = stockout_qty_t
            
        # Calculate aggregate metrics
        mean_profit = np.mean(trial_profits)
        std_profit = np.std(trial_profits)
        mean_holding = np.mean(trial_holding_costs)
        mean_stockout_cost = np.mean(trial_stockout_costs)
        mean_revenue = np.mean(trial_revenue)
        mean_stockout_units = np.mean(trial_stockout_units)
        
        # Risk indicators
        var_5pct = np.percentile(trial_profits, 5)  # Value at Risk (5th percentile)
        stockout_frequency = np.mean(trial_stockout_units > 0)  # Prob of at least one stockout
        
        return {
            "mean_profit": round(mean_profit, 2),
            "std_profit": round(std_profit, 2),
            "mean_holding_cost": round(mean_holding, 2),
            "mean_stockout_cost": round(mean_stockout_cost, 2),
            "mean_revenue": round(mean_revenue, 2),
            "mean_stockout_units": round(mean_stockout_units, 2),
            "value_at_risk_5pct": round(var_5pct, 2),
            "stockout_probability": round(stockout_frequency, 3),
            "daily_inventory": np.mean(daily_inv_traces, axis=0).tolist(),
            "daily_stockouts": np.mean(daily_stockout_traces, axis=0).tolist(),
            "daily_received": np.mean(daily_received_traces, axis=0).tolist(),
            "trial_profits": trial_profits.tolist()
        }

    def optimize_policy(self, product_metadata, predictive_core, port_congestion, weather_severity):
        """
        Runs a grid search over pricing and safety stock levels to maximize expected profit.
        Uses a quick simulation of 100 trials to find the optimal grid point.
        """
        base_price = product_metadata["base_price"]
        
        # Define search space
        price_grid = np.linspace(base_price * 0.85, base_price * 1.15, 6)
        safety_stock_grid = [0, 2, 4, 6, 8]  # safety stock in days of demand
        
        best_profit = -float("inf")
        best_price = base_price
        best_safety_stock = 4
        best_metrics = None
        
        # Grid Search
        for p in price_grid:
            p = round(p, 2)
            # Generate 14-day forecast for this candidate price
            forecast_df = predictive_core.generate_14day_forecast(p, seed=self.random_seed)
            
            for ss in safety_stock_grid:
                # Fast evaluation (40 trials)
                metrics = self.simulate_policy(
                    product_metadata=product_metadata,
                    forecast_df=forecast_df,
                    price=p,
                    safety_stock_days=ss,
                    port_congestion=port_congestion,
                    weather_severity=weather_severity,
                    num_trials=40
                )
                
                if metrics["mean_profit"] > best_profit:
                    best_profit = metrics["mean_profit"]
                    best_price = p
                    best_safety_stock = ss
                    best_metrics = metrics
                    
        # Run a full simulation (150 trials) for the optimal grid point to get robust details
        forecast_df_opt = predictive_core.generate_14day_forecast(best_price, seed=self.random_seed)
        opt_details = self.simulate_policy(
            product_metadata=product_metadata,
            forecast_df=forecast_df_opt,
            price=best_price,
            safety_stock_days=best_safety_stock,
            port_congestion=port_congestion,
            weather_severity=weather_severity,
            num_trials=150
        )
        
        return {
            "optimal_price": best_price,
            "optimal_safety_stock_days": best_safety_stock,
            "expected_max_profit": opt_details["mean_profit"],
            "expected_revenue": opt_details["mean_revenue"],
            "expected_holding_cost": opt_details["mean_holding_cost"],
            "expected_stockout_cost": opt_details["mean_stockout_cost"],
            "expected_stockout_units": opt_details["mean_stockout_units"],
            "stockout_probability": opt_details["stockout_probability"],
            "value_at_risk_5pct": opt_details["value_at_risk_5pct"],
            "details": opt_details
        }
