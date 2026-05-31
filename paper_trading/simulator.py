"""
Paper交易模拟器
"""
import time, json, os
from datetime import datetime
from threading import Lock

class PaperOrder:
    def __init__(self, symbol, side, qty, price, order_type='MARKET'):
        self.order_id = f"PAPER_{int(time.time()*1000)}"
        self.symbol = symbol
        self.side = side
        self.qty = qty
        self.price = price
        self.type = order_type
        self.status = 'filled'
        self.filled_price = price
        self.filled_qty = qty
        self.create_time = time.time()
        self.fill_time = time.time()

class PaperPosition:
    def __init__(self, symbol):
        self.symbol = symbol
        self.qty = 0
        self.avg_price = 0
        self.realized_pnl = 0

class PaperAccount:
    def __init__(self, initial_balance=10000):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.positions = {}  # {symbol: PaperPosition}
        self.orders = []
        self.trades = []
        self.equity_curve = []
    
    def update_equity(self, prices):
        """更新权益"""
        pos_value = sum(
            pos.qty * prices.get(pos.symbol, pos.avg_price)
            for pos in self.positions.values()
        )
        equity = self.balance + pos_value
        self.equity_curve.append({
            'time': datetime.now().isoformat(),
            'equity': equity,
            'cash': self.balance,
            'position_value': pos_value
        })
        return equity

class PaperSimulator:
    """
    Paper交易模拟器
    模拟真实交易所行为,用于策略测试
    """
    def __init__(self, initial_balance=10000, commission=0.001, slippage=0.0005):
        self.account = PaperAccount(initial_balance)
        self.commission = commission  # 手续费率
        self.slippage = slippage  # 滑点
        self.prices = {}  # 当前价格
        self.running = False
        self.lock = Lock()
        self.fee_tracker = {'buy': 0, 'sell': 0}
    
    def set_price(self, symbol, price):
        """设置当前价格"""
        self.prices[symbol] = price
    
    def buy(self, symbol, qty, price=None):
        """模拟买入"""
        with self.lock:
            price = price or self.prices.get(symbol)
            if not price:
                return {'success': False, 'msg': 'No price'}
            
            # 考虑滑点
            fill_price = price * (1 + self.slippage)
            cost = fill_price * qty
            commission_fee = cost * self.commission
            
            if self.account.balance < cost + commission_fee:
                return {'success': False, 'msg': 'Insufficient balance'}
            
            # 执行
            self.account.balance -= (cost + commission_fee)
            self.fee_tracker['buy'] += commission_fee
            
            # 更新持仓
            if symbol not in self.account.positions:
                self.account.positions[symbol] = PaperPosition(symbol)
            
            pos = self.account.positions[symbol]
            total_cost = pos.qty * pos.avg_price + cost
            pos.qty += qty
            pos.avg_price = total_cost / pos.qty if pos.qty > 0 else 0
            
            # 记录订单
            order = PaperOrder(symbol, 'BUY', qty, fill_price)
            self.account.orders.append(order)
            self.account.trades.append({
                'time': datetime.now().isoformat(),
                'order_id': order.order_id,
                'symbol': symbol,
                'side': 'BUY',
                'qty': qty,
                'price': fill_price,
                'commission': commission_fee
            })
            
            return {
                'success': True,
                'order_id': order.order_id,
                'symbol': symbol,
                'side': 'BUY',
                'qty': qty,
                'price': fill_price,
                'commission': commission_fee
            }
    
    def sell(self, symbol, qty=None, price=None):
        """模拟卖出"""
        with self.lock:
            price = price or self.prices.get(symbol)
            if not price:
                return {'success': False, 'msg': 'No price'}
            
            pos = self.account.positions.get(symbol)
            if not pos or pos.qty == 0:
                return {'success': False, 'msg': 'No position'}
            
            qty = qty or pos.qty
            qty = min(qty, pos.qty)
            
            # 考虑滑点
            fill_price = price * (1 - self.slippage)
            proceeds = fill_price * qty
            commission_fee = proceeds * self.commission
            
            # 计算已实现盈亏
            pnl = (fill_price - pos.avg_price) * qty
            pos.realized_pnl += pnl
            
            # 执行
            self.account.balance += (proceeds - commission_fee)
            self.fee_tracker['sell'] += commission_fee
            pos.qty -= qty
            
            if pos.qty == 0:
                pos.avg_price = 0
            
            # 记录
            order = PaperOrder(symbol, 'SELL', qty, fill_price)
            self.account.orders.append(order)
            self.account.trades.append({
                'time': datetime.now().isoformat(),
                'order_id': order.order_id,
                'symbol': symbol,
                'side': 'SELL',
                'qty': qty,
                'price': fill_price,
                'pnl': pnl,
                'commission': commission_fee
            })
            
            return {
                'success': True,
                'order_id': order.order_id,
                'symbol': symbol,
                'side': 'SELL',
                'qty': qty,
                'price': fill_price,
                'pnl': pnl,
                'commission': commission_fee
            }
    
    def get_position(self, symbol):
        return self.account.positions.get(symbol)
    
    def get_all_positions(self):
        return {k: {'symbol': v.symbol, 'qty': v.qty, 'avg_price': v.avg_price, 'realized_pnl': v.realized_pnl}
                for k, v in self.account.positions.items() if v.qty != 0}
    
    def get_account(self):
        equity = self.account.update_equity(self.prices)
        return {
            'initial_balance': self.account.initial_balance,
            'balance': self.account.balance,
            'equity': equity,
            'position_value': equity - self.account.balance,
            'total_pnl': equity - self.account.initial_balance,
            'total_pnl_pct': (equity - self.account.initial_balance) / self.account.initial_balance * 100,
            'total_commission': sum(self.fee_tracker.values()),
            'buy_fees': self.fee_tracker['buy'],
            'sell_fees': self.fee_tracker['sell']
        }
    
    def get_orders(self, limit=50):
        return self.account.orders[-limit:]
    
    def get_trades(self, limit=50):
        return self.account.trades[-limit:]
    
    def get_equity_curve(self):
        return self.account.equity_curve
    
    def save_results(self, filepath):
        """保存结果"""
        results = {
            'account': self.get_account(),
            'positions': self.get_all_positions(),
            'trades': self.get_trades(1000),
            'equity_curve': self.get_equity_curve()
        }
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"[PaperSim] 结果已保存: {filepath}")
    
    def run_strategy(self, strategy, datafeed, days=30):
        """运行策略模拟"""
        print(f"[PaperSim] 开始模拟 {days} 天")
        self.running = True
        
        day_count = 0
        cycle = 0
        
        while self.running and day_count < days:
            # 获取当前价格
            ticker = datafeed.get_ticker()
            if ticker:
                self.set_price(ticker['symbol'], ticker['last'])
            
            # 策略信号
            signal = strategy.on_tick(self.prices)
            
            if signal:
                if signal['action'] == 'BUY':
                    self.buy(signal['symbol'], signal.get('qty', 0.01))
                elif signal['action'] == 'SELL':
                    self.sell(signal['symbol'], signal.get('qty'))
            
            time.sleep(60)  # 1分钟循环
            cycle += 1
            
            if cycle % 1440 == 0:  # 每天
                day_count += 1
        
        self.running = False
        print(f"[PaperSim] 模拟结束: {len(self.account.trades)} 笔交易")
        return self.get_account()
