"""
Compliance Monitor - 合规监控系统
MiFID/Dodd-Frank标准
"""
import time
from enum import Enum
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

class ComplianceRuleType(Enum):
    POSITION_LIMIT = "position_limit"
    CONCENTRATION = "concentration"
    LEVERAGE = "leverage"
    TRADING_LIMIT = "trading_limit"
    RESTRICTED_SECURITY = "restricted_security"
    BEST_EXECUTION = "best_execution"
    REPORTING = "reporting"
    MARGIN_REQUIREMENT = "margin_requirement"

@dataclass
class ComplianceViolation:
    rule_type: ComplianceRuleType
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    description: str
    affected_trades: List[str]
    timestamp: float

class ComplianceRule:
    """合规规则"""
    def __init__(self, rule_id, rule_type: ComplianceRuleType, params: Dict):
        self.rule_id = rule_id
        self.rule_type = rule_type
        self.params = params
        self.enabled = True
    
    def check(self, context: Dict) -> Tuple[bool, Optional[str]]:
        """检查是否违规"""
        raise NotImplementedError

class PositionLimitRule(ComplianceRule):
    """持仓限制规则"""
    def check(self, context: Dict) -> Tuple[bool, Optional[str]]:
        max_position = self.params.get('max_position', 10000)
        current_position = context.get('position_value', 0)
        
        if current_position > max_position:
            return False, f"Position {current_position} exceeds limit {max_position}"
        return True, None

class ConcentrationRule(ComplianceRule):
    """集中度限制"""
    def check(self, context: Dict) -> Tuple[bool, Optional[str]]:
        max_concentration = self.params.get('max_concentration', 0.2)  # 20%
        total_equity = context.get('total_equity', 1)
        position_value = context.get('position_value', 0)
        
        concentration = position_value / total_equity if total_equity > 0 else 0
        
        if concentration > max_concentration:
            return False, f"Concentration {concentration*100:.1f}% exceeds {max_concentration*100:.1f}%"
        return True, None

class LeverageRule(ComplianceRule):
    """杠杆限制"""
    def check(self, context: Dict) -> Tuple[bool, Optional[str]]:
        max_leverage = self.params.get('max_leverage', 3)
        current_leverage = context.get('leverage', 1)
        
        if current_leverage > max_leverage:
            return False, f"Leverage {current_leverage}x exceeds {max_leverage}x"
        return True, None

class ComplianceEngine:
    """
    合规引擎
    规则检查、违规记录、报告生成
    """
    def __init__(self):
        self.rules = {}
        self.violations = []
        self.alerts = []
        self.reports = []
        self._init_default_rules()
    
    def _init_default_rules(self):
        """初始化默认规则"""
        # 持仓限制
        self.add_rule(PositionLimitRule(
            'pos_limit_1',
            ComplianceRuleType.POSITION_LIMIT,
            {'max_position': 50000}
        ))
        
        # 集中度
        self.add_rule(ConcentrationRule(
            'conc_limit_1',
            ComplianceRuleType.CONCENTRATION,
            {'max_concentration': 0.25}
        ))
        
        # 杠杆
        self.add_rule(LeverageRule(
            'lev_limit_1',
            ComplianceRuleType.LEVERAGE,
            {'max_leverage': 5}
        ))
    
    def add_rule(self, rule: ComplianceRule):
        """添加规则"""
        self.rules[rule.rule_id] = rule
    
    def remove_rule(self, rule_id: str):
        """移除规则"""
        self.rules.pop(rule_id, None)
    
    def check_trade(self, trade: Dict) -> Tuple[bool, List[str]]:
        """检查交易"""
        violations = []
        
        context = {
            'trade': trade,
            'position_value': trade.get('position_value', 0),
            'total_equity': trade.get('total_equity', 100000),
            'leverage': trade.get('leverage', 1),
            'symbol': trade.get('symbol', ''),
            'qty': trade.get('qty', 0)
        }
        
        for rule_id, rule in self.rules.items():
            if not rule.enabled:
                continue
            
            passed, reason = rule.check(context)
            if not passed:
                violations.append(f"Rule {rule_id}: {reason}")
                
                self.violations.append(ComplianceViolation(
                    rule_type=rule.rule_type,
                    severity='HIGH',
                    description=reason,
                    affected_trades=[trade.get('trade_id', '')],
                    timestamp=time.time()
                ))
        
        return len(violations) == 0, violations
    
    def check_position(self, position: Dict) -> List[ComplianceViolation]:
        """检查持仓"""
        violations = []
        
        context = {
            'position_value': position.get('value', 0),
            'total_equity': position.get('total_equity', 100000),
            'leverage': position.get('leverage', 1),
            'symbol': position.get('symbol', '')
        }
        
        for rule_id, rule in self.rules.items():
            if not rule.enabled:
                continue
            
            passed, reason = rule.check(context)
            if not passed:
                violations.append(ComplianceViolation(
                    rule_type=rule.rule_type,
                    severity='MEDIUM',
                    description=reason,
                    affected_trades=[],
                    timestamp=time.time()
                ))
        
        return violations
    
    def get_violations(self, since=None) -> List[ComplianceViolation]:
        """获取违规记录"""
        if since:
            return [v for v in self.violations if v.timestamp >= since]
        return self.violations
    
    def generate_compliance_report(self) -> Dict:
        """生成合规报告"""
        violations_by_type = {}
        for v in self.violations:
            rtype = v.rule_type.value
            if rtype not in violations_by_type:
                violations_by_type[rtype] = 0
            violations_by_type[rtype] += 1
        
        return {
            'period': {'start': self.violations[0].timestamp if self.violations else time.time(),
                       'end': time.time()},
            'total_violations': len(self.violations),
            'violations_by_type': violations_by_type,
            'rules_active': len([r for r in self.rules.values() if r.enabled]),
            'rules_total': len(self.rules),
            'severity_summary': {
                'critical': len([v for v in self.violations if v.severity == 'CRITICAL']),
                'high': len([v for v in self.violations if v.severity == 'HIGH']),
                'medium': len([v for v in self.violations if v.severity == 'MEDIUM']),
                'low': len([v for v in self.violations if v.severity == 'LOW'])
            }
        }
    
    def send_alert(self, violation: ComplianceViolation):
        """发送警报"""
        alert = {
            'timestamp': time.time(),
            'violation': violation,
            'action_required': self._get_action(violation)
        }
        self.alerts.append(alert)
        return alert
    
    def _get_action(self, violation: ComplianceViolation) -> str:
        """获取建议操作"""
        actions = {
            ComplianceRuleType.POSITION_LIMIT: "Reduce position or split across accounts",
            ComplianceRuleType.CONCENTRATION: "Diversify portfolio",
            ComplianceRuleType.LEVERAGE: "Reduce leverage immediately",
            ComplianceRuleType.MARGIN_REQUIREMENT: "Add margin or close positions"
        }
        return actions.get(violation.rule_type, "Review and remediate")

class MiFIDReporter:
    """MiFID交易报告"""
    def __init__(self):
        self.transactions = []
    
    def record_transaction(self, trade: Dict):
        """记录交易用于报告"""
        self.transactions.append({
            'trade_id': trade.get('trade_id'),
            'client_id': trade.get('client_id'),
            'symbol': trade.get('symbol'),
            'venue': trade.get('venue'),
            'price': trade.get('price'),
            'qty': trade.get('qty'),
            'timestamp': trade.get('timestamp', time.time()),
            'direction': trade.get('side')
        })
    
    def generate_mifid_report(self) -> Dict:
        """生成MiFID报告"""
        return {
            'report_type': 'TRANSACTION_REPORT',
            'regulator': 'ESMA',
            'framework': 'MiFID II',
            'transactions': len(self.transactions),
            'data': self.transactions
        }

class DoddFrankReporter:
    """Dodd-Frank报告"""
    def __init__(self):
        self.swap_data = []
    
    def record_swap(self, swap: Dict):
        """记录互换"""
        self.swap_data.append(swap)
    
    def generate_swap_report(self) -> Dict:
        """生成互换报告"""
        return {
            'report_type': 'SWAP_DATA_REPOSITORY',
            'regulator': 'CFTC',
            'framework': 'Dodd-Frank',
            'swaps': len(self.swap_data),
            'data': self.swap_data
        }
