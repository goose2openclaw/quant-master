"""
QuantMaster 融合模块
连接vnpy事件系统 + QMT交易引擎 + OPC执行
"""
from .event import EventEngine, Event
from .engine import TradingEngine
from .gateway import GatewayManager, BinanceSpotGateway
from .risk import RiskManager

# 导入vnpy模块
import sys
sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

from alpha.strategy.backtesting import BacktestingEngine
from alpha.dataset.processor import DataProcessor

class QuantMasterSystem:
    """
    统一量化系统 - vnpy事件 + QMT交易 + 风控
    """
    def __init__(self):
        # 核心组件
        self.event_engine = EventEngine()
        self.trading_engine = TradingEngine(self.event_engine)
        self.gateway_manager = GatewayManager()
        self.risk_manager = RiskManager()
        
        # vnpy组件
        self.backtesting_engine = BacktestingEngine()
        self.data_processor = DataProcessor()
        
        # 状态
        self.running = False
    
    def initialize(self, api_key, api_secret, proxy):
        """初始化"""
        print("[QuantMaster] 初始化系统...")
        
        # 启动事件引擎
        self.event_engine.start()
        
        # 配置网关
        gateway = BinanceSpotGateway(api_key, api_secret, proxy)
        self.gateway_manager.add_gateway('binance', gateway)
        gateway.connect()
        
        # 连接交易引擎
        self.trading_engine.set_gateway(gateway)
        
        print("[QuantMaster] 系统初始化完成")
        return True
    
    def shutdown(self):
        """关闭系统"""
        print("[QuantMaster] 关闭系统...")
        self.running = False
        self.event_engine.stop()
        self.gateway_manager.disconnect_all()
        print("[QuantMaster] 系统已关闭")
    
    def run_trading(self):
        """运行交易"""
        self.running = True
        print("[QuantMaster] 开始交易...")
        
        # 注册事件处理
        self.event_engine.register('order', self._on_order)
        self.event_engine.register('trade', self._on_trade)
        
        # 交易循环
        while self.running:
            # 处理持仓检查、信号生成、订单执行
            self._process_cycle()
    
    def _process_cycle(self):
        """处理周期"""
        # 1. 检查持仓
        positions = self.trading_engine.get_all_positions()
        
        # 2. 发送心跳事件
        self.event_engine.put(Event('heartbeat', {'time': None}))
        
        # 3. 等待处理
        import time
        time.sleep(1)
    
    def _on_order(self, event):
        """订单事件"""
        print(f"[Order] {event.data}")
    
    def _on_trade(self, event):
        """成交事件"""
        print(f"[Trade] {event.data}")
        self.risk_manager.on_trade(event.data)
    
    def run_backtest(self, strategy, data, start_date, end_date):
        """运行回测"""
        print("[QuantMaster] 运行回测...")
        self.backtesting_engine.run(strategy, data, start_date, end_date)
    
    def get_status(self):
        """获取状态"""
        return {
            'running': self.running,
            'positions': len(self.trading_engine.get_all_positions()),
            'gateway': list(self.gateway_manager.gateways.keys()),
            'risk': self.risk_manager.get_status()
        }
