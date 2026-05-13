#!/usr/bin/env python3
"""
G19 Live - 实盘交易版本
修复账户连接问题,支持现货+全仓
"""
import requests, hmac, hashlib, time

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']
PARAMS = {
    'BTC': {'rsi_buy': 45, 'rsi_sell': 79, 'tp': 0.092, 'sl': 0.034},
    'ETH': {'rsi_buy': 29, 'rsi_sell': 79, 'tp': 0.054, 'sl': 0.042},
    'SOL': {'rsi_buy': 45, 'rsi_sell': 76, 'tp': 0.082, 'sl': 0.054},
    'XRP': {'rsi_buy': 24, 'rsi_sell': 77, 'tp': 0.17, 'sl': 0.048},
    'ADA': {'rsi_buy': 43, 'rsi_sell': 63, 'tp': 0.079, 'sl': 0.025},
    'DOGE': {'rsi_buy': 45, 'rsi_sell': 80, 'tp': 0.07, 'sl': 0.03},
    'LINK': {'rsi_buy': 44, 'rsi_sell': 77, 'tp': 0.06, 'sl': 0.045},
}

def sign(params):
    params = dict(params)
    params['recvWindow'] = 5000
    params['timestamp'] = int(time.time()*1000)
    query = '&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    return query + '&signature=' + sig

def api_get(url, params=None):
    params = params or {}
    r = requests.get(url + '?' + sign(params), headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
    return r.json()

def api_post(url, params):
    r = requests.post(url + '?' + sign(params), headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
    return r.json()

def get_price(sym):
    try:
        r = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={sym}', proxies=PROXIES, timeout=5)
        return float(r.json()['price'])
    except: return 0

def get_klines(sym, limit=100):
    end = int(time.time()*1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&startTime={start}&endTime={end}&limit={limit}'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=15)
        return [float(k[4]) for k in r.json()]
    except: return []

def calc_rsi(prices, period=14):
    import numpy as np
    if len(prices) < period + 1: return 50
    deltas = np.diff(prices)
    gain = np.where(deltas > 0, deltas, 0)
    loss = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    if avg_loss == 0: return 100
    return 100 - (100 / (1 + avg_gain / avg_loss))

def get_account_summary():
    """获取所有账户概览"""
    total = 0
    summary = {}
    
    # 现货
    spot = api_get('https://api.binance.com/api/v3/account')
    if 'balances' in spot:
        for b in spot['balances']:
            free = float(b.get('free', 0))
            locked = float(b.get('locked', 0))
            if free + locked > 0.0001:
                asset = b['asset']
                price = get_price(asset + 'USDT') if asset != 'USDT' else 1.0
                val = (free + locked) * price
                summary[asset] = {'spot': free+locked, 'val': val}
                total += val
    
    # 全仓
    margin = api_get('https://api.binance.com/sapi/v1/margin/account')
    if 'totalAssetOfBtc' in margin:
        margin_btc = float(margin['totalAssetOfBtc'])
        margin_usd = margin_btc * get_price('BTCUSDT')
        summary['MARGIN'] = {'btc': margin_btc, 'usd': margin_usd}
        total += margin_usd
    
    return summary, total

def main():
    print("=" * 60)
    print("G19 Live - 实盘交易")
    print("=" * 60)
    
    # 账户概览
    summary, total = get_account_summary()
    print(f"\n💎 总资产: ${total:.2f}")
    
    # 现货持仓
    print("\n💰 现货持仓:")
    for asset, data in summary.items():
        if asset != 'MARGIN':
            print(f"  {asset}: {data['spot']:.6f} (≈${data['val']:.2f})")
    
    # 全仓
    if 'MARGIN' in summary:
        print(f"\n🏦 全仓: {summary['MARGIN']['btc']:.6f} BTC (≈${summary['MARGIN']['usd']:.2f})")
    
    # 信号分析
    print(f"\n🔍 G19信号:")
    signals = []
    for coin in COINS:
        prices = get_klines(f'{coin}USDT', 100)
        if len(prices) < 50: continue
        rsi = calc_rsi(prices)
        params = PARAMS.get(coin, PARAMS['BTC'])
        
        if rsi < params['rsi_buy']:
            signal = 'BUY'
        elif rsi > params['rsi_sell']:
            signal = 'SELL'
        else:
            signal = 'HOLD'
        
        signals.append({'coin': coin, 'rsi': rsi, 'signal': signal, 'params': params})
        emoji = '🟢' if signal == 'BUY' else '🔴' if signal == 'SELL' else '🟡'
        print(f"  {emoji} {coin:6} RSI:{rsi:5.1f} {signal}")
    
    # 买入信号处理
    buy_signals = [s for s in signals if s['signal'] == 'BUY']
    if buy_signals:
        print(f"\n🚀 买入信号: {[s['coin'] for s in buy_signals]}")
        for s in buy_signals:
            coin = s['coin']
            # 检查现货余额
            spot_bal = summary.get(coin, {}).get('spot', 0)
            if spot_bal > 0.001:
                qty = spot_bal * 0.3  # 30%转入全仓
                if qty > 0.0001:
                    result = api_post('https://api.binance.com/sapi/v1/margin/transfer', {
                        'asset': coin, 'type': 1, 'amount': f'{qty:.8f}'.rstrip('0').rstrip('.')
                    })
                    if 'tranId' in result:
                        print(f"  ✅ {coin}: 转入全仓 {qty:.6f}")
                    else:
                        print(f"  ❌ {coin}: {result.get('msg', result)}")
            else:
                print(f"  ⏸️ {coin}: 无现货持仓")
    else:
        print(f"\n⏸️ 无买入信号")

if __name__ == '__main__':
    main()
