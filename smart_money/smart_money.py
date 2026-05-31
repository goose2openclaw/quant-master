"""
Smart Money Tracking - 聪明钱追踪
"""
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class SmartMoneyFlow:
    address: str
    label: str
    flow_type: str  # INFLOW/OUTFLOW
    amount: float
    timestamp: float

class SmartMoneyTracker:
    """
    聪明钱追踪
    追踪机构/聪明地址行为
    """
    def __init__(self):
        self.smart_addresses = {
            '0x1a2b3c...': 'Binance Hot Wallet',
            '0x4d5e6f...': 'Coinbase Custody',
            '0x7g8h9i...': 'Robinhood',
            '0xabc...': 'Jump Trading',
            '0xdef...': 'Alameda Research'
        }
        self.flows = []
    
    def track_flow(self, address: str, flow_type: str, amount: float):
        """追踪资金流动"""
        label = self.smart_addresses.get(address, 'Unknown')
        flow = SmartMoneyFlow(address, label, flow_type, amount, __import__('time').time())
        self.flows.append(flow)
    
    def get_smarter_money_index(self, symbol: str) -> Dict:
        """获取聪明钱指数"""
        recent = self.flows[-100:]  # 最近100条
        
        inflows = sum(f.amount for f in recent if f.flow_type == 'INFLOW')
        outflows = sum(f.amount for f in recent if f.flow_type == 'OUTFLOW')
        
        return {
            'symbol': symbol,
            'inflows': inflows,
            'outflows': outflows,
            'net_flow': inflows - outflows,
            'smart_money_index': (inflows - outflows) / (inflows + outflows + 1) * 100,
            'signal': 'BULLISH' if inflows > outflows * 1.2 else 'BEARISH' if outflows > inflows * 1.2 else 'NEUTRAL'
        }
    
    def find_known_wallets(self, token: str) -> List[Dict]:
        """查找已知钱包"""
        known = []
        for addr, label in self.smart_addresses.items():
            known.append({
                'address': addr,
                'label': label,
                'activity': 'ACTIVE' if any(f.address == addr for f in self.flows[-50:]) else 'INACTIVE'
            })
        return known
