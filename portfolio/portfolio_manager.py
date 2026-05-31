"""
持仓管理器 - 多账号+资金分配
"""
import hashlib, hmac, time, requests
from threading import Thread

class Position:
    def __init__(self, symbol, qty, avg_price):
        self.symbol = symbol
        self.qty = qty
        self.avg_price = avg_price
        self.current_price = 0
        self.unrealized_pnl = 0
        self.update_time = time.time()

class Account:
    def __init__(self, name, api_key, api_secret, proxy):
        self.name = name
        self.api_key = api_key
        self.api_secret = api_secret
        self.proxy = proxy
        self.balance = 0
        self.positions = {}
        self.total_value = 0
        self.update_time = time.time()
    
    def update(self, data_source):
        ts = int(time.time() * 1000)
        params = f"timestamp={ts}&recvWindow=5000"
        sig = hmac.new(self.api_secret.encode(), params.encode(), hashlib.sha256).hexdigest()
        
        try:
            r = requests.get(
                f"https://api.binance.com/api/v3/account?{params}&signature={sig}",
                headers={"X-MBX-APIKEY": self.api_key},
                proxies=self.proxy, timeout=10
            )
            if r.status_code == 200:
                data = r.json()
                self.balance = float([b for b in data['balances'] if b['asset'] == 'USDT'][0]['free'])
                for b in data['balances']:
                    if float(b['free']) > 0 and b['asset'] != 'USDT':
                        sym = b['asset']
                        qty = float(b['free'])
                        price = data_source.get_price(sym + 'USDT') if data_source else 0
                        if price > 0:
                            self.positions[sym] = Position(sym, qty, price)
                self.total_value = self.balance + sum(p.qty * p.current_price for p in self.positions.values())
                self.update_time = time.time()
        except Exception as e:
            print(f"[Account] Error: {e}")

class PortfolioManager:
    def __init__(self):
        self.accounts = {}
        self.data_source = None
        self.running = False
        self.thread = None
    
    def set_data_source(self, ds):
        self.data_source = ds
    
    def add_account(self, name, api_key, api_secret):
        proxy = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
        self.accounts[name] = Account(name, api_key, api_secret, proxy)
        print(f"[Portfolio] 添加账户: {name}")
    
    def start_sync(self):
        self.running = True
        self.thread = Thread(target=self._sync_loop)
        self.thread.daemon = True
        self.thread.start()
        print("[Portfolio] 同步启动")
    
    def stop_sync(self):
        self.running = False
    
    def _sync_loop(self):
        while self.running:
            try:
                for account in self.accounts.values():
                    account.update(self.data_source)
                time.sleep(5)
            except Exception as e:
                print(f"[Portfolio] Sync error: {e}")
                time.sleep(10)
    
    def get_total_value(self):
        return sum(a.total_value for a in self.accounts.values())
    
    def get_all_positions(self):
        positions = {}
        for account in self.accounts.values():
            for sym, pos in account.positions.items():
                if sym not in positions:
                    positions[sym] = {'qty': 0, 'value': 0}
                positions[sym]['qty'] += pos.qty
                positions[sym]['value'] += pos.qty * pos.current_price
        return positions
