#!/usr/bin/env python3
"""
G42 - 终极收益最大化交易系统
============================
架构: 技能融合 + 多策略 + 自优化 + Mirofish Pro

版本: v2.0
目标: 30天收益最大化
技能: 162+可用
"""

import json, time, urllib.request, hmac, hashlib, signal, os, math
from datetime import datetime
from collections import defaultdict
import random

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = 'http://172.29.144.1:7897'
LOG_FILE = '/home/goose/.openclaw/workspace/logs/g42.log'

# Polymarket信号
POLYMARKET = {
    'BTC': 0.42, 'ETH': 0.35, 'SOL': 0.28, 'DOGE': 0.22,
    'XRP': 0.15, 'ADA': 0.12, 'DOT': 0.10, 'LINK': 0.08,
    'BNB': 0.05, 'AVAX': 0.05, 'MATIC': 0.04, 'FTM': 0.06
}

# 币种配置
COINS = {
    'mainstream': ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOT', 'LINK', 'BNB'],
    'meme': ['DOGE', 'SHIB', 'PEPE', 'BONK', 'NEIRO', 'BOME', 'FTM', 'MATIC', 'AVAX'],
    'all': ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOT', 'LINK', 'BNB', 'DOGE', 'SHIB', 'PEPE', 'BONK', 'NEIRO', 'BOME', 'FTM', 'MATIC', 'AVAX']
}

# ============ 高级策略库 ============

class StrategyLibrary:
    """策略库 - 10+高级策略"""
    
    STRATEGIES = {
        'go-core': {'weight': 0.15, 'func': 'trend_core'},
        'go-pool': {'weight': 0.12, 'func': 'liquidity_pool'},
        'go-rotate': {'weight': 0.10, 'func': 'market_rotate'},
        'go-long-short': {'weight': 0.10, 'func': 'long_short'},
        'go-detect': {'weight': 0.08, 'func': 'institution_detect'},
        'momentum': {'weight': 0.08, 'func': 'momentum'},
        'mean-reversion': {'weight': 0.08, 'func': 'mean_reversion'},
        'breakout': {'weight': 0.07, 'func': 'breakout'},
        'volume-profile': {'weight': 0.07, 'func': 'volume_profile'},
        'sentiment': {'weight': 0.05, 'func': 'sentiment'}
    }
    
    @staticmethod
    def trend_core(closes, volumes):
        ma5 = sum(closes[-5:])/5
        ma20 = sum(closes[-20:])/20
        ma50 = sum(closes[-50:])/50 if len(closes) >= 50 else ma20
        trend = (ma5 - ma20)/ma20 if ma20 > 0 else 0
        trend50 = (ma20 - ma50)/ma50 if ma50 > 0 else 0
        return trend * 10 + trend50 * 5
    
    @staticmethod
    def liquidity_pool(closes, volumes):
        vol_avg = sum(volumes[-20:])/20
        vol_ratio = volumes[-1]/vol_avg if vol_avg > 0 else 1
        return (vol_ratio - 1) * 0.5
    
    @staticmethod
    def market_rotate(closes, volumes, market):
        ma5 = sum(closes[-5:])/5
        ma20 = sum(closes[-20:])/20
        trend = (ma5 - ma20)/ma20 if ma20 > 0 else 0
        return trend * (0.8 if market == 'range' else 0.3)
    
    @staticmethod
    def long_short(closes, volumes):
        deltas = [closes[i+1]-closes[i] for i in range(len(closes)-1)]
        gains = [d for d in deltas if d > 0]
        losses = [-d for d in deltas if d < 0]
        avg_gain = sum(gains)/len(gains) if gains else 0
        avg_loss = sum(losses)/len(losses) if losses else 0
        rs = avg_gain/avg_loss if avg_loss > 0 else 100
        rsi = 100 - (100/(1+rs))
        return (rsi - 50) / 50
    
    @staticmethod
    def institution_detect(closes, volumes):
        ma20 = sum(closes[-20:])/20
        ma50 = sum(closes[-50:])/50 if len(closes) >= 50 else ma20
        trend50 = (ma20 - ma50)/ma50 if ma50 > 0 else 0
        return trend50 * 5
    
    @staticmethod
    def momentum(closes, volumes):
        returns = [(closes[i]-closes[i-1])/closes[i-1] for i in range(1, len(closes))]
        momentum = sum(returns[-10:])/10 if len(returns) >= 10 else 0
        return momentum * 100
    
    @staticmethod
    def mean_reversion(closes, volumes):
        ma20 = sum(closes[-20:])/20
        current = closes[-1]
        deviation = (current - ma20)/ma20 if ma20 > 0 else 0
        return -deviation * 10  # 回归均值
    
    @staticmethod
    def breakout(closes, volumes):
        if len(closes) < 20: return 0
        highs = [closes[i] for i in range(len(closes)-20, len(closes))]
        current = closes[-1]
        resistance = max(highs[:-1]) if highs else current
        return 1 if current > resistance * 1.01 else -0.5 if current < resistance * 0.99 else 0
    
    @staticmethod
    def volume_profile(closes, volumes):
        vol_ma = sum(volumes[-20:])/20
        vol_current = volumes[-1]
        price_ma = sum(closes[-20:])/20
        price_current = closes[-1]
        return 1 if vol_current > vol_ma * 1.5 and price_current > price_ma else 0
    
    @staticmethod
    def sentiment(closes, volumes, polymarket_signal=0):
        ma5 = sum(closes[-5:])/5
        ma20 = sum(closes[-20:])/20
        trend = (ma5 - ma20)/ma20 if ma20 > 0 else 0
        return trend * 20 + polymarket_signal

# ============ Mirofish Pro 仿真系统 ============

class MirofishPro:
    """Mirofish Pro - 高级仿真引擎"""
    
    def __init__(self):
        self.initial = 0
        self.capital = 0
        self.positions = {}
        self.history = []
        self.best_strategy = None
        self.strategy_returns = defaultdict(list)
        
    def init(self, capital):
        self.initial = capital
        self.capital = capital
        self.positions = {}
        self.history = []
        
    def simulate(self, signal, price, symbol, strategy_name):
        """单次仿真"""
        if signal > 0.1 and symbol not in self.positions:
            # 买入
            qty = (self.capital * 0.2) / price
            if qty * price > 1:
                self.positions[symbol] = {
                    'qty': qty, 'entry': price, 
                    'strategy': strategy_name, 'time': time.time()
                }
                self.history.append(('BUY', symbol, price, qty, strategy_name))
                self.capital -= qty * price
                
        elif signal < -0.05 and symbol in self.positions:
            # 卖出
            p = self.positions[symbol]
            pnl = (price - p['entry']) * p['qty']
            self.history.append(('SELL', symbol, price, p['qty'], pnl))
            self.capital += p['qty'] * price
            self.strategy_returns[p['strategy']].append(pnl)
            del self.positions[symbol]
            return pnl
        return 0
    
    def evaluate(self):
        """全面评测"""
        total_pnl = self.capital - self.initial
        final_value = self.capital + sum(p['qty'] * p['entry'] for p in self.positions.values())
        roi = (final_value - self.initial) / self.initial * 100 if self.initial > 0 else 0
        
        wins = [h for h in self.history if isinstance(h, tuple) and len(h) > 4 and h[4] > 0]
        losses = [h for h in self.history if isinstance(h, tuple) and len(h) > 4 and h[4] <= 0]
        win_rate = len(wins) / len(self.history) * 100 if self.history else 0
        
        # 最佳策略
        best = max(self.strategy_returns.items(), key=lambda x: sum(x[1])/len(x[1]) if x[1] else 0, default=(None, []))
        
        return {
            'roi': roi,
            'final_value': final_value,
            'win_rate': win_rate,
            'total_trades': len(self.history),
            'wins': len(wins),
            'losses': len(losses),
            'best_strategy': best[0] if best[0] else 'N/A',
            'positions': len(self.positions)
        }

# ============ 自优化引擎 ============

class AutoOptimizer:
    """自动优化引擎"""
    
    def __init__(self):
        self.cycle = 0
        self.performance = defaultdict(list)
        self.weights = {k: v['weight'] for k, v in StrategyLibrary.STRATEGIES.items()}
        self.market_type = 'range'
        self.best_config = None
        
    def analyze_market(self, closes, volumes):
        """分析市场类型"""
        if len(closes) < 50: return 'neutral'
        ma5 = sum(closes[-5:])/5
        ma20 = sum(closes[-20:])/20
        returns = [(closes[i]-closes[i-1])/closes[i-1] for i in range(1, len(closes))]
        vol = sum(abs(r) for r in returns[-20:])/20
        trend = (ma5 - ma20)/ma20 if ma20 > 0 else 0
        
        if trend > 0.03: return 'trend'
        elif vol < 0.015: return 'range'
        elif trend > 0.015 and vol > 0.025: return 'breakout'
        return 'range'
    
    def adjust_weights(self, market, eval_result):
        """根据市场调整权重"""
        self.cycle += 1
        self.market_type = market
        
        # 市场适应调整
        if market == 'trend':
            adjustments = {'go-core': 1.3, 'momentum': 1.2, 'go-long-short': 1.1}
        elif market == 'range':
            adjustments = {'go-pool': 1.3, 'mean-reversion': 1.2, 'go-rotate': 1.1}
        else:  # breakout
            adjustments = {'breakout': 1.4, 'volume-profile': 1.2, 'go-detect': 1.2}
        
        for k, v in adjustments.items():
            if k in self.weights:
                self.weights[k] *= v
        
        # 归一化
        total = sum(self.weights.values())
        self.weights = {k: v/total for k, v in self.weights.items()}
        
        return self.weights
    
    def get_weights(self):
        return self.weights.copy()

# ============ G42 核心 ============

class G42Core:
    """G42 核心引擎"""
    
    def __init__(self):
        self.strategies = StrategyLibrary()
        self.mirofish = MirofishPro()
        self.optimizer = AutoOptimizer()
        self.running = True
        self.cycle = 0
        
    def calculate_all_signals(self, closes, volumes, polymarket=0):
        """计算所有策略信号"""
        market = self.optimizer.analyze_market(closes, volumes)
        signals = {}
        
        # 基础信号
        signals['go-core'] = self.strategies.trend_core(closes, volumes)
        signals['go-pool'] = self.strategies.liquidity_pool(closes, volumes)
        signals['go-rotate'] = self.strategies.market_rotate(closes, volumes, market)
        signals['go-long-short'] = self.strategies.long_short(closes, volumes)
        signals['go-detect'] = self.strategies.institution_detect(closes, volumes)
        signals['momentum'] = self.strategies.momentum(closes, volumes)
        signals['mean-reversion'] = self.strategies.mean_reversion(closes, volumes)
        signals['breakout'] = self.strategies.breakout(closes, volumes)
        signals['volume-profile'] = self.strategies.volume_profile(closes, volumes)
        signals['sentiment'] = self.strategies.sentiment(closes, volumes, polymarket)
        
        return signals, market
    
    def fuse_signals(self, signals, weights, polymarket=0):
        """融合信号"""
        go_signal = sum(signals.get(k, 0) * weights.get(k, 0) for k in weights)
        return go_signal * 0.7 + polymarket * 0.3
    
    def select_top_coins(self, signals_dict, holdings, top_n=3):
        """选择最佳币种"""
        candidates = []
        for sym, data in signals_dict.items():
            if sym in holdings: continue
            combined = data['combined']
            strength = abs(combined)
            score = combined * (1 + strength)
            candidates.append((sym, score, combined, data['market']))
        
        candidates.sort(key=lambda x: -x[1])
        return candidates[:top_n]
    
    def should_sell(self, sym, holding_value, signals_dict):
        """判断是否卖出"""
        if sym not in signals_dict: return False
        return signals_dict[sym]['combined'] < -0.08 and holding_value > 1

# ============ API ============

def api_signed(endpoint, params=None, method='GET'):
    ts = int(time.time() * 1000)
    base = {'timestamp': ts, 'recvWindow': 5000}
    if params: base.update(params)
    q = '&'.join('{}={}'.format(k, v) for k, v in sorted(base.items()))
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = 'https://api.binance.com{}?{}&signature={}'.format(endpoint, q, sig)
    req = urllib.request.Request(url, method=method)
    req.add_header('X-MBX-APIKEY', API_KEY)
    proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    return json.loads(opener.open(req, timeout=15).read().decode())

def get_price(sym):
    try:
        url = 'https://api.binance.com/api/v3/ticker/price?symbol=' + sym + 'USDT'
        proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
        opener = urllib.request.build_opener(proxy_handler)
        d = json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())
        return float(d['price'])
    except: return 0

def get_klines(sym, interval='15m', limit=100):
    try:
        url = 'https://api.binance.com/api/v3/klines?symbol=' + sym + 'USDT&interval=' + interval + '&limit=' + str(limit)
        proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
        opener = urllib.request.build_opener(proxy_handler)
        return json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())
    except: return []

def place_order(sym, side, qty, retry=2):
    """下单函数，带自动修复"""
    for attempt in range(retry + 1):
        try:
            ts = int(time.time() * 1000)
            # Binance数量格式
            if qty >= 1:
                qty_str = str(int(qty))
            else:
                qty_str = '{:.6f}'.format(qty)
            
            params = {'symbol': sym + 'USDT', 'side': side, 'type': 'MARKET', 'quantity': qty_str, 'timestamp': ts, 'recvWindow': 5000}
            q = '&'.join('{}={}'.format(k, v) for k, v in sorted(params.items()))
            sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
            url = 'https://api.binance.com/api/v3/order?' + q + '&signature=' + sig
            req = urllib.request.Request(url, method='POST')
            req.add_header('X-MBX-APIKEY', API_KEY)
            proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
            opener = urllib.request.build_opener(proxy_handler)
            
            try:
                resp = json.loads(opener.open(req, timeout=10).read().decode())
            except urllib.error.HTTPError as e:
                error_body = e.read().decode()
                try:
                    error_json = json.loads(error_body)
                    error_msg = error_json.get('msg', error_body)
                except:
                    error_msg = error_body
                log('  Binance错误: {} (尝试{}/{})'.format(error_msg, attempt+1, retry+1))
                
                # 自动修复
                if 'LOT_SIZE' in error_msg or 'MIN_NOTIONAL' in error_msg:
                    qty = qty * 1.2
                    if qty >= 1:
                        qty_str = str(int(qty))
                    else:
                        qty_str = '{:.6f}'.format(qty)
                    log('  自动修复: 调整数量为 {}'.format(qty_str))
                    time.sleep(0.5)
                    continue
                elif 'INSUFFICIENT' in error_msg:
                    return {'success': False, 'error': '余额不足', 'retry': False}
                
                if attempt < retry:
                    time.sleep(1)
                    continue
                return {'success': False, 'error': error_msg}
            
            if 'code' in resp:
                error_msg = resp.get('msg', '')
                log('  错误: {} (尝试{}/{})'.format(error_msg, attempt+1, retry+1))
                if attempt < retry:
                    time.sleep(1)
                    continue
                return {'success': False, 'error': error_msg}
            
            log('  成功: {} {} x {}'.format(side, sym, qty_str))
            return {'success': True, 'symbol': sym}
            
        except Exception as e:
            log('  异常: {} (尝试{}/{})'.format(str(e), attempt+1, retry+1))
            if attempt < retry:
                time.sleep(1)
                continue
            return {'success': False, 'error': str(e)}
    
    return {'success': False, 'error': 'MAX_RETRIES'}

def log(msg):
    ts = datetime.now().strftime('%m-%d %H:%M:%S')
    line = '[' + ts + '] ' + msg
    try:
        with open(LOG_FILE, 'a') as f: f.write(line + chr(10))
    except: pass
    print(line, flush=True)

def get_account():
    try:
        ts = int(time.time() * 1000)
        params = {'timestamp': ts, 'recvWindow': 5000}
        q = '&'.join('{}={}'.format(k, v) for k, v in sorted(params.items()))
        sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
        url = 'https://api.binance.com/api/v3/account?' + q + '&signature=' + sig
        req = urllib.request.Request(url)
        req.add_header('X-MBX-APIKEY', API_KEY)
        proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
        opener = urllib.request.build_opener(proxy_handler)
        return json.loads(opener.open(req, timeout=15).read().decode())
    except: return {}

# ============ MAIN ============

def main():
    g42 = G42Core()
    
    def signal_handler(sig, frame):
        log('G42 停止信号...')
        g42.running = False
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    log('=' * 70)
    log('G42 v2.0 启动 - 终极收益最大化系统')
    log('策略数: 10+ | 币种: 17 | 目标: 30天收益最大化')
    log('=' * 70)
    
    scan_interval = 60  # 60秒
    
    while g42.running:
        try:
            g42.cycle += 1
            
            # 获取账户
            account = get_account()
            prices = {s: get_price(s) for s in COINS['all']}
            holdings = {}
            
            for b in account.get('balances', []):
                free = float(b.get('free', 0))
                asset = b['asset']
                if asset != 'USDT' and free > 0:
                    price = prices.get(asset, 0)
                    value = free * price
                    if value > 0.1:
                        holdings[asset] = {'amount': free, 'price': price, 'value': value}
            
            total = sum(h['value'] for h in holdings.values())
            usdt_bal = float([b for b in account.get('balances', []) if b['asset'] == 'USDT'][0]['free'])
            total += usdt_bal
            
            # Mirofish初始化
            g42.mirofish.init(usdt_bal)
            
            log('')
            log('=== G42 周期{} | 总资产:${:.2f} | USDT:${:.2f} ==='.format(g42.cycle, total, usdt_bal))
            
            # 分析所有币种
            signals_dict = {}
            market_counts = defaultdict(int)
            
            for sym in COINS['all']:
                klines = get_klines(sym)
                if not klines or len(klines) < 50: continue
                
                closes = [float(k[4]) for k in klines if len(k) > 4]
                volumes = [float(k[5]) for k in klines if len(k) > 5]
                pm = POLYMARKET.get(sym, 0)
                
                signals, market = g42.calculate_all_signals(closes, volumes, pm)
                weights = g42.optimizer.get_weights()
                combined = g42.fuse_signals(signals, weights, pm)
                
                signals_dict[sym] = {
                    'signals': signals,
                    'combined': combined,
                    'market': market,
                    'pm': pm
                }
                market_counts[market] += 1
                
                # Mirofish仿真
                g42.mirofish.simulate(combined, closes[-1], sym, 'multi-strategy')
            
            # 策略权重
            log('市场: ' + ', '.join(['{}:{}'.format(k, v) for k, v in market_counts.items()]))
            log('策略权重: ' + ', '.join(['{}:{:.0f}%'.format(k.replace('go-',''), v*100) for k, v in g42.optimizer.get_weights().items()]))
            
            # 决策 - 基于信号阈值自动执行
            decisions = {'buy': [], 'sell': []}
            
            # 卖出 - 阈值优化，检查最小订单金额
            MIN_NOTIONAL = 5  # 最小卖出价值$5
            for sym, holding in holdings.items():
                if sym in signals_dict:
                    sig = signals_dict[sym]['combined']
                    price = prices.get(sym, 0)
                    sell_value = holding['amount'] * 0.5 * price
                    if sig < -0.05 and sell_value >= MIN_NOTIONAL:
                        decisions['sell'].append({'symbol': sym, 'amount': holding['amount'] * 0.5})
                        log('  卖出信号: {} {:.2f} 价值${:.0f}'.format(sym, sig, sell_value))
                    elif sig < -0.05 and sell_value < MIN_NOTIONAL:
                        log('  跳过卖出: {} 价值${:.0f} < ${}'.format(sym, sell_value, MIN_NOTIONAL))
            
            # 买入 - 降低阈值提高执行率，确保最小订单金额
            MIN_NOTIONAL = 10  # 最小订单价值$10
            SKIP_COINS = ['FTM']  # 跳过关闭的市场
            for sym in COINS['all']:
                if sym in holdings or sym in SKIP_COINS or sym not in signals_dict: continue
                sig = signals_dict[sym]['combined']
                if sig > 0.05 and usdt_bal > 10:
                    budget = usdt_bal * 0.3
                    price = prices.get(sym, 0)
                    if price > 0:
                        qty = budget / price
                        notional = qty * price
                        if notional >= MIN_NOTIONAL and qty > 0.0001:
                            decisions['buy'].append({'symbol': sym, 'budget': budget, 'price': price, 'signal': sig})
                            log('  买入信号: {} {:.2f} 订单价值${:.0f}'.format(sym, sig, notional))
                        else:
                            log('  跳过: {} 订单价值${:.0f} < ${}'.format(sym, notional, MIN_NOTIONAL))
            
            # 执行卖出
            if decisions['sell']:
                log('卖出:')
                for d in decisions['sell'][:2]:
                    log('  SELL {} (信号: {:.2f})'.format(d['symbol'], signals_dict.get(d['symbol'], {}).get('combined', 0)))
                    result = place_order(d['symbol'], 'SELL', d['amount'])
                    log('    结果: {}'.format('成功' if result.get('success') else '失败'))
            
            # 执行买入
            if decisions['buy']:
                log('买入:')
                for d in decisions['buy'][:2]:
                    log('  BUY {} (信号: {:.2f}, 预算: ${:.0f})'.format(d['symbol'], d['signal'], d['budget']))
                    qty = d['budget'] / d['price']
                    if qty > 0.0001:
                        result = place_order(d['symbol'], 'BUY', qty)
                        log('    结果: {}'.format('成功' if result.get('success') else '失败'))
            
            # Mirofish评测
            if g42.cycle % 5 == 0:
                eval_result = g42.mirofish.evaluate()
                log('Mirofish: ROI{:.1f}% 胜率{:.0f}% 交易{} 最佳策略: {}'.format(
                    eval_result['roi'], eval_result['win_rate'],
                    eval_result['total_trades'], eval_result['best_strategy']))
                
                # 自优化
                main_market = max(market_counts.items(), key=lambda x: x[1])[0]
                g42.optimizer.adjust_weights(main_market, eval_result)
            
            # 等待
            for _ in range(scan_interval):
                if not g42.running: break
                time.sleep(1)
                
        except Exception as e:
            log('异常: ' + str(e))
            time.sleep(10)
    
    log('G42 v2.0 已停止')

if __name__ == '__main__': main()
