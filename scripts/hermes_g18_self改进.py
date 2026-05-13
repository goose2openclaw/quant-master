#!/usr/bin/env python3
"""
G18 Self-Improving v1.0 - 自主迭代优化版
目标: 收益100%+
策略: Lean Framework + G16 Core + 自适应参数
"""
import requests, numpy as np, time, json, hmac, hashlib, random
from datetime import datetime
from collections import defaultdict

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'

COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']
LOG_FILE = '/home/goose/.openclaw/workspace/logs/g18_self.log'

# ========== 核心组件 ==========
def sign(params):
    params['recvWindow'] = 5000
    params['timestamp'] = int(time.time()*1000)
    query = '&'.join([f'{k}={v}' for k,v in sorted(params.items())])
    sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    return query + '&signature=' + sig

def api_get(url, params=None):
    try:
        params = params or {}
        r = requests.get(url + '?' + sign(params), headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except: return {}

def api_post(url, params):
    try:
        r = requests.post(url + '?' + sign(params), headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
        return r.json()
    except: return {'code': -1}

def get_price(symbol):
    try:
        r = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}', proxies=PROXIES, timeout=5)
        return float(r.json()['price'])
    except: return 0

def get_klines(sym, limit=720):
    end = int(time.time()*1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&startTime={start}&endTime={end}&limit={limit}'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=15)
        return [float(k[4]) for k in r.json()]
    except: return []

# ========== 技术指标 ==========
def calc_ema(prices, period):
    if len(prices) < period: return None
    ema = prices[0]
    smoothing = 2.0 / (period + 1)
    for p in prices[1:]:
        ema = (p - ema) * smoothing + ema
    return ema

def calc_rsi(prices, period=14):
    if len(prices) < period + 1: return 50
    deltas = np.diff(prices)
    gain = np.where(deltas > 0, deltas, 0)
    loss = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    if avg_loss == 0: return 100
    return 100 - (100 / (1 + avg_gain / avg_loss))

def calc_bb(prices, period=20):
    if len(prices) < period: return 50
    recent = prices[-period:]
    sma = np.mean(recent)
    std = np.std(recent)
    if std == 0: return 50
    return (prices[-1] - sma) / (2 * std) * 100 + 50

def calc_momentum(prices, period=5):
    if len(prices) < period + 1: return 0
    return (prices[-1] - prices[-period-1]) / prices[-period-1] * 100

# ========== 自适应参数 ==========
class AdaptiveParams:
    def __init__(self):
        # 初始参数范围
        self.rsi_buy_range = (25, 40)
        self.rsi_sell_range = (55, 75)
        self.bb_buy_range = (20, 40)
        self.bb_sell_range = (60, 85)
        self.ema_fast_range = (8, 20)
        self.ema_slow_range = (20, 50)
        self.position_range = (0.15, 0.50)
        
        # 当前最佳参数
        self.current = {
            'rsi_buy': 30,
            'rsi_sell': 65,
            'bb_buy': 25,
            'bb_sell': 75,
            'ema_fast': 12,
            'ema_slow': 26,
            'position': 0.30,
            'momentum_weight': 0.20,
            'rsi_weight': 0.35,
            'bb_weight': 0.25,
            'ema_weight': 0.20
        }
        
        self.best_params = self.current.copy()
        self.best_score = 0
        self.history = []
    
    def mutate(self):
        """变异参数寻找更好的组合"""
        new_params = self.current.copy()
        
        # 随机调整2-3个参数
        mutations = random.sample([
            'rsi_buy', 'rsi_sell', 'bb_buy', 'bb_sell',
            'ema_fast', 'ema_slow', 'position'
        ], k=random.randint(2, 4))
        
        for key in mutations:
            if key == 'rsi_buy':
                new_params[key] = random.randint(*self.rsi_buy_range)
            elif key == 'rsi_sell':
                new_params[key] = random.randint(*self.rsi_sell_range)
            elif key == 'bb_buy':
                new_params[key] = random.randint(*self.bb_buy_range)
            elif key == 'bb_sell':
                new_params[key] = random.randint(*self.bb_sell_range)
            elif key == 'ema_fast':
                new_params[key] = random.randint(*self.ema_fast_range)
            elif key == 'ema_sell':
                new_params[key] = random.randint(*self.ema_slow_range)
            elif key == 'position':
                new_params[key] = round(random.uniform(*self.position_range), 2)
        
        return new_params
    
    def update(self, new_params, score):
        """更新参数如果新参数更好"""
        self.history.append({
            'params': new_params.copy(),
            'score': score,
            'time': datetime.now().strftime('%H:%M:%S')
        })
        
        if score > self.best_score:
            self.best_score = score
            self.best_params = new_params.copy()
            self.current = new_params.copy()
            return True
        else:
            # 保留30%概率接受较差的参数(避免局部最优)
            if random.random() < 0.3:
                self.current = new_params
            return False

# ========== 回测引擎 ==========
def backtest(params, prices_data):
    """回测给定参数"""
    capital = 100
    position = None
    entry_price = 0
    trades = []
    
    for coin, prices in prices_data.items():
        if len(prices) < 100:
            continue
        
        for i in range(50, len(prices)-1):
            p = prices[:i+1]
            
            # 计算指标
            ema_fast = calc_ema(p, params['ema_fast'])
            ema_slow = calc_ema(p, params['ema_slow'])
            rsi = calc_rsi(p)
            bb = calc_bb(p)
            mom = calc_momentum(p)
            
            # 评分
            score = 0
            
            # EMA贡献
            if ema_fast and ema_slow:
                if ema_fast > ema_slow:
                    score += params['ema_weight'] * 100
                else:
                    score -= params['ema_weight'] * 100
            
            # RSI贡献
            if rsi < params['rsi_buy']:
                score += params['rsi_weight'] * 100
            elif rsi > params['rsi_sell']:
                score -= params['rsi_weight'] * 100
            elif rsi < 45:
                score += params['rsi_weight'] * 50
            elif rsi > 55:
                score -= params['rsi_weight'] * 50
            
            # BB贡献
            if bb < params['bb_buy']:
                score += params['bb_weight'] * 100
            elif bb > params['bb_sell']:
                score -= params['bb_weight'] * 100
            
            # 动量贡献
            if mom > 2:
                score += params['momentum_weight'] * 50
            elif mom < -2:
                score -= params['momentum_weight'] * 50
            
            # 交易
            if position is None and score > 50:
                position = prices[i]
                entry_idx = i
            elif position is not None and score < -30:
                pnl = (prices[i] - position) / position * 100
                capital *= (1 + pnl/100)
                trades.append(pnl)
                position = None
    
    return {
        'return': (capital / 100 - 1) * 100,
        'trades': len(trades),
        'wins': sum(1 for t in trades if t > 0),
        'losses': sum(1 for t in trades if t <= 0),
        'avg_win': np.mean([t for t in trades if t > 0]) if trades else 0,
        'avg_loss': np.mean([t for t in trades if t <= 0]) if trades else 0
    }

# ========== 主策略类 ==========
class G18SelfImproving:
    def __init__(self):
        self.name = "G18 Self-Improving"
        self.params = AdaptiveParams()
        self.prices_data = {}
        self.iteration = 0
        self.last_optimize = 0
        self.optimize_interval = 3600  # 每小时优化一次
    
    def load_data(self):
        """加载所有K线数据"""
        print("📊 加载市场数据...")
        for coin in COINS:
            prices = get_klines(f'{coin}USDT', 720)
            if prices:
                self.prices_data[coin] = prices
                print(f"  {coin}: {len(prices)}条")
    
    def optimize(self):
        """自主优化参数"""
        self.iteration += 1
        print(f"\n🔬 第{self.iteration}次迭代优化...")
        
        # 生成候选参数
        candidates = [self.params.mutate() for _ in range(20)]
        
        # 添加当前最佳
        candidates.append(self.params.best_params.copy())
        
        # 回测所有候选
        results = []
        for params in candidates:
            result = backtest(params, self.prices_data)
            result['params'] = params
            results.append(result)
        
        # 选择最佳
        results.sort(key=lambda x: x['return'], reverse=True)
        best = results[0]
        
        improved = self.params.update(best['params'], best['return'])
        
        print(f"  最佳收益: {best['return']:+.2f}%")
        print(f"  交易次数: {best['trades']}")
        print(f"  胜率: {best['wins']/max(1,best['trades'])*100:.1f}%")
        
        if improved:
            print(f"  ✅ 新最佳参数!")
            print(f"     RSI: {best['params']['rsi_buy']}/{best['params']['rsi_sell']}")
            print(f"     EMA: {best['params']['ema_fast']}/{best['params']['ema_slow']}")
            print(f"     Position: {best['params']['position']*100:.0f}%")
        else:
            print(f"  ⏸️ 保持当前参数")
        
        return best
    
    def generate_signals(self):
        """使用当前最佳参数生成信号"""
        signals = []
        
        for coin, prices in self.prices_data.items():
            if len(prices) < 50:
                continue
            
            p = prices
            params = self.params.best_params
            
            # 计算指标
            ema_fast = calc_ema(p, params['ema_fast'])
            ema_slow = calc_ema(p, params['ema_slow'])
            rsi = calc_rsi(p)
            bb = calc_bb(p)
            mom = calc_momentum(p)
            
            # 评分
            score = 0
            
            if ema_fast and ema_slow:
                if ema_fast > ema_slow:
                    score += params['ema_weight'] * 100
                else:
                    score -= params['ema_weight'] * 100
            
            if rsi < params['rsi_buy']:
                score += params['rsi_weight'] * 100
            elif rsi > params['rsi_sell']:
                score -= params['rsi_weight'] * 100
            
            if bb < params['bb_buy']:
                score += params['bb_weight'] * 100
            elif bb > params['bb_sell']:
                score -= params['bb_weight'] * 100
            
            if mom > 2:
                score += params['momentum_weight'] * 50
            elif mom < -2:
                score -= params['momentum_weight'] * 50
            
            # 信号
            if score > 50:
                signal = 'BUY'
            elif score < -30:
                signal = 'SELL'
            else:
                signal = 'HOLD'
            
            signals.append({
                'coin': coin,
                'score': score,
                'signal': signal,
                'rsi': rsi,
                'bb': bb,
                'ema_fast': ema_fast,
                'ema_slow': ema_slow,
                'momentum': mom,
                'price': prices[-1]
            })
        
        return signals
    
    def run(self):
        print("=" * 70)
        print("G18 Self-Improving v1.0 - 自主迭代优化版")
        print("=" * 70)
        
        # 加载数据
        self.load_data()
        
        # 初始优化
        self.optimize()
        
        # 生成信号
        signals = self.generate_signals()
        
        print(f"\n📊 当前最佳参数收益: {self.params.best_score:.2f}%")
        print(f"\n🔍 信号分析:")
        
        for s in sorted(signals, key=lambda x: x['score'], reverse=True):
            emoji = '🟢' if s['signal'] == 'BUY' else '🔴' if s['signal'] == 'SELL' else '🟡'
            print(f"  {emoji} {s['coin']:6} Score:{s['score']:6.1f} RSI:{s['rsi']:5.1f} BB:{s['bb']:5.1f}% Signal:{s['signal']}")
        
        # 保存状态
        self.save_state()
        
        return signals
    
    def save_state(self):
        """保存状态"""
        state = {
            'iteration': self.iteration,
            'best_score': self.params.best_score,
            'best_params': self.params.best_params,
            'history': self.params.history[-10:]  # 最近10次
        }
        with open(LOG_FILE, 'w') as f:
            json.dump(state, f, indent=2)

# ========== 主程序 ==========
def main():
    strategy = G18SelfImproving()
    strategy.run()

if __name__ == '__main__':
    main()
