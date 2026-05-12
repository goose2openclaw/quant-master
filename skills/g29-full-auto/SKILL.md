# G29 Full Auto Trading Skill

## Overview
Autonomous cryptocurrency trading system using Oracle scoring algorithm for intelligent buy/sell decisions across Binance Spot, Cross Margin, Isolated, and Futures accounts.

## Features
- **Oracle Scoring System**: RSI + Momentum based scoring for buy/sell signals
- **Multi-Account Support**: Spot, Cross Margin, Isolated, Futures
- **Auto Fund Allocation**: Automatically sells low-score assets to fund high-score buys
- **30-second Scan Interval**: Fast response to market opportunities
- **Meme Coin Optimization**: Special handling for BOME, TURBO, PUMP, NEIRO

## Files
- `scripts/g29_full.py` - Main trading script
- `scripts/start_g29.sh` - Launcher script
- `dashboard/` - Web dashboard for monitoring

## Configuration
Edit the following in `scripts/g29_full.py`:
```python
API_KEY = 'your_api_key'
API_SECRET = 'your_api_secret'
PROXY = "http://your_proxy:port"
```

## Usage
```bash
# Start trading
bash scripts/start_g29.sh

# View logs
tail -f logs/g29.log
```

## Oracle Scoring
| RSI | Momentum | Score | Action |
|-----|----------|-------|--------|
| <25 | any | +50 | STRONG_BUY |
| <30 | <0 | +40 | BUY |
| <35 | <0 | +25 | ADD |
| >75 | any | -50 | STRONG_SELL |
| >70 | >0 | -35 | SELL |

## Risk Warning
⚠️ This is an aggressive trading bot. Use with caution and only invest what you can afford to lose.
