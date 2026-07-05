import sys
import json
import numpy as np

from src.data_ingestion import DataIngestor, fetch_realtime_logistics_modifiers, fetch_realtime_cost_multipliers
from src.predictive_core import PredictiveCore
from src.optimization_engine import OptimizationEngine
from src.agent_orchestration import AgentOrchestrator

def main():
    try:
        # Read JSON from stdin
        input_data = json.loads(sys.stdin.read())
    except Exception as e:
        input_data = {}

    # Extract parameters with defaults
    product_id = input_data.get("product_id", "semiconductors")
    use_realtime = input_data.get("use_realtime", False)
    
    if use_realtime:
        # Fetch the live world state telemetry instantly
        live_weather_delay = fetch_realtime_logistics_modifiers()
        live_storage_mult, live_stockout_mult = fetch_realtime_cost_multipliers(product_id)
        
        # Merge live values
        port_congestion = float(input_data.get("port_congestion", 0.40))  # slider congestion
        weather_severity = live_weather_delay
        holding_cost_mult = live_storage_mult
        stockout_penalty_mult = live_stockout_mult
    else:
        # Fall back to UI slider overrides
        port_congestion = float(input_data.get("port_congestion", 0.40))
        weather_severity = float(input_data.get("weather_severity", 0.20))
        holding_cost_mult = float(input_data.get("holding_cost_mult", 1.0))
        stockout_penalty_mult = float(input_data.get("stockout_penalty_mult", 1.0))
        
    capacity_mult = float(input_data.get("capacity_mult", 1.0))
    
    # 1. Initialize Ingestion
    ingestor = DataIngestor(random_seed=42)
    products = ingestor.get_all_products()
    
    if product_id not in products:
        product_id = list(products.keys())[0]
        
    product_meta = ingestor.get_product_metadata(product_id)
    
    # Apply multipliers
    active_meta = product_meta.copy()
    active_meta["holding_cost"] *= holding_cost_mult
    active_meta["stockout_penalty"] *= stockout_penalty_mult
    active_meta["warehouse_capacity"] = round(active_meta["warehouse_capacity"] * capacity_mult)
    
    # Manual policy settings
    manual_price = float(input_data.get("price", active_meta["base_price"]))
    manual_ss = int(input_data.get("safety_stock_days", 4))
    
    # Get congestion metrics
    logistics_risk_status = ingestor.simulate_transit_metrics(port_congestion, weather_severity)
    
    # 2. Ingest history and fit OLS Price Elasticity
    hist_df = ingestor.generate_historical_data(product_id, days=120)
    predictive = PredictiveCore()
    fit_summary = predictive.fit_demand_elasticity(hist_df)
    
    # 3. Evaluate manual policy
    manual_forecast_df = predictive.generate_14day_forecast(manual_price, seed=42)
    optimizer = OptimizationEngine(random_seed=42)
    manual_results = optimizer.simulate_policy(
        product_metadata=active_meta,
        forecast_df=manual_forecast_df,
        price=manual_price,
        safety_stock_days=manual_ss,
        port_congestion=port_congestion,
        weather_severity=weather_severity,
        num_trials=150
    )
    
    # 4. Run optimization search
    opt_results = optimizer.optimize_policy(
        product_metadata=active_meta,
        predictive_core=predictive,
        port_congestion=port_congestion,
        weather_severity=weather_severity
    )
    
    # 5. Run agent debate
    orchestrator = AgentOrchestrator()
    # Build metrics context
    current_metrics = {
        "price": manual_price,
        "safety_stock_days": manual_ss,
        "mean_profit": manual_results["mean_profit"],
        "mean_stockout_cost": manual_results["mean_stockout_cost"],
        "mean_stockout_units": manual_results["mean_stockout_units"],
        "mean_holding_cost": manual_results["mean_holding_cost"],
        "stockout_probability": manual_results["stockout_probability"],
        "value_at_risk_5pct": manual_results["value_at_risk_5pct"]
    }
    
    debate_text = orchestrator.run_debate(
        product_name=products[product_id],
        current_metrics=current_metrics,
        opt_metrics=opt_results,
        logistics_risk_details=logistics_risk_status
    )
    
    # Prepare JSON response payload
    # Convert numpy types to native python types for JSON serialization
    response = {
        "product_id": product_id,
        "product_name": products[product_id],
        "products_list": products,
        "logistics_risk": logistics_risk_status,
        "telemetry": {
            "active": use_realtime,
            "weather_severity": float(np.round(weather_severity, 3)),
            "holding_cost_mult": float(np.round(holding_cost_mult, 2)),
            "stockout_penalty_mult": float(np.round(stockout_penalty_mult, 2))
        },
        "metadata": {
            "base_price": active_meta["base_price"],
            "mfg_cost": active_meta["mfg_cost"],
            "holding_cost": active_meta["holding_cost"],
            "stockout_penalty": active_meta["stockout_penalty"],
            "warehouse_capacity": active_meta["warehouse_capacity"]
        },
        "fit_summary": {
            "alpha": float(fit_summary["alpha"]),
            "beta": float(fit_summary["beta"]),
            "gamma_season": float(fit_summary["gamma_season"]),
            "gamma_promo": float(fit_summary["gamma_promo"]),
            "r_squared": float(fit_summary["r_squared"]),
            "adj_r_squared": float(fit_summary["adj_r_squared"]),
            "mean_elasticity": float(fit_summary["mean_elasticity"]),
            "p_values": fit_summary["p_values"],
            "std_errs": fit_summary["std_errs"]
        },
        "manual_results": {
            "mean_profit": manual_results["mean_profit"],
            "mean_revenue": manual_results["mean_revenue"],
            "mean_holding_cost": manual_results["mean_holding_cost"],
            "mean_stockout_cost": manual_results["mean_stockout_cost"],
            "mean_stockout_units": manual_results["mean_stockout_units"],
            "stockout_probability": manual_results["stockout_probability"],
            "value_at_risk_5pct": manual_results["value_at_risk_5pct"],
            "daily_inventory": manual_results["daily_inventory"],
            "daily_stockouts": manual_results["daily_stockouts"],
            "daily_received": manual_results["daily_received"],
            "trial_profits": manual_results["trial_profits"]
        },
        "opt_results": {
            "optimal_price": opt_results["optimal_price"],
            "optimal_safety_stock_days": opt_results["optimal_safety_stock_days"],
            "expected_max_profit": opt_results["expected_max_profit"],
            "expected_revenue": opt_results["expected_revenue"],
            "expected_holding_cost": opt_results["expected_holding_cost"],
            "expected_stockout_cost": opt_results["expected_stockout_cost"],
            "expected_stockout_units": opt_results["expected_stockout_units"],
            "stockout_probability": opt_results["stockout_probability"],
            "value_at_risk_5pct": opt_results["value_at_risk_5pct"],
            "daily_inventory": opt_results["details"]["daily_inventory"],
            "daily_stockouts": opt_results["details"]["daily_stockouts"],
            "daily_received": opt_results["details"]["daily_received"],
            "trial_profits": opt_results["details"]["trial_profits"]
        },
        "agent_debate": debate_text,
        "historical_data": {
            "price": hist_df["price"].tolist(),
            "quantity": hist_df["quantity"].tolist(),
            "is_high_season": hist_df["is_high_season"].tolist()
        }
    }
    
    # Print clean JSON output
    print(json.dumps(response))

if __name__ == "__main__":
    main()
