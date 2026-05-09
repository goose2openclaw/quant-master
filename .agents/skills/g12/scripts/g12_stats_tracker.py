#!/usr/bin/env python3
import json
from datetime import datetime

TRADE_FILE = '/tmp/g12_plus_trades.json'
STATS_FILE = '/tmp/g12_daily_stats.json'

def load_trades():
    try:
        with open(TRADE_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def calc():
    trades = load_trades()
    now = datetime.now()
    today_0 = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    today = []
    for t in trades:
        try:
            t_time = datetime.fromisoformat(t['time'].replace('Z', '+00:00').split('.')[0])
            if t_time.replace(tzinfo=None) >= today_0:
                today.append(t)
        except:
            pass
    
    all_executed = [e for t in today for e in t.get('executed', [])]
    total_fee = sum(float(f.get('commission', 0)) for e in all_executed for f in e.get('result', {}).get('fills', []))
    
    stats = {
        'generated_at': now.isoformat(),
        'period': f"{today[0]['time'][:19] if today else 'N/A'} - {today[-1]['time'][:19] if today else 'N/A'}",
        'today_cycles': len(today),
        'total_signals': sum(len(t.get('signals', [])) for t in today),
        'executed_count': len(all_executed),
        'fee_usdt': round(total_fee, 4),
        'start_balance': today[0].get('balance', 0) if today else 0,
        'end_balance': today[-1].get('balance', 0) if today else 0,
    }
    
    with open(STATS_FILE, 'w') as f:
        json.dump(stats, f, indent=2)
    return stats

if __name__ == '__main__':
    print(json.dumps(calc(), indent=2))
