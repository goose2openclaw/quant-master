# G40 超级自主量化交易系统

## 版本
**v4.0** - 终极自主交易系统

## 核心升级

### 1. G40Optimizer - 超强自主优化器
- 7大策略融合: go-core, go-pool, go-rotate, go-long-short, go-detect, go-etf, top10
- 市场状态检测: trending, ranging, volatile
- 自适应权重调整
- 自我学习进化

### 2. AssetManagerPro - 智能资产管理Pro
- 智能杠杆调度
- 自动小额转换
- 风险平价配置
- USDT优化分配

### 3. AutoRebalancerPro - 自主调仓大师Pro
- 集中度实时监控
- 动态再平衡
- 紧急调仓保护
- 趋势止盈

## 核心策略

| 策略 | 功能 | 权重范围 |
|------|------|----------|
| go-core | 趋势跟踪核心信号 | 15-25% |
| go-pool | 资金流向撞球 | 10-20% |
| go-rotate | 板块轮动检测 | 15-20% |
| go-long-short | 多空信号 | 10-20% |
| go-detect | 异常波动检测 | 10-15% |
| go-etf | ETF流动性信号 | 10-15% |
| top10 | 顶级交易员信号 | 5-10% |

## 配置参数

```python
MIN_USDT_RESERVE = 3.0       # 最低储备
MIN_TRADE_VALUE = 0.3        # 最小交易
SCAN_INTERVAL = 25           # 扫描间隔
STOP_LOSS = 0.05             # 止损5%
TAKE_PROFIT = 0.25           # 止盈25%
MAX_POSITION = 0.25          # 单币最大25%
MARGIN_LEVERAGE = 3          # 杠杆3倍
```

## 启动

```bash
python3 skills/g40/g40.py
```

## 日志
- 状态文件: `/home/goose/.openclaw/workspace/.g40_state.json`
- 日志文件: `/home/goose/.openclaw/workspace/logs/g40.log`

## GitHub
- Branch: g12branch
- Commit: G40 v4.0 超级自主量化系统
