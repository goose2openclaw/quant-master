#!/usr/bin/env python3
"""
G39 - 全集成自主量化交易系统
===================
整合 G38 + 轮动 + 多空 + ETF流动性 + 资产管理的超级系统
"""

import json
import time
import math
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import deque

# ============ 配置 ============


# ============ 智能资产管理配置 ============
MIN_USDT_RESERVE = 5.0        # 最低USDT储备
AUTO_CONVERT_THRESHOLD = 1.0  # 小于此金额自动转换
CONVERT_COOLDOWN = 300         # 转换冷却时间(秒)
USE_CROSS_MARGIN = True        # USDT不足时使用全仓杠杆
MIN_TRADE_VALUE = 1.0          # 最小交易价值$

# 币种流动性评分 (用于决策)
LIQUIDITY_SCORE = {
    'BTC': 100, 'ETH': 95, 'BNB': 90, 'SOL': 85, 
    'XRP': 80, 'ADA': 75, 'DOT': 70, 'LINK': 65,
    'DOGE': 60, 'SHIB': 30, 'PEPE': 25, 'BONK': 25,
    'FLOKI': 20, 'NEIRO': 15, 'BOME': 20, 'TURBO': 15
}

# ============ 智能资产管理类 ============
class AssetManager:
    """智能资产管理 - 自动转换、调配、预警"""
    
    def __init__(self, g39):
        self.g39 = g39
        self.last_convert_time = 0
        self.convert_history = []
        self.min_usdt = MIN_USDT_RESERVE
    
    def get_spot_usdt(self) -> float:
        """获取现货USDT余额"""
        try:
            account = self.g39._api_signed("/api/v3/account")
            for b in account.get('balances', []):
                if b['asset'] == 'USDT':
                    return float(b.get('free', 0))
        except:
            pass
        return 0
    
    def get_all_holdings(self) -> dict:
        """获取所有持仓"""
        holdings = {}
        try:
            account = self.g39._api_signed("/api/v3/account")
            for b in account.get('balances', []):
                free = float(b.get('free', 0))
                locked = float(b.get('locked', 0))
                total = free + locked
                if total > 0.0001:
                    holdings[b['asset']] = {
                        'free': free, 'locked': locked, 'total': total
                    }
        except:
            pass
        return holdings
    
    def get_price_dict(self) -> dict:
        """获取所有相关币种价格"""
        prices = {}
        for sym in ['BTC', 'ETH', 'BNB', 'XRP', 'ADA', 'SOL', 'DOT', 'LINK', 
                    'DOGE', 'SHIB', 'PEPE', 'BONK', 'FLOKI', 'NEIRO', 'BOME', 'TURBO', 'LTC', 'ETC']:
            try:
                d = api_pub(f'https://api.binance.com/api/v3/ticker/price?symbol={sym}USDT')
                prices[sym] = float(d['price']) if d else 0
            except:
                prices[sym] = 0
        return prices
    
    def auto_convert_small_holdings(self) -> dict:
        """自动转换小额持仓为USDT"""
        result = {'converted': [], 'total': 0, 'success': True}
        
        # 检查冷却时间
        if time.time() - self.last_convert_time < CONVERT_COOLDOWN:
            return result
        
        usdt = self.get_spot_usdt()
        if usdt >= self.min_usdt:
            return result
        
        holdings = self.get_all_holdings()
        prices = self.get_price_dict()
        
        for asset, data in holdings.items():
            if asset == 'USDT':
                continue
            
            if asset in prices and prices[asset] > 0:
                value = data['total'] * prices[asset]
                
                # 小额持仓才转换 (避免大额转换损失)
                if value < 10 and value > AUTO_CONVERT_THRESHOLD:
                    try:
                        # 市价卖出入USDT
                        order = place_order(asset, "SELL", data['total'])
                        if order.get('success'):
                            result['converted'].append({
                                'asset': asset, 'amount': data['total'], 'value': value
                            })
                            result['total'] += value
                            self.g39.log(f"自动转换 {asset}: {data['total']:.4f} = ${value:.2f}", "INFO")
                    except Exception as e:
                        self.g39.log(f"转换失败 {asset}: {e}", "ERROR")
        
        if result['converted']:
            self.last_convert_time = time.time()
            self.convert_history.append(result)
        
        return result
    
    def get_trade_budget(self, confidence: float, signal_strength: float) -> float:
        """根据信号强度和信心度计算交易预算"""
        usdt = self.get_spot_usdt()
        
        # 基础预算
        budget = usdt * KELLY_BASE * confidence
        
        # 信号强度加成
        if signal_strength > 0.2:
            budget *= 1.2
        elif signal_strength > 0.15:
            budget *= 1.1
        
        # 确保最低交易额
        if budget < MIN_TRADE_VALUE:
            return 0
        
        return min(budget, usdt * 0.5)  # 最多用50%的USDT
    
    def should_use_margin(self, required: float) -> bool:
        """判断是否应该使用全仓杠杆"""
        if not USE_CROSS_MARGIN:
            return False
        
        usdt = self.get_spot_usdt()
        
        # USDT不足且需要使用杠杆
        if required > usdt and usdt >= MIN_TRADE_VALUE:
            # 检查全仓杠杆是否有多余USDT
            try:
                cross_data = self.g39._api_signed("/sapi/v1/margin/account")
                for a in cross_data.get('userAssets', []):
                    if a['asset'] == 'USDT':
                        net = float(a.get('netAsset', 0))
                        if net > required * 2:  # 杠杆有足够USDT
                            return True
            except:
                pass
        
        return False
    
    def execute_with_smarter_logic(self, signal) -> dict:
        """智能执行交易 - 考虑所有因素"""
        symbol = signal.symbol
        price = get_price(symbol)
        
        if price <= 0:
            return {"action": "error", "reason": "获取价格失败"}
        
        # 计算所需金额
        usdt = self.get_spot_usdt()
        min_order = max(MIN_TRADE_VALUE, price * 100)  # 至少价值$1
        
        if usdt < min_order:
            # 尝试自动转换
            self.auto_convert_small_holdings()
            usdt = self.get_spot_usdt()
        
        if usdt < min_order and self.should_use_margin(min_order):
            # 使用全仓杠杆
            self.g39.log(f"使用全仓杠杆交易 {symbol}", "INFO")
            return self._execute_via_margin(signal, price, usdt)
        
        if usdt < min_order:
            return {"action": "skip", "reason": f"资金不足(需要${min_order:.2f}, 只有${usdt:.2f})"}
        
        # 正常现货交易
        budget = self.get_trade_budget(signal.confidence, abs(signal.signal))
        quantity = budget / price
        
        if quantity <= 0:
            return {"action": "skip", "reason": "计算数量为0"}
        
        quantity = format_quantity(symbol, quantity)
        order_value = quantity * price
        
        if order_value < MIN_TRADE_VALUE:
            return {"action": "skip", "reason": f"订单价值${order_value:.2f}低于最低${MIN_TRADE_VALUE}"}
        
        result = place_order(symbol, "BUY", quantity)
        if result.get('success'):
            self.g39.log(f"✅ 智能买入 {symbol}: {quantity} @ {price}", "INFO")
        
        return result
    
    def _execute_via_margin(self, signal, price, spot_usdt) -> dict:
        """通过全仓杠杆执行"""
        symbol = signal.symbol
        
        # 从全仓借USDT
        try:
            # 计算杠杆交易数量
            margin_budget = spot_usdt * 3  # 3倍杠杆
            quantity = margin_budget / price
            quantity = format_quantity(symbol, quantity)
            
            # 执行市价单
            result = place_order(symbol, "BUY", quantity)
            if result.get('success'):
                self.g39.log(f"✅ 杠杆买入 {symbol}: {quantity} @ {price} (3x)", "INFO")
            return result
        except Exception as e:
            return {"action": "error", "reason": f"杠杆交易失败: {e}"}


API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

STATE_FILE = "/home/goose/.openclaw/workspace/.g39_state.json"
LOG_FILE = "/home/goose/.openclaw/workspace/logs/g39.log"

SCAN_INTERVAL = 30
STOP_LOSS = 0.05
TAKE_PROFIT = 0.20
KELLY_BASE = 0.30
MAX_POSITIONS = 3

MAINSTREAM = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOT']
MEME = ['PEPE', 'BONK', 'DOGE', 'SHIB', 'FLOKI', 'BOME', 'TURBO', 'NEIRO']

# ============ API工具 ============

def api_signed(endpoint: str, params: dict = None, method: str = "GET") -> dict:
    for i in range(3):
        try:
            import hmac, hashlib, urllib.request
            ts = int(time.time() * 1000)
            base = {"timestamp": ts, "recvWindow": 5000}
            if params: base.update(params)
            q = "&".join(f"{k}={v}" for k, v in sorted(base.items()))
            sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
            url = f"https://api.binance.com{endpoint}?{q}&signature={sig}"
            req = urllib.request.Request(url, method=method)
            req.add_header('X-MBX-APIKEY', API_KEY)
            proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
            opener = urllib.request.build_opener(proxy_handler)
            return json.loads(opener.open(req, timeout=15).read().decode())
        except:
            if i < 2: time.sleep(0.3)
    return {}

def api_pub(url: str) -> dict:
    import urllib.request
    import sys
    try:
        proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
        opener = urllib.request.build_opener(proxy_handler)
        http_resp = opener.open(urllib.request.Request(url), timeout=10)
        resp = http_resp.read().decode()
        result = json.loads(resp)
        return result
    except urllib.error.HTTPError as e:
        print(f"api_pub HTTPError for {url}: {e.code} {e.reason}", file=sys.stderr)
        try:
            err_body = e.read().decode()
            print(f"Error body: {err_body}", file=sys.stderr)
        except: pass
        return {}
    except Exception as e:
        print(f"api_pub exception for {url}: {type(e).__name__}: {e}", file=sys.stderr)
        return {}

import urllib.request

def get_price(symbol: str) -> float:
    try:
        url = f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT'
        data = api_pub(url)
        if not data:
            print(f"get_price: no data for {symbol}")
            return 0
        if 'price' not in data:
            print(f"get_price: no price key in data for {symbol}: {data}")
            return 0
        return float(data['price'])
    except Exception as e:
        print(f"get_price error for {symbol}: {e}")
        return 0

def get_klines(symbol: str, interval: str = '1h', limit: int = 100) -> List[dict]:
    try:
        data = api_pub(f'https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval={interval}&limit={limit}')
        return [{'time': k[0], 'open': float(k[1]), 'high': float(k[2]), 'low': float(k[3]),
                 'close': float(k[4]), 'volume': float(k[5])} for k in data] if data else []
    except: return []

# ============ 数据类 ============

@dataclass
class G39Signal:
    symbol: str
    direction: str
    confidence: float
    signal: float
    strategy: str
    phase: str
    market_type: str
    stop_loss: float
    take_profit: float
    position_size: float
    top_traders: List[str]
    sources: Dict[str, float]

@dataclass
class AccountStatus:
    spot_total: float
    cross_total: float
    isolated_total: float
    futures_total: float
    grand_total: float
    spot_usdt: float

# ============ 统计分析 ============

class Statistics:
    @staticmethod
    def mean(data: List[float]) -> float:
        return sum(data) / len(data) if data else 0
    
    @staticmethod
    def std(data: List[float]) -> float:
        if len(data) < 2: return 0
        m = Statistics.mean(data)
        return math.sqrt(sum((x - m) ** 2 for x in data) / (len(data) - 1))
    
    @staticmethod
    def rsi(closes: List[float], period: int = 14) -> float:
        if len(closes) < period + 1: return 50
        deltas = [closes[i+1] - closes[i] for i in range(len(closes)-1)]
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        return 100 - (100 / (1 + avg_gain / (avg_loss + 1e-10))) if avg_loss != 0 else 100
    
    @staticmethod
    def zscore(value: float, data: List[float]) -> float:
        m = Statistics.mean(data)
        s = Statistics.std(data)
        return (value - m) / s if s > 0 else 0

# ============ Top10交易员 (来自G38) ============

TRADERS = {
    'Soros': {'weight': 0.12, 'stop_loss': 0.08, 'take_profit': 0.25, 'strategy': 'reflexivity'},
    'Druckenmiller': {'weight': 0.10, 'stop_loss': 0.06, 'take_profit': 0.20, 'strategy': 'liquidity'},
    'Marcus': {'weight': 0.15, 'stop_loss': 0.10, 'take_profit': 0.30, 'strategy': 'trend_following'},
    'Jones': {'weight': 0.12, 'stop_loss': 0.05, 'take_profit': 0.20, 'strategy': 'ma_system'},
    'Schwartz': {'weight': 0.10, 'stop_loss': 0.08, 'take_profit': 0.25, 'strategy': 'candlestick'},
    'Kovner': {'weight': 0.08, 'stop_loss': 0.05, 'take_profit': 0.18, 'strategy': 'breakout'},
    'Dennis': {'weight': 0.08, 'stop_loss': 0.05, 'take_profit': 0.15, 'strategy': 'systematic'},
    'Lipschutz': {'weight': 0.08, 'stop_loss': 0.06, 'take_profit': 0.22, 'strategy': 'trend_trade'},
    'Livermore': {'weight': 0.09, 'stop_loss': 0.07, 'take_profit': 0.25, 'strategy': 'key_reversal'},
    'Rogers': {'weight': 0.08, 'stop_loss': 0.05, 'take_profit': 0.20, 'strategy': 'trend_id'}
}

# ============ G39 主系统 ============


# ============ 交易执行模块 ============

def place_order(symbol: str, side: str, quantity: float, order_type: str = "MARKET") -> dict:
    """在 Binance 执行真实下单"""
    import hmac, hashlib, urllib.request
    for i in range(3):
        try:
            ts = int(time.time() * 1000)
            # 获取精度信息
            try:
                info = api_pub(f'https://api.binance.com/api/v3/exchangeInfo?symbol={symbol}USDT')
                if info and 'symbols' in info:
                    filters = {f['filterType']: f for f in info['symbols'][0]['filters']}
                    step = float(filters.get('LOT_SIZE', {}).get('stepSize', 1))
                    if step >= 1:
                        qty_str = f"{int(quantity)}"
                    else:
                        prec = len(str(step).split('.')[-1].rstrip('0'))
                        qty_str = f"{quantity:.{prec}f}"
                else:
                    qty_str = f"{quantity:.6f}"
            except:
                qty_str = f"{quantity:.6f}"
            
            params = {
                "symbol": f"{symbol}USDT",
                "side": side,  # BUY or SELL
                "type": order_type,
                "quantity": qty_str,
                "timestamp": ts,
                "recvWindow": 5000
            }
            q = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
            sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
            url = f"https://api.binance.com/api/v3/order?{q}&signature={sig}"
            req = urllib.request.Request(url, method="POST")
            req.add_header('X-MBX-APIKEY', API_KEY)
            proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
            opener = urllib.request.build_opener(proxy_handler)
            resp = json.loads(opener.open(req, timeout=10).read().decode())
            
            # 检查 Binance 错误响应
            if "code" in resp:
                return {"success": False, "error": f"Binance Error {resp['code']}: {resp['msg']}"}
            
            return {"success": True, "order_id": resp.get("orderId"), "status": resp.get("status")}
        except urllib.error.HTTPError as e:
            try:
                err_resp = json.loads(e.read().decode())
                return {"success": False, "error": f"HTTP {e.code}: {err_resp.get('msg', str(e))}"}
            except:
                return {"success": False, "error": f"HTTP {e.code}: {str(e)}"}
        except Exception as e:
            error_msg = str(e)
            if i < 2: time.sleep(0.5)
            if i == 2:  # Last retry
                return {"success": False, "error": error_msg}
    return {"success": False, "error": "Max retries exceeded"}

def format_quantity(symbol: str, qty: float) -> float:
    """格式化下单数量"""
    try:
        info = api_pub(f'https://api.binance.com/api/v3/exchangeInfo?symbol={symbol}USDT')
        if info and 'symbols' in info:
            filters = {f['filterType']: f for f in info['symbols'][0]['filters']}
            step = float(filters.get('LOT_SIZE', {}).get('stepSize', 1))
            min_q = float(filters.get('LOT_SIZE', {}).get('minQty', 0))
            
            # 计算精度
            if step >= 1:
                # 整数步长，直接取整
                formatted = int(qty // step)
            else:
                prec = len(str(step).split('.')[-1].rstrip('0'))
                formatted = math.floor(qty / step) * step
                formatted = round(formatted, prec)
            
            # 确保不低于最小数量
            if formatted < min_q:
                formatted = min_q
            
            return float(formatted)
        return float(int(qty))
    except Exception as e:
        print(f"format_quantity error: {e}")
        return float(int(qty))
    return math.floor(qty)

class AutoTrader:
    """自动交易执行器"""
    
    def __init__(self, g39):
        self.g39 = g39
        self.active_trades = {}  # symbol -> {entry, quantity, side}
    
    def execute_signal(self, signal) -> dict:
        """执行信号"""
        if signal.direction == 'neutral' or signal.confidence < 0.5:
            return {"action": "skip", "reason": "信号不足"}
        
        # 使用智能资产管理器
        return self.g39.asset_manager.execute_with_smarter_logic(signal)
        
        # 执行交易
        if signal.direction == "long":
            result = place_order(symbol, "BUY", quantity)
            if result.get("success"):
                self.active_trades[symbol] = {
                    "entry": price,
                    "quantity": quantity,
                    "side": "long",
                    "stop_loss": price * (1 - STOP_LOSS),
                    "take_profit": price * (1 + TAKE_PROFIT),
                    "time": time.time()
                }
                self.g39.log(f"✅ 买入 {symbol}: {quantity} @ {price}", "INFO")
        elif signal.direction == "short":
            result = place_order(symbol, "SELL", quantity)
            if result.get("success"):
                self.active_trades[symbol] = {
                    "entry": price,
                    "quantity": quantity,
                    "side": "short",
                    "stop_loss": price * (1 + STOP_LOSS),
                    "take_profit": price * (1 - TAKE_PROFIT),
                    "time": time.time()
                }
                self.g39.log(f"✅ 做空 {symbol}: {quantity} @ {price}", "INFO")
        
        return result
    
    def check_positions(self):
        """检查持仓并执行止损止盈"""
        to_close = []
        
        for symbol, pos in self.active_trades.items():
            current_price = get_price(symbol)
            if current_price <= 0: continue
            
            entry = pos["entry"]
            side = pos["side"]
            
            if side == "long":
                pnl_pct = (current_price - entry) / entry
            else:
                pnl_pct = (entry - current_price) / entry
            
            # 检查止损止盈
            if pnl_pct <= -STOP_LOSS or pnl_pct >= TAKE_PROFIT:
                to_close.append(symbol)
        
        # 平仓
        for symbol in to_close:
            pos = self.active_trades[symbol]
            side = "SELL" if pos["side"] == "long" else "BUY"
            result = place_order(symbol, side, pos["quantity"])
            if result.get("success"):
                current_price = get_price(symbol)
                if pos["side"] == "long":
                    pnl_pct = (current_price - pos["entry"]) / pos["entry"]
                else:
                    pnl_pct = (pos["entry"] - current_price) / pos["entry"]
                self.g39.log(f"平仓 {symbol}: {pos['quantity']} @ {current_price} (PnL: {pnl_pct:+.2%})", "INFO")
                del self.active_trades[symbol]


class G39:
    """G39 全集成自主量化交易系统"""
    
    def __init__(self):
        self.state_file = STATE_FILE
        self.log_file = LOG_FILE
        self.positions = {}
        self.history = []
        self.is_running = False
        self.strategy_weights = self._init_weights()
        
        self.load_state()
        
        # 初始化自动交易器
        self.trader = AutoTrader(self)
        
        # 初始化智能资产管理器
        self.asset_manager = AssetManager(self)
    
    def _init_weights(self) -> Dict:
        """初始化策略权重"""
        return {
            'go-core': 0.20,
            'go-fit': 0.10,
            'go-noise': 0.08,
            'go-thermo': 0.08,
            'go-detect': 0.12,
            'go-pool': 0.15,
            'go-rotate': 0.12,
            'go-long-short': 0.15,
            'go-etf': 0.10,
            'go-ensemble': 0.05,
            'go-meta': 0.05
        }
    
    def log(self, msg: str, level: str = "INFO"):
        ts = datetime.now().strftime("%m-%d %H:%M:%S")
        line = f"[{ts}] [{level}] {msg}"
        print(line)
        try:
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
            with open(self.log_file, "a") as f:
                f.write(line + "\n")
        except: pass
    
    def load_state(self):
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file) as f:
                    state = json.load(f)
                    self.positions = state.get('positions', {})
                    self.history = state.get('history', [])
                    self.strategy_weights = state.get('weights', self.strategy_weights)
        except: pass
    
    def save_state(self):
        try:
            state = {
                'positions': self.positions,
                'history': self.history[-100:],
                'weights': self.strategy_weights,
                'timestamp': time.time()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f)
        except: pass
    
    # ============ 各模块信号 ============
    
    def _get_go_core_signal(self, symbol: str) -> Dict:
        """go-core 核心预测"""
        klines = get_klines(symbol, '1h', 100)
        if not klines: return {'signal': 0, 'confidence': 0.5}
        
        closes = [k['close'] for k in klines]
        mom = (closes[-1] - closes[-24]) / closes[-24] if len(closes) >= 24 else 0
        mom_long = (closes[-1] - closes[-168]) / closes[-168] if len(closes) >= 168 else mom
        
        signal = max(-1, min(1, mom_long * 5))
        confidence = abs(signal) * 0.8 + 0.2
        
        return {'signal': signal, 'confidence': confidence}
    
    def _get_go_fit_signal(self, symbol: str) -> Dict:
        """go-fit 趋势拟合"""
        klines = get_klines(symbol, '1h', 50)
        if not klines: return {'signal': 0, 'confidence': 0.5}
        
        closes = [k['close'] for k in klines]
        trend = (closes[-1] - closes[0]) / (max(closes) - min(closes) + 1e-10)
        aligns = sum(1 for i in range(1, len(closes)) if (closes[i] - closes[i-1]) > 0)
        persistence = aligns / (len(closes) - 1) if len(closes) > 1 else 0.5
        
        score = (trend + 1) / 2 * persistence
        return {'signal': (score - 0.5) * 2, 'confidence': 0.5 + persistence * 0.3}
    
    def _get_go_noise_signal(self, symbol: str) -> Dict:
        """go-noise 噪音过滤"""
        klines = get_klines(symbol, '1h', 50)
        if not klines: return {'signal': 0, 'confidence': 0.5}
        
        closes = [k['close'] for k in klines]
        returns = [math.log(closes[i]/closes[i-1]) for i in range(1, len(closes))]
        variance = sum((r - sum(returns)/len(returns))**2 for r in returns) / len(returns) if returns else 0
        noise_ratio = min(1, variance * 100)
        filtered = noise_ratio < 0.3
        
        return {'signal': -noise_ratio if filtered else noise_ratio * 0.5, 'confidence': 1 - noise_ratio}
    
    def _get_go_thermo_signal(self, symbol: str) -> Dict:
        """go-thermo 热力分析"""
        klines = get_klines(symbol, '1h', 100)
        if not klines: return {'signal': 0, 'confidence': 0.5, 'phase': 'normal'}
        
        closes = [k['close'] for k in klines]
        returns = [(closes[i]-closes[i-1])/closes[i-1] for i in range(1, len(closes))]
        volatility = math.sqrt(sum(r**2 for r in returns) / len(returns)) if returns else 0
        trend = (closes[-1] - closes[0]) / closes[0] if closes[0] > 0 else 0
        temp = volatility / (abs(trend) + 0.01)
        
        phase = 'hot' if temp > 1 else 'cold' if temp < 0.5 else 'normal'
        signal = (1 - min(1, temp)) if phase == 'cold' else -(min(1, temp) - 0.5)
        
        return {'signal': signal, 'confidence': 0.6, 'phase': phase, 'temperature': temp}
    
    def _get_go_detect_signal(self, symbol: str) -> Dict:
        """go-detect 机构侦测"""
        klines = get_klines(symbol, '1h', 50)
        if not klines: return {'signal': 0, 'confidence': 0.5}
        
        volumes = [k['volume'] for k in klines]
        closes = [k['close'] for k in klines]
        
        avg_vol = sum(volumes) / len(volumes) if volumes else 0
        recent_vol = volumes[-1] if volumes else avg_vol
        vol_ratio = recent_vol / avg_vol if avg_vol > 0 else 1
        
        price_change = (closes[-1] - closes[-5]) / closes[-5] if len(closes) >= 5 else 0
        
        pressure = vol_ratio * abs(price_change) * 10
        direction = 'long' if price_change > 0 else 'short' if price_change < 0 else 'neutral'
        
        return {'signal': pressure if direction == 'long' else -pressure, 'confidence': min(1, pressure), 'direction': direction}
    
    def _get_go_pool_signal(self, symbol: str) -> Dict:
        """go-pool 撞球策略"""
        klines = get_klines(symbol, '1h', 100)
        if not klines: return {'signal': 0, 'confidence': 0.5, 'phase': 'consolidation'}
        
        closes = [k['close'] for k in klines]
        rsi = Statistics.rsi(closes)
        mom = (closes[-1] - closes[-24]) / closes[-24] if len(closes) >= 24 else 0
        mom_long = (closes[-1] - closes[-168]) / closes[-168] if len(closes) >= 168 else mom
        
        # 阶段判断
        if mom_long < -0.08: phase = "decline"
        elif mom_long > 0.15:
            phase = "peak" if rsi > 75 else "acceleration" if mom > 0.03 and rsi > 55 else "startup"
        elif rsi > 72: phase = "peak"
        elif mom > 0.025 and rsi > 50: phase = "acceleration"
        elif rsi < 45 and mom > 0: phase = "startup"
        else: phase = "consolidation"
        
        phase_signals = {"acceleration": 0.8, "startup": 0.5, "consolidation": 0, "peak": -0.5, "decline": -0.8}
        
        return {'signal': phase_signals.get(phase, 0), 'confidence': 0.6, 'phase': phase}
    
    def _get_go_rotate_signal(self, symbol: str) -> Dict:
        """go-rotate 轮动策略"""
        klines = get_klines(symbol, '5m', 100)
        if not klines: return {'signal': 0, 'confidence': 0.5, 'action': 'hold'}
        
        closes = [k['close'] for k in klines]
        current_price = closes[-1]
        mean_price = Statistics.mean(closes)
        std_price = Statistics.std(closes)
        zscore = (current_price - mean_price) / std_price if std_price > 0 else 0
        rsi = Statistics.rsi(closes)
        
        if zscore < -1.5 or rsi < 35:
            action = 'buy'
            confidence = min(1, abs(zscore) / 2)
        elif zscore > 1.5 or rsi > 65:
            action = 'sell'
            confidence = min(1, zscore / 2)
        else:
            action = 'hold'
            confidence = 0.5
        
        signal = 0.5 if action == 'buy' else -0.5 if action == 'sell' else 0
        
        return {'signal': signal, 'confidence': confidence, 'action': action, 'zscore': zscore}
    
    def _get_go_long_short_signal(self, symbol: str) -> Dict:
        """go-long-short 多空策略"""
        klines = get_klines(symbol, '1h', 100)
        if not klines: return {'signal': 0, 'confidence': 0.5, 'direction': 'neutral'}
        
        closes = [k['close'] for k in klines]
        rsi = Statistics.rsi(closes)
        mom = (closes[-1] - closes[-24]) / closes[-24] if len(closes) >= 24 else 0
        
        # 多空判断
        if rsi < 40 and mom > 0: direction = 'long'
        elif rsi > 60 and mom < 0: direction = 'short'
        else: direction = 'neutral'
        
        signal = 0.6 if direction == 'long' else -0.6 if direction == 'short' else 0
        
        return {'signal': signal, 'confidence': 0.7, 'direction': direction}
    
    def _get_go_etf_signal(self, symbol: str) -> Dict:
        """go-etf-liquidity ETF流动性"""
        klines = get_klines(symbol, '1h', 100)
        if not klines: return {'signal': 0, 'confidence': 0.5, 'direction': 'neutral'}
        
        closes = [k['close'] for k in klines]
        volumes = [k['volume'] for k in klines]
        
        # 模拟ETF信号
        mom = (closes[-1] - closes[-24]) / closes[-24] if len(closes) >= 24 else 0
        vol_ratio = volumes[-1] / (sum(volumes) / len(volumes)) if volumes else 1
        
        signal = mom * 3
        direction = 'bullish' if signal > 0.2 else 'bearish' if signal < -0.2 else 'neutral'
        
        return {'signal': signal, 'confidence': 0.65, 'direction': direction}
    
    def _get_top10_trader_signal(self, symbol: str) -> Tuple[float, List[str]]:
        """Top10交易员信号"""
        klines = get_klines(symbol, '1h', 100)
        if not klines: return 0, []
        
        closes = [k['close'] for k in klines]
        rsi = Statistics.rsi(closes)
        mom = (closes[-1] - closes[-24]) / closes[-24] if len(closes) >= 24 else 0
        
        trader_signals = {}
        
        for name, trader in TRADERS.items():
            signal = 0
            if trader['strategy'] == 'trend_following':
                signal = min(1, mom * 10) if mom > 0 else max(-1, mom * 10)
            elif trader['strategy'] == 'candlestick':
                signal = 0.6 if rsi < 35 else -0.5 if rsi > 65 else 0
            elif trader['strategy'] == 'breakout':
                high_20 = max(closes[-20:]) if len(closes) >= 20 else max(closes)
                low_20 = min(closes[-20:]) if len(closes) >= 20 else min(closes)
                signal = 0.6 if closes[-1] >= high_20 else -0.6 if closes[-1] <= low_20 else 0
            else:
                signal = mom * 5
            
            trader_signals[name] = signal * trader['weight']
        
        combined = sum(trader_signals.values())
        top_traders = sorted(trader_signals.items(), key=lambda x: abs(x[1]), reverse=True)[:3]
        
        return combined, [t[0] for t in top_traders]
    
    # ============ 综合分析 ============
    
    def analyze(self, symbol: str) -> G39Signal:
        """完整分析"""
        # 获取各模块信号
        signals = {
            'go-core': self._get_go_core_signal(symbol),
            'go-fit': self._get_go_fit_signal(symbol),
            'go-noise': self._get_go_noise_signal(symbol),
            'go-thermo': self._get_go_thermo_signal(symbol),
            'go-detect': self._get_go_detect_signal(symbol),
            'go-pool': self._get_go_pool_signal(symbol),
            'go-rotate': self._get_go_rotate_signal(symbol),
            'go-long-short': self._get_go_long_short_signal(symbol),
            'go-etf': self._get_go_etf_signal(symbol)
        }
        
        # Top10交易员
        trader_signal, top_traders = self._get_top10_trader_signal(symbol)
        signals['top10'] = {'signal': trader_signal, 'confidence': 0.7}
        
        # 综合评分
        weights = {**self.strategy_weights, 'top10': 0.15}
        
        combined_signal = 0
        combined_confidence = 0
        total_weight = 0
        sources = {}
        
        for name, w in weights.items():
            if name in signals:
                s = signals[name]['signal']
                c = signals[name].get('confidence', 0.5)
                combined_signal += s * w
                combined_confidence += c * w
                sources[name] = s * w
                total_weight += w
        
        combined_signal /= total_weight
        combined_confidence /= total_weight
        
        # 市场类型
        pool = signals['go-pool']
        market_type = 'trending' if abs(combined_signal) > 0.3 and pool['phase'] in ['acceleration', 'decline'] else 'ranging'
        
        # 策略选择
        if market_type == 'trending':
            strategy = 'pool_long' if combined_signal > 0 else 'pool_short'
        else:
            strategy = 'rotate' if signals['go-rotate']['action'] != 'hold' else 'neutral'
        
        # 方向判断
        if combined_signal > 0.08: direction = 'long'
        elif combined_signal < -0.08: direction = 'short'
        else: direction = 'neutral'
        
        # 仓位
        position_size = KELLY_BASE if direction != 'neutral' else 0
        
        return G39Signal(
            symbol=symbol,
            direction=direction,
            confidence=min(1, abs(combined_confidence)),
            signal=combined_signal,
            strategy=strategy,
            phase=pool['phase'],
            market_type=market_type,
            stop_loss=STOP_LOSS,
            take_profit=TAKE_PROFIT,
            position_size=position_size,
            top_traders=top_traders,
            sources=sources
        )
    
    def batch_analyze(self, symbols: List[str]) -> List[G39Signal]:
        """批量分析"""
        return [self.analyze(s) for s in symbols]
    
    def get_account_status(self) -> AccountStatus:
        """获取四大账户状态"""
        def get_price(symbol):
            try:
                url = f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}'
                proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
                opener = urllib.request.build_opener(proxy_handler)
                data = json.loads(opener.open(urllib.request.Request(url), timeout=5).read().decode())
                return float(data['price'])
            except: return 0
        
        # 现货账户
        spot_data = self._api_signed("/api/v3/account")
        spot_usdt = 0
        spot_total = 0
        positions = {}
        
        if spot_data and 'balances' in spot_data:
            for b in spot_data.get('balances', []):
                free = float(b.get('free', 0))
                if free > 0.0001:
                    asset = b['asset']
                    if asset == 'USDT':
                        spot_usdt = free
                        spot_total += free
                    else:
                        price = get_price(f"{asset}USDT")
                        value = free * price
                        spot_total += value
                        if value > 1:
                            positions[asset] = {'amount': free, 'value': value, 'account': 'spot'}
        
        # 全仓杠杆账户
        cross_total = 0
        cross_data = self._api_signed("/sapi/v1/margin/account")
        if cross_data and 'userAssets' in cross_data:
            for a in cross_data.get('userAssets', []):
                net = float(a.get('netAsset', 0))
                if net != 0:
                    asset = a['asset']
                    if asset == 'BTC':
                        cross_total += net * get_price('BTCUSDT')
                    elif asset == 'USDT':
                        cross_total += net
                    else:
                        price = get_price(f"{asset}USDT")
                        cross_total += net * price if price > 0 else 0
        
        # 逐仓杠杆账户
        isolated_total = 0
        isolated_data = self._api_signed("/sapi/v1/margin/isolated/account")
        if isolated_data and 'assets' in isolated_data:
            for pair in isolated_data.get('assets', []):
                base = pair.get('baseAsset', {})
                quote = pair.get('quoteAsset', {})
                net_base = float(base.get('netAsset', 0))
                net_quote = float(quote.get('netAsset', 0))
                if net_base != 0 or net_quote != 0:
                    if base.get('asset') == 'BTC':
                        isolated_total += net_base * get_price('BTCUSDT')
                    elif quote.get('asset') == 'USDT':
                        isolated_total += abs(net_quote)
                    else:
                        if net_base != 0:
                            price = get_price(f"{base.get('asset')}USDT")
                            isolated_total += net_base * price if price > 0 else 0
        
        # 合约账户 (USDT-M)
        futures_total = 0
        futures_data = self._api_signed("/fapi/v2/account")
        if futures_data and 'error' not in futures_data:
            try:
                futures_total = float(futures_data.get('totalMarginBalance', 0))
            except:
                futures_total = 0
        
        grand_total = spot_total + cross_total + isolated_total + futures_total
        
        return AccountStatus(
            spot_total=spot_total,
            cross_total=cross_total,
            isolated_total=isolated_total,
            futures_total=futures_total,
            grand_total=grand_total,
            spot_usdt=spot_usdt
        )
    
    def _api_signed(self, endpoint, params=None):
        """签名API请求 - 调用全局api_signed"""
        return api_signed(endpoint, params)
    
    def run(self):
        """主运行循环"""
        self.log("=" * 60)
        self.log("G39 全集成系统启动", "INFO")
        self.log("=" * 60)
        
        self.is_running = True
        
        while self.is_running:
            try:
                # 账户状态
                status = self.get_account_status()
                
                self.log(f"\n{'='*60}")
                self.log(f"📊 G39 账户状态", "INFO")
                self.log(f"{'='*60}")
                self.log(f"现货: ${status.spot_total:.2f}", "INFO")
                self.log(f"全仓杠杆: ${status.cross_total:.2f}", "INFO")
                self.log(f"合约: ${status.futures_total:.2f}", "INFO")
                self.log(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "INFO")
                self.log(f"总资产: ${status.grand_total:.2f}", "INFO")
                
                # 分析
                all_symbols = MAINSTREAM + MEME
                results = self.batch_analyze(all_symbols)
                
                # 过滤有效信号
                valid = [r for r in results if r.direction != 'neutral' and r.confidence > 0.5]
                valid.sort(key=lambda x: -x.confidence)
                
                self.log(f"\n📈 Top信号:", "INFO")
                for r in valid[:5]:
                    self.log(f"  {r.symbol}: {r.direction} {r.confidence:.0%} [{r.strategy}] ({', '.join(r.top_traders[:2])})", "INFO")
                
                # 检查持仓止损止盈
                self.trader.check_positions()
                
                # 执行最佳信号 (前先检查资产)
                if valid:
                    best = valid[0]
                    self.log(f"最佳信号: {best.symbol} {best.direction} {best.confidence:.0%} signal={best.signal:.3f}", "INFO")
                    
                    # 自动转换小额持仓
                    self.asset_manager.auto_convert_small_holdings()
                    
                    if best.direction != "neutral" and best.confidence > 0.5:
                        result = self.trader.execute_signal(best)
                        if result.get("action") == "skip":
                            self.log(f"跳过 {best.symbol}: {result.get('reason')}", "INFO")
                        elif result.get("action") == "error":
                            self.log(f"错误 {best.symbol}: {result.get('reason')}", "ERROR")
                        elif result.get("success") == True:
                            self.log(f"✅ 交易成功 {best.symbol}", "INFO")
                        elif result.get("success") == False:
                            self.log(f"❌ 交易失败 {best.symbol}: {result.get('error', 'Unknown')}", "ERROR")
                        if result.get("action") == "skip":
                            self.log(f"跳过 {best.symbol}: {result.get('reason')}", "INFO")
                
                self.save_state()
                time.sleep(SCAN_INTERVAL)
                
            except Exception as e:
                self.log(f"错误: {e}", "ERROR")
                import traceback; traceback.print_exc()
                time.sleep(10)
    
    def stop(self):
        self.is_running = False

def main():
    g = G39()
    try:
        g.run()
    except KeyboardInterrupt:
        g.stop()

if __name__ == "__main__":
    main()

# ============ 自主优化模块 ============

class G39Optimizer:
    """G39 自主优化器"""
    
    def __init__(self, g39):
        self.g39 = g39
        self.strategy_performance = {name: {'wins': 0, 'losses': 0, 'returns': []} for name in g39.strategy_weights.keys()}
        self.trade_history = deque(maxlen=500)
        self.optimizer_cooldown = 3600  # 1小时优化一次
    
    def record_trade(self, strategy: str, pnl: float, market_type: str):
        """记录交易结果"""
        self.trade_history.append({
            'strategy': strategy,
            'pnl': pnl,
            'market_type': market_type,
            'time': time.time()
        })
        
        if pnl > 0:
            self.strategy_performance[strategy]['wins'] += 1
        else:
            self.strategy_performance[strategy]['losses'] += 1
        
        self.strategy_performance[strategy]['returns'].append(pnl)
        
        # 只保留最近100条记录
        if len(self.strategy_performance[strategy]['returns']) > 100:
            self.strategy_performance[strategy]['returns'] = self.strategy_performance[strategy]['returns'][-100:]
    
    def optimize_weights(self):
        """优化策略权重"""
        now = time.time()
        if hasattr(self, 'last_optimize') and now - self.last_optimize < self.optimizer_cooldown:
            return  # 冷却中
        
        self.last_optimize = now
        
        print("\n=== 自主优化 ===")
        
        for name in self.g39.strategy_weights:
            perf = self.strategy_performance[name]
            total = perf['wins'] + perf['losses']
            
            if total < 10:
                continue  # 数据不足
            
            win_rate = perf['wins'] / total
            returns = perf['returns']
            avg_return = sum(returns) / len(returns) if returns else 0
            
            old_weight = self.g39.strategy_weights[name]
            
            # 优化规则
            if win_rate < 0.4 or avg_return < -0.05:
                # 表现差，降低权重
                new_weight = old_weight * 0.8
                reason = f"表现差(胜率{win_rate:.0%}, 均收益{avg_return:+.1%})"
            elif win_rate > 0.6 and avg_return > 0.05:
                # 表现好，提高权重
                new_weight = old_weight * 1.1
                reason = f"表现好(胜率{win_rate:.0%}, 均收益{avg_return:+.1%})"
            else:
                new_weight = old_weight
                reason = "表现中等"
            
            # 限制范围
            new_weight = max(0.05, min(0.30, new_weight))
            
            if abs(new_weight - old_weight) > 0.01:
                self.g39.strategy_weights[name] = new_weight
                print(f"  {name}: {old_weight:.2f} → {new_weight:.2f} ({reason})")
        
        # 归一化
        total = sum(self.g39.strategy_weights.values())
        for name in self.g39.strategy_weights:
            self.g39.strategy_weights[name] /= total
        
        print("=" * 30)
    
    def get_strategy_score(self, name: str) -> float:
        """获取策略评分"""
        perf = self.strategy_performance.get(name, {'wins': 0, 'losses': 0, 'returns': []})
        total = perf['wins'] + perf['losses']
        
        if total < 5:
            return 0.5  # 数据不足返回中性
        
        win_rate = perf['wins'] / total
        avg_return = sum(perf['returns']) / len(perf['returns']) if perf['returns'] else 0
        
        # 综合评分
        score = win_rate * 0.6 + (avg_return + 0.1) * 2 * 0.4
        
        return max(0, min(1, score))
    
    def auto_switch_strategy(self, symbol: str, market_type: str) -> str:
        """自动切换策略"""
        # 根据市场类型选择最佳策略
        if market_type == 'trending':
            candidates = ['go-pool', 'go-core', 'go-long-short']
        else:
            candidates = ['go-rotate', 'go-long-short', 'go-etf']
        
        best_strategy = None
        best_score = 0
        
        for strategy in candidates:
            score = self.get_strategy_score(strategy)
            if score > best_score:
                best_score = score
                best_strategy = strategy
        
        return best_strategy or 'go-core'
