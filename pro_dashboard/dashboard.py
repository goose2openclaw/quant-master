"""
专业级监控Dashboard
"""
import time, json
from datetime import datetime
from threading import Thread

class ProDashboard:
    """
    专业Dashboard
    实时显示: 持仓、盈亏、信号、风险、市场数据
    """
    def __init__(self):
        self.widgets = {}
        self.data = {}
        self.alerts = []
        self.trades = []
        self.positions = {}
        self.equity = []
        self.running = False
        self.update_interval = 1  # 秒
    
    def add_widget(self, name, widget_type, config):
        """添加组件"""
        self.widgets[name] = {
            'type': widget_type,
            'config': config,
            'data': None
        }
    
    def update_data(self, key, value):
        self.data[key] = value
        if key == 'positions':
            self.positions = value
        elif key == 'equity':
            self.equity = value
        elif key == 'trade':
            self.trades.append(value)
            self.trades = self.trades[-100:]
    
    def add_alert(self, message, level='info'):
        """添加警报"""
        self.alerts.append({
            'time': datetime.now().isoformat(),
            'message': message,
            'level': level  # info, warning, critical
        })
        self.alerts = self.alerts[-50:]
    
    def get_summary(self):
        """获取汇总"""
        return {
            'timestamp': datetime.now().isoformat(),
            'positions_count': len(self.positions),
            'total_equity': self.data.get('total_equity', 0),
            'daily_pnl': self.data.get('daily_pnl', 0),
            'win_rate': self._calc_win_rate(),
            'open_positions': self._get_open_positions(),
            'recent_trades': self.trades[-5:],
            'alerts': self.alerts[-5:]
        }
    
    def _calc_win_rate(self):
        if len(self.trades) < 5:
            return 0
        pnl_list = [t.get('pnl', 0) for t in self.trades if 'pnl' in t]
        wins = sum(1 for p in pnl_list if p > 0)
        return wins / len(pnl_list) * 100 if pnl_list else 0
    
    def _get_open_positions(self):
        return [{'symbol': p.symbol, 'qty': p.qty, 'entry': p.avg_price} 
                for p in self.positions.values() if p.get('qty', 0) > 0]
    
    def generate_html(self):
        """生成HTML页面"""
        summary = self.get_summary()
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>QuantMaster Pro Dashboard</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ font-family: 'Segoe UI', Arial; background: #0a0a0f; color: #eee; }}
                .header {{ background: linear-gradient(90deg, #1a1a2e, #16213e); padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; }}
                .header h1 {{ color: #00d4ff; font-size: 24px; }}
                .header .status {{ display: flex; gap: 20px; }}
                .status-item {{ background: rgba(255,255,255,0.1); padding: 8px 15px; border-radius: 4px; }}
                .status-item .label {{ font-size: 11px; color: #888; }}
                .status-item .value {{ font-size: 18px; font-weight: bold; }}
                .green {{ color: #00ff88; }}
                .red {{ color: #ff4757; }}
                .main {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; padding: 15px; }}
                .panel {{ background: #1a1a2e; border-radius: 8px; padding: 15px; }}
                .panel h3 {{ color: #00d4ff; margin-bottom: 10px; border-bottom: 1px solid #333; padding-bottom: 5px; }}
                .metric {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #222; }}
                .metric .label {{ color: #888; }}
                .metric .value {{ font-weight: bold; }}
                .position-item {{ display: flex; justify-content: space-between; padding: 10px; background: #16213e; margin: 5px 0; border-radius: 4px; }}
                .alert {{ padding: 8px; margin: 5px 0; border-radius: 4px; }}
                .alert.info {{ background: rgba(0,212,255,0.2); border-left: 3px solid #00d4ff; }}
                .alert.warning {{ background: rgba(255,193,7,0.2); border-left: 3px solid #ffc107; }}
                .alert.critical {{ background: rgba(255,71,87,0.2); border-left: 3px solid #ff4757; }}
                .trade-item {{ display: flex; justify-content: space-between; padding: 8px; background: #16213e; margin: 5px 0; border-radius: 4px; }}
                .BUY {{ color: #00ff88; }}
                .SELL {{ color: #ff4757; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>QuantMaster Pro</h1>
                <div class="status">
                    <div class="status-item">
                        <div class="label">总权益</div>
                        <div class="value green">${summary['total_equity']:.2f}</div>
                    </div>
                    <div class="status-item">
                        <div class="label">日盈亏</div>
                        <div class="value {'green' if summary['daily_pnl'] >= 0 else 'red'}">${summary['daily_pnl']:.2f}</div>
                    </div>
                    <div class="status-item">
                        <div class="label">胜率</div>
                        <div class="value">{summary['win_rate']:.1f}%</div>
                    </div>
                    <div class="status-item">
                        <div class="label">持仓</div>
                        <div class="value">{summary['positions_count']}</div>
                    </div>
                </div>
            </div>
            <div class="main">
                <div class="panel">
                    <h3>当前持仓</h3>
                    {''.join(f"<div class='position-item'><span>{p['symbol']}</span><span>{p['qty']:.4f} @ ${p['entry']:.4f}</span></div>" 
                             for p in summary['open_positions']) or '<p style="color:#888">无持仓</p>'}
                </div>
                <div class="panel">
                    <h3>最近交易</h3>
                    {''.join(f"<div class='trade-item'><span class='{t.get('side','')}'>{t.get('side','')} {t.get('symbol','')}</span><span>${t.get('price',0):.4f}</span></div>" 
                             for t in summary['recent_trades']) or '<p style="color:#888">无交易</p>'}
                </div>
                <div class="panel">
                    <h3>警报</h3>
                    {''.join(f"<div class='alert {a['level']}'><span style='color:#888;font-size:11px'>{a['time'][-8:]}</span> {a['message']}</div>" 
                             for a in summary['alerts']) or '<p style="color:#888">无警报</p>'}
                </div>
                <div class="panel">
                    <h3>系统状态</h3>
                    <div class="metric"><span class="label">运行时间</span><span class="value">{datetime.now().strftime('%H:%M:%S')}</span></div>
                    <div class="metric"><span class="label">更新频率</span><span class="value">{self.update_interval}s</span></div>
                    <div class="metric"><span class="label">数据点</span><span class="value">{len(self.equity)}</span></div>
                </div>
            </div>
        </body>
        </html>
        """
    
    def save_html(self, filepath):
        with open(filepath, 'w') as f:
            f.write(self.generate_html())
