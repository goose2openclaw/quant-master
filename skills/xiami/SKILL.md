---
name: xiami
slug: xiami
version: 1.0.0
description: |
  XIAMI (XiaMi) - 融合9大交易机器人精华的多策略加密货币交易系统
  
  核心理念: "像虾米一样敏感 - 小规模、灵活、适应性强"
  
  结合了:
  - trading-brain 信息规模优势
  - rho-signals 多指标信号系统
  - binance-grid-trading 网格交易
  - polymarket-arbitrage 套利监控
  - freqtrade 趋势跟踪
author: xiami-trading
tags: [crypto, trading, bot, multi-strategy, grid, arbitrage, signals, AI]
homepage: https://github.com/xiami-trading/xiami
metadata: 
  openclaw:
    emoji: "🦐"
    requires:
      bins: ["python3"]
      env:
        - BINANCE_API_KEY
        - BINANCE_SECRET
    configPaths: ["~/xiami/"]
---

# 🦐 XIAMI Trading System

> eXtensible AI-Driven Multi-source Intelligent trading

## 核心理念

"像虾米一样敏感 - 小规模、灵活、适应性强"

XIAMI 融合了 9 大交易机器人的精华，创建了一个自适应多策略交易系统。

## 策略架构

### 🦐 模式1: 趋势确认模式 (50%仓位)

**条件 (满足2/3):**
- RSI(4h) < 40 (超卖)
- MACD 金叉
- 价格站上 SMA20

**执行:**
- 仓位: 10%
- 止损: 5%
- 止盈: 15% 或 RSI > 65

### 🦐 模式2: 网格震荡模式 (30%仓位)

**条件:**
- 波动率 < 3%
- 价格在 SMA20-SMA50 区间

**执行:**
- 网格: 5格, 间距 3%
- 仓位: 每格 2%

### 🦐 模式3: 套利监控模式 (20%仓位)

**监控:**
- Polymarket + Binance + OKX 三市场

**条件:**
- 价差 > 2%
- 流动性充足

**执行:**
- 仓位: 5%

### 🦐 信息过滤 (所有模式)

**优先信号:**
- Polymarket odds 变化 > 10%
- Twitter 热度飙升
- 新闻突变

**过滤规则:**
- 已涨幅 > 20% 不追高
- TradingView 讨论热度 > 50% 观望

## 安装

```bash
# 1. 安装依赖
pip install ccxt numpy pandas requests

# 2. 配置 API
export BINANCE_API_KEY="your_key"
export BINANCE_SECRET="your_secret"

# 3. 初始化
python scripts/xiami.py --init
```

## 使用

### 获取信号
```bash
python scripts/xiami.py --signal
```

### 运行策略
```bash
# 趋势模式
python scripts/xiami.py --mode trend

# 网格模式
python scripts/xiami.py --mode grid

# 套利模式
python scripts/xiami.py --mode arbitrage

# 全部模式
python scripts/xiami.py --mode all
```

### 回测
```bash
python scripts/xiami.py --backtest --days 30
```

## 配置

编辑 `config.json`:

```json
{
  "mode": {
    "trend": {"enabled": true, "allocation": 0.5},
    "grid": {"enabled": true, "allocation": 0.3},
    "arbitrage": {"enabled": true, "allocation": 0.2}
  },
  "risk": {
    "max_position": 0.1,
    "stop_loss": 0.05,
    "take_profit": 0.15
  },
  "symbols": ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
}
```

## 信号系统

| 分数 | 信号 | 建议 |
|------|------|------|
| +7~+10 | 强力买入 | 积极建仓 |
| +3~+6 | 温和看涨 | 小仓位试多 |
| -2~+2 | 中性 | 观望 |
| -6~-3 | 温和看跌 | 小仓位试空 |
| -10~-7 | 强力卖出 | 清仓 |

## 策略优势

1. **自适应**: 根据市场状态自动切换模式
2. **多指标确认**: 减少假信号
3. **信息过滤**: 利用多源信息优势
4. **风险分散**: 三策略同时运行

## 注意事项

⚠️ 交易有风险，请谨慎使用
- 建议先进行模拟盘测试
- 设置合理的止损
- 不要投入超过承受能力的资金
- 定期检查策略表现

## 更新日志

### v1.0.0 (2026-03-10)
- 初始版本
- 融合9大交易策略
- 三模式自适应切换
- 多源信息过滤
