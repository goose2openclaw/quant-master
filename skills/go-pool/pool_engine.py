#!/usr/bin/env python3
"""
go-pool - 撞球策略核心引擎 v1.0
================================
模拟台球连续进球的资金轮转策略

核心思想:
- 不同币种处于不同的回报周期阶段
- 系统识别并切换到正在加速的币种
- 享受完当前币种大半个回报周期后自然切换
- 始终保持"进球"状态
"""

import urllib.request, hmac, hashlib, time, json, sys, math
from datetime import datetime
from collections import defaultdict, deque

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

# ============ 撞球策略常量 ============

# 周期阶段
PHASE_CONSOLIDATION = 0  # 盘整期 (蓄力)
PHASE_EARLY = 1          # 启动期 (刚启动)
PHASE_ACCELERATION = 2   # 加速期 (快速上涨) ← 主要进球区间
PHASE_PEAK = 3           # 高峰期 (接近顶点)
PHASE_DECLINE = 4        # 衰退期 (开始下跌)

PHASE_NAMES = {
    PHASE_CONSOLIDATION: "盘整",
    PHASE_EARLY: "启动",
    PHASE_ACCELERATION: "加速",
    PHASE_PEAK: "高峰",
    PHASE_DECLINE: "衰退"
}

# 预算配置
MAX_ACTIVE_COINS = 3      # 最多同时持有
MIN_CYCLE_COMPLETION = 0.3  # 最少完成30%周期才切换
KELLY_BASE = 0.15         # Kelly基准仓位
SWITCH_COOLDOWN = 1800    # 切换冷却30分钟

# 币种池 (按类型分组)
MAJOR_COINS = ['BTC','ETH','BNB','SOL','XRP','ADA','DOGE','DOT','LINK','UNI','AVAX','ATOM','LTC','ETC','NEAR']
MEME_COINS = ['TURBO','BOME','NEIRO','BONK','PEPE','FLOKI','SHIB','PUMP']
ALL_COINS = MAJOR_COINS + MEME_COINS

# ============ 工具函数 ============

def api_get(url, retries=2):
    for i in range(retries):
        try:
            proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
            opener = urllib.request.build_opener(proxy_handler)
            return json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())
        except:
            if i < retries - 1: time.sleep(0.5)
    return None

def api_signed_get(endpoint, params=None, retries=3):
    for i in range(retries):
        try:
            ts = int(time.time() * 1000)
            base = {"timestamp": ts, "recvWindow": 5000}
            if params: base.update(params)
            q = "&".join(f"{k}={v}" for k, v in sorted(base.items()))
            sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
            url = f"https://api.binance.com{endpoint}?{q}&signature={sig}"
            req = urllib.request.Request(url)
            req.add_header('X-MBX-APIKEY', API_KEY)
            proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
            opener = urllib.request.build_opener(proxy_handler)
            return json.loads(opener.open(req, timeout=15).read().decode())
        except:
            if i < retries - 1: time.sleep(1)
    return None

def get_price(symbol):
    try:
        return float(api_get(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}')['price'])
    except: return 0

# ============ K线分析 ============

def get_klines(symbol, interval='1h', limit=100):
    data = api_get(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}')
    if not data: return []
    return [{
        'time': k[0] // 1000,
        'open': float(k[1]),
        'high': float(k[2]),
        'low': float(k[3]),
        'close': float(k[4]),
        'volume': float(k[5])
    } for k in data]

def get_rsi(closes, period=14):
    if len(closes) < period + 1: return 50
    deltas = [closes[i+1] - closes[i] for i in range(len(closes)-1)]
    gains = [d if d > 0 else 0 for d in deltas[-period:]]
    losses = [-d if d < 0 else 0 for d in deltas[-period:]]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0: return 100
    return 100 - (100 / (1 + avg_gain / avg_loss))

def get_momentum(closes, period=20):
    if len(closes) < period + 1: return 0
    return (closes[-1] - closes[0]) / closes[0]

def get_volatility(closes, period=20):
    if len(closes) < period + 1: return 0.01
    returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
    mean = sum(returns[-period:]) / len(returns[-period:])
    variance = sum((r - mean) ** 2 for r in returns[-period:]) / len(returns[-period:])
    return math.sqrt(variance)

# ============ 周期分析 ============

class CycleAnalyzer:
    """回报周期分析器"""
    
    def __init__(self, coin):
        self.coin = coin
        self.data_1h = get_klines(f"{coin}USDT", '1h', 168)  # 7天1h数据
        self.data_4h = get_klines(f"{coin}USDT", '4h', 180)   # 30天4h数据
        self.data_1d = get_klines(f"{coin}USDT", '1d', 90)    # 90天1d数据
    
    def detect_phase(self):
        """检测当前处于哪个周期阶段"""
        if not self.data_1h: return PHASE_CONSOLIDATION
        
        closes_1h = [d['close'] for d in self.data_1h]
        closes_4h = [d['close'] for d in self.data_4h] if self.data_4h else closes_1h
        
        # 计算各项指标
        rsi = get_rsi(closes_1h)
        momentum_short = get_momentum(closes_1h[-24:])  # 24小时动量
        momentum_long = get_momentum(closes_1h[-168:])  # 7天动量
        volatility = get_volatility(closes_1h)
        
        # 周期完成度估算
        cycle_completion = self._estimate_cycle_completion(closes_4h)
        
        # 阶段判断
        if momentum_long < -0.05:
            # 下跌趋势中的反弹
            if momentum_short > 0.03 and rsi < 60:
                return PHASE_EARLY
            return PHASE_DECLINE
        
        if momentum_long > 0.10:
            # 上涨趋势中
            if rsi > 75:
                return PHASE_PEAK
            elif momentum_short > 0.02 and rsi > 50:
                return PHASE_ACCELERATION
            elif rsi < 50:
                return PHASE_EARLY
            return PHASE_CONSOLIDATION
        
        # 盘整或启动
        if rsi < 45 and momentum_short > 0:
            return PHASE_EARLY
        elif rsi > 70:
            return PHASE_PEAK
        elif volatility < 0.01:
            return PHASE_CONSOLIDATION
        
        return PHASE_CONSOLIDATION
    
    def _estimate_cycle_completion(self, closes_4h):
        """估算周期完成度"""
        if len(closes_4h) < 20: return 0.5
        
        # 找到最近的低点和高点
        prices = closes_4h[-90:]  # 15天4h
        if len(prices) < 20: return 0.5
        
        # 简单估算: 从最近低点到现在涨了多少
        window = prices[-30:]
        min_idx = window.index(min(window))
        min_price = window[min_idx]
        current_price = window[-1]
        
        if min_price == 0: return 0.5
        
        # 估算这个周期可能的最大涨幅 (用历史波动率)
        volatility = get_volatility(prices)
        estimated_max = min_price * (1 + volatility * 5)  # 假设5倍波动率
        
        if estimated_max <= min_price: return 0.5
        
        completion = (current_price - min_price) / (estimated_max - min_price)
        return max(0, min(1, completion))
    
    def get_score(self):
        """获取综合评分 (0-100)"""
        phase = self.detect_phase()
        if not self.data_1h: return 50
        
        closes_1h = [d['close'] for d in self.data_1h]
        rsi = get_rsi(closes_1h)
        momentum = get_momentum(closes_1h[-24:])
        cycle_completion = self._estimate_cycle_completion(self.data_4h if self.data_4h else self.data_1h)
        
        score = 50
        
        # 阶段加分
        phase_bonus = {
            PHASE_ACCELERATION: 30,  # 加速期最加分
            PHASE_EARLY: 20,         # 启动期加分
            PHASE_CONSOLIDATION: 5,   # 盘整期微加分
            PHASE_PEAK: -10,          # 高峰期减分
            PHASE_DECLINE: -30        # 衰退期大减分
        }
        score += phase_bonus.get(phase, 0)
        
        # RSI加分 (40-60区间最好)
        if 40 <= rsi <= 60:
            score += 10
        elif rsi < 30:
            score += 15  # 超卖可能反弹
        elif rsi > 80:
            score -= 20  # 超买风险
        
        # 动量加分
        if momentum > 0.05:
            score += 15
        elif momentum > 0.02:
            score += 10
        elif momentum < -0.02:
            score -= 15
        
        # 周期完成度 (未完成更有空间)
        if cycle_completion < 0.5:
            score += 10  # 还有空间
        elif cycle_completion > 0.8:
            score -= 15  # 接近尾声
        
        return max(0, min(100, score))
    
    def should_enter(self):
        """是否应该进入"""
        phase = self.detect_phase()
        score = self.get_score()
        
        # 启动期或加速期 + 高分 = 买入信号
        if phase in [PHASE_EARLY, PHASE_ACCELERATION] and score >= 65:
            return True, score, f"进入{PHASE_NAMES[phase]}({score})"
        
        # 超卖反弹
        if phase == PHASE_DECLINE:
            closes_1h = [d['close'] for d in self.data_1h]
            rsi = get_rsi(closes_1h)
            if rsi < 35 and score >= 60:
                return True, score, f"超卖反弹({rsi:.0f})"
        
        return False, score, f"{PHASE_NAMES[phase]}({score})"
    
    def should_exit(self, entry_price):
        """是否应该退出 (相对于入场价)"""
        if not self.data_1h: return False, 0, ""
        
        current_price = self.data_1h[-1]['close']
        pnl_pct = (current_price - entry_price) / entry_price
        
        phase = self.detect_phase()
        closes_1h = [d['close'] for d in self.data_1h]
        rsi = get_rsi(closes_1h)
        cycle_completion = self._estimate_cycle_completion(self.data_4h if self.data_4h else self.data_1h)
        
        # 止盈: 高峰期 + 已完成大部分周期
        if phase == PHASE_PEAK and cycle_completion > 0.7 and pnl_pct > 0.05:
            return True, pnl_pct, f"高峰止盈({pnl_pct:.1%})"
        
        # 止损
        if pnl_pct <= -0.05:
            return True, pnl_pct, f"止损({pnl_pct:.1%})"
        
        # 追踪止盈
        if pnl_pct > 0.10:
            # 从高点回撤8%止盈
            highs = [d['high'] for d in self.data_1h[-24:]]
            max_high = max(highs)
            drawdown = (max_high - current_price) / max_high
            if drawdown > 0.08:
                return True, pnl_pct, f"追踪止盈({pnl_pct:.1%})"
        
        # 衰退期强制退出
        if phase == PHASE_DECLINE and pnl_pct > 0:
            return True, pnl_pct, f"衰退退出({pnl_pct:.1%})"
        
        return False, pnl_pct, f"持有中({pnl_pct:+.1%})"

# ============ 撞球策略主类 ============

class PoolStrategy:
    """撞球策略管理器"""
    
    def __init__(self):
        self.positions = {}      # 当前持仓 {coin: {'entry': price, 'entry_time': timestamp}}
        self.last_switch = {}     # 上次切换时间 {coin: timestamp}
        self.scan_count = 0
        self.total_pnl = 0
        self.history = deque(maxlen=100)  # 交易历史
        
        self.log_file = "/home/goose/.openclaw/workspace/logs/go_pool.log"
    
    def log(self, msg, level="INFO"):
        ts = datetime.now().strftime("%m-%d %H:%M:%S")
        print(f"[{ts}] [{level}] {msg}")
        with open(self.log_file, "a") as f:
            f.write(f"[{ts}] [{level}] {msg}\n")
    
    def get_account(self):
        """获取账户信息"""
        try:
            data = api_signed_get("/api/v3/account")
            result = {'usdt': 0, 'coins': {}}
            if data and 'balances' in data:
                for b in data.get('balances', []):
                    free = float(b.get('free', 0))
                    if free > 0.0001:
                        if b['asset'] == 'USDT':
                            result['usdt'] = free
                        else:
                            result['coins'][b['asset']] = free
            return result
        except Exception as e:
            self.log(f"获取账户失败: {e}", "ERROR")
            return {'usdt': 0, 'coins': {}}
    
    def get_total_value(self, balances):
        total = balances['usdt']
        for coin, qty in balances['coins'].items():
            price = get_price(f"{coin}USDT")
            if price > 0:
                total += qty * price
        return total
    
    def format_qty(self, coin, qty):
        if qty <= 0: return 0
        symbol = f"{coin}USDT"
        try:
            info = api_get(f'https://api.binance.com/api/v3/exchangeInfo?symbol={symbol}')
            if info and 'symbols' in info:
                sym = info['symbols'][0]
                filters = {f['filterType']: f for f in sym['filters']}
                lot_size = filters.get('LOT_SIZE', {})
                step_size = float(lot_size.get('stepSize', 1.0))
                min_qty = float(lot_size.get('minQty', 0))
                precision = 0
                if step_size < 1:
                    precision = len(str(step_size).split('.')[-1].rstrip('0'))
                formatted = math.floor(qty / step_size) * step_size
                formatted = round(formatted, precision) if precision > 0 else int(formatted)
                if formatted < min_qty: return 0
                return formatted
        except: pass
        return math.floor(qty)
    
    def place_order(self, symbol, side, quantity):
        try:
            ts = int(time.time() * 1000)
            q = f"timestamp={ts}&recvWindow=5000&symbol={symbol}&side={side}&type=MARKET&quantity={quantity}"
            sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
            url = f"https://api.binance.com/api/v3/order?{q}&signature={sig}"
            req = urllib.request.Request(url, method="POST")
            req.add_header('X-MBX-APIKEY', API_KEY)
            proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
            opener = urllib.request.build_opener(proxy_handler)
            result = json.loads(opener.open(req, timeout=15).read().decode())
            if 'orderId' in result:
                self.log(f"订单成功: {side} {quantity} {symbol}", "TRADE")
                return result
        except Exception as e:
            self.log(f"下单失败: {e}", "ERROR")
        return None
    
    def buy_coin(self, coin, total_value):
        """买入币种"""
        symbol = f"{coin}USDT"
        price = get_price(symbol)
        if price <= 0: return False
        
        # Kelly仓位计算
        analyzer = CycleAnalyzer(coin)
        phase = analyzer.detect_phase()
        score = analyzer.get_score()
        
        if phase == PHASE_ACCELERATION:
            position_pct = KELLY_BASE * 1.5
        elif phase == PHASE_EARLY:
            position_pct = KELLY_BASE * 1.2
        else:
            position_pct = KELLY_BASE
        
        position_value = total_value * position_pct
        quantity = position_value / price
        quantity = self.format_qty(coin, quantity)
        
        if quantity * price < 1: return False
        
        result = self.place_order(symbol, "BUY", quantity)
        if result:
            self.positions[coin] = {
                'entry': price,
                'entry_time': time.time(),
                'phase': phase,
                'score': score
            }
            self.last_switch[coin] = time.time()
            self.history.append({
                'coin': coin,
                'action': 'BUY',
                'price': price,
                'quantity': quantity,
                'time': time.time()
            })
            return True
        return False
    
    def sell_coin(self, coin, reason=""):
        """卖出币种"""
        symbol = f"{coin}USDT"
        price = get_price(symbol)
        if price <= 0: return False
        
        balances = self.get_account()
        qty = balances['coins'].get(coin, 0)
        if qty <= 0: return False
        
        quantity = self.format_qty(coin, qty)
        if quantity * price < 1: return False
        
        result = self.place_order(symbol, "SELL", quantity)
        if result and coin in self.positions:
            entry = self.positions[coin]['entry']
            pnl = (price - entry) / entry * 100
            self.log(f"卖出{coin}: {reason} 盈亏{pnl:+.2f}%", "TRADE")
            self.history.append({
                'coin': coin,
                'action': 'SELL',
                'price': price,
                'quantity': quantity,
                'pnl': pnl,
                'reason': reason,
                'time': time.time()
            })
            del self.positions[coin]
            return True
        return False
    
    def scan_and_decide(self):
        """扫描并决策"""
        # 1. 检查现有持仓是否需要退出
        for coin in list(self.positions.keys()):
            entry_info = self.positions[coin]
            should_exit, pnl, reason = self._check_exit(coin, entry_info)
            if should_exit:
                self.sell_coin(coin, reason)
        
        # 2. 扫描候选币种
        balances = self.get_account()
        total_value = self.get_total_value(balances)
        usdt = balances['usdt']
        
        candidates = []
        for coin in ALL_COINS:
            if coin in self.positions: continue
            if coin in balances['coins']: continue  # 已有现货
            
            analyzer = CycleAnalyzer(coin)
            should_enter, score, reason = analyzer.should_enter()
            if should_enter:
                candidates.append({
                    'coin': coin,
                    'score': score,
                    'reason': reason,
                    'phase': analyzer.detect_phase()
                })
        
        # 3. 决定是否切换
        if len(self.positions) >= MAX_ACTIVE_COINS:
            return  # 已达最大持仓
        
        if not candidates:
            return  # 没有候选
        
        # 按评分排序
        candidates.sort(key=lambda x: -x['score'])
        best = candidates[0]
        
        # 检查冷却期
        if best['coin'] in self.last_switch:
            if time.time() - self.last_switch[best['coin']] < SWITCH_COOLDOWN:
                return  # 还在冷却
        
        # 买入
        if usdt >= 5:
            self.log(f"🎯 撞球买入: {best['coin']} ({best['reason']})", "INFO")
            self.buy_coin(best['coin'], total_value)
    
    def _check_exit(self, coin, entry_info):
        """检查是否退出某持仓"""
        analyzer = CycleAnalyzer(coin)
        return analyzer.should_exit(entry_info['entry'])
    
    def run(self):
        self.log("=" * 60, "INFO")
        self.log("撞球策略 Pool Strategy v1.0 启动", "INFO")
        self.log(f"目标: 连续进球，保持高资金利用率", "INFO")
        self.log("=" * 60, "INFO")
        
        while True:
            try:
                self.scan_count += 1
                ts = datetime.now().strftime("%H:%M:%S")
                self.log(f"\n{'='*60}", "INFO")
                self.log(f"扫描 #{self.scan_count} ({ts})", "INFO")
                
                balances = self.get_account()
                total_value = self.get_total_value(balances)
                self.log(f"资产: USDT={balances['usdt']:.2f} 总计=${total_value:.2f}", "INFO")
                
                # 显示持仓状态
                for coin, info in self.positions.items():
                    current_price = get_price(f"{coin}USDT")
                    if current_price > 0:
                        pnl = (current_price - info['entry']) / info['entry'] * 100
                        analyzer = CycleAnalyzer(coin)
                        phase = analyzer.detect_phase()
                        self.log(f"  {coin}: {PHASE_NAMES[phase]} {pnl:+.1%}", "INFO")
                
                # 执行撞球策略
                self.scan_and_decide()
                
                self.log(f"等待60秒...", "INFO")
                time.sleep(60)
                
            except Exception as e:
                self.log(f"错误: {e}", "ERROR")
                import traceback
                traceback.print_exc()
                time.sleep(10)

if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════╗
║     撞球策略 Pool Strategy v1.0     ║
║   连续进球，资金轮转，收益最大化      ║
╚══════════════════════════════════════════════╝
    """)
    
    strategy = PoolStrategy()
    try:
        strategy.run()
    except KeyboardInterrupt:
        print("\n停止撞球策略...")
    except Exception as e:
        strategy.log(f"FATAL: {e}", "ERROR")
