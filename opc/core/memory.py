"""
记忆模块 - 持续学习
"""
import json, os, time
from datetime import datetime

MEMORY_DIR = '/home/goose/.openclaw/workspace/opc/memory'
os.makedirs(MEMORY_DIR, exist_ok=True)

def save_trade(trade):
    """保存交易记录"""
    trade_file = f'{MEMORY_DIR}/trades.json'
    trades = []
    if os.path.exists(trade_file):
        try:
            trades = json.load(open(trade_file))
        except:
            trades = []
    
    trade['timestamp'] = datetime.now().isoformat()
    trades.append(trade)
    
    # 只保留最近1000条
    if len(trades) > 1000:
        trades = trades[-1000:]
    
    with open(trade_file, 'w') as f:
        json.dump(trades, f, indent=2)

def get_trade_history(limit=100):
    """获取交易历史"""
    trade_file = f'{MEMORY_DIR}/trades.json'
    if not os.path.exists(trade_file):
        return []
    try:
        trades = json.load(open(trade_file))
        return trades[-limit:]
    except:
        return []

def analyze_performance():
    """分析性能"""
    trades = get_trade_history(500)
    if not trades:
        return {'total': 0, 'win_rate': 0, 'avg_pnl': 0}
    
    completed = [t for t in trades if t.get('pnl_pct') is not None]
    if not completed:
        return {'total': len(trades), 'win_rate': 0, 'avg_pnl': 0}
    
    wins = [t for t in completed if t['pnl_pct'] > 0]
    pnls = [t['pnl_pct'] for t in completed]
    
    return {
        'total': len(trades),
        'completed': len(completed),
        'wins': len(wins),
        'win_rate': len(wins) / len(completed) * 100 if completed else 0,
        'avg_pnl': sum(pnls) / len(pnls) * 100 if pnls else 0
    }

def log_learning(message):
    """记录学习"""
    log_file = f'{MEMORY_DIR}/learnings.json'
    logs = []
    if os.path.exists(log_file):
        try:
            logs = json.load(open(log_file))
        except:
            logs = []
    
    logs.append({
        'timestamp': datetime.now().isoformat(),
        'message': message
    })
    
    if len(logs) > 500:
        logs = logs[-500:]
    
    with open(log_file, 'w') as f:
        json.dump(logs, f, indent=2)
