#!/usr/bin/env python3
"""
Top 10 Trader to Crypto - 加密货币交易员组合系统
============================================
将十大交易员策略适配到加密货币市场
包含: 主流币 + Meme币 + ETF + Oracle 特殊逻辑

Trader Personas:
1. George Soros - 宏观对冲
2. Stanley Druckenmiller - 流动性狩猎
3. Bruce Kovner - 外汇期货
4. Michael Marcus - 商品期货
5. Paul Tudor Jones - 趋势跟踪
6. Richard Dennis - 系统化交易
7. Martin Schwartz - 技术分析
8. Bill Lipschutz - 外汇专精
9. Jesse Livermore - 价格行为
10. Jim Rogers - 商品期货

Special Adaptations:
- ETF: GBTC, ETHE, BITO 等
- Oracle: LINK, BAND, API3
- Mainstream: BTC, ETH, SOL 等
- Meme: DOGE, SHIB, PEPE 等
"""

import json
import time
import math
import urllib.request
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import deque

# ============ 基础配置 ============

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

@dataclass
class CryptoTraderProfile:
    name: str
    name_cn: str
    style: str
    base_weight: float
    best_for: List[str]  # 适应的币种类型
    signals: List[str]
    stop_loss: float
    take_profit: float

@dataclass
class MarketSignal:
    symbol: str
    trend: str
    volatility: str
    momentum: float
    volume_change: float
    fear_greed: float
    funding_rate: float
    coin_type: str  # mainstream/meme/etf/oracle

@dataclass
class TradeDecision:
    symbol: str
    trader: str
    trader_cn: str
    direction: str
    confidence: float
    position_size: float
    stop_loss: float
    take_profit: float
    reasoning: str

# ============ 交易员配置 ============

TRADERS = {
    "soros": CryptoTraderProfile(
        name="George Soros",
        name_cn="索罗斯",
        style="宏观对冲",
        base_weight=0.12,
        best_for=["BTC", "ETH", "ETF"],
        signals=["ETF溢价异常", "期货基差", "央行政策"],
        stop_loss=0.08,
        take_profit=0.25
    ),
    "druckenmiller": CryptoTraderProfile(
        name="Stanley Druckenmiller",
        name_cn="德鲁肯米勒",
        style="流动性狩猎",
        base_weight=0.12,
        best_for=["BTC", "ETH", "LINK"],
        signals=["链上流动性", "交易所余额", "稳定币流量"],
        stop_loss=0.06,
        take_profit=0.20
    ),
    "kovner": CryptoTraderProfile(
        name="Bruce Kovner",
        name_cn="柯夫纳",
        style="外汇期货",
        base_weight=0.10,
        best_for=["LINK", "BAND", "AAVE"],
        signals=["技术突破", "趋势线", "央行政策"],
        stop_loss=0.05,
        take_profit=0.18
    ),
    "marcus": CryptoTraderProfile(
        name="Michael Marcus",
        name_cn="马库斯",
        style="商品期货",
        base_weight=0.08,
        best_for=["BTC", "ETH", "SOL"],
        signals=["趋势形成", "持仓量增加", "供需变化"],
        stop_loss=0.10,
        take_profit=0.30
    ),
    "jones": CryptoTraderProfile(
        name="Paul Tudor Jones",
        name_cn="琼斯",
        style="趋势跟踪",
        base_weight=0.12,
        best_for=["BTC", "ETH", "DOGE", "PEPE"],
        signals=["均线多头排列", "RSI极端", "趋势线突破"],
        stop_loss=0.05,
        take_profit=0.20
    ),
    "dennis": CryptoTraderProfile(
        name="Richard Dennis",
        name_cn="丹尼斯",
        style="系统化交易",
        base_weight=0.08,
        best_for=["BTC", "ETH", "SOL"],
        signals=["唐奇安通道", "20日突破", "规则化信号"],
        stop_loss=0.05,
        take_profit=0.15
    ),
    "schwartz": CryptoTraderProfile(
        name="Martin Schwartz",
        name_cn="舒华兹",
        style="技术分析",
        base_weight=0.10,
        best_for=["DOGE", "SHIB", "PEPE", "BONK"],
        signals=["K线形态", "Meme叙事", "社交热度"],
        stop_loss=0.08,
        take_profit=0.25
    ),
    "lipschutz": CryptoTraderProfile(
        name="Bill Lipschutz",
        name_cn="利普舒茨",
        style="外汇专精",
        base_weight=0.08,
        best_for=["LINK", "BAND", "AAVE"],
        signals=["汇率对", "DeFiTVL", "预言机数据"],
        stop_loss=0.05,
        take_profit=0.18
    ),
    "livermore": CryptoTraderProfile(
        name="Jesse Livermore",
        name_cn="利弗莫尔",
        style="价格行为",
        base_weight=0.10,
        best_for=["BTC", "ETH", "SOL", "DOGE"],
        signals=["价格新高/低", "板块轮动", "龙头效应"],
        stop_loss=0.06,
        take_profit=0.22
    ),
    "rogers": CryptoTraderProfile(
        name="Jim Rogers",
        name_cn="罗杰斯",
        style="商品期货",
        base_weight=0.10,
        best_for=["BTC", "ETH", "LINK"],
        signals=["机构持仓", "ETF流入", "美元走势"],
        stop_loss=0.08,
        take_profit=0.25
    )
}

# ============ 币种分类 ============

COIN_CATEGORIES = {
    "mainstream": ["BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "AVAX", "DOGE", "DOT", "MATIC"],
    "meme": ["DOGE", "SHIB", "PEPE", "BONK", "FLOKI", "BOME", "TURBO", "NEIRO", "WIF", "MOG"],
    "etf": ["GBTC", "ETHE", "FBTC", "IBIT", "ARKB"],
    "oracle": ["LINK", "BAND", "API3", "POKT", "TRAC"]
}

# ============ 工具函数 ============

def api_pub(url):
    try:
        proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
        opener = urllib.request.build_opener(proxy_handler)
        return json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())
    except: return None

def api_signed(endpoint, params=None, method="GET"):
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
        except: time.sleep(0.3)
    return None

import hmac, hashlib

def get_price(symbol):
    data = api_pub(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}')
    return float(data['price']) if data else 0

def get_klines(symbol, interval='1h', limit=100):
    data = api_pub(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}')
    if not data: return []
    return [{'time': k[0], 'open': float(k[1]), 'high': float(k[2]), 'low': float(k[3]), 'close': float(k[4]), 'volume': float(k[5])} for k in data]

def get_rsi(closes, period=14):
    if len(closes) < period+1: return 50
    deltas = [closes[i+1]-closes[i] for i in range(len(closes)-1)]
    gains = [d if d>0 else 0 for d in deltas[-period:]]
    losses = [-d if d<0 else 0 for d in deltas[-period:]]
    avg_gain = sum(gains)/period
    avg_loss = sum(losses)/period
    return 100-(100/(1+avg_gain/(avg_loss+1e-10))) if avg_loss != 0 else 100

def get_momentum(closes, period=20):
    return (closes[-1]-closes[0])/closes[0] if len(closes) >= period else 0

def get_volatility(highs, lows, closes, period=20):
    if len(closes) < period: return 0.02
    returns = [(closes[i]-closes[i-1])/closes[i-1] for i in range(1, len(closes))]
    variance = sum(r*r for r in returns[-period:]) / period
    return math.sqrt(variance)

def get_volume_change(volumes, period=24):
    if len(volumes) < period*2: return 0
    recent_avg = sum(volumes[-period:])/period
    prev_avg = sum(volumes[-period*2:-period])/period
    return (recent_avg - prev_avg) / prev_avg if prev_avg > 0 else 0

def get_funding_rate(symbol):
    try:
        data = api_pub(f'https://fapi.binance.com/fapi/v1/premiumIndex?symbol={symbol}')
        return float(data.get('lastFundingRate', 0)) if data else 0
    except: return 0

# ============ 市场分析 ============

def analyze_market(symbol: str) -> MarketSignal:
    """分析市场信号"""
    klines_hour = get_klines(symbol, '1h', 100)
    klines_day = get_klines(symbol, '1d', 30)
    
    closes = [k['close'] for k in klines_hour]
    highs = [k['high'] for k in klines_hour]
    lows = [k['low'] for k in klines_hour]
    volumes = [k['volume'] for k in klines_hour]
    
    rsi = get_rsi(closes)
    mom = get_momentum(closes[-24:]) if len(closes) >= 24 else 0
    mom_long = get_momentum(closes[-168:]) if len(closes) >= 168 else mom
    vol = get_volatility(highs, lows, closes)
    vol_change = get_volume_change(volumes)
    funding = get_funding_rate(symbol)
    
    # 判断趋势
    if mom_long > 0.1 and rsi > 60: trend = "bull"
    elif mom_long < -0.1 and rsi < 40: trend = "bear"
    else: trend = "sideways"
    
    # 判断波动率
    if vol > 0.05: volatility = "high"
    elif vol > 0.02: volatility = "medium"
    else: volatility = "low"
    
    # 判断币种类型
    coin_type = "mainstream"
    for cat, coins in COIN_CATEGORIES.items():
        if symbol in coins:
            coin_type = cat
            break
    
    return MarketSignal(
        symbol=symbol,
        trend=trend,
        volatility=volatility,
        momentum=mom_long,
        volume_change=vol_change,
        fear_greed=50 + (rsi - 50) * 2,
        funding_rate=funding,
        coin_type=coin_type
    )

# ============ 权重计算 ============

def calculate_weights(market: MarketSignal) -> Dict[str, float]:
    """根据市场状态和币种类型计算权重"""
    base = {k: v.base_weight for k, v in TRADERS.items()}
    
    # 币种类型调整
    if market.coin_type == "meme":
        base["schwartz"] *= 1.5  # Meme专精
        base["jones"] *= 1.2
        base["livermore"] *= 1.1
        base["marcus"] *= 0.8
        base["kovner"] *= 0.8
    elif market.coin_type == "mainstream":
        base["jones"] *= 1.3
        base["livermore"] *= 1.2
        base["rogers"] *= 1.1
        base["soros"] *= 1.1
    elif market.coin_type == "oracle":
        base["kovner"] *= 1.4
        base["lipschutz"] *= 1.3
        base["druckenmiller"] *= 1.1
    elif market.coin_type == "etf":
        base["soros"] *= 1.5
        base["rogers"] *= 1.3
        base["druckenmiller"] *= 1.1
    
    # 趋势调整
    if market.trend == "bull":
        base["jones"] *= 1.3
        base["marcus"] *= 1.2
        base["livermore"] *= 1.1
    elif market.trend == "bear":
        base["soros"] *= 1.4
        base["schwartz"] *= 1.2
        base["kovner"] *= 1.1
    else:
        base["dennis"] *= 1.3
        base["schwartz"] *= 1.2
    
    # 波动率调整
    if market.volatility == "high":
        base["schwartz"] *= 1.2
        base["livermore"] *= 1.1
        base["dennis"] *= 0.9
    elif market.volatility == "low":
        base["rogers"] *= 1.2
        base["kovner"] *= 1.1
        base["schwartz"] *= 0.8
    
    # 动量调整
    if market.momentum > 0.15:
        base["marcus"] *= 1.3
        base["jones"] *= 1.2
    elif market.momentum < -0.1:
        base["schwartz"] *= 1.3
        base["soros"] *= 1.2
    
    # 资金费率调整
    if abs(market.funding_rate) > 0.001:
        base["soros"] *= 1.2  # 高资金费率预示反转
    
    # 归一化
    total = sum(base.values())
    return {k: v/total for k, v in base.items()}

# ============ 决策生成 ============

def generate_decision(weights: Dict[str, float], market: MarketSignal) -> TradeDecision:
    """生成交易决策"""
    sorted_traders = sorted(weights.items(), key=lambda x: -x[1])
    primary_id = sorted_traders[0][0]
    primary = TRADERS[primary_id]
    
    confidence = sum(w for _, w in sorted_traders[:3])
    
    # 方向判断
    if market.trend == "bull": direction = "long"
    elif market.trend == "bear": direction = "short"
    else: direction = "neutral"
    
    # 仓位计算
    if market.coin_type == "meme":
        position_size = 0.20 if market.volatility == "high" else 0.15
    elif market.coin_type == "mainstream":
        position_size = 0.25
    else:
        position_size = 0.20
    
    # 止损止盈
    stop_loss = primary.stop_loss
    take_profit = primary.take_profit
    
    if market.coin_type == "meme":
        stop_loss *= 0.8
        take_profit *= 1.2
    
    # 推理
    top_traders = [TRADERS[t].name_cn for t, _ in sorted_traders[:3]]
    reasoning = f"{market.coin_type}+{market.trend}+{' '.join(top_traders)}"
    
    return TradeDecision(
        symbol=market.symbol,
        trader=primary_id,
        trader_cn=primary.name_cn,
        direction=direction,
        confidence=confidence,
        position_size=position_size,
        stop_loss=stop_loss,
        take_profit=take_profit,
        reasoning=reasoning
    )

# ============ 回测系统 ============

class Backtester:
    """回测系统"""
    
    def __init__(self):
        self.results = {
            "mainstream": [],
            "meme": [],
            "etf": [],
            "oracle": []
        }
        self.trades = []
    
    def get_historical_data(self, symbol: str, days: int = 30):
        """获取历史数据"""
        klines = get_klines(symbol, '1h', days * 24)
        return klines
    
    def backtest_symbol(self, symbol: str, coin_type: str, days: int = 30) -> Dict:
        """回测单个币种"""
        klines = self.get_historical_data(symbol, days)
        if len(klines) < 100: return None
        
        closes = [k['close'] for k in klines]
        highs = [k['high'] for k in klines]
        lows = [k['low'] for k in klines]
        volumes = [k['volume'] for k in klines]
        
        trades = []
        wins = 0
        losses = 0
        total_return = 0
        
        # 模拟交易
        position = None
        entry_price = 0
        entry_time = 0
        
        for i in range(50, len(klines) - 1):
            current = klines[i]
            window = klines[max(0, i-100):i]
            window_closes = [k['close'] for k in window]
            window_highs = [k['high'] for k in window]
            window_lows = [k['low'] for k in window]
            
            if len(window_closes) < 50: continue
            
            rsi = get_rsi(window_closes)
            mom = get_momentum(window_closes[-24:]) if len(window_closes) >= 24 else 0
            mom_long = get_momentum(window_closes[-168:]) if len(window_closes) >= 168 else mom
            
            # 判断趋势
            if mom_long > 0.1 and rsi > 60: trend = "bull"
            elif mom_long < -0.1 and rsi < 40: trend = "bear"
            else: trend = "sideways"
            
            # 模拟信号
            if position is None:
                if trend == "bull" and rsi > 55 and rsi < 80:
                    position = "long"
                    entry_price = current['close']
                    entry_time = i
            else:
                pnl = (current['close'] - entry_price) / entry_price
                if pnl <= -0.05 or pnl >= 0.20 or trend == "bear":
                    if pnl > 0: wins += 1
                    else: losses += 1
                    total_return += pnl
                    trades.append({
                        'symbol': symbol,
                        'entry': entry_price,
                        'exit': current['close'],
                        'pnl': pnl,
                        'direction': position,
                        'hold_hours': (i - entry_time) * 1
                    })
                    position = None
        
        total_trades = wins + losses
        win_rate = wins / total_trades if total_trades > 0 else 0
        avg_return = total_return / total_trades if total_trades > 0 else 0
        
        return {
            'symbol': symbol,
            'coin_type': coin_type,
            'total_trades': total_trades,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'avg_return': avg_return,
            'total_return': total_return,
            'trades': trades
        }
    
    def run_backtest(self, categories: Dict[str, List[str]], days: int = 30) -> Dict:
        """运行完整回测"""
        results = {}
        
        for coin_type, symbols in categories.items():
            print(f"\n回测 {coin_type}: {symbols}")
            type_results = []
            
            for symbol in symbols:
                try:
                    result = self.backtest_symbol(symbol, coin_type, days)
                    if result:
                        type_results.append(result)
                        print(f"  {symbol}: 交易{result['total_trades']}次, 胜率{result['win_rate']:.1%}, 收益{result['total_return']:.1%}")
                except Exception as e:
                    print(f"  {symbol}: 错误 {e}")
            
            if type_results:
                total_trades = sum(r['total_trades'] for r in type_results)
                wins = sum(r['wins'] for r in type_results)
                losses = sum(r['losses'] for r in type_results)
                total_return = sum(r['total_return'] for r in type_results)
                avg_return = sum(r['avg_return'] for r in type_results) / len(type_results)
                
                results[coin_type] = {
                    'symbols': symbols,
                    'total_trades': total_trades,
                    'wins': wins,
                    'losses': losses,
                    'win_rate': wins / total_trades if total_trades > 0 else 0,
                    'total_return': total_return,
                    'avg_return': avg_return,
                    'symbol_results': type_results
                }
        
        return results
    
    def print_matrix(self, results: Dict):
        """打印结果矩阵"""
        print("\n" + "=" * 80)
        print("📊 30天回测结果矩阵")
        print("=" * 80)
        
        for coin_type, data in results.items():
            print(f"\n【{coin_type.upper()}】")
            print("-" * 60)
            print(f"{'Symbol':<12} {'Trades':<8} {'WinRate':<10} {'Avg Return':<12} {'Total':<10}")
            print("-" * 60)
            
            for r in data['symbol_results']:
                print(f"{r['symbol']:<12} {r['total_trades']:<8} {r['win_rate']:>8.1%} {r['avg_return']:>10.2%} {r['total_return']:>8.1%}")
            
            print("-" * 60)
            print(f"{'汇总':<12} {data['total_trades']:<8} {data['win_rate']:>8.1%} {data['avg_return']:>10.2%} {data['total_return']:>8.1%}")
        
        print("\n" + "=" * 80)
        print("📈 胜率 vs 收益矩阵")
        print("=" * 80)
        print(f"{'Coin Type':<15} {'WinRate':<12} {'AvgReturn':<12} {'TotalReturn':<12}")
        print("-" * 60)
        for coin_type, data in results.items():
            print(f"{coin_type:<15} {data['win_rate']:>10.1%} {data['avg_return']:>10.2%} {data['total_return']:>10.1%}")

# ============ 主系统 ============

class Top10TraderCrypto:
    """Top10交易员加密货币系统"""
    
    def __init__(self):
        self.state_file = "/home/goose/.openclaw/workspace/.top10_crypto_state.json"
        self.performance = []
        self.weights = {k: v.base_weight for k, v in TRADERS.items()}
        self.load_state()
    
    def load_state(self):
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
                self.performance = state.get('performance', [])
                self.weights = state.get('weights', self.weights)
        except: pass
    
    def save_state(self):
        state = {
            'weights': self.weights,
            'performance': self.performance[-100:],
            'last_update': time.time()
        }
        with open(self.state_file, 'w') as f:
            json.dump(state, f)
    
    def analyze(self, symbol: str) -> TradeDecision:
        """分析单个币种"""
        market = analyze_market(symbol)
        weights = calculate_weights(market)
        decision = generate_decision(weights, market)
        return decision
    
    def analyze_all(self) -> Dict[str, TradeDecision]:
        """分析所有分类币种"""
        decisions = {}
        for coin_type, symbols in COIN_CATEGORIES.items():
            for symbol in symbols[:5]:  # 每类分析前5个
                try:
                    decisions[symbol] = self.analyze(symbol)
                except: pass
        return decisions
    
    def optimize(self):
        """基于表现优化权重"""
        if len(self.performance) < 10: return
        
        recent = self.performance[-20:]
        for trader in TRADERS.keys():
            wins = sum(1 for p in recent if p['trader'] == trader and p['pnl'] > 0)
            if wins < 3:
                self.weights[trader] *= 0.95
            elif wins > 8:
                self.weights[trader] *= 1.05
        
        # 归一化
        total = sum(self.weights.values())
        self.weights = {k: v/total for k, v in self.weights.items()}
        self.save_state()
    
    def run_backtest_30d(self):
        """运行30天回测"""
        print("=" * 80)
        print("🔄 Top10 Trader to Crypto - 30天回测")
        print("=" * 80)
        
        backtester = Backtester()
        results = backtester.run_backtest(COIN_CATEGORIES, days=30)
        backtester.print_matrix(results)
        
        return results

def main():
    """主函数"""
    system = Top10TraderCrypto()
    
    print("=" * 80)
    print("Top10 Trader to Crypto - 加密货币交易员组合系统")
    print("=" * 80)
    
    # 1. 先运行30天回测
    print("\n【1. 运行30天回测】")
    results = system.run_backtest_30d()
    
    # 2. 分析当前市场
    print("\n【2. 当前市场分析】")
    decisions = system.analyze_all()
    for symbol, decision in sorted(decisions.items(), key=lambda x: -x[1].confidence):
        print(f"\n{symbol}:")
        print(f"  交易员: {decision.trader_cn} ({decision.trader})")
        print(f"  方向: {decision.direction}")
        print(f"  信心: {decision.confidence:.1%}")
        print(f"  仓位: {decision.position_size:.0%}")
        print(f"  止损/止盈: {decision.stop_loss:.0%}/{decision.take_profit:.0%}")
        print(f"  推理: {decision.reasoning}")

if __name__ == "__main__":
    main()
