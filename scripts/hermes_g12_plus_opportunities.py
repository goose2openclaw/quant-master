#!/usr/bin/env python3
"""
G12+ 机会策略系统
集成: 资金费率套利 | 相关性统计 | 动能排名 | 布林收口 | Polymarket联动
"""
import requests, time, numpy as np
from datetime import datetime

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

# ========== 机会1: 资金费率套利 ==========
def opportunity_funding_arbitrage():
    """资金费率套利 - 做多负费率,做空正费率"""
    print("\n【策略1: 资金费率套利】")
    
    results = []
    for c in ['BTC','ETH','SOL']:
        try:
            url = f'https://fapi.binance.com/fapi/v1/premiumIndex?symbol={c}USDT'
            r = requests.get(url, proxies=PROXIES, timeout=5)
            rate = float(r.json().get('lastFundingRate', 0)) * 100
            results.append({'coin': c, 'rate': rate, 'action': '做多' if rate < 0 else '做空'})
            time.sleep(0.1)
        except: pass
    
    if results:
        # 按费率绝对值排序
        results.sort(key=lambda x: -abs(x['rate']))
        for r in results[:3]:
            emoji = "🟢" if abs(r['rate']) > 0.01 else "⚪"
            print(f"  {emoji} {r['coin']}: {r['rate']:+.4f}% → {r['action']}")
            if abs(r['rate']) > 0.02:
                print(f"    ⚡ 高费率! 预计收益: {r['rate']*3*4:.2f}%/日 (8次结算)")
    return results

# ========== 机会2: 相关性统计套利 ==========
def opportunity_correlation_arbitrage():
    """基于币种相关性统计套利"""
    print("\n【策略2: 相关性统计套利】")
    
    prices = {}
    for c in ['BTC','ETH','SOL']:
        end = int(time.time()*1000)
        start = end - 168 * 3600 * 1000
        url = f'https://api.binance.com/api/v3/klines?symbol={c}USDT&interval=1h&startTime={start}&endTime={end}&limit=168'
        try:
            r = requests.get(url, proxies=PROXIES, timeout=15)
            prices[c] = [float(k[4]) for k in r.json()]
        except: pass
        time.sleep(0.1)
    
    if len(prices) >= 2:
        btc = np.array(prices['BTC'])
        
        # 计算24小时价格变动差异
        signals = []
        for c in ['ETH','SOL']:
            if c in prices and len(prices[c]) >= 25:
                # 计算相关性
                if len(prices[c]) == len(btc):
                    corr = np.corrcoef(btc, np.array(prices[c]))[0,1]
                    
                    # 计算24h变动差异
                    chg_btc = (btc[-1] - btc[-25]) / btc[-25] * 100
                    chg_c = (prices[c][-1] - prices[c][-25]) / prices[c][-25] * 100
                    spread = chg_c - chg_btc
                    
                    signals.append({
                        'coin': c,
                        'corr': corr,
                        'spread': spread,
                        'chg_c': chg_c,
                        'chg_btc': chg_btc
                    })
        
        # 按spread排序
        signals.sort(key=lambda x: -abs(x['spread']))
        
        for s in signals[:3]:
            emoji = "🟢" if abs(s['spread']) > 1 else "🟡"
            print(f"  {emoji} {s['coin']}: 相关={s['corr']:.2f} spread={s['spread']:+.2f}%")
            if abs(s['spread']) > 2:
                action = "配对做空" if s['spread'] > 0 else "配对做多"
                print(f"    ⚡ {action} {s['coin']} vs BTC, 预计收益: {abs(s['spread'])*0.5:.1f}%")
    return signals

# ========== 机会3: 动能排名轮动 ==========
def opportunity_momentum_rotation():
    """动能排名轮动策略"""
    print("\n【策略3: 动能排名轮动】")
    
    momenta = []
    for c in COINS:
        end = int(time.time()*1000)
        start = end - 168 * 3600 * 1000
        url = f'https://api.binance.com/api/v3/klines?symbol={c}USDT&interval=1h&startTime={start}&endTime={end}&limit=168'
        try:
            r = requests.get(url, proxies=PROXIES, timeout=10)
            data = [float(k[4]) for k in r.json()]
            if len(data) >= 50:
                chg_7d = (data[-1] - data[-1]) / data[-1] * 100
                chg_24h = (data[-1] - data[-25]) / data[-25] * 100 if len(data) >= 25 else 0
                chg_1h = (data[-1] - data[-2]) / data[-2] * 100 if len(data) >= 2 else 0
                # 综合动能评分
                score = chg_24h * 0.6 + chg_7d * 0.3 + chg_1h * 0.1
                momenta.append({
                    'coin': c, 'score': score,
                    '24h': chg_24h, '7d': chg_7d
                })
        except: pass
        time.sleep(0.1)
    
    if momenta:
        momenta.sort(key=lambda x: -x['score'])
        print(f"  动能排名:")
        for i, m in enumerate(momenta[:5], 1):
            emoji = "🟢" if m['score'] > 0 else "🔴"
            print(f"    {i}. {emoji} {m['coin']}: {m['24h']:+.2f}%/24h 动能:{m['score']:+.2f}")
        
        # 弱势币换成强势币
        if len(momenta) >= 2:
            weakest = momenta[-1]
            strongest = momenta[0]
            if weakest['score'] < -2 and strongest['score'] > 2:
                print(f"  ⚡ 轮动信号: {weakest['coin']} → {strongest['coin']}")
                print(f"     预计收益: {strongest['24h'] - weakest['24h']:.2f}%")
    return momenta

# ========== 机会4: 布林带收口突破 ==========
def opportunity_bb_squeeze():
    """布林带收口突破预判"""
    print("\n【策略4: 布林带收口突破预判】")
    
    signals = []
    for c in ['BTC','ETH','SOL']:
        end = int(time.time()*1000)
        start = end - 200 * 3600 * 1000
        url = f'https://api.binance.com/api/v3/klines?symbol={c}USDT&interval=1h&startTime={start}&endTime={end}&limit=200'
        try:
            r = requests.get(url, proxies=PROXIES, timeout=15)
            closes = np.array([float(k[4]) for k in r.json()])
            
            # 当前布林宽度 vs 历史平均
            bb_now = np.std(closes[-20:]) / np.mean(closes[-20:]) * 100
            bb_hist = np.std(closes) / np.mean(closes) * 100
            
            ratio = bb_now / bb_hist if bb_hist > 0 else 1
            
            signals.append({
                'coin': c,
                'bb_now': bb_now,
                'bb_hist': bb_hist,
                'ratio': ratio
            })
        except: pass
        time.sleep(0.1)
    
    if signals:
        for s in signals:
            emoji = "🔴" if s['ratio'] < 0.4 else ("🟡" if s['ratio'] < 0.6 else "🟢")
            print(f"  {emoji} {s['coin']}: 布林宽度{s['bb_now']:.2f}% vs 历史{s['bb_hist']:.2f}% (比{s['ratio']:.2f}x)")
            
            if s['ratio'] < 0.4:
                print(f"    ⚡ 极端收口! 预计突破幅度: {s['bb_hist']*2:.1f}%")
    return signals

# ========== 机会5: Polymarket联动 ==========
def opportunity_polymarket():
    """Polymarket预测市场联动"""
    print("\n【策略5: Polymarket联动】")
    
    try:
        r = requests.get('https://clob.polymarket.com/markets?limit=10', proxies=PROXIES, timeout=10)
        data = r.json()
        
        keywords = {
            'BTC': ['bitcoin', 'btc', 'crypto'],
            'ETH': ['ethereum', 'eth', 'defi', 'ether'],
            'SOL': ['solana', 'sol'],
            'XRP': ['ripple', 'xrp'],
        }
        
        correlations = {c: 0 for c in keywords}
        
        for m in data.get('data', [])[:10]:
            q = m.get('question', '').lower()
            prices = m.get('outcomePrices', {})
            prob = float(list(prices.values())[0]) * 100 if prices else 50
            vol = float(m.get('volume', 0))
            
            for c, kws in keywords.items():
                for kw in kws:
                    if kw in q:
                        correlations[c] += prob * vol / 10000
                        break
        
        if correlations:
            sorted_corr = sorted(correlations.items(), key=lambda x: -x[1])
            print("  Polymarket热度排名:")
            for c, score in sorted_corr[:5]:
                emoji = "🟢" if score > 50 else ("🟡" if score > 10 else "⚪")
                print(f"    {emoji} {c}: 热度{score:.1f}")
        return correlations
    except Exception as e:
        print(f"  ⚠️ Polymarket连接失败: {e}")
        return {}

# ========== 主程序 ==========
def main():
    print("="*70)
    print("G12+ 机会策略系统")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # 执行各策略
    opp1 = opportunity_funding_arbitrage()
    opp2 = opportunity_correlation_arbitrage()
    opp3 = opportunity_momentum_rotation()
    opp4 = opportunity_bb_squeeze()
    opp5 = opportunity_polymarket()
    
    # 综合评分
    print("\n" + "="*70)
    print("【G12+ 综合机会评分】")
    print("="*70)
    
    # 汇总各策略信号
    signals = []
    
    if opp1:
        for r in opp1:
            if abs(r.get('rate', 0)) > 0.01:
                signals.append({
                    'type': '资金费率',
                    'coin': r['coin'],
                    'action': r['action'],
                    'score': abs(r['rate']) * 100,
                    'expected': abs(r['rate']) * 3 * 4  # 每日4次结算
                })
    
    if opp2:
        for s in opp2:
            if abs(s.get('spread', 0)) > 1:
                signals.append({
                    'type': '相关性套利',
                    'coin': s['coin'],
                    'action': '做空' if s['spread'] > 0 else '做多',
                    'score': abs(s['spread']) * 10,
                    'expected': abs(s['spread']) * 0.5
                })
    
    if opp3:
        if len(opp3) >= 2:
            weakest = opp3[-1]
            strongest = opp3[0]
            if weakest['score'] < -2 and strongest['score'] > 2:
                signals.append({
                    'type': '动能轮动',
                    'coin': f"{weakest['coin']}→{strongest['coin']}",
                    'action': '换仓',
                    'score': strongest['score'] - weakest['score'],
                    'expected': abs(strongest['24h'] - weakest['24h']) * 0.3
                })
    
    if opp4:
        for s in opp4:
            if s['ratio'] < 0.4:
                signals.append({
                    'type': '布林突破',
                    'coin': s['coin'],
                    'action': '观望突破方向',
                    'score': (1 - s['ratio']) * 50,
                    'expected': s['bb_hist'] * 2
                })
    
    # 按分数排序
    signals.sort(key=lambda x: -x['score'])
    
    print("\n机会排名:")
    for i, s in enumerate(signals[:5], 1):
        print(f"  {i}. {s['type']}: {s['coin']} {s['action']}")
        print(f"     评分: {s['score']:.1f} | 预期收益: {s['expected']:.2f}%")
    
    if not signals:
        print("  🟡 暂无高置信度信号")
    
    print("\n" + "="*70)
    print("✅ G12+ 机会扫描完成")
    print("="*70)
    
    return signals

if __name__ == '__main__':
    main()
