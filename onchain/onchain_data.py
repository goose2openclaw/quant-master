"""
链上数据 - 交易所流量、链上指标
"""
import requests, time
from threading import Thread

class OnChainData:
    """
    链上数据获取
    使用公开API: Whale Alert, Glassnode, CoinGecko
    """
    def __init__(self, proxy=None):
        self.proxy = proxy
        self.cache = {}
        self.whale_alerts = []
        self.exchange_flows = {}
        self.active_addresses = {}
    
    def get_whale_transactions(self, min_value=1000000, limit=20):
        """获取大额转账 (Whale Alert API)"""
        # 简化: 使用公开whale alert端点
        try:
            r = requests.get(
                "https://api.whale-alert.io/v1/transactions",
                params={'min_value': min_value, 'limit': limit},
                proxies=self.proxy, timeout=10
            )
            if r.status_code == 200:
                data = r.json().get('transactions', [])
                for tx in data:
                    self.whale_alerts.append({
                        'time': tx.get('timestamp'),
                        'symbol': tx.get('symbol', '').upper(),
                        'amount': tx.get('amount'),
                        'value': tx.get('usd_value'),
                        'from': tx.get('from', {}).get('owner_type'),
                        'to': tx.get('to', {}).get('owner_type')
                    })
                return self.whale_alerts[-limit:]
        except Exception as e:
            print(f"[OnChain] Whale API error: {e}")
        return []
    
    def get_exchange_reserves(self, symbol):
        """获取交易所储备金"""
        # 使用CoinGecko
        try:
            symbol_id = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum',
                'USDT': 'tether',
                'USDC': 'usd-coin'
            }.get(symbol, symbol.lower())
            
            r = requests.get(
                f"https://api.coingecko.com/api/v3/coins/{symbol_id}",
                params={'tickers': 'false', 'market_data': 'true'},
                proxies=self.proxy, timeout=10
            )
            if r.status_code == 200:
                data = r.json()
                return {
                    'symbol': symbol,
                    'price': data['market_data']['current_price']['usd'],
                    'market_cap': data['market_data']['market_cap']['usd'],
                    'volume_24h': data['market_data']['total_volume']['usd']
                }
        except:
            pass
        return {}
    
    def get_funding_rate(self, symbol):
        """获取合约资金费率"""
        try:
            r = requests.get(
                f"https://fapi.binance.com/fapi/v1/premiumIndex",
                params={'symbol': symbol.upper()},
                proxies=self.proxy, timeout=10
            )
            if r.status_code == 200:
                d = r.json()
                return {
                    'symbol': symbol,
                    'funding_rate': float(d.get('lastFundingRate', 0)) * 100,
                    'next_funding': d.get('nextFundingTime')
                }
        except:
            pass
        return {}
    
    def get_open_interest(self, symbol):
        """获取合约持仓量"""
        try:
            r = requests.get(
                "https://fapi.binance.com/futures/data/openInterestHist",
                params={'symbol': symbol.upper(), 'period': '1d', 'limit': 10},
                proxies=self.proxy, timeout=10
            )
            if r.status_code == 200:
                data = r.json()
                if data:
                    return {
                        'symbol': symbol,
                        'open_interest': float(data[-1].get('sumOpenInterest', 0)),
                        'timestamp': data[-1].get('timestamp')
                    }
        except:
            pass
        return {}
    
    def get_liquidation_data(self, symbol, limit=50):
        """获取强平数据"""
        try:
            r = requests.get(
                "https://fapi.binance.com/futures/data/liquidationOrders",
                params={'symbol': symbol.upper(), 'limit': limit},
                proxies=self.proxy, timeout=10
            )
            if r.status_code == 200:
                return [{
                    'symbol': d['symbol'],
                    'side': d['side'],
                    'price': float(d['price']),
                    'qty': float(d['origQty']),
                    'value': float(d.get('usdValue', 0))
                } for d in r.json()]
        except:
            pass
        return []
    
    def monitor_exchange_flow(self, symbols=['BTC', 'ETH']):
        """监控交易所资金流"""
        flows = {}
        for sym in symbols:
            reserves = self.get_exchange_reserves(sym)
            if reserves:
                flows[sym] = reserves
        
        self.exchange_flows = flows
        return flows
    
    def get_market_summary(self, symbol):
        """获取市场综合信息"""
        return {
            'funding': self.get_funding_rate(symbol),
            'open_interest': self.get_open_interest(symbol),
            'liquidations': self.get_liquidation_data(symbol, 10)
        }

class WhaleTracker:
    """巨鲸追踪器"""
    def __init__(self, proxy=None):
        self.proxy = proxy
        self.alerts = []
        self.wallets = {}  # 已知巨鲸钱包
    
    def add_wallet(self, address, label):
        self.wallets[address.lower()] = label
    
    def check_transactions(self):
        """检查巨鲸交易"""
        onchain = OnChainData(self.proxy)
        txs = onchain.get_whale_transactions(min_value=1000000, limit=50)
        
        whale_txs = []
        for tx in txs:
            from_addr = tx.get('from', {}).get('address', '').lower()
            to_addr = tx.get('to', {}).get('address', '').lower()
            
            # 检查是否是已知巨鲸
            if from_addr in self.wallets:
                tx['wallet_label'] = self.wallets[from_addr]
                tx['direction'] = 'OUT'
                whale_txs.append(tx)
            elif to_addr in self.wallets:
                tx['wallet_label'] = self.wallets[to_addr]
                tx['direction'] = 'IN'
                whale_txs.append(tx)
        
        self.alerts.extend(whale_txs)
        self.alerts = self.alerts[-100:]  # 保留最近100条
        return whale_txs
