"""
Binance Optimizer - 币安深度优化引擎
实时数据 + API集成 + 智能下单 + 动态风控
"""
import sys
import time
import hmac
import hashlib
import urllib.request
import json
from typing import Dict, List, Optional
from dataclasses import dataclass

class BinanceAPI:
    """币安API封装"""
    
    def __init__(self, api_key: str = None, api_secret: str = None, proxy: str = None):
        self.api_key = api_key or "QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61"
        self.api_secret = api_secret or "BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk"
        self.proxy = proxy or "http://172.29.144.1:7897"
        self.base_url = "https://api.binance.com"
        
    def _sign(self, params: Dict) -> str:
        """签名"""
        query = urllib.parse.urlencode(params)
        signature = hmac.new(
            self.api_secret.encode(),
            query.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """发送请求"""
        try:
            params = params or {}
            params['timestamp'] = int(time.time() * 1000)
            params['recvWindow'] = 5000
            
            query = urllib.parse.urlencode(params)
            signature = self._sign(params)
            query += f"&signature={signature}"
            
            url = f"{self.base_url}{endpoint}?{query}"
            
            req = urllib.request.Request(url)
            req.add_header('X-MBX-APIKEY', self.api_key)
            
            if self.proxy:
                proxy_handler = urllib.request.ProxyHandler({
                    'http': self.proxy,
                    'https': self.proxy
                })
                opener = urllib.request.build_opener(proxy_handler)
            else:
                opener = urllib.request.build_opener()
            
            with opener.open(req, timeout=5) as response:
                return json.loads(response.read().decode())
        except Exception as e:
            return None
    
    def get_account(self) -> Optional[Dict]:
        """获取账户信息"""
        return self._request("/api/v3/account")
    
    def get_balance(self) -> Optional[Dict]:
        """获取余额"""
        account = self.get_account()
        if not account:
            return None
        
        balances = {}
        for bal in account.get('balances', []):
            free = float(bal.get('free', 0))
            locked = float(bal.get('locked', 0))
            if free > 0 or locked > 0:
                balances[bal['asset']] = {'free': free, 'locked': locked, 'total': free + locked}
        
        return balances
    
    def get_ticker(self, symbol: str) -> Optional[Dict]:
        """获取行情"""
        try:
            url = f"{self.base_url}/api/v3/ticker/24hr?symbol={symbol.upper()}"
            req = urllib.request.Request(url)
            
            proxy_handler = urllib.request.ProxyHandler({'http': self.proxy, 'https': self.proxy})
            opener = urllib.request.build_opener(proxy_handler)
            
            with opener.open(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                return {
                    'symbol': data['symbol'],
                    'price': float(data['lastPrice']),
                    'change': float(data['priceChange']),
                    'change_pct': float(data['priceChangePercent']),
                    'high': float(data['highPrice']),
                    'low': float(data['lowPrice']),
                    'volume': float(data['volume']),
                    'quote_volume': float(data['quoteVolume'])
                }
        except:
            return None
    
    def get_all_tickers(self) -> List[Dict]:
        """获取所有行情"""
        try:
            url = f"{self.base_url}/api/v3/ticker/price"
            req = urllib.request.Request(url)
            
            proxy_handler = urllib.request.ProxyHandler({'http': self.proxy, 'https': self.proxy})
            opener = urllib.request.build_opener(proxy_handler)
            
            with opener.open(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                return [{'symbol': t['symbol'], 'price': float(t['price'])} for t in data if t['symbol'].endswith('USDT')]
        except:
            return []
    
    def get_depth(self, symbol: str, limit: int = 20) -> Optional[Dict]:
        """获取订单簿"""
        try:
            url = f"{self.base_url}/api/v3/depth?symbol={symbol.upper()}&limit={limit}"
            req = urllib.request.Request(url)
            
            proxy_handler = urllib.request.ProxyHandler({'http': self.proxy, 'https': self.proxy})
            opener = urllib.request.build_opener(proxy_handler)
            
            with opener.open(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                return {
                    'symbol': symbol.upper(),
                    'bids': [[float(p), float(q)] for p, q in data.get('bids', [])[:10]],
                    'asks': [[float(p), float(q)] for p, q in data.get('asks', [])[:10]]
                }
        except:
            return None
    
    def get_klines(self, symbol: str, interval: str = "1h", limit: int = 100) -> Optional[List]:
        """获取K线数据"""
        try:
            url = f"{self.base_url}/api/v3/klines?symbol={symbol.upper()}&interval={interval}&limit={limit}"
            req = urllib.request.Request(url)
            
            proxy_handler = urllib.request.ProxyHandler({'http': self.proxy, 'https': self.proxy})
            opener = urllib.request.build_opener(proxy_handler)
            
            with opener.open(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                return [{
                    'open_time': k[0],
                    'open': float(k[1]),
                    'high': float(k[2]),
                    'low': float(k[3]),
                    'close': float(k[4]),
                    'volume': float(k[5]),
                    'close_time': k[6]
                } for k in data]
        except:
            return None
    
    def get_funding_rate(self, symbol: str) -> Optional[Dict]:
        """获取资金费率"""
        try:
            url = f"{self.base_url}/fapi/v1/fundingRate?symbol={symbol.upper()}"
            req = urllib.request.Request(url)
            
            proxy_handler = urllib.request.ProxyHandler({'http': self.proxy, 'https': self.proxy})
            opener = urllib.request.build_opener(proxy_handler)
            
            with opener.open(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                return {
                    'symbol': data['symbol'],
                    'funding_rate': float(data['fundingRate']) * 100,  # 转为百分比
                    'next_funding_time': data['nextFundingTime']
                }
        except:
            return None

@dataclass
class CoinData:
    """币种数据"""
    symbol: str
    price: float
    change_24h: float
    volume_24h: float
    funding_rate: float
    score: float

class BinanceOptimizer:
    """
    币安优化引擎
    
    功能:
    1. 实时行情获取
    2. 多维度评分
    3. 机会筛选
    4. 智能推荐
    5. 下单优化
    """
    
    def __init__(self, api: BinanceAPI = None):
        self.api = api or BinanceAPI()
        self.cache = {}
        self.cache_time = {}
        
    def get_coin_data(self, symbol: str) -> Optional[CoinData]:
        """获取币种完整数据"""
        ticker = self.api.get_ticker(symbol)
        if not ticker:
            return None
        
        # 资金费率
        funding = self.api.get_funding_rate(symbol)
        funding_rate = funding['funding_rate'] if funding else 0
        
        # 计算评分
        score = self._calculate_score(ticker, funding_rate)
        
        return CoinData(
            symbol=ticker['symbol'],
            price=ticker['price'],
            change_24h=ticker['change_pct'],
            volume_24h=ticker['quote_volume'],
            funding_rate=funding_rate,
            score=score
        )
    
    def _calculate_score(self, ticker: Dict, funding_rate: float) -> float:
        """计算综合评分"""
        # 涨跌幅评分 (权重 30%)
        change = abs(ticker['change_pct'])
        change_score = min(100, change * 10)
        
        # 成交量评分 (权重 25%)
        vol = ticker['quote_volume']
        vol_score = min(100, vol / 1e8 * 50)  # 1亿成交量=50分
        
        # 资金费率评分 (权重 25%)
        if funding_rate > 0.0003:  # 正资金费率>0.03%
            funding_score = 80 + min(20, funding_rate * 1000)
        elif funding_rate < -0.0003:  # 负资金费率
            funding_score = 70 + min(30, abs(funding_rate) * 1000)
        else:
            funding_score = 50
        
        # 波动性评分 (权重 20%)
        high_low_range = (ticker['high'] - ticker['low']) / ticker['price'] * 100
        volatility_score = min(100, high_low_range * 20)
        
        # 综合评分
        total_score = (
            change_score * 0.30 +
            vol_score * 0.25 +
            funding_score * 0.25 +
            volatility_score * 0.20
        )
        
        return total_score
    
    def get_top_coins(self, limit: int = 20) -> List[CoinData]:
        """获取评分最高的币种"""
        # 主流币种列表
        symbols = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT',
            'ADAUSDT', 'DOGEUSDT', 'AVAXUSDT', 'LINKUSDT', 'DOTUSDT',
            'MATICUSDT', 'UNIUSDT', 'LTCUSDT', 'ATOMUSDT', 'NEARUSDT',
            'APTUSDT', 'ARBUSDT', 'OPUSDT', 'INJUSDT', 'SUIUSDT'
        ]
        
        coins = []
        for symbol in symbols:
            data = self.get_coin_data(symbol)
            if data:
                coins.append(data)
        
        # 按评分排序
        coins.sort(key=lambda x: x.score, reverse=True)
        return coins[:limit]
    
    def find_arbitrage(self) -> List[Dict]:
        """寻找套利机会"""
        opportunities = []
        
        # 现货-合约套利
        spot_coins = ['BTC', 'ETH', 'BNB', 'SOL', 'XRP']
        
        for coin in spot_coins:
            spot = self.api.get_ticker(f"{coin}USDT")
            funding = self.api.get_funding_rate(f"{coin}USD")
            
            if spot and funding:
                # 买入现货, 做空合约
                # 资金费率收益
                annual_funding = funding['funding_rate'] * 365
                
                opportunities.append({
                    'type': 'FUNDING_ARB',
                    'symbol': coin,
                    'spot_price': spot['price'],
                    'funding_rate': funding['funding_rate'],
                    'annual_return': annual_funding,
                    'action': 'LONG_SPOT_SHORT_FUTURES' if funding['funding_rate'] > 0 else 'SHORT_SPOT_LONG_FUTURES'
                })
        
        return sorted(opportunities, key=lambda x: x['annual_return'], reverse=True)
    
    def optimize_portfolio(self, capital: float = 10000) -> Dict:
        """优化投资组合"""
        top_coins = self.get_top_coins(10)
        
        if not top_coins:
            return {'error': 'No data available'}
        
        # 按评分分配
        total_score = sum(c.score for c in top_coins)
        
        allocations = []
        remaining = capital
        
        for i, coin in enumerate(top_coins[:8]):
            # 评分权重
            weight = coin.score / total_score
            
            # 资本分配 (首权重稍微倾斜)
            if i == 0:
                alloc = remaining * 0.25
                remaining -= alloc
            else:
                alloc = remaining * weight * 0.8
                remaining -= alloc
            
            # 计算数量
            quantity = alloc / coin.price
            
            allocations.append({
                'symbol': coin.symbol.replace('USDT', ''),
                'price': coin.price,
                'quantity': quantity,
                'capital': alloc,
                'weight': weight * 100,
                'score': coin.score,
                'change_24h': coin.change_24h,
                'action': 'BUY'
            })
        
        return {
            'total_capital': capital,
            'allocated': sum(a['capital'] for a in allocations),
            'allocations': allocations
        }
    
    def generate_report(self) -> str:
        """生成报告"""
        print("=" * 70)
        print("🔧 Binance Optimizer - 币安优化引擎")
        print("=" * 70)
        
        # 获取Top币种
        print("\n📊 正在获取市场数据...")
        top_coins = self.get_top_coins(10)
        
        if not top_coins:
            print("❌ 无法获取市场数据")
            return ""
        
        print(f"\n╔══════════════════════════════════════════════════════════════════════╗")
        print(f"║                    🏆 Top 10 币种评分                           ║")
        print(f"╚══════════════════════════════════════════════════════════════════════╝")
        
        for i, coin in enumerate(top_coins, 1):
            emoji = "🟢" if coin.change_24h > 0 else "🔴"
            funding_icon = "📈" if coin.funding_rate > 0 else "📉" if coin.funding_rate < 0 else "➖"
            print(f"{i:2}. {emoji} {coin.symbol:12} ${coin.price:>10,.2f} {coin.change_24h:+6.2f}% {funding_icon}{coin.funding_rate:+.4f}% Score: {coin.score:.1f}")
        
        # 套利机会
        print(f"\n╔══════════════════════════════════════════════════════════════════════╗")
        print(f"║                    💰 套利机会                                  ║")
        print(f"╚══════════════════════════════════════════════════════════════════════╝")
        
        arb_opps = self.find_arbitrage()
        for opp in arb_opps[:5]:
            emoji = "🟢" if opp['annual_return'] > 0 else "🔴"
            print(f"   {emoji} {opp['symbol']:6} 资金费率: {opp['funding_rate']:+.4f}% 年化: {opp['annual_return']:+.1f}%")
        
        # 优化组合
        print(f"\n╔══════════════════════════════════════════════════════════════════════╗")
        print(f"║                    📋 优化投资组合 ($10,000)                      ║")
        print(f"╚══════════════════════════════════════════════════════════════════════╝")
        
        portfolio = self.optimize_portfolio(10000)
        for a in portfolio.get('allocations', []):
            print(f"   🟢 {a['symbol']:8} ${a['capital']:>8,.0f} ({a['weight']:>5.1f}%) {a['change_24h']:+6.2f}%")
        
        print(f"\n   总分配: ${portfolio.get('allocated', 0):,.0f}")
        
        print("\n" + "=" * 70)
        
        return ""

def main():
    optimizer = BinanceOptimizer()
    optimizer.generate_report()

if __name__ == '__main__':
    main()
