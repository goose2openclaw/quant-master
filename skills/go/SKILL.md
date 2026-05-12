# go - Crypto Quantitative Simulation & Prediction Engine

## Overview
**go** is a comprehensive cryptocurrency quantitative analysis and prediction system that combines multi-agent simulation, historical backtesting, factor analysis, and self-iterating optimization. It serves as the "brain" for crypto quantitative trading decisions.

## Core Components

### 1. Mirofish 1000-Agent Simulation
- **1000 intelligent agents** running parallel simulations
- Multiple strategy types: aggressive, conservative, momentum, high-confidence,均值回归, 突破, 套利
- Real-time voting and consensus mechanism
- Bayesian probability updates

### 2. Strategy Library

#### Trend Following Strategies
- **RSI Momentum**: RSI < 30 BUY, RSI > 70 SELL
- **MACD Crossover**: Signal line crossover detection
- **Moving Average**: MA50/MA200 Golden Cross
- **Bollinger Bands**: Breakout and mean reversion
- **Supertrend**: Dynamic stop-loss following

#### Mean Reversion Strategies
- **RSI Mean Reversion**: Extreme RSI returns to mean
- **Bollinger Band Reversion**: Price returns to bands
- **ATR Channel**: Average True Range channels
- **VWAP Reversion**: Price deviation from VWAP

#### Volatility Strategies
- **Volatility Breakout**: High volatility expansion
- **ATR Trailing Stop**: Volatility-based exits
- **Keltner Channel**: Channel breakouts

#### Arbitrage Strategies
- **Cross-Exchange**: Price differences across exchanges
- **Funding Rate**: Futures-spot differential
- **Triangular**: USDT→BTC→ETH→USDT

### 3. Factor Analysis Engine

#### Technical Factors
| Factor | Description | Weight |
|--------|-------------|--------|
| RSI | Relative Strength Index | 0.15 |
| MACD | Moving Average Convergence | 0.12 |
| Bollinger | Bollinger Band Position | 0.10 |
| Volume | Volume Ratio vs Average | 0.13 |
| Momentum | 24h Price Change | 0.15 |
| Trend | MA Direction | 0.10 |
| Volatility | ATR Percentile | 0.12 |
| Support | Support/Resistance | 0.08 |
| Funding | Funding Rate Deviation | 0.05 |

#### On-Chain Factors
- Active Addresses
- Transaction Volume
- Gas Price
- DEX Volume
- Whale Transactions
- Exchange Flows
- Staking Ratio

#### Sentiment Factors
- Social Media Volume
- Google Trends
- News Sentiment
- Fear & Greed Index
- Options Open Interest
- Short Interest

#### Macro Factors
- BTC Dominance
- Altcoin Season Index
- USDT Market Cap
- Correlation with S&P 500
- Bond Yields
- Dollar Index (DXY)

#### "Mystical" Factors (玄学)
- **Moon Phase**: Lunar cycle correlation
- **Day of Week**: Weekday seasonality
- **Hour of Day**: Hourly volatility patterns
- **Chinese Zodiac**: CNY cycle effects
- **Market Cycle**: 4-year BTC halving cycle
- **Golden Ratio**: Fibonacci retracements
- **Pi Cycle**: Pi cycle indicators
- **Planetary**: Rare astronomical alignments

### 4. Backtesting Engine

```python
# Example backtest configuration
{
    'period': '2020-2026',
    'initial_capital': 10000,
    'commission': 0.001,
    'slippage': 0.0005,
    'positions': ['BTC', 'ETH', 'BNB', 'SOL', 'ADA', 'XRP', 'DOGE', 'AVAX', 'LINK', 'UNI', 
                  'BOME', 'PEPE', 'FLOKI', 'SHIB', 'WIF', 'BONK', 'TURBO', 'PUMP', 'NEIRO'],
    'timeframes': ['1h', '4h', '1d'],
    'strategies': ['rsil_momentum', 'macd_cross', 'bollinger_reversion', 'supertrend']
}
```

### 5. Coin Classification

#### Tier 1: Major (30 coins)
BTC, ETH, BNB, SOL, XRP, ADA, DOGE, DOT, LINK, UNI, AVAX, MATIC, ATOM, LTC, ETC, AAVE, APT, NEAR, FIL, ICP, INJ, TIA, SEI, SUI, OP, ARB, LDO, CRV, RDNT, ENS

#### Tier 2: Meme (25 coins)
PEPE, SHIB, FLOKI, WIF, BABYDOGE, COOKIE, AI, NEIRO, BOME, TURBO, PUMP, BONK, MEME, AIDOGE, ELON, BABYPEPE, POG, CHEEL, YOKO, WHALE, JENNER, BEBE, CHRO, MOODENG, FRED

#### Tier 3: Polymarket/Real World (20)
Polymarket events, Real-world assets, Prediction markets, Sports, Elections

#### Tier 4: DeFi/CG
AAVE, CRV, LD0, UNI, SUSHI, CAKE, Venus, Alpaca

### 6. Oracle Decision System

| RSI | Momentum | Volume | Funding | Score | Action |
|-----|----------|--------|---------|-------|--------|
| <25 | < -5% | High | Negative | ≥80 | STRONG_BUY |
| <30 | < -3% | >avg | Negative | ≥60 | BUY |
| <35 | < 0% | >avg | Neutral | ≥40 | ADD |
| 30-50 | 0% | avg | Neutral | 20-40 | HOLD |
| >65 | > 3% | <avg | Positive | <20 | REDUCE |
| >70 | > 5% | Low | Positive | <0 | SELL |

## API Usage

### Python API
```python
from skills.go import GoEngine

go = GoEngine(api_key='your_key', secret='your_secret')

# Get prediction for a coin
prediction = go.predict('BTC', timeframe='1h')
print(f"BTC signal: {prediction['signal']}")
print(f"Confidence: {prediction['confidence']}%")
print(f"Price target: ${prediction['target']}")

# Run simulation
result = go.simulate(coin='ETH', agents=1000, iterations=100)
print(f"Win rate: {result['win_rate']}%")
print(f"Expected return: {result['expected_return']}%")

# Backtest strategy
bt = go.backtest(strategy='rsil_momentum', 
                 coins=['BTC', 'ETH', 'SOL'],
                 period='2024-2026')
print(f"Sharpe: {bt['sharpe']}")
print(f"Max drawdown: {bt['max_dd']}%")
```

### Command Line
```bash
# Predict
go predict BTC --timeframe 1h --agents 1000

# Simulate
go simulate ETH --agents 1000 --iterations 100

# Backtest
go backtest --strategy rsil_momentum --coins BTC,ETH,SOL --period 2024-2026

# Scan market
go scan --tier meme --min-score 60

# Analyze
go analyze BTC --factors all
```

## Output Examples

### Prediction Output
```
🔮 GO Prediction: BTC (1h)
==========================
Signal:    🟢 STRONG_BUY
Score:     85/100
Confidence: 78%
Price:     $67,450
Target:    $72,000 (+6.7%)
Stop:      $64,000 (-5.1%)
Time:      2026-05-12 23:50

📊 Factor Breakdown:
  RSI:        24 (-30) ⭐
  Momentum:   -4.2% (+25)
  Volume:    1.8x avg (+20)
  Trend:     Bullish (+15)
  Funding:   -0.02% (+10)
  
🗳️ Agent Vote: 823/1000 BUY (82.3%)
```

## Self-Iteration Mechanism

### 1. Performance Tracking
- Daily P&L per strategy
- Win rate by market condition
- Factor weight optimization
- Hyperparameter tuning

### 2. Pattern Learning
- Market regime detection
- Seasonal patterns
- Cross-coin correlation
- Volatility clustering

### 3. Model Evolution
-淘汰 underperforming agents
- Breed successful strategies
- Mutate parameters
- Ensemble optimization

## Files
```
skills/go/
├── SKILL.md           # This file
├── go_engine.py       # Core engine
├── agents.py          # Mirofish agents
├── strategies.py      # Strategy library
├── factors.py         # Factor analysis
├── backtest.py       # Backtesting engine
├── oracle.py         # Decision system
└── data/             # Historical data
```

## Risk Warning
⚠️ This tool is for simulation and prediction only. Not financial advice. Cryptocurrency trading involves substantial risk of loss.

---

**Version**: 1.0.0
**Created**: 2026-05-12
**Author**: OpenClaw AI Assistant
