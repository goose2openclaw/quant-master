#!/usr/bin/env python3
"""Hermes持续运行包装器"""
import subprocess, time, sys, os

WORKSPACE = '/home/goose/.openclaw/workspace'
SCRIPTS = {
    'g16': f'{WORKSPACE}/scripts/hermes_g16.py',
    'g12_autoloop': f'{WORKSPACE}/scripts/hermes_g12_autoloop_v4.py',
    'g12_god_mode': f'{WORKSPACE}/scripts/hermes_g12_god_mode.py',
    'g12_unified': f'{WORKSPACE}/scripts/hermes_g12_unified.py',
    'g12_plus_trader': f'{WORKSPACE}/scripts/hermes_g12_plus_trader.py',
}

INTERVALS = {
    'g16': 300,        # 5分钟
    'g12_autoloop': 300,  # 5分钟
    'g12_god_mode': 300,  # 5分钟
    'g12_unified': 300,   # 5分钟
    'g12_plus_trader': 300,  # 5分钟
}

def run_script(name, path):
    log_file = f'{WORKSPACE}/logs/{name}.out'
    try:
        with open(log_file, 'a') as f:
            f.write(f'\n[{time.strftime("%Y-%m-%d %H:%M:%S")}] Running {name}\n')
        result = subprocess.run(
            ['python3', '-c', f'exec(open("{path}").read())'],
            capture_output=True, text=True, timeout=120,
            cwd=WORKSPACE
        )
        with open(log_file, 'a') as f:
            f.write(result.stdout[-500:] if result.stdout else '')
            if result.returncode != 0:
                f.write(f'ERROR: {result.stderr[-200:]}\n')
        return True
    except Exception as e:
        with open(log_file, 'a') as f:
            f.write(f'EXCEPTION: {e}\n')
        return False

def main():
    if len(sys.argv) < 2:
        print("用法: python3 run_hermes_continuous.py <script_name>")
        print(f"可用: {list(SCRIPTS.keys())}")
        sys.exit(1)
    
    name = sys.argv[1]
    if name not in SCRIPTS:
        print(f"未知脚本: {name}")
        sys.exit(1)
    
    path = SCRIPTS[name]
    interval = INTERVALS[name]
    
    print(f"启动 {name} 持续运行 (间隔{interval}秒)")
    
    while True:
        run_script(name, path)
        time.sleep(interval)

if __name__ == '__main__':
    main()
