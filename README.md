# QuantMaster - QMT + vnpy 融合量化平台 v3.2

## 概述
完全自主可控的加密货币量化交易平台，融合QMT快捷交易与vnpy量化框架。

## 完整模块矩阵

| # | 模块 | 功能 | 状态 |
|---|------|------|------|
| 1 | core/ | 核心引擎 (事件/交易/网关/风控) | ✅ |
| 2 | data/ | 数据源 (HTTP+WebSocket) | ✅ |
| 3 | portfolio/ | 持仓同步+资金管理 | ✅ |
| 4 | order/ | 订单管理 (生命周期+撤单+重试) | ✅ |
| 5 | monitor/ | 监控面板 | ✅ |
| 6 | notification/ | 报警通知 | ✅ |
| 7 | log_system/ | 日志系统 | ✅ |
| 8 | permission/ | 权限管理 | ✅ |
| 9 | strategy_ide/ | 策略IDE | ✅ |
| 10 | performance/ | 绩效分析 | ✅ |
| 11 | strategies/ | 4种策略 (RSI/MACD/Bollinger/Momentum) | ✅ |
| 12 | backtest/ | 事件驱动回测 | ✅ |
| 13 | api_server/ | REST + WebSocket API | ✅ |
| 14 | factors/ | 10+技术因子 | ✅ |
| 15 | **db/** | **SQLite数据库持久化** | ✅ v3.2 |
| 16 | **exchanges/** | **多交易所 (Binance/OKX/Bybit)** | ✅ v3.2 |
| 17 | **optimizer/** | **网格+遗传算法优化器** | ✅ v3.2 |
| 18 | **ml_factors/** | **机器学习因子+预测模型** | ✅ v3.2 |
| 19 | alpha/ | Alpha策略 (vnpy) | ✅ |
| 20 | trader/ | 交易核心 (vnpy) | ✅ |

## v3.2 新增模块

### db/database.py
```python
from db import Database
db = Database('/tmp/qm.db')
db.save_order(order)
db.save_trade(trade)
db.get_positions()
db.save_equity(equity, position_value, cash)
db.get_klines('BTCUSDT', '1m', 1000)
```

### exchanges/
```python
from exchanges import BinanceExchange, OKXExchange, BybitExchange
from exchanges import ExchangeManager

binance = BinanceExchange(api_key, api_secret, proxy)
okx = OKXExchange(api_key, api_secret, passphrase, proxy)
bybit = BybitExchange(api_key, api_secret, proxy)

manager = ExchangeManager()
manager.add_exchange(binance, primary=True)
manager.add_exchange(okx)
manager.connect_all()
```

### optimizer/
```python
from optimizer import GridOptimizer, GeneticOptimizer

# 网格优化
optimizer = GridOptimizer(RSIStrategy, data)
optimizer.add_param('rsi_period', [10, 14, 20])
optimizer.add_param('buy_threshold', [25, 30, 35])
results = optimizer.run(n_workers=4)

# 遗传优化
ga = GeneticOptimizer(RSIStrategy, param_space)
ga.run()
```

### ml_factors/
```python
from ml_factors import MomentumFactor, MeanReversionFactor, VolatilityFactor
from ml_factors import PricePredictor, EnsemblePredictor

# 因子
momentum = MomentumFactor('mom', periods=[5, 10, 20])
momentum.update(price)
print(momentum.all_momentums())

# 价格预测
predictor = PricePredictor(lookback=20)
predictor.update(price, volume)
predictor.train()
direction = predictor.predict_direction()

# 集成预测
ensemble = EnsemblePredictor()
ensemble.add_predictor(momentum_predictor, weight=1.0)
ensemble.add_predictor(meanrev_predictor, weight=0.8)
signal = ensemble.predict()
```

## REST API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/status` | GET | 系统状态 |
| `/api/v1/positions` | GET | 持仓 |
| `/api/v1/orders` | GET/POST | 订单 |
| `/api/v1/backtest` | POST | 回测 |
| `/api/v1/optimizer` | POST | 参数优化 |
| `/api/v1/predict` | GET | 价格预测 |

## 快速开始

```python
from quant_master import QuantMaster

qm = QuantMaster()
qm.initialize(API_KEY, API_SECRET, PROXY)
qm.start()

# 交易
order = qm.send_order('BTCUSDT', 'BUY', 0.01)

# 数据库持久化
qm.db.save_order(order)

# 多交易所
qm.exchanges.add_exchange(okx_exchange)

# 优化策略
results = qm.optimizer.optimize(strategy, param_grid)

# ML预测
signal = qm.predictor.predict_direction()
```

## 自主升级
```bash
git remote add upstream https://github.com/vnpy/vnpy.git
git fetch upstream && git merge upstream/master
```

## 许可证
MIT
