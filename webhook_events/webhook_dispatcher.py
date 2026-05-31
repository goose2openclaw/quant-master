"""
Webhook Events - Webhook事件系统
"""
import json, time, hmac, hashlib, requests
from threading import Thread, Lock
from typing import Dict, List, Callable

class WebhookEvent:
    """Webhook事件"""
    def __init__(self, event_type, data, timestamp=None):
        self.event_type = event_type
        self.data = data
        self.timestamp = timestamp or time.time()
        self.delivery_attempts = 0
        self.last_delivery_time = None
        self.success = False

class WebhookEndpoint:
    """Webhook端点"""
    def __init__(self, url, events, secret=None, headers=None):
        self.url = url
        self.events = events  # 订阅的事件类型
        self.secret = secret
        self.headers = headers or {}
        self.enabled = True
        self.delivery_count = 0
        self.failure_count = 0

class WebhookDispatcher:
    """
    Webhook事件分发器
    """
    def __init__(self, max_retries=3, retry_delay=5):
        self.endpoints = {}  # {endpoint_id: WebhookEndpoint}
        self.event_queue = []
        self.lock = Lock()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.running = False
        self.thread = None
        self.callbacks = []  # 内存回调
    
    def add_endpoint(self, endpoint_id, url, events, secret=None, headers=None):
        """添加端点"""
        endpoint = WebhookEndpoint(url, events, secret, headers)
        self.endpoints[endpoint_id] = endpoint
        print(f"[Webhook] Added endpoint: {endpoint_id} -> {url}")
    
    def remove_endpoint(self, endpoint_id):
        """移除端点"""
        if endpoint_id in self.endpoints:
            del self.endpoints[endpoint_id]
    
    def subscribe(self, event_type, callback):
        """订阅内存回调"""
        self.callbacks.append({'event': event_type, 'callback': callback})
    
    def emit(self, event_type, data):
        """触发事件"""
        event = WebhookEvent(event_type, data)
        
        # 触发内存回调
        for cb in self.callbacks:
            if cb['event'] == event_type or cb['event'] == '*':
                try:
                    cb['callback'](event)
                except:
                    pass
        
        # 队列事件
        with self.lock:
            self.event_queue.append(event)
    
    def start(self):
        """启动分发"""
        self.running = True
        self.thread = Thread(target=self._dispatch_loop)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """停止分发"""
        self.running = False
    
    def _dispatch_loop(self):
        """分发循环"""
        while self.running:
            try:
                event = None
                with self.lock:
                    if self.event_queue:
                        event = self.event_queue.pop(0)
                
                if event:
                    self._dispatch_event(event)
                
                time.sleep(0.1)
            except Exception as e:
                print(f"[Webhook] Dispatch error: {e}")
    
    def _dispatch_event(self, event):
        """分发单个事件"""
        for endpoint_id, endpoint in self.endpoints.items():
            if not endpoint.enabled:
                continue
            
            if event.event_type not in endpoint.events and '*' not in endpoint.events:
                continue
            
            # 发送
            self._deliver(endpoint_id, event)
    
    def _deliver(self, endpoint_id, event):
        """投递事件"""
        endpoint = self.endpoints[endpoint_id]
        
        # 构建payload
        payload = {
            'event': event.event_type,
            'data': event.data,
            'timestamp': event.timestamp,
            'delivery_id': f"{endpoint_id}_{int(time.time()*1000)}"
        }
        
        # 签名
        headers = dict(endpoint.headers)
        if endpoint.secret:
            payload_json = json.dumps(payload)
            signature = hmac.new(
                endpoint.secret.encode(),
                payload_json.encode(),
                hashlib.sha256
            ).hexdigest()
            headers['X-Webhook-Signature'] = signature
        
        headers['Content-Type'] = 'application/json'
        
        # 发送请求
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    endpoint.url,
                    json=payload,
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code in [200, 201, 202, 204]:
                    endpoint.delivery_count += 1
                    event.success = True
                    return True
            except Exception as e:
                print(f"[Webhook] Delivery failed: {e}")
                time.sleep(self.retry_delay)
        
        endpoint.failure_count += 1
        return False
    
    def get_stats(self):
        """获取统计"""
        return {
            'endpoints': len(self.endpoints),
            'queue_size': len(self.event_queue),
            'total_deliveries': sum(e.delivery_count for e in self.endpoints.values()),
            'total_failures': sum(e.failure_count for e in self.endpoints.values())
        }
