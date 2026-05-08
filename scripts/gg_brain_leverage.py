#!/usr/bin/env python3
"""
GBrain Leverage v1.0 - 合约杠杆版本
目标: 月收益100%+
"""
import requests, hmac, hashlib, time, json, numpy as np

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']
LEVERAGE = 5  # 默认5倍杠杆

def get_price(sym):
    try:
        r = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={sym}', proxies=PROXIES, timeout=5)
        return float(r.json()['price'])
    except: return 0

def get_klines(sym, interval='1h', limit=100):
    end = int(time.time()*1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval={interval}&startTime={start}&endTime={end}&limit={limit}'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=15)
        return [{'open':float(k[1]),'high':float(k[2]),'low':float(k[3]),'close':float(k[4]),'volume':float(k[5])} for k in r.json()]
    except: return []

def get_rsi(prices, period=14):
    if len(prices) < period+1: return 50
    deltas = np.diff(prices)
    gain = np.where(deltas>0, deltas, 0)
    loss = np.where(deltas<0, -deltas, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    return 100-(100/(1+avg_gain/avg_loss)) if avg_loss!=0 else 100

def get_futures_account():
    ts = int(time.time()*1000)
    params = f'timestamp={ts}&recvWindow=5000'
    sig = hmac.new(API_SECRET.encode(), params.encode(), hashlib.sha256).hexdigest()
    try:
        r = requests.get(f'https://api.binance.com/fapi/v2/account?{params}&signature={sig}', headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except: return None

def set_leverage(symbol, leverage):
    ts = int(time.time()*1000)
    params = f'symbol={symbol}&leverage={leverage}&timestamp={ts}&recvWindow=5000'
    sig = hmac.new(API_SECRET.encode(), params.encode(), hashlib.sha256).hexdigest()
    try:
        r = requests.post(f'https://api.binance.com/fapi/v1/leverage?{params}&signature={sig}', headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except: return None

def futures_order(symbol, side, position_side, quantity, leverage=5):
    ts = int(time.time()*1000)
    params = {
        'symbol': symbol, 'side': side, 'positionSide': position_side,
        'type': 'MARKET', 'quantity': quantity, 'leverage': leverage,
        'timestamp': ts, 'recvWindow': 5000
    }
    query = '&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    try:
        r = requests.post(f'https://api.binance.com/fapi/v1/order?{query}&signature={sig}', headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except: return None

def simulate_leverage(initial_capital, price_data, cfg):
    """杠杆模拟回测"""
    capital = initial_capital
    leverage = cfg['leverage']
    position = 0  # 0=无, 1=多, -1=空
    entry_price = 0
    trades = []
    
    for day_idx in range(len(price_data.get('BTC', [])) - 1):
        signal = None
        
        # 收集所有币种信号
        signals = []
        for c in COINS:
            if c not in price_data or day_idx >= len(price_data[c]) - 1:
                continue
            prices = [price_data[c][i]['close'] for i in range(max(0, day_idx-14), day_idx+1)]
            rsi = get_rsi(prices, cfg['rsi_period'])
            chg = (price_data[c][day_idx+1]['close'] - price_data[c][day_idx]['close']) / price_data[c][day_idx]['close'] * 100
            
            # 多头信号
            if rsi < cfg['rsi_buy'] and position != 1:
                signals.append(('LONG', c, rsi, chg))
            # 空头信号
            elif rsi > cfg['rsi_sell'] and position != -1 and cfg.get('allow_short', False):
                signals.append(('SHORT', c, rsi, chg))
        
        # 选择信号
        if signals:
            # 选择RSI最极端的
            signals.sort(key=lambda x: x[2] if x[0]=='LONG' else -x[2])
            if signals[0][0] == 'LONG':
                signal = ('LONG', signals[0][1])
            elif cfg.get('allow_short', False):
                signal = ('SHORT', signals[0][1])
        
        # 执行交易
        price = price_data['BTC'][day_idx]['close']  # 用BTC计算
        
        if signal and capital > 10:
            _, coin = signal
            coin_price = price_data[coin][day_idx]['close']
            
            # 仓位大小
            pos_size = capital * leverage * cfg['position_ratio']
            qty = pos_size / coin_price
            
            if signal[0] == 'LONG':
                position = 1
                entry_price = coin_price
                trades.append({'type':'LONG','coin':coin,'price':coin_price,'rsi':signals[0][2]})
            elif signal[0] == 'SHORT':
                position = -1
                entry_price = coin_price
                trades.append({'type':'SHORT','coin':coin,'price':coin_price,'rsi':signals[0][2]})
        
        # 持仓管理
        if position != 0:
            coin = trades[-1]['coin'] if trades else 'BTC'
            coin_price = price_data.get(coin, [{}])[day_idx]['close']
            if coin_price == 0: coin_price = entry_price
            
            pnl = (coin_price - entry_price) / entry_price * 100
            if position == -1:
                pnl = -pnl  # 空头PnL反转
            
            # 止损
            if pnl <= -cfg['stop_loss'] * 100:
                capital += capital * pnl / 100 * leverage
                trades.append({'type':'STOP_LOSS','coin':coin,'pnl':pnl})
                position = 0
            
            # 止盈
            elif pnl >= cfg['take_profit'] * 100:
                capital += capital * pnl / 100 * leverage
                trades.append({'type':'TAKE_PROFIT','coin':coin,'pnl':pnl})
                position = 0
            
            # RSI平仓信号
            prices = [price_data[coin][i]['close'] for i in range(max(0, day_idx-14), day_idx+1)]
            rsi = get_rsi(prices, cfg['rsi_period'])
            
            if position == 1 and rsi > cfg['rsi_sell']:
                capital += capital * pnl / 100 * leverage
                trades.append({'type':'CLOSE_LONG','coin':coin,'pnl':pnl})
                position = 0
            elif position == -1 and rsi < cfg['rsi_buy']:
                capital += capital * pnl / 100 * leverage
                trades.append({'type':'CLOSE_SHORT','coin':coin,'pnl':pnl})
                position = 0
    
    final_return = (capital - initial_capital) / initial_capital * 100
    
    longs = [t for t in trades if t['type'] in ['LONG','TAKE_PROFIT','STOP_LOSS']]
    wins = sum(1 for t in longs if t.get('pnl', 0) > 0)
    
    return {
        'return': final_return,
        'win_rate': wins / len(longs) * 100 if longs else 0,
        'total_trades': len(trades),
        'wins': wins,
        'losses': len(longs) - wins
    }

# ==================== 主程序 ====================
print("="*70)
print("GBrain Leverage v1.0 - 合约杠杆版本")
print("目标: 月收益100%+")
print("="*70)

# 获取数据
print("\n【获取小时级数据】")
price_data = {}
for c in COINS:
    print(f"  {c}...", end=' ')
    data = get_klines(f'{c}USDT', '1h', 720)  # 30天*24小时
    if data and len(data) > 100:
        price_data[c] = data
        print(f"{len(data)}条")
    else:
        # 降级到日线
        data = get_klines(f'{c}USDT', '1d', 60)
        if data:
            price_data[c] = data
            print(f"{len(data)}条(日线)")
    time.sleep(0.1)

print(f"\n数据范围: {len(price_data.get('BTC',[]))}条")

# 配置矩阵
configs = [
    # 高杠杆配置
    {'name':'5x稳健','leverage':5,'rsi_period':14,'rsi_buy':30,'rsi_sell':70,'position_ratio':0.3,'take_profit':0.10,'stop_loss':0.04,'allow_short':True},
    {'name':'5x积极','leverage':5,'rsi_period':14,'rsi_buy':25,'rsi_sell':75,'position_ratio':0.4,'take_profit':0.15,'stop_loss':0.05,'allow_short':True},
    {'name':'5x激进','leverage':5,'rsi_period':7,'rsi_buy':25,'rsi_sell':75,'position_ratio':0.5,'take_profit':0.20,'stop_loss':0.06,'allow_short':True},
    {'name':'10x稳健','leverage':10,'rsi_period':14,'rsi_buy':30,'rsi_sell':70,'position_ratio':0.2,'take_profit':0.08,'stop_loss':0.03,'allow_short':True},
    {'name':'10x积极','leverage':10,'rsi_period':14,'rsi_buy':25,'rsi_sell':75,'position_ratio':0.3,'take_profit':0.12,'stop_loss':0.04,'allow_short':True},
    {'name':'10x激进','leverage':10,'rsi_period':7,'rsi_buy':20,'rsi_sell':80,'position_ratio':0.4,'take_profit':0.15,'stop_loss':0.05,'allow_short':True},
    {'name':'3x高频','leverage':3,'rsi_period':7,'rsi_buy':30,'rsi_sell':70,'position_ratio':0.6,'take_profit':0.08,'stop_loss':0.03,'allow_short':False},
    {'name':'3x全向','leverage':3,'rsi_period':7,'rsi_buy':25,'rsi_sell':75,'position_ratio':0.5,'take_profit':0.10,'stop_loss':0.04,'allow_short':True},
]

results = []

print(f"\n【执行{len(configs)}种杠杆配置回测】")
for cfg in configs:
    stats = simulate_leverage(1000, price_data, cfg)
    results.append({**cfg, **stats})
    print(f"  {cfg['name']:12} {cfg['leverage']}x 仓:{cfg['position_ratio']*100:.0f}% RSI:{cfg['rsi_buy']}/{cfg['rsi_sell']} -> 收益:{stats['return']:>+8.2f}% 胜率:{stats['win_rate']:>5.1f}% 交易:{stats['total_trades']}")

results.sort(key=lambda x: -x['return'])

print("\n" + "="*70)
print("【GBrain Leverage 结果矩阵】")
print("="*70)
print(f"\n{'配置':14} {'杠杆':5} {'仓位':6} {'RSI买':6} {'RSI卖':6} {'止盈':6} {'止损':6} {'收益':10} {'胜率':7} {'交易':6}")
print("-"*80)
for r in results:
    print(f"{r['name']:14} {r['leverage']:4d}x {r['position_ratio']*100:5.0f}% {r['rsi_buy']:6d} {r['rsi_sell']:6d} {r['take_profit']*100:5.0f}% {r['stop_loss']*100:5.1f}% {r['return']:>+9.2f}% {r['win_rate']:>5.1f}% {r['total_trades']:5d}")

best = results[0]
print(f"""
======================================================================
【GBrain Leverage 最优配置】
======================================================================
配置: {best['name']}
杠杆: {best['leverage']}x 仓位:{best['position_ratio']*100:.0f}%
RSI: {best['rsi_buy']}/{best['rsi_sell']} RSI周期:{best['rsi_period']}
止盈:{best['take_profit']*100:.0f}% 止损:{best['stop_loss']*100:.1f}%
收益: {best['return']:+.2f}% 胜率:{best['win_rate']:.1f}%
交易: {best['total_trades']}次 胜:{best['wins']} 负:{best['losses']}
======================================================================
""")

# 100%目标检查
high_return = [r for r in results if r['return'] >= 100]
if high_return:
    print(f"🎉 {len(high_return)}种配置达到100%目标!")
    for h in high_return:
        print(f"  {h['name']}: {h['return']:+.2f}%")
else:
    best_result = results[0]
    print(f"最高收益: {best_result['return']:+.2f}%")
    print(f"距离100%目标还差: {100 - best_result['return']:.2f}%")

with open('/tmp/backtest_leverage.json', 'w') as f:
    json.dump(results, f, indent=2)

print("✅ GBrain Leverage回测完成!")
