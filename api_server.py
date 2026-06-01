#!/usr/bin/env python3
"""
QuantMaster Flask API Server
Frontend-Backend Integration
"""
import sys
sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

from flask import Flask, jsonify, request
from quant_master_hub import QuantMasterHub

app = Flask(__name__, static_folder='../public', static_url_path='')
hub = QuantMasterHub()

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/status')
def status():
    return jsonify({'status': 'running', 'modules': len(hub.modules)})

@app.route('/api/market/snapshot')
def market_snapshot():
    symbol = request.args.get('symbol', 'BTC')
    return jsonify(hub.get_market_snapshot(symbol))

@app.route('/api/market/all')
def market_all():
    return jsonify(hub.get_all_market_data())

@app.route('/api/signal/generate')
def signal():
    symbol = request.args.get('symbol', 'BTC')
    return jsonify(hub.generate_trading_signal(symbol))

@app.route('/api/order/place', methods=['POST'])
def order():
    data = request.json
    return jsonify(hub.place_order(
        data.get('symbol'), data.get('side'), data.get('amount')
    ))

@app.route('/api/dex/quote')
def dex_quote():
    return jsonify(hub.get_dex_quote(
        request.args.get('token_in', 'ETH'),
        request.args.get('token_out', 'USDT'),
        float(request.args.get('amount', 1000))
    ))

@app.route('/api/polymarket/markets')
def polymarket():
    return jsonify(hub.get_polymarket_markets())

@app.route('/api/portfolio/health')
def health():
    return jsonify(hub.get_portfolio_health())

if __name__ == '__main__':
    hub.start()
    app.run(host='0.0.0.0', port=8088, debug=False)
