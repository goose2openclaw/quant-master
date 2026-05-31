# QuantMaster - QMT + vnpy 融合量化平台 v6.0

## 概述
完全自主可控的加密货币量化交易平台,融合QMT快捷交易与vnpy量化框架。

## 完整模块矩阵 (63个)

| # | 模块 | 功能 | 状态 |
|---|------|------|------|
| 1 | core/ | 核心引擎 | ✅ |
| 2 | data/ | HTTP+WebSocket数据 | ✅ |
| 3 | portfolio/ | 持仓同步+资金管理 | ✅ |
| 4 | order/ | 订单管理 | ✅ |
| 5 | monitor/ | 基础监控 | ✅ |
| 6 | notification/ | 报警通知 | ✅ |
| 7 | log_system/ | 日志系统 | ✅ |
| 8 | permission/ | 权限管理 | ✅ |
| 9 | strategy_ide/ | 策略IDE | ✅ |
| 10 | performance/ | 绩效分析 | ✅ |
| 11 | strategies/ | 18种策略 | ✅ |
| 12 | backtest/ | 回测引擎 | ✅ |
| 13 | api_server/ | REST+WebSocket | ✅ |
| 14 | factors/ | 技术因子 | ✅ |
| 15 | db/ | SQLite持久化 | ✅ |
| 16 | exchanges/ | 多交易所 | ✅ |
| 17 | optimizer/ | 网格+遗传优化 | ✅ |
| 18 | ml_factors/ | ML因子+预测 | ✅ |
| 19 | futures/ | 合约交易 | ✅ |
| 20 | scheduler/ | Cron调度器 | ✅ |
| 21 | paper_trading/ | Paper模拟交易 | ✅ |
| 22 | risk/ | VAR+止损风控 | ✅ |
| 23 | onchain/ | 链上数据 | ✅ |
| 24 | news/ | 财经日历+新闻 | ✅ |
| 25 | sentiment/ | 社交情绪 | ✅ |
| 26 | arbitrage/ | 跨交易所套利 | ✅ |
| 27 | factor_research/ | 因子研究框架 | ✅ |
| 28 | pro_dashboard/ | 专业Dashboard | ✅ |
| 29 | slippage/ | 成交质量分析 | ✅ |
| 30 | live_signals/ | 实时信号推送 | ✅ |
| 31 | automation/ | 信号自动执行 | ✅ |
| 32 | chart/ | TradingView图表 | ✅ |
| 33 | copy_trading/ | 跟单交易 | ✅ |
| 34 | strategy_market/ | 策略市场 | ✅ |
| 35 | options/ | 期权交易 | ✅ |
| 36 | defi_yield/ | DeFi收益聚合 | ✅ |
| 37 | tax_report/ | 税务报告 | ✅ |
| 38 | monte_carlo/ | 蒙特卡洛回测 | ✅ |
| 39 | mobile_app/ | 移动端App | ✅ |
| 40 | sentiment_realtime/ | 实时情绪监控 | ✅ |
| 41 | dex_aggregator/ | DEX聚合器 | ✅ |
| 42 | api_docs/ | API文档生成 | ✅ |
| 43 | portfolio_optimizer/ | 组合优化器 | ✅ |
| 44 | liquidity/ | 流动性检测 | ✅ |
| 45 | **smart_routing/** | **SOR智能路由** | ✅ v6.0 |
| 46 | **twap_vwap/** | **TWAP/VWAP算法** | ✅ v6.0 |
| 47 | **pretrade_risk/** | **下单前风控** | ✅ v6.0 |
| 48 | **margin_management/** | **保证金管理** | ✅ v6.0 |
| 49 | **performance_attribution/** | **收益归因** | ✅ v6.0 |
| 50 | **strategy_git/** | **策略Git版本控制** | ✅ v6.0 |
| 51 | **ab_testing/** | **A/B测试框架** | ✅ v6.0 |
| 52 | **factor_exposure/** | **因子敞口分析** | ✅ v6.0 |
| 53 | **strategy_correlation/** | **策略相关性** | ✅ v6.0 |
| 54 | **scenario_stress/** | **情景压测** | ✅ v6.0 |
| 55 | **multi_leg_orders/** | **组合单** | ✅ v6.0 |
| 56 | **docker_k8s/** | **容器化部署** | ✅ v6.0 |
| 57 | **api_rate_limit/** | **API限流** | ✅ v6.0 |
| 58 | **webhook_events/** | **Webhook事件** | ✅ v6.0 |
| 59 | **backup_restore/** | **备份恢复** | ✅ v6.0 |
| 60 | **options_greeks_stream/** | **期权希腊值实时** | ✅ v6.0 |

## v6.0 新增16个模块

### smart_routing/ - SOR智能订单路由
```python
from smart_routing import SmartOrderRouter
router = SmartOrderRouter()
best = router.get_best_route('BTCUSDT', 'BUY', 1)
fills = router.get_split_route('BTCUSDT', 'BUY', 10)
```

### twap_vwap/ - TWAP/VWAP算法
```python
from twap_vwap import TWAPExecutor, VWAPExecutor
twap = TWAPExecutor(order_manager)
twap.create_order('BTCUSDT', 'BUY', 10, duration_min=30)
```

### pretrade_risk/ - 下单前风控
```python
from pretrade_risk import PreTradeRiskChecker
checker = PreTradeRiskChecker()
result = checker.check_order(order, account, positions, current_price)
```

### margin_management/ - 保证金管理
```python
from margin_management import MarginManager
mm = MarginManager()
mm.open_position('BTCUSDT', qty=1, leverage=10)
```

### performance_attribution/ - 收益归因
```python
from performance_attribution import PerformanceAttribution
attr = PerformanceAttribution()
attr.add_return(date, port_return, bench_return)
attr.get_brinson_attribution(positions, benchmarks)
```

### strategy_git/ - 策略版本控制
```python
from strategy_git import StrategyRepository
repo = StrategyRepository()
repo.commit('RSIStrategy', code, 'v1.0', 'author')
repo.get_history('RSIStrategy')
```

### ab_testing/ - A/B测试框架
```python
from ab_testing import ABTestingFramework
fw = ABTestingFramework()
test_id = fw.create_test('RSI vs MACD', config_a, config_b)
fw.analyze(test_id, 'sharpe_ratio')
```

### factor_exposure/ - 因子敞口
```python
from factor_exposure import FactorExposureAnalyzer
analyzer = FactorExposureAnalyzer()
exposure = analyzer.calculate_portfolio_exposure(holdings, factor_values)
```

### strategy_correlation/ - 策略相关性
```python
from strategy_correlation import StrategyCorrelationAnalyzer
corr = StrategyCorrelationAnalyzer()
corr.add_strategy_returns('RSI', returns1)
corr.get_highly_correlated('RSI', threshold=0.7)
```

### scenario_stress/ - 情景压测
```python
from scenario_stress import ScenarioStressTester
tester = ScenarioStressTester()
tester.run_stress_test(portfolio, positions)
```

### multi_leg_orders/ - 组合单
```python
from multi_leg_orders import SpreadOrderManager
spread = SpreadOrderManager(om)
spread.create_straddle('BTCUSDT', qty=1)
spread.create_butterfly('BTCUSDT', qty=1)
```

### docker_k8s/ - 容器化部署
```python
from docker_k8s import DockerGenerator, KubernetesGenerator
dg = DockerGenerator()
dg.generate_dockerfile()
```

### api_rate_limit/ - API限流
```python
from api_rate_limit import RateLimiter
limiter = RateLimiter()
limiter.add_rule('/api/order', 100, 60)
limiter.check_rate_limit('/api/order', client_id)
```

### webhook_events/ - Webhook事件
```python
from webhook_events import WebhookDispatcher
dispatcher = WebhookDispatcher()
dispatcher.add_endpoint('myhook', 'https://...', ['trade', 'signal'])
dispatcher.emit('trade', trade_data)
```

### backup_restore/ - 备份恢复
```python
from backup_restore import BackupManager
bm = BackupManager()
bm.create_backup('full')
bm.restore_backup('backup_full_20260101.tar.gz')
```

### options_greeks_stream/ - 期权希腊值
```python
from options_greeks_stream import GreeksCalculator, GreeksStreamMonitor
calc = GreeksCalculator()
greeks = calc.calculate_greeks(S, K, T, r, sigma)
```

## 功能对照

| 功能 | 3Commas | Pionex | Deribit | QuantMaster |
|------|----------|---------|----------|-------------|
| SOR | ✅ | ✅ | ✅ | ✅ |
| TWAP/VWAP | ✅ | ✅ | ✅ | ✅ |
| Pre-trade Risk | ✅ | ✅ | ✅ | ✅ |
| Margin Mgmt | ✅ | ✅ | ✅ | ✅ |
| Strategy Git | ❌ | ❌ | ❌ | ✅ |
| A/B Testing | ❌ | ❌ | ❌ | ✅ |
| Performance Attribution | ❌ | ❌ | ❌ | ✅ |
| Factor Exposure | ❌ | ❌ | ❌ | ✅ |
| Strategy Correlation | ❌ | ❌ | ❌ | ✅ |
| Scenario Stress | ❌ | ❌ | ❌ | ✅ |
| Multi-leg Orders | ❌ | ✅ | ✅ | ✅ |
| Docker/K8s | ❌ | ❌ | ❌ | ✅ |
| Rate Limiting | ❌ | ❌ | ❌ | ✅ |
| Webhook Events | ❌ | ❌ | ❌ | ✅ |
| Backup/Restore | ❌ | ❌ | ❌ | ✅ |
| Options Greeks | ❌ | ✅ | ✅ | ✅ |

## 代码规模
- **60+ 模块**
- **35,000+ 行代码**
- **完整专业量化平台**

## 许可证
MIT
