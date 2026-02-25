"""
REGIME-BASED PORTFOLIO OPTIMIZATION SYSTEM - COMPLETE MODULES
==============================================================

File 1 of 2: Core System Modules

⚙️ EDIT THESE THREE PARAMETERS BELOW:
• SHORT_TERM_TREND = 21 days
• LONG_TERM_TREND = 63 days
• N_REGIMES = 4

All modules automatically use these settings.

Author: Regime Trading System
Date: January 2026
Version: 1.0 (Production)
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import squareform
from hmmlearn import hmm
from sklearn.cluster import KMeans
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Set plotting style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


# ============================================================================
# ⚙️ CONFIGURATION - EDIT THESE THREE PARAMETERS
# ============================================================================

class Config:
    """Global configuration - EASILY EDITABLE"""
    
    # ✏️ MAIN PARAMETERS - EDIT THESE THREE
    SHORT_TERM_TREND = 21   # Days for short-term trend (default: 21 = ~1 month)
    LONG_TERM_TREND = 63    # Days for long-term trend & rebalancing (default: 63 = quarterly)
    N_REGIMES = 4           # Number of market regimes (options: 2, 3, or 4)
    
    # Advanced Parameters (usually don't need to change)
    MAX_POSITION_SIZE = 0.15    # 15% max per asset
    MIN_POSITION_SIZE = 0.02    # 2% min per asset
    TRANSACTION_COST = 0.001    # 0.1% per trade
    RISK_AVERSION = 1.0         # Risk aversion in optimization
    SHRINKAGE = 0.6             # Regularization strength (0.6 = strong)
    INITIAL_CAPITAL = 100000    # Starting capital
    N_SIMULATIONS = 1000        # Monte Carlo simulations


# ============================================================================
# MODULE 1: DATA GENERATION
# ============================================================================

class DataGenerator:
    """Generate synthetic market data using Geometric Brownian Motion"""
    
    @staticmethod
    def generate_gbm(S0: float, mu: float, sigma: float, T: float, 
                     dt: float, n_paths: int = 1) -> np.ndarray:
        """
        Generate Geometric Brownian Motion paths
        
        Formula: dS = μS dt + σS dW
        
        Parameters:
        -----------
        S0 : float - Initial price
        mu : float - Drift (expected return)
        sigma : float - Volatility
        T : float - Time horizon in years
        dt : float - Time step (e.g., 1/252 for daily)
        n_paths : int - Number of paths to generate
        
        Returns:
        --------
        np.ndarray : Array of shape (n_steps, n_paths)
        """
        n_steps = int(T / dt)
        t = np.linspace(0, T, n_steps)
        
        # Generate random shocks
        W = np.random.standard_normal(size=(n_steps, n_paths))
        W = np.cumsum(W, axis=0) * np.sqrt(dt)
        
        # GBM formula: S(t) = S0 * exp((μ - σ²/2)t + σW(t))
        drift = (mu - 0.5 * sigma**2) * t[:, np.newaxis]
        diffusion = sigma * W
        S = S0 * np.exp(drift + diffusion)
        
        return S
    
    @staticmethod
    def generate_correlated_gbm(S0: List[float], mu: List[float], 
                                sigma: List[float], corr_matrix: np.ndarray,
                                T: float, dt: float) -> pd.DataFrame:
        """
        Generate correlated GBM for multiple assets
        
        Uses Cholesky decomposition to create correlated Brownian motions
        """
        n_assets = len(S0)
        n_steps = int(T / dt)
        
        # Cholesky decomposition for correlation
        L = np.linalg.cholesky(corr_matrix)
        
        # Generate correlated random shocks
        Z = np.random.standard_normal(size=(n_steps, n_assets))
        W = np.cumsum(Z @ L.T, axis=0) * np.sqrt(dt)
        
        # Generate prices for each asset
        prices = np.zeros((n_steps, n_assets))
        t = np.linspace(0, T, n_steps)
        
        for i in range(n_assets):
            drift = (mu[i] - 0.5 * sigma[i]**2) * t
            diffusion = sigma[i] * W[:, i]
            prices[:, i] = S0[i] * np.exp(drift + diffusion)
        
        return pd.DataFrame(prices, columns=[f'Asset_{i}' for i in range(n_assets)])
    
    @staticmethod
    def generate_regime_switching_data(n_days: int = 1260, 
                                       sectors: List[str] = None,
                                       n_regimes: int = None) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Generate synthetic data with regime switches
        
        Automatically adapts to Config.N_REGIMES
        """
        if sectors is None:
            sectors = ['XLK', 'XLF', 'XLV', 'XLY', 'XLP', 'XLE', 
                      'XLI', 'XLB', 'XLRE', 'XLU', 'XLC']
        
        if n_regimes is None:
            n_regimes = Config.N_REGIMES
        
        n_sectors = len(sectors)
        
        # Define regime characteristics (adapts to n_regimes)
        if n_regimes == 2:
            regimes = {
                0: {'mu': -0.05, 'sigma': 0.30, 'corr': 0.7},  # Bear
                1: {'mu': 0.10, 'sigma': 0.18, 'corr': 0.4},   # Bull
            }
            probs = [0.3, 0.7]
        elif n_regimes == 3:
            regimes = {
                0: {'mu': -0.10, 'sigma': 0.35, 'corr': 0.8},  # Crisis
                1: {'mu': 0.12, 'sigma': 0.15, 'corr': 0.3},   # Bull
                2: {'mu': 0.02, 'sigma': 0.22, 'corr': 0.5},   # Normal
            }
            probs = [0.15, 0.35, 0.50]
        else:  # 4 regimes (default)
            regimes = {
                0: {'mu': -0.10, 'sigma': 0.35, 'corr': 0.8},  # Crisis
                1: {'mu': 0.12, 'sigma': 0.15, 'corr': 0.3},   # Bull
                2: {'mu': 0.05, 'sigma': 0.20, 'corr': 0.5},   # Normal
                3: {'mu': -0.02, 'sigma': 0.25, 'corr': 0.6}   # Bear
            }
            probs = [0.1, 0.3, 0.4, 0.2]
        
        # Generate regime sequence
        regime_sequence = []
        current_regime = n_regimes // 2  # Start in middle regime
        regime_length = 0
        min_regime_length = 60
        max_regime_length = 180
        
        for _ in range(n_days):
            if regime_length >= np.random.randint(min_regime_length, max_regime_length):
                current_regime = np.random.choice(list(regimes.keys()), p=probs)
                regime_length = 0
            regime_sequence.append(current_regime)
            regime_length += 1
        
        # Generate prices with regime switches
        prices = np.zeros((n_days, n_sectors))
        prices[0] = 100  # Initial price
        
        for day in range(1, n_days):
            regime = regime_sequence[day]
            regime_params = regimes[regime]
            
            # Create correlation matrix
            corr = regime_params['corr']
            corr_matrix = np.full((n_sectors, n_sectors), corr)
            np.fill_diagonal(corr_matrix, 1.0)
            
            # Generate correlated returns
            L = np.linalg.cholesky(corr_matrix)
            Z = np.random.standard_normal(n_sectors)
            eps = L @ Z
            
            # Daily returns
            returns = regime_params['mu']/252 + regime_params['sigma']/np.sqrt(252) * eps
            prices[day] = prices[day-1] * (1 + returns)
        
        # Create DataFrame
        df = pd.DataFrame(prices, columns=sectors)
        df['SPY'] = df.mean(axis=1)  # Synthetic market index
        
        return df, pd.Series(regime_sequence, name='true_regime')


# ============================================================================
# MODULE 2: REGIME DETECTION (Uses Config parameters)
# ============================================================================

class RegimeDetector:
    """Detect market regimes using HMM with configurable trend periods"""
    
    def __init__(self, n_regimes: int = None, 
                 short_term_window: int = None,
                 long_term_window: int = None):
        """
        Initialize regime detector
        
        Uses Config values if not specified
        """
        self.n_regimes = n_regimes or Config.N_REGIMES
        self.short_term_window = short_term_window or Config.SHORT_TERM_TREND
        self.long_term_window = long_term_window or Config.LONG_TERM_TREND
        self.model = None
        self.scaler_mean = None
        self.scaler_std = None
    
    def prepare_features(self, data: pd.DataFrame, market_col: str = 'SPY') -> np.ndarray:
        """
        Prepare features using Config.SHORT_TERM_TREND and Config.LONG_TERM_TREND
        
        Features:
        - Returns
        - Volatility (short-term window)
        - Short-term trend
        - Long-term trend
        """
        if market_col not in data.columns:
            market_col = data.columns[0]
        
        returns = data[market_col].pct_change()
        
        features = pd.DataFrame({
            'returns': returns,
            'volatility_st': returns.rolling(self.short_term_window).std(),
            'trend_st': data[market_col].pct_change(self.short_term_window),
            'trend_lt': data[market_col].pct_change(self.long_term_window)
        })
        
        features = features.dropna()
        features = features.replace([np.inf, -np.inf], np.nan)
        features = features.ffill().bfill()
        
        return features.values
    
    def fit(self, data: pd.DataFrame, market_col: str = 'SPY') -> 'RegimeDetector':
        """Fit HMM with robust error handling"""
        X = self.prepare_features(data, market_col)
        
        # Standardize features
        self.scaler_mean = X.mean(axis=0)
        self.scaler_std = X.std(axis=0)
        self.scaler_std[self.scaler_std == 0] = 1.0
        
        X_scaled = (X - self.scaler_mean) / self.scaler_std
        
        # Try different covariance types
        covariance_types = ['diag', 'spherical']
        
        for cov_type in covariance_types:
            try:
                self.model = hmm.GaussianHMM(
                    n_components=self.n_regimes,
                    covariance_type=cov_type,
                    n_iter=100,
                    random_state=42,
                    init_params='stmc',
                    params='stmc'
                )
                
                self.model.fit(X_scaled)
                print(f"✓ HMM converged using '{cov_type}' covariance ({self.n_regimes} regimes)")
                print(f"  Short-term trend: {self.short_term_window} days")
                print(f"  Long-term trend: {self.long_term_window} days")
                break
                
            except (ValueError, np.linalg.LinAlgError):
                if cov_type == covariance_types[-1]:
                    # Fallback to K-means
                    print(f"⚠️  HMM failed, using K-means clustering fallback")
                    kmeans = KMeans(n_clusters=self.n_regimes, random_state=42, n_init=10)
                    kmeans.fit(X_scaled)
                    self.model = kmeans
                    print(f"✓ Using K-means clustering ({self.n_regimes} regimes)")
                else:
                    continue
        
        return self
    
    def predict(self, data: pd.DataFrame, market_col: str = 'SPY') -> pd.Series:
        """Predict regimes"""
        X = self.prepare_features(data, market_col)
        X_scaled = (X - self.scaler_mean) / self.scaler_std
        
        regimes = self.model.predict(X_scaled)
        
        # Align with original data index
        feature_index = data.index[max(self.short_term_window, self.long_term_window):]
        return pd.Series(regimes, index=feature_index, name='regime')


# ============================================================================
# MODULE 3: PORTFOLIO OPTIMIZATION (Heavy Regularization)
# ============================================================================

class PortfolioOptimizer:
    """Optimize portfolio weights with heavy regularization"""
    
    @staticmethod
    def calculate_regime_statistics(data: pd.DataFrame, regime_mask: pd.Series,
                                    sectors: List[str]) -> Dict:
        """Calculate returns and covariance for a regime"""
        regime_data = data.loc[regime_mask, sectors]
        returns = regime_data.pct_change().dropna()
        
        return {
            'mean_returns': returns.mean(),
            'cov_matrix': returns.cov(),
            'n_samples': len(returns)
        }
    
    @staticmethod
    def optimize_weights(mean_returns: pd.Series, cov_matrix: pd.DataFrame,
                        risk_aversion: float = None,
                        shrinkage: float = None) -> np.ndarray:
        """
        Mean-variance optimization with Ledoit-Wolf shrinkage
        
        Uses Config.RISK_AVERSION and Config.SHRINKAGE if not specified
        """
        if risk_aversion is None:
            risk_aversion = Config.RISK_AVERSION
        if shrinkage is None:
            shrinkage = Config.SHRINKAGE
        
        n_assets = len(mean_returns)
        
        # Apply shrinkage to covariance (Ledoit-Wolf)
        cov_values = cov_matrix.values
        diag_cov = np.diag(np.diag(cov_values))
        cov_shrunk = (1 - shrinkage) * cov_values + shrinkage * diag_cov
        
        # Shrink returns toward zero (skepticism)
        mean_shrunk = mean_returns.values * (1 - shrinkage * 0.5)
        
        # Add regularization
        cov_regularized = cov_shrunk + np.eye(n_assets) * 1e-5
        
        try:
            inv_cov = np.linalg.inv(cov_regularized)
            weights = inv_cov @ mean_shrunk / risk_aversion
            
            # Normalize
            weights = weights / weights.sum()
            
            # Apply constraints from Config
            weights = np.maximum(weights, 0)
            weights = np.minimum(weights, Config.MAX_POSITION_SIZE)
            weights[weights < Config.MIN_POSITION_SIZE] = 0
            
            # Re-normalize
            if weights.sum() > 0:
                weights = weights / weights.sum()
            else:
                weights = np.ones(n_assets) / n_assets
            
        except np.linalg.LinAlgError:
            weights = np.ones(n_assets) / n_assets
        
        return weights
    
    @staticmethod
    def optimize_all_regimes(data: pd.DataFrame, regimes: pd.Series,
                            sectors: List[str]) -> Dict[int, np.ndarray]:
        """Optimize weights for all regimes"""
        common_index = data.index.intersection(regimes.index)
        data_aligned = data.loc[common_index]
        regimes_aligned = regimes.loc[common_index]
        
        available_sectors = [s for s in sectors if s in data_aligned.columns]
        regime_weights = {}
        
        for regime in sorted(regimes_aligned.unique()):
            mask = (regimes_aligned == regime)
            
            # Need sufficient data (increased from 30 to 60)
            if mask.sum() < 60:
                regime_weights[regime] = np.ones(len(available_sectors)) / len(available_sectors)
                continue
            
            stats = PortfolioOptimizer.calculate_regime_statistics(
                data_aligned, mask, available_sectors
            )
            
            weights = PortfolioOptimizer.optimize_weights(
                stats['mean_returns'],
                stats['cov_matrix']
            )
            
            regime_weights[regime] = weights
        
        return regime_weights


# ============================================================================
# MODULE 4: BACKTESTING (Uses Config.LONG_TERM_TREND for rebalancing)
# ============================================================================

class Backtester:
    """Backtest regime-based strategy"""
    
    def __init__(self, rebalance_period: int = None, transaction_cost: float = None):
        """
        Initialize backtester
        
        Uses Config values if not specified
        """
        self.rebalance_period = rebalance_period or Config.LONG_TERM_TREND
        self.transaction_cost = transaction_cost or Config.TRANSACTION_COST
    
    def run_backtest(self, data: pd.DataFrame, regimes: pd.Series,
                    regime_weights: Dict[int, np.ndarray],
                    sectors: List[str], initial_capital: float = None) -> pd.DataFrame:
        """Run backtest with regime-based rebalancing"""
        if initial_capital is None:
            initial_capital = Config.INITIAL_CAPITAL
        
        common_index = data.index.intersection(regimes.index)
        data_aligned = data.loc[common_index]
        regimes_aligned = regimes.loc[common_index]
        
        available_sectors = [s for s in sectors if s in data_aligned.columns]
        
        portfolio_value = initial_capital
        positions = np.zeros(len(available_sectors))
        results = []
        last_rebalance = 0
        
        for i, date in enumerate(data_aligned.index):
            current_regime = regimes_aligned.iloc[i]
            days_since_rebalance = i - last_rebalance
            
            if days_since_rebalance >= self.rebalance_period or i == 0:
                old_weights = positions / positions.sum() if positions.sum() > 0 else np.zeros_like(positions)
                new_weights = regime_weights.get(current_regime, 
                                                np.ones(len(available_sectors)) / len(available_sectors))
                
                # Calculate turnover and costs
                turnover = np.abs(new_weights - old_weights).sum()
                costs = portfolio_value * turnover * self.transaction_cost
                portfolio_value -= costs
                
                # Update positions
                positions = new_weights * portfolio_value / data_aligned.loc[date, available_sectors].values
                last_rebalance = i
            
            # Calculate portfolio value
            portfolio_value = (positions * data_aligned.loc[date, available_sectors].values).sum()
            
            results.append({
                'date': date,
                'portfolio_value': portfolio_value,
                'regime': current_regime,
                'turnover': turnover if days_since_rebalance == 0 else 0
            })
        
        return pd.DataFrame(results).set_index('date')
    
    def run_benchmark(self, data: pd.DataFrame, market_col: str = 'SPY',
                     initial_capital: float = None) -> pd.DataFrame:
        """Run buy-and-hold benchmark"""
        if initial_capital is None:
            initial_capital = Config.INITIAL_CAPITAL
        
        returns = data[market_col].pct_change()
        # Fill first NaN with 0 (no return on first day)
        returns = returns.fillna(0)
        portfolio_value = initial_capital * (1 + returns).cumprod()
        
        return pd.DataFrame({
            'portfolio_value': portfolio_value,
            'strategy': 'Buy & Hold'
        })


# ============================================================================
# MODULE 4B: WALK-FORWARD BACKTESTING (NO LOOK-AHEAD BIAS)
# ============================================================================

class WalkForwardBacktester:
    """
    Walk-forward backtester with NO look-ahead bias
    
    This is the CORRECT way to backtest:
    - Only uses data available up to current time
    - Retrains model at each rebalancing period
    - No future data leakage
    
    Performance will be LOWER but REALISTIC compared to biased version.
    """
    
    def __init__(self, 
                 training_window: int = None,  # None = expanding window
                 rebalance_period: int = None,
                 min_training_days: int = 252,
                 transaction_cost: float = None):
        """
        Parameters:
        -----------
        training_window : int or None
            Size of training window in days
            - None: Expanding window (use all past data)
            - int: Rolling window (use last N days)
        rebalance_period : int
            Days between rebalancing
        min_training_days : int
            Minimum days needed before starting backtest (default: 252 = 1 year)
        transaction_cost : float
            Cost per dollar of turnover
        """
        self.training_window = training_window  # None = expanding
        self.rebalance_period = rebalance_period or Config.LONG_TERM_TREND
        self.min_training_days = min_training_days
        self.transaction_cost = transaction_cost or Config.TRANSACTION_COST
    
    def run_backtest(self, data: pd.DataFrame, sectors: List[str],
                    initial_capital: float = None, verbose: bool = True) -> pd.DataFrame:
        """
        Run walk-forward backtest with NO look-ahead bias
        
        At each rebalancing:
        1. Use ONLY past data for training
        2. Detect current regime
        3. Optimize weights on past regime data
        4. Hold until next rebalance
        
        Returns:
        --------
        pd.DataFrame with columns: date, portfolio_value, regime, method
        """
        if initial_capital is None:
            initial_capital = Config.INITIAL_CAPITAL
        
        available_sectors = [s for s in sectors if s in data.columns]
        n_sectors = len(available_sectors)
        
        portfolio_value = initial_capital
        positions = np.zeros(n_sectors)
        results = []
        
        rebalance_dates = []
        current_regime = None
        
        # Start after minimum training period
        start_idx = self.min_training_days
        
        if verbose:
            print(f"\n{'='*80}")
            print(f"WALK-FORWARD BACKTEST (No Look-Ahead Bias)")
            print(f"{'='*80}")
            print(f"Training window: {'Expanding' if self.training_window is None else f'{self.training_window} days'}")
            print(f"Rebalance period: {self.rebalance_period} days")
            print(f"Minimum training: {self.min_training_days} days")
            print(f"Start date: {data.index[start_idx].date()}")
            print(f"End date: {data.index[-1].date()}")
            print(f"Total days: {len(data) - start_idx}")
        
        for i in range(start_idx, len(data)):
            date = data.index[i]
            
            # Check if we need to rebalance
            is_rebalance_day = (i == start_idx or 
                               (i - start_idx) % self.rebalance_period == 0)
            
            if is_rebalance_day:
                # CRITICAL: Only use data UP TO current date
                if self.training_window is None:
                    # Expanding window: use all past data
                    training_data = data.iloc[:i]
                else:
                    # Rolling window: use last N days
                    start_train = max(0, i - self.training_window)
                    training_data = data.iloc[start_train:i]
                
                if verbose and len(rebalance_dates) % 10 == 0:
                    print(f"  Rebalancing {len(rebalance_dates)+1}: {date.date()}, "
                          f"training on {len(training_data)} days")
                
                # Step 1: Detect regimes using ONLY past data
                detector = RegimeDetector()
                try:
                    detector.fit(training_data, market_col='SPY')
                    regimes_past = detector.predict(training_data, market_col='SPY')
                    
                    # Current regime = last detected regime
                    current_regime = regimes_past.iloc[-1]
                    
                    # Step 2: Optimize weights for current regime using ONLY past data
                    regime_mask = (regimes_past == current_regime)
                    
                    if regime_mask.sum() >= 30:  # Need sufficient data
                        stats = PortfolioOptimizer.calculate_regime_statistics(
                            training_data, regime_mask, available_sectors
                        )
                        new_weights = PortfolioOptimizer.optimize_weights(
                            stats['mean_returns'],
                            stats['cov_matrix']
                        )
                    else:
                        # Not enough data for this regime, use equal weights
                        new_weights = np.ones(n_sectors) / n_sectors
                
                except Exception as e:
                    if verbose:
                        print(f"    Warning: Regime detection failed at {date.date()}, using equal weights")
                    new_weights = np.ones(n_sectors) / n_sectors
                    current_regime = -1
                
                # Calculate turnover and costs
                old_weights = positions / positions.sum() if positions.sum() > 0 else np.zeros(n_sectors)
                turnover = np.abs(new_weights - old_weights).sum()
                costs = portfolio_value * turnover * self.transaction_cost
                portfolio_value -= costs
                
                # Update positions
                current_prices = data.loc[date, available_sectors].values
                positions = new_weights * portfolio_value / current_prices
                
                rebalance_dates.append(date)
            
            # Calculate portfolio value for this day
            current_prices = data.loc[date, available_sectors].values
            portfolio_value = (positions * current_prices).sum()
            
            results.append({
                'date': date,
                'portfolio_value': portfolio_value,
                'regime': current_regime if current_regime is not None else -1,
                'method': 'walk_forward'
            })
        
        if verbose:
            print(f"\n✓ Walk-forward backtest complete!")
            print(f"  Total rebalances: {len(rebalance_dates)}")
            print(f"  Final portfolio value: ${portfolio_value:,.2f}")
            print(f"  Total return: {(portfolio_value/initial_capital - 1)*100:.2f}%")
        
        return pd.DataFrame(results).set_index('date')


# ============================================================================
# MODULE 4C: DATA BOOTSTRAPPING
# ============================================================================

class BootstrapGenerator:
    """
    Generate bootstrapped samples for robust testing
    
    Methods:
    1. Block bootstrap: Preserve time-series structure
    2. Residual bootstrap: Preserve statistical properties
    3. Parametric bootstrap: Generate from fitted models
    """
    
    @staticmethod
    def block_bootstrap(data: pd.DataFrame, n_samples: int = 100, 
                       block_size: int = 21) -> List[pd.DataFrame]:
        """
        Block bootstrap for time series
        
        Preserves temporal structure by resampling blocks of consecutive days
        
        Parameters:
        -----------
        data : pd.DataFrame
            Original data
        n_samples : int
            Number of bootstrap samples to generate
        block_size : int
            Size of each block (default: 21 = 1 month)
        
        Returns:
        --------
        List of bootstrapped DataFrames
        """
        n_days = len(data)
        n_blocks = n_days // block_size
        
        samples = []
        
        for _ in range(n_samples):
            # Randomly sample blocks with replacement
            block_indices = np.random.choice(n_blocks, size=n_blocks, replace=True)
            
            # Concatenate blocks
            bootstrap_data = []
            for block_idx in block_indices:
                start = block_idx * block_size
                end = min(start + block_size, n_days)
                bootstrap_data.append(data.iloc[start:end])
            
            # Combine into single DataFrame
            boot_df = pd.concat(bootstrap_data, ignore_index=True)
            boot_df.index = data.index[:len(boot_df)]  # Reset index
            
            samples.append(boot_df)
        
        return samples
    
    @staticmethod
    def residual_bootstrap(data: pd.DataFrame, sectors: List[str],
                          n_samples: int = 100) -> List[pd.DataFrame]:
        """
        Residual bootstrap: Fit model, resample residuals
        
        Better preserves statistical properties while generating new scenarios
        
        Parameters:
        -----------
        data : pd.DataFrame
            Original data
        sectors : List[str]
            Sector columns to bootstrap
        n_samples : int
            Number of samples
        
        Returns:
        --------
        List of bootstrapped DataFrames
        """
        samples = []
        
        # Calculate returns
        returns = data[sectors].pct_change().dropna()
        
        # Fit simple model: mean + residuals
        mean_returns = returns.mean()
        residuals = returns - mean_returns
        
        for _ in range(n_samples):
            # Resample residuals with replacement
            boot_residuals = residuals.sample(n=len(residuals), replace=True)
            boot_residuals.index = residuals.index
            
            # Reconstruct returns
            boot_returns = mean_returns + boot_residuals
            
            # Reconstruct prices
            boot_prices = (1 + boot_returns).cumprod() * data[sectors].iloc[0]
            
            # Add SPY if present
            if 'SPY' in data.columns:
                boot_prices['SPY'] = boot_prices[sectors].mean(axis=1)
            
            samples.append(boot_prices)
        
        return samples
    
    @staticmethod
    def parametric_bootstrap(data: pd.DataFrame, sectors: List[str],
                            n_samples: int = 100) -> List[pd.DataFrame]:
        """
        Parametric bootstrap: Fit distribution, generate new samples
        
        Assumes multivariate normal distribution of returns
        
        Parameters:
        -----------
        data : pd.DataFrame
            Original data
        sectors : List[str]
            Sector columns
        n_samples : int
            Number of samples
        
        Returns:
        --------
        List of bootstrapped DataFrames
        """
        samples = []
        
        # Calculate returns
        returns = data[sectors].pct_change().dropna()
        
        # Estimate mean and covariance
        mu = returns.mean().values
        sigma = returns.cov().values
        
        n_days = len(returns)
        
        for _ in range(n_samples):
            # Generate from multivariate normal
            boot_returns = np.random.multivariate_normal(mu, sigma, size=n_days)
            boot_returns_df = pd.DataFrame(boot_returns, columns=sectors, index=returns.index)
            
            # Reconstruct prices
            boot_prices = (1 + boot_returns_df).cumprod() * data[sectors].iloc[0]
            
            # Add SPY
            if 'SPY' in data.columns:
                boot_prices['SPY'] = boot_prices[sectors].mean(axis=1)
            
            samples.append(boot_prices)
        
        return samples


# ============================================================================
# MODULE 5: PERFORMANCE METRICS
# ============================================================================

class PerformanceMetrics:
    """Calculate comprehensive performance metrics"""
    
    @staticmethod
    def calculate_metrics(portfolio_values: pd.Series) -> Dict:
        """Calculate all performance metrics"""
        returns = portfolio_values.pct_change().dropna()
        
        total_return = (portfolio_values.iloc[-1] / portfolio_values.iloc[0]) - 1
        annual_return = (1 + total_return) ** (252 / len(returns)) - 1
        volatility = returns.std() * np.sqrt(252)
        sharpe_ratio = annual_return / volatility if volatility > 0 else 0
        
        # Maximum drawdown
        cummax = portfolio_values.cummax()
        drawdown = (portfolio_values - cummax) / cummax
        max_drawdown = drawdown.min()
        
        # Win rate
        win_rate = (returns > 0).sum() / len(returns)
        
        return {
            'Total Return': f'{total_return:.2%}',
            'Annual Return': f'{annual_return:.2%}',
            'Volatility': f'{volatility:.2%}',
            'Sharpe Ratio': f'{sharpe_ratio:.2f}',
            'Max Drawdown': f'{max_drawdown:.2%}',
            'Win Rate': f'{win_rate:.2%}'
        }
    
    @staticmethod
    def compare_strategies(results_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Compare multiple strategies"""
        comparison = {}
        
        for name, results in results_dict.items():
            metrics = PerformanceMetrics.calculate_metrics(results['portfolio_value'])
            comparison[name] = metrics
        
        return pd.DataFrame(comparison).T


# ============================================================================
# MODULE 6: VISUALIZATION
# ============================================================================

class Visualizer:
    """Comprehensive visualization toolkit"""
    
    @staticmethod
    def plot_regime_classification(data: pd.DataFrame, regimes: pd.Series,
                                   market_col: str = None):
        """Plot market performance with regime colors"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
        
        common_index = data.index.intersection(regimes.index)
        data_aligned = data.loc[common_index]
        regimes_aligned = regimes.loc[common_index]
        
        if market_col is None or market_col not in data_aligned.columns:
            market_col = data_aligned.columns[0]
        
        market = data_aligned[market_col]
        
        regime_colors = {0: 'red', 1: 'green', 2: 'blue', 3: 'orange', 4: 'purple'}
        for regime in sorted(regimes_aligned.unique()):
            mask = (regimes_aligned == regime)
            if mask.sum() > 0:
                ax1.scatter(regimes_aligned[mask].index, market[mask],
                          c=regime_colors.get(regime, 'gray'), s=1, alpha=0.6,
                          label=f'Regime {regime}')
        
        ax1.set_title(f'Market Performance ({market_col}) with {Config.N_REGIMES} Detected Regimes',
                     fontsize=14, fontweight='bold')
        ax1.set_ylabel('Price', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        for regime in sorted(regimes_aligned.unique()):
            ax2.fill_between(regimes_aligned.index, 0, 1,
                           where=(regimes_aligned == regime),
                           color=regime_colors.get(regime, 'gray'),
                           alpha=0.3, label=f'Regime {regime}')
        
        ax2.set_title(f'Regime Timeline (ST={Config.SHORT_TERM_TREND}d, LT={Config.LONG_TERM_TREND}d)', 
                     fontsize=14, fontweight='bold')
        ax2.set_xlabel('Date', fontsize=12)
        ax2.set_yticks([])
        ax2.legend(loc='upper right')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
    
    @staticmethod
    def plot_backtest_results(results: pd.DataFrame, benchmark: pd.DataFrame = None):
        """Plot backtest performance"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
        
        ax1.plot(results.index, results['portfolio_value'], 
                label='Regime Strategy', linewidth=2)
        
        if benchmark is not None:
            ax1.plot(benchmark.index, benchmark['portfolio_value'],
                    label='Buy & Hold', linewidth=2, alpha=0.7)
        
        ax1.set_title(f'Portfolio Performance (Rebalance every {Config.LONG_TERM_TREND} days)', 
                     fontsize=14, fontweight='bold')
        ax1.set_ylabel('Portfolio Value ($)', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        if 'regime' in results.columns:
            regime_colors = {0: 'red', 1: 'green', 2: 'blue', 3: 'orange', 4: 'purple'}
            for regime in sorted(results['regime'].unique()):
                mask = results['regime'] == regime
                ax2.fill_between(results.index, 0, 1, where=mask,
                               color=regime_colors.get(regime, 'gray'),
                               alpha=0.3, label=f'Regime {regime}')
            
            ax2.set_title('Active Regimes During Backtest', fontsize=14, fontweight='bold')
            ax2.set_xlabel('Date', fontsize=12)
            ax2.set_yticks([])
            ax2.legend(loc='upper right')
        
        plt.tight_layout()
        plt.show()
    
    @staticmethod
    def plot_monte_carlo_results_with_benchmark(strategy_returns, benchmark_returns,
                                                strategy_sharpe, benchmark_sharpe,
                                                strategy_dd, benchmark_dd,
                                                outperformance, title="Monte Carlo Results"):
        """Plot comprehensive Monte Carlo comparison"""
        fig = plt.figure(figsize=(18, 12))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # Returns distribution
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.hist(strategy_returns, bins=50, alpha=0.6, color='blue', 
                label=f'Strategy (μ={np.mean(strategy_returns):.1%})', edgecolor='black')
        ax1.hist(benchmark_returns, bins=50, alpha=0.6, color='orange',
                label=f'Benchmark (μ={np.mean(benchmark_returns):.1%})', edgecolor='black')
        ax1.axvline(np.mean(strategy_returns), color='blue', linestyle='--', linewidth=2)
        ax1.axvline(np.mean(benchmark_returns), color='orange', linestyle='--', linewidth=2)
        ax1.set_title('Returns Distribution', fontweight='bold')
        ax1.set_xlabel('Total Return')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Sharpe comparison
        ax2 = fig.add_subplot(gs[0, 1])
        ax2.hist(strategy_sharpe, bins=50, alpha=0.6, color='blue',
                label=f'Strategy (μ={np.mean(strategy_sharpe):.2f})', edgecolor='black')
        ax2.hist(benchmark_sharpe, bins=50, alpha=0.6, color='orange',
                label=f'Benchmark (μ={np.mean(benchmark_sharpe):.2f})', edgecolor='black')
        ax2.axvline(np.mean(strategy_sharpe), color='blue', linestyle='--', linewidth=2)
        ax2.axvline(np.mean(benchmark_sharpe), color='orange', linestyle='--', linewidth=2)
        ax2.set_title('Sharpe Ratio Distribution', fontweight='bold')
        ax2.set_xlabel('Sharpe Ratio')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Max DD comparison
        ax3 = fig.add_subplot(gs[0, 2])
        ax3.hist(strategy_dd, bins=50, alpha=0.6, color='blue',
                label=f'Strategy (μ={np.mean(strategy_dd):.1%})', edgecolor='black')
        ax3.hist(benchmark_dd, bins=50, alpha=0.6, color='orange',
                label=f'Benchmark (μ={np.mean(benchmark_dd):.1%})', edgecolor='black')
        ax3.axvline(np.mean(strategy_dd), color='blue', linestyle='--', linewidth=2)
        ax3.axvline(np.mean(benchmark_dd), color='orange', linestyle='--', linewidth=2)
        ax3.set_title('Max Drawdown Distribution', fontweight='bold')
        ax3.set_xlabel('Max Drawdown')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Outperformance distribution
        ax4 = fig.add_subplot(gs[1, :2])
        ax4.hist(outperformance, bins=60, alpha=0.7, color='purple', edgecolor='black')
        ax4.axvline(0, color='black', linestyle='-', linewidth=2, alpha=0.5)
        ax4.axvline(np.mean(outperformance), color='red', linestyle='--', linewidth=2,
                   label=f'Mean: {np.mean(outperformance):.2%}')
        ax4.axvline(np.median(outperformance), color='green', linestyle='--', linewidth=2,
                   label=f'Median: {np.median(outperformance):.2%}')
        
        outperform_pct = sum(1 for o in outperformance if o > 0) / len(outperformance) * 100
        ax4.set_title(f'Outperformance Distribution (Strategy - Benchmark)\n'
                     f'{outperform_pct:.1f}% outperformed', fontweight='bold', fontsize=12)
        ax4.set_xlabel('Outperformance')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        # Win rate comparison
        ax5 = fig.add_subplot(gs[1, 2])
        strategy_wins = sum(1 for r in strategy_returns if r > 0)
        benchmark_wins = sum(1 for r in benchmark_returns if r > 0)
        outperform_wins = sum(1 for o in outperformance if o > 0)
        
        x = ['Strategy\nPositive', 'Benchmark\nPositive', 'Strategy\nOutperforms']
        y = [strategy_wins/len(strategy_returns)*100,
             benchmark_wins/len(benchmark_returns)*100,
             outperform_wins/len(outperformance)*100]
        colors = ['blue', 'orange', 'purple']
        
        bars = ax5.bar(x, y, color=colors, alpha=0.7, edgecolor='black')
        ax5.axhline(50, color='black', linestyle='--', alpha=0.3, label='50% line')
        ax5.set_ylabel('Percentage (%)')
        ax5.set_title('Win Rates', fontweight='bold')
        ax5.set_ylim([0, 100])
        
        for bar in bars:
            height = bar.get_height()
            ax5.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}%', ha='center', va='bottom', fontweight='bold')
        ax5.grid(True, alpha=0.3, axis='y')
        
        # Scatter plots
        ax6 = fig.add_subplot(gs[2, 0])
        ax6.scatter(benchmark_returns, strategy_returns, alpha=0.3, s=20)
        ax6.plot([min(benchmark_returns), max(benchmark_returns)],
                [min(benchmark_returns), max(benchmark_returns)],
                'r--', label='Equal performance', linewidth=2)
        ax6.set_xlabel('Benchmark Return')
        ax6.set_ylabel('Strategy Return')
        ax6.set_title('Return Comparison', fontweight='bold')
        ax6.legend()
        ax6.grid(True, alpha=0.3)
        
        ax7 = fig.add_subplot(gs[2, 1])
        ax7.scatter(benchmark_sharpe, strategy_sharpe, alpha=0.3, s=20)
        ax7.plot([min(benchmark_sharpe), max(benchmark_sharpe)],
                [min(benchmark_sharpe), max(benchmark_sharpe)],
                'r--', label='Equal Sharpe', linewidth=2)
        ax7.set_xlabel('Benchmark Sharpe')
        ax7.set_ylabel('Strategy Sharpe')
        ax7.set_title('Sharpe Comparison', fontweight='bold')
        ax7.legend()
        ax7.grid(True, alpha=0.3)
        
        # Summary statistics table
        ax8 = fig.add_subplot(gs[2, 2])
        ax8.axis('off')
        
        summary_data = [
            ['Metric', 'Strategy', 'Benchmark', 'Diff'],
            ['Mean Return', f'{np.mean(strategy_returns):.1%}', 
             f'{np.mean(benchmark_returns):.1%}',
             f'{np.mean(outperformance):.1%}'],
            ['Median Return', f'{np.median(strategy_returns):.1%}',
             f'{np.median(benchmark_returns):.1%}',
             f'{np.median(outperformance):.1%}'],
            ['Mean Sharpe', f'{np.mean(strategy_sharpe):.2f}',
             f'{np.mean(benchmark_sharpe):.2f}',
             f'{np.mean(strategy_sharpe) - np.mean(benchmark_sharpe):.2f}'],
            ['Mean Max DD', f'{np.mean(strategy_dd):.1%}',
             f'{np.mean(benchmark_dd):.1%}',
             f'{np.mean(strategy_dd) - np.mean(benchmark_dd):.1%}'],
            ['Win Rate', f'{strategy_wins/len(strategy_returns)*100:.1f}%',
             f'{benchmark_wins/len(benchmark_returns)*100:.1f}%',
             f'{outperform_wins/len(outperformance)*100:.1f}%']
        ]
        
        table = ax8.table(cellText=summary_data, cellLoc='center', loc='center',
                         colWidths=[0.25, 0.25, 0.25, 0.25])
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2)
        
        # Style header row
        for i in range(4):
            table[(0, i)].set_facecolor('#4CAF50')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        fig.suptitle(title, fontsize=16, fontweight='bold', y=0.995)
        plt.show()


# ============================================================================
# SYSTEM INITIALIZATION
# ============================================================================

print("=" * 80)
print("REGIME-BASED PORTFOLIO OPTIMIZATION SYSTEM")
print("=" * 80)
print(f"\n📊 Current Configuration:")
print(f"  • Short-term trend: {Config.SHORT_TERM_TREND} days")
print(f"  • Long-term trend: {Config.LONG_TERM_TREND} days")
print(f"  • Number of regimes: {Config.N_REGIMES}")
print(f"  • Rebalancing period: {Config.LONG_TERM_TREND} days")
print(f"  • Max position size: {Config.MAX_POSITION_SIZE:.1%}")
print(f"  • Shrinkage (regularization): {Config.SHRINKAGE:.1%}")
print("\n✓ All modules loaded successfully!")
print("\nAvailable components:")
print("  • DataGenerator - Synthetic market data")
print("  • RegimeDetector - HMM-based regime detection")
print("  • PortfolioOptimizer - Mean-variance optimization")
print("  • Backtester - Strategy backtesting (⚠️ HAS LOOK-AHEAD BIAS)")
print("  • WalkForwardBacktester - Proper walk-forward (✓ NO BIAS)")
print("  • BootstrapGenerator - Data bootstrapping methods")
print("  • PerformanceMetrics - Performance analysis")
print("  • Visualizer - Comprehensive visualizations")
print("\n🚀 Ready to run tests!")
print("\n⚠️  IMPORTANT: Use WalkForwardBacktester for realistic results!")
print("   The regular Backtester has look-ahead bias and inflates performance.")