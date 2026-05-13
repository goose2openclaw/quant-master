#!/usr/bin/env python3
"""
G19.2 - Trading Systems增强版
1. 多时间框架分析 (1h + 4h + 1d)
2. 动态风控增强 (波动率调整)
3. 事件驱动信号 (RSI + MACD确认)
"""
import requests, numpy as np, time, json
from datetime import datetime

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

def get_klines(sym, interval='1h', limit=720):
    end = int(time.time()*1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval={interval}&startTime={start}&endTime={end}&limit={limit}'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=15)
        return [float(k[4]) for k in r.json()]
    except: return []

def calc_rsi(prices, period=14):
    if len(prices) < period + 1: return 50
    deltas = np.diff(prices)
    gain = np.where(deltas > 0, deltas, 0)
    loss = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    if avg_loss == 0: return 100
    return 100 - (100 / (1 + avg_gain / avg_loss))

def calc_macd(prices, fast=12, slow=26, signal=9):
    if len(prices) < slow: return 0, 0
    ema_fast = np.mean(prices[-fast:])
    ema_slow = np.mean(prices[-slow:])
    macd = ema_fast - ema_slow
    return macd, 0  # 简化

def calc_volatility(prices, period=20):
    if len(prices) < period: return 0.05
    returns = np.diff(prices[-period:]) / prices[-period:-1]
    return np.std(returns)

def calc_trend(prices, period=20):
    if len(prices) < period: return 0
    ma20 = np.mean(prices[-20:])
    ma50 = np.mean(prices[-50:]) if len(prices) >= 50 else ma20
    return (ma20 - ma50) / ma50 * 100

class G19_2:
    def __init__(self, coin):
        self.coin = coin
        self.params = G19_PARAMS.get(coin, DEFAULT_PARAMS)
        
    def get_multi_tf_data(self):
        """获取多时间框架数据"""
        sym = f'{self.coin}USDT'
        return {
            '1h': get_klines(sym, '1h', 100),
            '4h': get_klines(sym, '4h', 100),
            '1d': get_klines(sym, '1d', 30)
        }
    
    def analyze(self, data):
        """多时间框架分析"""
        results = {}
        
        for tf, prices in data.items():
            if len(prices) < 30:
                results[tf] = {'rsi': 50, 'macd': 0, 'trend': 0, 'vol': 0.05}
                continue
                
            rsi = calc_rsi(prices)
            macd, _ = calc_macd(prices)
            trend = calc_trend(prices)
            vol = calc_volatility(prices)
            
            results[tf] = {
                'rsi': rsi,
                'macd': macd,
                'trend': trend,
                'vol': vol,
                'signal': 'BUY' if rsi < self.params['rsi_buy'] and macd > 0 else 
                         'SELL' if rsi > self.params['rsi_sell'] else 'HOLD'
            }
        
        return results
    
    def dynamic_risk(self, tf_data):
        """动态风控 - 根据波动率调整止盈止损"""
        base_tp = self.params['tp']
        base_sl = self.params['sl']
        
        # 计算综合波动率
        vol_1h = tf_data['1h']['vol']
        vol_4h = tf_data['4h']['vol']
        avg_vol = (vol_1h + vol_4h) / 2
        
        # 波动率调整因子
        vol_factor = min(2.0, max(0.5, avg_vol / 0.02))  # 基准2%波动
        
        # 动态调整
        dyn_tp = base_tp * vol_factor
        dyn_sl = base_sl * vol_factor
        
        # 趋势调整
        trend_1d = tf_data['1d']['trend']
        if trend_1d > 2:  # 强上升趋势
            dyn_tp *= 1.3  # 持有更久
            dyn_sl *= 0.8  # 宽止损
        elif trend_1d < -2:  # 下降趋势
            dyn_tp *= 0.7
            dyn_sl *= 1.2
        
        return {
            'tp': min(0.20, dyn_tp),  # 最大20%止盈
            'sl': max(0.01, dyn_sl),  # 最小1%止损
            'vol_factor': vol_factor
        }
    
    def generate_signal(self, tf_data, risk):
        """生成交易信号"""
        rsi_1h = tf_data['1h']['rsi']
        rsi_4h = tf_data['4h']['rsi']
        trend_1d = tf_data['1d']['trend']
        
        # 多时间框架确认
        confirm_4h = rsi_4h < self.params['rsi_buy'] if rsi_1h < self.params['rsi_buy'] else rsi_4h > self.params['rsi_sell']
        confirm_1d = trend_1d > 0
        
        # RSI信号
        if rsi_1h < self.params['rsi_buy']:
            if confirm_4h and confirm_1d:
                return 'STRONG_BUY', f"RSI确认(1h:{rsi_1h:.1f},4h:{rsi_4h:.1f})"
            return 'BUY', f"RSI超卖(1h:{rsi_1h:.1f})"
        elif rsi_1h > self.params['rsi_sell']:
            return 'SELL', f"RSI超买({rsi_1h:.1f})"
        else:
            return 'HOLD', f"中性(1h:{rsi_1h:.1f})"
    
    def run(self):
        """执行分析"""
        tf_data = self.get_multi_tf_data()
        analysis = self.analyze(tf_data)
        risk = self.dynamic_risk(analysis)
        signal, reason = self.generate_signal(analysis, risk)
        
        return {
            'coin': self.coin,
            'tf_data': analysis,
            'risk': risk,
            'signal': signal,
            'reason': reason
        }

# G19原始参数
G19_PARAMS = {
    'BTC': {'rsi_buy': 45, 'rsi_sell': 79, 'tp': 0.092, 'sl': 0.034},
    'ETH': {'rsi_buy': 29, 'rsi_sell': 79, 'tp': 0.054, 'sl': 0.042},
    'SOL': {'rsi_buy': 45, 'rsi_sell': 76, 'tp': 0.082, 'sl': 0.054},
    'XRP': {'rsi_buy': 24, 'rsi_sell': 77, 'tp': 0.17, 'sl': 0.048},
    'ADA': {'rsi_buy': 43, 'rsi_sell': 63, 'tp': 0.079, 'sl': 0.025},
    'DOGE': {'rsi_buy': 45, 'rsi_sell': 80, 'tp': 0.07, 'sl': 0.03},
    'LINK': {'rsi_buy': 44, 'rsi_sell': 77, 'tp': 0.06, 'sl': 0.045},
}
DEFAULT_PARAMS = {'rsi_buy': 45, 'rsi_sell': 75, 'tp': 0.08, 'sl': 0.035}

def backtest_g19_2(coin, prices_1h, prices_4h, prices_1d, params):
    """G19.2回测"""
    capital = 100
    position = None
    entry = 0
    trades = []
    
    min_len = min(len(prices_1h), len(prices_4h), len(prices_1d))
    
    for i in range(50, min_len - 1):
        # 获取多时间框架数据
        d_1h = prices_1h[:i+1]
        d_4h = prices_4h[:i+1]
        d_1d = prices_1d[:i+1]
        
        rsi_1h = calc_rsi(d_1h)
        rsi_4h = calc_rsi(d_4h)
        trend_1d = calc_trend(d_1d)
        vol = calc_volatility(d_1h)
        
        # 动态风控
        vol_factor = min(2.0, max(0.5, vol / 0.02))
        dyn_tp = params['tp'] * vol_factor
        dyn_sl = params['sl'] * vol_factor
        
        if trend_1d > 2:
            dyn_tp *= 1.3
            dyn_sl *= 0.8
        
        # 信号
        confirm_4h = rsi_4h < params['rsi_buy']
        confirm_1d = trend_1d > 0
        
        if position is None:
            if rsi_1h < params['rsi_buy'] and confirm_4h and confirm_1d:
                position = prices_1h[i]
                entry = prices_1h[i]
        else:
            pnl = (prices_1h[i] - entry) / entry
            if pnl >= dyn_tp or pnl <= -dyn_sl or rsi_1h > params['rsi_sell']:
                capital *= (1 + pnl)
                trades.append({'pnl': pnl*100, 'win': pnl > 0, 'tp': dyn_tp, 'sl': dyn_sl})
                position = None
    
    return {'capital': capital, 'trades': trades}

def main():
    print("=" * 70)
    print("G19.2 - Trading Systems增强版")
    print("=" * 70)
    
    COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']
    
    # 1. 多时间框架分析
    print("\n【多时间框架分析】")
    results = []
    for coin in COINS:
        g = G19_2(coin)
        result = g.run()
        results.append(result)
        
        tf = result['tf_data']
        risk = result['risk']
        
        emoji = '🟢' if 'BUY' in result['signal'] else '🔴' if 'SELL' in result['signal'] else '🟡'
        print(f"\n{emoji} {coin} ({result['signal']})")
        print(f"   1h: RSI={tf['1h']['rsi']:.1f}, MACD={tf['1h']['macd']:.4f}")
        print(f"   4h: RSI={tf['4h']['rsi']:.1f}, Trend={tf['4h']['trend']:.2f}%")
        print(f"   1d: RSI={tf['1d']['rsi']:.1f}, Trend={tf['1d']['trend']:.2f}%")
        print(f"   动态风险: TP={risk['tp']*100:.1f}%, SL={risk['sl']*100:.1f}%, VF={risk['vol_factor']:.2f}")
        print(f"   原因: {result['reason']}")
    
    # 2. 回测对比
    print("\n" + "=" * 70)
    print("【G19 vs G19.2 回测对比】")
    print("币种       G19收益      G19.2收益     改进")
    print("-" * 50)
    
    g19_total = g192_total = 0
    
    for coin in COINS:
        params = G19_PARAMS.get(coin, DEFAULT_PARAMS)
        
        p1h = get_klines(f'{coin}USDT', '1h', 720)
        p4h = get_klines(f'{coin}USDT', '4h', 180)
        p1d = get_klines(f'{coin}USDT', '1d', 30)
        
        if len(p1h) < 500 or len(p4h) < 100 or len(p1d) < 20:
            continue
        
        # G19
        g19_cap = 100
        pos = None
        entry = 0
        for i in range(50, len(p1h)-1):
            rsi = calc_rsi(p1h[:i+1])
            if pos is None:
                if rsi < params['rsi_buy']:
                    pos = p1h[i]
                    entry = p1h[i]
            else:
                pnl = (p1h[i] - entry) / entry
                if pnl >= params['tp'] or pnl <= -params['sl'] or rsi > params['rsi_sell']:
                    g19_cap *= (1 + pnl)
                    pos = None
        g19_ret = g19_cap - 100
        
        # G19.2
        g192 = backtest_g19_2(coin, p1h, p4h, p1d, params)
        g192_ret = g192['capital'] - 100
        
        g19_total += g19_ret
        g192_total += g192_ret
        
        improvement = g192_ret - g19_ret
        emoji = "✅" if improvement > 0 else "⚠️"
        print(f"{coin:<8} {g19_ret:>+6.1f}%      {g192_ret:>+6.1f}%      {emoji}{improvement:+.1f}%")
    
    print("-" * 50)
    print(f"{'平均':<8} {g19_total/7:>+6.1f}%      {g192_total/7:>+6.1f}%")
    
    # 保存结果
    output = {
        'timestamp': datetime.now().isoformat(),
        'signals': [{
            'coin': r['coin'],
            'signal': r['signal'],
            'reason': r['reason'],
            'risk': r['risk']
        } for r in results]
    }
    
    with open('/home/goose/.openclaw/workspace/logs/g19_2_signals.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ 信号已保存")

if __name__ == '__main__':
    main()
