#!/usr/bin/env python3
"""
G18 - Lean架构移植 + G16核心策略
Lean成分: 事件驱动架构、Alpha模型框架、Portfolio模块
G16成分: RSI/BB决策、全仓转移、杠杆增强
"""
import requests, numpy as np, time, json, hmac, hashlib
from datetime import datetime
from collections import defaultdict

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'

COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

# ========== Lean风格Alpha模型 ==========
class G16AlphaModel:
    """G16策略作为Lean样式的Alpha模型"""
    
    def __init__(self):
        self.name = "G16AlphaModel"
        self.insights = []
        self.symbol_data = {}
    
    def update(self, algorithm, data):
        """生成Insight - 类似Lean的Alpha模型"""
        insights = []
        for symbol in algorithm.active_securities:
            symbol_data = algorithm.symbol_data.get(symbol)
            if symbol_data and symbol_data.is_ready:
                # G16核心信号
                if symbol_data.score >= 50:
                    insights.append({
                        'symbol': symbol,
                        'direction': 'UP',
                        'score': symbol_data.score,
                        'rsi': symbol_data.rsi,
                        'ema_fast': symbol_data.ema_fast,
                        'ema_slow': symbol_data.ema_slow
                    })
                elif symbol_data.score <= -50:
                    insights.append({
                        'symbol': symbol,
                        'direction': 'DOWN', 
                        'score': symbol_data.score,
                        'rsi': symbol_data.rsi,
                        'ema_fast': symbol_data.ema_fast,
                        'ema_slow': symbol_data.ema_slow
                    })
        return insights

# ========== Lean风格Portfolio模型 ==========
class G16PortfolioModel:
    """Lean样式的Portfolio模型 - 目标权重执行"""
    
    def __init__(self, target_weights):
        self.target_weights = target_weights  # {symbol: weight}
        self.name = "G16PortfolioModel"
    
    def rebalance(self, algorithm):
        """根据目标权重调仓 - Lean's Portfolio Construction Model"""
        for symbol, target in self.target_weights.items():
            current = algorithm.positions.get(symbol, 0)
            target_qty = algorithm.portfolio_value * target / algorithm.prices.get(symbol, 1)
            
            diff = target_qty - current
            if abs(diff) > 0.0001:
                algorithm.pending_orders.append({
                    'symbol': symbol,
                    'qty': diff,
                    'direction': 'BUY' if diff > 0 else 'SELL'
                })

# ========== SymbolData - Lean样式 ==========
class SymbolData:
    def __init__(self, symbol, prices):
        self.symbol = symbol
        self.prices = prices
        self.ema_fast = None
        self.ema_slow = None
        self.rsi = None
        self.bb = None
        self.score = 0
        self.is_ready = len(prices) > 50
    
    def update(self):
        if not self.is_ready:
            return
        
        # EMA (Lean)
        self.ema_fast = self.calc_ema(12)
        self.ema_slow = self.calc_ema(26)
        
        # RSI + BB (G16)
        self.rsi = self.calc_rsi()
        self.bb = self.calc_bb()
        
        # G16综合评分
        self.calc_score()
    
    def calc_ema(self, period):
        if len(self.prices) < period:
            return None
        ema = self.prices[0]
        smoothing = 2.0 / (period + 1)
        for p in self.prices[1:]:
            ema = (p - ema) * smoothing + ema
        return ema
    
    def calc_rsi(self, period=14):
        if len(self.prices) < period + 1:
            return 50
        deltas = np.diff(self.prices)
        gain = np.where(deltas > 0, deltas, 0)
        loss = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gain[-period:])
        avg_loss = np.mean(loss[-period:])
        if avg_loss == 0:
            return 100
        return 100 - (100 / (1 + avg_gain / avg_loss))
    
    def calc_bb(self, period=20):
        if len(self.prices) < period:
            return 50
        recent = self.prices[-period:]
        sma = np.mean(recent)
        std = np.std(recent)
        if std == 0:
            return 50
        return (self.prices[-1] - sma) / (2 * std) * 100 + 50
    
    def calc_score(self):
        # 融合Lean EMA + G16
        score = 0
        
        # Lean EMA贡献 (40%)
        if self.ema_fast and self.ema_slow:
            if self.ema_fast > self.ema_slow:
                score += 40
            else:
                score -= 40
        
        # G16 RSI贡献 (35%)
        if self.rsi < 35:
            score += 35
        elif self.rsi < 45:
            score += 15
        elif self.rsi > 65:
            score -= 35
        elif self.rsi > 55:
            score -= 15
        
        # G16 BB贡献 (25%)
        if self.bb < 30:
            score += 25
        elif self.bb > 70:
            score -= 25
        
        self.score = score

# ========== Lean风格Algorithm框架 ==========
class G16LeanFramework:
    """Lean框架的Python移植版"""
    
    def __init__(self):
        self.name = "G18 - Lean Framework + G16"
        self.alpha_model = G16AlphaModel()
        self.portfolio_model = None
        
        self.active_securities = COINS
        self.prices = {}  # {symbol: price}
        self.positions = {}  # {symbol: qty}
        self.portfolio_value = 0
        self.symbol_data = {}
        self.pending_orders = []
        
        self.signature = None
    
    # ========== API ==========
    def sign(self, params):
        params['recvWindow'] = 5000
        params['timestamp'] = int(time.time()*1000)
        query = '&'.join([f'{k}={v}' for k,v in sorted(params.items())])
        sig = hmac.new(self.signature.encode(), query.encode(), hashlib.sha256).hexdigest()
        return query + '&signature=' + sig
    
    def api_get(self, url, params=None):
        try:
            params = params or {}
            r = requests.get(url + '?' + self.sign(params), 
                          headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
            return r.json()
        except: return {}
    
    def api_post(self, url, params):
        try:
            r = requests.post(url + '?' + self.sign(params), 
                            headers={'X-MBX-APIKEY': API_KEY}, proxies=PROXIES, timeout=10)
            return r.json()
        except: return {'code': -1}
    
    def get_price(self, symbol):
        try:
            r = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}', 
                           proxies=PROXIES, timeout=5)
            return float(r.json()['price'])
        except: return 0
    
    def get_klines(self, sym, limit=200):
        end = int(time.time()*1000)
        start = end - limit * 3600 * 1000
        url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&startTime={start}&endTime={end}&limit={limit}'
        try:
            r = requests.get(url, proxies=PROXIES, timeout=15)
            return [float(k[4]) for k in r.json()]
        except: return []
    
    # ========== 数据更新 ==========
    def initialize(self):
        """Lean的Initialize()"""
        self.signature = API_SECRET
        
        # 获取账户数据
        spot_data = self.api_get('https://api.binance.com/api/v3/account')
        if 'balances' in spot_data:
            for b in spot_data['balances']:
                free = float(b.get('free', 0))
                if free > 0.00001:
                    self.positions[b['asset']] = free
        
        # 获取K线数据并构建SymbolData
        for coin in self.active_securities:
            prices = self.get_klines(f'{coin}USDT')
            if prices:
                self.prices[coin] = prices[-1]
                self.symbol_data[coin] = SymbolData(coin, prices)
                self.symbol_data[coin].update()
        
        # 计算总资产
        self.portfolio_value = sum(
            self.positions.get(c, 0) * self.prices.get(c, 0) 
            for c in self.active_securities
        )
        
        # 构建Portfolio模型
        self.build_portfolio_model()
    
    def build_portfolio_model(self):
        """Lean's Portfolio Construction Model"""
        weights = {}
        for coin, sd in self.symbol_data.items():
            if sd.is_ready:
                if sd.score >= 50:
                    weights[coin] = 0.35
                elif sd.score >= 25:
                    weights[coin] = 0.20
                elif sd.score <= -25:
                    weights[coin] = 0.0
        
        self.portfolio_model = G16PortfolioModel(weights)
    
    # ========== Lean生命周期 ==========
    def on_data(self, data):
        """Lean's OnData() - 每个数据点触发"""
        # 更新价格
        for coin in self.active_securities:
            prices = self.get_klines(f'{coin}USDT')
            if prices:
                self.prices[coin] = prices[-1]
                if coin in self.symbol_data:
                    self.symbol_data[coin].prices = prices
                    self.symbol_data[coin].update()
        
        # Alpha模型产生Insight
        insights = self.alpha_model.update(self, data)
        
        # 重建Portfolio模型
        self.build_portfolio_model()
        
        return insights
    
    def execute_orders(self):
        """执行Pending订单"""
        results = []
        for order in self.pending_orders:
            symbol = order['symbol']
            qty = order['qty']
            
            if order['direction'] == 'BUY':
                result = self.spot_to_margin(symbol, abs(qty))
            else:
                result = self.margin_to_spot(symbol, abs(qty))
            
            results.append({'order': order, 'result': result})
        
        self.pending_orders = []
        return results
    
    def spot_to_margin(self, asset, qty):
        url = 'https://api.binance.com/sapi/v1/margin/transfer'
        params = {
            'asset': asset, 'type': 1,
            'amount': f'{qty:.8f}'.rstrip('0').rstrip('.')
        }
        return self.api_post(url, params)
    
    def margin_to_spot(self, asset, qty):
        url = 'https://api.binance.com/sapi/v1/margin/transfer'
        params = {
            'asset': asset, 'type': 2,
            'amount': f'{qty:.8f}'.rstrip('0').rstrip('.')
        }
        return self.api_post(url, params)
    
    # ========== 主循环 ==========
    def run(self):
        """Lean风格的主循环"""
        print("=" * 70)
        print("G18 v1.0 - Lean Framework + G16 Core")
        print("=" * 70)
        
        # Initialize
        self.initialize()
        
        print(f"\n📊 Portfolio Value: ${self.portfolio_value:.2f}")
        
        # OnData - 产生信号
        insights = self.on_data({})
        
        print(f"\n🔍 Alpha Insights (Lean Framework):")
        for ins in insights:
            emoji = '🟢' if ins['direction'] == 'UP' else '🔴'
            print(f"  {emoji} {ins['symbol']}: {ins['direction']} Score:{ins['score']} RSI:{ins['rsi']:.0f}")
        
        # Portfolio Rebalance
        if self.portfolio_model:
            self.portfolio_model.rebalance(self)
            
            print(f"\n⚖️ Portfolio Rebalance:")
            if not self.pending_orders:
                print("  ⏸️ 无需调仓")
            else:
                for order in self.pending_orders:
                    print(f"  📈 {order['direction']} {order['symbol']} {order['qty']:.6f}")
            
            # Execute
            if self.pending_orders:
                print("\n🚀 执行订单:")
                results = self.execute_orders()
                for r in results:
                    order = r['order']
                    result = r['result']
                    if 'tranId' in result:
                        print(f"  ✅ {order['symbol']}: {order['direction']} {order['qty']:.6f}")
                    else:
                        print(f"  ❌ {order['symbol']}: {result.get('msg', result)}")

# ========== 主程序 ==========
def main():
    algo = G16LeanFramework()
    algo.run()

if __name__ == '__main__':
    main()
