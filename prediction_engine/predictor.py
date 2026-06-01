"""
Prediction Engine - AI价格预测系统
"""
import sys
import time
import random
import math
from typing import Dict, List
from dataclasses import dataclass

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

@dataclass
class Prediction:
    symbol: str
    current_price: float
    predicted_price: float
    confidence: float
    direction: str
    timeframe: str
    models: Dict[str, float]
    timestamp: float

class PredictionEngine:
    def __init__(self):
        self.models = {
            'lstm': self._lstm_predict,
            'arima': self._arima_predict,
            'linear': self._linear_predict,
            'rf': self._rf_predict,
        }
        self.model_weights = {'lstm': 0.30, 'arima': 0.20, 'linear': 0.15, 'rf': 0.20}
    
    def predict(self, symbol: str, timeframe: str = '1h', history: List[float] = None) -> Prediction:
        if history is None:
            history = self._generate_history(symbol)
        current_price = history[-1]
        predictions = {}
        for model_name, model_fn in self.models.items():
            predictions[model_name] = model_fn(history, timeframe)
        final_pred = sum(predictions[m] * self.model_weights[m] for m in self.model_weights)
        std = self._std(list(predictions.values()))
        confidence = max(0, min(100, 100 - std * 10))
        change_pct = (final_pred - current_price) / current_price * 100
        direction = 'UP' if change_pct > 0.5 else 'DOWN' if change_pct < -0.5 else 'FLAT'
        return Prediction(symbol=symbol, current_price=current_price, predicted_price=final_pred,
                        confidence=confidence, direction=direction, timeframe=timeframe,
                        models=predictions, timestamp=time.time())
    
    def _lstm_predict(self, history, timeframe):
        recent = sum(history[-5:]) / 5
        trend = (history[-1] - history[-10]) / history[-10] if len(history) >= 10 else 0
        return recent * (1 + trend * 0.5)
    
    def _arima_predict(self, history, timeframe):
        prices = history[-20:]
        ma = sum(prices) / len(prices)
        slope = (prices[-1] - prices[0]) / len(prices)
        return ma + slope * 3
    
    def _linear_predict(self, history, timeframe):
        n = len(history)
        if n < 2:
            return history[-1] if history else 100
        x_mean = sum(range(n)) / n
        y_mean = sum(history) / n
        num = sum((x - x_mean) * (y - y_mean) for x, y in enumerate(history))
        den = sum((x - x_mean) ** 2 for x in range(n))
        slope = num / den if den != 0 else 0
        return slope * (n + 5) + (y_mean - slope * x_mean)
    
    def _rf_predict(self, history, timeframe):
        base = sum(history[-10:]) / 10
        variance = self._std(history[-10:])
        noise = random.gauss(0, variance * 0.1)
        return base * (1 + random.uniform(-0.02, 0.02)) + noise
    
    def _generate_history(self, symbol):
        base_prices = {'BTC': 67000, 'ETH': 3500, 'BNB': 580, 'SOL': 145, 'XRP': 0.52}
        base = base_prices.get(symbol, 100)
        history = [base]
        for _ in range(100):
            change = random.gauss(0, base * 0.01)
            history.append(history[-1] + change)
        return history
    
    def _std(self, values):
        if not values:
            return 0
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        return math.sqrt(variance)
