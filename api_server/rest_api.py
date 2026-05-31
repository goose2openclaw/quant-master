"""
REST API服务器
"""
from flask import Flask, jsonify, request
import sys
sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

app = Flask(__name__)

# 全局组件引用
system = None

def init_system(qm_system):
    global system
    system = qm_system

@app.route('/api/v1/status')
def status():
    """系统状态"""
    return jsonify(system.get_status() if system else {'error': 'Not initialized'})

@app.route('/api/v1/positions')
def positions():
    """持仓"""
    return jsonify(system.get_positions() if system else {})

@app.route('/api/v1/orders', methods=['GET'])
def list_orders():
    """订单列表"""
    return jsonify(system.get_orders() if system else [])

@app.route('/api/v1/orders', methods=['POST'])
def create_order():
    """创建订单"""
    if not system:
        return jsonify({'error': 'Not initialized'}), 500
    
    data = request.json
    order = system.send_order(
        symbol=data.get('symbol'),
        side=data.get('side'),
        qty=data.get('qty'),
        price=data.get('price')
    )
    return jsonify({'order_id': order.order_id, 'status': order.status.value})

@app.route('/api/v1/orders/<order_id>', methods=['DELETE'])
def cancel_order(order_id):
    """取消订单"""
    if not system:
        return jsonify({'error': 'Not initialized'}), 500
    result = system.cancel_order(order_id)
    return jsonify({'success': result})

@app.route('/api/v1/account')
def account():
    """账户信息"""
    return jsonify(system.get_account() if system else {})

@app.route('/api/v1/backtest', methods=['POST'])
def run_backtest():
    """运行回测"""
    from backtest.engine import BacktestEngine
    from strategies.rsi_strategy import RSIStrategy
    from data.data_source import HistoryData
    
    data = request.json
    symbol = data.get('symbol', 'BTCUSDT')
    
    engine = BacktestEngine(initial_capital=data.get('capital', 10000))
    strategy = RSIStrategy(symbol)
    engine.set_strategy(strategy)
    
    result = engine.run(symbol, data.get('start'), data.get('end'))
    return jsonify(result or {})

@app.route('/api/v1/strategies')
def list_strategies():
    """策略列表"""
    from strategies import __all__ as strategies
    return jsonify(strategies)

@app.route('/api/v1/performance')
def performance():
    """绩效"""
    return jsonify(system.get_performance() if system else {})

@app.route('/api/v1/risk/status')
def risk_status():
    """风控状态"""
    return jsonify(system.get_risk_status() if system else {})

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

def run(port=8091):
    print(f"[REST API] 启动: http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
