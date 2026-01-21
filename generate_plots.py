import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
import ast
import os

if not os.path.exists('assets'):
    os.makedirs('assets')

def load_data():
    print("Loading data...")
    try:
        regimes = pd.read_csv('market_regimes.csv', parse_dates=['Date'], index_col='Date')
        try:
            signals = pd.read_csv('final_strategy_signals.csv', parse_dates=['Date'], index_col='Date')
        except:
            signals = None
        return regimes, signals
    except Exception as e:
        print(f"Error loading CSVs: {e}")
        return None, None

def plot_regimes(regimes, save_path):
    print("Plotting Regimes...")
    plt.figure(figsize=(12, 6))
    
    # Plot SPY Price
    plt.plot(regimes.index, regimes['SPY_Price'], color='black', alpha=0.3, label='SPY Price')
    
    # Regimes: 0=Bull(Green), 1=Neutral(Orange), 2=Crisis(Red)
    # Check unique regimes to assign colors dynamically if needed, but standard is:
    colors = {0: 'lime', 1: 'gold', 2: 'red', 3: 'blue'} 
    
    for regime_id in sorted(regimes['Regime'].unique()):
        subset = regimes[regimes['Regime'] == regime_id]
        plt.scatter(subset.index, subset['SPY_Price'], 
                   s=15, 
                   color=colors.get(regime_id, 'blue'),
                   label=f"Regime {regime_id}", zorder=10)
    
    plt.title('Market Regimes Detection (GMM)', fontsize=14)
    plt.ylabel('S&P 500 Price')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

def plot_performance(strategy_rets, spy_rets, save_path):
    print("Plotting Performance...")
    
    # Filter common dates
    common = strategy_rets.index.intersection(spy_rets.index)
    strat = strategy_rets.loc[common]
    bench = spy_rets.loc[common]
    
    strat_cum = (1 + strat).cumprod()
    spy_cum = (1 + bench).cumprod()
    
    plt.figure(figsize=(12, 6))
    plt.plot(strat_cum.index, strat_cum, label='Regime Strategy', color='blue', linewidth=2)
    plt.plot(spy_cum.index, spy_cum, label='S&P 500', color='gray', linestyle='--')
    
    plt.title('Strategy vs. Benchmark Cumulative Returns', fontsize=14)
    plt.ylabel('Growth of $1')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

def plot_drawdown(strategy_rets, spy_rets, save_path):
    print("Plotting Drawdown...")
    common = strategy_rets.index.intersection(spy_rets.index)
    strat = strategy_rets.loc[common]
    bench = spy_rets.loc[common]
    
    def get_dd(series):
        cum = (1 + series).cumprod()
        roll_max = cum.cummax()
        dd = (cum - roll_max) / roll_max
        return dd.fillna(0)
        
    strat_dd = get_dd(strat)
    spy_dd = get_dd(bench)
    
    plt.figure(figsize=(12, 4))
    plt.plot(strat_dd.index, strat_dd, label='Strategy Drawdown', color='red', alpha=0.7)
    plt.plot(spy_dd.index, spy_dd, label='SPY Drawdown', color='gray', alpha=0.4)
    
    plt.fill_between(strat_dd.index, strat_dd, 0, color='red', alpha=0.1)
    
    plt.title('Drawdown Analysis', fontsize=14)
    plt.ylabel('Drawdown (%)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

def save_metrics(strategy_rets, spy_rets):
    strat_total = (1 + strategy_rets).prod() - 1
    spy_total = (1 + spy_rets).prod() - 1
    strat_sharpe = (strategy_rets.mean() / strategy_rets.std()) * np.sqrt(252)
    
    with open('assets/results.txt', 'w') as f:
        f.write(f"Strategy Total Return: {strat_total:.2%}\n")
        f.write(f"Benchmark Total Return: {spy_total:.2%}\n")
        f.write(f"Strategy Sharpe Ratio: {strat_sharpe:.2f}\n")

def run_simple_backtest(regimes):
    print("Running Simple Backtest (SPY vs Cash)...")
    # Regime 0, 1 -> Long SPY. Regime 2 -> Cash (0%)
    # Adjust alignment: Signal today affects tomorrow? 
    # Usually backtests align signal[t-1] with Data[t].
    # Let's assume 'Regime' col in CSV is the regime for that day.
    
    # Create Strategy Return
    # If Regime == 2 (High Vol), go to Cash. Else SPY.
    
    # We shift signal by 1 day to trade on 'previous close' info?
    # Or assuming the CSV aligns signal with the day's return:
    # If 'Regime' is derived from GMM on *past* data, we can trade today.
    # Let's take the naive approach: Strategy = 0 if Regime==2 else SPY_Return
    
    strategy_rets = np.where(regimes['Regime'] == 2, 0, regimes['SPY_Return'])
    strategy_rets = pd.Series(strategy_rets, index=regimes.index)
    
    return strategy_rets, regimes['SPY_Return']

def run_sector_backtest(regimes, signals):
    print("Attempting Dynamic Sector Backtest...")
    
    # Cleaning tickers
    all_tickers = set()
    for basket_str in signals['Signal_Basket']:
        try:
            if isinstance(basket_str, str):
                basket = ast.literal_eval(basket_str)
                for t in basket:
                    # Filter out non-tickers like 'CASH'
                    if "CASH" not in t:
                        all_tickers.add(t)
        except:
            pass
            
    if 'SPY' in all_tickers:
        all_tickers.remove('SPY')
        
    ticker_list = list(all_tickers)
    ticker_list.append('SPY')
    
    print(f"Fetching data for: {ticker_list}")
    
    try:
        # Download data
        data = yf.download(ticker_list, start=regimes.index.min(), end=regimes.index.max(), progress=False)['Adj Close']
        
        # Handle single ticker result (Series) vs Multi (DataFrame)
        if isinstance(data, pd.Series):
            data = data.to_frame()
            
        data = data.ffill()
        returns_data = data.pct_change()
        
        # Check if SPY exists
        if 'SPY' not in returns_data.columns:
            raise ValueError("SPY data missing from download.")
            
        spy_rets = returns_data['SPY']
        
        # Calculate Strategy
        strategy_rets_list = []
        valid_dates = []
        
        common_idx = signals.index.intersection(returns_data.index)
        
        for date in common_idx:
            basket_str = signals.loc[date, 'Signal_Basket']
            daily_ret = 0.0
            
            try:
                if isinstance(basket_str, str):
                    basket = ast.literal_eval(basket_str)
                    
                    # Filter valid
                    valid_basket_tickers = [t for t in basket if t in returns_data.columns and "CASH" not in t]
                    
                    if valid_basket_tickers:
                        daily_ret = returns_data.loc[date, valid_basket_tickers].mean()
                    else:
                        # If basket is empty or only CASH, assumes 0
                        daily_ret = 0.0
            except:
                daily_ret = 0.0
                
            strategy_rets_list.append(daily_ret)
            valid_dates.append(date)
            
        strategy_series = pd.Series(strategy_rets_list, index=valid_dates)
        return strategy_series, spy_rets.loc[valid_dates]
        
    except Exception as e:
        print(f"Sector Fetch/Backtest failed: {e}")
        return None, None

def main():
    regimes, signals = load_data()
    if regimes is None:
        print("No regime data found.")
        return

    # Try Sector Backtest
    strat_rets = None
    spy_rets = None
    
    if signals is not None:
        strat_rets, spy_rets = run_sector_backtest(regimes, signals)
        
    # Fallback to Simple
    if strat_rets is None:
        print("Falling back to Simple Backtest...")
        strat_rets, spy_rets = run_simple_backtest(regimes)
    
    if strat_rets is None or spy_rets is None:
        print("Failed to generate returns.")
        return
        
    # Plotting
    plot_regimes(regimes, 'assets/market_regimes.png')
    plot_performance(strat_rets, spy_rets, 'assets/performance_comparison.png')
    plot_drawdown(strat_rets, spy_rets, 'assets/drawdown.png')
    
    save_metrics(strat_rets, spy_rets)
    print("Success.")

if __name__ == "__main__":
    main()
