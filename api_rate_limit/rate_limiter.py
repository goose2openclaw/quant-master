"""
API Rate Limiting - API限流
"""
import time
from collections import defaultdict, deque
from enum import Enum

class RateLimitType(Enum):
    FIXED_WINDOW = "fixed"
    SLIDING_WINDOW = "sliding"
    TOKEN_BUCKET = "token_bucket"

class RateLimitRule:
    """限流规则"""
    def __init__(self, endpoint, limit, window_sec, limit_type=RateLimitType.SLIDING_WINDOW):
        self.endpoint = endpoint
        self.limit = limit
        self.window_sec = window_sec
        self.limit_type = limit_type

class RateLimiter:
    """
    API限流器
    支持: 固定窗口/滑动窗口/令牌桶
    """
    def __init__(self):
        self.rules = {}  # {endpoint: RateLimitRule}
        self.counters = defaultdict(lambda: {'count': 0, 'reset_time': 0})
        self.sliding_windows = defaultdict(deque)
        self.token_buckets = {}  # {endpoint: {'tokens': float, 'last_refill': float}}
        
        # 默认限制
        self.default_limit = 100
        self.default_window = 60
    
    def add_rule(self, endpoint, limit, window_sec, limit_type=RateLimitType.SLIDING_WINDOW):
        """添加限流规则"""
        self.rules[endpoint] = RateLimitRule(endpoint, limit, window_sec, limit_type)
    
    def check_rate_limit(self, endpoint, client_id='default'):
        """
        检查限流
        返回: (allowed, remaining, reset_time)
        """
        key = f"{endpoint}:{client_id}"
        rule = self.rules.get(endpoint, RateLimitRule(endpoint, self.default_limit, self.default_window))
        
        if rule.limit_type == RateLimitType.FIXED_WINDOW:
            return self._check_fixed_window(key, rule)
        elif rule.limit_type == RateLimitType.SLIDING_WINDOW:
            return self._check_sliding_window(key, rule)
        elif rule.limit_type == RateLimitType.TOKEN_BUCKET:
            return self._check_token_bucket(key, rule)
        
        return True, rule.limit, 0
    
    def _check_fixed_window(self, key, rule):
        """固定窗口限流"""
        now = time.time()
        counter = self.counters[key]
        
        # 检查是否需要重置
        if now >= counter['reset_time']:
            counter['count'] = 0
            counter['reset_time'] = now + rule.window_sec
        
        if counter['count'] >= rule.limit:
            return False, 0, counter['reset_time']
        
        counter['count'] += 1
        remaining = rule.limit - counter['count']
        
        return True, remaining, counter['reset_time']
    
    def _check_sliding_window(self, key, rule):
        """滑动窗口限流"""
        now = time.time()
        window = self.sliding_windows[key]
        
        # 移除过期的请求
        cutoff = now - rule.window_sec
        while window and window[0] < cutoff:
            window.popleft()
        
        if len(window) >= rule.limit:
            return False, 0, window[0] + rule.window_sec if window else now
        
        window.append(now)
        remaining = rule.limit - len(window)
        
        return True, remaining, now + rule.window_sec
    
    def _check_token_bucket(self, key, rule):
        """令牌桶限流"""
        now = time.time()
        bucket = self.token_buckets.get(key, {'tokens': rule.limit, 'last_refill': now})
        
        # 补充令牌
        elapsed = now - bucket['last_refill']
        refill_rate = rule.limit / rule.window_sec
        new_tokens = elapsed * refill_rate
        bucket['tokens'] = min(rule.limit, bucket['tokens'] + new_tokens)
        bucket['last_refill'] = now
        
        self.token_buckets[key] = bucket
        
        if bucket['tokens'] < 1:
            return False, 0, now + (1 - bucket['tokens']) / refill_rate
        
        bucket['tokens'] -= 1
        return True, bucket['tokens'], now
    
    def get_usage(self, endpoint, client_id='default'):
        """获取使用情况"""
        key = f"{endpoint}:{client_id}"
        rule = self.rules.get(endpoint, RateLimitRule(endpoint, self.default_limit, self.default_window))
        
        if rule.limit_type == RateLimitType.FIXED_WINDOW:
            return {'count': self.counters[key]['count'], 'limit': rule.limit}
        elif rule.limit_type == RateLimitType.SLIDING_WINDOW:
            return {'count': len(self.sliding_windows[key]), 'limit': rule.limit}
        elif rule.limit_type == RateLimitType.TOKEN_BUCKET:
            return {'tokens': self.token_buckets.get(key, {}).get('tokens', rule.limit), 'limit': rule.limit}
        
        return {}

# 14. Webhook Events
cat > /home/goose/.openclaw/workspace/quant_master/webhook_events/__init__.py << 'EOF'
"""Webhook事件模块"""
