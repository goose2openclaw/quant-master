#!/usr/bin/env python3
"""
G20 自主实盘增强版
自主决策 + 自主操作
"""
import requests, hmac, hashlib, time, numpy as np, json
from datetime import datetime

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'

def sign(params):
    sorted_params = sorted(params.items())
    query = '&'.join([f'{k}={v}' for k,v in sorted_params])
    return hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()

def api_get(url, endpoint, params=None):
    params = params or {}
    params['timestamp'] = int(time.time()*1000)
    params['signature'] = sign(params)
    r = requests.get(f'{url}{endpoint}', params=params, headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
    return r.json()

def api_post(url, endpoint, params=None):
    params = params or {}
    params['timestamp'] = int(time.time()*1000)
    params['signature'] = sign(params)
    r = requests.post(f'{url}{endpoint}', params=params, headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
    return r.json()

def get_price(symbol):
    r = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}', proxies=PROXIES, timeout=10)
    return float(r.json()['price'])

def get_klines(sym, limit=720):
    end = int(time.time()*1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&startTime={start}&endTime={end}&limit={limit}'
    r = requests.get(url, proxies=PROXIES, timeout=15)
    return [float(k[4]) for k in r.json()]

def calc_rsi(prices, period=14):
    if len(prices) < period + 1: return 50
    deltas = np.diff(prices)
    gain = np.where(deltas > 0, deltas, 0)
    loss = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    if avg_loss == 0: return 100
    return 100 - (100 / (1 + avg_gain / avg_loss))

# G20参数
PARAMS = {
    'BTC': {'rsi_buy': 45, 'rsi_sell': 79, 'tp': 0.092, 'sl': 0.034},
    'ETH': {'rsi_buy': 29, 'rsi_sell': 79, 'tp': 0.054, 'sl': 0.042},
    'DOGE': {'rsi_buy': 45, 'rsi_sell': 80, 'tp': 0.07, 'sl': 0.03},
    'LINK': {'rsi_buy': 44, 'rsi_sell': 77, 'tp': 0.06, 'sl': 0.045},
}

def main():
    print("=" * 70)
    print("G20 自主实盘增强版")
    print("=" * 70)
    
    log = {'timestamp': datetime.now().isoformat(), 'actions': []}
    
    # Step 1: 检查全仓逐仓资产
    print("\n[Step 1] 检查全仓逐仓资产...")
    margin = api_get('https://api.binance.com', '/sapi/v1/margin/account')
    
    assets_to_convert = []
    for a in margin.get('userAssets', []):
        free = float(a.get('free', 0))
        if free > 1 and a['asset'] in ['ADA', 'XRP', 'DOGE', 'SOL', 'BNB', 'ETH', 'BTC']:
            price = get_price(a['asset'] + 'USDT')
            val = free * price
            assets_to_convert.append((a['asset'], free, price, val))
            print(f"  {a['asset']}: {free:.4f} = ${val:.2f}")
            log['actions'].append(f"检测到{a['asset']}: {free:.4f}")
    
    # Step 2: 变现决策
    total_convertible = sum(a[3] for a in assets_to_convert)
    print(f"\n可变现总额: ${total_convertible:.2f}")
    
    if total_convertible > 100:
        print("\n[Step 2] 执行变现操作...")
        for asset, qty, price, val in assets_to_convert:
            if val > 10:  # 只变现大于$10的
                print(f"  卖出 {asset}...")
                # 全仓逐仓卖出
                params = {
                    'asset': asset,
                    'symbol': f'{asset}USDT',
                    'amount': str(qty),
                    'type': 'SELL'
                }
                try:
                    result = api_post('https://api.binance.com', '/sapi/v1/margin/order', params)
                    if 'symbol' in result:
                        print(f"    ✅ 成功卖出 {asset}")
                        log['actions'].append(f"卖出{asset}: {qty}")
                    else:
                        print(f"    ❌ 失败: {result.get('msg', result)}")
                        log['actions'].append(f"卖出{asset}失败")
                except Exception as e:
                    print(f"    ❌ 错误: {e}")
    else:
        print("  资产不足,跳过变现")
    
    # Step 3: 检查交易信号
    print("\n[Step 3] 检查G20交易信号...")
    signals = []
    
    for coin, params in PARAMS.items():
        prices = get_klines(f'{coin}USDT', 100)
        if len(prices) < 50: continue
        
        rsi = calc_rsi(prices)
        
        if rsi < params['rsi_buy']:
            signal = 'BUY'
        elif rsi > params['rsi_sell']:
            signal = 'SELL'
        else:
            signal = 'HOLD'
        
        signals.append({'coin': coin, 'rsi': rsi, 'signal': signal, 'params': params})
        
        emoji = '🟢' if signal == 'BUY' else '🔴' if signal == 'SELL' else '🟡'
        print(f"  {emoji} {coin}: RSI={rsi:.1f}, Signal={signal}")
    
    log['signals'] = signals
    
    # Step 4: 获取可用USDT
    print("\n[Step 4] 检查可用资金...")
    spot = api_get('https://api.binance.com', '/api/v3/account')
    usdt_balance = 0
    for b in spot.get('balances', []):
        if b['asset'] == 'USDT':
            usdt_balance = float(b['free'])
            print(f"  现货USDT: ${usdt_balance:.2f}")
    
    fut_bal = api_get('https://fapi.binance.com', '/fapi/v2/balance')
    fut_usdt = 0
    for b in fut_bal:
        if b['asset'] in ['USDT', 'FDUSD']:
            fut_usdt += float(b.get('availableBalance', 0))
    print(f"  合约USDT: ${fut_usdt:.2f}")
    print(f"  总可用: ${usdt_balance + fut_usdt:.2f}")
    
    log['balance'] = {'spot': usdt_balance, 'futures': fut_usdt}
    
    # Step 5: 执行交易
    print("\n[Step 5] 交易决策...")
    buy_signals = [s for s in signals if s['signal'] == 'BUY']
    
    if buy_signals and usdt_balance + fut_usdt > 10:
        total_capital = usdt_balance + fut_usdt
        per_coin = total_capital / len(buy_signals) * 0.95  # 保留5%备用
        
        print(f"  买入信号: {[s['coin'] for s in buy_signals]}")
        print(f"  每币分配: ${per_coin:.2f}")
        
        for sig in buy_signals:
            coin = sig['coin']
            qty = per_coin / get_price(f'{coin}USDT')
            print(f"  尝试买入 {coin}: {qty:.4f}")
            log['actions'].append(f"尝试买入{coin}: {qty:.4f}")
    else:
        print("  无买入信号或资金不足")
    
    # 保存日志
    with open('/home/goose/.openclaw/workspace/logs/g20_enhanced_log.json', 'w') as f:
        json.dump(log, f, indent=2)
    
    print("\n" + "=" * 70)
    print("执行完成")
    print("=" * 70)

if __name__ == '__main__':
    main()
