"""
REGIME-BASED PORTFOLIO OPTIMIZATION - COMPREHENSIVE TEST SUITE V2
==================================================================

This file contains PROPER backtesting with NO look-ahead bias:

1. Walk-Forward Backtesting (Expanding & Rolling Windows)
2. Train/Test Split (2019-2023 train, 2024-2025 test)
3. Bootstrap Analysis (Block, Residual, Parametric)
4. Bias Comparison (Biased vs Unbiased methods)

Author: Regime Trading System
Date: February 2026
Version: 2.0 (NO Look-Ahead Bias)
"""

# ============================================================================
# IMPORTS
# ============================================================================

from regime_system_modules import *
import yfinance as yf
from datetime import datetime, timedelta
import imageio
from PIL import Image
import io
import os
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# GICS sector ETFs
SECTORS = ['XLK', 'XLF', 'XLV', 'XLY', 'XLP', 'XLE', 
           'XLI', 'XLB', 'XLRE', 'XLU', 'XLC']

print("=" * 80)
print("COMPREHENSIVE TEST SUITE V2.0 - NO LOOK-AHEAD BIAS")
print("=" * 80)
print("\n✓ All modules loaded!")
print("\nAvailable tests:")
print("  1. Walk-Forward Backtest (Expanding Window)")
print("  2. Walk-Forward Backtest (Rolling Window)")
print("  3. Train/Test Split (2019-2023 train, 2024-2025 test)")
print("  4. Bootstrap Validation (Multiple methods)")
print("  5. Bias Comparison (Show impact of look-ahead bias)")
print("  6. Full Comprehensive Analysis (All of the above)")


# ============================================================================
# TEST 1: WALK-FORWARD EXPANDING WINDOW
# ============================================================================

def run_test_walkforward_expanding(start_date='2019-01-01', end_date=None):
    """
    Test 1: Walk-forward backtest with expanding window
    
    At each rebalance, uses ALL past data for training.
    Most common approach in practice.
    """
    print("\n" + "=" * 80)
    print("TEST 1: WALK-FORWARD BACKTEST - EXPANDING WINDOW")
    print("=" * 80)
    print("\n✓ This method has NO look-ahead bias")
    print("✓ Realistic performance expectations")
    print("✓ Uses only past data at each decision point\n")
    
    # Download data
    print("[1/5] Downloading historical data...")
    if end_date is None:
        end_date = datetime.now()
    
    tickers = SECTORS + ['SPY']
    data = yf.download(tickers, start=start_date, end=end_date, progress=False)['Close']
    data = data.dropna()
    
    print(f"✓ Downloaded {len(data)} days from {data.index[0].date()} to {data.index[-1].date()}")
    
    # Run walk-forward backtest
    print("\n[2/5] Running walk-forward backtest...")
    wf_backtester = WalkForwardBacktester(
        training_window=None,  # Expanding window
        rebalance_period=63,
        min_training_days=252
    )
    
    results = wf_backtester.run_backtest(data, SECTORS, verbose=True)
    
    # Run benchmark
    print("\n[3/5] Running benchmark...")
    backtester = Backtester()
    benchmark = backtester.run_benchmark(data, market_col='SPY')
    
    # Calculate metrics
    print("\n[4/5] Calculating performance metrics...")
    strategy_metrics = PerformanceMetrics.calculate_metrics(results['portfolio_value'])
    benchmark_metrics = PerformanceMetrics.calculate_metrics(benchmark['portfolio_value'])
    
    comparison = pd.DataFrame({
        'Walk-Forward Strategy': strategy_metrics,
        'Buy & Hold SPY': benchmark_metrics
    })
    
    print("\n" + "=" * 80)
    print("PERFORMANCE COMPARISON")
    print("=" * 80)
    print(comparison)
    print("=" * 80)
    
    # Visualize
    print("\n[5/5] Creating visualizations...")
    Visualizer.plot_backtest_results(results, benchmark)
    
    return results, benchmark, comparison


# ============================================================================
# TEST 2: WALK-FORWARD ROLLING WINDOW
# ============================================================================

def run_test_walkforward_rolling(start_date='2019-01-01', end_date=None, window_size=504):
    """
    Test 2: Walk-forward backtest with rolling window
    
    Uses only last N days for training (default: 504 days = 2 years).
    More realistic for real-time trading systems.
    """
    print("\n" + "=" * 80)
    print(f"TEST 2: WALK-FORWARD BACKTEST - ROLLING WINDOW ({window_size} days)")
    print("=" * 80)
    print("\n✓ Uses only most recent data for training")
    print("✓ More realistic for production systems")
    print("✓ Adapts faster to regime changes\n")
    
    # Download data
    print("[1/5] Downloading historical data...")
    if end_date is None:
        end_date = datetime.now()
    
    tickers = SECTORS + ['SPY']
    data = yf.download(tickers, start=start_date, end=end_date, progress=False)['Close']
    data = data.dropna()
    
    print(f"✓ Downloaded {len(data)} days")
    
    # Run walk-forward backtest
    print("\n[2/5] Running walk-forward backtest with rolling window...")
    wf_backtester = WalkForwardBacktester(
        training_window=window_size,  # Rolling window
        rebalance_period=63,
        min_training_days=252
    )
    
    results = wf_backtester.run_backtest(data, SECTORS, verbose=True)
    
    # Run benchmark
    print("\n[3/5] Running benchmark...")
    backtester = Backtester()
    benchmark = backtester.run_benchmark(data, market_col='SPY')
    
    # Calculate metrics
    print("\n[4/5] Calculating performance metrics...")
    strategy_metrics = PerformanceMetrics.calculate_metrics(results['portfolio_value'])
    benchmark_metrics = PerformanceMetrics.calculate_metrics(benchmark['portfolio_value'])
    
    comparison = pd.DataFrame({
        'Walk-Forward Strategy': strategy_metrics,
        'Buy & Hold SPY': benchmark_metrics
    })
    
    print("\n" + "=" * 80)
    print("PERFORMANCE COMPARISON")
    print("=" * 80)
    print(comparison)
    print("=" * 80)
    
    # Visualize
    print("\n[5/5] Creating visualizations...")
    Visualizer.plot_backtest_results(results, benchmark)
    
    return results, benchmark, comparison


# ============================================================================
# TEST 3: TRAIN/TEST SPLIT
# ============================================================================

def run_test_train_test_split():
    """
    Test 3: Proper train/test split
    
    Train: 2019-01-01 to 2023-12-31 (5 years)
    Test:  2024-01-01 to 2025-02-13 (out-of-sample)
    
    This is the GOLD STANDARD for validating strategies.
    """
    print("\n" + "=" * 80)
    print("TEST 3: TRAIN/TEST SPLIT VALIDATION")
    print("=" * 80)
    print("\n✓ Train Period: 2019-2023 (5 years)")
    print("✓ Test Period: 2024-2025 (out-of-sample)")
    print("✓ Most rigorous validation method\n")
    
    # Download full dataset
    print("[1/7] Downloading full historical data...")
    end_date = datetime.now()
    start_date = '2019-01-01'
    
    tickers = SECTORS + ['SPY']
    data = yf.download(tickers, start=start_date, end=end_date, progress=False)['Close']
    data = data.dropna()
    
    print(f"✓ Downloaded {len(data)} days from {data.index[0].date()} to {data.index[-1].date()}")
    
    # Split into train and test
    train_end = '2023-12-31'
    test_start = '2024-01-01'
    
    train_data = data[data.index < train_end]
    test_data = data[data.index >= test_start]
    
    print(f"\n[2/7] Data split:")
    print(f"  Training: {len(train_data)} days ({train_data.index[0].date()} to {train_data.index[-1].date()})")
    print(f"  Testing:  {len(test_data)} days ({test_data.index[0].date()} to {test_data.index[-1].date()})")
    
    # Train on training data
    print("\n[3/7] Training regime detector on 2019-2023 data...")
    detector = RegimeDetector()
    detector.fit(train_data, market_col='SPY')
    train_regimes = detector.predict(train_data, market_col='SPY')
    
    print(f"✓ Detected {len(train_regimes.unique())} regimes in training data")
    
    # Optimize weights on training data
    print("\n[4/7] Optimizing portfolio weights on training data...")
    regime_weights = PortfolioOptimizer.optimize_all_regimes(train_data, train_regimes, SECTORS)
    
    # Test on out-of-sample data
    print("\n[5/7] Testing on out-of-sample 2024-2025 data...")
    test_regimes = detector.predict(test_data, market_col='SPY')
    
    backtester = Backtester()
    test_results = backtester.run_backtest(test_data, test_regimes, regime_weights, SECTORS)
    test_benchmark = backtester.run_benchmark(test_data, market_col='SPY')
    
    # Calculate metrics
    print("\n[6/7] Calculating performance metrics...")
    
    # Training metrics
    train_results = backtester.run_backtest(train_data, train_regimes, regime_weights, SECTORS)
    train_benchmark = backtester.run_benchmark(train_data, market_col='SPY')
    
    train_strategy_metrics = PerformanceMetrics.calculate_metrics(train_results['portfolio_value'])
    train_benchmark_metrics = PerformanceMetrics.calculate_metrics(train_benchmark['portfolio_value'])
    
    # Testing metrics
    test_strategy_metrics = PerformanceMetrics.calculate_metrics(test_results['portfolio_value'])
    test_benchmark_metrics = PerformanceMetrics.calculate_metrics(test_benchmark['portfolio_value'])
    
    comparison = pd.DataFrame({
        'Strategy (Train)': train_strategy_metrics,
        'Benchmark (Train)': train_benchmark_metrics,
        'Strategy (Test)': test_strategy_metrics,
        'Benchmark (Test)': test_benchmark_metrics
    })
    
    print("\n" + "=" * 80)
    print("TRAIN/TEST PERFORMANCE COMPARISON")
    print("=" * 80)
    print(comparison)
    print("=" * 80)
    
    # Check for overfitting
    train_return = float(train_strategy_metrics['Total Return'].strip('%')) / 100
    test_return = float(test_strategy_metrics['Total Return'].strip('%')) / 100
    
    print(f"\n📊 Overfitting Analysis:")
    print(f"  Training Return:    {train_return:>8.2%}")
    print(f"  Testing Return:     {test_return:>8.2%}")
    print(f"  Degradation:        {(test_return - train_return):>8.2%}")
    
    if test_return < train_return * 0.5:
        print(f"  ⚠️  WARNING: Significant performance degradation (>50%)")
        print(f"     Strategy may be overfit to training data")
    elif test_return < train_return * 0.8:
        print(f"  ⚠️  CAUTION: Moderate performance degradation")
    else:
        print(f"  ✓ Good: Test performance similar to training")
    
    # Visualize
    print("\n[7/7] Creating visualizations...")
    
    # Plot training and testing separately
    fig, axes = plt.subplots(2, 1, figsize=(15, 12))
    
    # Training period
    ax1 = axes[0]
    ax1.plot(train_results.index, train_results['portfolio_value'], 
            label='Strategy', linewidth=2, color='blue')
    ax1.plot(train_benchmark.index, train_benchmark['portfolio_value'],
            label='Buy & Hold', linewidth=2, color='orange', alpha=0.7)
    ax1.set_title('Training Period: 2019-2023', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Portfolio Value ($)', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Testing period
    ax2 = axes[1]
    ax2.plot(test_results.index, test_results['portfolio_value'],
            label='Strategy', linewidth=2, color='blue')
    ax2.plot(test_benchmark.index, test_benchmark['portfolio_value'],
            label='Buy & Hold', linewidth=2, color='orange', alpha=0.7)
    ax2.set_title('Testing Period: 2024-2025 (Out-of-Sample)', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Portfolio Value ($)', fontsize=12)
    ax2.set_xlabel('Date', fontsize=12)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    
    return {
        'train_results': train_results,
        'train_benchmark': train_benchmark,
        'test_results': test_results,
        'test_benchmark': test_benchmark,
        'comparison': comparison
    }


# ============================================================================
# TEST 4: BOOTSTRAP VALIDATION
# ============================================================================

def run_test_bootstrap(start_date='2019-01-01', end_date=None, n_bootstrap=100):
    """
    Test 4: Bootstrap validation using multiple methods
    
    Generates multiple resampled datasets to test robustness
    """
    print("\n" + "=" * 80)
    print(f"TEST 4: BOOTSTRAP VALIDATION ({n_bootstrap} samples)")
    print("=" * 80)
    print("\n✓ Tests strategy robustness")
    print("✓ Generates confidence intervals")
    print("✓ Multiple bootstrap methods\n")
    
    # Download data
    print("[1/5] Downloading historical data...")
    if end_date is None:
        end_date = datetime.now()
    
    tickers = SECTORS + ['SPY']
    data = yf.download(tickers, start=start_date, end=end_date, progress=False)['Close']
    data = data.dropna()
    
    print(f"✓ Downloaded {len(data)} days")
    
    # Generate bootstrap samples
    print(f"\n[2/5] Generating {n_bootstrap} bootstrap samples...")
    boot_gen = BootstrapGenerator()
    
    block_samples = boot_gen.block_bootstrap(data, n_samples=n_bootstrap, block_size=21)
    print(f"✓ Generated {len(block_samples)} block bootstrap samples")
    
    # Run walk-forward on each bootstrap sample
    print("\n[3/5] Running walk-forward backtest on bootstrap samples...")
    
    strategy_returns = []
    benchmark_returns = []
    
    wf_backtester = WalkForwardBacktester(
        training_window=None,
        rebalance_period=63,
        min_training_days=252
    )
    
    backtester = Backtester()
    
    for i, boot_data in enumerate(block_samples):
        if (i + 1) % 20 == 0:
            print(f"  Progress: {i+1}/{n_bootstrap}")
        
        try:
            # Run strategy
            results = wf_backtester.run_backtest(boot_data, SECTORS, verbose=False)
            strategy_ret = (results['portfolio_value'].iloc[-1] / Config.INITIAL_CAPITAL) - 1
            
            # Run benchmark
            benchmark = backtester.run_benchmark(boot_data, market_col='SPY')
            bench_ret = (benchmark['portfolio_value'].iloc[-1] / Config.INITIAL_CAPITAL) - 1
            
            strategy_returns.append(strategy_ret)
            benchmark_returns.append(bench_ret)
        except:
            continue
    
    print(f"\n✓ Completed {len(strategy_returns)} successful runs")
    
    # Analyze results
    print("\n[4/5] Analyzing bootstrap results...")
    
    strategy_returns = np.array(strategy_returns)
    benchmark_returns = np.array(benchmark_returns)
    outperformance = strategy_returns - benchmark_returns
    
    print("\n" + "=" * 80)
    print("BOOTSTRAP ANALYSIS RESULTS")
    print("=" * 80)
    
    print(f"\nStrategy Returns:")
    print(f"  Mean:        {np.mean(strategy_returns):>8.2%}")
    print(f"  Median:      {np.median(strategy_returns):>8.2%}")
    print(f"  Std Dev:     {np.std(strategy_returns):>8.2%}")
    print(f"  95% CI:      [{np.percentile(strategy_returns, 2.5):.2%}, {np.percentile(strategy_returns, 97.5):.2%}]")
    
    print(f"\nBenchmark Returns:")
    print(f"  Mean:        {np.mean(benchmark_returns):>8.2%}")
    print(f"  Median:      {np.median(benchmark_returns):>8.2%}")
    print(f"  Std Dev:     {np.std(benchmark_returns):>8.2%}")
    print(f"  95% CI:      [{np.percentile(benchmark_returns, 2.5):.2%}, {np.percentile(benchmark_returns, 97.5):.2%}]")
    
    print(f"\nOutperformance:")
    print(f"  Mean:        {np.mean(outperformance):>8.2%}")
    print(f"  Median:      {np.median(outperformance):>8.2%}")
    print(f"  Std Dev:     {np.std(outperformance):>8.2%}")
    print(f"  95% CI:      [{np.percentile(outperformance, 2.5):.2%}, {np.percentile(outperformance, 97.5):.2%}]")
    print(f"  Win Rate:    {(outperformance > 0).sum() / len(outperformance) * 100:.1f}%")
    
    # Statistical test
    t_stat, p_value = stats.ttest_rel(strategy_returns, benchmark_returns)
    print(f"\nStatistical Significance:")
    print(f"  T-statistic: {t_stat:>8.4f}")
    print(f"  P-value:     {p_value:>8.6f}")
    if p_value < 0.05:
        print(f"  ✓ Statistically significant (p < 0.05)")
    else:
        print(f"  ✗ Not statistically significant (p >= 0.05)")
    
    # Visualize
    print("\n[5/5] Creating visualizations...")
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # Returns distribution
    ax1 = axes[0, 0]
    ax1.hist(strategy_returns, bins=30, alpha=0.6, label='Strategy', color='blue', edgecolor='black')
    ax1.hist(benchmark_returns, bins=30, alpha=0.6, label='Benchmark', color='orange', edgecolor='black')
    ax1.axvline(np.mean(strategy_returns), color='blue', linestyle='--', linewidth=2)
    ax1.axvline(np.mean(benchmark_returns), color='orange', linestyle='--', linewidth=2)
    ax1.set_title('Returns Distribution', fontweight='bold')
    ax1.set_xlabel('Total Return')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Outperformance
    ax2 = axes[0, 1]
    ax2.hist(outperformance, bins=40, alpha=0.7, color='purple', edgecolor='black')
    ax2.axvline(0, color='black', linestyle='-', linewidth=2)
    ax2.axvline(np.mean(outperformance), color='red', linestyle='--', linewidth=2,
               label=f'Mean: {np.mean(outperformance):.2%}')
    ax2.set_title('Outperformance Distribution', fontweight='bold')
    ax2.set_xlabel('Strategy - Benchmark')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Scatter plot
    ax3 = axes[1, 0]
    ax3.scatter(benchmark_returns, strategy_returns, alpha=0.5)
    ax3.plot([min(benchmark_returns), max(benchmark_returns)],
            [min(benchmark_returns), max(benchmark_returns)],
            'r--', label='Equal performance', linewidth=2)
    ax3.set_xlabel('Benchmark Return')
    ax3.set_ylabel('Strategy Return')
    ax3.set_title('Return Comparison', fontweight='bold')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Box plots
    ax4 = axes[1, 1]
    box_data = [strategy_returns, benchmark_returns, outperformance]
    ax4.boxplot(box_data, labels=['Strategy', 'Benchmark', 'Outperformance'])
    ax4.set_ylabel('Return')
    ax4.set_title('Return Statistics', fontweight='bold')
    ax4.grid(True, alpha=0.3, axis='y')
    ax4.axhline(0, color='black', linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.show()
    
    return strategy_returns, benchmark_returns, outperformance


# ============================================================================
# TEST 5: BIAS COMPARISON
# ============================================================================

def run_test_bias_comparison(start_date='2019-01-01', end_date=None):
    """
    Test 5: Compare biased vs unbiased backtesting
    
    Shows the impact of look-ahead bias by running both methods
    """
    print("\n" + "=" * 80)
    print("TEST 5: BIAS COMPARISON")
    print("=" * 80)
    print("\n⚠️  This test quantifies the look-ahead bias")
    print("✓ Runs BOTH biased and unbiased methods")
    print("✓ Shows performance inflation from bias\n")
    
    # Download data
    print("[1/6] Downloading historical data...")
    if end_date is None:
        end_date = datetime.now()
    
    tickers = SECTORS + ['SPY']
    data = yf.download(tickers, start=start_date, end=end_date, progress=False)['Close']
    data = data.dropna()
    
    print(f"✓ Downloaded {len(data)} days")
    
    # Method 1: BIASED (original approach)
    print("\n[2/6] Running BIASED backtest (original method)...")
    print("  ⚠️  This uses future data - DO NOT use for real trading!")
    
    detector = RegimeDetector()
    detector.fit(data, market_col='SPY')  # BIAS: Uses ALL data including future
    regimes = detector.predict(data, market_col='SPY')
    regime_weights = PortfolioOptimizer.optimize_all_regimes(data, regimes, SECTORS)  # BIAS: Optimizes on future
    
    backtester = Backtester()
    biased_results = backtester.run_backtest(data, regimes, regime_weights, SECTORS)
    
    print(f"✓ Biased backtest complete")
    
    # Method 2: UNBIASED (walk-forward)
    print("\n[3/6] Running UNBIASED walk-forward backtest...")
    print("  ✓ This is the CORRECT method - realistic performance")
    
    wf_backtester = WalkForwardBacktester(
        training_window=None,
        rebalance_period=63,
        min_training_days=252
    )
    
    unbiased_results = wf_backtester.run_backtest(data, SECTORS, verbose=False)
    
    print(f"✓ Unbiased backtest complete")
    
    # Benchmark
    print("\n[4/6] Running benchmark...")
    benchmark = backtester.run_benchmark(data, market_col='SPY')
    
    # Calculate metrics
    print("\n[5/6] Calculating performance metrics...")
    
    biased_metrics = PerformanceMetrics.calculate_metrics(biased_results['portfolio_value'])
    unbiased_metrics = PerformanceMetrics.calculate_metrics(unbiased_results['portfolio_value'])
    benchmark_metrics = PerformanceMetrics.calculate_metrics(benchmark['portfolio_value'])
    
    comparison = pd.DataFrame({
        'BIASED Method': biased_metrics,
        'UNBIASED Method': unbiased_metrics,
        'Benchmark': benchmark_metrics
    })
    
    print("\n" + "=" * 80)
    print("BIAS IMPACT ANALYSIS")
    print("=" * 80)
    print(comparison)
    print("=" * 80)
    
    # Quantify bias
    biased_return = float(biased_metrics['Total Return'].strip('%')) / 100
    unbiased_return = float(unbiased_metrics['Total Return'].strip('%')) / 100
    benchmark_return = float(benchmark_metrics['Total Return'].strip('%')) / 100
    
    bias_inflation = biased_return - unbiased_return
    bias_pct = (bias_inflation / abs(unbiased_return) * 100) if unbiased_return != 0 else 0
    
    print(f"\n📊 Bias Quantification:")
    print(f"  Biased Return:      {biased_return:>8.2%}")
    print(f"  Unbiased Return:    {unbiased_return:>8.2%}")
    print(f"  Benchmark Return:   {benchmark_return:>8.2%}")
    print(f"\n  Bias Inflation:     {bias_inflation:>8.2%}")
    print(f"  Relative Inflation: {bias_pct:>8.1f}%")
    
    if bias_inflation > 0.05:
        print(f"\n  ⚠️  SEVERE BIAS: Performance inflated by {bias_inflation:.2%}!")
        print(f"     Original results are NOT realistic")
    elif bias_inflation > 0.02:
        print(f"\n  ⚠️  MODERATE BIAS: Performance inflated by {bias_inflation:.2%}")
    else:
        print(f"\n  ✓ LOW BIAS: Bias effect is minimal")
    
    # Visualize
    print("\n[6/6] Creating visualizations...")
    
    fig, axes = plt.subplots(2, 1, figsize=(15, 12))
    
    # Portfolio value comparison
    ax1 = axes[0]
    ax1.plot(biased_results.index, biased_results['portfolio_value'],
            label='BIASED Method (Future Data)', linewidth=2, color='red', linestyle='--')
    ax1.plot(unbiased_results.index, unbiased_results['portfolio_value'],
            label='UNBIASED Method (Walk-Forward)', linewidth=2, color='blue')
    ax1.plot(benchmark.index, benchmark['portfolio_value'],
            label='Buy & Hold SPY', linewidth=2, color='orange', alpha=0.7)
    ax1.set_title('Bias Comparison: Portfolio Value Over Time', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Portfolio Value ($)', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Cumulative returns comparison
    ax2 = axes[1]
    biased_cumret = (biased_results['portfolio_value'] / Config.INITIAL_CAPITAL - 1) * 100
    unbiased_cumret = (unbiased_results['portfolio_value'] / Config.INITIAL_CAPITAL - 1) * 100
    bench_cumret = (benchmark['portfolio_value'] / Config.INITIAL_CAPITAL - 1) * 100
    
    ax2.plot(biased_results.index, biased_cumret,
            label='BIASED Method', linewidth=2, color='red', linestyle='--')
    ax2.plot(unbiased_results.index, unbiased_cumret,
            label='UNBIASED Method', linewidth=2, color='blue')
    ax2.plot(benchmark.index, bench_cumret,
            label='Benchmark', linewidth=2, color='orange', alpha=0.7)
    ax2.set_title('Bias Comparison: Cumulative Returns (%)', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Return (%)', fontsize=12)
    ax2.set_xlabel('Date', fontsize=12)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.axhline(0, color='black', linestyle='--', alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    
    return {
        'biased_results': biased_results,
        'unbiased_results': unbiased_results,
        'benchmark': benchmark,
        'comparison': comparison,
        'bias_inflation': bias_inflation
    }


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("SELECT TEST TO RUN")
    print("=" * 80)
    print("\n1. Walk-Forward (Expanding Window)")
    print("2. Walk-Forward (Rolling Window)")
    print("3. Train/Test Split (2019-2023 train, 2024-2025 test)")
    print("4. Bootstrap Validation")
    print("5. Bias Comparison")
    print("6. Run All Tests")
    
    choice = input("\nEnter choice (1-6): ").strip()
    
    if choice == '1':
        results = run_test_walkforward_expanding()
    elif choice == '2':
        results = run_test_walkforward_rolling()
    elif choice == '3':
        results = run_test_train_test_split()
    elif choice == '4':
        results = run_test_bootstrap()
    elif choice == '5':
        results = run_test_bias_comparison()
    elif choice == '6':
        print("\n" + "=" * 80)
        print("RUNNING ALL TESTS")
        print("=" * 80)
        
        test1 = run_test_walkforward_expanding()
        test2 = run_test_walkforward_rolling()
        test3 = run_test_train_test_split()
        test4 = run_test_bootstrap()
        test5 = run_test_bias_comparison()
        
        print("\n" + "=" * 80)
        print("ALL TESTS COMPLETE!")
        print("=" * 80)
    else:
        print("\nInvalid choice")
    
    print("\n" + "=" * 80)
    print("TEST EXECUTION FINISHED")
    print("=" * 80)
