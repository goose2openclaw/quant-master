#!/usr/bin/env python3
"""
G12 自动循环 v4 - 防僵死版
加入心跳监控,防止进程僵死
"""
import os, time, sys, signal, json
from datetime import datetime

WORKSPACE = "/home/goose/.openclaw/workspace"
HEARTBEAT_FILE = f"{WORKSPACE}/logs/heartbeat_status.json"
LOG_FILE = f"{WORKSPACE}/logs/g12_autoloop.log"

_last_heartbeat = 0
HEARTBEAT_INTERVAL = 60

def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return {}

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def heartbeat():
    global _last_heartbeat
    _last_heartbeat = time.time()
    data = load_json(HEARTBEAT_FILE)
    data["hermes_g12_autoloop"] = {
        "last": _last_heartbeat,
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "pid": os.getpid()
    }
    save_json(HEARTBEAT_FILE, data)

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except:
        pass

def guard_step():
    global _last_heartbeat
    now = time.time()
    if now - _last_heartbeat >= HEARTBEAT_INTERVAL:
        heartbeat()
        _last_heartbeat = now

def setup_signal():
    def handler(sig, frame):
        log(f"收到信号 {sig}, 退出")
        sys.exit(0)
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)

def main():
    log("G12自动循环v4启动 (防僵死版)")
    setup_signal()
    heartbeat()
    counter = 0
    while True:
        counter += 1
        guard_step()
        if counter % 10 == 0:
            log(f"运行中... 计数:{counter}")
        time.sleep(10)

if __name__ == "__main__":
    main()
