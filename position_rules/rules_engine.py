"""
Position Sizing Rules Engine
ROO1-4: 仓位限制/日内止损/ESN/其他
"""
import sys
from typing import Dict, List, Optional
from dataclasses import dataclass

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

@dataclass
class PositionLimit:
    rule_id: str
    name: str
    description: str
    max_position_pct: float
    current_position_pct: float
    status: str  # OK/WARNING/VIOLATED
    action_required: Optional[str] = None

class PositionRulesEngine:
    """
    仓位规则引擎
    ROO1-4 规则执行
    """
    
    def __init__(self):
        self.name = "Position Rules Engine"
        self.rules = self._init_rules()
    
    def _init_rules(self) -> Dict[str, PositionLimit]:
        """初始化规则"""
        return {
            'ROO1': PositionLimit(
                rule_id='ROO1',
                name='仓位限制',
                description='单币种仓位不超过总资产X%',
                max_position_pct=25.0,
                current_position_pct=0,
                status='OK'
            ),
            'ROO2': PositionLimit(
                rule_id='ROO2',
                name='日内止损',
                description='日内亏损不超过总资产Y%',
                max_position_pct=5.0,
                current_position_pct=0,
                status='OK'
            ),
            'ROO3': PositionLimit(
                rule_id='ROO3',
                name='ESN',
                description='紧急止损线',
                max_position_pct=10.0,
                current_position_pct=0,
                status='OK'
            ),
            'ROO4': PositionLimit(
                rule_id='ROO4',
                name=' Hut限制',
                description='每小时最大交易次数',
                max_position_pct=10.0,
                current_position_pct=0,
                status='OK'
            ),
        }
    
    def check_position(self, symbol: str, position_value: float,
                      total_assets: float, daily_pnl: float) -> Dict:
        """检查仓位是否符合规则"""
        position_pct = position_value / total_assets * 100
        daily_loss_pct = abs(daily_pnl) / total_assets * 100 if daily_pnl < 0 else 0
        
        results = {}
        
        # ROO1: 仓位限制
        results['ROO1'] = {
            'rule': self.rules['ROO1'],
            'violated': position_pct > self.rules['ROO1'].max_position_pct,
            'action': f"Reduce {symbol} by {position_pct - self.rules['ROO1'].max_position_pct:.1f}%"
                     if position_pct > self.rules['ROO1'].max_position_pct else None
        }
        
        # ROO2: 日内止损
        results['ROO2'] = {
            'rule': self.rules['ROO2'],
            'violated': daily_loss_pct > self.rules['ROO2'].max_position_pct,
            'action': f"Stop trading - daily loss {daily_loss_pct:.1f}% exceeds limit"
                     if daily_loss_pct > self.rules['ROO2'].max_position_pct else None
        }
        
        # ROO3: ESN
        results['ROO3'] = {
            'rule': self.rules['ROO3'],
            'violated': position_pct > self.rules['ROO3'].max_position_pct,
            'action': f"Emergency stop - position {position_pct:.1f}% at ESN"
                     if position_pct > self.rules['ROO3'].max_position_pct else None
        }
        
        return results
    
    def get_max_position(self, total_assets: float, rule: str = 'ROO1') -> float:
        """获取最大仓位"""
        if rule not in self.rules:
            return 0
        return total_assets * self.rules[rule].max_position_pct / 100
    
    def validate_trade(self, symbol: str, trade_value: float,
                      total_assets: float, positions: Dict[str, float],
                      daily_trades: int) -> Dict:
        """验证交易"""
        # 当前总持仓
        current_total_position = sum(positions.values())
        new_total_position = current_total_position + trade_value
        
        position_after_trade_pct = new_total_position / total_assets * 100
        
        validations = {
            'approved': True,
            'warnings': [],
            'blocks': [],
            'max_position_value': self.get_max_position(total_assets, 'ROO1'),
            'position_after_trade_pct': position_after_trade_pct
        }
        
        # 检查ROO1
        if position_after_trade_pct > self.rules['ROO1'].max_position_pct:
            validations['approved'] = False
            validations['blocks'].append(
                f"ROO1 Violated: Position would be {position_after_trade_pct:.1f}% (max {self.rules['ROO1'].max_position_pct}%)"
            )
        
        # 检查ROO4 (每小时交易次数)
        if daily_trades >= self.rules['ROO4'].max_position_pct:
            validations['approved'] = False
            validations['blocks'].append(
                f"ROO4 Violated: {daily_trades} trades this hour (max {self.rules['ROO4'].max_position_pct})"
            )
        
        # 警告
        if position_after_trade_pct > self.rules['ROO1'].max_position_pct * 0.8:
            validations['warnings'].append(
                f"Position at {position_after_trade_pct:.1f}% - approaching limit"
            )
        
        return validations
    
    def get_all_rules_status(self) -> List[PositionLimit]:
        """获取所有规则状态"""
        return list(self.rules.values())
    
    def update_rule_limit(self, rule_id: str, new_max: float) -> bool:
        """更新规则限制"""
        if rule_id in self.rules:
            self.rules[rule_id].max_position_pct = new_max
            return True
        return False

if __name__ == '__main__':
    pre = PositionRulesEngine()
    
    print("=== Position Rules Engine ===\n")
    
    # 规则状态
    rules = pre.get_all_rules_status()
    print("Rules:")
    for rule in rules:
        print(f"  {rule.rule_id}: {rule.name}")
        print(f"    Max: {rule.max_position_pct}%")
        print(f"    Status: {rule.status}")
    
    # 验证交易
    total_assets = 10000
    positions = {'BTC': 2000, 'ETH': 1500}
    daily_trades = 3
    
    validation = pre.validate_trade('SOL', 1000, total_assets, positions, daily_trades)
    print(f"\nTrade Validation (Buy SOL $1000):")
    print(f"  Approved: {validation['approved']}")
    print(f"  Warnings: {validation['warnings']}")
    print(f"  Blocks: {validation['blocks']}")
    print(f"  Position after: {validation['position_after_trade_pct']:.1f}%")
