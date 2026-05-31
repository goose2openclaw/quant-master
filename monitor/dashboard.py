"""实时Dashboard"""
from flask import render_template_string
import time

class Dashboard:
    def __init__(self, portfolio_manager, order_manager):
        self.portfolio = portfolio_manager
        self.order_manager = order_manager
        self.alerts = []
    
    def get_status(self):
        """获取状态"""
        return {
            'total_value': self.portfolio.get_total_value(),
            'positions': self.portfolio.get_all_positions(),
            'orders': len(self.order_manager.get_all_orders()),
            'open_orders': len(self.order_manager.get_open_orders()),
            'time': time.strftime('%H:%M:%S')
        }
    
    def add_alert(self, msg, level='info'):
        """添加警报"""
        self.alerts.append({
            'time': time.time(),
            'msg': msg,
            'level': level  # info/warning/critical
        })
        # 只保留最近100条
        self.alerts = self.alerts[-100:]
    
    def get_alerts(self, level=None):
        """获取警报"""
        if level:
            return [a for a in self.alerts if a['level'] == level]
        return self.alerts
    
    def html(self):
        """生成HTML"""
        status = self.get_status()
        alerts = self.get_alerts()
        return f"""
        <div class='dashboard'>
            <h2>QuantMaster Dashboard</h2>
            <div class='metrics'>
                <div>总权益: ${status['total_value']:.2f}</div>
                <div>持仓数: {len(status['positions'])}</div>
                <div>订单数: {status['orders']}</div>
                <div>时间: {status['time']}</div>
            </div>
            <div class='alerts'>
                <h3>警报</h3>
                {''.join(f"<div class='{a['level']}'>{a['msg']}</div>" for a in alerts[-5:])}
            </div>
        </div>
        """
