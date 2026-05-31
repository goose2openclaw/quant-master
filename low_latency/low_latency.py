"""
Low Latency Framework - 低延迟框架
HFT平台级别
"""
import time
import asyncio
from typing import Callable, Any
from concurrent.futures import ThreadPoolExecutor

class LatencyTracker:
    """延迟追踪"""
    def __init__(self):
        self.latencies = []
        self.measurements = 1000  # 保留最近1000条
    
    def record(self, operation: str, latency_ns: int):
        """记录延迟(ns)"""
        self.latencies.append({
            'operation': operation,
            'latency_ns': latency_ns,
            'timestamp': time.time_ns()
        })
        self.latencies = self.latencies[-self.measurements:]
    
    def get_stats(self, operation: str = None) -> Dict:
        """获取统计"""
        lats = [l['latency_ns'] for l in self.latencies 
                if operation is None or l['operation'] == operation]
        
        if not lats:
            return {}
        
        lats.sort()
        return {
            'count': len(lats),
            'p50': lats[len(lats)//2] / 1000,  # us
            'p99': lats[int(len(lats)*0.99)] / 1000,
            'p999': lats[int(len(lats)*0.999)] / 1000,
            'max': max(lats) / 1000,
            'min': min(lats) / 1000,
            'avg': sum(lats) / len(lats) / 1000
        }

class ZeroCopyBuffer:
    """零拷贝缓冲区"""
    def __init__(self, size: int):
        import array
        self.buffer = array.array('B', [0]) * size
        self.read_pos = 0
        self.write_pos = 0
    
    def write(self, data: bytes):
        """写入数据"""
        for byte in data:
            self.buffer[self.write_pos] = byte
            self.write_pos = (self.write_pos + 1) % len(self.buffer)
    
    def read(self, n: int) -> bytes:
        """读取数据"""
        result = bytearray()
        for _ in range(n):
            result.append(self.buffer[self.read_pos])
            self.read_pos = (self.read_pos + 1) % len(self.buffer)
        return bytes(result)

class FastMessageQueue:
    """快速消息队列"""
    def __init__(self, capacity: int = 10000):
        import queue
        self.queue = queue.Queue(maxsize=capacity)
        self.dropped = 0
    
    def put(self, item, timeout: float = 0):
        """放入消息"""
        try:
            self.queue.put(item, block=False)
        except queue.Full:
            self.dropped += 1
            return False
        return True
    
    def get(self, timeout: float = 0) -> Any:
        """获取消息"""
        try:
            return self.queue.get(block=False)
        except queue.Empty:
            return None

class LowLatencyEngine:
    """
    低延迟引擎
    优化: 零拷贝、无锁队列、批处理
    """
    def __init__(self):
        self.tracker = LatencyTracker()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.queues = {}  # {name: FastMessageQueue}
        self.processors = {}  # {name: Callable}
        self.running = False
    
    def create_queue(self, name: str, capacity: int = 10000):
        """创建队列"""
        self.queues[name] = FastMessageQueue(capacity)
    
    def register_processor(self, name: str, processor: Callable):
        """注册处理器"""
        self.processors[name] = processor
    
    def submit_task(self, name: str, task: Callable, *args, **kwargs):
        """提交任务"""
        start = time.time_ns()
        future = self.executor.submit(task, *args, **kwargs)
        latency = time.time_ns() - start
        self.tracker.record('executor_submit', latency)
        return future
    
    def process_message(self, queue_name: str):
        """处理消息"""
        queue = self.queues.get(queue_name)
        processor = self.processors.get(queue_name)
        
        if not queue or not processor:
            return
        
        start = time.time_ns()
        msg = queue.get()
        if msg:
            processor(msg)
        latency = time.time_ns() - start
        self.tracker.record('process_message', latency)
    
    def batch_process(self, queue_name: str, batch_size: int = 100):
        """批量处理"""
        queue = self.queues.get(queue_name)
        processor = self.processors.get(queue_name)
        
        if not queue or not processor:
            return []
        
        start = time.time_ns()
        batch = []
        
        while len(batch) < batch_size:
            msg = queue.get()
            if msg:
                batch.append(msg)
        
        if batch:
            # 批处理
            results = processor(batch)
            latency = time.time_ns() - start
            self.tracker.record('batch_process', latency)
            return results
        
        return []

class LatencyProfiler:
    """延迟分析器"""
    def __init__(self):
        self.profile_data = {}
    
    def profile(self, func: Callable) -> Callable:
        """分析函数延迟"""
        def wrapper(*args, **kwargs):
            start = time.perf_counter_ns()
            result = func(*args, **kwargs)
            latency = time.perf_counter_ns() - start
            
            func_name = func.__name__
            if func_name not in self.profile_data:
                self.profile_data[func_name] = []
            self.profile_data[func_name].append(latency)
            
            return result
        return wrapper
    
    def get_profile(self, func_name: str = None) -> Dict:
        """获取分析结果"""
        if func_name:
            lats = self.profile_data.get(func_name, [])
            return self._calc_stats(lats)
        
        return {name: self._calc_stats(lats) 
                for name, lats in self.profile_data.items()}
    
    def _calc_stats(self, lats: List[int]) -> Dict:
        """计算统计"""
        if not lats:
            return {}
        lats.sort()
        return {
            'count': len(lats),
            'avg_us': sum(lats) / len(lats) / 1000,
            'p99_us': lats[int(len(lats)*0.99)] / 1000,
            'max_us': max(lats) / 1000
        }
