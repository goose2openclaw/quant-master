"""
Alert System - Top5异动 + 实时告警
币种异动/策略信号/系统告警
"""
import sys
import time
import random
from typing import Dict, List, Optional
from dataclasses import dataclass, field

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

@dataclass
class Alert:
    alert_id: str
    priority: str  # HIGH/MEDIUM/LOW
    category: str  # PRICE_MOVE/RISK/SYSTEM/SIGNAL
    title: str
    message: str
    symbol: Optional[str]
    value: float
    timestamp: float
    acknowledged: bool = False
    metadata: Dict = field(default_factory=dict)

class AlertSystem:
    """
    告警系统
    - Top5异动监控
    - 实时告警
    - 分级处理
    """
    
    def __init__(self):
        self.name = "Alert System"
        self.alerts: List[Alert] = []
        self.alert_count = 0
        
        # 告警阈值
        self.price_move_threshold = 5.0  # %
        self.volume_threshold = 2.0  # 2x average
        self.risk_threshold = 20.0  # VaR %
    
    def check_price_alerts(self, prices: Dict[str, float],
                          prev_prices: Dict[str, float]) -> List[Alert]:
        """检查价格异动"""
        new_alerts = []
        
        for symbol in prices:
            if symbol not in prev_prices:
                continue
            
            change_pct = (prices[symbol] - prev_prices[symbol]) / prev_prices[symbol] * 100
            
            if abs(change_pct) >= self.price_move_threshold:
                priority = 'HIGH' if abs(change_pct) >= 10 else 'MEDIUM'
                direction = '🚀' if change_pct > 0 else '📉'
                
                alert = Alert(
                    alert_id=f"ALERT_{self.alert_count + 1:05d}",
                    priority=priority,
                    category='PRICE_MOVE',
                    title=f"{symbol} 价格异动",
                    message=f"{direction} {symbol} 涨跌 {change_pct:+.2f}%",
                    symbol=symbol,
                    value=change_pct,
                    timestamp=time.time()
                )
                new_alerts.append(alert)
                self.alerts.append(alert)
                self.alert_count += 1
        
        return new_alerts
    
    def check_volume_alerts(self, volumes: Dict[str, float],
                          avg_volumes: Dict[str, float]) -> List[Alert]:
        """检查成交量异动"""
        new_alerts = []
        
        for symbol in volumes:
            if symbol not in avg_volumes:
                continue
            
            ratio = volumes[symbol] / avg_volumes[symbol]
            
            if ratio >= self.volume_threshold:
                alert = Alert(
                    alert_id=f"ALERT_{self.alert_count + 1:05d}",
                    priority='MEDIUM',
                    category='VOLUME_SPIKE',
                    title=f"{symbol} 成交量放大",
                    message=f"📊 {symbol} 成交量达到平均 {ratio:.1f}x",
                    symbol=symbol,
                    value=ratio,
                    timestamp=time.time()
                )
                new_alerts.append(alert)
                self.alerts.append(alert)
                self.alert_count += 1
        
        return new_alerts
    
    def check_signal_alerts(self, signals: Dict[str, str]) -> List[Alert]:
        """检查信号告警"""
        new_alerts = []
        
        for symbol, signal in signals.items():
            if signal in ['STRONG_BUY', 'STRONG_SELL']:
                alert = Alert(
                    alert_id=f"ALERT_{self.alert_count + 1:05d}",
                    priority='HIGH',
                    category='SIGNAL',
                    title=f"{symbol} {signal}",
                    message=f"🎯 {symbol} 发出 {signal} 信号",
                    symbol=symbol,
                    value=1.0,
                    timestamp=time.time()
                )
                new_alerts.append(alert)
                self.alerts.append(alert)
                self.alert_count += 1
        
        return new_alerts
    
    def check_risk_alerts(self, metrics: Dict) -> List[Alert]:
        """检查风险告警"""
        new_alerts = []
        
        # VaR告警
        if metrics.get('var_95', 0) > metrics.get('total_assets', 0) * 0.1:
            alert = Alert(
                alert_id=f"ALERT_{self.alert_count + 1:05d}",
                priority='HIGH',
                category='RISK',
                title="VaR 超限",
                message=f"⚠️ VaR(95%) ${metrics['var_95']:.2f} 超过资产10%",
                symbol=None,
                value=metrics.get('var_95', 0),
                timestamp=time.time()
            )
            new_alerts.append(alert)
            self.alerts.append(alert)
            self.alert_count += 1
        
        # MDD告警
        if metrics.get('max_drawdown_pct', 0) > 20:
            alert = Alert(
                alert_id=f"ALERT_{self.alert_count + 1:05d}",
                priority='HIGH',
                category='RISK',
                title="回撤超限",
                message=f"⚠️ 最大回撤 {metrics['max_drawdown_pct']:.1f}% 超过20%",
                symbol=None,
                value=metrics.get('max_drawdown_pct', 0),
                timestamp=time.time()
            )
            new_alerts.append(alert)
            self.alerts.append(alert)
            self.alert_count += 1
        
        return new_alerts
    
    def get_top_alerts(self, limit: int = 5) -> List[Alert]:
        """获取Top异动"""
        sorted_alerts = sorted(self.alerts, key=lambda x: (
            {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}[x.priority],
            -x.timestamp
        ))
        return sorted_alerts[:limit]
    
    def get_unacknowledged_count(self) -> int:
        """获取未确认告警数"""
        return sum(1 for a in self.alerts if not a.acknowledged)
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """确认告警"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                return True
        return False
    
    def get_alert_summary(self) -> Dict:
        """获取告警摘要"""
        return {
            'total': len(self.alerts),
            'unacknowledged': self.get_unacknowledged_count(),
            'by_priority': {
                'HIGH': sum(1 for a in self.alerts if a.priority == 'HIGH'),
                'MEDIUM': sum(1 for a in self.alerts if a.priority == 'MEDIUM'),
                'LOW': sum(1 for a in self.alerts if a.priority == 'LOW'),
            },
            'by_category': {
                'PRICE_MOVE': sum(1 for a in self.alerts if a.category == 'PRICE_MOVE'),
                'VOLUME_SPIKE': sum(1 for a in self.alerts if a.category == 'VOLUME_SPIKE'),
                'SIGNAL': sum(1 for a in self.alerts if a.category == 'SIGNAL'),
                'RISK': sum(1 for a in self.alerts if a.category == 'RISK'),
            }
        }

if __name__ == '__main__':
    alert_sys = AlertSystem()
    
    print("=== Alert System ===\n")
    
    # Simulate price alerts
    prev_prices = {'BTC': 65000, 'ETH': 3200, 'SOL': 75}
    prices = {'BTC': 69596, 'ETH': 3500, 'SOL': 82}
    
    alerts = alert_sys.check_price_alerts(prices, prev_prices)
    print(f"Price Alerts: {len(alerts)}")
    for a in alerts:
        print(f"  {a.priority} {a.title}: {a.message}")
    
    # Top 5 alerts
    print(f"\nTop Alerts:")
    for a in alert_sys.get_top_alerts(5):
        print(f"  {a.priority} {a.category} {a.title}")
    
    # Summary
    summary = alert_sys.get_alert_summary()
    print(f"\nSummary: {summary['total']} alerts, {summary['unacknowledged']} unacked")
