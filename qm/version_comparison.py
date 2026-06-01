"""
版本对比测试
对比: 0601v3 vs 0610
"""
import sys
import time
sys.path.insert(0, '.')

print("="*70)
print("📊 版本对比测试: 0601v3 vs 0610")
print("="*70)

# 测试0601v3
print("\n[1] 测试 0601v3...")
from qm.quant_master_0601v3 import QuantMaster0601v3

start = time.time()
qm1 = QuantMaster0601v3(10000)
result1 = qm1.run_scan()
time1 = time.time() - start

print(f"\n0601v3 结果:")
print(f"  信号: {len(qm1.signals)}个")
print(f"  耗时: {time1:.2f}s")
print(f"  买入: {len([s for s in qm1.signals if s['action'] in ['BUY','LONG']])}")
print(f"  卖出: {len([s for s in qm1.signals if s['action'] in ['SELL','SHORT']])}")

# 测试0610
print("\n[2] 测试 0610...")
from qm.quant_master_0610 import QuantMaster0610
from importlib import reload

start = time.time()
qm2 = QuantMaster0610(10000)
signals2 = qm2.scan_all()
time2 = time.time() - start

print(f"\n0610 结果:")
print(f"  信号: {len(signals2)}个")
print(f"  耗时: {time2:.2f}s")
print(f"  买入: {len([s for s in signals2 if s['action'] in ['BUY','LONG']])}")
print(f"  卖出: {len([s for s in signals2 if s['action'] in ['SELL','SHORT']])}")

# 进化组件状态
print(f"\n0610 进化组件:")
print(f"  MultiMemory: {len(qm2.memory.semantic_memory)}条语义")
print(f"  AntiStuck: 重复{qm2.anti_stuck.repeat_count}次")
print(f"  LoopBreaker: {'OPEN' if qm2.loop_breaker.circuit_open else 'CLOSED'}")
print(f"  TokenBudget: {qm2.token_budget.used_tokens} tokens")
print(f"  CapyCortex: {len(qm2.cortex.lessons_learned)}条教训, 最佳={qm2.cortex.get_best_strategy()}")

# 对比总结
print("\n" + "="*70)
print("📋 版本对比总结")
print("="*70)
print(f"""
| 指标       | 0601v3  | 0610    | 变化    |
|------------|----------|----------|---------|
| 信号数     | {len(qm1.signals):8} | {len(signals2):8} | {len(signals2)-len(qm1.signals):+4}    |
| 买入       | {len([s for s in qm1.signals if s['action'] in ['BUY','LONG']]):8} | {len([s for s in signals2 if s['action'] in ['BUY','LONG']]):8} | {len([s for s in signals2 if s['action'] in ['BUY','LONG']])-len([s for s in qm1.signals if s['action'] in ['BUY','LONG']]):+4}    |
| 卖出       | {len([s for s in qm1.signals if s['action'] in ['SELL','SHORT']]):8} | {len([s for s in signals2 if s['action'] in ['SELL','SHORT']]):8} | {len([s for s in signals2 if s['action'] in ['SELL','SHORT']])-len([s for s in qm1.signals if s['action'] in ['SELL','SHORT']]):+4}    |
| 耗时(s)    | {time1:8.2f} | {time2:8.2f} | {time2-time1:+.2f}   |

进化组件增加:
✓ v2 MultiMemory - 多记忆架构
✓ v3 AntiStuck - 防卡顿机制
✓ v4 LoopBreaker - 防死循环
✓ v5 TokenBudget - Token优化
✓ v6 ParallelCoordinator - 并行协调
✓ v7 CapyCortex - 自主学习
""")
print("="*70)
