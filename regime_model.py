import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.mixture import GaussianMixture

class MarketRegimeModel:
    """
    Encapsulates Gaussian Mixture Model logic for market regime detection.
    Identifies 'Bull/Calm', 'Transition', and 'Crisis/Crash' regimes based on
    Log_Sector_Vol and Log_VIX.
    """
    
    def __init__(self, n_components=3, random_state=42):
        self.n_components = n_components
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.model = GaussianMixture(n_components=n_components, random_state=random_state)
        self.mapping = {}

    def fit_predict(self, data: pd.DataFrame, feature_cols=['Log_Sector_Vol', 'Log_VIX']):
        """
        Fits the model to the data and returns regime labels.
        Applies mapping logic where highest average Log_VIX = 'Crisis/Crash'.
        """
        # 1. Scale
        features = data[feature_cols]
        scaled_feat = self.scaler.fit_transform(features)
        
        # 2. Fit GMM
        regimes = self.model.fit_predict(scaled_feat)
        
        # 3. Determine Mapping (Sort by VIX to ensure consistency)
        # Create temp DF to calculate means
        temp_df = data.copy()
        temp_df['Regime_Raw'] = regimes
        
        # Calculate mean VIX for each cluster
        regime_stats = temp_df.groupby('Regime_Raw')[feature_cols[1]].mean().sort_values()
        
        # Assume 3 components: Lowest VIX -> Bull, Mid -> Transition, High -> Crisis
        if self.n_components == 3:
            self.mapping = {
                regime_stats.index[0]: 'Bull/Calm',
                regime_stats.index[1]: 'Transition',
                regime_stats.index[2]: 'Crisis/Crash'
            }
        else:
            # Fallback for non-3 component models, just map by VIX intensity
            self.mapping = {idx: f"Regime_{i} (VIX_Rank_{i})" for i, idx in enumerate(regime_stats.index)}

        # 4. Map Labels
        return pd.Series(regimes, index=data.index).map(self.mapping)
