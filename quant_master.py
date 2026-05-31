"""
QuantMaster 统一系统
整合所有模块
"""
from core import TradingEngine, EventEngine, GatewayManager, RiskManager
from core.gateway import BinanceSpotGateway
from data import DataSource, HistoryData
from data.websocket_data import WebSocketClient
from portfolio import PortfolioManager
from order import OrderManager
from monitor import Dashboard
from notification import Notifier, TelegramHandler
from log_system import TradeLogger
from permission import PermissionManager
from strategy_ide import StrategyIDE
from performance import PerformanceAnalyzer
from backtest.engine import BacktestEngine
from api_server.rest_api import app as flask_app, init_system as init_api
from factors.technical import TechnicalFactors

class QuantMaster:
    """
    QuantMaster 统一量化交易系统
    """
    def __init__(self):
        # 核心组件
        self.event_engine = EventEngine()
        self.trading_engine = TradingEngine(self.event_engine)
        self.gateway_manager = GatewayManager()
        self.risk_manager = RiskManager()
        
        # 数据组件
        self.data_source = None
        self.ws_client = None
        self.history_data = None
        
        # 交易组件
        self.portfolio = None
        self.order_manager = None
        
        # 监控组件
        self.dashboard = Dashboard(self.portfolio, self.order_manager)
        self.notifier = Notifier()
        self.logger = None
        self.performance = None
        
        # 工具组件
        self.permission = PermissionManager()
        self.strategy_ide = StrategyIDE('/tmp/strategies')
        self.factors = TechnicalFactors
        
        # 状态
        self.running = False
        self.api_initialized = False
    
    def initialize(self, api_key, api_secret, proxy):
        """初始化系统"""
        print("[QuantMaster] 初始化...")
        
        # 核心
        self.event_engine.start()
        
        # 数据
        self.data_source = DataSource(proxy)
        self.history_data = HistoryData(proxy)
        self.ws_client = WebSocketClient(proxy)
        
        # 网关
        gateway = BinanceSpotGateway(api_key, api_secret, proxy)
        self.gateway_manager.add_gateway('binance', gateway)
        gateway.connect()
        self.trading_engine.set_gateway(gateway)
        
        # 持仓
        self.portfolio = PortfolioManager()
        self.portfolio.set_data_source(self.data_source)
        self.portfolio.add_account('main', api_key, api_secret)
        
        # 订单
        self.order_manager = OrderManager(api_key, api_secret, proxy)
        
        # 监控
        self.dashboard = Dashboard(self.portfolio, self.order_manager)
        self.logger = TradeLogger('/tmp/qm_logs')
        self.performance = PerformanceAnalyzer(self.logger)
        
        # 通知
        self.notifier.add_handler(TelegramHandler(
            '8735448790:AAHi8eUhot2vWm9DY8PguicAgnOiR410njo',
            '6270866128'
        ))
        
        # API
        init_api(self)
        self.api_initialized = True
        
        print("[QuantMaster] 初始化完成")
        return True
    
    def start(self):
        """启动系统"""
        if self.running:
            return
        print("[QuantMaster] 启动...")
        self.running = True
        
        # 启动数据源
        self.data_source.start()
        self.ws_client.start()
        self.portfolio.start_sync()
        
        print("[QuantMaster] 运行中")
    
    def stop(self):
        """停止系统"""
        print("[QuantMaster] 停止...")
        self.running = False
        self.data_source.stop()
        self.ws_client.stop()
        self.portfolio.stop_sync()
        self.event_engine.stop()
        print("[QuantMaster] 已停止")
    
    def send_order(self, symbol, side, qty, price=None):
        """下单"""
        return self.order_manager.send_order(symbol, side, qty, price)
    
    def cancel_order(self, order_id):
        """取消订单"""
        return self.order_manager.cancel_order(order_id)
    
    def get_status(self):
        """获取状态"""
        return {
            'running': self.running,
            'positions': self.portfolio.get_all_positions() if self.portfolio else {},
            'total_value': self.portfolio.get_total_value() if self.portfolio else 0
        }
    
    def get_positions(self):
        return self.portfolio.get_all_positions() if self.portfolio else {}
    
    def get_orders(self):
        return self.order_manager.get_all_orders() if self.order_manager else []
    
    def get_account(self):
        return {'balance': 0, 'total': self.portfolio.get_total_value() if self.portfolio else 0}
    
    def get_performance(self):
        return self.performance.analyze() if self.performance else {}
    
    def get_risk_status(self):
        return self.risk_manager.get_status() if self.risk_manager else {}
    
    def run_backtest(self, strategy, symbol, start, end):
        """运行回测"""
        engine = BacktestEngine()
        engine.set_strategy(strategy)
        return engine.run(symbol, start, end)
    
    def run_api(self, port=8091):
        """启动API服务"""
        from api_server import rest_api
        rest_api.run(port)
    
    def run_ws_api(self, port=8092):
        """启动WebSocket服务"""
        from api_server import websocket_api
        websocket_api.run_ws(port)
