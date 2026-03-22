# HK Stock Multi-Factor Model / 港股多因子模型

A factor-based long-short equity strategy backtested on 20 Hang Seng constituent stocks.

基于20只恒生指数成分股的因子多空策略回测系统。

---

## What This Does / 项目简介

Downloads 2 years of daily price data for 20 Hong Kong stocks, constructs three classic equity factors, combines them into a multi-factor model, and evaluates performance using industry-standard metrics.

下载20只港股两年的日线数据，构建三个经典股票因子，组合为多因子模型，并使用行业标准指标评估表现。

---

## Factors / 因子说明

| Factor / 因子 | Logic / 逻辑 | Window / 窗口 |
|--------|-------|--------|
| **Momentum / 动量** | Stocks that went up tend to keep going up / 过去涨的股票倾向于继续涨 | 20 days / 20天 |
| **Short-term Reversal / 短期反转** | Stocks that dropped sharply tend to bounce back / 短期急跌的股票倾向于反弹 | 5 days / 5天 |
| **Low Volatility / 低波动率** | Less volatile stocks tend to outperform / 波动率低的股票收益反而更高 | 20 days / 20天 |
| **Combo / 组合因子** | Equal-weighted z-score combination of all three / 三个因子等权z-score组合 | — |

---

## Strategy / 策略逻辑

- Each day, rank all 20 stocks by factor value / 每天按因子值对20只股票排名
- Go long the top 5 (strongest signal) / 做多排名前5（信号最强）
- Go short the bottom 5 (weakest signal) / 做空排名后5（信号最弱）
- Equal-weight positions within each leg / 组内等权配置
- 1-day lag to avoid look-ahead bias / 延迟1天避免前瞻偏差

---

## Key Metrics / 核心指标

| Metric / 指标 | Description / 说明 |
|--------|--------|
| **Annualized Return / 年化收益** | Mean daily return × 252 / 日均收益 × 252 |
| **Sharpe Ratio / 夏普比率** | Annualized return / annualized volatility / 年化收益 / 年化波动率 |
| **Maximum Drawdown / 最大回撤** | Largest peak-to-trough decline / 从最高点到最低点的最大跌幅 |
| **Rank IC** | Daily Spearman correlation between factor values and next-day returns / 因子值与次日收益的每日Spearman相关系数 |
| **ICIR** | IC mean / IC std, the signal's information ratio / IC均值 / IC标准差，信号的信噪比 |

---

## Results / 研究发现

The Reversal factor showed the strongest standalone performance with low correlation to the Hang Seng Index, suggesting genuine market-neutral alpha. The Combo factor improved stability (lower drawdown) compared to individual factors, though its absolute return was diluted by weaker components.

反转因子表现最强，且与恒生指数走势相关性低，具有真正的市场中性Alpha。组合因子相比单因子降低了回撤、提升了稳定性，但绝对收益被较弱的因子稀释。

![Factor Report](factor_report.png)

---

## Setup / 运行方法

```bash
pip install pandas numpy matplotlib yfinance scipy
python3 factor_model.py
```

---

## Project Structure / 项目结构

```
├── factor_model.py        # Main script / 主代码
├── factor_report.png      # Output chart / 输出图表
└── README.md
```

---


