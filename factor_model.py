"""
============================================================
HK Stock Multi-Factor Model
============================================================
A factor-based long-short equity strategy for Hong Kong stocks.

Factors:
  - Momentum (20-day cumulative log return)
  - Short-term Reversal (5-day inverse cumulative log return)
  - Low Volatility (20-day inverse realized volatility)
  - Combo (equal-weighted z-score combination)

Usage:
  pip install pandas numpy matplotlib yfinance scipy
  python3 factor_model.py
============================================================
"""

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import warnings
warnings.filterwarnings("ignore")


# ============================================================
# Config
# ============================================================

TICKERS = [
    "0700.HK",  # Tencent
    "9988.HK",  # Alibaba
    "0005.HK",  # HSBC
    "1299.HK",  # AIA
    "0941.HK",  # China Mobile
    "2318.HK",  # Ping An
    "0388.HK",  # HKEX
    "0001.HK",  # CK Hutchison
    "0027.HK",  # Galaxy Entertainment
    "1928.HK",  # Sands China
    "0023.HK",  # Hang Seng Bank
    "0016.HK",  # SHK Properties
    "0002.HK",  # CLP Holdings
    "0003.HK",  # HK & China Gas
    "0006.HK",  # Power Assets
    "1038.HK",  # CK Infrastructure
    "0012.HK",  # Henderson Land
    "0017.HK",  # New World Dev
    "0066.HK",  # MTR Corporation
    "0883.HK",  # CNOOC
]

START_DATE = "2022-01-01"
END_DATE = "2024-12-31"
N_LONG = 5
N_SHORT = 5


# ============================================================
# Data
# ============================================================

def download_data(tickers, start, end):
    """Download daily price data from Yahoo Finance."""
    print("Downloading data...")
    data = yf.download(tickers, start=start, end=end, progress=False)
    close = data["Close"]
    log_returns = np.log(close / close.shift(1)).dropna()
    print(f"Done: {log_returns.shape[0]} trading days, {log_returns.shape[1]} stocks")
    return close, log_returns


# ============================================================
# Factor Construction
# ============================================================

def build_factors(log_returns):
    """Build momentum, reversal, and low-volatility factors."""
    momentum = log_returns.rolling(window=20).sum()
    reversal = -log_returns.rolling(window=5).sum()
    volatility = -log_returns.rolling(window=20).std()
    return momentum, reversal, volatility


def zscore_cross_section(df):
    """Cross-sectional z-score: standardize each row (each day) across stocks."""
    return df.sub(df.mean(axis=1), axis=0).div(df.std(axis=1), axis=0)


def build_combo_factor(momentum, reversal, volatility):
    """Combine three factors using equal-weighted z-scores."""
    mom_z = zscore_cross_section(momentum.dropna(how="all"))
    rev_z = zscore_cross_section(reversal.dropna(how="all"))
    vol_z = zscore_cross_section(volatility.dropna(how="all"))

    common_dates = mom_z.index.intersection(rev_z.index).intersection(vol_z.index)
    combo = (mom_z.loc[common_dates] + rev_z.loc[common_dates] + vol_z.loc[common_dates]) / 3
    return combo


# ============================================================
# Backtest
# ============================================================

def backtest_factor(factor, returns, n_long=N_LONG, n_short=N_SHORT, name="Factor"):
    """
    Long-short backtest for a given factor.
    
    - Ranks stocks each day by factor value
    - Goes long top n_long, short bottom n_short
    - Uses 1-day lag to avoid look-ahead bias
    - Computes Rank IC (Spearman) each day
    
    Returns a dict with performance metrics and time series.
    """
    factor_clean = factor.dropna(how="all")
    returns_aligned = returns.loc[factor_clean.index.intersection(returns.index)]

    factor_shifted = factor_clean.shift(1).dropna()
    common_dates = factor_shifted.index.intersection(returns_aligned.index)
    factor_shifted = factor_shifted.loc[common_dates]
    future_ret = returns_aligned.loc[common_dates]

    ranks = factor_shifted.rank(axis=1, ascending=False)

    portfolio_returns = []
    ic_series = []

    for date in ranks.index:
        rank_today = ranks.loc[date]
        ret_today = future_ret.loc[date]

        valid = rank_today.dropna().index.intersection(ret_today.dropna().index)
        if len(valid) < n_long + n_short:
            continue

        rank_valid = rank_today[valid]
        ret_valid = ret_today[valid]

        long_stocks = rank_valid.nlargest(n_long).index
        short_stocks = rank_valid.nsmallest(n_short).index

        long_ret = ret_valid[long_stocks].mean()
        short_ret = ret_valid[short_stocks].mean()
        ls_ret = long_ret - short_ret
        portfolio_returns.append({"date": date, "return": ls_ret})

        # Rank IC
        f_today = factor_shifted.loc[date]
        r_today = future_ret.loc[date]
        common = f_today.dropna().index.intersection(r_today.dropna().index)
        if len(common) >= 10:
            ic, pvalue = stats.spearmanr(f_today[common], r_today[common])
            ic_series.append({"date": date, "IC": ic, "p_value": pvalue})

    pf = pd.DataFrame(portfolio_returns).set_index("date")
    pf["cumulative"] = pf["return"].cumsum()
    ic_df = pd.DataFrame(ic_series).set_index("date")

    ann_ret = pf["return"].mean() * 252
    ann_vol = pf["return"].std() * np.sqrt(252)
    sharpe = ann_ret / ann_vol if ann_vol > 0 else 0
    cummax = pf["cumulative"].cummax()
    max_dd = (pf["cumulative"] - cummax).min()
    ic_mean = ic_df["IC"].mean()
    icir = ic_mean / ic_df["IC"].std() if ic_df["IC"].std() > 0 else 0

    return {
        "name": name,
        "portfolio": pf,
        "ic_df": ic_df,
        "ann_return": ann_ret,
        "ann_vol": ann_vol,
        "sharpe": sharpe,
        "max_drawdown": max_dd,
        "ic_mean": ic_mean,
        "icir": icir,
    }


# ============================================================
# Visualization
# ============================================================

def plot_report(results, combo_result, save_path="factor_report.png"):
    """Generate a 2x2 performance report chart."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle("HK Stock Factor Model - Performance Report",
                 fontsize=16, fontweight="bold", y=1.02)

    colors = ["#2E75B6", "#E74C3C", "#2ECC71", "#F39C12"]

    # Chart 1: Cumulative returns comparison
    ax1 = axes[0, 0]
    for i, res in enumerate(results):
        ax1.plot(res["portfolio"]["cumulative"],
                 label=res["name"], color=colors[i], linewidth=1.5)
    ax1.plot(combo_result["portfolio"]["cumulative"],
             label=combo_result["name"], color=colors[3], linewidth=2.5, linestyle="--")
    ax1.set_title("Cumulative Returns Comparison")
    ax1.legend(fontsize=9)
    ax1.axhline(y=0, color="gray", linestyle="--", alpha=0.5)
    ax1.grid(True, alpha=0.3)

    # Chart 2: IC time series (combo factor)
    ax2 = axes[0, 1]
    ic_df = combo_result["ic_df"]
    ax2.bar(ic_df.index, ic_df["IC"], width=2,
            color=["#2E75B6" if x > 0 else "#E74C3C" for x in ic_df["IC"]], alpha=0.6)
    ax2.axhline(y=0, color="black", linewidth=0.5)
    ax2.axhline(y=ic_df["IC"].mean(), color="green", linestyle="--",
                label=f"IC Mean = {ic_df['IC'].mean():.4f}")
    ax2.set_title("Combo Factor - Daily IC")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Chart 3: Drawdown comparison
    ax3 = axes[1, 0]
    for i, res in enumerate(results):
        cum = res["portfolio"]["cumulative"]
        dd = cum - cum.cummax()
        ax3.plot(dd, label=res["name"], color=colors[i], alpha=0.7)
    combo_cum = combo_result["portfolio"]["cumulative"]
    combo_dd = combo_cum - combo_cum.cummax()
    ax3.fill_between(combo_dd.index, combo_dd.values,
                     color=colors[3], alpha=0.3, label=combo_result["name"])
    ax3.set_title("Drawdown Comparison")
    ax3.legend(fontsize=9)
    ax3.grid(True, alpha=0.3)

    # Chart 4: Sharpe comparison bar chart
    ax4 = axes[1, 1]
    all_results = results + [combo_result]
    names = [r["name"] for r in all_results]
    sharpes = [r["sharpe"] for r in all_results]
    bars = ax4.bar(names, sharpes, color=colors[:len(names)], alpha=0.8,
                   edgecolor="white", linewidth=1.5)
    ax4.set_title("Sharpe Ratio Comparison")
    ax4.axhline(y=0, color="gray", linestyle="--")
    for bar, val in zip(bars, sharpes):
        ax4.text(bar.get_x() + bar.get_width() / 2., bar.get_height() + 0.02,
                 f"{val:.3f}", ha="center", va="bottom", fontsize=10, fontweight="bold")
    ax4.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    print(f"Chart saved: {save_path}")


# ============================================================
# Main
# ============================================================

def main():
    # Download data
    close, log_returns = download_data(TICKERS, START_DATE, END_DATE)

    # Build factors
    momentum, reversal, volatility = build_factors(log_returns)
    combo = build_combo_factor(momentum, reversal, volatility)

    # Backtest all factors
    print("\n" + "=" * 60)
    print("  Factor Backtest Results")
    print("=" * 60)

    res_mom = backtest_factor(momentum, log_returns, name="Momentum(20D)")
    res_rev = backtest_factor(reversal, log_returns, name="Reversal(5D)")
    res_vol = backtest_factor(volatility, log_returns, name="Low Vol(20D)")
    res_combo = backtest_factor(combo, log_returns, name="Combo")

    # Summary table
    print("\n" + "=" * 60)
    print("  Performance Summary")
    print("=" * 60)

    summary = []
    for res in [res_mom, res_rev, res_vol, res_combo]:
        summary.append({
            "Factor": res["name"],
            "Ann Return": f"{res['ann_return']:.4f}",
            "Sharpe": f"{res['sharpe']:.4f}",
            "Max DD": f"{res['max_drawdown']:.4f}",
            "IC Mean": f"{res['ic_mean']:.4f}",
            "ICIR": f"{res['icir']:.4f}",
        })
    print(f"\n{pd.DataFrame(summary).set_index('Factor')}")

    # Plot
    plot_report([res_mom, res_rev, res_vol], res_combo)


if __name__ == "__main__":
    main()
