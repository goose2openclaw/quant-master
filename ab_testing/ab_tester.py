"""
A/B Testing Framework - 策略A/B测试
"""
import random, json
from datetime import datetime
from typing import Dict, List
from scipy import stats

class ABTest:
    """A/B测试"""
    def __init__(self, test_id, name, variant_a_config, variant_b_config):
        self.test_id = test_id
        self.name = name
        self.variant_a = variant_a_config  # 对照组
        self.variant_b = variant_b_config  # 实验组
        self.status = 'running'  # running, completed, stopped
        self.start_time = datetime.now()
        self.traffic_split = 0.5  # 50/50分配
        
        # 结果
        self.group_a_results = []
        self.group_b_results = []
    
    def assign_variant(self, user_id):
        """分配变体"""
        # 确定性分配
        if hash(user_id) % 100 < self.traffic_split * 100:
            return 'A'
        return 'B'
    
    def record_result(self, user_id, metric_name, value):
        """记录结果"""
        variant = self.assign_variant(user_id)
        
        if variant == 'A':
            self.group_a_results.append({'metric': metric_name, 'value': value, 'time': datetime.now().isoformat()})
        else:
            self.group_b_results.append({'metric': metric_name, 'value': value, 'time': datetime.now().isoformat()})
    
    def analyze(self, metric_name='default'):
        """分析结果"""
        a_values = [r['value'] for r in self.group_a_results if r['metric'] == metric_name]
        b_values = [r['value'] for r in self.group_b_results if r['metric'] == metric_name]
        
        if len(a_values) < 10 or len(b_values) < 10:
            return {'status': 'insufficient_data'}
        
        # t检验
        t_stat, p_value = stats.ttest_ind(a_values, b_values)
        
        # 计算效应量
        pooled_std = ((sum(a_values)**2/len(a_values) + sum(b_values)**2/len(b_values))**0.5)
        effect_size = (sum(a_values)/len(a_values) - sum(b_values)/len(b_values)) / pooled_std if pooled_std > 0 else 0
        
        # 置信区间
        mean_a = sum(a_values) / len(a_values)
        mean_b = sum(b_values) / len(b_values)
        
        return {
            'status': 'completed',
            'metric': metric_name,
            'variant_a': {
                'count': len(a_values),
                'mean': mean_a,
                'std': (sum((x - mean_a)**2 for x in a_values) / len(a_values))**0.5 if len(a_values) > 1 else 0
            },
            'variant_b': {
                'count': len(b_values),
                'mean': mean_b,
                'std': (sum((x - mean_b)**2 for x in b_values) / len(b_values))**0.5 if len(b_values) > 1 else 0
            },
            'lift': ((mean_b - mean_a) / mean_a * 100) if mean_a != 0 else 0,
            'p_value': p_value,
            'effect_size': effect_size,
            'significant': p_value < 0.05,
            'winner': 'B' if p_value < 0.05 and mean_b > mean_a else ('A' if p_value < 0.05 else 'None')
        }

class ABTestingFramework:
    """
    A/B测试框架
    """
    def __init__(self):
        self.tests = {}  # {test_id: ABTest}
    
    def create_test(self, name, variant_a_config, variant_b_config, traffic_split=0.5):
        """创建测试"""
        test_id = f"AB_{len(self.tests) + 1:04d}"
        test = ABTest(test_id, name, variant_a_config, variant_b_config)
        test.traffic_split = traffic_split
        self.tests[test_id] = test
        print(f"[A/B] Created test {test_id}: {name}")
        return test_id
    
    def record(self, test_id, user_id, metric_name, value):
        """记录指标"""
        test = self.tests.get(test_id)
        if test:
            test.record_result(user_id, metric_name, value)
    
    def analyze(self, test_id, metric_name='default'):
        """分析测试"""
        test = self.tests.get(test_id)
        if test:
            return test.analyze(metric_name)
        return None
    
    def stop_test(self, test_id):
        """停止测试"""
        test = self.tests.get(test_id)
        if test:
            test.status = 'stopped'
    
    def get_test_status(self, test_id):
        """获取测试状态"""
        test = self.tests.get(test_id)
        if not test:
            return None
        
        return {
            'test_id': test_id,
            'name': test.name,
            'status': test.status,
            'a_count': len(test.group_a_results),
            'b_count': len(test.group_b_results),
            'start_time': test.start_time.isoformat()
        }
