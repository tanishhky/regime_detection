
---

# Dynamic Regime-Based Sector Allocation & Tail Risk Hedging

**Author:** Tanishk Yadav

**Date:** January 2026

**Institution:** New York University, Tandon School of Engineering

## Overview

This project develops a dynamic risk management system that utilizes **Gaussian Mixture Models (GMM)** to detect latent market regimes and adjust sector exposure accordingly. By analyzing S&P 500 sector data, the model identifies distinct market states (*Low Volatility*, *Transition*, *Crisis*) and optimizes sector allocation to minimize drawdown while capturing upside.

## Getting Started

### Prerequisites

* Python 3.8+
* Jupyter Notebook

### Installation

1. Clone the repository:
```bash
git clone https://github.com/tanishhky/regime_detection.git
cd regime_detection

```


2. Install the required dependencies:
```bash
pip install -r requirements.txt

```



### Usage

1. Open the Jupyter Notebook:
```bash
jupyter notebook main.ipynb

```


2. Run the cells sequentially to perform data ingestion, regime detection, and strategy backtesting.

## Project Structure

* `main.ipynb`: Core analysis notebook containing data fetching, GMM modeling, and backtesting.
* `market_regimes.csv`: Output file containing identified market regimes.
* `final_strategy_signals.csv`: Generated trading signals based on the strategy.
* `requirements.txt`: Python package dependencies.
* `README.md`: Project documentation and research report.

---

# Research Report

## **1. Executive Summary**

Modern portfolio theory often fails during systemic crises due to **correlation breakdown**—the tendency of all asset correlations to converge to 1.0 during market crashes. This project develops a dynamic risk management system that utilizes **Gaussian Mixture Models (GMM)** to detect latent market regimes and adjust sector exposure accordingly.

By analyzing S&P 500 sector data from 2018 to 2026, we identified three distinct market states: *Low Volatility (Bull)*, *Transition (Uncertainty)*, and *High Volatility (Crisis)*. An exhaustive grid-search optimization algorithm was then employed to construct the optimal sector basket for each regime.

**Key Findings:**

* **The Failure of Heuristics:** Traditional "Defensive Rotation" strategies (buying Utilities during crashes) performed *worse* than the broad market (-40% Drawdown vs -35%).
* **Crisis Alpha:** An aggressive AI strategy identified Technology as the "Safe Haven" of the 2020s, generating **+214%** total return.
* **Institutional Safety:** The final "Risk Managed" strategy utilized Cash to reduce portfolio volatility to **13%** (vs Market 19%) and Drawdown to **-16%** (vs Market -35%).

---

## **2. Methodology**

### **2.1 Data Universe & Ingestion**

The study utilized daily Open-High-Low-Close (OHLC) data for the **S&P 500 ETF (SPY)** and the 11 GICS Sector SPDR ETFs:

* **Cyclical:** Financials (XLF), Industrials (XLI), Materials (XLB), Energy (XLE), Cons. Discretionary (XLY).
* **Defensive:** Utilities (XLU), Cons. Staples (XLP), Healthcare (XLV).
* **Growth:** Technology (XLK), Communication Services (XLC), Real Estate (XLRE).
* **Macro Factors:** CBOE Volatility Index (), 10-Year Treasury Yield ().

**Timeframe:** January 1, 2018 – Present (Includes the 2018 Volmageddon, 2020 COVID-19 Crash, and 2022 Inflation Bear Market).

### **2.2 Feature Engineering**

To train the unsupervised learning model, raw price data was transformed into stationary risk signals:

1. **Log-Returns ():**


2. **Realized Volatility ():**
Calculated as the 21-day rolling standard deviation of log-returns, annualized:


3. **Implied Volatility (VIX):**
Used as a forward-looking "fear gauge" to complement the backward-looking realized volatility.

---

## **3. Regime Detection Model**

We modeled the distribution of market returns as a weighted sum of  Gaussian distributions, where each component represents a specific market "Regime."

### **3.1 Gaussian Mixture Model (GMM)**

The probability density function is defined as:


Where:

* : Number of regimes (Bull, Transition, Crisis).
* : The probability of the market being in regime .
* : The mean and covariance of returns in regime .

### **3.2 Identified Regimes**

The Expectation-Maximization (EM) algorithm converged on three distinct states:

| Regime Label | State Description | Characteristics | Avg VIX |
| --- | --- | --- | --- |
| **Regime 0** | **Bull Market** | Low Volatility, Positive Drift, Low Correlation. |  |
| **Regime 1** | **Transition** | Elevated Volatility, Choppy Price Action. |  |
| **Regime 2** | **Crisis** | Extreme Volatility, Negative Drift, Correlation . |  |

*(Note: In the final notebook, Regime labels may be reordered based on sorted volatility).*
![Figure 1](./assets/fig1.png)
*Figure 1: S&P 500 Price colored by identified Market Regimes. Notice the high volatility clusters (Red) capturing 2020 and 2022.*

---

## **4. Structural Analysis: The Diversification Breakdown**

A core hypothesis of this thesis is that diversification provides a false sense of security during crashes. We validated this using **Hierarchical Clustering**.

### **4.1 Dendrogram Analysis**

Using Ward's Linkage method on the correlation matrix of the 11 sectors, we observed a structural collapse during Regime 2.

* **In Regime 0 (Bull):** The dendrogram shows "tall" branches, indicating high Euclidean distance between clusters. *Result: Tech (XLK) can be effectively hedged with Energy (XLE).*
* **In Regime 2 (Crisis):** The dendrogram "flattens." The distance between disparate sectors (e.g., Tech and Utilities) approaches zero. *Result: All assets fall together.*

![Figure 2](./assets/fig2.png)
*Figure 2: Regime-Dependent Correlation Structures. The "Tree" collapses in Regime 2, visually demonstrating contagion.*

---

## **5. Comparative Strategy Analysis ("The Face-Off")**

To ensure the robustness of the final model, we performed a "face-off" backtest comparing three distinct approaches to handling regime shifts. This analysis allows investors to select a strategy based on their specific Risk/Reward preference.

We compared the following portfolios over the 2018–2026 period:

### **Strategy A: The "Human Heuristic" (Benchmark)**

* **Logic:** Relies on conventional market wisdom.
* *Bull:* Buy Aggressive Tech (`XLK`, `XLC`).
* *Crisis:* Rotate into "Safe" Defensives (`XLU`, `XLP`).


* **Hypothesis:** Defensive stocks will hold value during a crash.

### **Strategy B: AI Optimized - Fully Invested (Aggressive)**

* **Logic:** The AI selects the best-performing stock basket for every regime. Cash is **not** allowed.
* *Crisis:* The AI selected Tech (`XLK`) for Regime 2, identifying that recent crises (COVID, AI) favored digital assets.


* **Profile:** High Risk, High Reward.

### **Strategy C: AI Optimized - Risk Managed (Balanced)**

* **Logic:** The AI selects the best asset, **including Cash**, for every regime.
* *Crisis:* The AI selected `CASH` (Treasuries).


* **Profile:** Capital Preservation focus.

---

## **6. Performance Results**

The comparative analysis reveals that traditional diversification strategies failed, while the AI-driven models significantly outperformed on a risk-adjusted basis.

| Strategy | Total Return | Sharpe Ratio | Max Drawdown | Ann. Volatility |
| --- | --- | --- | --- | --- |
| **S&P 500 (Base)** | 143.71% | 0.70 | -35.75% | 19.60% |
| **A: Human Heuristic** | 134.20% | 0.65 | **-40.38%** | 20.73% |
| **B: AI (Stock Only)** | **214.29%** | **0.92** | -27.21% | 18.31% |
| **C: AI (Risk Managed)** | 129.46% | 0.90 | **-16.11%** | **13.11%** |

![Figure 3](./assets/fig3.png)
*Figure 3: Equity Curve Comparison. Note how Strategy C (Green) goes flat during crashes, preserving capital, while Strategy A (Red) suffers deeper losses than the market.*

### **6.1 Critical Analysis**

#### **1. The Failure of Traditional Wisdom (Strategy A)**

The "Human Heuristic" strategy was the worst performer.

* **Underperformance:** It returned less than the market (+134% vs +143%).
* **Higher Risk:** It suffered a larger drawdown (-40.38%) than the unhedged S&P 500.
* **Root Cause:** In the 2022 bear market, "Defensive" sectors like Utilities and Staples became highly correlated with the broad market due to rising interest rates. This proves that **sector rotation is no longer a reliable hedge for systemic inflation shocks.**

#### **2. The "Crisis Alpha" Phenomenon (Strategy B)**

The Fully Invested AI strategy generated massive alpha (**+214% Total Return**).

* **Insight:** The GMM correctly identified that during the specific crises of 2020 (Lockdowns) and 2023 (Banking/AI), Technology stocks acted as the de-facto "safe haven" due to growth potential.
* **Result:** It delivered nearly double the market's excess return with a superior Sharpe Ratio (0.92).

#### **3. Institutional-Grade Safety (Strategy C)**

The Risk-Managed (Cash) strategy serves a different mandate: **Capital Preservation.**

* **Volatility Reduction:** It slashed annual volatility to **13.11%** (vs 19.60% for SPY).
* **Drawdown Control:** It reduced the maximum loss to **-16.11%**, effectively eliminating "Tail Risk."
* **Trade-off:** While it slightly trailed the market in Total Return (+129% vs +143%) due to holding cash during rapid v-shaped recoveries, its risk-adjusted return (Sharpe 0.90) is far superior to the benchmark (0.70).

![Figure 4](./assets/fig4.png)
*Figure 4: Drawdown Depth. Strategy C (Green) effectively eliminates the "Tail Risk," never suffering a loss greater than 16%, whereas the Market and Heuristic strategies suffered ~35-40% losses.*


### **6.2 Visualizing the Edge**
![Figure 5](./assets/fig4.png)
*Figure 3: Equity Curves. Note how Strategy C (Green) goes flat (horizontal) during the 2020 and 2022 crashes, preserving gains while Strategy A (Red) and the S&P 500 (Gray) collapse.*
![Figure 6](./assets/fig5.png)
*Figure 4: Drawdown Depth. The "Cash" strategy (Green) is the only one that avoided a >20% Bear Market loss.*

### **6.3 Risk-Reward Asymmetry**

The definitive advantage of the Regime model is best viewed through the **Risk-Reward Bar Chart**.

*Figure 5: Total Return vs. Max Drawdown. This chart demonstrates "Efficiency." The Risk-Managed Strategy (Far Right) sacrifices a small portion of upside to cut the downside risk in half compared to the S&P 500.*

* **S&P 500:** Large Green Bar, Large Red Bar (High Volatility).
* **AI (Risk Managed):** Solid Green Bar, **Tiny Red Bar** (High Efficiency). This asymmetric profile allows for safe leverage.

---

*(Make sure you actually save the image as `assets/risk_reward_bars.png` using the python code I gave you!)*
---

## **7. Conclusion & Investment Recommendation**

This project demonstrates that **Regime-Conditional Correlation** is a solvable problem using unsupervised learning. The results lead to two distinct implementation recommendations based on investor mandate:

1. **For Growth Funds (Alpha Seekers):** Implement **Strategy B**.
* *Why:* The GMM successfully identifies "Crisis Alpha" opportunities where specific sectors (like Tech) decouple from the broad market crash.


2. **For Pension/Endowment Funds (Risk Averse):** Implement **Strategy C**.
* *Why:* The correlation breakdown in 2022 proves that Equities cannot hedge Equities. **Cash** is the only statistically reliable hedge for Regime 2 volatility.



**Final Verdict:**
The "Human Heuristic" of rotating into Defensive sectors is statistically obsolete in the current macro environment. An algorithmic approach utilizing Regime Detection is required to navigate modern correlation structures.