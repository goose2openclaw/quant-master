"""
Alert System - 从TradingView精细克隆
强大的警报系统，支持价格、条件、指标警报

来源: TradingView Alert System
"""
import time
import json
import threading
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


class AlertType(Enum):
    """警报类型"""
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    RSI_OVERBOUGHT = "rsi_overbought"
    RSI_OVERSOLD = "rsi_oversold"
    MACD_CROSS = "macd_cross"
    KDJ_CROSS = "kdj_cross"
    BOLLINGER_TOUCH = "bollinger_touch"
    VOLUME_SPIKE = "volume_spike"
    CUSTOM = "custom"


class AlertPriority(Enum):
    """警报优先级"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Alert:
    """警报数据类"""
    id: str
    name: str
    alert_type: AlertType
    symbol: str
    condition: Dict[str, Any]
    priority: AlertPriority = AlertPriority.MEDIUM
    enabled: bool = True
    triggered: bool = False
    trigger_count: int = 0
    last_triggered: float = 0
    cooldown: int = 60  # 秒
    callbacks: List[Callable] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


class AlertCondition:
    """警报条件构建器"""
    
    @staticmethod
    def price_above(price: float) -> Dict:
        return {'type': 'price_above', 'value': price}
    
    @staticmethod
    def price_below(price: float) -> Dict:
        return {'type': 'price_below', 'value': price}
    
    @staticmethod
    def rsi_above(value: float) -> Dict:
        return {'type': 'rsi_above', 'value': value}
    
    @staticmethod
    def rsi_below(value: float) -> Dict:
        return {'type': 'rsi_below', 'value': value}
    
    @staticmethod
    def macd_cross_up() -> Dict:
        return {'type': 'macd_cross', 'direction': 'up'}
    
    @staticmethod
    def macd_cross_down() -> Dict:
        return {'type': 'macd_cross', 'direction': 'down'}
    
    @staticmethod
    def volume_spike(multiplier: float = 2.0) -> Dict:
        return {'type': 'volume_spike', 'multiplier': multiplier}
    
    @staticmethod
    def and_(*conditions: Dict) -> Dict:
        return {'type': 'and', 'conditions': list(conditions)}
    
    @staticmethod
    def or_(*conditions: Dict) -> Dict:
        return {'type': 'or', 'conditions': list(conditions)}


class AlertManager:
    """警报管理器"""
    
    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: List[Dict] = []
        self.lock = threading.Lock()
        self._id_counter = 0
        
        # Statistics
        self.stats = {
            'total_triggered': 0,
            'by_type': defaultdict(int),
            'by_symbol': defaultdict(int)
        }
    
    def _generate_id(self) -> str:
        """生成唯一ID"""
        self._id_counter += 1
        return f"alert_{int(time.time()*1000)}_{self._id_counter}"
    
    def create_alert(self, name: str, alert_type: AlertType, symbol: str, 
                     condition: Dict, priority: AlertPriority = AlertPriority.MEDIUM,
                     cooldown: int = 60) -> str:
        """创建警报"""
        alert_id = self._generate_id()
        
        alert = Alert(
            id=alert_id,
            name=name,
            alert_type=alert_type,
            symbol=symbol,
            condition=condition,
            priority=priority,
            cooldown=cooldown
        )
        
        with self.lock:
            self.alerts[alert_id] = alert
        
        return alert_id
    
    def add_callback(self, alert_id: str, callback: Callable):
        """添加警报回调"""
        with self.lock:
            if alert_id in self.alerts:
                self.alerts[alert_id].callbacks.append(callback)
    
    def enable_alert(self, alert_id: str):
        """启用警报"""
        with self.lock:
            if alert_id in self.alerts:
                self.alerts[alert_id].enabled = True
    
    def disable_alert(self, alert_id: str):
        """禁用警报"""
        with self.lock:
            if alert_id in self.alerts:
                self.alerts[alert_id].enabled = False
    
    def delete_alert(self, alert_id: str):
        """删除警报"""
        with self.lock:
            if alert_id in self.alerts:
                del self.alerts[alert_id]
    
    def check_alert(self, alert_id: str, market_data: Dict) -> Optional[Dict]:
        """检查警报条件"""
        with self.lock:
            if alert_id not in self.alerts:
                return None
            
            alert = self.alerts[alert_id]
            
            if not alert.enabled or alert.triggered:
                return None
            
            # Check cooldown
            if time.time() - alert.last_triggered < alert.cooldown:
                return None
        
        # Evaluate condition
        triggered = self._evaluate_condition(alert, market_data)
        
        if triggered:
            return self._trigger_alert(alert_id)
        
        return None
    
    def _evaluate_condition(self, alert: Alert, data: Dict) -> bool:
        """评估警报条件"""
        condition = alert.condition
        cond_type = condition.get('type')
        
        if cond_type == 'price_above':
            return data.get('price', 0) > condition['value']
        
        elif cond_type == 'price_below':
            return data.get('price', 0) < condition['value']
        
        elif cond_type == 'rsi_above':
            return data.get('rsi', 50) > condition['value']
        
        elif cond_type == 'rsi_below':
            return data.get('rsi', 50) < condition['value']
        
        elif cond_type == 'macd_cross':
            macd = data.get('macd', {})
            direction = condition.get('direction')
            if direction == 'up':
                return macd.get('macd', 0) > macd.get('signal', 0) and \
                       data.get('prev_macd', 0) <= data.get('prev_signal', 0)
            else:
                return macd.get('macd', 0) < macd.get('signal', 0) and \
                       data.get('prev_macd', 0) >= data.get('prev_signal', 0)
        
        elif cond_type == 'volume_spike':
            return data.get('volume', 0) > data.get('avg_volume', 0) * condition['multiplier']
        
        elif cond_type == 'and':
            return all(self._check_simple_condition(c, data) for c in condition['conditions'])
        
        elif cond_type == 'or':
            return any(self._check_simple_condition(c, data) for c in condition['conditions'])
        
        return False
    
    def _check_simple_condition(self, condition: Dict, data: Dict) -> bool:
        """检查简单条件"""
        cond_type = condition.get('type')
        
        if cond_type == 'price_above':
            return data.get('price', 0) > condition['value']
        elif cond_type == 'price_below':
            return data.get('price', 0) < condition['value']
        elif cond_type == 'rsi_above':
            return data.get('rsi', 50) > condition['value']
        elif cond_type == 'rsi_below':
            return data.get('rsi', 50) < condition['value']
        
        return False
    
    def _trigger_alert(self, alert_id: str) -> Dict:
        """触发警报"""
        with self.lock:
            alert = self.alerts[alert_id]
            
            alert.triggered = True
            alert.trigger_count += 1
            alert.last_triggered = time.time()
            
            # Update stats
            self.stats['total_triggered'] += 1
            self.stats['by_type'][alert.alert_type.value] += 1
            self.stats['by_symbol'][alert.symbol] += 1
        
        # Build trigger info
        trigger_info = {
            'alert_id': alert_id,
            'name': alert.name,
            'type': alert.alert_type.value,
            'symbol': alert.symbol,
            'priority': alert.priority.name,
            'timestamp': time.time(),
            'trigger_count': alert.trigger_count
        }
        
        # Execute callbacks
        for callback in alert.callbacks:
            try:
                callback(trigger_info)
            except Exception as e:
                print(f"Alert callback error: {e}")
        
        # Log to history
        self.alert_history.append(trigger_info)
        
        # Reset triggered flag after cooldown
        threading.Timer(alert.cooldown, self._reset_alert, args=[alert_id]).start()
        
        return trigger_info
    
    def _reset_alert(self, alert_id: str):
        """重置警报触发状态"""
        with self.lock:
            if alert_id in self.alerts:
                self.alerts[alert_id].triggered = False
    
    def check_all(self, market_data: Dict[str, Dict]) -> List[Dict]:
        """检查所有警报"""
        triggered = []
        
        for alert_id in list(self.alerts.keys()):
            symbol = self.alerts[alert_id].symbol
            if symbol in market_data:
                result = self.check_alert(alert_id, market_data[symbol])
                if result:
                    triggered.append(result)
        
        return triggered
    
    def get_alerts(self, symbol: str = None, enabled: bool = None) -> List[Alert]:
        """获取警报列表"""
        with self.lock:
            alerts = list(self.alerts.values())
            
            if symbol:
                alerts = [a for a in alerts if a.symbol == symbol]
            if enabled is not None:
                alerts = [a for a in alerts if a.enabled == enabled]
            
            return alerts
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        with self.lock:
            return {
                **self.stats,
                'total_alerts': len(self.alerts),
                'enabled_alerts': sum(1 for a in self.alerts.values() if a.enabled),
                'recent_history': self.alert_history[-10:]
            }
    
    def export_alerts(self) -> str:
        """导出警报配置"""
        with self.lock:
            data = {
                alert_id: {
                    'name': alert.name,
                    'type': alert.alert_type.value,
                    'symbol': alert.symbol,
                    'condition': alert.condition,
                    'priority': alert.priority.name,
                    'enabled': alert.enabled,
                    'cooldown': alert.cooldown
                }
                for alert_id, alert in self.alerts.items()
            }
            return json.dumps(data, indent=2)
    
    def import_alerts(self, json_str: str):
        """导入警报配置"""
        data = json.loads(json_str)
        
        with self.lock:
            for alert_id, config in data.items():
                alert = Alert(
                    id=alert_id,
                    name=config['name'],
                    alert_type=AlertType(config['type']),
                    symbol=config['symbol'],
                    condition=config['condition'],
                    priority=AlertPriority[config.get('priority', 'MEDIUM')],
                    enabled=config.get('enabled', True),
                    cooldown=config.get('cooldown', 60)
                )
                self.alerts[alert_id] = alert


class AlertNotifier:
    """警报通知器"""
    
    def __init__(self, alert_manager: AlertManager):
        self.alert_manager = alert_manager
        self.notifiers = []
    
    def add_notifier(self, notifier: Callable):
        """添加通知器"""
        self.notifiers.append(notifier)
    
    def notify(self, alert_info: Dict):
        """发送通知"""
        for notifier in self.notifiers:
            try:
                notifier(alert_info)
            except Exception as e:
                print(f"Notifier error: {e}")
    
    def telegram_notify(self, token: str, chat_id: str):
        """Telegram通知"""
        def send(alert_info: Dict):
            import urllib.request
            import urllib.parse
            
            message = f"🔔 *{alert_info['name']}*\n"
            message += f"类型: {alert_info['type']}\n"
            message += f"交易对: {alert_info['symbol']}\n"
            message += f"优先级: {alert_info['priority']}\n"
            message += f"时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(alert_info['timestamp']))}"
            
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = urllib.parse.urlencode({
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }).encode()
            
            try:
                req = urllib.request.Request(url, data=data)
                urllib.request.urlopen(req, timeout=10)
            except Exception as e:
                print(f"Telegram notification failed: {e}")
        
        self.add_notifier(send)
    
    def log_notify(self):
        """日志通知"""
        def send(alert_info: Dict):
            print(f"\n{'='*50}")
            print(f"🔔 警报触发: {alert_info['name']}")
            print(f"   类型: {alert_info['type']}")
            print(f"   交易对: {alert_info['symbol']}")
            print(f"   优先级: {alert_info['priority']}")
            print(f"{'='*50}\n")
        
        self.add_notifier(send)


if __name__ == "__main__":
    # Test Alert System
    manager = AlertManager()
    
    # Create alerts
    alert_id1 = manager.create_alert(
        name="BTC RSI超卖",
        alert_type=AlertType.RSI_OVERSOLD,
        symbol="BTCUSDT",
        condition=AlertCondition.rsi_below(30),
        priority=AlertPriority.HIGH
    )
    
    alert_id2 = manager.create_alert(
        name="BTC价格突破",
        alert_type=AlertType.PRICE_ABOVE,
        symbol="BTCUSDT",
        condition=AlertCondition.price_above(75000),
        priority=AlertPriority.MEDIUM
    )
    
    # Add callback
    def on_alert(info):
        print(f"回调收到警报: {info['name']}")
    
    manager.add_callback(alert_id1, on_alert)
    
    # Test check
    print("\n=== Alert System Test ===")
    print(f"Created 2 alerts")
    print(f"Alert ID 1: {alert_id1}")
    print(f"Alert ID 2: {alert_id2}")
    
    # Check alert
    test_data = {
        'BTCUSDT': {
            'price': 71000,
            'rsi': 28,
            'volume': 1000,
            'avg_volume': 800
        }
    }
    
    results = manager.check_all(test_data)
    print(f"\nTriggered alerts: {len(results)}")
    for r in results:
        print(f"  - {r['name']}")
    
    # Get stats
    stats = manager.get_stats()
    print(f"\nStats: {stats['total_triggered']} total triggered")
