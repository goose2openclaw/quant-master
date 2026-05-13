# go-liquidation - 清算地图预测技能

## 概述
清算价格预测，爆仓点预警，清算风险评估。

## 核心功能

### 1. 清算价格计算
- 多交易所清算价格
- 杠杆倍数影响
- 资金费率影响

### 2. 爆仓预警
- 距离清算价格百分比
- 危险等级 (HIGH/MEDIUM/LOW)
- 历史爆仓数据

### 3. 清算地图
- 集中爆仓区域
- 流动性池分析
- 空/多力量对比

## API
```python
from skills.go_liquidation import LiquidationMap

liquidation = LiquidationMap()
result = liquidation.analyze('BTC', entry_price=80000, position_type='long', leverage=5)
print(f"清算价格: ${result['liquidation_price']}")
print(f"危险等级: {result['danger_level']}")
```
