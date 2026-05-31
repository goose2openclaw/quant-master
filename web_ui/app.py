"""
QuantMaster Web UI - 类QMT界面
基于Flask的Web图形界面
"""

from flask import Flask, render_template, jsonify, request
import sys
sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

from core import TradingEngine, EventEngine, GatewayManager, RiskManager
from core.gateway import BinanceSpotGateway

app = Flask(__name__)

# 全局组件
event_engine = EventEngine()
trading_engine = TradingEngine(event_engine)
gateway_manager = GatewayManager()
risk_manager = RiskManager()

@app.route('/')
def index():
    """主页 - 类QMT布局"""
    return render_template('index.html')

@app.route('/api/positions')
def get_positions():
    """获取持仓"""
    return jsonify(trading_engine.get_all_positions())

@app.route('/api/orders', methods=['POST'])
def send_order():
    """快捷下单"""
    data = request.json
    order = trading_engine.send_order(
        symbol=data['symbol'],
        side=data['side'],
        qty=data['qty'],
        price=data.get('price')
    )
    return jsonify({'success': True, 'order_id': order.order_id})

@app.route('/api/risk/status')
def risk_status():
    """风控状态"""
    return jsonify(risk_manager.get_status())

@app.route('/api/gateways')
def list_gateways():
    """网关列表"""
    return jsonify(list(gateway_manager.gateways.keys()))

def init():
    """初始化"""
    # 初始化事件引擎
    event_engine.start()
    
    # 添加币安网关
    gateway = BinanceSpotGateway(
        api_key="YOUR_KEY",
        api_secret="YOUR_SECRET",
        proxy={'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
    )
    gateway_manager.add_gateway('binance', gateway)
    gateway.connect()
    
    trading_engine.set_gateway(gateway)
    
    print("[QuantMaster] 系统初始化完成")

if __name__ == '__main__':
    init()
    app.run(host='0.0.0.0', port=8090, debug=False)
