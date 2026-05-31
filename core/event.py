"""
事件引擎 - QMT核心 + vnpy事件驱动
"""
from datetime import datetime
from queue import Queue, Empty
from threading import Thread

class Event:
    """事件基类"""
    def __init__(self, type_, data=None):
        self.type = type_
        self.data = data
        self.datetime = datetime.now()

class EventEngine:
    """
    事件驱动引擎 - vnpy事件引擎 + QMT事件机制
    """
    EVENT_TICK = 'tick'
    EVENT_ORDER = 'order'
    EVENT_TRADE = 'trade'
    EVENT_POSITION = 'position'
    EVENT_ACCOUNT = 'account'
    EVENT_LOG = 'log'
    
    def __init__(self):
        self.queue = Queue()
        self.handlers = {}
        self.active = False
        self.thread = None
    
    def start(self):
        """启动事件引擎"""
        self.active = True
        self.thread = Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()
        print("[QuantMaster] 事件引擎已启动")
    
    def stop(self):
        """停止事件引擎"""
        self.active = False
        if self.thread:
            self.thread.join()
        print("[QuantMaster] 事件引擎已停止")
    
    def _run(self):
        """事件循环"""
        while self.active:
            try:
                event = self.queue.get(timeout=1)
                self._process(event)
            except Empty:
                continue
    
    def _process(self, event):
        """处理事件"""
        if event.type in self.handlers:
            for handler in self.handlers[event.type]:
                handler(event)
    
    def register(self, type_, handler):
        """注册事件处理"""
        if type_ not in self.handlers:
            self.handlers[type_] = []
        self.handlers[type_].append(handler)
    
    def put(self, event):
        """推送事件"""
        self.queue.put(event)
    
    def log(self, msg):
        """记录日志事件"""
        self.put(Event(self.EVENT_LOG, {'msg': msg}) if hasattr(self, 'EVENT_LOG') else None
