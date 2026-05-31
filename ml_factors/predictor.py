"""
机器学习预测模型
"""
import numpy as np
from collections import deque

class PricePredictor:
    """
    价格预测模型 - 简化版
    使用线性回归 + 特征工程
    """
    def __init__(self, lookback=20):
        self.lookback = lookback
        self.price_history = deque(maxlen=lookback+1)
        self.volume_history = deque(maxlen=lookback+1)
        self.features = []
        self.labels = []
        self.model = None
        self._trained = False
    
    def update(self, price, volume=0):
        self.price_history.append(price)
        self.volume_history.append(volume)
    
    def _extract_features(self):
        """提取特征"""
        if len(self.price_history) < self.lookback + 1:
            return None
        
        prices = np.array(self.price_history)
        volumes = np.array(self.volume_history) if self.volume_history else np.ones_like(prices)
        
        # 特征: [returns, volatility, momentum, volume_ratio, trend]
        returns = (prices[-1] - prices[-self.lookback]) / prices[-self.lookback]
        volatility = np.std(np.diff(prices)) / np.mean(prices)
        momentum = (prices[-1] - prices[-5]) / prices[-5] if len(prices) >= 5 else 0
        volume_ratio = volumes[-1] / np.mean(volumes) if np.mean(volumes) > 0 else 1
        
        # 趋势: 最近5点线性回归斜率
        x = np.arange(min(5, len(prices)))
        y = prices[-min(5, len(prices)):]
        trend = np.polyfit(x, y, 1)[0] if len(x) > 1 else 0
        
        return [returns, volatility, momentum, volume_ratio, trend]
    
    def train(self):
        """训练模型 (简化版 - 使用线性回归)"""
        if len(self.price_history) < self.lookback + 10:
            print("[Predictor] 数据不足")
            return False
        
        # 构建训练数据
        self.features = []
        self.labels = []
        
        prices = list(self.price_history)
        for i in range(self.lookback+1, len(prices)):
            feat = self._compute_features_at(prices[:i])
            if feat:
                self.features.append(feat)
                # 标签: 下一天收益
                self.labels.append((prices[i] - prices[i-1]) / prices[i-1])
        
        if len(self.features) < 10:
            print("[Predictor] 训练数据不足")
            return False
        
        # 简单线性回归 (无外部依赖)
        self.model = self._linear_regression(np.array(self.features), np.array(self.labels))
        self._trained = True
        print(f"[Predictor] 训练完成, {len(self.features)} 样本")
        return True
    
    def _compute_features_at(self, prices):
        """计算指定位置的特征"""
        if len(prices) < self.lookback + 1:
            return None
        lookback = self.lookback
        p = prices[-lookback-1:-1]  # lookback个价格
        last = prices[-1]
        
        returns = (last - p[0]) / p[0] if p[0] != 0 else 0
        volatility = np.std(np.diff(p)) / np.mean(p) if np.mean(p) != 0 else 0
        momentum = (last - p[-5]) / p[-5] if len(p) >= 5 and p[-5] != 0 else 0
        
        return [returns, volatility, momentum, 1.0, 0.0]
    
    def _linear_regression(self, X, y):
        """简单线性回归: y = Xw + b"""
        # 添加偏置
        X_b = np.c_[np.ones(X.shape[0]), X]
        # 最小二乘法: w = (X'X)^(-1) X'y
        try:
            XX_inv = np.linalg.inv(X_b.T @ X_b)
            self.weights = XX_inv @ X_b.T @ y
            return True
        except np.linalg.LinAlgError:
            return False
    
    def predict(self):
        """预测"""
        if not self._trained or self.model is None:
            return {'direction': 0, 'confidence': 0, 'error': 'Not trained'}
        
        feat = self._extract_features()
        if feat is None:
            return {'direction': 0, 'confidence': 0}
        
        # 添加偏置
        feat_b = np.array([1] + feat)
        
        # 预测
        pred = np.dot(self.weights, feat_b)
        
        # 方向
        direction = 1 if pred > 0 else -1 if pred < 0 else 0
        
        # 置信度 (基于特征归一化)
        confidence = min(abs(pred) * 10, 1.0)  # 简化版
        
        return {'direction': direction, 'confidence': confidence, 'predicted_return': pred}
    
    def predict_direction(self):
        """预测方向"""
        result = self.predict()
        if result.get('direction') == 1 and result.get('confidence', 0) > 0.6:
            return 'BUY'
        elif result.get('direction') == -1 and result.get('confidence', 0) > 0.6:
            return 'SELL'
        return 'HOLD'


class EnsemblePredictor:
    """
    集成预测器 - 多模型融合
    """
    def __init__(self):
        self.predictors = []
        self.weights = []
    
    def add_predictor(self, predictor, weight=1.0):
        self.predictors.append(predictor)
        self.weights.append(weight)
    
    def predict(self):
        """加权平均预测"""
        votes = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
        total_weight = sum(self.weights)
        
        for pred, weight in zip(self.predictors, self.weights):
            direction = pred.predict_direction()
            votes[direction] += weight / total_weight
        
        # 返回最高置信度方向
        return max(votes, key=votes.get)
    
    def train_all(self):
        """训练所有预测器"""
        for p in self.predictors:
            p.train()
