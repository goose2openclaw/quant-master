# QuantMaster - QMT + vnpy 融合量化平台 v5.0

## 概述
完全自主可控的加密货币量化交易平台，融合QMT快捷交易与vnpy量化框架。

## 完整模块矩阵 (47个)

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
| 33 | **copy_trading/** | **跟单交易系统** | ✅ v5.0 |
| 34 | **strategy_market/** | **策略市场** | ✅ v5.0 |
| 35 | **options/** | **期权交易引擎** | ✅ v5.0 |
| 36 | **defi_yield/** | **DeFi收益聚合** | ✅ v5.0 |
| 37 | **tax_report/** | **税务报告生成器** | ✅ v5.0 |
| 38 | **monte_carlo/** | **蒙特卡洛回测** | ✅ v5.0 |
| 39 | **mobile_app/** | **移动端App** | ✅ v5.0 |
| 40 | **sentiment_realtime/** | **实时情绪监控** | ✅ v5.0 |
| 41 | **dex_aggregator/** | **DEX聚合器** | ✅ v5.0 |
| 42 | **api_docs/** | **API文档生成器** | ✅ v5.0 |
| 43 | **portfolio_optimizer/** | **组合优化器** | ✅ v5.0 |
| 44 | **liquidity/** | **流动性检测** | ✅ v5.0 |

## v5.0 新增12个模块

### copy_trading/ - 跟单交易
```python
from copy_trading import CopyTradingSystem
ct = CopyTradingSystem()
provider_id = ct.register_provider('Trader1', 'momentum')
follower_id = ct.register_follower('User1', 1000, provider_id)
ct.execute_signal(provider_id, 'BTCUSDT', 'BUY', 0.1, 100000)
```

### strategy_market/ - 策略市场
```python
from strategy_market import StrategyMarketplace
market = StrategyMarketplace()
strategy_id = market.publish_strategy(author, 'RSI Bot', 'rsi', 29.99, desc, code)
market.purchase_strategy(user_id, strategy_id)
```

### options/ - 期权交易
```python
from options import OptionsTrading
opt = OptionsTrading(api_key, api_secret, proxy)
opt.buy_option('BTCUSDT', OptionType.CALL, 100000, expiry, qty)
opt.calculate_greeks(S, K, T, r, sigma)
```

### defi_yield/ - DeFi收益聚合
```python
from defi_yield import DefiYieldAggregator
agg = DefiYieldAggregator()
agg.add_pool('PancakeSwap', addr, 'BTC', 'USDT', apy=45.5, tvl=1000000)
agg.deposit(pool_id, amount)
```

### tax_report/ - 税务报告
```python
from tax_report import TaxReportGenerator
tax = TaxReportGenerator('US')
tax.add_transaction(date, 'SELL', 'BTC', 0.5, 50000)
report = tax.generate_tax_report()
tax.export_csv('tax_report.csv')
```

### monte_carlo/ - 蒙特卡洛回测
```python
from monte_carlo import MonteCarloSimulator
mc = MonteCarloSimulator(initial_capital=10000, num_simulations=1000)
stats = mc.run_simulation(initial_price=100000, mu=0.0002, sigma=0.03, days=30)
```

### mobile_app/ - 移动端App
```python
from mobile_app import MobileAppGenerator
gen = MobileAppGenerator('QuantMaster')
code = gen.generate_react_native()  # React Native
code = gen.generate_flutter()       # Flutter
pwa = gen.generate_pwa()           # PWA
```

### sentiment_realtime/ - 实时情绪
```python
from sentiment_realtime import RealtimeSentimentMonitor
mon = RealtimeSentimentMonitor()
mon.start()
score = mon.get_sentiment_score()
trends = mon.get_trending_topics()
```

### dex_aggregator/ - DEX聚合器
```python
from dex_aggregator import DEXAggregator, LiquidityChecker
agg = DEXAggregator('ethereum')
best = agg.get_best_quote('USDT', 'BTC', 10000)
agg.execute_swap('uniswap_v3', 'USDT', 'BTC', 10000, recipient)
```

### api_docs/ - API文档
```python
from api_docs import get_default_docs
docs = get_default_docs()
docs.save_openapi('openapi.json')
docs.save_markdown('api.md')
```

### portfolio_optimizer/ - 组合优化器
```python
from portfolio_optimizer import PortfolioOptimizer
opt = PortfolioOptimizer(returns, cov_matrix)
result = opt.max_sharpe()
frontier = opt.efficient_frontier(50)
```

### liquidity/ - 流动性检测
```python
from liquidity import LiquidityChecker
lc = LiquidityChecker()
lc.fetch_order_book('BTCUSDT')
slip = lc.estimate_slippage('BTCUSDT', 'BUY', 1)
score = lc.get_liquidity_score('BTCUSDT')
```

## 功能对照

| 类别 | 功能 | 状态 |
|------|------|------|
| 现货交易 | 快捷/篮子/市价/限价 | ✅ |
| 合约交易 | 永续/杠杆/止损止盈 | ✅ |
| 期权交易 | 币权/期权/希腊字母 | ✅ |
| DeFi收益 | 流动性挖矿/借贷/质押 | ✅ |
| 跟单交易 | 信号提供者/跟单者/盈亏分摊 | ✅ |
| 策略市场 | 上架/购买/评分/下载 | ✅ |
| 数据 | HTTP+WS+链上+新闻+情绪 | ✅ |
| 策略 | 18种策略+自定义 | ✅ |
| 回测 | 事件驱动+蒙特卡洛 | ✅ |
| 参数优化 | 网格+遗传+组合优化 | ✅ |
| 风控 | VAR/止损/风险敞口 | ✅ |
| 图表 | TradingView实时图表 | ✅ |
| 通知 | TG/邮件/Webhook/信号 | ✅ |
| 多账号 | 跨交易所管理 | ✅ |
| 套利 | 跨交易所价差监控 | ✅ |
| 调度 | Cron定时任务 | ✅ |
| Paper交易 | 模拟盘 | ✅ |
| 税务 | 自动报税报告 | ✅ |
| 移动端 | React Native/Flutter/PWA | ✅ |
| DEX聚合 | 多DEX比价/最佳路径 | ✅ |
| API文档 | OpenAPI/Markdown/Postman | ✅ |
| 流动性 | 订单簿深度/滑点/冲击 | ✅ |

## 代码规模
- **200+ Python文件**
- **30000+ 行代码**
- **47个模块**
- **完整专业量化平台**

## 许可证
MIT
