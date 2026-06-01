#!/usr/bin/env python3
"""QuantMaster API Server v8.3 - Autonomous Mode"""
import sys
sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

from dataclasses import asdict
from flask import Flask, jsonify, request
from quant_master_hub import QuantMasterHub
from autonomous_scanner.scanner import AutonomousScanner

app = Flask(__name__, static_folder='../public', static_url_path='')
hub = QuantMasterHub()
scanner = AutonomousScanner()

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/status')
def status():
    return jsonify({
        'status': 'running',
        'modules': len(hub.modules),
        'scanner_targets': len(scanner.targets),
        'mode': 'autonomous'
    })

@app.route('/api/scan')
def scan():
    results = scanner.scan_all()
    return jsonify({
        'timestamp': results[0].timestamp if results else None,
        'count': len(results),
        'results': [asdict(r) for r in results]
    })

@app.route('/api/scan/top')
def scan_top():
    results = scanner.scan_all()
    return jsonify({
        'timestamp': results[0].timestamp if results else None,
        'results': [asdict(r) for r in results[:10]]
    })

@app.route('/api/scan/buy')
def scan_buys():
    results = scanner.scan_all()
    buys = [r for r in results if r.action == 'LONG']
    return jsonify({'count': len(buys), 'results': [asdict(r) for r in buys]})

@app.route('/api/scan/sell')
def scan_sells():
    results = scanner.scan_all()
    sells = [r for r in results if r.action == 'SHORT']
    return jsonify({'count': len(sells), 'results': [asdict(r) for r in sells]})

@app.route('/api/analyze/<symbol>')
def analyze_symbol(symbol):
    analysis = scanner.analyze_symbol(symbol.upper())
    return jsonify(asdict(analysis))

@app.route('/api/market/snapshot')
def market_snapshot():
    return jsonify(hub.get_market_snapshot(request.args.get('symbol', 'BTC')))

@app.route('/api/signal/generate')
def signal():
    return jsonify(hub.generate_trading_signal(request.args.get('symbol', 'BTC')))

@app.route('/api/portfolio/health')
def portfolio_health():
    return jsonify(hub.get_portfolio_health())

if __name__ == '__main__':
    hub.start()
    scanner.running = True
    print("QuantMaster API v8.3 - Autonomous Mode")
    app.run(host='0.0.0.0', port=8088, debug=False, threaded=True)
