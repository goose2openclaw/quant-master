#!/usr/bin/env python3
"""
QuantMaster Web UI - 融合系统统一入口
QMT界面 + vnpy事件 + OPC执行
"""

from flask import Flask, render_template, jsonify, request
import sys
sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

from core import TradingEngine, EventEngine, GatewayManager, RiskManager
from core.gateway import BinanceSpotGateway
from core.integration import QuantMasterSystem

app = Flask(__name__)

# 全局系统
system = None

def init_system():
    """初始化系统"""
    global system
    system = QuantMasterSystem()
    
    # 使用OPC配置
    API_KEY = "QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61"
    API_SECRET = "BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk"
    PROXY = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
    
    system.initialize(API_KEY, API_SECRET, PROXY)
    return system

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def status():
    if system is None:
        return jsonify({'error': 'Not initialized'})
    return jsonify(system.get_status())

@app.route('/api/positions')
def positions():
    if system is None:
        return jsonify({})
    return jsonify(system.trading_engine.get_all_positions())

@app.route('/api/order', methods=['POST'])
def order():
    if system is None:
        return jsonify({'success': False, 'error': 'Not initialized'})
    
    data = request.json
    order = system.trading_engine.send_order(
        data['symbol'],
        data['side'],
        data['qty']
    )
    return jsonify({'success': True, 'order_id': order.order_id})

@app.route('/api/risk/status')
def risk():
    if system is None:
        return jsonify({})
    return jsonify(system.risk_manager.get_status())

@app.route('/api/gateways')
def gateways():
    if system is None:
        return jsonify([])
    return jsonify(list(system.gateway_manager.gateways.keys()))

if __name__ == '__main__':
    init_system()
    print("[QuantMaster] Web UI 启动: http://localhost:8090")
    app.run(host='0.0.0.0', port=8090, debug=False)
