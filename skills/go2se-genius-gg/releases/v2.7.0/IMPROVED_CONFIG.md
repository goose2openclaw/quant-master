# 破军策略改进配置 v2.7.1

## 改进版配置

```python
# 破军策略 v2.7.1
POJUN_IMPROVED = {
    'name': '破军改进版',
    'leverage': 4,        # 5x → 4x
    'tp': 0.10,          # 10%止盈
    'sl': 0.02,          # 3% → 2%止损
    'win_rate': 0.75,
    'trend_confirm': True,  # 加入趋势确认
    'partial_tp': True,     # 分批止盈
}

# 分批止盈配置
PARTIAL_TP = {
    'first_tp': 0.05,   # 5%
    'first_ratio': 0.5,  # 50%仓位
    'second_tp': 0.10,   # 10%
    'second_ratio': 0.5, # 50%仓位
}

# 趋势确认配置
TREND_CONFIRM = {
    'd_threshold': 0.5,    # D>0.5
    'rsi_max': 60,          # RSI<60
    'volume_confirm': 1.2,  # 成交量>1.2x
}

# 保证金安全
MARGIN_SAFE = {
    'min_level': 3.0,    # 2.5 → 3.0
    'warning': 3.5,
    'good': 4.0,
}
```

---

## 期望收益

| 市场 | 收益范围 | 概率 |
|------|----------|------|
| 强势上涨 | +500-1000% | 20% |
| 震荡偏多 | +200-500% | 50% |
| 震荡偏空 | +50-200% | 20% |
| 极端下跌 | -50-0% | 10% |

---

*配置版本: v2.7.1*
*更新时间: 2026-05-06*
