---

# **Research Report: Dynamic Regime-Based Sector Allocation & Tail Risk Hedging**

**Author:** Tanishk Yadav
**Date:** January 2026
**Institution:** New York University, Tandon School of Engineering
**Project Type:** Quantitative Risk Management / Algorithmic Trading

---

## **1. Executive Summary**

Modern portfolio theory often fails during systemic crises due to **correlation breakdown**—the tendency of all asset correlations to converge to 1.0 during market crashes. This project develops a dynamic risk management system that utilizes **Gaussian Mixture Models (GMM)** to detect latent market regimes and adjust sector exposure accordingly.

By analyzing S&P 500 sector data from 2018 to 2026, we identified three distinct market states: *Low Volatility (Bull)*, *Transition (Uncertainty)*, and *High Volatility (Crisis)*. An exhaustive grid-search optimization algorithm was then employed to construct the optimal sector basket for each regime.

**Key Findings:**

* **Alpha Generation:** The optimized strategy significantly reduced downside risk while maintaining participation in bull markets.
* **Risk Reduction:** Maximum Drawdown was reduced from **-35.75%** (S&P 500 Benchmark) to **-16.11%** (Dynamic Strategy).
* **Capital Preservation:** The model correctly identified "Cash" (Treasuries) as the only statistically viable hedge during Regime 2 (Crisis), rejecting the common heuristic of using "Defensive Stocks" during systemic collapses.

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

---

## **4. Structural Analysis: The Diversification Breakdown**

A core hypothesis of this thesis is that diversification provides a false sense of security during crashes. We validated this using **Hierarchical Clustering**.

### **4.1 Dendrogram Analysis**

Using Ward's Linkage method on the correlation matrix of the 11 sectors, we observed a structural collapse during Regime 2.

* **In Regime 0 (Bull):** The dendrogram shows "tall" branches, indicating high Euclidean distance between clusters. *Result: Tech (XLK) can be effectively hedged with Energy (XLE).*
* **In Regime 2 (Crisis):** The dendrogram "flattens." The distance between disparate sectors (e.g., Tech and Utilities) approaches zero. *Result: All assets fall together.*

> **Quant Insight:** This structural breakdown confirms that "Sector Rotation" is insufficient during a Regime 2 event. A purely "Risk-Off" asset (Cash/Treasuries) is required.

---

## **5. Strategy Optimization & Backtesting**

We employed an **Exhaustive Grid Search** to determine the optimal asset basket for each regime. The algorithm tested  combinations per regime to maximize the Sharpe Ratio and minimize Max Drawdown.

### **5.1 The Optimization Process**

1. **Baseline (Naive):** Buy & Hold SPY.
2. **Iteration 1 (Active):** Rotate into Defensive Stocks (XLU, XLP) during Crisis.
* *Result:* Failed. Drawdown -37%. (Defensive stocks still have Beta > 0.5 during crashes).


3. **Iteration 2 (AI-Selected):** Allowed the optimizer to select "Cash" (0% Return, 0 Volatility).
* *Result:* Success. The algorithm rejected all stock sectors for Regime 2.



### **5.2 The "Golden Strategy" Configuration**

| Regime | Signal | Optimized Basket | Rationale |
| --- | --- | --- | --- |
| **0** | **Bull** | `XLF, XLU, XLK, XLV, XLC` | **"All-Weather Growth"**<br>

<br>Balances aggressive Tech/Comm (XLK, XLC) with Financials (XLF) and Healthcare (XLV) to capture upside while smoothing daily variance. |
| **1** | **Transition** | `XLU, XLV, XLP` | **"The Shield"**<br>

<br>When VIX rises, the model retreats to low-beta sectors (Utilities, Staples). This prevents "Whipsaw" losses during false alarms. |
| **2** | **Crisis** | `CASH` | **"The Stop Loss"**<br>

<br>Complete exit to risk-free assets. This avoids the "left tail" events (e.g., COVID Crash) entirely. |

---

## **6. Performance Metrics**

The dynamic strategy was backtested against the S&P 500 (SPY) Buy & Hold approach over the 2018–2026 period.

| Metric | S&P 500 (Benchmark) | Dynamic Regime Strategy | Improvement |
| --- | --- | --- | --- |
| **Max Drawdown** | **-35.75%** | **-16.11%** | **Risk Halved** |
| **Recovery Load** | +55.6% return needed to recover | +19.2% return needed to recover | **Faster Compounding** |
| **Sharpe Ratio** | 0.65 | **0.86** | **Superior Risk-Adj Return** |
| **Stress Test (2020)** | Full Crash Exposure | Exited to Cash in early March | **Pass** |
| **Stress Test (2022)** | -19% Loss | Hedged via Regime 1 Baskets | **Pass** |

### **6.1 Drawdown Analysis**

The strategy's primary alpha comes from **capital preservation**. By avoiding the deep drawdowns of 2020 and 2022, the portfolio requires significantly less "recovery growth" to reach new all-time highs. This illustrates the mathematical reality that *avoiding a 50% loss is more valuable than capturing a 50% gain.*

---

## **7. Conclusion & Future Work**

This project demonstrates that **Regime-Conditional Correlation** is a solvable problem using unsupervised learning. The GMM successfully identified the latent "Crisis State" where diversification fails, allowing the system to mechanically enact a "Stop Loss" by moving to Cash.

**Implications for Fund Management:**
The inclusion of a "Transition Regime" (Regime 1) is the critical innovation. Unlike binary "Risk On / Risk Off" models which suffer from excessive trading costs and whipsaw, the Transition Regime acts as a buffer, allowing the portfolio to hold Defensive Equities before committing to a full exit.

**Future Extensions:**

* Integration of alternative data (Sentiment Analysis) to speed up regime detection.
* Application of the regime overlay to specific Factor Strategies (Momentum vs. Mean Reversion).

---
