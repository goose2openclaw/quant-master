#!/usr/bin/env python3
"""
G12自动循环看门狗 - 集成到autoloop脚本
每分钟记录心跳,超时自动重启
"""
import os, time, sys, signal
from datetime import datetime

WORKSPACE = '/home/goose/.openclaw/workspace'
HEARTBEAT_FILE = f'{WORKSPACE}/logs/heartbeat_status.json'
SCRIPT_NAME = 'hermes_g12_autoloop'
TIMEOUT_SEC = 600  # 10分钟无心跳则认为僵死

def load_json(path):
    try:
        import json
        with open(path) as f:
            return json.load(f)
    except:
        return {}

def save_json(path, data):
    import json
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def heartbeat():
    """记录心跳"""
    data = load_json(HEARTBEAT_FILE)
    data[SCRIPT_NAME] = {
        'last': time.time(),
        'ts': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'pid': os.getpid()
    }
    save_json(HEARTBEAT_FILE, data)

def check_heartbeat():
    """检查心跳是否过期"""
    data = load_json(HEARTBEAT_FILE)
    if SCRIPT_NAME not in data:
        return True  # 从未记录,认为过期
    
    last = data[SCRIPT_NAME].get('last', 0)
    age = time.time() - last
    
    if age > TIMEOUT_SEC:
        print(f"[GUARD] 心跳过期! {age/60:.1f}分钟无更新")
        return False
    return True

def setup_guard():
    """设置信号处理器,检测父进程是否存活"""
    def signal_handler(sig, frame):
        print(f"[GUARD] 收到信号 {sig}, 准备退出")
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

# 在循环中定期调用
_last_heartbeat = 0
def guard_step(interval=60):
    """在主循环中每分钟调用一次"""
    global _last_heartbeat
    now = time.time()
    if now - _last_heartbeat >= interval:
        heartbeat()
        _last_heartbeat = now
        
        # 检查自己是否僵死
        if not check_heartbeat():
            print("[GUARD] 检测到可能僵死,记录警告")
            # 这里可以触发告警

if __name__ == '__main__':
    print(f"[GUARD] 看门狗启动, PID={os.getpid()}")
    setup_guard()
    
    # 测试心跳
    heartbeat()
    time.sleep(2)
    
    # 检查
    if check_heartbeat():
        print("[GUARD] 心跳正常")
    else:
        print("[GUARD] 心跳过期!")
