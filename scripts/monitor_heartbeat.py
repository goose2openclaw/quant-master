#!/usr/bin/env python3
"""
G12/G16心跳监控器 - 防止脚本僵死
每分钟检查一次,记录最后心跳时间
"""
import os, time, sys
from datetime import datetime

WORKSPACE = '/home/goose/.openclaw/workspace'
HEARTBEAT_FILE = f'{WORKSPACE}/logs/heartbeat_status.json'

def load_status():
    try:
        import json
        if os.path.exists(HEARTBEAT_FILE):
            with open(HEARTBEAT_FILE) as f:
                return json.load(f)
    except:
        pass
    return {}

def save_status(status):
    import json
    with open(HEARTBEAT_FILE, 'w') as f:
        json.dump(status, f, indent=2)

def update_heartbeat(name):
    status = load_status()
    status[name] = {
        'last_heartbeat': time.time(),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'alive': True
    }
    save_status(status)

def check_stale():
    """检查哪些进程心跳过期"""
    status = load_status()
    now = time.time()
    stale = []
    
    for name, info in status.items():
        last = info.get('last_heartbeat', 0)
        age = now - last
        if age > 600:  # 10分钟无心跳
            stale.append((name, age))
    
    return stale

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python3 monitor_heartbeat.py <update|check> [name]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'update':
        if len(sys.argv) < 3:
            print("需要提供进程名")
            sys.exit(1)
        update_heartbeat(sys.argv[2])
        print(f"心跳更新: {sys.argv[2]}")
    
    elif cmd == 'check':
        stale = check_stale()
        if stale:
            print("⚠️ 心跳过期:")
            for name, age in stale:
                print(f"  {name}: {age/60:.1f}分钟无心跳")
        else:
            print("✅ 所有进程心跳正常")
