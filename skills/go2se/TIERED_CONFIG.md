# GO2SE 分层交易配置

## 主流币策略 (Tier 1)
- 策略: v4 (高胜率)
- 仓位: 15%
- 止损: 3%
- 止盈: 8%
- 交易对: BTC, ETH, BNB, SOL, XRP, ADA, DOGE, AVAX, DOT, MATIC

## 山寨币策略 (Tier 2 - 打地鼠)
- 策略: 快速异动
- 仓位: 8%
- 止损: 5%
- 止盈: 12%
- 手续费预留: 0.2%

## 运行命令
```bash
# 主流币策略
python skills/xiami/scripts/mainstream_strategy.py

# 打地鼠策略  
python skills/xiami/scripts/mole_strategy.py
```
