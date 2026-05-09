#!/usr/bin/env python3
"""GO2SE Genius v6.0 修复版 - 处理杠杆强平 + 放宽条件"""
import requests, time, json, numpy as np

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

def get_klines(sym, interval='1h', limit=720):
    end = int(time.time()*1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval={interval}&startTime={start}&endTime={end}&limit={limit}'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=30)
        return [{'close':float(k[4]),'high':float(k[2]),'low':float(k[3])} for k in r.json()]
    except: return []

def get_rsi(prices, period=14):
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

def simulate_fixed(initial_capital, price_data, cfg):
    """修复版: 处理强平 + 放宽条件"""
    valid_coins = [c for c in COINS if c in price_data and len(price_data[c]) > 0]
    if not valid_coins: return None
    min_days = min(len(price_data[c]) for c in valid_coins)
    
    capital = initial_capital
    positions = {c: 0 for c in valid_coins}
    entry_prices = {c: 0 for c in valid_coins}
    trades = []
    leverage = cfg.get('leverage', 1)
    liquidation_ratio = 0.5  # 强平线50%
    
    for day_idx in range(min_days):
        day_data = {c: price_data[c][day_idx] for c in valid_coins}
        
        for c in valid_coins:
            d = day_data[c]
            highs = [price_data[c][i]['high'] for i in range(max(0, day_idx-19), day_idx+1)]
            lows = [price_data[c][i]['low'] for i in range(max(0, day_idx-19), day_idx+1)]
            prices = [price_data[c][i]['close'] for i in range(max(0, day_idx-14), day_idx+1)]
            
            rsi_7 = get_rsi(prices, 7)
            rsi_14 = get_rsi(prices, 14)
            bb_pos = bollinger_pos(d['close'], highs, lows, 20)
            cur_qty = positions[c]
            
            # ========== 买入信号 ==========
            buy = False
            if cfg['mode'] == 'normal':
                # 普通模式: OR条件 (放宽)
                if rsi_7 < cfg['rsi_buy'] or bb_pos < cfg['bb_buy'] or cfg.get('chg_buy', 0) < -2:
                    buy = True
            else:
                # 专家模式: OR条件 (放宽，不是AND)
                if rsi_7 < cfg['rsi_buy'] or bb_pos < cfg['bb_buy']:
                    buy = True
            
            if buy and capital > 10:
                invest = capital * cfg['position_ratio']
                qty = invest / d['close']
                cost = qty * d['close'] * 1.001
                if cost <= capital:
                    capital -= cost
                    positions[c] += qty
                    entry_prices[c] = d['close']
                    trades.append({'type':'BUY','coin':c,'price':d['close']})
            
            # ========== 持仓管理 ==========
            if cur_qty > 0:
                entry = entry_prices[c]
                pnl_ratio = (d['close'] - entry) / entry
                
                # ========== 杠杆强平检查 ==========
                if leverage > 1:
                    # 杠杆亏损 = pnl_ratio * leverage
                    leveraged_pnl = pnl_ratio * leverage
                    # 强平线: 亏损 > 1/leverage (如3x杠杆，强平线-33%)
                    if leveraged_pnl < -liquidation_ratio:
                        # 触发强平，损失50%
                        loss_amount = capital * liquidation_ratio
                        capital -= loss_amount
                        positions[c] = 0
                        entry_prices[c] = 0
                        trades.append({'type':'LIQUIDATION','coin':c,'price':d['close'],'loss':loss_amount})
                        continue
                
                # ========== 止盈止损 ==========
                sell = False
                pnl = pnl_ratio * leverage if leverage > 1 else pnl_ratio
                
                if pnl >= cfg['take_profit']:
                    sell = True
                    trades.append({'type':'TAKE_PROFIT','coin':c,'price':d['close'],'pnl':pnl})
                elif pnl <= -cfg['stop_loss']:
                    sell = True
                    trades.append({'type':'STOP_LOSS','coin':c,'price':d['close'],'pnl':pnl})
                
                # ========== 卖出信号 ==========
                if not sell:
                    if cfg['mode'] == 'normal':
                        if rsi_7 > cfg['rsi_sell'] or bb_pos > cfg['bb_sell']:
                            sell = True
                    else:
                        if rsi_7 > cfg['rsi_sell'] or bb_pos > cfg['bb_sell']:
                            sell = True
                
                if sell:
                    qty = cur_qty * cfg['sell_ratio']
                    revenue = qty * d['close'] * 0.999
                    capital += revenue
                    positions[c] -= qty
                    if positions[c] <= 0:
                        positions[c] = 0
                        entry_prices[c] = 0
                    trades.append({'type':'SELL','coin':c,'price':d['close'],'pnl':pnl})
    
    # 计算结果
    final_prices = {c: price_data[c][-1]['close'] for c in valid_coins}
    final_value = capital + sum(positions[c] * final_prices.get(c, 0) for c in valid_coins)
    
    total_return = (final_value - initial_capital) / initial_capital * 100
    
    closed_trades = [t for t in trades if t['type'] in ['TAKE_PROFIT','STOP_LOSS','SELL','LIQUIDATION']]
    wins = sum(1 for t in closed_trades if t.get('pnl', 0) > 0)
    losses = sum(1 for t in closed_trades if t.get('pnl', 0) < 0)
    liquidations = sum(1 for t in trades if t['type'] == 'LIQUIDATION')
    win_rate = wins / (wins + losses) * 100 if (wins + losses) > 0 else 0
    
    return {
        'return': total_return, 'win_rate': win_rate,
        'total_trades': len(trades),
        'wins': wins, 'losses': losses,
        'liquidations': liquidations
    }

print("="*70)
print("GO2SE Genius v6.0 修复版")
print("修复: 杠杆强平 + 条件放宽 + 小时级数据")
print("="*70)

print("\n【获取小时级数据 (30天x24小时)】")
price_data = {}
for c in COINS:
    print(f"  {c}...", end=' ')
    data = get_klines(f'{c}USDT', '1h', 720)  # 30天小时数据
    if data and len(data) > 100:
        price_data[c] = data
        print(f"{len(data)}条")
    time.sleep(0.1)

# 配置矩阵 - 修复版
configs = [
    # 普通模式 - 1x
    {'name':'普通-1x','mode':'normal','rsi_buy':35,'rsi_sell':65,'bb_buy':25,'bb_sell':75,'position_ratio':0.7,'take_profit':0.05,'stop_loss':0.02,'sell_ratio':0.5,'leverage':1},
    {'name':'普通-1xR','mode':'normal','rsi_buy':40,'rsi_sell':60,'bb_buy':30,'bb_sell':70,'position_ratio':0.6,'take_profit':0.04,'stop_loss':0.02,'sell_ratio':0.5,'leverage':1},
    # 普通模式 - 3x (有强平)
    {'name':'普通-3x','mode':'normal','rsi_buy':35,'rsi_sell':65,'bb_buy':25,'bb_sell':75,'position_ratio':0.4,'take_profit':0.06,'stop_loss':0.025,'sell_ratio':0.5,'leverage':3},
    {'name':'普通-3xR','mode':'normal','rsi_buy':40,'rsi_sell':60,'bb_buy':30,'bb_sell':70,'position_ratio':0.35,'take_profit':0.05,'stop_loss':0.02,'sell_ratio':0.5,'leverage':3},
    # 专家模式 - 1x (OR条件)
    {'name':'专家-1x','mode':'expert','rsi_buy':35,'rsi_sell':65,'bb_buy':25,'bb_sell':75,'position_ratio':0.7,'take_profit':0.05,'stop_loss':0.02,'sell_ratio':0.5,'leverage':1},
    {'name':'专家-1xR','mode':'expert','rsi_buy':40,'rsi_sell':60,'bb_buy':30,'bb_sell':70,'position_ratio':0.6,'take_profit':0.04,'stop_loss':0.02,'sell_ratio':0.5,'leverage':1},
    # 专家模式 - 3x (有强平)
    {'name':'专家-3x','mode':'expert','rsi_buy':35,'rsi_sell':65,'bb_buy':25,'bb_sell':75,'position_ratio':0.4,'take_profit':0.06,'stop_loss':0.025,'sell_ratio':0.5,'leverage':3},
    {'name':'专家-3xR','mode':'expert','rsi_buy':40,'rsi_sell':60,'bb_buy':30,'bb_sell':70,'position_ratio':0.35,'take_profit':0.05,'stop_loss':0.02,'sell_ratio':0.5,'leverage':3},
    # 高频版
    {'name':'高频-1x','mode':'normal','rsi_buy':45,'rsi_sell':55,'bb_buy':35,'bb_sell':65,'position_ratio':0.5,'take_profit':0.03,'stop_loss':0.015,'sell_ratio':0.6,'leverage':1},
    {'name':'高频-3x','mode':'normal','rsi_buy':45,'rsi_sell':55,'bb_buy':35,'bb_sell':65,'position_ratio':0.3,'take_profit':0.04,'stop_loss':0.02,'sell_ratio':0.6,'leverage':3},
]

results = []

print(f"\n【执行{len(configs)}种配置回测】")
for cfg in configs:
    stats = simulate_fixed(1000, price_data, cfg)
    if stats:
        results.append({**cfg, **stats})
        print(f"  {cfg['name']:12} {cfg['mode']:7} {cfg['leverage']}x RSI:{cfg['rsi_buy']}/{cfg['rsi_sell']} BB:{cfg['bb_buy']}/{cfg['bb_sell']} -> 收益:{stats['return']:>+7.2f}% 胜率:{stats['win_rate']:>5.1f}% 交易:{stats['total_trades']} 强平:{stats['liquidations']}")

results.sort(key=lambda x: -x['return'])

print("\n" + "="*70)
print("【结果矩阵 - v6.0修复版】")
print("="*70)

print(f"\n{'配置':12} {'模式':7} {'杠杆':5} {'仓位':6} {'RSI':8} {'BB':8} {'止盈':6} {'止损':6} {'收益':9} {'胜率':7} {'交易':6} {'强平':5}")
print("-"*100)
for r in results:
    print(f"{r['name']:12} {r['mode']:7} {r['leverage']:4d}x {r['position_ratio']*100:5.0f}% {r['rsi_buy']}/{r['rsi_sell']:5} {r['bb_buy']}/{r['bb_sell']:5} {r['take_profit']*100:5.1f}% {r['stop_loss']*100:5.1f}% {r['return']:>+8.2f}% {r['win_rate']:>5.1f}% {r['total_trades']:5d} {r['liquidations']:4d}")

best = results[0] if results else None

print("\n" + "="*70)
print("【最优配置 - v6.0修复版】")
print("="*70)

if best:
    print(f"""
┌─────────────────────────────────────────────────────────────────┐
│  配置: {best['name']}                                               │
│  模式: {best['mode']}  杠杆: {best['leverage']}x                                      │
│  ─────────────────────────────────────────────────────────────  │
│  收益: {best['return']:>+8.2f}%  胜率: {best['win_rate']:.1f}%                           │
│  交易: {best['total_trades']}次  胜: {best['wins']}  负: {best['losses']}  强平: {best['liquidations']}                  │
└─────────────────────────────────────────────────────────────────┘
""")

# 分类对比
normal_best = [r for r in results if r['mode']=='normal'][0] if [r for r in results if r['mode']=='normal'] else None
expert_best = [r for r in results if r['mode']=='expert'][0] if [r for r in results if r['mode']=='expert'] else None

print("【普通 vs 专家 对比】")
if normal_best and expert_best:
    print(f"  普通模式: {normal_best['return']:+.2f}% ({normal_best['win_rate']:.1f}%胜率, {normal_best['total_trades']}交易, {normal_best['liquidations']}强平)")
    print(f"  专家模式: {expert_best['return']:+.2f}% ({expert_best['win_rate']:.1f}%胜率, {expert_best['total_trades']}交易, {expert_best['liquidations']}强平)")
    better = "普通" if normal_best['return'] > expert_best['return'] else "专家"
    print(f"  推荐: {better}模式")

# 杠杆对比
lev1 = [r for r in results if r['leverage']==1]
lev3 = [r for r in results if r['leverage']==3]
if lev1 and lev3:
    best_lev1 = max(lev1, key=lambda x: x['return'])
    best_lev3 = max(lev3, key=lambda x: x['return'])
    print(f"\n【杠杆对比】")
    print(f"  1x最佳: {best_lev1['name']} {best_lev1['return']:+.2f}% (强平:{best_lev1['liquidations']})")
    print(f"  3x最佳: {best_lev3['name']} {best_lev3['return']:+.2f}% (强平:{best_lev3['liquidations']})")

with open('/tmp/backtest_v60_fixed.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\n✅ v6.0修复版回测完成!")
