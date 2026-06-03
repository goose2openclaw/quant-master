"""Q@C v10.1.0 模块评测脚本"""
import sys
import time
import json
import math
sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

print("=" * 70)
print("🔬 Q@C v10.1.0 模块评测")
print("=" * 70)

# ============================================================
# 模块1: BinanceAPI 测试
# ============================================================
print("\n[模块1] BinanceAPI - 数据获取和账户检测")
print("-" * 50)

from qm.quant_master_qcv10 import BinanceAPI, Indicators

binance = BinanceAPI()
print(f"  模式检测: {binance.mode}")

# 测试获取K线
klines = binance.get_klines('BTCUSDT', '1h', 100)
print(f"  K线获取: {len(klines)} 条")

if klines:
    print(f"  最新价格: ${klines[-1]['close']:.2f}")
    print(f"  最高: ${max(k['high'] for k in klines[-24:]):.2f}")
    print(f"  最低: ${min(k['low'] for k in klines[-24:]):.2f}")

# 测试账户
account = binance.get_account()
if account:
    print(f"  账户信息: ✅ 获取成功")
else:
    print(f"  账户信息: ❌ 获取失败")

# ============================================================
# 模块2: 技术指标测试
# ============================================================
print("\n[模块2] 技术指标 (Indicators)")
print("-" * 50)

indicators = Indicators()
prices = [k['close'] for k in klines] if klines else []

if len(prices) >= 50:
    rsi = indicators.RSI(prices)
    macd = indicators.MACD(prices)
    kdj_data = indicators.KDJ([k['high'] for k in klines], [k['low'] for k in klines], prices)
    bb = indicators.BollingerBands(prices)
    
    print(f"  RSI(14): {rsi:.2f}")
    print(f"  MACD: {macd['macd']:.4f}, Signal: {macd['signal']:.4f}")
    print(f"  KDJ: K={kdj_data['k']:.2f} D={kdj_data['d']:.2f} J={kdj_data['j']:.2f}")
    print(f"  BB Upper: ${bb['upper']:.2f}, Middle: ${bb['middle']:.2f}, Lower: ${bb['lower']:.2f}")
    print(f"  BB Position: {(prices[-1] - bb['lower']) / (bb['upper'] - bb['lower']) * 100:.2f}%")
else:
    print(f"  数据不足: {len(prices)} 条")

# ============================================================
# 模块3: V8 SignalEngine 测试
# ============================================================
print("\n[模块3] V8 SignalEngine")
print("-" * 50)

from qm.quant_master_qcv10 import SignalEngine

signal_engine = SignalEngine()
v8_result = signal_engine.analyze('BTCUSDT', klines)

if v8_result:
    print(f"  V8评分: {v8_result.get('score', 0):.0f}")
    print(f"  V8动作: {v8_result.get('action', 'HOLD')}")
    print(f"  信号数量: {len(v8_result.get('signals', []))}")
    for sig in v8_result.get('signals', [])[:3]:
        print(f"    - {sig['type']}: {sig['action']} (conf={sig['conf']:.0f})")

# ============================================================
# 模块4: G12 策略矩阵测试
# ============================================================
print("\n[模块4] G12 策略矩阵")
print("-" * 50)

from qm.quant_master_qcv10 import G12StrategyMatrix

g12 = G12StrategyMatrix()
g12_signals = g12.evaluate(v8_result)
g12_action, g12_conf = g12.weighted_vote(g12_signals)
g12_score = 50 + (g12_conf - 50) / 50 * 30

print(f"  G12策略数: {len(g12.STRATEGIES)}")
print(f"  G12信号: {list(g12_signals.keys())}")
print(f"  G12动作: {g12_action}, 置信: {g12_conf:.0f}")
print(f"  G12评分: {g12_score:.0f}")

# ============================================================
# 模块5: Mirofish 仿真引擎测试
# ============================================================
print("\n[模块5] Mirofish 仿真引擎")
print("-" * 50)

from qm.quant_master_qcv10 import MirofishSimulator

mirofish = MirofishSimulator()
mirofish_result = mirofish.analyze(v8_result, klines)

print(f"  Mirofish版本: {mirofish.version}")
print(f"  Mirofish评分: {mirofish_result.get('score', 0):.0f}")
print(f"  Mirofish动作: {mirofish_result.get('action', 'HOLD')}")
print(f"  策略信号: {mirofish_result.get('strategy_signals', {})}")
print(f"  因子值: {mirofish_result.get('factors', {})}")

# ============================================================
# 模块6: 主动探测引擎测试
# ============================================================
print("\n[模块6] 主动探测引擎")
print("-" * 50)

from qm.quant_master_qcv10 import ProbingEngine

probing = ProbingEngine(binance)
opportunities = probing.probe_market()

print(f"  探测币种数: {len(probing.probed_symbols)}")
print(f"  发现机会: {len(opportunities)}")
for opp in opportunities[:3]:
    print(f"    - {opp['symbol']}: {opp['type']} {opp['action']} (rsi={opp['rsi']:.1f})")

# ============================================================
# 模块7: 自主决策引擎测试
# ============================================================
print("\n[模块7] 自主决策引擎")
print("-" * 50)

from qm.quant_master_qcv10 import AutonomousDecisionEngine

autonomous = AutonomousDecisionEngine()

# 测试不同评分下的决策
test_scores = [
    ('BTCUSDT', 75, 60, 65, 70),
    ('ETHUSDT', 25, 40, 35, 30),
    ('XRPUSDT', 55, 50, 55, 50),
]

for symbol, v8, g12, miro, combined in test_scores:
    decision = autonomous.decide(symbol, combined, v8, g12, miro)
    print(f"  {symbol}: 综合={combined:.0f} → {decision['action']} (auto={decision['auto_execute']})")

print(f"  累计自动执行: {autonomous.approved_trades} 次")

# ============================================================
# 模块8: 仿真交易执行器测试
# ============================================================
print("\n[模块8] 仿真交易执行器")
print("-" * 50)

from qm.quant_master_qcv10 import SimulatedExecutor

executor = SimulatedExecutor(10000)
print(f"  初始资金: ${executor.capital:.2f}")

# 测试买入
if klines:
    price = klines[-1]['close']
    result = executor.buy('BTCUSDT', 0.01, price)
    print(f"  买入BTC: {result}")
    
    # 测试更新
    executor.update({'BTCUSDT': price * 1.02})
    print(f"  更新后持仓: {executor.positions.get('BTCUSDT', {})}")
    
    # 测试止损检查
    should_close, reason = executor.check_stops('BTCUSDT', price * 0.98)
    print(f"  止损检查(跌2%): should_close={should_close}, reason={reason}")
    
    # 测试止盈检查
    should_close, reason = executor.check_stops('BTCUSDT', price * 1.09)
    print(f"  止盈检查(涨9%): should_close={should_close}, reason={reason}")

# ============================================================
# 模块9: Watchdog 测试
# ============================================================
print("\n[模块9] Watchdog 监控")
print("-" * 50)

from qm.quant_master_qcv10 import Watchdog

watchdog = Watchdog("TEST")
watchdog.heartbeat({'cycles': 1, 'trades': 5, 'profit': 100})

import os
if os.path.exists('/home/goose/.openclaw/workspace/test_status.json'):
    with open('/home/goose/.openclaw/workspace/test_status.json') as f:
        status = json.load(f)
    print(f"  状态文件: ✅")
    print(f"  内容: {status}")
else:
    print(f"  状态文件: ❌ 未找到")

# ============================================================
# 模块间数据流通测试
# ============================================================
print("\n[模块10] 模块间数据流通")
print("-" * 50)

# 完整流程测试
print("  流程: BinanceAPI → Indicators → SignalEngine → G12/Mirofish → Autonomous → Executor")

# 1. 获取数据
klines = binance.get_klines('ETHUSDT', '1h', 100)
print(f"  [1] BinanceAPI → {len(klines)} 条K线")

# 2. 技术分析
prices = [k['close'] for k in klines]
rsi = indicators.RSI(prices)
print(f"  [2] Indicators → RSI={rsi:.2f}")

# 3. V8信号
v8 = signal_engine.analyze('ETHUSDT', klines)
print(f"  [3] SignalEngine → score={v8.get('score', 0):.0f}, action={v8.get('action', 'HOLD')}")

# 4. G12信号
g12_sig = g12.evaluate(v8)
g12_act, g12_conf = g12.weighted_vote(g12_sig)
print(f"  [4] G12 → action={g12_act}, conf={g12_conf:.0f}")

# 5. Mirofish
miro = mirofish.analyze(v8, klines)
print(f"  [5] Mirofish → score={miro.get('score', 0):.0f}")

# 6. 三重权重
weights = {'v8': 0.50, 'g12': 0.30, 'mirofish': 0.20}
v8_score = v8.get('score', 50)
g12_score = 50 + (g12_conf - 50) / 50 * 30
miro_score = miro.get('score', 50)
combined = v8_score * weights['v8'] + g12_score * weights['g12'] + miro_score * weights['mirofish']
print(f"  [6] 三重权重 → {v8_score}×0.5 + {g12_score:.0f}×0.3 + {miro_score:.0f}×0.2 = {combined:.0f}")

# 7. 自主决策
decision = autonomous.decide('ETHUSDT', combined, v8_score, g12_score, miro_score)
print(f"  [7] Autonomous → {decision['action']} (auto={decision['auto_execute']})")

# 8. 执行
if decision['action'] == 'BUY' and decision['auto_execute']:
    result = executor.buy('ETHUSDT', 1.0, klines[-1]['close'])
    print(f"  [8] Executor → {result.get('status', 'ERROR')}")

print("\n" + "=" * 70)
print("✅ 模块评测完成")
print("=" * 70)
