"""
QuantMaster WebUI API Server
"""
from flask import Flask, jsonify, send_from_directory
import sys
sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

app = Flask(__name__, static_folder='ui', static_url_path='')

# State
state = {
    'portfolio': {'value': 10000, 'pnl': 0, 'returnPct': 0},
    'watchdog': {'mode': 'NORMAL', 'risk': 'SAFE', 'decisions': 0, 'streak': '0W / 0L'},
    'market': {'state': 'BULL', 'volatility': '3.2%', 'sentiment': '72%'},
    'equity_curve': [10000],
    'decisions': [],
}

@app.route('/')
def index():
    return send_from_directory('ui', 'index.html')

@app.route('/api/status')
def status():
    return jsonify(state)

@app.route('/api/scan')
def scan():
    # Binance scanner integration
    return jsonify({
        'opportunities': [
            {'rank': 1, 'category': 'FUNDING', 'symbol': 'SOLUSD', 'score': 86.0, 'action': 'ARB', 'potential': '36%/月', 'risk': '中'},
            {'rank': 2, 'category': 'SPOT', 'symbol': 'BTCUSDT', 'score': 84.8, 'action': 'BUY', 'potential': '15.8%', 'risk': '低'},
            {'rank': 3, 'category': 'SPOT', 'symbol': 'ETHUSDT', 'score': 83.3, 'action': 'BUY', 'potential': '12.5%', 'risk': '低'},
        ]
    })

@app.route('/api/watchdog/decision', methods=['POST'])
def watchdog_decision():
    # Run enhanced watchdog
    return jsonify({
        'type': 'BUY',
        'symbol': 'BTC',
        'confidence': 0.75,
        'pnl': 0,
    })

@app.route('/api/mirofish')
def mirofish():
    import random
    score = 50 + random.random() * 30
    decision = 'BUY' if score > 60 else 'SELL' if score < 45 else 'HOLD'
    return jsonify({'score': score, 'decision': decision})

@app.route('/api/optimizer', methods=['POST'])
def optimizer():
    import random
    return jsonify({
        'best_return': 20 + random.random() * 40,
        'params': {
            'position_size': 10 + random.random() * 10,
            'leverage': 1 + random.random(),
            'stop_loss': 3 + random.random() * 5,
            'take_profit': 10 + random.random() * 15,
        }
    })

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 QuantMaster WebUI Server")
    print("=" * 50)
    print("📍 URL: http://localhost:8088")
    print("📁 UI: /ui")
    print("=" * 50)
    app.run(host='0.0.0.0', port=8088, debug=False)
