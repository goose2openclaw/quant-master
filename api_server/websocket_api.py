"""
WebSocket API - 实时数据推送
"""
import json, time
from threading import Thread
from flask_socketio import SocketIO, emit

socketio = SocketIO(cors_allowed_origins="*")

# 实时数据缓存
ticker_cache = {}
kline_cache = {}
order_cache = []

def init_ws():
    """初始化WebSocket"""
    print("[WebSocket API] 初始化")

@socketio.on('connect')
def on_connect():
    print("[WS] Client connected")
    emit('connected', {'status': 'ok'})

@socketio.on('disconnect')
def on_disconnect():
    print("[WS] Client disconnected")

@socketio.on('subscribe_ticker')
def subscribe_ticker(data):
    symbol = data.get('symbol', '').upper()
    emit('subscribed', {'channel': 'ticker', 'symbol': symbol})

@socketio.on('subscribe_kline')
def subscribe_kline(data):
    symbol = data.get('symbol', '').upper()
    interval = data.get('interval', '1m')
    emit('subscribed', {'channel': 'kline', 'symbol': symbol, 'interval': interval})

@socketio.on('subscribe_orders')
def subscribe_orders():
    emit('subscribed', {'channel': 'orders'})

def broadcast_ticker(ticker):
    """广播Ticker"""
    socketio.emit('ticker', ticker)

def broadcast_kline(kline):
    """广播K线"""
    socketio.emit('kline', kline)

def broadcast_order(order):
    """广播订单"""
    socketio.emit('order', order)

def broadcast_position(position):
    """广播持仓"""
    socketio.emit('position', position)

def run_ws(port=8092):
    print(f"[WebSocket API] 启动: ws://0.0.0.0:{port}")
    socketio.run(app=None, host='0.0.0.0', port=port, debug=False)
