# go-cross-exchange - 跨交易所套利技能

## 概述
多交易所价格对比，捕捉套利机会，跨交易所交易。

## 核心功能

### 1. 价格对比
- Binance, OKX, Bybit, Gate
- 交易所间价差计算
- 价格差异百分比

### 2. 套利机会
- 三角套利
- 跨交易所套利
- 资金费率套利

### 3. 交易执行
- 多交易所下单
- 交易延迟补偿
- 成功率评估

## API
```python
from skills.go_cross_exchange import CrossExchange

cross = CrossExchange()
prices = cross.get_all_prices('BTC')
print(f"Binance: ${prices['binance']}")
print(f"OKX: ${prices['okx']}")
print(f"价差: {prices['spread']:.2f}%")
```
