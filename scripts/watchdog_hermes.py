#!/usr/bin/env python3
"""
Hermes/G12/G16 看门狗 - 防止进程僵死
功能:
1. 检测进程是否僵死(无输出/无响应)
2. 自动重启僵死进程
3. 记录僵死事件到日志
4. 发送告警通知
"""
import os, sys, time, subprocess, signal, requests
from datetime import datetime
from pathlib import Path

# ========== 配置 ==========
WORKSPACE = '/home/goose/.openclaw/workspace'
LOG_FILE = f'{WORKSPACE}/logs/watchdog_hermes.log'
PID_DIR = f'{WORKSPACE}/pids'
TELEGRAM_TOKEN = '8735448790:AAHi8eUhot2vWm9DY8PguicAgnOiR410njo'
TELEGRAM_CHAT = '6270866128'

# 进程配置: (名字, 脚本路径, 检测间隔秒, 允许无响应秒数)
PROCESSES = [
    ('hermes_g12', f'{WORKSPACE}/scripts/hermes_g12_autoloop_v4.py', 300, 600),
    ('hermes_g16', f'{WORKSPACE}/scripts/hermes_g16.py', 300, 600),
    ('go2se_v6a', 'go2se', 120, 300),
    ('go2se_v6i', 'go2se', 120, 300),
]

os.makedirs(f'{WORKSPACE}/logs', exist_ok=True)
os.makedirs(PID_DIR, exist_ok=True)

# ========== 日志 ==========
def log(msg, level='INFO'):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def log_error(msg):
    log(msg, 'ERROR')

def log_warn(msg):
    log(msg, 'WARN')

# ========== 进程检测 ==========
def get_pid(name):
    """获取进程PID"""
    try:
        result = subprocess.run(['pgrep', '-f', name], 
                               capture_output=True, text=True, timeout=5)
        pids = [int(p) for p in result.stdout.strip().split('\n') if p]
        return pids[0] if pids else None
    except:
        return None

def is_process_alive(pid):
    """检测进程是否存活"""
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False

def get_process_age(pid):
    """获取进程运行时间(秒)"""
    try:
        result = subprocess.run(['ps', '-o', 'etime=', '-p', str(pid)],
                               capture_output=True, text=True, timeout=5)
        etime = result.stdout.strip()
        if not etime:
            return 0
        # 格式: [[dd-]hh:]mm:ss
        parts = etime.strip().split('-')
        if len(parts) == 2:
            return int(parts[0])*86400 + parse_time(parts[1])
        return parse_time(etime)
    except:
        return 0

def parse_time(t):
    """解析时间字符串为秒"""
    parts = t.split(':')
    if len(parts) == 3:
        return int(parts[0])*3600 + int(parts[1])*60 + int(parts[2])
    elif len(parts) == 2:
        return int(parts[0])*60 + int(parts[1])
    return 0

def get_last_output_time(script_path):
    """获取脚本最后输出时间"""
    try:
        pid_file = f'{PID_DIR}/{Path(script_path).name}.pid'
        if os.path.exists(pid_file):
            with open(pid_file) as f:
                data = f.read().strip()
                if data:
                    parts = data.split('|')
                    if len(parts) >= 2:
                        return float(parts[1])
    except:
        pass
    return 0

def check_process(name, script_path, interval, timeout_sec):
    """检测单个进程"""
    pid = get_pid(name)
    
    if pid is None:
        log_warn(f"进程未运行: {name}")
        return {'status': 'dead', 'name': name}
    
    if not is_process_alive(pid):
        log_error(f"进程已僵死: {name} (PID:{pid})")
        return {'status': 'frozen', 'name': name, 'pid': pid}
    
    last_out = get_last_output_time(script_path)
    now = time.time()
    silence_sec = now - last_out
    
    if silence_sec > timeout_sec:
        log_error(f"进程无响应: {name} (沉默{silence_sec:.0f}秒, 超时{timeout_sec}秒)")
        return {'status': 'stuck', 'name': name, 'pid': pid, 'silence': silence_sec}
    
    return {'status': 'alive', 'name': name, 'pid': pid, 'silence': silence_sec}

# ========== 进程管理 ==========
def restart_process(name, script_path):
    """重启进程"""
    pid = get_pid(name)
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(2)
            # 强制杀死
            try:
                os.kill(pid, signal.SIGKILL)
            except:
                pass
        except:
            pass
    
    log(f"重启进程: {name}")
    
    try:
        if script_path.endswith('.py'):
            subprocess.Popen(['python3', script_path], 
                           cwd=WORKSPACE,
                           stdout=open(f'{WORKSPACE}/logs/{name}.out', 'a'),
                           stderr=subprocess.STDOUT)
        elif 'go2se' in name:
            # go2se进程
            mode = 'v6a' if 'v6a' in name else 'v6i'
            port = '8000' if 'v6a' in name else '8001'
            subprocess.Popen(['go2se', mode, '--port', port],
                           cwd=WORKSPACE,
                           stdout=open(f'{WORKSPACE}/logs/{name}.out', 'a'),
                           stderr=subprocess.STDOUT)
        
        log(f"启动成功: {name}")
        return True
    except Exception as e:
        log_error(f"启动失败: {name} - {e}")
        return False

def kill_and_notify(name, reason):
    """杀死进程并发送通知"""
    pid = get_pid(name)
    if pid:
        try:
            os.kill(pid, signal.SIGKILL)
        except:
            pass
    
    msg = f"🚨 进程被强制终止\n{name}\n原因: {reason}"
    send_telegram(msg)

# ========== 通知 ==========
def send_telegram(msg):
    """发送Telegram通知"""
    try:
        url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
        requests.post(url, {'chat_id': TELEGRAM_CHAT, 'text': msg}, timeout=10)
    except:
        pass

# ========== 主循环 ==========
def main():
    log("=== Hermes看门狗启动 ===")
    send_telegram("🔍 Hermes看门狗已启动")
    
    while True:
        for name, script_path, interval, timeout in PROCESSES:
            result = check_process(name, script_path, interval, timeout)
            
            if result['status'] == 'dead':
                log_warn(f"尝试启动死亡进程: {name}")
                restart_process(name, script_path)
                
            elif result['status'] == 'frozen':
                log_error(f"检测到僵死进程, 尝试重启: {name}")
                restart_process(name, script_path)
                send_telegram(f"♻️ 重启僵死进程: {name}")
                
            elif result['status'] == 'stuck':
                log_error(f"检测到无响应进程, 尝试重启: {name}")
                restart_process(name, script_path)
                send_telegram(f"⏰ 重启无响应进程: {name}")
        
        time.sleep(60)

if __name__ == '__main__':
    main()
