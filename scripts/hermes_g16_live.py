#!/usr/bin/env python3
"""
G16 v2.0 实盘交易系统
支持FDUSD和USDT双账户
"""
import requests, numpy as np, time, json, hmac, hashlib
from datetime import datetime

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'

COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']
CONFIG = {
    'rsi_buy': 35, 'rsi_sell': 65,
    'bb_buy': 30, 'bb_sell': 70,
    'tp': 0.12, 'sl': 0.04,
    'position': 0.35, 'leverage': 5
}

def get_klines(sym, limit=200):
    end = int(time.time()*1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&startTime={start}&endTime={end}&limit={limit}'
    r = requests.get(url, proxies=PROXIES, timeout=15)
    return [{'close':float(k[4])} for k in r.json()]

def calc_rsi(prices):
    deltas = np.diff(prices)
    gain = np.where(deltas>0, deltas, 0)
    loss = np.where(deltas<0, -deltas, 0)
    avg_gain = np.mean(gain[-7:])
    avg_loss = np.mean(loss[-7:])
    return 100-(100/(1+avg_gain/avg_loss)) if avg_loss!=0 else 50

def calc_bb(closes):
    std = np.std(closes[-20:])
    mean = np.mean(closes[-20:])
    upper, lower = mean + 2*std, mean - 2*std
    pos = (closes[-1] - lower) / (upper - lower) * 100 if upper > lower else 50
    ratio = std / mean * 100 if mean > 0 else 0
    return pos, ratio

def get_balance():
    """获取所有合约账户余额"""
    balances = {}
    for asset in ['USDT', 'FDUSD']:
        try:
            url = f'https://fapi.binance.com/fapi/v2/balance'
            params = {'asset': asset, 'timestamp': int(time.time()*1000)}
            query = f"asset={asset}&timestamp={params['timestamp']}"
            sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
            params['signature'] = sig
            r = requests.get(url, params=params, headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
            for item in r.json():
                if item['asset'] == asset:
                    balances[asset] = {
                        'available': float(item['availableBalance']),
                        'balance': float(item['balance'])
                    }
        except:
            pass
    return balances

def get_positions():
    """获取所有持仓"""
    try:
        url = 'https://fapi.binance.com/fapi/v2/positionRisk'
        params = {'timestamp': int(time.time()*1000)}
        query = f"timestamp={params['timestamp']}"
        sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
        params['signature'] = sig
        r = requests.get(url, params=params, headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
        return {p['symbol']: float(p['positionAmt']) for p in r.json() if float(p['positionAmt']) != 0}
    except:
        return {}

def generate_signal(coin):
    try:
        klines = get_klines(f'{coin}USDT', 200)
        closes = [k['close'] for k in klines]
        if len(closes) < 50: return None
        rsi = calc_rsi(closes)
        bb_pos, ratio = calc_bb(closes)
        if ratio < 0.35:
            if rsi < CONFIG['rsi_buy'] and bb_pos < CONFIG['bb_buy']:
                return {'type': 'LONG', 'coin': coin, 'rsi': rsi, 'bb': bb_pos, 'price': closes[-1]}
            elif rsi > CONFIG['rsi_sell'] and bb_pos >= CONFIG['bb_sell']:
                return {'type': 'SHORT', 'coin': coin, 'rsi': rsi, 'bb': bb_pos, 'price': closes[-1]}
        return None
    except:
        return None

def main():
    print("=" * 60)
    print("G16 v2.0 实盘交易系统")
    print("=" * 60)
    print(f"配置: RSI {CONFIG['rsi_buy']}/{CONFIG['rsi_sell']} TP {CONFIG['tp']*100:.0f}%")
    print(f"仓位: {CONFIG['position']*100:.0f}% | 杠杆: {CONFIG['leverage']}x")
    print("=" * 60)
    
    # 获取余额
    balances = get_balance()
    print("\n账户余额:")
    total = 0
    for asset, data in balances.items():
        print(f"  {asset}: ${data['available']:.2f} (余额: ${data['balance']:.2f})")
        total += data['available']
    print(f"  总计: ${total:.2f}")
    
    if total < 5:
        print("\n⚠️ 余额不足,无法开仓")
        return []
    
    # 获取持仓
    positions = get_positions()
    print(f"\n当前持仓: {positions if positions else '无'}")
    
    # 扫描信号
    print("\n扫描信号:")
    signals = []
    for c in COINS:
        sig = generate_signal(c)
        if sig:
            signals.append(sig)
            print(f"  📊 {sig['type']} {c} @ ${sig['price']:.2f} (RSI:{sig['rsi']:.1f} BB:{sig['bb']:.0f}%)")
    
    if not signals:
        print("  ⏸️ 无高置信度信号")
    
    return signals

if __name__ == '__main__':
    main()
