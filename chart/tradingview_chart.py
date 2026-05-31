"""
实时TradingView风格图表
支持K线、指标、绘图工具
"""
import json, time
from datetime import datetime
from threading import Thread
from flask import Flask, render_template, Response

class CandleData:
    def __init__(self, time, open, high, low, close, volume):
        self.time = time
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume

class TradingViewChart:
    """
    TradingView风格图表引擎
    支持: K线、均线、MACD、RSI、成交量
    """
    def __init__(self, symbol='BTCUSDT'):
        self.symbol = symbol
        self.candles = []  # K线数据
        self.indicators = {}  # 指标缓存
        self.drawings = []  # 绘图工具
        self.subscribers = []  # WebSocket订阅者
        
        # 时间框架
        self.timeframes = ['1m', '5m', '15m', '1h', '4h', '1d']
        self.current_tf = '1m'
        
        # 配置
        self.config = {
            'show_grid': True,
            'show_volume': True,
            'show_overlay': True,
            'indicators': ['MA', 'BB', 'MACD', 'RSI']
        }
    
    def add_candle(self, candle):
        """添加K线"""
        self.candles.append(candle)
        # 保持最近1000根
        self.candles = self.candles[-1000:]
        
        # 更新指标
        self._update_indicators()
        
        # 推送更新
        self._broadcast({'type': 'candle', 'data': self._candle_to_dict(candle)})
    
    def _update_indicators(self):
        """更新指标计算"""
        closes = [c.close for c in self.candles]
        highs = [c.high for c in self.candles]
        lows = [c.low for c in self.candles]
        volumes = [c.volume for c in self.candles]
        
        if len(closes) < 2:
            return
        
        # MA
        self.indicators['MA5'] = self._ma(closes, 5)
        self.indicators['MA10'] = self._ma(closes, 10)
        self.indicators['MA20'] = self._ma(closes, 20)
        self.indicators['MA60'] = self._ma(closes, 60)
        
        # EMA
        self.indicators['EMA12'] = self._ema(closes, 12)
        self.indicators['EMA26'] = self._ema(closes, 26)
        
        # Bollinger Bands
        self.indicators['BB'] = self._bollinger(closes, 20, 2)
        
        # MACD
        self.indicators['MACD'] = self._macd(closes)
        
        # RSI
        self.indicators['RSI'] = self._rsi(closes, 14)
        
        # Volume
        self.indicators['Volume'] = volumes
    
    # 指标计算
    def _ma(self, data, period):
        if len(data) < period:
            return None
        return sum(data[-period:]) / period
    
    def _ema(self, data, period):
        if len(data) < period:
            return None
        multiplier = 2 / (period + 1)
        ema = sum(data[:period]) / period
        for price in data[period:]:
            ema = (price - ema) * multiplier + ema
        return ema
    
    def _bollinger(self, data, period, std_dev):
        if len(data) < period:
            return None, None, None
        window = data[-period:]
        mean = sum(window) / period
        variance = sum((p - mean) ** 2 for p in window) / period
        std = (variance ** 0.5) * std_dev
        return mean + std, mean, mean - std
    
    def _macd(self, data):
        if len(data) < 26:
            return None, None, None
        ema12 = self._ema(data, 12)
        ema26 = self._ema(data, 26)
        if ema12 is None or ema26 is None:
            return None, None, None
        macd = ema12 - ema26
        signal = macd * 0.9  # 简化signal
        histogram = macd - signal
        return macd, signal, histogram
    
    def _rsi(self, data, period=14):
        if len(data) < period + 1:
            return None
        deltas = [data[i] - data[i-1] for i in range(1, len(data))]
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        if avg_loss == 0:
            return 100
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def _candle_to_dict(self, candle):
        return {
            'time': candle.time,
            'open': candle.open,
            'high': candle.high,
            'low': candle.low,
            'close': candle.close,
            'volume': candle.volume
        }
    
    def _broadcast(self, msg):
        """广播到订阅者"""
        for subscriber in self.subscribers:
            try:
                subscriber(msg)
            except:
                pass
    
    def subscribe(self, callback):
        self.subscribers.append(callback)
    
    def get_chart_data(self, limit=500):
        """获取图表数据"""
        candles = self.candles[-limit:]
        return {
            'symbol': self.symbol,
            'timeframe': self.current_tf,
            'candles': [self._candle_to_dict(c) for c in candles],
            'indicators': {k: v for k, v in self.indicators.items() if v is not None},
            'drawings': self.drawings
        }
    
    def add_drawing(self, drawing_type, points, color='#00d4ff'):
        """添加绘图工具"""
        drawing = {
            'type': drawing_type,
            'points': points,
            'color': color
        }
        self.drawings.append(drawing)
        return drawing
    
    def clear_drawings(self):
        self.drawings = []


class ChartServer:
    """
    图表Web服务器
    提供TradingView图表展示
    """
    def __init__(self, chart, port=8095):
        self.chart = chart
        self.port = port
        self.app = Flask(__name__)
        self._setup_routes()
    
    def _setup_routes(self):
        @self.app.route('/')
        def index():
            return self._generate_html()
        
        @self.app.route('/data')
        def data():
            limit = int(request.args.get('limit', 500))
            return jsonify(self.chart.get_chart_data(limit))
        
        @self.app.route('/ws')
        def ws():
            return self._websocket_route()
        
        from flask import request, Response
        
        @self.app.route('/chart_data')
        def chart_data():
            return jsonify(self.chart.get_chart_data(100))
    
    def _generate_html(self):
        """生成TradingView风格HTML"""
        return '''
<!DOCTYPE html>
<html>
<head>
    <title>QuantMaster Chart</title>
    <script src="https://unpkg.com/lightweight-charts@4.0.0/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #0f0f14; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; }
        .header { background: #1a1a24; padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #2a2a3a; }
        .header h1 { color: #00d4ff; font-size: 18px; }
        .symbol { font-size: 20px; font-weight: bold; color: #fff; }
        .price { font-size: 24px; color: #00ff88; }
        .change { font-size: 14px; margin-left: 10px; }
        .change.up { color: #00ff88; }
        .change.down { color: #ff4757; }
        .chart-container { display: flex; }
        .main-chart { flex: 1; height: 60vh; }
        .indicators { flex: 1; height: 25vh; }
        .controls { background: #1a1a24; padding: 10px; display: flex; gap: 10px; }
        .controls button { background: #2a2a3a; border: none; color: #fff; padding: 8px 16px; border-radius: 4px; cursor: pointer; }
        .controls button:hover { background: #3a3a4a; }
        .controls button.active { background: #00d4ff; color: #000; }
        .tf-buttons { display: flex; gap: 5px; }
        .tf-buttons button { padding: 5px 10px; font-size: 12px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>QuantMaster</h1>
        <div>
            <span class="symbol" id="symbol">BTCUSDT</span>
            <span class="price" id="price">--</span>
            <span class="change" id="change">--</span>
        </div>
    </div>
    <div class="controls">
        <div class="tf-buttons">
            <button onclick="setTimeframe('1m')">1m</button>
            <button onclick="setTimeframe('5m')">5m</button>
            <button onclick="setTimeframe('15m')">15m</button>
            <button onclick="setTimeframe('1h')">1h</button>
            <button onclick="setTimeframe('4h')">4h</button>
            <button onclick="setTimeframe('1d')">1D</button>
        </div>
        <button onclick="toggleIndicator('MA')">MA</button>
        <button onclick="toggleIndicator('BB')">BB</button>
        <button onclick="toggleIndicator('MACD')">MACD</button>
        <button onclick="toggleIndicator('RSI')">RSI</button>
    </div>
    <div id="main-chart" class="main-chart"></div>
    <div id="indicator-chart" class="indicators"></div>

    <script>
        let chart, candlestickSeries, volumeSeries, lineSeries = {};
        let indicators = {MA: true, BB: false, MACD: true, RSI: false};
        
        async function init() {
            chart = LightweightCharts.createChart(document.getElementById('main-chart'), {
                width: window.innerWidth,
                height: window.innerHeight * 0.55,
                layout: { backgroundColor: '#0f0f14', textColor: '#e0e0e0' },
                grid: { vertLines: { color: '#1a1a24' }, horzLines: { color: '#1a1a24' } },
                crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
                timeScale: { borderColor: '#2a2a3a' },
                rightPriceScale: { borderColor: '#2a2a3a' }
            });
            
            candlestickSeries = chart.addCandlestickSeries({
                upColor: '#00ff88',
                downColor: '#ff4757',
                borderUpColor: '#00ff88',
                borderDownColor: '#ff4757',
                wickUpColor: '#00ff88',
                wickDownColor: '#ff4757'
            });
            
            volumeSeries = chart.addHistogramSeries({
                color: '#26a69a',
                priceFormat: { type: 'volume' },
                priceScaleId: '',
                scaleMargins: { top: 0.8, bottom: 0 }
            });
            
            // MA lines
            lineSeries.MA5 = chart.addLineSeries({ color: '#ffd700', lineWidth: 1 });
            lineSeries.MA20 = chart.addLineSeries({ color: '#00d4ff', lineWidth: 1 });
            
            // Load data
            await loadData();
            
            // Auto update
            setInterval(loadData, 1000);
        }
        
        async function loadData() {
            try {
                const resp = await fetch('/chart_data');
                const data = await resp.json();
                
                if (data.candles && data.candles.length > 0) {
                    const c = data.candles.map(candle => ({
                        time: candle.time,
                        open: candle.open,
                        high: candle.high,
                        low: candle.low,
                        close: candle.close
                    }));
                    candlestickSeries.setData(c);
                    
                    // Volume
                    const v = data.candles.map(candle => ({
                        time: candle.time,
                        value: candle.volume,
                        color: candle.close >= candle.open ? 'rgba(0,255,136,0.3)' : 'rgba(255,71,87,0.3)'
                    }));
                    volumeSeries.setData(v);
                    
                    // Update price display
                    const last = data.candles[data.candles.length-1];
                    document.getElementById('price').textContent = '$' + last.close.toFixed(2);
                    
                    // MA
                    if (data.indicators.MA5) {
                        const ma5 = data.candles.map((c, i) => ({time: c.time, value: data.indicators.MA5[i] || c.close}));
                        lineSeries.MA5.setData(ma5);
                    }
                }
            } catch(e) { console.log(e); }
        }
        
        function setTimeframe(tf) {
            document.querySelectorAll('.tf-buttons button').forEach(b => b.classList.remove('active'));
            event.target.classList.add('active');
        }
        
        function toggleIndicator(name) {
            indicators[name] = !indicators[name];
        }
        
        init();
        window.addEventListener('resize', () => chart.applyOptions({ width: window.innerWidth }));
    </script>
</body>
</html>
        '''
    
    def run(self):
        print(f"[ChartServer] TradingView图表启动: http://localhost:{self.port}")
        self.app.run(host='0.0.0.0', port=self.port, debug=False)
    
    def start_background(self):
        self.thread = Thread(target=self.run, daemon=True)
        self.thread.start()
