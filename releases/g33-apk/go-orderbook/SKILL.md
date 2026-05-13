# go-orderbook - 实时订单簿分析技能

## 概述
实时订单簿分析，捕捉机构订单，预测价格支撑阻力。

## 核心功能

### 1. 订单簿深度分析
- 买卖盘密度
- 大单检测 (whale detection)
- 支撑/阻力墙识别
- 价差分析

### 2. 机构订单捕捉
- 订单簿不平衡预警
- 冰山订单识别
- 大户动向追踪

## API
```python
from skills.go_orderbook import OrderbookAnalyzer

analyzer = OrderbookAnalyzer()
result = analyzer.analyze('BTC')
print(f"买单密度: {result['bid_density']}")
print(f"卖单密度: {result['ask_density']}")
print(f"不平衡度: {result['imbalance']}")
```
