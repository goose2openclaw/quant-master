# HEARTBEAT.md

## ⚠️ 核心指令
**GO2SE Genius + Hermes v5.5 必须常开 - 收益最大化最高优先级**

### 🎯 最高目标: 收益最大化
> **高抛低吸短线操作 + 趋势匹配中长期交易**

### 📈 策略核心: 高抛低吸
- **低吸**: 布林下轨(位置<20%)或大跌(chg<-3%) → 买入
- **高抛**: 布林上轨(位置>80%)或大涨(chg>3%) → 卖出
- **追涨**: 突破日高 + 趋势确认 → 顺势买入
- **止损**: 大跌(chg<-5%) → 减仓50%

### 📊 趋势匹配
- 短线: RSI/布林带/价格位置
- 中线: 1h趋势跟随
- 长线: 日线趋势确认

### 🛡️ 风险控制
- 单笔仓位: SPOT 20%资金
- 止损线: -5%强制减仓
- 布林位置: 0-100量化信号

## 常驻任务 (持续在线)

| 任务 | 频率 | 脚本 | 功能 |
|------|------|------|------|
| 1 | */3min | hermes_v55.sh | 高抛低吸短线 |
| 2 | */5min | gg_spike_system.sh | 波动率监控 |
| 3 | */5min | gg_spike_catcher.sh | 插针捕捉 |
| 4 | */10min | gg_autonomous_trader.sh | 自主交易 |
| 5 | */10min | gg_auto_fixer.sh | 自主修复 |
| 6 | */15min | gg_polymarket_scraper.sh | 预测市场 |
| 7 | */30min | gg_autonomous_iterate.sh | 策略迭代 |
| 8 | */30min | gg_asset_scanner.sh | 资产监控 |
| 9 | */5min | gg_kline.sh | K线实时展示 |
| 9 | 21:00 | gg_cron_3layer.sh | 日终结算 |
| 10 | @reboot | hermes_daemon.sh | 守护进程 |

## GO2SE Genius v5.5
- 策略: 高抛低吸 + 趋势跟随
- 频率: 高频短线 + 中长期匹配
- 状态: 持续在线

## 学习数据
```json
{"DOGE": "38%", "SOL": "38%", "ADA": "38%", "BTC": "20%", "ETH": "20%", "LINK": "20%", "XRP": "33%"}
```

---
**最后更新**: 2026-05-07 17:47
**版本**: hermes_v55 高抛低吸版
