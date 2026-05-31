"""
Priority Gas Queue - 优先Gas队列
"""
from typing import Dict

class PriorityGasQueue:
    """
    优先Gas队列
    EIP-1559 PriorityFee优化
    """
    def __init__(self):
        self.pending_txs = []
    
    def estimate_priority_fee(self, urgency: str) -> float:
        """估算优先费用"""
        base_fee = 30  # Gwei
        
        multipliers = {
            'low': 1.0,
            'medium': 1.5,
            'high': 2.5,
            'urgent': 5.0
        }
        
        priority_fee = base_fee * multipliers.get(urgency, 1.0)
        
        return {
            'base_fee': base_fee,
            'priority_fee': priority_fee,
            'max_fee': priority_fee * 2,
            'estimated_wait_blocks': 12 if urgency == 'low' else 2 if urgency == 'urgent' else 5
        }
    
    def submit_with_priority(self, tx_hash: str, urgency: str, gas_limit: int) -> Dict:
        """提交优先交易"""
        fees = self.estimate_priority_fee(urgency)
        
        return {
            'tx_hash': tx_hash,
            'priority_fee': fees['priority_fee'],
            'max_fee': fees['max_fee'],
            'gas_limit': gas_limit,
            'estimated_wait': f"{fees['estimated_wait_blocks']} blocks",
            'position': len(self.pending_txs)
        }
