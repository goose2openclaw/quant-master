"""
交易所基类
"""
from abc import ABC, abstractmethod

class Exchange(ABC):
    """交易所基类"""
    def __init__(self, name, api_key, api_secret, proxy):
        self.name = name
        self.api_key = api_key
        self.api_secret = api_secret
        self.proxy = proxy
        self.connected = False
    
    @abstractmethod
    def connect(self): pass
    
    @abstractmethod
    def disconnect(self): pass
    
    @abstractmethod
    def get_balance(self): pass
    
    @abstractmethod
    def get_positions(self): pass
    
    @abstractmethod
    def get_ticker(self, symbol): pass
    
    @abstractmethod
    def get_klines(self, symbol, interval, limit): pass
    
    @abstractmethod
    def send_order(self, symbol, side, qty, price=None, order_type='MARKET'): pass
    
    @abstractmethod
    def cancel_order(self, order_id, symbol): pass
    
    @abstractmethod
    def get_order(self, order_id, symbol): pass
    
    def normalize_symbol(self, symbol):
        """标准化交易对"""
        return symbol.upper()

class ExchangeManager:
    """交易所管理器"""
    def __init__(self):
        self.exchanges = {}  # {name: Exchange}
        self.primary = None
    
    def add_exchange(self, exchange, primary=False):
        self.exchanges[exchange.name] = exchange
        if primary or not self.primary:
            self.primary = exchange.name
    
    def get_exchange(self, name=None):
        if name:
            return self.exchanges.get(name)
        if self.primary:
            return self.exchanges[self.primary]
        return None
    
    def get_all_exchanges(self):
        return list(self.exchanges.values())
    
    def connect_all(self):
        for ex in self.exchanges.values():
            ex.connect()
    
    def disconnect_all(self):
        for ex in self.exchanges.values():
            ex.disconnect()
