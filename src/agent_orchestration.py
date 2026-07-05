import os
import time
from openai import OpenAI

class AgentOrchestrator:
    """
    Tier 4: Multi-Agent Orchestration Layer
    Coordinates persona-driven debates (Finance, Supply Chain, and Strategy)
    using LLMs to build executive consensus based on optimization metrics.
    """
    
    def __init__(self):
        # Initialize OpenAI client if API key is available
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if self.api_key and self.api_key != "SET":
            self.client = OpenAI(api_key=self.api_key, max_retries=0, timeout=2.0)
        else:
            self.client = None

    def run_debate(self, product_name, current_metrics, opt_metrics, logistics_risk_details):
        """
        Executes the agent debate. If OpenAI is available, queries the model.
        Otherwise, falls back to a high-fidelity local template.
        """
        if self.client:
            try:
                return self._call_llm_debate(product_name, current_metrics, opt_metrics, logistics_risk_details)
            except Exception as e:
                # Fallback to local simulation in case of connection/quota errors
                return self._generate_local_fallback(product_name, current_metrics, opt_metrics, logistics_risk_details, error_msg=str(e))
        else:
            return self._generate_local_fallback(product_name, current_metrics, opt_metrics, logistics_risk_details)

    def _call_llm_debate(self, product_name, current_metrics, opt_metrics, logistics_risk):
        """
        Calls OpenAI to perform a contextual debate among the three agents.
        """
        prompt = f"""
        You are simulating an executive debate for the product: {product_name}.
        
        CONTEXT & METRICS:
        - Port Congestion Index: {logistics_risk['port_congestion']} (Scale 0-1)
        - Weather Severity Index: {logistics_risk['weather_severity']} (Scale 0-1)
        - Combined Logistics Risk: {logistics_risk['logistics_risk_index']} (Status: {logistics_risk['status']})
        
        CURRENT OPERATIONAL POLICY (Manual/Default):
        - Pricing: ${current_metrics.get('price', 'N/A')}
        - Safety Stock Buffer: {current_metrics.get('safety_stock_days', 'N/A')} days
        - Expected Profit: ${current_metrics.get('mean_profit', 'N/A')}
        - Expected Stockout Cost: ${current_metrics.get('mean_stockout_cost', 'N/A')}
        - Expected Stockout Units: {current_metrics.get('mean_stockout_units', 'N/A')} units
        - Expected Holding Cost: ${current_metrics.get('mean_holding_cost', 'N/A')}
        - Probability of Stockout: {current_metrics.get('stockout_probability', 'N/A') * 100:.1f}%
        - Value at Risk (5th Percentile Profit): ${current_metrics.get('value_at_risk_5pct', 'N/A')}
        
        AI-OPTIMIZED OPERATIONAL POLICY:
        - Optimal Pricing: ${opt_metrics.get('optimal_price', 'N/A')}
        - Optimal Safety Stock Buffer: {opt_metrics.get('optimal_safety_stock_days', 'N/A')} days
        - Expected Optimized Profit: ${opt_metrics.get('expected_max_profit', 'N/A')}
        - Expected Optimized Revenue: ${opt_metrics.get('expected_revenue', 'N/A')}
        - Expected Optimized Holding Cost: ${opt_metrics.get('expected_holding_cost', 'N/A')}
        - Expected Optimized Stockout Cost: ${opt_metrics.get('expected_stockout_cost', 'N/A')}
        - Expected Optimized Stockout Units: {opt_metrics.get('expected_stockout_units', 'N/A')} units
        - Optimized Probability of Stockout: {opt_metrics.get('stockout_probability', 'N/A') * 100:.1f}%
        - Optimized Value at Risk (5th Percentile Profit): ${opt_metrics.get('value_at_risk_5pct', 'N/A')}
        
        Please generate a multi-agent debate transcript in Markdown.
        We have three personas:
        1. **Supply Chain Risk Agent (Logistics Buffer Advocate)**:
           - Prioritizes inventory availability.
           - Warns about port congestion and weather delays.
           - Explains why safety stock buffer shifts are needed or dangerous.
           - References the stockout probability and delay indices.
        2. **Financial Controller Agent (Margin & Cost Controller)**:
           - Prioritizes capital optimization, high margins, and lean logistics.
           - Warns against high holding costs and capital locked up in warehouses.
           - Cites expected holding costs and overall capital efficiency.
        3. **Strategy Commander Agent (Consensus Architect & Executive Summarizer)**:
           - Mediates the conflict.
           - Evaluates the optimization recommendation.
           - Provides the final "So What?" operational policy directive in clean English.
        
        Write the debate in a conversational, professional tone. Keep individual contributions concise (2-3 sentences each) and focus on the quantitative numbers. Conclude with a clear Strategy Commander Directive summarizing the policy shift.
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a decision science agent framework. You output clear, markdown-formatted professional debates."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000,
            timeout=2.0
        )
        
        return response.choices[0].message.content

    def _generate_local_fallback(self, product_name, current_metrics, opt_metrics, logistics_risk, error_msg=None):
        """
        A high-fidelity local template fallback that populates dynamic operational values
        into a pre-defined agent debate context.
        """
        # Determine status flags
        risk_status = logistics_risk["status"]
        curr_price = current_metrics.get('price', 0)
        opt_price = opt_metrics.get('optimal_price', 0)
        curr_ss = current_metrics.get('safety_stock_days', 0)
        opt_ss = opt_metrics.get('optimal_safety_stock_days', 0)
        
        # Build Markdown conversation
        fallback_md = f"""### 🤝 Decision Science Multi-Agent Consensus Board
*System Status: Local Simulation Active {f'(API Error Fallback: {error_msg})' if error_msg else ''}*

---

#### 📦 **Supply Chain Risk Agent** (Logistics & Buffer Advocate)
> "Looking at the current logistics configuration for **{product_name}**, our logistics risk index is at **{logistics_risk['logistics_risk_index']}** (Status: **{risk_status}**). Under our manual safety stock of **{curr_ss} days**, our simulated stockout probability is **{current_metrics.get('stockout_probability', 0) * 100:.1f}%**, which translates to an expected stockout cost of **${current_metrics.get('mean_stockout_cost', 0):,.2f}**. 
> By moving to the recommended safety stock of **{opt_ss} days**, we can compress the stockout probability down to **{opt_metrics.get('stockout_probability', 0) * 100:.1f}%**, protecting our customer relationships and buffer levels against the current congestion."

---

#### 📊 **Financial Controller Agent** (Capital & Margin Controller)
> "I hear the concern on stockouts, but we must protect capital efficiency. Storing EV batteries or semiconductor units is not free. Under the manual settings, daily holding costs sit at **${current_metrics.get('mean_holding_cost', 0):,.2f}**.
> If we shift to the optimized pricing of **${opt_price:.2f}** (up/down from **${curr_price:.2f}**), we can offset the warehouse holding cost of **${opt_metrics.get('expected_holding_cost', 0):,.2f}** with stronger margins. The OLS price elasticity is driving this decision; the optimized price maximizes overall net expected margin without leaving excess cash tied up in dead-stock."

---

#### 🎖️ **Strategy Commander Agent** (Consensus Directive)
> "Excellent points from both sides. Let's look at the bottom-line numbers. Under the manual policy, we expect a net profit of **${current_metrics.get('mean_profit', 0):,.2f}** with a high tail-risk (5% VaR is **${current_metrics.get('value_at_risk_5pct', 0):,.2f}**).
> The AI-Optimized model increases expected net profit to **${opt_metrics.get('expected_max_profit', 0):,.2f}** and raises our 5% VaR to **${opt_metrics.get('value_at_risk_5pct', 0):,.2f}**—meaning the portfolio is more resilient to transit disruptions.
> 
> **Operational Directive:**
> 1. **Price Adjustment**: Set price to **${opt_price:.2f}**.
> 2. **Inventory Buffer**: Shift safety stock to **{opt_ss} days**.
> 3. **Expected Impact**: This will capture **${(opt_metrics.get('expected_max_profit', 0) - current_metrics.get('mean_profit', 0)):,.2f}** in incremental profit while reducing stockout exposure by **{max(0.0, (current_metrics.get('stockout_probability', 0) - opt_metrics.get('stockout_probability', 0)) * 100):.1f}%**."
"""
        return fallback_md
