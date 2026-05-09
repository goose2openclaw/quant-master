#!/usr/bin/env python3
"""
G12 配置快照系统
在每次配置变更前自动创建快照，支持一键回滚
"""
import json, os, time, shutil
from datetime import datetime

BACKUP_DIR = '/home/goose/.openclaw/workspace/scripts/g12_backup/'
CONFIG_DIR = '/home/goose/.openclaw/workspace/scripts/'

SNAPSHOT_FILE = BACKUP_DIR + 'snapshots.json'
PROFIT_GUARD_FILE = BACKUP_DIR + 'profit_guard.json'

def ensure_backup_dir():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    if not os.path.exists(SNAPSHOT_FILE):
        with open(SNAPSHOT_FILE, 'w') as f:
            json.dump({'snapshots': [], 'current': None}, f)

def get_current_config():
    """获取当前所有G12配置"""
    configs = {}
    scripts = [
        'hermes_g12_unified.py',
        'hermes_g12_god_mode.py', 
        'hermes_g12_plus_trader.py',
        'hermes_g12_autoloop_v4.py'
    ]
    for script in scripts:
        path = CONFIG_DIR + script
        if os.path.exists(path):
            with open(path) as f:
                content = f.read()
            # 提取CONFIG字典
            if 'CONFIG' in content:
                configs[script] = content
    return configs

def create_snapshot(reason="手动快照"):
    """创建配置快照"""
    ensure_backup_dir()
    
    with open(SNAPSHOT_FILE) as f:
        data = json.load(f)
    
    snapshot = {
        'id': len(data['snapshots']) + 1,
        'timestamp': datetime.now().isoformat(),
        'reason': reason,
        'configs': get_current_config()
    }
    
    data['snapshots'].append(snapshot)
    data['current'] = snapshot['id']
    
    with open(SNAPSHOT_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ 快照创建成功: #{snapshot['id']} - {reason}")
    return snapshot['id']

def restore_snapshot(snapshot_id=None):
    """恢复指定快照"""
    ensure_backup_dir()
    
    with open(SNAPSHOT_FILE) as f:
        data = json.load(f)
    
    if snapshot_id is None:
        snapshot_id = data['current']
    
    target = None
    for s in data['snapshots']:
        if s['id'] == snapshot_id:
            target = s
            break
    
    if not target:
        print(f"❌ 快照 #{snapshot_id} 不存在")
        return False
    
    # 恢复配置
    for script, content in target['configs'].items():
        path = CONFIG_DIR + script
        with open(path, 'w') as f:
            f.write(content)
        print(f"✅ 已恢复: {script}")
    
    print(f"✅ 成功恢复到快照 #{snapshot_id}")
    return True

def list_snapshots():
    """列出所有快照"""
    ensure_backup_dir()
    with open(SNAPSHOT_FILE) as f:
        data = json.load(f)
    
    print("\n📸 G12 配置快照列表:")
    print("-" * 60)
    for s in sorted(data['snapshots'], key=lambda x: -x['id']):
        marker = " ←当前" if s['id'] == data['current'] else ""
        print(f"  #{s['id']:2d} | {s['timestamp'][:19]} | {s['reason']}{marker}")
    print("-" * 60)

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'snap':
            reason = sys.argv[2] if len(sys.argv) > 2 else "手动快照"
            create_snapshot(reason)
        elif cmd == 'list':
            list_snapshots()
        elif cmd == 'restore':
            sid = int(sys.argv[2]) if len(sys.argv) > 2 else None
            restore_snapshot(sid)
        elif cmd == 'rollback':
            # 回滚到上一个快照
            with open(SNAPSHOT_FILE) as f:
                data = json.load(f)
            current = data['current']
            candidates = [s for s in data['snapshots'] if s['id'] < current]
            if candidates:
                restore_snapshot(candidates[-1]['id'])
    else:
        print("用法: python3 g12_snapshot.py [snap|list|restore|rollback]")
        list_snapshots()
