"""在线策略编辑器"""
import json, os

class StrategyIDE:
    def __init__(self, strategies_dir):
        self.strategies_dir = strategies_dir
        os.makedirs(strategies_dir, exist_ok=True)
        self.current_code = ""
    
    def save_strategy(self, name, code):
        """保存策略"""
        path = f"{self.strategies_dir}/{name}.py"
        with open(path, 'w') as f:
            f.write(code)
        return True
    
    def load_strategy(self, name):
        """加载策略"""
        path = f"{self.strategies_dir}/{name}.py"
        if os.path.exists(path):
            with open(path, 'r') as f:
                return f.read()
        return None
    
    def list_strategies(self):
        """列出策略"""
        return [f.replace('.py', '') for f in os.listdir(self.strategies_dir) if f.endswith('.py')]
    
    def delete_strategy(self, name):
        """删除策略"""
        path = f"{self.strategies_dir}/{name}.py"
        if os.path.exists(path):
            os.remove(path)
            return True
        return False
    
    def run_backtest(self, name, data):
        """回测策略"""
        code = self.load_strategy(name)
        if not code:
            return {'error': 'Strategy not found'}
        # 简化回测执行
        return {'result': 'Backtest would run here'}
