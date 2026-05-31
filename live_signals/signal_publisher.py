"""
实时信号推送
"""
import time, json
from datetime import datetime
from queue import Queue
from threading import Thread

class TradingSignal:
    """交易信号"""
    def __init__(self, symbol, action, qty, price, confidence, source, reason):
        self.id = f"SIG_{int(time.time()*1000)}"
        self.symbol = symbol
        self.action = action  # BUY, SELL, CLOSE
        self.qty = qty
        self.price = price
        self.confidence = confidence  # 0-100
        self.source = source  # strategy name
        self.reason = reason
        self.timestamp = datetime.now().isoformat()
        self.status = 'pending'  # pending, executed, cancelled, expired
        self.executed_price = 0
        self.executed_time = None
        self.pnl = 0

class SignalPublisher:
    """
    实时信号发布器
    支持: Telegram, Webhook, WebSocket
    """
    def __init__(self):
        self.signal_queue = Queue()
        self.signals = []
        self.subscribers = []  # [(channel, config)]
        self.running = False
        self.thread = None
        
        # 信号过滤
        self.min_confidence = 60
        self.blacklist = set()
        self.whitelist = set()  # 非空时只在白名单内
    
    def add_telegram(self, bot_token, chat_id):
        self.subscribers.append(('telegram', {'token': bot_token, 'chat_id': chat_id}))
    
    def add_webhook(self, url):
        self.subscribers.append(('webhook', {'url': url}))
    
    def add_websocket_client(self, ws_client):
        self.subscribers.append(('websocket', ws_client))
    
    def set_filters(self, min_confidence=None, blacklist=None, whitelist=None):
        if min_confidence:
            self.min_confidence = min_confidence
        if blacklist:
            self.blacklist = set(blacklist)
        if whitelist:
            self.whitelist = set(whitelist)
    
    def publish(self, signal):
        """发布信号"""
        # 过滤
        if signal.confidence < self.min_confidence:
            return None
        
        if signal.symbol in self.blacklist:
            return None
        
        if self.whitelist and signal.symbol not in self.whitelist:
            return None
        
        signal.status = 'published'
        self.signals.append(signal)
        self.signal_queue.put(signal)
        
        # 广播到所有订阅者
        self._broadcast(signal)
        
        return signal
    
    def _broadcast(self, signal):
        """广播信号"""
        for channel, config in self.subscribers:
            try:
                if channel == 'telegram':
                    self._send_telegram(signal, config)
                elif channel == 'webhook':
                    self._send_webhook(signal, config)
                elif channel == 'websocket':
                    self._send_websocket(signal, config)
            except Exception as e:
                print(f"[SignalPublisher] {channel} error: {e}")
    
    def _send_telegram(self, signal, config):
        import requests
        emoji = "🟢" if signal.action == "BUY" else "🔴" if signal.action == "SELL" else "⚪"
        text = f"""
{emoji} *{signal.action}* Signal

📊 Symbol: `{signal.symbol}`
💰 Qty: `{signal.qty}`
💵 Price: `${signal.price:.6f}`
🎯 Confidence: `{signal.confidence}%`
📝 Reason: `{signal.reason}`
🤖 Source: `{signal.source}`
⏰ Time: `{signal.timestamp}`

ID: `{signal.id}`
        """
        
        requests.post(
            f"https://api.telegram.org/bot{config['token']}/sendMessage",
            json={'chat_id': config['chat_id'], 'text': text, 'parse_mode': 'Markdown'},
            timeout=10
        )
    
    def _send_webhook(self, signal, config):
        import requests
        data = {
            'id': signal.id,
            'symbol': signal.symbol,
            'action': signal.action,
            'qty': signal.qty,
            'price': signal.price,
            'confidence': signal.confidence,
            'reason': signal.reason,
            'source': signal.source,
            'timestamp': signal.timestamp
        }
        requests.post(config['url'], json=data, timeout=10)
    
    def _send_websocket(self, signal, config):
        # WebSocket发送
        pass
    
    def start(self):
        self.running = True
        self.thread = Thread(target=self._process_loop)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        self.running = False
    
    def _process_loop(self):
        while self.running:
            try:
                signal = self.signal_queue.get(timeout=1)
                # 处理信号 (日志、存储等)
                print(f"[Signal] {signal.action} {signal.symbol} @ {signal.price} (置信度: {signal.confidence}%)")
            except:
                pass
    
    def get_signals(self, limit=50):
        return self.signals[-limit:]
    
    def get_pending_signals(self):
        return [s for s in self.signals if s.status == 'pending']
    
    def update_signal_status(self, signal_id, status, executed_price=None, pnl=None):
        for s in self.signals:
            if s.id == signal_id:
                s.status = status
                if executed_price:
                    s.executed_price = executed_price
                    s.executed_time = datetime.now().isoformat()
                if pnl is not None:
                    s.pnl = pnl
                break
