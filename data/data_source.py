"""
数据源 - Binance实时+历史
"""
import requests, time, json
from datetime import datetime, timedelta
from threading import Thread
from queue import Queue

class MarketData:
    """市场数据"""
    def __init__(self, symbol):
        self.symbol = symbol
        self.last_price = 0
        self.bid1 = 0
        self.ask1 = 0
        self.volume = 0
        self.timestamp = 0

class DataSource:
    """
    数据源 - 支持多交易所
    """
    def __init__(self, proxy):
        self.proxy = proxy
        self.cache = {}
        self.subscribers = []
        self.running = False
        self.thread = None
        
        # 交易所API
        self.binance_base = "https://api.binance.com"
        
    def start(self):
        """启动数据源"""
        self.running = True
        self.thread = Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()
        print("[DataSource] 启动")
    
    def stop(self):
        """停止数据源"""
        self.running = False
        print("[DataSource] 停止")
    
    def _run(self):
        """数据循环"""
        while self.running:
            try:
                self._update_all()
                time.sleep(0.5)  # 500ms刷新
            except Exception as e:
                print(f"[DataSource] Error: {e}")
                time.sleep(1)
    
    def _update_all(self):
        """更新所有订阅数据"""
        for sym in list(self.cache.keys()):
            self._fetch_ticker(sym)
    
    def _fetch_ticker(self, symbol):
        """获取Ticker"""
        try:
            r = requests.get(
                f"{self.binance_base}/api/v3/ticker/bookTicker",
                params={"symbol": symbol},
                proxies=self.proxy,
                timeout=5
            )
            if r.status_code == 200:
                d = r.json()
                self.cache[symbol].bid1 = float(d['bidPrice'])
                self.cache[symbol].ask1 = float(d['askPrice'])
                self.cache[symbol].last_price = (float(d['bidPrice']) + float(d['askPrice'])) / 2
                self.cache[symbol].timestamp = time.time()
        except Exception as e:
            pass
    
    def subscribe(self, symbol):
        """订阅行情"""
        if symbol not in self.cache:
            self.cache[symbol] = MarketData(symbol)
            self._fetch_ticker(symbol)
    
    def get_price(self, symbol):
        """获取价格"""
        if symbol in self.cache:
            return self.cache[symbol].last_price
        return 0
    
    def get_full_ticker(self, symbol):
        """获取完整Ticker"""
        return self.cache.get(symbol)

class HistoryData:
    """历史数据"""
    def __init__(self, proxy):
        self.proxy = proxy
        self.binance_base = "https://api.binance.com"
    
    def get_klines(self, symbol, interval='1m', limit=100):
        """获取K线"""
        try:
            r = requests.get(
                f"{self.binance_base}/api/v3/klines",
                params={"symbol": symbol, "interval": interval, "limit": limit},
                proxies=self.proxy,
                timeout=10
            )
            if r.status_code == 200:
                data = r.json()
                return [{
                    'time': datetime.fromtimestamp(k[0]/1000),
                    'open': float(k[1]),
                    'high': float(k[2]),
                    'low': float(k[3]),
                    'close': float(k[4]),
                    'volume': float(k[5])
                } for k in data]
        except:
            return []
    
    def get_closes(self, symbol, interval='1m', limit=100):
        """获取收盘价序列"""
        klines = self.get_klines(symbol, interval, limit)
        return [k['close'] for k in klines]
