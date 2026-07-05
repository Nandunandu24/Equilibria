// Global Operational State
let activeProductId = 'semiconductors';
let activeData = null;

// Explanatory points for each flow block
const flowDescriptions = {
    '1': '<h4>Data Ingestion & Synthesis Layer</h4><p>Compiles 120-day transaction tables, pricing structures, promotions, and logistics lead-time constraints. It models baseline inventory positions and projects starting buffers for downstream analysis.</p>',
    '2': '<h4>Predictive Analytics Core (OLS Model)</h4><p>Fits transaction logs using Ordinary Least Squares: <em>Q = α + βP + γ₁X₁ + γ₂X₂ + ε</em>. Solves for price elasticity coefficients ($E = β × P/Q$), p-values, and model R-squared statistics.</p>',
    '3': '<h4>Stochastic Simulation Engine</h4><p>Executes 300 Monte Carlo trials across a 14-day window. Projects supply delays as a stochastically shifted lognormal distribution, evaluating stockout frequencies and tail profit risks (Value-at-Risk).</p>',
    '4': '<h4>Multi-Agent Consensus Layer</h4><p>Feeds analytics matrices into a collaborative council (Finance, Supply Chain, Strategy). Persona agents debate inventory storage overheads vs out-of-stock penalties, producing an actionable operational directive.</p>'
};

// -------------------------------------------------------------
// EVENT LISTENERS & INITIALIZATION
// -------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Flow Block Hover/Click handlers
    const flowBlocks = document.querySelectorAll('.flow-block');
    flowBlocks.forEach(block => {
        const trigger = () => {
            flowBlocks.forEach(b => b.classList.remove('active'));
            block.classList.add('active');
            
            const flowId = block.getAttribute('data-flow');
            document.getElementById('visual-desc').innerHTML = flowDescriptions[flowId];
            
            // Highlight flow nodes in graphic
            document.querySelectorAll('.flow-node').forEach(node => node.classList.remove('active'));
            document.getElementById(`node-${flowId}`).classList.add('active');
        };
        block.addEventListener('mouseenter', trigger);
        block.addEventListener('click', trigger);
    });

    // 2. Select Product Card handler
    const cards = document.querySelectorAll('.portfolio-card');
    cards.forEach(card => {
        card.addEventListener('click', () => {
            cards.forEach(c => c.classList.remove('active'));
            card.classList.add('active');
            
            // Adjust card button styles
            cards.forEach(c => {
                const btn = c.querySelector('.btn-select-product');
                btn.className = 'btn btn-outline btn-sm btn-select-product';
            });
            card.querySelector('.btn-select-product').className = 'btn btn-primary btn-sm btn-glow btn-select-product';

            activeProductId = card.getAttribute('data-product');
            document.getElementById('lbl-active-product').innerText = card.querySelector('.card-title').innerText;
            
            // Adjust slider defaults based on product metadata
            if (activeProductId === 'semiconductors') {
                updateSliderRange('slider-price', 100, 200, 150);
            } else if (activeProductId === 'medical_kits') {
                updateSliderRange('slider-price', 50, 110, 80);
            } else if (activeProductId === 'ev_batteries') {
                updateSliderRange('slider-price', 400, 800, 600);
            }
            
            runEvaluation();
        });
    });

    // Helper to change slider boundary properties
    function updateSliderRange(id, min, max, val) {
        const slider = document.getElementById(id);
        slider.min = min;
        slider.max = max;
        slider.value = val;
        document.getElementById('val-price').innerText = `$${val}`;
    }

    // 3. Tab Button Click Handler
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.getElementById(btn.getAttribute('data-tab')).classList.add('active');
            
            // Relayout Plotly charts to adapt to hidden tab container expansions
            if (activeData) {
                Plotly.Plots.resize('chart-elasticity');
                Plotly.Plots.resize('chart-inventory-paths');
                Plotly.Plots.resize('chart-profit-dist');
            }
        });
    });

    // Initialize checkbox listener for live telemetry
    const chkRealtime = document.getElementById('chk-use-realtime');
    const updateSliderStates = () => {
        const isLive = chkRealtime.checked;
        const slidersToLock = ['slider-weather-severity', 'slider-storage-mult', 'slider-stockout-mult'];
        
        slidersToLock.forEach(id => {
            const slider = document.getElementById(id);
            slider.disabled = isLive;
            if (isLive) {
                slider.classList.add('input-slider-disabled');
            } else {
                slider.classList.remove('input-slider-disabled');
            }
        });
        
        const statusDiv = document.getElementById('telemetry-status');
        if (isLive) {
            statusDiv.className = 'telemetry-status-active';
            statusDiv.innerText = 'CONNECTING TELEMETRY...';
        } else {
            statusDiv.className = 'telemetry-status-inactive';
            statusDiv.innerText = 'MANUAL SANDBOX ACTIVE';
        }
    };
    chkRealtime.addEventListener('change', () => {
        updateSliderStates();
        runEvaluation();
    });
    updateSliderStates();

    // 4. Slider real-time label updates
    setupSliderLabel('slider-port-congestion', 'val-port-congestion', '');
    setupSliderLabel('slider-weather-severity', 'val-weather-severity', '');
    setupSliderLabel('slider-price', 'val-price', '$');
    setupSliderLabel('slider-safety-stock', 'val-safety-stock', '', ' days');
    setupSliderLabel('slider-storage-mult', 'val-storage-mult', '', 'x');
    setupSliderLabel('slider-stockout-mult', 'val-stockout-mult', '', 'x');

    function setupSliderLabel(sliderId, labelId, prefix, suffix = '') {
        const slider = document.getElementById(sliderId);
        const lbl = document.getElementById(labelId);
        slider.addEventListener('input', () => {
            lbl.innerText = `${prefix}${slider.value}${suffix}`;
        });
    }

    // 5. Run Evaluation trigger
    document.getElementById('btn-run-simulation').addEventListener('click', runEvaluation);

    // Initial Trigger
    runEvaluation();
});

// -------------------------------------------------------------
// CORE API DATA FLOW & PLOTTING
// -------------------------------------------------------------
async function runEvaluation() {
    // Show Loading Spinners in UI output panels
    document.getElementById('debate-board-content').innerHTML = '<div class="loading-spinner">Executing OLS & Monte Carlo... Please wait.</div>';
    
    // Gather UI parameters
    const payload = {
        product_id: activeProductId,
        use_realtime: document.getElementById('chk-use-realtime').checked,
        port_congestion: parseFloat(document.getElementById('slider-port-congestion').value),
        weather_severity: parseFloat(document.getElementById('slider-weather-severity').value),
        price: parseFloat(document.getElementById('slider-price').value),
        safety_stock_days: parseInt(document.getElementById('slider-safety-stock').value),
        holding_cost_mult: parseFloat(document.getElementById('slider-storage-mult').value),
        stockout_penalty_mult: parseFloat(document.getElementById('slider-stockout-mult').value)
    };

    try {
        const response = await fetch('/api/evaluate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            const errMsg = errData.details || errData.error || "API call failed";
            throw new Error(errMsg);
        }
        
        activeData = await response.json();
        updateDashboardUI();
        
    } catch (err) {
        console.error(err);
        document.getElementById('debate-board-content').innerHTML = `<div class="loading-spinner" style="color:var(--color-danger)">Error running evaluation model: ${err.message}</div>`;
    }
}

function updateDashboardUI() {
    const m = activeData.manual_results;
    const o = activeData.opt_results;
    
    // Sync telemetry indicators
    const tel = activeData.telemetry;
    const statusDiv = document.getElementById('telemetry-status');
    if (tel && tel.active) {
        statusDiv.className = 'telemetry-status-active';
        statusDiv.innerText = 'LIVE DATA INGESTION ACTIVE';
        
        // Update label readouts
        document.getElementById('val-weather-severity').innerText = `${tel.weather_severity} (LIVE)`;
        document.getElementById('val-storage-mult').innerText = `${tel.holding_cost_mult}x (LIVE)`;
        document.getElementById('val-stockout-mult').innerText = `${tel.stockout_penalty_mult}x (LIVE)`;
        
        // Sync slider values
        document.getElementById('slider-weather-severity').value = tel.weather_severity;
        document.getElementById('slider-storage-mult').value = tel.holding_cost_mult;
        document.getElementById('slider-stockout-mult').value = tel.stockout_penalty_mult;
    } else {
        statusDiv.className = 'telemetry-status-inactive';
        statusDiv.innerText = 'MANUAL SANDBOX ACTIVE';
        
        // Restore standard labels
        document.getElementById('val-weather-severity').innerText = document.getElementById('slider-weather-severity').value;
        document.getElementById('val-storage-mult').innerText = `${document.getElementById('slider-storage-mult').value}x`;
        document.getElementById('val-stockout-mult').innerText = `${document.getElementById('slider-stockout-mult').value}x`;
    }
    
    // 1. Update Hero stats
    const deltaProfitPct = ((o.expected_max_profit - m.mean_profit) / Math.max(1, m.mean_profit)) * 100;
    document.getElementById('hero-yield-val').innerText = `${deltaProfitPct >= 0 ? '+' : ''}${deltaProfitPct.toFixed(1)}%`;
    document.getElementById('hero-risk-val').innerText = activeData.logistics_risk.logistics_risk_index.toFixed(2);

    // 2. Populate Metric Cards
    document.getElementById('metric-profit').innerText = `$${m.mean_profit.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}`;
    
    const profitDiff = o.expected_max_profit - m.mean_profit;
    const diffPrefix = profitDiff >= 0 ? '+' : '';
    document.getElementById('metric-profit-delta').className = `metric-change ${profitDiff >= 0 ? 'delta-positive' : 'delta-negative'}`;
    document.getElementById('metric-profit-delta').innerText = `${diffPrefix}$${profitDiff.toLocaleString(undefined, {maximumFractionDigits:0})} vs Manual`;
    
    document.getElementById('metric-stockout').innerText = `${(m.stockout_probability * 100).toFixed(1)}%`;
    const stockoutDiff = m.stockout_probability - o.stockout_probability;
    document.getElementById('metric-stockout-delta').className = `metric-change ${stockoutDiff >= 0 ? 'delta-positive' : 'delta-negative'}`;
    document.getElementById('metric-stockout-delta').innerText = `${stockoutDiff >= 0 ? '-' : '+'}${(Math.abs(stockoutDiff) * 100).toFixed(1)}% Risk exposure`;

    document.getElementById('metric-holding').innerText = `$${m.mean_holding_cost.toLocaleString(undefined, {maximumFractionDigits:0})}`;
    document.getElementById('metric-var').innerText = `$${m.value_at_risk_5pct.toLocaleString(undefined, {maximumFractionDigits:0})}`;

    // 3. Render Agent Debate
    renderDebateSection();

    // 4. Fill OLS Table & Render OLS Chart
    renderOLSElasticity();

    // 5. Render Trajectories (Inventory & Profit Distribution)
    renderStochasticPlots();

    // 6. Fill Comparison Table
    renderComparisonTable();
}

function renderDebateSection() {
    const rawDebate = activeData.agent_debate;
    const lines = rawDebate.split("---");
    const container = document.getElementById('debate-board-content');
    container.innerHTML = '';
    
    if (lines.length >= 3) {
        lines.forEach(section => {
            let className = '';
            let title = '';
            
            if (section.includes("Supply Chain Risk Agent") || section.includes("Supply Chain Buffer Agent")) {
                className = 'db-sc';
                title = '📦 Supply Chain Buffer Agent (Logistics Risk)';
            } else if (section.includes("Financial Controller")) {
                className = 'db-fc';
                title = '📊 Financial Controller Agent (Capital Efficiency)';
            } else if (section.includes("Strategy Commander")) {
                className = 'db-cmd';
                title = '🎖️ Strategy Commander Agent (Operational Consensus)';
            } else {
                return; // Skip other blocks
            }
            
            // Clean markdown blockquotes/headings
            let text = section
                .replace(/#+.*?\n/g, '')
                .replace(/>/g, '')
                .replace(/\*\*/g, '')
                .trim();
                
            const cardHtml = `
                <div class="db-bubble ${className}">
                    <div class="bubble-lbl">${title}</div>
                    <div class="bubble-txt">${text}</div>
                </div>
            `;
            container.insertAdjacentHTML('beforeend', cardHtml);
        });
    } else {
        container.innerHTML = `<div class="db-bubble db-cmd"><div class="bubble-txt">${rawDebate}</div></div>`;
    }
}

function renderOLSElasticity() {
    const f = activeData.fit_summary;
    
    // Populate Diagnostic Table
    const tbody = document.getElementById('ols-tbody');
    tbody.innerHTML = `
        <tr><td>Intercept (α)</td><td>${f.alpha.toFixed(2)}</td><td>${f.p_values.const.toExponential(2)}</td></tr>
        <tr><td>Price Coefficient (β)</td><td>${f.beta.toFixed(3)}</td><td>${f.p_values.price.toExponential(2)}</td></tr>
        <tr><td>High Season (γ₁)</td><td>${f.gamma_season.toFixed(2)}</td><td>${f.p_values.is_high_season.toExponential(2)}</td></tr>
    `;
    
    document.getElementById('val-r2').innerText = f.r_squared.toFixed(4);
    
    // Calculate point elasticity
    const manualPrice = parseFloat(document.getElementById('slider-price').value);
    // Predicted Q = alpha + beta*P
    const predQ = f.alpha + f.beta * manualPrice;
    const currentPed = predQ > 0 ? f.beta * (manualPrice / predQ) : 0;
    document.getElementById('val-ped-coef').innerText = currentPed.toFixed(3);
    
    // Plot Demand Curve
    const prices = activeData.historical_data.price;
    const quantities = activeData.historical_data.quantity;
    
    const pMin = Math.min(...prices) * 0.95;
    const pMax = Math.max(...prices) * 1.05;
    
    const fitPrices = [];
    const fitQuantities = [];
    const steps = 50;
    for (let i = 0; i <= steps; i++) {
        const p = pMin + (i * (pMax - pMin)) / steps;
        fitPrices.push(p);
        // Predict demand at mean high season (0.25)
        fitQuantities.push(f.alpha + f.beta * p + f.gamma_season * 0.25);
    }
    
    const traceScatter = {
        x: prices,
        y: quantities,
        mode: 'markers',
        type: 'scatter',
        name: 'Historical Transact Logs',
        marker: { color: 'rgba(148, 163, 184, 0.4)', size: 6 }
    };
    
    const traceFit = {
        x: fitPrices,
        y: fitQuantities,
        mode: 'lines',
        type: 'scatter',
        name: 'Fitted Demand Curve OLS',
        line: { color: '#38bdf8', width: 3 }
    };
    
    const traceManualPoint = {
        x: [manualPrice],
        y: [predQ],
        mode: 'markers',
        type: 'scatter',
        name: 'Manual Price Target',
        marker: { color: '#f59e0b', size: 12, symbol: 'star' }
    };

    const traceOptPoint = {
        x: [activeData.opt_results.optimal_price],
        y: [f.alpha + f.beta * activeData.opt_results.optimal_price + f.gamma_season * 0.25],
        mode: 'markers',
        type: 'scatter',
        name: 'AI Optimized Price',
        marker: { color: '#10b981', size: 12, symbol: 'diamond' }
    };
    
    const layout = {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#94a3b8', family: 'Outfit' },
        margin: { t: 30, b: 40, l: 50, r: 20 },
        xaxis: { gridcolor: 'rgba(255,255,255,0.05)', title: 'Unit Price ($)' },
        yaxis: { gridcolor: 'rgba(255,255,255,0.05)', title: 'Quantity Demanded' },
        legend: { x: 0.99, y: 0.99, xanchor: 'right', yanchor: 'top' }
    };
    
    Plotly.newPlot('chart-elasticity', [traceScatter, traceFit, traceManualPoint, traceOptPoint], layout, {responsive: true});
}

function renderStochasticPlots() {
    const days = Array.from({length: 14}, (_, i) => i + 1);
    const m = activeData.manual_results;
    const o = activeData.opt_results;
    const cap = activeData.metadata.warehouse_capacity;
    
    // 1. Inventory Trajectories
    const traceCap = {
        x: days,
        y: Array(14).fill(cap),
        mode: 'lines',
        name: 'Warehouse Capacity Limit',
        line: { color: '#ef4444', width: 2, dash: 'dash' }
    };
    
    const traceManualInv = {
        x: days,
        y: m.daily_inventory,
        mode: 'lines+markers',
        name: 'Manual Expected Inventory',
        line: { color: '#f59e0b', width: 3 }
    };
    
    const traceOptInv = {
        x: days,
        y: o.daily_inventory,
        mode: 'lines+markers',
        name: 'AI Optimized Inventory',
        line: { color: '#10b981', width: 3 }
    };
    
    const layoutInv = {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#94a3b8', family: 'Outfit' },
        margin: { t: 20, b: 40, l: 40, r: 20 },
        xaxis: { gridcolor: 'rgba(255,255,255,0.05)', title: 'Planning Horizon Day' },
        yaxis: { gridcolor: 'rgba(255,255,255,0.05)', title: 'Inventory Units' },
        legend: { orientation: 'h', y: 1.15 }
    };
    
    Plotly.newPlot('chart-inventory-paths', [traceCap, traceManualInv, traceOptInv], layoutInv, {responsive: true});
    
    // 2. Profit Distribution Histogram
    const traceManualHist = {
        x: m.trial_profits,
        type: 'histogram',
        name: 'Manual Profits',
        opacity: 0.6,
        marker: { color: '#f59e0b' }
    };
    
    const traceOptHist = {
        x: o.trial_profits,
        type: 'histogram',
        name: 'Optimized Profits',
        opacity: 0.6,
        marker: { color: '#10b981' }
    };
    
    const layoutHist = {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#94a3b8', family: 'Outfit' },
        margin: { t: 20, b: 40, l: 40, r: 20 },
        barmode: 'overlay',
        xaxis: { gridcolor: 'rgba(255,255,255,0.05)', title: 'Net Profit ($)' },
        yaxis: { gridcolor: 'rgba(255,255,255,0.05)', title: 'Trial Count' },
        legend: { orientation: 'h', y: 1.15 },
        shapes: [
            {
                type: 'line',
                x0: m.value_at_risk_5pct, y0: 0, x1: m.value_at_risk_5pct, y1: 1,
                xref: 'x', yref: 'paper',
                line: { color: '#d97706', width: 2, dash: 'dot' }
            },
            {
                type: 'line',
                x0: o.value_at_risk_5pct, y0: 0, x1: o.value_at_risk_5pct, y1: 1,
                xref: 'x', yref: 'paper',
                line: { color: '#059669', width: 2, dash: 'dot' }
            }
        ]
    };
    
    Plotly.newPlot('chart-profit-dist', [traceManualHist, traceOptHist], layoutHist, {responsive: true});
}

function renderComparisonTable() {
    const m = activeData.manual_results;
    const o = activeData.opt_results;
    const manualPrice = parseFloat(document.getElementById('slider-price').value);
    const manualSS = parseInt(document.getElementById('slider-safety-stock').value);
    
    const tbody = document.getElementById('comparison-tbody');
    
    const fmt = (val) => `$${val.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    const delta = (v1, v2) => {
        const diff = v2 - v1;
        const color = diff >= 0 ? 'color:var(--color-success)' : 'color:var(--color-danger)';
        return `<span style="${color}">${diff >= 0 ? '+' : ''}${diff.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}</span>`;
    };
    const deltaStockout = (s1, s2) => {
        const diff = (s2 - s1) * 100;
        const color = diff <= 0 ? 'color:var(--color-success)' : 'color:var(--color-danger)';
        return `<span style="${color}">${diff >= 0 ? '+' : ''}${diff.toFixed(1)}%</span>`;
    };
    
    tbody.innerHTML = `
        <tr>
            <td>Operational Pricing</td>
            <td>$${manualPrice.toFixed(2)}</td>
            <td>$${o.optimal_price.toFixed(2)}</td>
            <td>${delta(manualPrice, o.optimal_price)}</td>
        </tr>
        <tr>
            <td>Safety Stock Buffer (Days)</td>
            <td>${manualSS} days</td>
            <td>${o.optimal_safety_stock_days} days</td>
            <td>${o.optimal_safety_stock_days - manualSS} days</td>
        </tr>
        <tr>
            <td>Expected Net profit</td>
            <td>${fmt(m.mean_profit)}</td>
            <td>${fmt(o.expected_max_profit)}</td>
            <td>${delta(m.mean_profit, o.expected_max_profit)}</td>
        </tr>
        <tr>
            <td>Expected Revenue Yield</td>
            <td>${fmt(m.mean_revenue)}</td>
            <td>${fmt(o.expected_revenue)}</td>
            <td>${delta(m.mean_revenue, o.expected_revenue)}</td>
        </tr>
        <tr>
            <td>Expected Storage Cost</td>
            <td>${fmt(m.mean_holding_cost)}</td>
            <td>${fmt(o.expected_holding_cost)}</td>
            <td>${delta(m.mean_holding_cost, o.expected_holding_cost)}</td>
        </tr>
        <tr>
            <td>Expected Stockout Cost</td>
            <td>${fmt(m.mean_stockout_cost)}</td>
            <td>${fmt(o.expected_stockout_cost)}</td>
            <td>${delta(m.mean_stockout_cost, o.expected_stockout_cost)}</td>
        </tr>
        <tr>
            <td>Stockout Frequency (%)</td>
            <td>${(m.stockout_probability * 100).toFixed(1)}%</td>
            <td>${(o.stockout_probability * 100).toFixed(1)}%</td>
            <td>${deltaStockout(m.stockout_probability, o.stockout_probability)}</td>
        </tr>
    `;
}

function triggerAgentFocus(agentKey) {
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        if (btn.getAttribute('data-tab') === 'tab-debate') {
            btn.click();
        }
    });
    
    // Highlight the selected agent bubble
    let selector = '';
    if (agentKey === 'sc') selector = '.db-sc';
    else if (agentKey === 'fc') selector = '.db-fc';
    else if (agentKey === 'cmd') selector = '.db-cmd';
    
    const element = document.querySelector(selector);
    if (element) {
        element.style.transform = 'scale(1.02)';
        element.style.boxShadow = '0 0 20px rgba(255,255,255,0.08)';
        setTimeout(() => {
            element.style.transform = '';
            element.style.boxShadow = '';
        }, 1200);
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}
