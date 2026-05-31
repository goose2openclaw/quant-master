"""
Audit Trail - 审计追踪
监管合规
"""
import time, json
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class AuditEvent:
    timestamp: float
    event_type: str
    user_id: str
    action: str
    resource: str
    details: Dict
    ip_address: str = ''
    session_id: str = ''

class AuditLogger:
    """
    审计日志
    所有操作可追溯
    """
    def __init__(self, log_dir='/tmp/audit_logs'):
        self.log_dir = log_dir
        self.events = []
        self.current_user = None
    
    def log(self, event_type: str, action: str, resource: str, details: Dict = None):
        """记录审计事件"""
        event = AuditEvent(
            timestamp=time.time(),
            event_type=event_type,
            user_id=self.current_user or 'system',
            action=action,
            resource=resource,
            details=details or {}
        )
        self.events.append(event)
        self._write_to_file(event)
        return event
    
    def _write_to_file(self, event: AuditEvent):
        """写入文件"""
        import os
        os.makedirs(self.log_dir, exist_ok=True)
        
        date = datetime.fromtimestamp(event.timestamp).strftime('%Y-%m-%d')
        filepath = f"{self.log_dir}/audit_{date}.jsonl"
        
        with open(filepath, 'a') as f:
            f.write(json.dumps(asdict(event)) + '\n')
    
    def query(self, filters: Dict = None, start_time: float = None,
              end_time: float = None) -> List[AuditEvent]:
        """查询审计事件"""
        results = self.events
        
        if start_time:
            results = [e for e in results if e.timestamp >= start_time]
        if end_time:
            results = [e for e in results if e.timestamp <= end_time]
        
        if filters:
            for key, value in filters.items():
                results = [e for e in results if getattr(e, key, None) == value]
        
        return results
    
    def generate_compliance_report(self, start: float, end: float) -> Dict:
        """生成合规报告"""
        events = self.query(start_time=start, end_time=end)
        
        by_type = {}
        for event in events:
            if event.event_type not in by_type:
                by_type[event.event_type] = 0
            by_type[event.event_type] += 1
        
        by_user = {}
        for event in events:
            if event.user_id not in by_user:
                by_user[event.user_id] = 0
            by_user[event.user_id] += 1
        
        return {
            'period': {'start': start, 'end': end},
            'total_events': len(events),
            'events_by_type': by_type,
            'events_by_user': by_user,
            'compliance_checks': self._check_compliance(events)
        }
    
    def _check_compliance(self, events: List[AuditEvent]) -> Dict:
        """检查合规"""
        checks = {
            'trade_audit': len([e for e in events if e.event_type == 'trade']),
            'config_changes': len([e for e in events if e.event_type == 'config']),
            'login_events': len([e for e in events if e.event_type == 'auth']),
        }
        return checks

class ImmutableLedger:
    """不可变账本"""
    def __init__(self):
        self.ledger = []
    
    def append(self, entry: Dict):
        """追加条目 (不可修改)"""
        import hashlib
        entry['hash'] = self._compute_hash(entry)
        entry['prev_hash'] = self.ledger[-1]['hash'] if self.ledger else 'genesis'
        self.ledger.append(entry)
    
    def _compute_hash(self, entry: Dict) -> str:
        data = json.dumps(entry, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()
    
    def verify(self) -> bool:
        """验证完整性"""
        for i, entry in enumerate(self.ledger):
            if i == 0:
                continue
            if entry['prev_hash'] != self.ledger[i-1]['hash']:
                return False
            if self._compute_hash({k: v for k, v in entry.items() if k != 'hash'}) != entry['hash']:
                return False
        return True
