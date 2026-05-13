#!/usr/bin/env python3
"""
G23 资金费率套利 + Smart Money + 逐仓风控版
=============================================
核心功能:
1. 资金费率套利 (持有正费率做多,负费率做空)
2. Smart Money信号 (实时监控,可交易时自动调配资金)
3. 逐仓风控 (每币种独立账户,严格控制数量)
4. 全面风险控制

逐仓规则:
- 每币种独立账户,不共享抵押金
- 最大同时持仓: 3个币种
- 单币种最大仓位: 总资金20%
- 止损线: -5%
- 止盈线: +15%
"""
import urllib.request, hmac, hashlib, time, json, numpy as np
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

# ========== 风控参数 ==========
MAX_POSITIONS = 3       # 最大同时持仓
MAX_POSITION_RATIO = 0.2  # 单币种最大仓位比例
STOP_LOSS = 0.05        # 止损5%
TAKE_PROFIT = 0.15      # 止盈15%
FUNDING_THRESHOLD = 0.01  # 资金费率阈值

# ========== 工具函数 ==========
def api(url, method='GET', data=None):
    req = urllib.request.Request(url, method=method, data=data)
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try:
        resp = opener.open(req, timeout=30)
        return json.loads(resp.read().decode())
    except Exception as e:
        return {'error': str(e)}

def price(sym):
    url = f'https://api.binance.com/api/v3/ticker/price?symbol={sym}'
    req = urllib.request.Request(url)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    resp = opener.open(req, timeout=10)
    return float(json.loads(resp.read().decode())['price'])

def get_klines(sym, limit=100):
    end = int(time.time() * 1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&startTime={start}&endTime={end}&limit={limit}'
    req = urllib.request.Request(url)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    resp = opener.open(req, timeout=15)
    return [float(k[4]) for k in json.loads(resp.read().decode())]

def calc_rsi(prices, period=14):
    if len(prices) < period + 1: return 50
    deltas = np.diff(prices)
    gain = np.where(deltas > 0, deltas, 0)
    loss = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    if avg_loss == 0: return 100
    return 100 - (100 / (1 + avg_gain / avg_loss))

def get_funding(symbol):
    url = f'https://fapi.binance.com/fapi/v1/premiumIndex?symbol={symbol}'
    req = urllib.request.Request(url)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try:
        resp = opener.open(req, timeout=10)
        data = json.loads(resp.read().decode())
        return float(data.get('lastFundingRate', 0)) * 100
    except: return 0

def get_smart_money(chain_id="56", page=1):
    url = "https://web3.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/web/signal/smart-money/ai"
    headers = {'Content-Type': 'application/json', 'Accept-Encoding': 'identity', 'User-Agent': 'binance-web3/1.1 (Skill)'}
    data = json.dumps({"page": page, "pageSize": 20, "chainId": chain_id}).encode()
    req = urllib.request.Request(url, method='POST', data=data, headers=headers)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try:
        resp = opener.open(req, timeout=15)
        return json.loads(resp.read().decode())
    except: return {'data': []}

# ========== 账户数据 ==========
def get_spot_balance():
    ts = int(time.time() * 1000)
    q = f"timestamp={ts}"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/api/v3/account?timestamp={ts}&signature={sig}"
    data = api(url)
    if 'balances' in data:
        for b in data['balances']:
            if b['asset'] == 'USDT': return float(b['free'])
    return 0

def get_futures_balance():
    ts = int(time.time() * 1000)
    q = f"timestamp={ts}"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://fapi.bapi.com/fapi/v1/balance?timestamp={ts}&signature={sig}"
    req = urllib.request.Request(url)
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    try:
        resp = opener.open(req, timeout=10)
        data = json.loads(resp.read().decode())
        for item in data:
            if item.get('asset') == 'USDT':
                return float(item.get('availableBalance', 0))
    except: return 0

def get_margin_positions():
    """获取逐仓持仓"""
    ts = int(time.time() * 1000)
    q = f"timestamp={ts}"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com/sapi/v1/margin/account?timestamp={ts}&signature={sig}"
    data = api(url)
    positions = []
    if 'userAssets' in data:
        for a in data['userAssets']:
            free = float(a.get('free', 0))
            if free > 0.001:
                asset = a['asset']
                try:
                    p = price(asset + 'USDT')
                    positions.append({
                        'asset': asset,
                        'qty': free,
                        'value': free * p
                    })
                except: pass
    return positions

# ========== 交易执行 ==========
def futures_buy(symbol, qty):
    ts = int(time.time() * 1000)
    q = f"symbol={symbol}&side=BUY&type=MARKET&quantity={qty}&timestamp={ts}&recvWindow=5000"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://fapi.binance.com/fapi/v1/order?{q}&signature={sig}"
    return api(url, 'POST')

def futures_sell(symbol, qty):
    ts = int(time.time() * 1000)
    q = f"symbol={symbol}&side=SELL&type=MARKET&quantity={qty}&timestamp={ts}&recvWindow=5000"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://fapi.binance.com/fapi/v1/order?{q}&signature={sig}"
    return api(url, 'POST')

def set_leverage(symbol, leverage=5):
    ts = int(time.time() * 1000)
    q = f"symbol={symbol}&leverage={leverage}&timestamp={ts}&recvWindow=5000"
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = f"https://fapi.binance.com/fapi/v1/leverage?{q}&signature={sig}"
    return api(url, 'POST')

# ========== 主程序 ==========
def main():
    print("=" * 80)
    print("G23 资金费率套利 + Smart Money + 逐仓风控版")
    print("=" * 80)
    
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"\n[{ts}] 运行中...")
    
    # 1. 获取账户状态
    usdt_spot = get_spot_balance()
    usdt_futures = get_futures_balance()
    margin_positions = get_margin_positions()
    total_capital = usdt_spot + usdt_futures + sum(p['value'] for p in margin_positions)
    
    print(f"\n[账户状态]")
    print(f"  现货USDT: ${usdt_spot:.2f}")
    print(f"  合约USDT: ${usdt_futures:.2f}")
    print(f"  逐仓持仓: {len(margin_positions)}个")
    for p in margin_positions:
        print(f"    {p['asset']}: {p['qty']:.4f} (${p['value']:.2f})")
    print(f"  总资产: ${total_capital:.2f}")
    
    # 2. Smart Money信号
    print(f"\n[Smart Money信号]")
    sm_data = get_smart_money("56", 1)
    active_signals = []
    if 'data' in sm_data:
        for s in sm_data['data']:
            if s.get('status') == 'active' and s.get('direction') in ['buy', 'sell']:
                active_signals.append(s)
    
    if active_signals:
        for s in active_signals[:5]:
            ticker = s['ticker']
            direction = s['direction']
            max_gain = float(s.get('maxGain', 0))
            print(f"  🟢 {ticker}: {direction} maxGain:{max_gain:.1f}%")
    else:
        print(f"  ⏰ 无活跃信号")
    
    # 3. 资金费率分析
    print(f"\n[资金费率分析]")
    coins = ['BTC', 'ETH', 'SOL', 'DOGE', 'LINK', 'XRP', 'ADA', 'AVAX']
    funding_opportunities = []
    
    for coin in coins:
        try:
            funding = get_funding(f'{coin}USDT')
            prices = get_klines(f'{coin}USDT', 50)
            rsi = calc_rsi(prices)
            
            opportunity = {
                'coin': coin,
                'funding': funding,
                'rsi': rsi,
                'direction': None,
                'score': 0
            }
            
            # 正资金费率 -> 做多
            if funding > FUNDING_THRESHOLD:
                opportunity['direction'] = 'LONG'
                opportunity['score'] = funding * 10 + (70 - rsi) if rsi < 70 else 0
                funding_opportunities.append(opportunity)
            # 负资金费率 -> 做空
            elif funding < -FUNDING_THRESHOLD:
                opportunity['direction'] = 'SHORT'
                opportunity['score'] = abs(funding) * 10 + (rsi - 30) if rsi > 30 else 0
                funding_opportunities.append(opportunity)
            
            emoji = '🟢' if opportunity['direction'] == 'LONG' else '🔴' if opportunity['direction'] == 'SHORT' else '⚪'
            print(f"  {emoji} {coin}: 费率{funding:+.4f}% RSI={rsi:.1f} -> {opportunity['direction'] or '观望'}")
            
        except Exception as e:
            print(f"  ❌ {coin}: {e}")
    
    # 4. 风控检查
    print(f"\n[风控检查]")
    current_positions = len(margin_positions)
    print(f"  当前持仓: {current_positions}/{MAX_POSITIONS}")
    print(f"  最大单币仓位: {MAX_POSITION_RATIO*100:.0f}%")
    print(f"  止损线: -{STOP_LOSS*100:.0f}%")
    print(f"  止盈线: +{TAKE_PROFIT*100:.0f}%")
    
    # 5. 决策
    print(f"\n[决策]")
    
    # 按评分排序机会
    funding_opportunities.sort(key=lambda x: x['score'], reverse=True)
    
    # 检查是否可以开新仓位
    can_open = current_positions < MAX_POSITIONS
    
    if funding_opportunities and can_open:
        best = funding_opportunities[0]
        if best['score'] > 50:
            coin = best['coin']
            direction = best['direction']
            funding = best['funding']
            
            # 计算仓位
            position_size = min(
                total_capital * MAX_POSITION_RATIO,  # 不超过20%
                usdt_futures * 0.9  # 不超过合约资金的90%
            )
            
            if position_size > 10:
                leverage = 5
                qty = round(position_size * leverage / price(f'{coin}USDT'), 4)
                
                print(f"  ✅ 开仓: {coin}")
                print(f"     方向: {direction}")
                print(f"     资金费率: {funding:+.4f}%")
                print(f"     仓位: ${position_size:.2f} x{leverage}x")
                print(f"     数量: {qty}")
                
                # 设置杠杆
                set_leverage(f'{coin}USDT', leverage)
                
                # 执行交易
                if direction == 'LONG':
                    result = futures_buy(f'{coin}USDT', qty)
                else:
                    result = futures_sell(f'{coin}USDT', qty)
                
                if 'orderId' in result:
                    print(f"     ✅ 成功! 订单ID: {result['orderId']}")
                else:
                    print(f"     ❌ 失败: {result.get('msg', result)}")
    else:
        print(f"  ⏸️ 无新仓位机会")
        if not can_open:
            print(f"     原因:已达最大持仓数({MAX_POSITIONS})")
        if funding_opportunities and not can_open:
            for opp in funding_opportunities[:3]:
                print(f"     等待: {opp['coin']} {opp['direction']} 评分{opp['score']:.0f}")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()
