"""
跨交易所套利监控
"""
import time
from threading import Thread
from collections import defaultdict

class ArbitrageOpportunity:
    def __init__(self, symbol, buy_exchange, sell_exchange, buy_price, sell_price, profit_pct):
        self.symbol = symbol
        self.buy_exchange = buy_exchange
        self.sell_exchange = sell_exchange
        self.buy_price = buy_price
        self.sell_price = sell_price
        self.profit_pct = profit_pct
        self.timestamp = time.time()
        self.detected = False
        self.executed = False

class ArbitrageMonitor:
    """
    跨交易所套利监控
    检测交易所间价格差异
    """
    def __init__(self):
        self.exchanges = {}  # {name: exchange}
        self.prices = defaultdict(dict)  # {symbol: {exchange: price}}
        self.opportunities = []
        self.running = False
        self.min_profit_pct = 0.5  # 最小利润阈值
        self.thread = None
    
    def add_exchange(self, name, exchange):
        self.exchanges[name] = exchange
    
    def start(self):
        self.running = True
        self.thread = Thread(target=self._monitor_loop)
        self.thread.daemon = True
        self.thread.start()
        print("[Arbitrage] 监控启动")
    
    def stop(self):
        self.running = False
        print("[Arbitrage] 监控停止")
    
    def _monitor_loop(self):
        while self.running:
            try:
                # 获取所有交易所价格
                for name, exchange in self.exchanges.items():
                    for symbol in ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']:
                        try:
                            ticker = exchange.get_ticker(symbol)
                            if ticker:
                                self.prices[symbol][name] = ticker['last']
                        except:
                            pass
                
                # 检测套利机会
                self._find_opportunities()
                
                time.sleep(5)  # 5秒刷新
            except Exception as e:
                print(f"[Arbitrage] Error: {e}")
                time.sleep(10)
    
    def _find_opportunities(self):
        """寻找套利机会"""
        for symbol, exchange_prices in self.prices.items():
            if len(exchange_prices) < 2:
                continue
            
            # 找出最低价和最高价
            sorted_prices = sorted(exchange_prices.items(), key=lambda x: x[1])
            buy_exchange, buy_price = sorted_prices[0]
            sell_exchange, sell_price = sorted_prices[-1]
            
            # 计算利润
            profit_pct = (sell_price - buy_price) / buy_price * 100
            
            if profit_pct >= self.min_profit_pct:
                opp = ArbitrageOpportunity(
                    symbol, buy_exchange, sell_exchange,
                    buy_price, sell_price, profit_pct
                )
                self.opportunities.append(opp)
                print(f"[Arbitrage] 发现机会: {symbol} {buy_exchange}→{sell_exchange} 利润 {profit_pct:.2f}%")
        
        # 只保留最近100个
        self.opportunities = self.opportunities[-100:]
    
    def get_opportunities(self, min_profit=None):
        """获取套利机会"""
        if min_profit:
            return [o for o in self.opportunities if o.profit_pct >= min_profit]
        return self.opportunities
    
    def triangular_arbitrage(self):
        """三角套利 (BTC->ETH->USDT->BTC)"""
        # 简化实现
        opportunities = []
        
        # 示例: BTC/ETH, ETH/USDT, BTC/USDT
        try:
            btc_eth = self.prices.get('BTCUSDT', {}).get('binance', 0)
            eth_usdt = self.prices.get('ETHUSDT', {}).get('binance', 0)
            
            if btc_eth > 0 and eth_usdt > 0:
                # 简单三角套利计算
                # 1 BTC -> ETH -> USDT -> BTC
                btc_to_eth = 1 / btc_eth
                eth_to_usdt = btc_to_eth * eth_usdt
                usdt_to_btc = eth_to_usdt / btc_eth
                
                profit = (usdt_to_btc - 1) * 100
                if abs(profit) > 0.1:
                    opportunities.append({
                        'type': 'triangular',
                        'path': 'BTC->ETH->USDT->BTC',
                        'profit_pct': profit
                    })
        except:
            pass
        
        return opportunities
    
    def get_spread_history(self, symbol):
        """获取价差历史"""
        return [o for o in self.opportunities if o.symbol == symbol]
