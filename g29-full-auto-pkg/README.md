# G29 Full Auto Trading System

Autonomous cryptocurrency trading bot using Oracle scoring algorithm for Binance.

## Features

- 🤖 **Fully Autonomous** - 24/7 automated trading
- 📊 **Oracle Scoring** - RSI + Momentum based signal analysis
- 💰 **Multi-Account** - Spot, Cross Margin, Isolated, Futures
- ⚡ **30-Second Scan** - Fast response to market opportunities
- 🧠 **Self-Learning** - Adaptive strategy based on market conditions

## Quick Start

```bash
# 1. Configure API credentials
nano src/g29_full.py

# 2. Start trading
bash scripts/start_g29.sh

# 3. View dashboard
# Open http://localhost:8090
```

## Configuration

Edit `src/g29_full.py`:

```python
API_KEY = 'your_binance_api_key'
API_SECRET = 'your_binance_api_secret'
PROXY = "http://your_proxy:port"  # Optional
```

## Oracle Scoring Algorithm

| RSI | Momentum | Score | Signal |
|-----|----------|-------|--------|
| <25 | - | +50 | STRONG_BUY |
| <30 | <0 | +40 | BUY |
| <35 | <0 | +25 | ADD |
| >75 | - | -50 | STRONG_SELL |
| >70 | >0 | -35 | SELL |

## Supported Coins

- **Major**: BTC, ETH, LINK, SOL, UNI
- **Meme**: BOME, TURBO, PUMP, NEIRO

## Risk Warning

⚠️ **HIGH RISK**: This is an aggressive trading bot. cryptocurrency trading involves substantial risk of loss. Only invest what you can afford to lose.

## License

MIT License - Use at your own risk.
