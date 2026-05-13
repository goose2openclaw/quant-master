#!/usr/bin/env python3
"""G16信号扫描"""
import requests, numpy as np, time

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'

CONFIG = {'rsi_buy':35,'rsi_sell':65,'bb_buy':30,'bb_sell':70,'tp':0.12,'sl':0.04,'position':0.35,'leverage':5}

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

COINS = ['DOGE','XRP','ADA','SOL','ETH','BTC']

print("=" * 55)
print("G16 v2.0 信号扫描")
print("=" * 55)

for c in COINS:
    try:
        klines = get_klines(f'{c}USDT', 200)
        closes = [k['close'] for k in klines]
        rsi = calc_rsi(closes)
        bb_pos, ratio = calc_bb(closes)
        
        signal = ""
        if ratio < 0.35:
            if rsi < 35 and bb_pos < 30:
                signal = "📈 LONG"
            elif rsi > 65 and bb_pos >= 70:
                signal = "📉 SHORT"
        
        status = "✅" if signal else "⏸️"
        print(f"{status} {c:5} RSI:{rsi:5.1f} BB:{bb_pos:5.0f}% 波动:{ratio:4.2f}% {signal}")
    except Exception as e:
        print(f"❌ {c} 失败: {e}")

print("=" * 55)
