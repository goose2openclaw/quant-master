# QuantMaster - QMT + vnpy 融合系统

## 概述
QuantMaster是基于vnpy量化框架，融合QMT快捷交易功能的完全自主可控量化交易平台。

## 融合架构

```
QuantMaster/
├── core/              # 核心引擎
│   ├── event.py      # 事件引擎 (vnpy)
│   ├── engine.py     # 交易引擎 (QMT)
│   ├── gateway.py    # 网关管理
│   └── risk.py       # 风控 (QMT)
│
├── alpha/            # Alpha策略 (vnpy)
│   ├── dataset/      # 数据集
│   ├── model/        # 模型
│   └── strategy/     # 策略
│
├── chart/            # 图表 (vnpy)
├── event/            # 事件 (vnpy)
├── rpc/              # 远程调用 (vnpy)
├── trader/           # 交易核心 (vnpy)
│   ├── gateway/      # 交易所接口
│   ├── ui/          # 界面
│   ├── engine.py    # 引擎
│   └── ...
│
├── strategies/        # 策略库
├── backtest/         # 回测引擎
├── data/             # 数据管理
├── examples/         # 示例 (vnpy)
└── web_ui/          # Web界面 (QMT风格)
```

## 融合对照

| QMT功能 | vnpy实现 | QuantMaster |
|---------|----------|-------------|
| 快捷交易 | - | ✅ core/engine.py |
| 篮子交易 | - | ✅ core/engine.py |
| 风控规则 | - | ✅ core/risk.py |
| 事件驱动 | ✅ event/ | ✅ 完整融合 |
| Alpha研究 | ✅ alpha/ | ✅ 完整融合 |
| CTA策略 | ✅ trader/ | ✅ 完整融合 |
| 图表 | ✅ chart/ | ✅ 完整融合 |
| RPC调用 | ✅ rpc/ | ✅ 完整融合 |

## 自主升级
```bash
cd quant_master
git remote add upstream https://github.com/vnpy/vnpy.git
git fetch upstream
git merge upstream/master
git push origin master
```

## 使用

### 快捷交易
```python
from core import TradingEngine, EventEngine
engine = TradingEngine(event_engine)
order = engine.send_order('BTCUSDT', 'BUY', 0.01)
```

### 风控
```python
from core import RiskManager
risk = RiskManager()
allowed, reason = risk.check_order(order, account, positions)
```

### Alpha研究
```python
from alpha.strategy import AlphaStrategy
```

## 许可证
MIT
