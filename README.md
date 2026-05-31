# QuantMaster - QMT + vnpy 融合量化平台 v7.0

## 概述
完全自主可控的加密货币量化交易平台,融合QMT快捷交易与vnpy量化框架。

## 完整模块矩阵 (78个)

| # | 模块 | 功能 | 状态 |
|---|------|------|------|
| 1-45 | 交易/风控/数据层 | 核心模块 | ✅ |
| 46-60 | 高级功能 | SOR/期权/DeFi等 | ✅ |
| 61 | **oms/** | **完整订单管理系统** | ✅ v7.0 |
| 62 | **fix_protocol/** | **FIX Protocol机构协议** | ✅ v7.0 |
| 63 | **nlp_signals/** | **NLP交易信号** | ✅ v7.0 |
| 64 | **candlestick_ai/** | **K线形态识别AI** | ✅ v7.0 |
| 65 | **reconciliation/** | **对账清算系统** | ✅ v7.0 |
| 66 | **compliance/** | **合规监控(MiFID/Dodd-Frank)** | ✅ v7.0 |
| 67 | **esg/** | **ESG评分系统** | ✅ v7.0 |
| 68 | **low_latency/** | **低延迟框架** | ✅ v7.0 |
| 69 | **basket_trading/** | **Basket大单拆分** | ✅ v7.0 |
| 70 | **corporate_actions/** | **公司行动处理** | ✅ v7.0 |
| 71 | **investor_reports/** | **投资者报告** | ✅ v7.0 |
| 72 | **audit_trail/** | **审计追踪** | ✅ v7.0 |
| 73 | **fx_hedge/** | **外汇对冲** | ✅ v7.0 |
| 74 | **dma/** | **DMA直连** | ✅ v7.0 |
| 75 | **reinforcement_learning/** | **强化学习交易** | ✅ v7.0 |

## v7.0 新增15个模块

### oms/ - 完整订单管理系统
```python
from oms import OMS
oms = OMS()
order_id = oms.create_order('BTCUSDT', 'BUY', 0.1)
oms.route_order(order_id, ['binance', 'bybit'])
oms.split_order(order_id, splits)
```

### fix_protocol/ - FIX Protocol
```python
from fix_protocol import FIXProtocol
fix = FIXProtocol({'sender_id': 'CLIENT', 'target_id': 'Binance'})
fix.connect()
fix.send_order('BTCUSDT', 'BUY', 0.1)
```

### nlp_signals/ - NLP交易信号
```python
from nlp_signals import NLPSignalEngine
nlp = NLPSignalEngine()
signal = nlp.process_news(headline, body)
```

### candlestick_ai/ - K线形态识别
```python
from candlestick_ai import AIBasedRecognizer
recognizer = AIBasedRecognizer()
result = recognizer.predict_with_confidence(candles)
```

### reconciliation/ - 对账清算
```python
from reconciliation import ReconciliationEngine
recon = ReconciliationEngine()
recon.add_internal_trade(trade)
result = recon.run_reconciliation()
```

### compliance/ - 合规监控
```python
from compliance import ComplianceEngine
comp = ComplianceEngine()
comp.check_trade(trade)
comp.generate_compliance_report()
```

### esg/ - ESG评分
```python
from esg import ESGScorer
scorer = ESGScorer()
scores = scorer.calculate_scores('BTC')
```

### low_latency/ - 低延迟框架
```python
from low_latency import LowLatencyEngine
engine = LowLatencyEngine()
engine.create_queue('trades', capacity=10000)
```

### basket_trading/ - Basket交易
```python
from basket_trading import BasketExecutionManager
manager.execute_basket(orders, algorithm='vwap')
```

### corporate_actions/ - 公司行动
```python
from corporate_actions import CorporateActionProcessor
processor.process_actions(holdings)
```

### investor_reports/ - 投资者报告
```python
from investor_reports import ReportGenerator
report = generator.generate('monthly', data)
```

### audit_trail/ - 审计追踪
```python
from audit_trail import AuditLogger
logger.log('trade', 'BUY', 'BTCUSDT')
```

### fx_hedge/ - 外汇对冲
```python
from fx_hedge import FXHedgeManager
manager.execute_hedge('EUR', 10000)
```

### dma/ - DMA直连
```python
from dma import DMAGateway
gateway.add_connection('binance', '127.0.0.1', 9000)
```

### reinforcement_learning/ - 强化学习
```python
from reinforcement_learning import RLTradingEnvironment
env = RLTradingEnvironment()
state = env.reset()
state, reward, done = env.step(action, price)
```

## 功能对照

| 功能 | Bloomberg | 3Commas | QuantMaster |
|------|-----------|---------|-------------|
| OMS | ✅ | 部分 | ✅ |
| FIX Protocol | ✅ | ❌ | ✅ |
| NLP Signals | ✅ | ❌ | ✅ |
| Pattern AI | ✅ | 部分 | ✅ |
| Reconciliation | ✅ | ❌ | ✅ |
| Compliance | ✅ | ❌ | ✅ |
| ESG | ✅ | ❌ | ✅ |
| Low Latency | ✅ | ❌ | ✅ |
| Basket Trading | ✅ | ✅ | ✅ |
| Corporate Actions | ✅ | ❌ | ✅ |
| Investor Reports | ✅ | ❌ | ✅ |
| Audit Trail | ✅ | ❌ | ✅ |
| FX Hedge | ✅ | ❌ | ✅ |
| DMA | ✅ | ❌ | ✅ |
| RL Trading | 部分 | ❌ | ✅ |

## 代码规模
- **78个模块**
- **40,000+ 行代码**
- **接近Bloomberg级别专业平台**

## 许可证
MIT

## v7.5 加密货币专业模块 (新增15个) 🆕

| # | 模块 | 功能 |
|---|------|------|
| 79 | **funding_rate_tracking/** | 永续合约资金费率追踪、套利机会发现 |
| 80 | **open_interest/** | 未平仓合约追踪、资金流入/流出检测 |
| 81 | **liquidations/** | 强平事件追踪、多空挤压检测、强平墙 |
| 82 | **whale_tracker/** | 巨鲸地址监控、大额转账追踪、聪明钱 |
| 83 | **stablecoin_flow/** | USDT/USDC流向分析、储备金监测 |
| 84 | **crypto_fear_greed/** | 加密恐惧贪婪指数、综合情绪分析 |
| 85 | **onchain_metrics_pool/** | 链上指标池 (TVL/活跃地址/Gas/NVT/MVRV) |
| 86 | **liquidation_squeezes/** | 多空挤压检测、杠杆清洗预警 |
| 87 | **dex_cex_arb/** | DEX-CEX价格差异套利机会发现 |
| 88 | **mempool_analyzer/** | 待确认交易池分析、Gas优化 |
| 89 | **crypto_correlations/** | 跨资产相关性矩阵、配对交易信号 |
| 90 | **perpetual_funding_arb/** | 永续-现货资金费率套利策略 |
| 91 | **dust_detection/** | Dust UTXO检测与整合优化 |
| 92 | **exchange_reserves/** | 交易所储备金分析、净流量监测 |
| 93 | **crypto_gamma_squeeze/** | 期权Gamma挤压检测、价格影响分析 |

### 核心功能示例

```python
# 资金费率追踪
from funding_rate_tracking import FundingRateTracker
tracker = FundingRateTracker()
opps = tracker.find_arbitrage_opportunities(threshold=0.0005)

# 巨鲸追踪
from whale_tracker import WhaleTracker
tracker.record_transaction(whale_tx)
sentiment = tracker.get_whale_sentiment('BTC')

# 恐惧贪婪指数
from crypto_fear_greed import FearGreedIndex
fg = FearGreedIndex()
signal = fg.generate_trade_signal()

# 强平追踪
from liquidations import LiquidationTracker
squeeze = tracker.detect_squeeze('BTC', window_minutes=60)

# DEX-CEX套利
from dex_cex_arb import DEXCEXArbitrage
arb = DEXCEXArbitrage()
opps = arb.get_arb_opportunities(min_spread_pct=0.1)
```

### QuantMaster v7.5 最终规模
- **93个模块**
- **~45,000+行代码**
- 覆盖: 交易/风控/数据/机构级/Bloomberg级/加密货币专业
