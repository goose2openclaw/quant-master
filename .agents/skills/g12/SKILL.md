# G12 Trading System v2.0

## 最新最优参数 (2026-05-09)
- RSI: 28/70 | BB: 20/80
- TP: 15% | SL: 5%
- 仓位: 35% | 杠杆: 5x
- 回测收益: +184.68%
- 胜率: 71.4%

## 核心脚本
- hermes_g12_unified.py - 统一核心
- hermes_g12_plus_trader.py - 实盘交易(含验证函数)
- hermes_g12_god_mode.py - 上帝视角
- hermes_g12_autoloop_v4.py - 自主迭代

## 验证函数
validate_trade() - 验证交易可行性,自动跳过余额不足订单

## 使用
```bash
python3 hermes_g12_plus_trader.py
```

