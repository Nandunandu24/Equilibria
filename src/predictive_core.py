import numpy as np
import pandas as pd
import statsmodels.api as sm

class PredictiveCore:
    """
    Tier 2: Predictive Analytics Core
    Fits Ordinary Least Squares (OLS) regression models to establish price elasticity
    and forecasts future baseline demand based on seasonal context flags.
    """
    
    def __init__(self):
        self.model = None
        self.results = None
        self.alpha = None
        self.beta = None
        self.gamma_season = None
        self.gamma_promo = None
        
    def fit_demand_elasticity(self, df):
        """
        Fits OLS regression: Q = alpha + beta*Price + gamma_1*is_high_season + gamma_2*is_promo + epsilon
        Returns a dict of model performance and parameters.
        """
        # Prepare variables
        X = df[["price", "is_high_season", "is_promo"]].copy()
        X = sm.add_constant(X)
        y = df["quantity"]
        
        # Fit OLS
        self.model = sm.OLS(y, X)
        self.results = self.model.fit()
        
        # Extract coefficients
        self.alpha = self.results.params["const"]
        self.beta = self.results.params["price"]
        self.gamma_season = self.results.params["is_high_season"]
        self.gamma_promo = self.results.params["is_promo"]
        
        # Model diagnostics
        r_squared = self.results.rsquared
        adj_r_squared = self.results.rsquared_adj
        f_pvalue = self.results.f_pvalue
        
        # P-values and standard errors for coefficients
        p_values = self.results.pvalues.to_dict()
        std_errs = self.results.bse.to_dict()
        
        # Mean elasticities
        mean_price = df["price"].mean()
        mean_qty = df["quantity"].mean()
        mean_elasticity = self.beta * (mean_price / mean_qty)
        
        return {
            "alpha": self.alpha,
            "beta": self.beta,
            "gamma_season": self.gamma_season,
            "gamma_promo": self.gamma_promo,
            "r_squared": r_squared,
            "adj_r_squared": adj_r_squared,
            "f_pvalue": f_pvalue,
            "p_values": p_values,
            "std_errs": std_errs,
            "mean_elasticity": mean_elasticity,
            "summary_text": self.results.summary().as_text()
        }
        
    def calculate_elasticity(self, price, predicted_qty):
        """Calculates point price elasticity: E = beta * (P / Q)"""
        if self.beta is None:
            raise ValueError("Model is not fitted yet. Call fit_demand_elasticity first.")
        if predicted_qty <= 0:
            return 0.0
        return self.beta * (price / predicted_qty)
        
    def predict_demand(self, price, is_high_season, is_promo):
        """
        Predicts expected demand quantity for given conditions.
        """
        if self.beta is None:
            raise ValueError("Model is not fitted yet. Call fit_demand_elasticity first.")
            
        qty = self.alpha + self.beta * price + self.gamma_season * is_high_season + self.gamma_promo * is_promo
        return max(0.0, qty)
        
    def generate_14day_forecast(self, future_price, base_seasonality=0.25, base_promo=0.10, seed=42):
        """
        Generates a 14-day baseline forecast under a constant or variable pricing policy.
        Returns a DataFrame representing dates and predicted demand.
        """
        if self.beta is None:
            raise ValueError("Model is not fitted yet.")
            
        rng = np.random.default_rng(seed)
        
        dates = [pd.Timestamp.now() + pd.Timedelta(days=i) for i in range(14)]
        
        # Simulate future seasonalities and promotions for the next 14 days
        # E.g., weekends (Friday=4, Saturday=5) are high season, plus random promos
        future_season = []
        future_promo = []
        
        for d in dates:
            # Friday & Saturday (4 & 5)
            is_weekend = 1 if d.weekday() in [4, 5] else 0
            future_season.append(is_weekend)
            # 10% chance of promotion on other days
            future_promo.append(1 if (not is_weekend and rng.random() < base_promo) else 0)
            
        # Pricing policy: check if future_price is list or scaler
        if isinstance(future_price, (list, np.ndarray)):
            prices = future_price
        else:
            prices = [future_price] * 14
            
        predicted_qtys = []
        elasticities = []
        
        for p, s, pr in zip(prices, future_season, future_promo):
            qty = self.predict_demand(p, s, pr)
            predicted_qtys.append(round(qty))
            elasticities.append(self.calculate_elasticity(p, qty))
            
        forecast_df = pd.DataFrame({
            "day": range(1, 15),
            "date": [d.strftime("%Y-%m-%d") for d in dates],
            "price": prices,
            "is_high_season": future_season,
            "is_promo": future_promo,
            "forecasted_demand": predicted_qtys,
            "elasticity": np.round(elasticities, 3)
        })
        
        return forecast_df
