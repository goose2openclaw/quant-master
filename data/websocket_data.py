"""
WebSocket实时行情 - Binance WebSocket
"""
import websocket, json, time, threading
from queue import Queue

class WebSocketClient:
    """WebSocket客户端"""
    def __init__(self, proxy):
        self.proxy = proxy
        self.ws = None
        self.running = False
        self.subscriptions = []
        self.ticker_callbacks = []
        self.kline_callbacks = []
        self.depth_callbacks = []
        self._last_ping = 0
    
    def start(self):
        """启动WebSocket"""
        self.running = True
        self._connect()
    
    def stop(self):
        """停止WebSocket"""
        self.running = False
        if self.ws:
            self.ws.close()
    
    def _connect(self):
        """连接"""
        try:
            # 设置代理
            ws_proxy = None
            if self.proxy.get('http'):
                p = self.proxy['http'].replace('http://', '')
                ws_proxy = f"http://{p}"
            
            self.ws = websocket.WebSocketApp(
                "wss://stream.binance.com:9443/ws",
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                on_open=self._on_open
            )
            
            if ws_proxy:
                self.thread = threading.Thread(target=self.ws.run_forever, 
                    kwargs={'proxy_type':'http', 'http_proxy_host':ws_proxy.split(':')[0],
                            'http_proxy_port':int(ws_proxy.split(':')[1])})
            else:
                self.thread = threading.Thread(target=self.ws.run_forever)
            self.thread.daemon = True
            self.thread.start()
        except Exception as e:
            print(f"[WS] Connect error: {e}")
            time.sleep(5)
            if self.running:
                self._connect()
    
    def _on_open(self, ws):
        print("[WS] Connected")
        self._resubscribe()
    
    def _on_message(self, ws, msg):
        try:
            data = json.loads(msg)
            self._handle_message(data)
        except:
            pass
    
    def _on_error(self, ws, error):
        print(f"[WS] Error: {error}")
    
    def _on_close(self, ws):
        print("[WS] Closed")
        if self.running:
            time.sleep(5)
            self._connect()
    
    def _handle_message(self, data):
        """处理消息"""
        if 'e' in data:
            event_type = data['e']
            if event_type == '24hrTicker':
                for cb in self.ticker_callbacks:
                    cb(data)
            elif event_type == 'kline':
                for cb in self.kline_callbacks:
                    cb(data['k'])
            elif event_type == 'depthUpdate':
                for cb in self.depth_callbacks:
                    cb(data)
    
    def subscribe_ticker(self, symbol):
        """订阅Ticker"""
        self.subscriptions.append(f"{symbol.lower()}@ticker")
        if self.ws and self.ws.sock and self.ws.sock.connected:
            self.ws.send(json.dumps({
                "method": "SUBSCRIBE",
                "params": [f"{symbol.lower()}@ticker"],
                "id": int(time.time()*1000)
            }))
    
    def subscribe_kline(self, symbol, interval='1m'):
        """订阅K线"""
        self.subscriptions.append(f"{symbol.lower()}@kline_{interval}")
        if self.ws and self.ws.sock and self.ws.sock.connected:
            self.ws.send(json.dumps({
                "method": "SUBSCRIBE",
                "params": [f"{symbol.lower()}@kline_{interval}"],
                "id": int(time.time()*1000)
            }))
    
    def subscribe_depth(self, symbol, level=20):
        """订阅深度"""
        self.subscriptions.append(f"{symbol.lower()}@depth{level}")
        if self.ws and self.ws.sock and self.ws.sock.connected:
            self.ws.send(json.dumps({
                "method": "SUBSCRIBE",
                "params": [f"{symbol.lower()}@depth{level}@100ms"],
                "id": int(time.time()*1000)
            }))
    
    def _resubscribe(self):
        """重新订阅"""
        if self.subscriptions and self.ws:
            self.ws.send(json.dumps({
                "method": "SUBSCRIBE",
                "params": self.subscriptions,
                "id": int(time.time()*1000)
            }))
    
    def on_ticker(self, callback):
        """Ticker回调"""
        self.ticker_callbacks.append(callback)
    
    def on_kline(self, callback):
        """K线回调"""
        self.kline_callbacks.append(callback)
    
    def on_depth(self, callback):
        """深度回调"""
        self.depth_callbacks.append(callback)
