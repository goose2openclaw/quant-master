"""
Corporate Actions - 公司行动处理
分红/拆股/并购
"""
from datetime import datetime
from dataclasses import dataclass

@dataclass
class CorporateAction:
    symbol: str
    action_type: str  # DIVIDEND, SPLIT, MERGER, ACQUISITION
    effective_date: float
    details: dict

class CorporateActionProcessor:
    """
    公司行动处理器
    """
    def __init__(self):
        self.pending_actions = []
        self.processed_actions = []
    
    def add_action(self, action: CorporateAction):
        """添加行动"""
        self.pending_actions.append(action)
    
    def process_actions(self, holdings: Dict[str, float]) -> Dict[str, float]:
        """处理公司行动,返回调整后的持仓"""
        adjusted_holdings = dict(holdings)
        
        for action in self.pending_actions:
            if action.action_type == 'DIVIDEND':
                adjusted_holdings = self._process_dividend(action, adjusted_holdings)
            elif action.action_type == 'SPLIT':
                adjusted_holdings = self._process_split(action, adjusted_holdings)
            elif action.action_type == 'MERGER':
                adjusted_holdings = self._process_merger(action, adjusted_holdings)
            
            self.processed_actions.append(action)
        
        self.pending_actions.clear()
        return adjusted_holdings
    
    def _process_dividend(self, action: CorporateAction, holdings: Dict) -> Dict:
        """处理分红"""
        symbol = action.symbol
        if symbol in holdings:
            # 分红通常是代币空投
            amount = action.details.get('amount', 0)
            holdings[symbol] = holdings.get(symbol, 0) + amount
        return holdings
    
    def _process_split(self, action: CorporateAction, holdings: Dict) -> Dict:
        """处理拆股"""
        symbol = action.symbol
        ratio = action.details.get('ratio', 1)
        if symbol in holdings:
            holdings[symbol] = holdings.get(symbol, 0) * ratio
        return holdings
    
    def _process_merger(self, action: CorporateAction, holdings: Dict) -> Dict:
        """处理并购"""
        from_symbol = action.symbol
        to_symbol = action.details.get('to_symbol', from_symbol)
        ratio = action.details.get('ratio', 1)
        
        if from_symbol in holdings:
            holdings[to_symbol] = holdings.get(to_symbol, 0) + holdings[from_symbol] * ratio
            del holdings[from_symbol]
        
        return holdings
    
    def get_upcoming_actions(self, days: int = 30) -> List[CorporateAction]:
        """获取即将到来的行动"""
        cutoff = datetime.now().timestamp() + days * 86400
        return [a for a in self.pending_actions if a.effective_date <= cutoff]
