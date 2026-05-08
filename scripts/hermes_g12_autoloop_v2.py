#!/usr/bin/env python3
"""
Hermes G12 - 自主优化持续迭代系统 v3 (修复MACD计算)
"""
import requests, time, json, numpy as np
from datetime import datetime

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']
LOG_FILE = '/tmp/g12_autoloop.log'
ITER_FILE = '/tmp/g12_iterations.json'

def log(msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{ts}] {msg}")

def get_klines(sym, limit=720):
    end = int(time.time()*1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&startTime={start}&endTime={end}&limit={limit}'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=30)
        return [{'close':float(k[4]),'high':float(k[2]),'low':float(k[3])} for k in r.json()]
    except: return []

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

def get_macd(prices):
    if len(prices) < 26: return 0
    return np.mean(prices[-12:]) - np.mean(prices[-26:])

def simulate(initial_capital, price_data, cfg):
    valid = [c for c in COINS if c in price_data and len(price_data[c]) > 100]
    if not valid: return None
    min_d = min(len(price_data[c]) for c in valid)
    
    cap = initial_capital
    pos = {c: 0.0 for c in valid}
    entry = {c: 0.0 for c in valid}
    short = {c: 0.0 for c in valid}
    sent = {c: 0.0 for c in valid}
    trades = []
    
    lev = cfg.get('leverage', 3)
    pr = cfg.get('position', 0.30)
    
    for d in range(min_d):
        day = {c: price_data[c][d] for c in valid}
        
        for c in valid:
            k = day[c]
            # 使用足够长的数据计算指标
            cs = [price_data[c][i]['close'] for i in range(max(0,d-30),d+1)]  # 至少31个点
            hs = [price_data[c][i]['high'] for i in range(max(0,d-19),d+1)]
            ls = [price_data[c][i]['low'] for i in range(max(0,d-19),d+1)]
            
            if len(cs) < 30: continue
            
            rsi = get_rsi(cs[-15:], 7)  # RSI用最近14个
            bb = bollinger_pos(k['close'], hs, ls, 20)
            macd = get_macd(cs)  # MACD需要26个
            
            # 简化的决策 (去掉decision阈值,避免MACD=0问题)
            buy_sig = rsi < cfg['rsi_buy'] and bb < cfg['bb_buy']
            short_sig = rsi > cfg['short_rsi'] and bb > cfg['short_bb']
            
            # 做多
            if buy_sig and cap > 10 and pos[c] == 0 and short[c] == 0:
                inv = cap * pr * lev
                qty = inv / k['close']
                cap -= inv * 0.001
                pos[c] = qty
                entry[c] = k['close']
                trades.append({'t':'LONG','c':c,'p':k['close']})
            
            # 平多
            if pos[c] > 0:
                pnl = (k['close'] - entry[c]) / entry[c] * lev
                sell = pnl >= cfg['tp'] or pnl <= -cfg['sl'] or (rsi > cfg['rsi_sell'] and bb > cfg['bb_sell'])
                if sell:
                    cap += (k['close'] - entry[c]) * pos[c] * lev - pos[c] * k['close'] * 0.001
                    trades.append({'t':'CLOSE','c':c,'p':pnl})
                    pos[c] = 0; entry[c] = 0
            
            # 做空
            if short_sig and cap > 10 and short[c] == 0 and pos[c] == 0:
                inv = cap * pr * lev
                qty = inv / k['close']
                cap -= inv * 0.001
                short[c] = qty
                sent[c] = k['close']
                trades.append({'t':'SHORT','c':c,'p':k['close']})
            
            # 平空
            if short[c] > 0:
                pnl = (sent[c] - k['close']) / sent[c] * lev
                cover = pnl >= cfg['tp'] or pnl <= -cfg['sl'] or rsi < cfg['rsi_buy'] or bb < cfg['bb_buy']
                if cover:
                    cap += (sent[c] - k['close']) * short[c] * lev - short[c] * k['close'] * 0.001
                    trades.append({'t':'COVER','c':c,'p':pnl})
                    short[c] = 0; sent[c] = 0
    
    fin = cap
    for c in valid:
        fin += pos[c] * price_data[c][-1]['close']
        fin += short[c] * (sent[c] - price_data[c][-1]['close'])
    
    closed = [t for t in trades if t['t'] in ('CLOSE','COVER')]
    wins = sum(1 for t in closed if t.get('p',0) > 0)
    
    return {
        'return': (fin-initial_capital)/initial_capital*100,
        'win_rate': wins/len(closed)*100 if closed else 0,
        'trades': len(trades),
        'final': fin
    }

def load_state():
    try:
        with open(ITER_FILE, 'r') as f:
            return json.load(f)
    except: return {'iter':0,'best':None,'best_ret':0,'history':[]}

def save_state(state):
    with open(ITER_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def optimize():
    log("="*50)
    log("G12 自主优化迭代启动 v3")
    
    data = {}
    for c in COINS:
        d = get_klines(f'{c}USDT', 720)
        if d and len(d) > 100:
            data[c] = d
        time.sleep(0.05)
    
    if len(data) < 3:
        log("数据不足")
        return
    
    state = load_state()
    state['iter'] += 1
    iter_num = state['iter']
    
    log(f"第{iter_num}次迭代")
    
    base = state['best'] or {
        'rsi_buy':43,'rsi_sell':53,'bb_buy':25,'bb_sell':75,
        'tp':0.08,'sl':0.035,'position':0.30,'leverage':3,
        'short_rsi':70,'short_bb':85
    }
    
    base_stats = simulate(1000, data, base)
    if not base_stats:
        log("模拟失败")
        return
    
    log(f"基线: {base_stats['return']:+.2f}% | 胜率{base_stats['win_rate']:.1f}% | 交易{base_stats['trades']}笔")
    
    best_cfg = base.copy()
    best_ret = base_stats['return']
    improved = False
    
    # RSI变体
    for rb in [38,40,43,45,48]:
        for rs in [50,53,55,58,60]:
            if rb >= rs: continue
            cfg = base.copy()
            cfg['rsi_buy'] = rb
            cfg['rsi_sell'] = rs
            r = simulate(1000, data, cfg)
            if r and r['return'] > best_ret:
                best_ret = r['return']
                best_cfg = cfg.copy()
                improved = True
                log(f"  🆕 RSI{rb}/{rs} → {r['return']:+.2f}%")
    
    # 止盈止损
    for tp in [0.06,0.08,0.10]:
        for sl in [0.03,0.035,0.04]:
            if tp <= sl: continue
            cfg = base.copy()
            cfg['tp'] = tp; cfg['sl'] = sl
            r = simulate(1000, data, cfg)
            if r and r['return'] > best_ret:
                best_ret = r['return']
                best_cfg = cfg.copy()
                improved = True
                log(f"  🆕 TP{int(tp*100)}% SL{int(sl*100)}% → {r['return']:+.2f}%")
    
    # 仓位
    for pos in [0.25,0.30,0.35]:
        cfg = base.copy()
        cfg['position'] = pos
        r = simulate(1000, data, cfg)
        if r and r['return'] > best_ret:
            best_ret = r['return']
            best_cfg = cfg.copy()
            improved = True
            log(f"  🆕 仓{int(pos*100)}% → {r['return']:+.2f}%")
    
    if improved:
        state['best'] = best_cfg
        state['best_ret'] = best_ret
        log(f"🏆 新最优: {best_ret:.2f}%")
        log(f"   RSI:{best_cfg['rsi_buy']}/{best_cfg['rsi_sell']} TP:{best_cfg['tp']*100:.0f}% SL:{best_cfg['sl']*100:.1f}%")
    else:
        log("⚠️ 未改进")
    
    state['history'].append({
        'iter': iter_num,
        'time': datetime.now().isoformat(),
        'return': base_stats['return'],
        'best': best_ret,
        'improved': improved
    })
    state['history'] = state['history'][-50:]
    
    save_state(state)
    log(f"完成 | 最优:{state['best_ret']:+.2f}%")
    log("="*50)
    
    return state

if __name__ == '__main__':
    optimize()
