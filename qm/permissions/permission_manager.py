"""
QM Permission Manager - 权限管理系统
Matrix权限控制 - 防止核心策略/因子矩阵被随意修改
"""
import sys
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

class PermissionLevel(Enum):
    """权限级别"""
    NONE = 0      # 无权限
    READ = 1      # 只读
    EXECUTE = 2   # 执行
    WRITE = 3     # 写入
    ADMIN = 4     # 管理员

class MatrixType(Enum):
    """矩阵类型"""
    STRATEGY = "strategy_matrix"
    FACTOR = "factor_matrix"
    ALLOCATION = "allocation"
    RISK = "risk_settings"

@dataclass
class Permission:
    """权限项"""
    matrix_type: MatrixType
    level: PermissionLevel
    reason: str
    granted_by: str
    granted_at: float
    expires_at: Optional[float] = None

@dataclass
class UserProfile:
    """用户配置"""
    user_id: str
    name: str
    level: PermissionLevel
    permissions: Dict[MatrixType, Permission] = field(default_factory=dict)
    audit_log: List[Dict] = field(default_factory=list)

class QMPermissionManager:
    """
    QM权限管理器
    
    功能:
    1. 矩阵权限控制 (Strategy/Factor)
    2. 用户权限分级
    3. 操作审计日志
    4. 权限申请/审批流程
    """
    
    def __init__(self):
        self.name = "QM Permission Manager"
        
        # 默认用户
        self.default_users = {
            'system': UserProfile(
                user_id='system',
                name='System',
                level=PermissionLevel.ADMIN
            ),
            'eric': UserProfile(
                user_id='eric',
                name='Eric',
                level=PermissionLevel.ADMIN
            ),
            'trader': UserProfile(
                user_id='trader',
                name='Trader',
                level=PermissionLevel.EXECUTE
            ),
            'guest': UserProfile(
                user_id='guest',
                name='Guest',
                level=PermissionLevel.READ
            )
        }
        
        # 默认矩阵权限
        self.matrix_permissions = {
            MatrixType.STRATEGY: {
                PermissionLevel.NONE: ["view"],
                PermissionLevel.READ: ["view", "export"],
                PermissionLevel.EXECUTE: ["view", "export", "use"],
                PermissionLevel.WRITE: ["view", "export", "use", "modify_weights"],
                PermissionLevel.ADMIN: ["view", "export", "use", "modify_weights", "modify_strategies", "delete"]
            },
            MatrixType.FACTOR: {
                PermissionLevel.NONE: ["view"],
                PermissionLevel.READ: ["view", "export"],
                PermissionLevel.EXECUTE: ["view", "export", "use"],
                PermissionLevel.WRITE: ["view", "export", "use", "modify_weights"],
                PermissionLevel.ADMIN: ["view", "export", "use", "modify_weights", "modify_factors", "delete"]
            },
            MatrixType.ALLOCATION: {
                PermissionLevel.NONE: ["view"],
                PermissionLevel.READ: ["view"],
                PermissionLevel.EXECUTE: ["view", "execute"],
                PermissionLevel.WRITE: ["view", "execute", "modify"],
                PermissionLevel.ADMIN: ["view", "execute", "modify", "reset"]
            },
            MatrixType.RISK: {
                PermissionLevel.NONE: ["view"],
                PermissionLevel.READ: ["view"],
                PermissionLevel.EXECUTE: ["view", "execute"],
                PermissionLevel.WRITE: ["view", "execute", "modify_limits"],
                PermissionLevel.ADMIN: ["view", "execute", "modify_limits", "disable_protections"]
            }
        }
        
        self.current_user = self.default_users['eric']
        
    def check_permission(self, matrix_type: MatrixType, action: str) -> bool:
        """检查权限"""
        user_level = self.current_user.level
        
        # 管理员拥有所有权限
        if user_level == PermissionLevel.ADMIN:
            return True
        
        # 获取该级别允许的操作
        allowed_actions = self.matrix_permissions.get(matrix_type, {}).get(user_level, [])
        
        return action in allowed_actions
    
    def require_permission(self, matrix_type: MatrixType, action: str):
        """要求权限装饰器"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                if not self.check_permission(matrix_type, action):
                    raise PermissionError(
                        f"Permission denied: {action} on {matrix_type.value}\n"
                        f"User: {self.current_user.name} ({self.current_user.level.name})\n"
                        f"Required level: {action} not in allowed actions"
                    )
                # 记录操作
                self._log_action(matrix_type.value, action, 'GRANTED')
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def grant_permission(self, user_id: str, matrix_type: MatrixType, 
                        level: PermissionLevel, reason: str) -> bool:
        """授予权限"""
        if self.current_user.level != PermissionLevel.ADMIN:
            self._log_action('grant', level.name, 'DENIED - Not Admin')
            return False
        
        if user_id not in self.default_users:
            self.default_users[user_id] = UserProfile(
                user_id=user_id,
                name=user_id,
                level=PermissionLevel.READ
            )
        
        user = self.default_users[user_id]
        user.permissions[matrix_type] = Permission(
            matrix_type=matrix_type,
            level=level,
            reason=reason,
            granted_by=self.current_user.name,
            granted_at=datetime.now().timestamp()
        )
        
        self._log_action(f'grant:{user_id}', matrix_type.value, f'GRANTED - {reason}')
        return True
    
    def revoke_permission(self, user_id: str, matrix_type: MatrixType) -> bool:
        """撤销权限"""
        if self.current_user.level != PermissionLevel.ADMIN:
            return False
        
        if user_id in self.default_users:
            user = self.default_users[user_id]
            if matrix_type in user.permissions:
                del user.permissions[matrix_type]
                self._log_action(f'revoke:{user_id}', matrix_type.value, 'REVOKED')
                return True
        return False
    
    def _log_action(self, subject: str, action: str, result: str):
        """记录操作"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'user': self.current_user.name,
            'subject': subject,
            'action': action,
            'result': result
        }
        self.current_user.audit_log.append(log_entry)
    
    def get_user_permissions(self, user_id: str = None) -> Dict:
        """获取用户权限"""
        user = self.default_users.get(user_id or self.current_user.user_id)
        if not user:
            return {}
        
        perms = {}
        for matrix_type in MatrixType:
            if matrix_type in user.permissions:
                p = user.permissions[matrix_type]
                perms[matrix_type.value] = {
                    'level': p.level.name,
                    'reason': p.reason,
                    'granted_by': p.granted_by,
                    'granted_at': datetime.fromtimestamp(p.granted_at).isoformat()
                }
            else:
                perms[matrix_type.value] = {'level': user.level.name}
        
        return perms
    
    def get_audit_log(self, limit: int = 50) -> List[Dict]:
        """获取审计日志"""
        return self.current_user.audit_log[-limit:]
    
    def set_user(self, user_id: str) -> bool:
        """切换用户"""
        if user_id in self.default_users:
            self.current_user = self.default_users[user_id]
            return True
        return False
    
    def switch_to_admin(self):
        """切换到管理员"""
        self.current_user = self.default_users['eric']
    
    def switch_to_guest(self):
        """切换到访客(只读)"""
        self.current_user = self.default_users['guest']

class ProtectedMatrix:
    """
    受保护的矩阵
    策略/因子矩阵需要通过权限管理器才能修改
    """
    
    def __init__(self, matrix_type: MatrixType, name: str, pm: QMPermissionManager):
        self.matrix_type = matrix_type
        self.name = name
        self.pm = pm
        self._data = {}
        
    def _check_write(self, action: str):
        """检查写入权限"""
        if not self.pm.check_permission(self.matrix_type, action):
            raise PermissionError(
                f"Write permission denied for {self.name}\n"
                f"Required action: {action}\n"
                f"Current user: {self.pm.current_user.name} ({self.pm.current_user.level.name})"
            )
    
    def _check_read(self):
        """检查读取权限"""
        if not self.pm.check_permission(self.matrix_type, 'view'):
            raise PermissionError(
                f"Read permission denied for {self.name}\n"
                f"Current user: {self.pm.current_user.name}"
            )
    
    def get(self, key: str, default=None):
        """读取数据"""
        self._check_read()
        return self._data.get(key, default)
    
    def set(self, key: str, value, action: str = 'use'):
        """写入数据"""
        self._check_write(action)
        self._data[key] = value
    
    def update_weights(self, weights: Dict):
        """更新权重 (需要WRITE权限)"""
        self._check_write('modify_weights')
        self._data['weights'] = weights
    
    def reset(self):
        """重置 (需要ADMIN权限)"""
        self._check_write('delete')
        self._data = {}

def create_protected_matrices(pm: QMPermissionManager) -> Dict[str, ProtectedMatrix]:
    """创建受保护的矩阵"""
    return {
        'strategy': ProtectedMatrix(MatrixType.STRATEGY, 'Strategy Matrix', pm),
        'factor': ProtectedMatrix(MatrixType.FACTOR, 'Factor Matrix', pm),
        'allocation': ProtectedMatrix(MatrixType.ALLOCATION, 'Allocation Matrix', pm),
        'risk': ProtectedMatrix(MatrixType.RISK, 'Risk Matrix', pm),
    }

if __name__ == '__main__':
    pm = QMPermissionManager()
    matrices = create_protected_matrices(pm)
    
    print("=" * 70)
    print("🔐 QM Permission Manager - 权限管理")
    print("=" * 70)
    
    # 显示当前用户权限
    print(f"\n当前用户: {pm.current_user.name} ({pm.current_user.level.name})")
    
    print("\n📊 权限矩阵:")
    for matrix_type in MatrixType:
        has_access = pm.check_permission(matrix_type, 'modify_weights')
        icon = "✅" if has_access else "❌"
        print(f"   {icon} {matrix_type.value}: modify_weights = {has_access}")
    
    # 测试受保护矩阵
    print("\n🔒 测试受保护矩阵:")
    
    # Admin可以写入
    print("\n[Admin Mode]")
    pm.switch_to_admin()
    try:
        matrices['strategy'].set('test', 'value', 'modify_weights')
        print("   ✅ Strategy Matrix: 写入成功")
    except PermissionError as e:
        print(f"   ❌ {e}")
    
    # Guest不能写入
    print("\n[Guest Mode]")
    pm.switch_to_guest()
    try:
        matrices['strategy'].set('test', 'value', 'modify_weights')
        print("   ✅ Strategy Matrix: 写入成功")
    except PermissionError as e:
        print(f"   ❌ 写入被拒绝: Permission Denied")
    
    # Guest可以读取
    print("\n[Guest Mode - Read]")
    try:
        value = matrices['strategy'].get('test')
        print(f"   ✅ 读取成功: {value}")
    except PermissionError as e:
        print(f"   ❌ 读取被拒绝")
    
    print("\n" + "=" * 70)
