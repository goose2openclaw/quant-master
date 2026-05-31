"""
SQLite数据库 - 持久化存储
"""
import sqlite3, os, json
from datetime import datetime

class Database:
    """SQLite数据库"""
    def __init__(self, db_path='/tmp/quant_master.db'):
        self.db_path = db_path
        self.conn = None
        self._connect()
        self._init_tables()
    
    def _connect(self):
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
    
    def _init_tables(self):
        """初始化表"""
        c = self.conn.cursor()
        
        # 订单表
        c.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT UNIQUE,
                client_id TEXT,
                symbol TEXT,
                side TEXT,
                qty REAL,
                price REAL,
                type TEXT,
                status TEXT,
                filled_qty REAL,
                avg_price REAL,
                error TEXT,
                created_time REAL,
                updated_time REAL
            )
        ''')
        
        # 持仓表
        c.execute('''
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT UNIQUE,
                qty REAL,
                avg_price REAL,
                current_price REAL,
                unrealized_pnl REAL,
                update_time REAL
            )
        ''')
        
        # 交易记录表
        c.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT,
                symbol TEXT,
                side TEXT,
                qty REAL,
                price REAL,
                value REAL,
                pnl REAL,
                commission REAL,
                trade_time TEXT
            )
        ''')
        
        # 权益曲线表
        c.execute('''
            CREATE TABLE IF NOT EXISTS equity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time TEXT,
                equity REAL,
                position_value REAL,
                cash REAL
            )
        ''')
        
        # K线数据表
        c.execute('''
            CREATE TABLE IF NOT EXISTS klines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                interval TEXT,
                time TEXT,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                UNIQUE(symbol, interval, time)
            )
        ''')
        
        # 绩效表
        c.execute('''
            CREATE TABLE IF NOT EXISTS performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE,
                total_trades INTEGER,
                win_rate REAL,
                total_pnl REAL,
                max_drawdown REAL,
                sharpe_ratio REAL
            )
        ''')
        
        self.conn.commit()
    
    # === 订单 ===
    def save_order(self, order):
        c = self.conn.cursor()
        c.execute('''
            INSERT OR REPLACE INTO orders 
            (order_id, client_id, symbol, side, qty, price, type, status, filled_qty, avg_price, error, created_time, updated_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            order.order_id, getattr(order, 'client_id', ''), order.symbol,
            order.side, order.qty, order.price, order.type, order.status.value if hasattr(order.status, 'value') else order.status,
            order.filled_qty, order.avg_price, getattr(order, 'error', None),
            getattr(order, 'create_time', 0), getattr(order, 'update_time', 0)
        ))
        self.conn.commit()
    
    def get_orders(self, limit=100):
        c = self.conn.cursor()
        c.execute('SELECT * FROM orders ORDER BY created_time DESC LIMIT ?', (limit,))
        return [dict(row) for row in c.fetchall()]
    
    def get_order(self, order_id):
        c = self.conn.cursor()
        c.execute('SELECT * FROM orders WHERE order_id=?', (order_id,))
        row = c.fetchone()
        return dict(row) if row else None
    
    # === 持仓 ===
    def save_position(self, symbol, qty, avg_price, current_price=0):
        c = self.conn.cursor()
        pnl = (current_price - avg_price) * qty if qty > 0 else 0
        c.execute('''
            INSERT OR REPLACE INTO positions (symbol, qty, avg_price, current_price, unrealized_pnl, update_time)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (symbol, qty, avg_price, current_price, pnl, datetime.now().timestamp()))
        self.conn.commit()
    
    def get_positions(self):
        c = self.conn.cursor()
        c.execute('SELECT * FROM positions WHERE qty > 0')
        return [dict(row) for row in c.fetchall()]
    
    # === 交易 ===
    def save_trade(self, trade):
        c = self.conn.cursor()
        c.execute('''
            INSERT INTO trades (order_id, symbol, side, qty, price, value, pnl, commission, trade_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade.get('order_id', ''), trade.get('symbol', ''),
            trade.get('side', ''), trade.get('qty', 0),
            trade.get('price', 0), trade.get('value', 0),
            trade.get('pnl', 0), trade.get('commission', 0),
            trade.get('time', datetime.now().isoformat())
        ))
        self.conn.commit()
    
    def get_trades(self, limit=100):
        c = self.conn.cursor()
        c.execute('SELECT * FROM trades ORDER BY trade_time DESC LIMIT ?', (limit,))
        return [dict(row) for row in c.fetchall()]
    
    # === K线 ===
    def save_klines(self, symbol, interval, klines):
        c = self.conn.cursor()
        for k in klines:
            c.execute('''
                INSERT OR IGNORE INTO klines (symbol, interval, time, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (symbol, interval, k['time'].isoformat() if hasattr(k['time'], 'isoformat') else str(k['time']),
                  k['open'], k['high'], k['low'], k['close'], k['volume']))
        self.conn.commit()
    
    def get_klines(self, symbol, interval, limit=1000):
        c = self.conn.cursor()
        c.execute('''
            SELECT * FROM klines WHERE symbol=? AND interval=? 
            ORDER BY time DESC LIMIT ?
        ''', (symbol, interval, limit))
        return [dict(row) for row in c.fetchall()]
    
    # === 权益 ===
    def save_equity(self, equity, position_value, cash):
        c = self.conn.cursor()
        c.execute('''
            INSERT INTO equity (time, equity, position_value, cash)
            VALUES (?, ?, ?, ?)
        ''', (datetime.now().isoformat(), equity, position_value, cash))
        self.conn.commit()
    
    def get_equity_curve(self, days=30):
        c = self.conn.cursor()
        c.execute('''
            SELECT * FROM equity ORDER BY time DESC LIMIT ?
        ''', (days * 24 * 60,))  # 假设1分钟1条
        return [dict(row) for row in c.fetchall()]
    
    def close(self):
        if self.conn:
            self.conn.close()
