#!/usr/bin/env python3
"""
G12 配置变更检测器
监控核心配置变更，变更前自动快照
"""
import os, hashlib, time

CONFIG_DIR = '/home/goave/.openclaw/workspace/scripts/'
MONITOR_FILES = [
    'hermes_g12_unified.py',
    'hermes_g12_god_mode.py',
    'hermes_g12_plus_trader.py'
]

STATE_FILE = '/tmp/g12_config_state.json'

def get_file_hash(path):
    if os.path.exists(path):
        with open(path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    return None

def check_changes():
    """检查配置是否有变更"""
    try:
        import json
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE) as f:
                state = json.load(f)
        else:
            state = {'hashes': {}}
    except:
        state = {'hashes': {}}
    
    changes = []
    for fname in MONITOR_FILES:
        path = CONFIG_DIR + fname
        current_hash = get_file_hash(path)
        old_hash = state['hashes'].get(fname)
        
        if current_hash != old_hash:
            changes.append({
                'file': fname,
                'old_hash': old_hash,
                'new_hash': current_hash,
                'action': 'modified' if old_hash else 'created'
            })
            state['hashes'][fname] = current_hash
    
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)
    
    return changes

def auto_snapshot_on_change():
    """检测到变更时自动快照"""
    changes = check_changes()
    if changes:
        print(f"🛡️ 检测到 {len(changes)} 个配置变更:")
        for c in changes:
            print(f"   {c['action']}: {c['file']}")
        
        # 调用快照系统
        import subprocess
        result = subprocess.run(
            ['python3', CONFIG_DIR + 'g12_governance/g12_snapshot.py', 'snap', '自动变更前快照'],
            capture_output=True, text=True
        )
        print(result.stdout.decode() if result.stdout else "")
        return True
    return False

if __name__ == '__main__':
    auto_snapshot_on_change()
