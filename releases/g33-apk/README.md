# G33 Optimized Trading System APK

## 版本
v2.0.0

## 功能
- go-core v2.0 核心引擎
- 订单簿分析 (OrderbookSignal)
- 清算预警 (LiquidationWarning)
- 跨交易所套利 (ArbitrageScanner)

## 使用方法
```bash
# 启动G33
python3 g33_live.py

# 查看日志
tail -f logs/g33_live.log
```

## 配置
- 最低交易: $1 USDT
- 最大仓位: 15%
- 止损: 5%
- 止盈: 25%
- 扫描间隔: 20秒
