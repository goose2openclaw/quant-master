# G12 - 加密货币量化投资系统 v2.0

## 概述
G12是基于12个顶级量化交易系统的全面蒸馏，集成了Freqtrade、Jesse、QuantDinger等最佳实践，目标月收益100%+。

## 核心模块

### 1. 交易核心
- `hermes_g12_unified.py` - 统一核心 v2.0
- `hermes_g12_plus_trader.py` - 实盘交易 v4.0
- `hermes_g12_god_mode.py` - 上帝视角 v2.0

### 2. 资金管理
- `g12_smart_fund_manager.py` - 智能资金分配 v2.0
- `g12_fund_manager.py` - 账户间转账
- 自动监控现货/合约/逐仓账户

### 3. 数据追踪
- `g12_stats_tracker.py` - 实时统计
- `g12_api_data.py` - API数据获取

### 4. 仪表板
- `g12_webui/index.html` - 实时Dashboard
- 端口8083

## 核心参数
- RSI: 43/53
- 布林: 25/75  
- 止盈: 8%
- 止损: 3.5%
- 仓位: 20%
- 杠杆: 5x

## Cron任务
```
*/5  hermes_g12_god_mode.py      # 上帝视角
*/5  hermes_g12_unified.py       # 统一核心
*/5  hermes_g12_plus_trader.py    # 实盘交易
*/5  g12_smart_fund_manager.py    # 智能资金
*/5  g12_stats_tracker.py         # 数据追踪
*/15 hermes_g12_plus_monitor.py   # 机会监控
*/30 hermes_g12_autoloop_v3.py   # 自主迭代
```

## API配置
- Binance API Key已配置
- Proxy: 172.29.144.1:7897
- 支持现货/合约/逐仓账户

## 版本历史
- v2.0: 添加智能资金管理系统，支持全账户监控
