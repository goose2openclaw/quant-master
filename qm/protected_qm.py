"""
Protected QM - 带权限控制的QuantMaster
Strategy/Factor矩阵受保护,防止随意修改
"""
import sys
import time
from typing import Dict, List, Optional

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

try:
    from qm.permissions.permission_manager import (
        QMPermissionManager, 
        create_protected_matrices,
        ProtectedMatrix,
        PermissionLevel,
        MatrixType
    )
    HAS_PERMISSIONS = True
except:
    HAS_PERMISSIONS = False

class ProtectedStrategyMatrix:
    """
    受保护的策略矩阵
    8种策略权重需要权限才能修改
    """
    
    def __init__(self, pm: QMPermissionManager):
        self.pm = pm
        self._matrix = pm.default_users['eric'] if pm else None
        
        # 默认策略权重
        self.default_weights = {
            'RSI': 0.20,
            'MACD': 0.20,
            'Bollinger': 0.15,
            'Momentum': 0.15,
            'Breakout': 0.10,
            'Scalping': 0.10,
            'Swing': 0.05,
            'Grid': 0.05
        }
        
        # 当前权重(受保护)
        self._weights = self.default_weights.copy()
        
    def get_weights(self) -> Dict[str, float]:
        """获取权重 (只读)"""
        if HAS_PERMISSIONS:
            self.pm.check_permission(MatrixType.STRATEGY, 'view')
        return self._weights.copy()
    
    def set_weights(self, weights: Dict[str, float]) -> bool:
        """设置权重 (需要WRITE权限)"""
        if HAS_PERMISSIONS:
            if not self.pm.check_permission(MatrixType.STRATEGY, 'modify_weights'):
                raise PermissionError(
                    "Permission denied: modify_weights on strategy_matrix\n"
                    f"Required: WRITE level\n"
                    f"Current: {self.pm.current_user.level.name}"
                )
        
        # 验证权重总和
        total = sum(weights.values())
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Weights must sum to 1.0, got {total}")
        
        self._weights = weights
        return True
    
    def reset_weights(self) -> bool:
        """重置为默认权重 (需要ADMIN权限)"""
        if HAS_PERMISSIONS:
            if not self.pm.check_permission(MatrixType.STRATEGY, 'delete'):
                raise PermissionError("Admin permission required to reset strategy matrix")
        
        self._weights = self.default_weights.copy()
        return True
    
    def get_strategies(self) -> List[str]:
        """获取策略列表"""
        return list(self._weights.keys())


class ProtectedFactorMatrix:
    """
    受保护的因子矩阵
    20个因子权重需要权限才能修改
    """
    
    def __init__(self, pm: QMPermissionManager):
        self.pm = pm
        
        # 默认因子权重
        self.default_factors = {
            # Technical (40%)
            'RSI': 0.08,
            'MACD': 0.08,
            'Bollinger': 0.06,
            'Volume': 0.06,
            'Price': 0.06,
            'KDJ': 0.04,
            
            # On-chain (25%)
            'DEX_flows': 0.06,
            'TVL': 0.05,
            'Gas_fees': 0.05,
            'Whale_moves': 0.05,
            'Active_addresses': 0.04,
            
            # Sentiment (20%)
            'Social_volume': 0.06,
            'KOL_signals': 0.06,
            'News': 0.04,
            'Fear_Greed': 0.04,
            
            # Macro (15%)
            'Funding_rates': 0.05,
            'Open_interest': 0.04,
            'ETF_flows': 0.03,
            'CPI': 0.03
        }
        
        self._factors = self.default_factors.copy()
    
    def get_factors(self) -> Dict[str, float]:
        """获取因子 (只读)"""
        if HAS_PERMISSIONS:
            self.pm.check_permission(MatrixType.FACTOR, 'view')
        return self._factors.copy()
    
    def set_factors(self, factors: Dict[str, float]) -> bool:
        """设置因子 (需要WRITE权限)"""
        if HAS_PERMISSIONS:
            if not self.pm.check_permission(MatrixType.FACTOR, 'modify_weights'):
                raise PermissionError(
                    "Permission denied: modify_weights on factor_matrix\n"
                    f"Required: WRITE level\n"
                    f"Current: {self.pm.current_user.level.name}"
                )
        
        # 验证权重总和
        total = sum(factors.values())
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Factor weights must sum to 1.0, got {total}")
        
        self._factors = factors
        return True
    
    def reset_factors(self) -> bool:
        """重置为默认因子 (需要ADMIN权限)"""
        if HAS_PERMISSIONS:
            if not self.pm.check_permission(MatrixType.FACTOR, 'delete'):
                raise PermissionError("Admin permission required to reset factor matrix")
        
        self._factors = self.default_factors.copy()
        return True


class ProtectedQM:
    """
    受保护的QM系统
    
    功能:
    - 策略矩阵受保护
    - 因子矩阵受保护
    - 权限分级控制
    - 审计日志
    """
    
    def __init__(self, capital: float = 10000):
        self.capital = capital
        
        # 初始化权限管理器
        if HAS_PERMISSIONS:
            self.pm = QMPermissionManager()
            self.strategy_matrix = ProtectedStrategyMatrix(self.pm)
            self.factor_matrix = ProtectedFactorMatrix(self.pm)
        else:
            self.pm = None
            self.strategy_matrix = None
            self.factor_matrix = None
        
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            'user': self.pm.current_user.name if self.pm else 'N/A',
            'user_level': self.pm.current_user.level.name if self.pm else 'N/A',
            'has_permissions': HAS_PERMISSIONS,
        }
    
    def switch_user(self, user_id: str) -> bool:
        """切换用户"""
        if self.pm:
            return self.pm.set_user(user_id)
        return False
    
    def get_permissions(self) -> Dict:
        """获取当前用户权限"""
        if self.pm:
            return self.pm.get_user_permissions()
        return {}
    
    def get_strategy_weights(self) -> Dict[str, float]:
        """获取策略权重 (只读)"""
        if self.strategy_matrix:
            return self.strategy_matrix.get_weights()
        return {}
    
    def set_strategy_weights(self, weights: Dict[str, float]) -> bool:
        """设置策略权重 (需要权限)"""
        if self.strategy_matrix:
            return self.strategy_matrix.set_weights(weights)
        return False
    
    def get_factor_weights(self) -> Dict[str, float]:
        """获取因子权重 (只读)"""
        if self.factor_matrix:
            return self.factor_matrix.get_factors()
        return {}
    
    def set_factor_weights(self, factors: Dict[str, float]) -> bool:
        """设置因子权重 (需要权限)"""
        if self.factor_matrix:
            return self.factor_matrix.set_factors(factors)
        return False


if __name__ == '__main__':
    print("=" * 70)
    print("🔐 Protected QM - 权限控制版")
    print("=" * 70)
    
    # 创建受保护的QM
    qm = ProtectedQM(10000)
    
    print(f"\n📊 当前状态:")
    status = qm.get_status()
    for k, v in status.items():
        print(f"   {k}: {v}")
    
    # 权限信息
    print(f"\n🔐 当前用户权限:")
    perms = qm.get_permissions()
    for matrix, info in perms.items():
        print(f"   {matrix}: {info.get('level', 'N/A')}")
    
    # 测试Admin操作
    print(f"\n[Admin Mode]")
    qm.switch_user('eric')
    
    # 获取策略权重
    weights = qm.get_strategy_weights()
    print(f"   策略权重: {len(weights)} strategies")
    
    # 修改策略权重
    new_weights = weights.copy()
    new_weights['RSI'] = 0.30
    new_weights['MACD'] = 0.25
    try:
        qm.set_strategy_weights(new_weights)
        print(f"   ✅ 策略权重修改成功")
    except PermissionError as e:
        print(f"   ❌ 修改被拒绝: {e}")
    
    # 测试Guest操作
    print(f"\n[Guest Mode]")
    qm.switch_user('guest')
    
    # 尝试修改(应该失败)
    try:
        qm.set_strategy_weights(new_weights)
        print(f"   ❌ 意外成功 (不应该!)")
    except PermissionError:
        print(f"   ✅ 修改被正确拒绝: Permission Denied")
    
    # Guest可以读取
    weights = qm.get_strategy_weights()
    print(f"   读取成功: {len(weights)} strategies")
    
    # 尝试重置(应该失败)
    try:
        qm.strategy_matrix.reset_weights()
        print(f"   ❌ 重置成功 (不应该!)")
    except PermissionError:
        print(f"   ✅ 重置被正确拒绝: Admin Required")
    
    print("\n" + "=" * 70)
