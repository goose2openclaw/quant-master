"""权限管理"""
import hashlib, time
from enum import Enum

class Role(Enum):
    ADMIN = "admin"
    TRADER = "trader"
    VIEWER = "viewer"

class User:
    def __init__(self, username, password, role=Role.VIEWER):
        self.username = username
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()
        self.role = role
        self.last_login = 0
        self.enabled = True

class PermissionManager:
    def __init__(self):
        self.users = {}
        self.current_user = None
    
    def add_user(self, username, password, role=Role.VIEWER):
        self.users[username] = User(username, password, role)
    
    def login(self, username, password):
        user = self.users.get(username)
        if user and user.enabled:
            pwd_hash = hashlib.sha256(password.encode()).hexdigest()
            if pwd_hash == user.password_hash:
                user.last_login = time.time()
                self.current_user = user
                return True
        return False
    
    def logout(self):
        self.current_user = None
    
    def has_permission(self, action):
        if not self.current_user:
            return False
        role = self.current_user.role
        if role == Role.ADMIN:
            return True
        if role == Role.TRADER:
            return action in ['trade', 'view']
        return action == 'view'
