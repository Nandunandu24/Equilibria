import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.data_ingestion import DataIngestor
from src.predictive_core import PredictiveCore
from src.optimization_engine import OptimizationEngine
from src.agent_orchestration import AgentOrchestrator

# Set page configuration for a wide, premium layout
st.set_page_config(
    page_title="Dynamic Profit & Supply Chain Command Center",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom CSS for premium styling, fonts, and dark mode UI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Space+Grotesk:wght@300;500;700&display=swap');
    
    /* Main layout modifications */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .stApp {
        background-color: #0E1117;
        color: #E2E8F0;
    }
    
    /* Header and Title Styles */
    h1, h2, h3 {
        font-family: 'Space Grotesk', sans-serif;
        color: #F8FAFC;
        font-weight: 700;
    }
    
    .main-title {
        font-size: 2.8rem;
        background: linear-gradient(135deg, #38BDF8, #818CF8, #C084FC);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.1rem;
        font-weight: 800;
    }
    
    .sub-title {
        font-size: 1.1rem;
        color: #94A3B8;
        margin-bottom: 2rem;
    }
    
    /* Glassmorphic Metric Cards */
    .metric-card {
        background: rgba(30, 41, 59, 0.45);
        border: 1px solid rgba(148, 163, 184, 0.1);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(99, 102, 241, 0.4);
    }
    
    .metric-label {
        font-size: 0.85rem;
        text-transform: uppercase;
        color: #94A3B8;
        font-weight: 600;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #F8FAFC;
        margin-bottom: 4px;
    }
    
    .metric-delta {
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    .delta-positive {
        color: #10B981;
    }
    
    .delta-negative {
        color: #EF4444;
    }
    
    /* Agent Message Styling */
    .agent-bubble {
        padding: 18px;
        border-radius: 12px;
        margin-bottom: 16px;
        border-left: 5px solid;
    }
    
    .agent-sc {
        background-color: rgba(56, 189, 248, 0.07);
        border-left-color: #38BDF8;
        border: 1px solid rgba(56, 189, 248, 0.15);
    }
    
    .agent-fc {
        background-color: rgba(245, 158, 11, 0.07);
        border-left-color: #F59E0B;
        border: 1px solid rgba(245, 158, 11, 0.15);
    }
    
    .agent-cmd {
        background-color: rgba(139, 92, 246, 0.07);
        border-left-color: #8B5CF6;
        border: 1px solid rgba(139, 92, 246, 0.15);
    }
    
    /* Custom Sidebar styling */
    .css-1644z7q, [data-testid="stSidebar"] {
        background-color: #1E293B !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# STEP 1: INITIALIZE DATA & MODELS
# -------------------------------------------------------------
@st.cache_resource
def get_system_components():
    ingestor = DataIngestor(random_seed=42)
    predictive = PredictiveCore()
    optimizer = OptimizationEngine(random_seed=42)
    orchestrator = AgentOrchestrator()
    return ingestor, predictive, optimizer, orchestrator

ingestor, predictive, optimizer, orchestrator = get_system_components()

# -------------------------------------------------------------
# STEP 2: SIDEBAR - CONFIGURATION & RISK CONTROLS
# -------------------------------------------------------------
st.sidebar.markdown("### 🎛️ PORTFOLIO SELECTOR")
product_choices = ingestor.get_all_products()
selected_product_id = st.sidebar.selectbox(
    "Active Business Unit / Product",
    options=list(product_choices.keys()),
    format_func=lambda x: product_choices[x]
)

product_meta = ingestor.get_product_metadata(selected_product_id)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🚢 LOGISTICS DISRUPTION SLIDERS")
port_congestion = st.sidebar.slider(
    "Port Congestion Index",
    min_value=0.0,
    max_value=1.0,
    value=0.40,
    step=0.05,
    help="Higher values simulate longer queue delays at shipping ports."
)
weather_severity = st.sidebar.slider(
    "Weather Delay Severity",
    min_value=0.0,
    max_value=1.0,
    value=0.20,
    step=0.05,
    help="Models severe weather routing bottlenecks and safety speed reductions."
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 💰 OPERATIONAL COST MODIFIERS")
holding_cost_mult = st.sidebar.slider(
    "Warehouse Storage Fee Mult",
    min_value=0.5,
    max_value=3.0,
    value=1.0,
    step=0.1,
    help="Multiplies physical unit warehouse storage fees."
)
stockout_penalty_mult = st.sidebar.slider(
    "Stockout Financial Penalty Mult",
    min_value=0.5,
    max_value=3.0,
    value=1.0,
    step=0.1,
    help="Multiplies penalty costs for unfulfilled consumer demand."
)
capacity_mult = st.sidebar.slider(
    "Warehouse Capacity Modifier",
    min_value=0.5,
    max_value=1.5,
    value=1.0,
    step=0.1,
    help="Adjusts maximum physical warehouse holding capacity."
)

# Apply multipliers to active metadata copy
active_metadata = product_meta.copy()
active_metadata["holding_cost"] *= holding_cost_mult
active_metadata["stockout_penalty"] *= stockout_penalty_mult
active_metadata["warehouse_capacity"] = round(active_metadata["warehouse_capacity"] * capacity_mult)

# Compute transit indicators
logistics_risk_status = ingestor.simulate_transit_metrics(port_congestion, weather_severity)

# Render transit risk indicators in sidebar
st.sidebar.markdown("### 🚦 Logistics Congestion Status")
status_col, index_col = st.sidebar.columns(2)
with status_col:
    color_map = {"green": "🟢 Nominal", "orange": "🟡 Elevated", "red": "🔴 Critical"}
    st.markdown(f"**{color_map[logistics_risk_status['color']]}**")
with index_col:
    st.markdown(f"Risk Index: `{logistics_risk_status['logistics_risk_index']:.2f}`")

# -------------------------------------------------------------
# STEP 3: DEMAND ELASTICITY MODEL FITTING (Cached by Product ID)
# -------------------------------------------------------------
@st.cache_data
def get_historical_and_fit_model(prod_id):
    hist_df = ingestor.generate_historical_data(prod_id, days=120)
    # Instantiate clean predictive core and fit
    core = PredictiveCore()
    fit_summary = core.fit_demand_elasticity(hist_df)
    return hist_df, core, fit_summary

hist_df, active_core, fit_summary = get_historical_and_fit_model(selected_product_id)

# -------------------------------------------------------------
# STEP 4: RUN SIMULATION AND OPTIMIZATION
# -------------------------------------------------------------
# Default user manual settings (starting point)
st.sidebar.markdown("---")
st.sidebar.markdown("### 🛠️ MANUAL PORTFOLIO POLICIES")
manual_price = st.sidebar.slider(
    "Manual Price ($)",
    min_value=round(product_meta["base_price"] * 0.7),
    max_value=round(product_meta["base_price"] * 1.3),
    value=round(product_meta["base_price"]),
    step=1
)
manual_safety_stock_days = st.sidebar.slider(
    "Manual Safety Stock (Days)",
    min_value=0,
    max_value=10,
    value=4,
    step=1
)

# Run manual policy evaluation
manual_forecast_df = active_core.generate_14day_forecast(manual_price, seed=42)
manual_results = optimizer.simulate_policy(
    product_metadata=active_metadata,
    forecast_df=manual_forecast_df,
    price=manual_price,
    safety_stock_days=manual_safety_stock_days,
    port_congestion=port_congestion,
    weather_severity=weather_severity,
    num_trials=300
)

# Run optimal policy finder
with st.spinner("Solving dynamic decision grid for optimal policy..."):
    opt_results = optimizer.optimize_policy(
        product_metadata=active_metadata,
        predictive_core=active_core,
        port_congestion=port_congestion,
        weather_severity=weather_severity
    )

# -------------------------------------------------------------
# MAIN DASHBOARD RENDER
# -------------------------------------------------------------
st.markdown(f"<div class='main-title'>Dynamic Profit & Supply Chain Command Center</div>", unsafe_allow_html=True)
st.markdown(f"<div class='sub-title'>An Enterprise Decision Science Portfolio Framework for <strong>{product_choices[selected_product_id]}</strong></div>", unsafe_allow_html=True)

# Tabs
tab_command, tab_elasticity, tab_simulation, tab_sandbox = st.tabs([
    "🤝 Executive Command & Consensus", 
    "📈 Demand Elasticity Analytics", 
    "🎲 Stochastic Simulation & Risk",
    "🎛️ Sandbox Policy Comparison"
])

# -------------------------------------------------------------
# TAB 1: EXECUTIVE COMMAND & CONSENSUS BOARD
# -------------------------------------------------------------
with tab_command:
    # Metric rows using columns
    col1, col2, col3, col4 = st.columns(4)
    
    # Delta profit calculation
    profit_delta = opt_results["expected_max_profit"] - manual_results["mean_profit"]
    delta_class = "delta-positive" if profit_delta >= 0 else "delta-negative"
    delta_prefix = "+" if profit_delta >= 0 else ""
    
    # Stockout reduction calculation
    stockout_reduction = manual_results["stockout_probability"] - opt_results["stockout_probability"]
    stk_delta_class = "delta-positive" if stockout_reduction >= 0 else "delta-negative"
    stk_delta_prefix = "-" if stockout_reduction >= 0 else "+"
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Expected Net Profit (Manual)</div>
            <div class="metric-value">${manual_results['mean_profit']:,.2f}</div>
            <div class="metric-delta">Baseline operational policy</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Expected Net Profit (Optimized)</div>
            <div class="metric-value">${opt_results['expected_max_profit']:,.2f}</div>
            <div class="metric-delta {delta_class}">{delta_prefix}${profit_delta:,.2f} Expected Yield ({delta_prefix}{profit_delta/max(1.0, manual_results['mean_profit'])*100:.1f}%)</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Stockout Probability (Optimized)</div>
            <div class="metric-value">{opt_results['stockout_probability']*100:.1f}%</div>
            <div class="metric-delta {stk_delta_class}">{stk_delta_prefix}{abs(stockout_reduction)*100:.1f}% Risk Exposure vs Manual</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Value at Risk (Optimized 5% VaR)</div>
            <div class="metric-value">${opt_results['value_at_risk_5pct']:,.2f}</div>
            <div class="metric-delta">Downside limit under disruption</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Policy Summary Cards
    col_summary_1, col_summary_2 = st.columns(2)
    with col_summary_1:
        st.subheader("Manual Operational Settings")
        st.markdown(f"""
        * **Sales Pricing**: `${manual_price:.2f}` per unit
        * **Target Safety Stock**: `{manual_safety_stock_days} days` of expected demand
        * **Expected Holding Cost**: `${manual_results['mean_holding_cost']:,.2f}`
        * **Expected Stockout Cost**: `${manual_results['mean_stockout_cost']:,.2f}`
        """)
        
    with col_summary_2:
        st.subheader("🤖 AI-Optimized System Directives")
        st.markdown(f"""
        * **Optimal Sales Pricing**: `${opt_results['optimal_price']:.2f}` per unit (OLS Elasticity Guided)
        * **Optimal Safety Stock**: `{opt_results['optimal_safety_stock_days']} days` of demand (Monte Carlo Shielded)
        * **Expected Holding Cost**: `${opt_results['expected_holding_cost']:,.2f}`
        * **Expected Stockout Cost**: `${opt_results['expected_stockout_cost']:,.2f}`
        """)
        
    st.markdown("---")
    st.subheader("🤝 Multi-Agent Executive Consensus Debate")
    
    # Run Agent Debate dynamically or read cached debate
    # Cache key depends on products, congestion index, costs, policies
    # This prevents triggering LLM requests on basic UI scrolls
    @st.cache_data
    def get_agent_debate(prod_id, m_metrics, o_metrics, risk_details):
        prod_name = product_choices[prod_id]
        return orchestrator.run_debate(prod_name, m_metrics, o_metrics, risk_details)
        
    debate_markdown = get_agent_debate(
        selected_product_id, 
        {
            "price": manual_price,
            "safety_stock_days": manual_safety_stock_days,
            "mean_profit": manual_results["mean_profit"],
            "mean_stockout_cost": manual_results["mean_stockout_cost"],
            "mean_stockout_units": manual_results["mean_stockout_units"],
            "mean_holding_cost": manual_results["mean_holding_cost"],
            "stockout_probability": manual_results["stockout_probability"],
            "value_at_risk_5pct": manual_results["value_at_risk_5pct"]
        },
        opt_results,
        logistics_risk_status
    )
    
    # Stylize the output to fit our premium design framework
    # We split by agent headers and format with beautiful HTML containers
    lines = debate_markdown.split("---")
    
    if len(lines) >= 3:
        # Standard format parses into distinct styled boxes
        for section in lines:
            if "Supply Chain Risk Agent" in section:
                st.markdown(f"<div class='agent-bubble agent-sc'>{section.strip()}</div>", unsafe_allow_html=True)
            elif "Financial Controller" in section:
                st.markdown(f"<div class='agent-bubble agent-fc'>{section.strip()}</div>", unsafe_allow_html=True)
            elif "Strategy Commander" in section:
                st.markdown(f"<div class='agent-bubble agent-cmd'>{section.strip()}</div>", unsafe_allow_html=True)
            else:
                st.markdown(section)
    else:
        st.markdown(debate_markdown)

# -------------------------------------------------------------
# TAB 2: DEMAND ELASTICITY ANALYTICS
# -------------------------------------------------------------
with tab_elasticity:
    st.subheader("📊 Price Elasticity of Demand (PED) Estimation")
    st.markdown("""
    This panel fits historical transaction sales quantities against historical average pricing and seasonal factors using **Ordinary Least Squares (OLS) regression**.
    By identifying the price sensitivity coefficient ($\\beta$), we can mathematically forecast how pricing shifts impact volume.
    """)
    
    col_reg1, col_reg2 = st.columns([3, 2])
    
    with col_reg1:
        # Plotly chart showing historical scatter and regression curve
        # Create regression line overlay
        p_min = hist_df["price"].min() * 0.95
        p_max = hist_df["price"].max() * 1.05
        p_range = np.linspace(p_min, p_max, 100)
        
        # Predict at mean seasonality/promo
        mean_season = hist_df["is_high_season"].mean()
        mean_promo = hist_df["is_promo"].mean()
        
        # Q = alpha + beta*P + gamma_season*S + gamma_promo*Pr
        q_pred = fit_summary["alpha"] + fit_summary["beta"] * p_range + fit_summary["gamma_season"] * mean_season + fit_summary["gamma_promo"] * mean_promo
        
        fig = go.Figure()
        
        # Scatter actual sales
        fig.add_trace(go.Scatter(
            x=hist_df["price"],
            y=hist_df["quantity"],
            mode='markers',
            name='Historical Transaction Days',
            marker=dict(color='#818CF8', size=7, opacity=0.7)
        ))
        
        # Plot fitted curve
        fig.add_trace(go.Scatter(
            x=p_range,
            y=q_pred,
            mode='lines',
            name='Fitted Demand Curve (Fitted OLS)',
            line=dict(color='#38BDF8', width=3)
        ))
        
        # Highlight current manual price and current predicted qty
        pred_qty_manual = active_core.predict_demand(manual_price, 0, 0)
        fig.add_trace(go.Scatter(
            x=[manual_price],
            y=[pred_qty_manual],
            mode='markers+text',
            name='Current Manual Pricing',
            text=["Manual Policy"],
            textposition="top right",
            marker=dict(color='#F59E0B', size=12, symbol='star')
        ))
        
        # Highlight optimal price
        pred_qty_opt = active_core.predict_demand(opt_results["optimal_price"], 0, 0)
        fig.add_trace(go.Scatter(
            x=[opt_results["optimal_price"]],
            y=[pred_qty_opt],
            mode='markers+text',
            name='Optimal Pricing',
            text=["AI Optimal"],
            textposition="bottom left",
            marker=dict(color='#10B981', size=12, symbol='diamond')
        ))
        
        fig.update_layout(
            title="OLS Fitted Demand Curve: Q = f(P)",
            xaxis_title="Sales Unit Price ($)",
            yaxis_title="Quantity Demanded (Units/Day)",
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99)
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with col_reg2:
        # Elasticity coefficient slider demo
        st.markdown("#### ⚡ Real-Time Elasticity Calculator")
        test_price = st.slider("Select Trial Pricing ($)", min_value=int(p_min), max_value=int(p_max), value=int(manual_price))
        
        test_qty = active_core.predict_demand(test_price, 0, 0)
        elasticity_coef = active_core.calculate_elasticity(test_price, test_qty)
        
        # Elasticity classification
        if abs(elasticity_coef) < 0.5:
            classification = "Highly Inelastic (Low sensitivity to price)"
            class_color = "#38BDF8"
        elif abs(elasticity_coef) < 1.0:
            classification = "Relatively Inelastic (Slight sensitivity)"
            class_color = "#818CF8"
        elif abs(elasticity_coef) == 1.0:
            classification = "Unit Elastic"
            class_color = "#C084FC"
        else:
            classification = "Elastic (High sensitivity - price drops trigger major demand jumps)"
            class_color = "#EF4444"
            
        st.markdown(f"""
        * **Predicted Daily Demand (Baseline)**: `{test_qty:.1f} units`
        * **Fitted Elasticity Coefficient ($E$)**: <span style="font-size:1.3rem; font-weight:700; color:{class_color};">{elasticity_coef:.3f}</span>
        * **Market Classification**: <span style="font-weight:600; color:{class_color};">{classification}</span>
        """, unsafe_allow_html=True)
        
        st.markdown("#### 📐 Ordinary Least Squares Summary Diagnostics")
        
        # Create a simplified dataframe of OLS coefficients
        coef_data = {
            "Variable": ["Intercept (α)", "Price Coefficient (β)", "High Season (γ₁)", "Promo (γ₂)"],
            "Coefficient Value": [fit_summary["alpha"], fit_summary["beta"], fit_summary["gamma_season"], fit_summary["gamma_promo"]],
            "Std Error": [fit_summary["std_errs"]["const"], fit_summary["std_errs"]["price"], fit_summary["std_errs"]["is_high_season"], fit_summary["std_errs"]["is_promo"]],
            "P-Value": [fit_summary["p_values"]["const"], fit_summary["p_values"]["price"], fit_summary["p_values"]["is_high_season"], fit_summary["p_values"]["is_promo"]]
        }
        coef_df = pd.DataFrame(coef_data)
        
        st.dataframe(
            coef_df.style.format({
                "Coefficient Value": "{:.3f}",
                "Std Error": "{:.3f}",
                "P-Value": "{:.4e}"
            }),
            use_container_width=True,
            hide_index=True
        )
        
        st.markdown(f"""
        * **R-Squared ($R^2$)**: `{fit_summary['r_squared']:.4f}`
        * **Adjusted R-Squared**: `{fit_summary['adj_r_squared']:.4f}`
        * **Model F-Statistic P-Value**: `{fit_summary['f_pvalue']:.4e}`
        """)

# -------------------------------------------------------------
# TAB 3: STOCHASTIC SIMULATION & RISK ANALYSIS
# -------------------------------------------------------------
with tab_simulation:
    st.subheader("🎲 Monte Carlo Simulation Trajectories (14-Day Horizon)")
    st.markdown("""
    This panel models shipping bottlenecks as a stochastic lognormal lead-time delay. 
    By simulating 300 possible delay realizations, we visualize warehouse depletion trajectories, safety stock breaches, and tail profit risks.
    """)
    
    col_sim1, col_sim2 = st.columns(2)
    
    # 1. Trajectory Plot: Inventory levels over 14 days
    with col_sim1:
        # Gather daily inventory trajectories
        days = list(range(1, 15))
        manual_inv = manual_results["daily_inventory"]
        opt_inv = opt_results["details"]["daily_inventory"]
        
        fig_traj = go.Figure()
        
        # Warehouse capacity line
        fig_traj.add_trace(go.Scatter(
            x=days,
            y=[active_metadata["warehouse_capacity"]]*14,
            mode='lines',
            name='Warehouse Max Capacity',
            line=dict(color='#EF4444', width=2, dash='dash')
        ))
        
        # Manual inventory trajectory
        fig_traj.add_trace(go.Scatter(
            x=days,
            y=manual_inv,
            mode='lines+markers',
            name='Manual Inventory Trajectory',
            line=dict(color='#F59E0B', width=3)
        ))
        
        # Optimized inventory trajectory
        fig_traj.add_trace(go.Scatter(
            x=days,
            y=opt_inv,
            mode='lines+markers',
            name='AI-Optimized Trajectory',
            line=dict(color='#10B981', width=3)
        ))
        
        fig_traj.update_layout(
            title="Expected Physical Warehouse Stocks over 14 Days",
            xaxis=dict(tickmode='array', tickvals=days),
            xaxis_title="Planning Day",
            yaxis_title="Inventory on Hand (Units)",
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
        )
        st.plotly_chart(fig_traj, use_container_width=True)
        
    # 2. Risk Distribution: Profit Histograms
    with col_sim2:
        # Extract profits
        manual_profits = manual_results["trial_profits"]
        opt_profits = opt_results["details"]["trial_profits"]
        
        fig_dist = go.Figure()
        
        # Add manual profit distribution
        fig_dist.add_trace(go.Histogram(
            x=manual_profits,
            name='Manual Policy Expected Net Profits',
            marker_color='#F59E0B',
            opacity=0.55
        ))
        
        # Add optimized profit distribution
        fig_dist.add_trace(go.Histogram(
            x=opt_profits,
            name='Optimized Policy Expected Net Profits',
            marker_color='#10B981',
            opacity=0.55
        ))
        
        # Add Value at Risk markers
        fig_dist.add_vline(
            x=manual_results["value_at_risk_5pct"], 
            line_width=2, 
            line_dash="dash", 
            line_color="#D97706",
            annotation_text=f"Manual 5% VaR: ${manual_results['value_at_risk_5pct']:.0f}"
        )
        fig_dist.add_vline(
            x=opt_results["value_at_risk_5pct"], 
            line_width=2, 
            line_dash="dash", 
            line_color="#059669",
            annotation_text=f"Opt 5% VaR: ${opt_results['value_at_risk_5pct']:.0f}"
        )
        
        fig_dist.update_layout(
            title="Stochastic Profit Distribution & Value at Risk (VaR)",
            barmode='overlay',
            xaxis_title="Total Planning Period Net Profit ($)",
            yaxis_title="Frequency / Trial Count",
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_dist, use_container_width=True)

    # 3. Trajectory Data Frame
    st.markdown("#### 📅 Expected Trajectory Breakdown")
    daily_data = pd.DataFrame({
        "Day": days,
        "Manual Projected Demand": manual_forecast_df["forecasted_demand"].values,
        "Manual Avg Inventory": np.round(manual_inv, 1),
        "Manual Avg Stockout Units": np.round(manual_results["daily_stockouts"], 1),
        "Optimized Projected Demand": active_core.generate_14day_forecast(opt_results["optimal_price"])["forecasted_demand"].values,
        "Optimized Avg Inventory": np.round(opt_inv, 1),
        "Optimized Avg Stockout Units": np.round(opt_results["details"]["daily_stockouts"], 1)
    })
    
    st.dataframe(daily_data, use_container_width=True, hide_index=True)

# -------------------------------------------------------------
# TAB 4: SANDBOX POLICY COMPARISON
# -------------------------------------------------------------
with tab_sandbox:
    st.subheader("🎛️ Sandbox Policy Simulator")
    st.markdown("""
    Use this sandbox tab to test your own custom Pricing and Safety Stock policies. 
    The engine will run 200 Monte Carlo trials under the current logistics constraints to evaluate your policy's expected yield.
    """)
    
    col_sand1, col_sand2 = st.columns([1, 2])
    
    with col_sand1:
        st.markdown("#### Adjust Custom Sandbox Policy")
        custom_price = st.slider("Sandbox Price ($)", min_value=int(p_min), max_value=int(p_max), value=int(manual_price), key="sand_p")
        custom_ss = st.slider("Sandbox Safety Stock (Days)", min_value=0, max_value=12, value=int(manual_safety_stock_days), key="sand_ss")
        
        # Button to re-evaluate
        run_evaluation = st.button("⚡ Run Custom Policy Simulation")
        
        if run_evaluation:
            with st.spinner("Evaluating policy..."):
                custom_forecast_df = active_core.generate_14day_forecast(custom_price, seed=42)
                custom_results = optimizer.simulate_policy(
                    product_metadata=active_metadata,
                    forecast_df=custom_forecast_df,
                    price=custom_price,
                    safety_stock_days=custom_ss,
                    port_congestion=port_congestion,
                    weather_severity=weather_severity,
                    num_trials=300
                )
                st.session_state["custom_results"] = custom_results
                st.session_state["custom_price"] = custom_price
                st.session_state["custom_ss"] = custom_ss
                
        # Retrieve results
        c_results = st.session_state.get("custom_results", None)
        
    with col_sand2:
        st.markdown("#### 📊 Comparative Matrix")
        
        # Display side-by-side comparison table
        comp_data = {
            "Policy Parameter": ["Price ($)", "Safety Stock (Days)", "Expected Net Profit", "Expected Revenue", "Expected Holding Cost", "Expected Stockout Cost", "Stockout Probability"],
            "Manual Baseline Policy": [
                f"${manual_price:.2f}",
                f"{manual_safety_stock_days} days",
                f"${manual_results['mean_profit']:,.2f}",
                f"${manual_results['mean_revenue']:,.2f}",
                f"${manual_results['mean_holding_cost']:,.2f}",
                f"${manual_results['mean_stockout_cost']:,.2f}",
                f"{manual_results['stockout_probability']*100:.1f}%"
            ],
            "AI-Optimized Policy": [
                f"${opt_results['optimal_price']:.2f}",
                f"{opt_results['optimal_safety_stock_days']} days",
                f"${opt_results['expected_max_profit']:,.2f}",
                f"${opt_results['expected_revenue']:,.2f}",
                f"${opt_results['expected_holding_cost']:,.2f}",
                f"${opt_results['expected_stockout_cost']:,.2f}",
                f"{opt_results['stockout_probability']*100:.1f}%"
            ],
            "Your Custom Policy": [
                f"${st.session_state.get('custom_price', manual_price):.2f}",
                f"{st.session_state.get('custom_ss', manual_safety_stock_days)} days",
                f"${c_results['mean_profit']:,.2f}" if c_results else "Click Run",
                f"${c_results['mean_revenue']:,.2f}" if c_results else "Click Run",
                f"${c_results['mean_holding_cost']:,.2f}" if c_results else "Click Run",
                f"${c_results['mean_stockout_cost']:,.2f}" if c_results else "Click Run",
                f"{c_results['stockout_probability']*100:.1f}%" if c_results else "Click Run"
            ]
        }
        
        comp_df = pd.DataFrame(comp_data)
        st.dataframe(comp_df, use_container_width=True, hide_index=True)
        
        # Plotly chart comparing profits if custom policy exists
        if c_results:
            fig_comp = go.Figure()
            fig_comp.add_trace(go.Box(
                y=manual_results["trial_profits"],
                name="Manual Baseline",
                marker_color="#F59E0B"
            ))
            fig_comp.add_trace(go.Box(
                y=opt_results["details"]["trial_profits"],
                name="AI Optimized",
                marker_color="#10B981"
            ))
            fig_comp.add_trace(go.Box(
                y=c_results["trial_profits"],
                name="Your Custom",
                marker_color="#C084FC"
            ))
            fig_comp.update_layout(
                title="Profit Distribution Comparisons",
                yaxis_title="Net Profit ($)",
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_comp, use_container_width=True)
