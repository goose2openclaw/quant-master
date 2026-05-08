#!/usr/bin/env python3
"""
Hermes G12 - 简化正确模拟器
不使用杠杆计算,只乘以杠杆计算盈亏
"""
import requests, time, json, numpy as np, random
from datetime import datetime

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

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
    """简化正确的模拟"""
    valid = [c for c in COINS if c in data and len(data[c]) > 100]
    if not valid: return None
    min_d = min(len(data[c]) for c in valid)
    
    # 初始资金
    cash = initial
    
    # 持仓: {币种: 数量}
    positions = {c: 0.0 for c in valid}
    # 入场价
    entries = {c: 0.0 for c in valid}
    
    trades = []
    equity_curve = [initial]
    
    lev = cfg.get('leverage', 3)
    pos_size = cfg.get('position', 0.30)  # 仓位比例
    tp = cfg.get('tp', 0.08)  # 止盈
    sl = cfg.get('sl', 0.035)  # 止损
    
    for d in range(min_d):
        prices = {c: data[c][d]['close'] for c in valid}
        
        for c in valid:
            cs = [data[c][i]['close'] for i in range(max(0,d-30),d+1)]
            hs = [data[c][i]['high'] for i in range(max(0,d-19),d+1)]
            ls = [data[c][i]['low'] for i in range(max(0,d-19),d+1)]
            
            if len(cs) < 30: continue
            
            rsi = get_rsi(cs[-15:], 7)
            bb = bollinger_pos(prices[c], hs, ls, 20)
            
            # ========== 做多 ==========
            # 开多仓条件
            if rsi < cfg['rsi_buy'] and bb < cfg['bb_buy'] and positions[c] == 0 and cash > 10:
                # 用30%仓位,3倍杠杆
                invest = cash * pos_size
                qty = invest / prices[c]
                cost = qty * prices[c]
                fee = cost * 0.001
                cash -= fee
                positions[c] = qty
                entries[c] = prices[c]
                trades.append({'type':'LONG','c':c,'price':prices[c],'qty':qty})
            
            # 平多仓
            if positions[c] > 0:
                pnl_pct = (prices[c] - entries[c]) / entries[c]
                
                # 止盈/止损/信号
                if pnl_pct >= tp or pnl_pct <= -sl or (rsi > cfg['rsi_sell'] and bb > cfg['bb_sell']):
                    pnl = positions[c] * entries[c] * pnl_pct * lev
                    fee = positions[c] * prices[c] * 0.001
                    cash += positions[c] * entries[c] + pnl - fee
                    trades.append({'type':'CLOSE_LONG','c':c,'pnl':pnl})
                    positions[c] = 0
            
            # ========== 做空 ==========
            # 开空仓条件  
            if rsi > cfg['short_rsi'] and bb > cfg['short_bb'] and positions[c] == 0 and cash > 10:
                invest = cash * pos_size
                qty = invest / prices[c]
                fee = qty * prices[c] * 0.001
                cash -= fee
                positions[c] = -qty  # 负数表示做空
                entries[c] = prices[c]
                trades.append({'type':'SHORT','c':c,'price':prices[c],'qty':qty})
            
            # 平空仓
            if positions[c] < 0:
                qty = abs(positions[c])
                pnl_pct = (entries[c] - prices[c]) / entries[c]  # 做空盈亏
                
                if pnl_pct >= tp or pnl_pct <= -sl or (rsi < cfg['rsi_buy'] or bb < cfg['bb_buy']):
                    pnl = qty * entries[c] * pnl_pct * lev
                    fee = qty * prices[c] * 0.001
                    cash += qty * entries[c] + pnl - fee
                    trades.append({'type':'CLOSE_SHORT','c':c,'pnl':pnl})
                    positions[c] = 0
        
        # 计算当日权益
        equity = cash
        for c in valid:
            if positions[c] > 0:
                equity += positions[c] * prices[c]
            elif positions[c] < 0:
                qty = abs(positions[c])
                equity += entries[c] * qty + (entries[c] - prices[c]) * qty
        equity_curve.append(equity)
    
    # 最终平仓
    final_prices = {c: data[c][-1]['close'] for c in valid}
    final = cash
    for c in valid:
        if positions[c] > 0:
            pnl = positions[c] * entries[c] * ((final_prices[c] - entries[c]) / entries[c]) * lev
            final += positions[c] * final_prices[c] + pnl - positions[c] * final_prices[c] * 0.001
        elif positions[c] < 0:
            qty = abs(positions[c])
            pnl_pct = (entries[c] - final_prices[c]) / entries[c]
            pnl = qty * entries[c] * pnl_pct * lev
            final += qty * entries[c] + pnl - qty * final_prices[c] * 0.001
    
    closed = [t for t in trades if 'CLOSE' in t['type']]
    wins = sum(1 for t in closed if t.get('pnl', 0) > 0)
    
    peak = initial
    max_dd = 0
    for v in equity_curve:
        peak = max(peak, v)
        dd = (peak - v) / peak * 100
        if dd > max_dd: max_dd = dd
    
    return {
        'return': (final - initial) / initial * 100,
        'win_rate': wins / len(closed) * 100 if closed else 0,
        'trades': len(trades),
        'wins': wins,
        'losses': len(closed) - wins,
        'max_dd': max_dd,
        'final': final
    }

def main():
    print("="*60)
    print("G12 简化模拟器测试")
    print("="*60)
    
    # 获取数据
    print("\n📥 获取数据...")
    data = {}
    for c in COINS:
        d = get_klines(f'{c}USDT', 720)
        if d and len(d) > 100:
            data[c] = d
            print(f"  {c}: {len(d)}条")
        time.sleep(0.05)
    
    cfg = {
        'rsi_buy':43,'rsi_sell':53,'bb_buy':25,'bb_sell':75,
        'tp':0.08,'sl':0.035,'position':0.30,'leverage':3,
        'short_rsi':70,'short_bb':85
    }
    
    print("\n📊 基线测试:")
    r = simulate(1000, data, cfg)
    if r:
        print(f"  收益: {r['return']:+.2f}%")
        print(f"  胜率: {r['win_rate']:.1f}%")
        print(f"  交易: {r['trades']}笔")
        print(f"  最大回撤: {r['max_dd']:.1f}%")
        print(f"  最终: ${r['final']:.2f}")
    else:
        print("  ❌ 测试失败")
    
    print("\n" + "="*60)

if __name__ == '__main__':
    main()
