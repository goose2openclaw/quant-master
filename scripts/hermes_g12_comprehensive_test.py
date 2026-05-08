#!/usr/bin/env python3
"""
Hermes G12 - 全面测试套件 (修复版)
"""
import requests, time, json, numpy as np, random
from datetime import datetime

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']
LOG_FILE = '/tmp/g12_test_report.txt'

def log(msg):
    print(msg)
    with open(LOG_FILE, 'a') as f:
        f.write(msg + '\n')

def get_rsi(prices, period=7):
    if len(prices) < period+1: return 50
    deltas = np.diff(prices)
    gain = np.where(deltas>0, deltas, 0)
    loss = np.where(deltas<0, -deltas, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    return 100-(100/(1+avg_gain/avg_loss)) if avg_loss!=0 else 100

def bollinger_pos(price, highs, lows, period=20):
    if len(highs) < period: return 50
    bb_high = np.mean(highs[-period:]) + 2*np.std(highs[-period:])
    bb_low = np.mean(lows[-period:]) - 2*np.std(lows[-period:])
    return (price - bb_low) / (bb_high - bb_low) * 100 if bb_high > bb_low else 50

def get_klines(sym, limit=720):
    end = int(time.time()*1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&startTime={start}&endTime={end}&limit={limit}'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=30)
        return [{'close':float(k[4]),'high':float(k[2]),'low':float(k[3])} for k in r.json()]
    except: return []

def simulate(initial, data, cfg):
    """修复版模拟器"""
    valid = [c for c in COINS if c in data and len(data[c]) > 100]
    if not valid: return None
    min_d = min(len(data[c]) for c in valid)
    
    cap = initial
    pos = {c: 0.0 for c in valid}      # 做多数量
    entry = {c: 0.0 for c in valid}     # 做多入场价
    short_qty = {c: 0.0 for c in valid} # 做空数量
    short_entry = {c: 0.0 for c in valid}# 做空入场价
    trades = []
    
    lev = cfg.get('leverage', 3)
    pr = cfg.get('position', 0.30)
    
    for d in range(min_d):
        day_price = {c: data[c][d]['close'] for c in valid}
        
        for c in valid:
            cs = [data[c][i]['close'] for i in range(max(0,d-30),d+1)]
            hs = [data[c][i]['high'] for i in range(max(0,d-19),d+1)]
            ls = [data[c][i]['low'] for i in range(max(0,d-19),d+1)]
            
            if len(cs) < 30: continue
            
            rsi = get_rsi(cs[-15:], 7)
            bb = bollinger_pos(day_price[c], hs, ls, 20)
            price = day_price[c]
            
            # 做多开仓
            if rsi < cfg['rsi_buy'] and bb < cfg['bb_buy'] and cap > 10 and pos[c] == 0 and short_qty[c] == 0:
                invest = cap * pr  # 不用杠杆计算,只用杠杆决定实际数量
                qty = invest * lev / price
                fee = invest * 0.001
                cap -= (invest + fee)
                pos[c] = qty
                entry[c] = price
                trades.append({'t':'LONG_OPEN','c':c,'p':price,'qty':qty})
            
            # 平多
            if pos[c] > 0:
                pnl = (price - entry[c]) * pos[c]
                pnl_pct = (price - entry[c]) / entry[c]
                
                close = False
                reason = ''
                if pnl_pct >= cfg['tp']:
                    close = True; reason = 'tp'
                if pnl_pct <= -cfg['sl']:
                    close = True; reason = 'sl'
                if rsi > cfg['rsi_sell'] and bb > cfg['bb_sell']:
                    close = True; reason = 'rsi_overbought'
                
                if close:
                    fee = price * pos[c] * 0.001
                    cap += entry[c] * pos[c] + pnl - fee
                    trades.append({'t':'LONG_CLOSE','c':c,'p':price,'pnl':pnl,'reason':reason})
                    pos[c] = 0; entry[c] = 0
            
            # 做空开仓
            if rsi > cfg['short_rsi'] and bb > cfg['short_bb'] and cap > 10 and short_qty[c] == 0 and pos[c] == 0:
                invest = cap * pr
                qty = invest * lev / price
                fee = invest * 0.001
                cap -= (invest + fee)  # 借入等值资产
                short_qty[c] = qty
                short_entry[c] = price
                trades.append({'t':'SHORT_OPEN','c':c,'p':price,'qty':qty})
            
            # 平空
            if short_qty[c] > 0:
                pnl = (short_entry[c] - price) * short_qty[c]
                pnl_pct = (short_entry[c] - price) / short_entry[c]
                
                close = False
                reason = ''
                if pnl_pct >= cfg['tp']:
                    close = True; reason = 'tp'
                if pnl_pct <= -cfg['sl']:
                    close = True; reason = 'sl'
                if rsi < cfg['rsi_buy'] or bb < cfg['bb_buy']:
                    close = True; reason = 'rsi_oversold'
                
                if close:
                    fee = price * short_qty[c] * 0.001
                    # 平空: 归还资产,获得利润
                    cap += short_entry[c] * short_qty[c] + pnl - fee
                    trades.append({'t':'SHORT_CLOSE','c':c,'p':price,'pnl':pnl,'reason':reason})
                    short_qty[c] = 0; short_entry[c] = 0
    
    # 最终计算 (平掉所有仓位)
    final = cap
    for c in valid:
        if pos[c] > 0:
            final += entry[c] * pos[c] + (day_price[c] - entry[c]) * pos[c] - day_price[c] * pos[c] * 0.001
        if short_qty[c] > 0:
            final += short_entry[c] * short_qty[c] + (short_entry[c] - day_price[c]) * short_qty[c] - day_price[c] * short_qty[c] * 0.001
    
    closed = [t for t in trades if 'CLOSE' in t['t']]
    wins = sum(1 for t in closed if t.get('pnl', 0) > 0)
    
    return {
        'return': (final - initial) / initial * 100,
        'win_rate': wins / len(closed) * 100 if closed else 0,
        'trades': len(trades),
        'wins': wins,
        'losses': len(closed) - wins,
        'final': final
    }

def stress_test(initial, data, cfg):
    log("\n" + "="*60)
    log("【测试1: 极限测试】")
    log("="*60)
    
    results = {}
    
    # 极端下跌
    log("\n📉 极端下跌 (-60%):")
    sdata = {c: data[c][-200:].copy() if c in data else [] for c in COINS}
    for c in sdata:
        for i in range(30):
            idx = len(sdata[c]) - 30 + i
            if 0 <= idx < len(sdata[c]):
                sdata[c][idx]['close'] *= (1 - 0.03 * (i+1))
    r = simulate(initial, sdata, cfg)
    results['drop'] = r['return'] if r else 0
    log(f"  → {results['drop']:+.2f}%")
    
    # 极端上涨
    log("\n📈 极端上涨 (+50%):")
    sdata = {c: data[c][-200:].copy() if c in data else [] for c in COINS}
    for c in sdata:
        for i in range(30):
            idx = len(sdata[c]) - 30 + i
            if 0 <= idx < len(sdata[c]):
                sdata[c][idx]['close'] *= (1 + 0.025 * (i+1))
    r = simulate(initial, sdata, cfg)
    results['rise'] = r['return'] if r else 0
    log(f"  → {results['rise']:+.2f}%")
    
    # 横盘
    log("\n➡️ 横盘 (±2%):")
    sdata = {c: data[c][-100:].copy() if c in data else [] for c in COINS}
    for c in sdata:
        base = sdata[c][-1]['close']
        for i in range(len(sdata[c])):
            sdata[c][i]['close'] = base * (1 + np.random.uniform(-0.02, 0.02))
    r = simulate(initial, sdata, cfg)
    results['sideways'] = r['return'] if r else 0
    log(f"  → {results['sideways']:+.2f}%")
    
    return results

def backtest(initial, data, cfg):
    log("\n" + "="*60)
    log("【测试2: 30天回测】")
    log("="*60)
    
    r = simulate(initial, data, cfg)
    if not r:
        log("  ❌ 回测失败")
        return None, 0
    
    log(f"\n  📊 核心指标")
    log(f"  总收益: {r['return']:+.2f}%")
    log(f"  胜率: {r['win_rate']:.1f}%")
    log(f"  交易: {r['trades']}笔 (盈:{r['wins']} 亏:{r['losses']})")
    log(f"  最终资产: ${r['final']:.2f}")
    
    score = 100
    if r['return'] < 0: score -= 30
    if r['return'] < 50: score -= 20
    if r['win_rate'] < 50: score -= 20
    
    log(f"\n  🏆 回测评分: {score}/100")
    return r, score

def optimize(initial, data, base_cfg):
    log("\n" + "="*60)
    log("【测试3: 自主优化】")
    log("="*60)
    
    best_cfg = base_cfg.copy()
    best_ret = 0
    
    # 测试RSI
    log("\n🔍 测试RSI组合...")
    for rb in [38, 40, 43, 45, 48]:
        for rs in [50, 53, 55, 58, 60]:
            if rb >= rs: continue
            cfg = base_cfg.copy()
            cfg['rsi_buy'] = rb
            cfg['rsi_sell'] = rs
            r = simulate(initial, data, cfg)
            if r and r['return'] > best_ret:
                best_ret = r['return']
                best_cfg = cfg.copy()
                log(f"  🆕 RSI{rb}/{rs} → {best_ret:.2f}%")
    
    # 测试止盈止损
    log("\n🔍 测试止盈止损...")
    for tp in [0.06, 0.08, 0.10]:
        for sl in [0.03, 0.035, 0.04]:
            if tp <= sl: continue
            cfg = base_cfg.copy()
            cfg['tp'] = tp
            cfg['sl'] = sl
            r = simulate(initial, data, cfg)
            if r and r['return'] > best_ret:
                best_ret = r['return']
                best_cfg = cfg.copy()
                log(f"  🆕 TP{int(tp*100)}% SL{int(sl*100)}% → {best_ret:.2f}%")
    
    # 测试仓位
    log("\n🔍 测试仓位...")
    for pos in [0.25, 0.30, 0.35]:
        cfg = base_cfg.copy()
        cfg['position'] = pos
        r = simulate(initial, data, cfg)
        if r and r['return'] > best_ret:
            best_ret = r['return']
            best_cfg = cfg.copy()
            log(f"  🆕 仓{int(pos*100)}% → {best_ret:.2f}%")
    
    log(f"\n🏆 最优: {best_ret:.2f}%")
    log(f"  RSI:{best_cfg['rsi_buy']}/{best_cfg['rsi_sell']} TP:{best_cfg['tp']*100:.0f}% 仓:{best_cfg['position']*100:.0f}%")
    
    return best_cfg, best_ret

def iterate(initial, data, iterations=5):
    log("\n" + "="*60)
    log(f"【测试4: 持续迭代 ({iterations}轮)】")
    log("="*60)
    
    base_cfg = {
        'rsi_buy':43,'rsi_sell':53,'bb_buy':25,'bb_sell':75,
        'tp':0.08,'sl':0.035,'position':0.30,'leverage':3,
        'short_rsi':70,'short_bb':85
    }
    
    best_cfg = base_cfg.copy()
    best_ret = 0
    history = []
    
    for i in range(iterations):
        cfg = best_cfg.copy()
        mutation = random.choice(['rsi', 'tp', 'position'])
        
        if mutation == 'rsi':
            cfg['rsi_buy'] = max(30, min(50, cfg['rsi_buy'] + random.choice([-3, 3])))
            cfg['rsi_sell'] = max(55, min(70, cfg['rsi_sell'] + random.choice([-3, 3])))
        elif mutation == 'tp':
            cfg['tp'] = max(0.04, min(0.15, cfg['tp'] + random.choice([-0.02, 0.02])))
        else:
            cfg['position'] = max(0.15, min(0.45, cfg['position'] + random.choice([-0.05, 0.05])))
        
        r = simulate(initial, data, cfg)
        if r:
            log(f"  第{i+1}轮: {r['return']:+.2f}% (RSI{cfg['rsi_buy']}/{cfg['rsi_sell']} TP:{cfg['tp']*100:.0f}%)")
            history.append({'iter':i+1,'return':r['return'],'config':cfg.copy()})
            
            if r['return'] > best_ret:
                best_ret = r['return']
                best_cfg = cfg.copy()
                log(f"    🆕 新最优!")
    
    log(f"\n🏆 最终最优: {best_ret:.2f}%")
    return best_cfg, best_ret, history

def main():
    print("="*60)
    print("Hermes G12 全面测试套件 (修复版)")
    print("="*60)
    
    with open(LOG_FILE, 'w') as f:
        f.write(f"G12全面测试 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 获取数据
    print("\n📥 获取数据...")
    data = {}
    for c in COINS:
        d = get_klines(f'{c}USDT', 720)
        if d and len(d) > 100:
            data[c] = d
            print(f"  {c}: {len(d)}条")
        time.sleep(0.05)
    
    if len(data) < 3:
        print("❌ 数据不足"); return
    
    initial = 1000
    base_cfg = {
        'rsi_buy':43,'rsi_sell':53,'bb_buy':25,'bb_sell':75,
        'tp':0.08,'sl':0.035,'position':0.30,'leverage':3,
        'short_rsi':70,'short_bb':85
    }
    
    # 测试
    stress_results = stress_test(initial, data, base_cfg)
    bt_result, bt_score = backtest(initial, data, base_cfg)
    opt_cfg, opt_ret = optimize(initial, data, base_cfg)
    iter_cfg, iter_ret, iter_history = iterate(initial, data, 5)
    
    # 报告
    print("\n" + "="*60)
    print("【综合测试报告】")
    print("="*60)
    print(f"""
📊 极限测试:
  极端下跌: {stress_results.get('drop', 0):+.2f}%
  极端上涨: {stress_results.get('rise', 0):+.2f}%
  横盘:     {stress_results.get('sideways', 0):+.2f}%

📈 30天回测:
  收益: {bt_result['return'] if bt_result else 0:+.2f}%
  胜率: {bt_result['win_rate'] if bt_result else 0:.1f}%
  评分: {bt_score}/100

🔧 自主优化最优:
  收益: {opt_ret:.2f}%
  配置: RSI{opt_cfg['rsi_buy']}/{opt_cfg['rsi_sell']} TP:{opt_cfg['tp']*100:.0f}%

🔄 持续迭代最优:
  收益: {iter_ret:.2f}%

🏆 推荐配置:
  RSI: {iter_cfg['rsi_buy']}/{iter_cfg['rsi_sell']}
  TP: {iter_cfg['tp']*100:.0f}% SL: {iter_cfg['sl']*100:.1f}%
  仓: {iter_cfg['position']*100:.0f}%
""")
    
    with open('/tmp/g12_comprehensive_results.json', 'w') as f:
        json.dump({
            'stress': stress_results,
            'backtest': bt_result,
            'optimized': {'config': opt_cfg, 'return': opt_ret},
            'iterated': {'config': iter_cfg, 'return': iter_ret},
        }, f, indent=2, default=str)
    
    print("="*60)
    print("✅ 测试完成!")
    print("="*60)

if __name__ == '__main__':
    main()
