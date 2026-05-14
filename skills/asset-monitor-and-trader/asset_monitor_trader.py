#!/usr/bin/env python3
"""
Asset Monitor and Trader
======================
资产管理与自主币种调换系统

解决顽固问题:
1. 账户丢失 (启动时API同步)
2. 无法自动恢复交易 (状态持久化)
3. 无法自主币种调换 (基于预测的比较决策)
4. 总提示转入资金 (默认使用现有资产)

四大账户:
- 现货 (SPOT)
- 全仓杠杆 (CROSS MARGIN)
- 逐仓杠杆 (ISOLATED MARGIN)
- USDT合约 (FUTURES)
"""

import urllib.request
import hmac
import hashlib
import time
import json
import math
import os
import sys
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import deque

# ============ 配置 ============

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

STATE_FILE = "/home/goose/.openclaw/workspace/.asset_monitor_state.json"
LOG_FILE = "/home/goose/.openclaw/workspace/logs/asset_monitor.log"
PID_FILE = "/home/goose/.openclaw/workspace/.asset_monitor.pid"

SCAN_INTERVAL = 30
MAX_POSITIONS = 3
STOP_LOSS = 0.05
TAKE_PROFIT = 0.20

TOP6_MEME = ['BOME', 'TURBO', 'BONK', 'FLOKI', 'PEPE', 'NEIRO']
TOP_MAJOR = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOT']

# ============ 数据类 ============

@dataclass
class Position:
    symbol: str
    amount: float
    entry_price: float
    account: str  # spot, cross_margin, isolated, futures
    entry_time: float
    high_price: float

@dataclass
class AccountStatus:
    spot_usdt: float
    spot_total: float
    cross_total: float
    cross_borrowed: float
    isolated_total: float
    futures_total: float
    grand_total: float
    positions: Dict[str, Position]

@dataclass
class CoinPrediction:
    symbol: str
    current_price: float
    predicted_return: float  # 预测收益率
    phase: str  # consolidation, startup, acceleration, peak, decline
    score: float  # 信号评分
    confidence: float

@dataclass
class TradeDecision:
    action: str  # buy, sell, switch, hold
    from_coin: Optional[str]
    to_coin: Optional[str]
    amount: float
    reason: str
    priority: int

# ============ API工具 ============

def api_signed(endpoint: str, params: dict = None, method: str = "GET") -> dict:
    for i in range(3):
        try:
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
        except Exception as e:
            if i < 2: time.sleep(0.5)
    return {}

def api_pub(url: str) -> dict:
    try:
        proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
        opener = urllib.request.build_opener(proxy_handler)
        return json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())
    except: return {}

def get_price(symbol: str) -> float:
    try:
        data = api_pub(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}')
        return float(data['price']) if data else 0
    except: return 0

def get_klines(symbol: str, interval: str = '1h', limit: int = 100) -> List[dict]:
    try:
        data = api_pub(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}')
        return [{'close': float(k[4]), 'high': float(k[2]), 'volume': float(k[5])} for k in data] if data else []
    except: return []

def format_qty(coin: str, qty: float) -> float:
    if qty <= 0: return 0
    try:
        info = api_pub(f'https://api.binance.com/api/v3/exchangeInfo?symbol={coin}USDT')
        if info and 'symbols' in info:
            filters = {f['filterType']: f for f in info['symbols'][0]['filters']}
            step = float(filters.get('LOT_SIZE', {}).get('stepSize', 1))
            min_q = float(filters.get('LOT_SIZE', {}).get('minQty', 0))
            prec = len(str(step).split('.')[-1].rstrip('0')) if step < 1 else 0
            formatted = math.floor(qty / step) * step
            formatted = round(formatted, prec) if prec > 0 else int(formatted)
            return 0 if formatted < min_q else formatted
    except: pass
    return math.floor(qty)

# ============ 账户同步 ============

def sync_spot_account() -> Tuple[float, Dict[str, Position]]:
    """同步现货账户"""
    positions = {}
    data = api_signed("/api/v3/account")
    if not data or 'balances' not in data:
        return 0, positions
    
    usdt = 0
    for b in data.get('balances', []):
        free = float(b.get('free', 0))
        if free > 0.0001:
            asset = b['asset']
            if asset == 'USDT':
                usdt = free
            else:
                price = get_price(f"{asset}USDT")
                if price > 0:
                    positions[asset] = Position(
                        symbol=asset,
                        amount=free,
                        entry_price=price,  # 简化:使用当前价作为入场价
                        account='spot',
                        entry_time=time.time(),
                        high_price=price
                    )
    total = usdt + sum(p.amount * p.entry_price for p in positions.values())
    return usdt, positions

def sync_cross_margin_account() -> Tuple[float, float, Dict[str, Position]]:
    """同步全仓杠杆账户"""
    positions = {}
    data = api_signed("/sapi/v1/margin/account")
    if not data or 'userAssets' not in data:
        return 0, 0, positions
    
    btc_price = get_price("BTCUSDT")
    total = 0
    borrowed = 0
    
    for a in data.get('userAssets', []):
        net = float(a.get('netAsset', 0))
        if abs(net) > 0.0001:
            asset = a['asset']
            if asset == 'BTC':
                usd = net * btc_price
            elif asset == 'USDT':
                usd = net
                if float(a.get('borrowed', 0)) > 0:
                    borrowed += abs(net)
            else:
                price = get_price(f"{asset}USDT")
                usd = net * price if price > 0 else 0
            
            total += usd
            
            if asset != 'USDT' and usd > 1:
                positions[asset] = Position(
                    symbol=asset,
                    amount=abs(net),
                    entry_price=price if price > 0 else usd / abs(net),
                    account='cross_margin',
                    entry_time=time.time(),
                    high_price=price if price > 0 else usd / abs(net)
                )
    
    return total, borrowed, positions

def sync_isolated_account() -> Tuple[float, Dict[str, Position]]:
    """同步逐仓杠杆账户"""
    positions = {}
    data = api_signed("/sapi/v1/margin/isolated/account")
    if not data or 'assets' not in data:
        return 0, positions
    
    total = 0
    for a in data.get('assets', []):
        sym = a.get('symbol', '')
        base = a.get('baseAsset', {})
        quote = a.get('quoteAsset', {})
        
        base_val = float(base.get('free', 0)) * get_price(f"{base.get('asset','USDT')}USDT")
        quote_val = float(quote.get('free', 0))
        
        if base_val + quote_val > 1:
            total += base_val + quote_val
            asset = base.get('asset', '')
            if asset:
                positions[asset] = Position(
                    symbol=asset,
                    amount=float(base.get('free', 0)),
                    entry_price=get_price(f"{asset}USDT"),
                    account='isolated',
                    entry_time=time.time(),
                    high_price=get_price(f"{asset}USDT")
                )
    
    return total, positions

def sync_futures_account() -> Tuple[float, Dict[str, Position]]:
    """同步合约账户"""
    positions = {}
    data = api_signed("/fapi/v2/account")
    if not data or 'error' in data:
        return 0, positions
    
    total = float(data.get('totalMarginBalance', 0))
    
    for p in data.get('positions', []):
        amt = float(p.get('positionAmt', 0))
        if abs(amt) > 0.0001:
            symbol = p.get('symbol', '').replace('USDT', '')
            entry_price = float(p.get('entryPrice', 0))
            positions[symbol] = Position(
                symbol=symbol,
                amount=abs(amt),
                entry_price=entry_price,
                account='futures',
                entry_time=time.time(),
                high_price=entry_price
            )
    
    return total, positions

# ============ 市场分析 ============

def detect_phase(coin: str) -> Tuple[str, float]:
    """检测周期阶段"""
    klines = get_klines(f"{coin}USDT", '1h', 200)
    if not klines: return "consolidation", 50
    
    closes = [k['close'] for k in klines]
    rsi = get_rsi(closes)
    mom = get_momentum(closes[-24:]) if len(closes) >= 24 else 0
    mom_long = get_momentum(closes[-168:]) if len(closes) >= 168 else mom
    
    phase = "consolidation"
    score = 50
    
    if mom_long < -0.08: 
        phase = "decline" if mom < 0 else "startup"
        score = 30 if mom < 0 else 60
    elif mom_long > 0.15:
        if rsi > 75: 
            phase = "peak"
            score = 25
        elif mom > 0.03 and rsi > 55: 
            phase = "acceleration"
            score = 85
        elif rsi < 50: 
            phase = "startup"
            score = 70
    elif rsi > 72: 
        phase = "peak"
        score = 30
    elif mom > 0.025 and rsi > 50: 
        phase = "acceleration"
        score = 75
    elif rsi < 45 and mom > 0: 
        phase = "startup"
        score = 65
    
    return phase, score

def get_rsi(closes: List[float], period: int = 14) -> float:
    if len(closes) < period + 1: return 50
    deltas = [closes[i+1] - closes[i] for i in range(len(closes)-1)]
    gains = [d if d > 0 else 0 for d in deltas[-period:]]
    losses = [-d if d < 0 else 0 for d in deltas[-period:]]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    return 100 - (100 / (1 + avg_gain / (avg_loss + 1e-10))) if avg_loss != 0 else 100

def get_momentum(closes: List[float], period: int = 20) -> float:
    return (closes[-1] - closes[0]) / closes[0] if len(closes) >= period else 0

def predict_return(coin: str) -> CoinPrediction:
    """预测币种收益"""
    current_price = get_price(f"{coin}USDT")
    if current_price == 0: 
        return CoinPrediction(coin, 0, 0, "consolidation", 0, 0)
    
    phase, score = detect_phase(coin)
    
    # 简单预测模型
    predicted_return = 0
    if phase == "acceleration":
        predicted_return = 0.15 + (score - 50) / 100
    elif phase == "startup":
        predicted_return = 0.08 + (score - 50) / 100
    elif phase == "peak":
        predicted_return = -0.05
    elif phase == "decline":
        predicted_return = -0.10
    else:
        predicted_return = 0.02
    
    return CoinPrediction(
        symbol=coin,
        current_price=current_price,
        predicted_return=predicted_return,
        phase=phase,
        score=score,
        confidence=score / 100
    )

# ============ 交易操作 ============

def spot_buy(coin: str, amount: float) -> bool:
    """现货买入"""
    try:
        price = get_price(f"{coin}USDT")
        qty = format_qty(coin, amount / price)
        if qty * price < 1: return False
        
        params = {"symbol": f"{coin}USDT", "side": "BUY", "type": "MARKET", "quantity": str(qty)}
        result = api_signed("/api/v3/order", params, "POST")
        return 'orderId' in result if result else False
    except: return False

def spot_sell(coin: str, amount: float) -> bool:
    """现货卖出"""
    try:
        qty = format_qty(coin, amount)
        if qty <= 0: return False
        
        params = {"symbol": f"{coin}USDT", "side": "SELL", "type": "MARKET", "quantity": str(qty)}
        result = api_signed("/api/v3/order", params, "POST")
        return 'orderId' in result if result else False
    except: return False

# ============ 主系统 ============

class AssetMonitorTrader:
    """资产监控与自主交易系统"""
    
    def __init__(self):
        self.state_file = STATE_FILE
        self.log_file = LOG_FILE
        self.positions: Dict[str, Position] = {}
        self.history = deque(maxlen=200)
        self.last_sync = 0
        self.is_running = False
        
        self.load_state()
    
    def log(self, msg: str, level: str = "INFO"):
        ts = datetime.now().strftime("%m-%d %H:%M:%S")
        line = f"[{ts}] [{level}] {msg}"
        print(line)
        try:
            with open(self.log_file, "a") as f:
                f.write(line + "\n")
        except: pass
    
    def load_state(self):
        """加载持久化状态"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file) as f:
                    state = json.load(f)
                    self.positions = {
                        k: Position(**v) for k, v in state.get('positions', {}).items()
                    }
                    self.history = deque(state.get('history', []), maxlen=200)
                    self.last_sync = state.get('last_sync', 0)
        except Exception as e:
            self.log(f"加载状态失败: {e}", "WARNING")
    
    def save_state(self):
        """保存状态"""
        try:
            state = {
                'positions': {k: asdict(v) for k, v in self.positions.items()},
                'history': list(self.history),
                'last_sync': time.time()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f)
        except Exception as e:
            self.log(f"保存状态失败: {e}", "ERROR")
    
    def sync_all_accounts(self) -> AccountStatus:
        """同步所有账户"""
        self.log("同步所有账户...", "INFO")
        
        # 同步各账户
        spot_usdt, spot_positions = sync_spot_account()
        cross_total, cross_borrowed, cross_positions = sync_cross_margin_account()
        isolated_total, isolated_positions = sync_isolated_account()
        futures_total, futures_positions = sync_futures_account()
        
        # 合并持仓
        all_positions = {}
        all_positions.update(spot_positions)
        all_positions.update(cross_positions)
        all_positions.update(isolated_positions)
        all_positions.update(futures_positions)
        
        # 计算现货总值
        spot_total = spot_usdt + sum(p.amount * p.entry_price for p in spot_positions.values())
        
        # 总资产
        grand_total = spot_total + cross_total + isolated_total + futures_total
        
        status = AccountStatus(
            spot_usdt=spot_usdt,
            spot_total=spot_total,
            cross_total=cross_total,
            cross_borrowed=cross_borrowed,
            isolated_total=isolated_total,
            futures_total=futures_total,
            grand_total=grand_total,
            positions=all_positions
        )
        
        # 更新本地持仓
        self.positions = all_positions
        self.last_sync = time.time()
        self.save_state()
        
        return status
    
    def get_status(self) -> AccountStatus:
        """获取状态"""
        return self.sync_all_accounts()
    
    def analyze_switch_opportunities(self) -> List[TradeDecision]:
        """分析调换机会"""
        decisions = []
        status = self.get_status()
        
        # 收集所有持仓币种的预测
        holding_predictions = []
        for symbol in self.positions.keys():
            if symbol == 'USDT': continue
            pred = predict_return(symbol)
            holding_predictions.append(pred)
        
        # 收集候选币种的预测
        candidate_symbols = set(TOP6_MEME + TOP_MAJOR) - set(self.positions.keys())
        candidate_predictions = []
        for symbol in candidate_symbols:
            pred = predict_return(symbol)
            if pred.phase in ["startup", "acceleration"]:
                candidate_predictions.append(pred)
        
        # 按预期收益排序
        holding_predictions.sort(key=lambda x: -x.predicted_return)
        candidate_predictions.sort(key=lambda x: -x.predicted_return)
        
        # 决策1: 如果有持仓进入衰退期,考虑卖出
        for pred in holding_predictions:
            if pred.phase == "decline":
                decisions.append(TradeDecision(
                    action="sell",
                    from_coin=pred.symbol,
                    to_coin=None,
                    amount=pred.amount if pred.symbol in self.positions else 0,
                    reason=f"{pred.symbol} 进入衰退期, 预测收益{pred.predicted_return:.1%}",
                    priority=1
                ))
        
        # 决策2: 如果有更好的候选,且持仓已满,考虑调换
        if len(self.positions) >= MAX_POSITIONS and candidate_predictions:
            worst_holding = holding_predictions[-1]
            best_candidate = candidate_predictions[0]
            
            # 机会成本分析
            benefit = best_candidate.predicted_return - worst_holding.predicted_return
            if benefit > 0.05:  # 收益差超过5%才调换
                decisions.append(TradeDecision(
                    action="switch",
                    from_coin=worst_holding.symbol,
                    to_coin=best_candidate.symbol,
                    amount=worst_holding.amount if worst_holding.symbol in self.positions else 0,
                    reason=f"调换 {worst_holding.symbol}→{best_candidate.symbol}, 收益差{benefit:.1%}",
                    priority=2
                ))
        
        # 决策3: 如果有空位,且有启动/加速期候选,考虑买入
        if len(self.positions) < MAX_POSITIONS and candidate_predictions:
            best = candidate_predictions[0]
            if best.phase in ["startup", "acceleration"] and best.confidence > 0.6:
                decisions.append(TradeDecision(
                    action="buy",
                    from_coin=None,
                    to_coin=best.symbol,
                    amount=status.spot_usdt * 0.3,  # 使用30%的USDT
                    reason=f"买入 {best.symbol} in {best.phase}, 预测收益{best.predicted_return:.1%}",
                    priority=3
                ))
        
        return decisions
    
    def execute_decision(self, decision: TradeDecision) -> bool:
        """执行决策"""
        if decision.action == "sell" and decision.from_coin:
            self.log(f"卖出 {decision.from_coin}: {decision.reason}", "TRADE")
            return spot_sell(decision.from_coin, decision.amount)
        
        elif decision.action == "buy" and decision.to_coin:
            self.log(f"买入 {decision.to_coin}: {decision.reason}", "TRADE")
            return spot_buy(decision.to_coin, decision.amount)
        
        elif decision.action == "switch":
            self.log(f"调换 {decision.from_coin}→{decision.to_coin}: {decision.reason}", "TRADE")
            # 先卖出
            if spot_sell(decision.from_coin, decision.amount):
                time.sleep(1)
                # 再买入
                return spot_buy(decision.to_coin, decision.amount * get_price(f"{decision.from_coin}USDT"))
        
        return False
    
    def run(self):
        """主运行循环"""
        self.log("=" * 60, "INFO")
        self.log("Asset Monitor and Trader 启动", "INFO")
        self.log("=" * 60, "INFO")
        
        self.is_running = True
        
        # 保存PID
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        
        while self.is_running:
            try:
                # 1. 同步所有账户
                status = self.sync_all_accounts()
                
                self.log(f"\n{'='*60}", "INFO")
                self.log(f"📊 账户状态", "INFO")
                self.log(f"{'='*60}", "INFO")
                self.log(f"现货: ${status.spot_total:.2f} (USDT ${status.spot_usdt:.2f})", "INFO")
                self.log(f"全仓杠杆: ${status.cross_total:.2f}", "INFO")
                self.log(f"逐仓杠杆: ${status.isolated_total:.2f}", "INFO")
                self.log(f"合约: ${status.futures_total:.2f}", "INFO")
                self.log(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "INFO")
                self.log(f"总资产: ${status.grand_total:.2f}", "INFO")
                self.log(f"持仓数: {len(self.positions)}/{MAX_POSITIONS}", "INFO")
                
                # 2. 分析调换机会
                decisions = self.analyze_switch_opportunities()
                
                # 3. 执行决策
                for decision in decisions[:3]:  # 每次最多执行3个决策
                    if decision.priority <= 2:  # 只执行高优先级决策
                        self.log(f"决策: {decision.action} {decision.from_coin or ''}→{decision.to_coin or ''}", "INFO")
                        if self.execute_decision(decision):
                            self.history.append({
                                'action': decision.action,
                                'from': decision.from_coin,
                                'to': decision.to_coin,
                                'time': time.time(),
                                'reason': decision.reason
                            })
                
                # 4. 显示持仓状态
                self.log(f"\n📈 持仓状态:", "INFO")
                for symbol, pos in self.positions.items():
                    current = get_price(f"{symbol}USDT")
                    pnl = (current - pos.entry_price) / pos.entry_price if pos.entry_price > 0 else 0
                    phase, _ = detect_phase(symbol)
                    self.log(f"  {symbol}: {phase} {pnl:+.1%}", "INFO")
                
                if not self.positions:
                    self.log("  无持仓", "INFO")
                
                # 保存状态
                self.save_state()
                
                # 等待下次扫描
                time.sleep(SCAN_INTERVAL)
                
            except Exception as e:
                self.log(f"错误: {e}", "ERROR")
                import traceback
                traceback.print_exc()
                time.sleep(10)
    
    def stop(self):
        """停止"""
        self.is_running = False
        self.log("停止 Asset Monitor Trader", "INFO")

def main():
    amt = AssetMonitorTrader()
    try:
        amt.run()
    except KeyboardInterrupt:
        amt.stop()

if __name__ == "__main__":
    main()
