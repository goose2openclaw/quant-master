# G12/G16 Trading System

## 版本
- **v2.0 (2026-05-09)**: G16正式版
- **v1.0 (2026-05-09)**: 初始版本

## G16 v2.0 最优配置
```python
CONFIG = {
    'rsi_buy': 35,
    'rsi_sell': 65,
    'bb_buy': 30,
    'bb_sell': 70,
    'tp': 0.12,
    'sl': 0.04,
    'position': 0.35,
    'leverage': 5,
    'bb_threshold': 0.35
}
```

## 回测结果
- 收益: +52.01%
- 胜率: 41.7%
- 交易: 12次

## 核心功能
- 多因子信号 (RSI + BB + 成交量)
- 市场状态检测
- 自适应配置

## 脚本
- hermes_g16.py - G16 v2.0正式版
