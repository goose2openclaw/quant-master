"""
税务报告生成器 - 加密货币税务计算
支持: 交易记录、收益计算、税务报表生成
"""
import json, csv
from datetime import datetime, timedelta
from io import StringIO

class TaxEvent:
    """税务事件"""
    def __init__(self, date, type, asset, proceeds, cost_basis, gain_loss):
        self.date = date
        self.type = type  # SELL, TRADE, INCOME, GIFT
        self.asset = asset
        self.proceeds = proceeds
        self.cost_basis = cost_basis
        self.gain_loss = gain_loss
        self.holding_period = ""  # SHORT, LONG
        self.taxable = True

class TaxReportGenerator:
    """
    税务报告生成器
    支持: FIFO/LIFO成本计算、短中长期持有个税计算
    """
    def __init__(self, country='US'):
        self.country = country
        self.transactions = []
        self.cost_basis_method = 'FIFO'  # FIFO, LIFO, HIFO
        self.tax_year = datetime.now().year
        
        # 税率 (简化)
        self.rates = {
            'US': {
                'short_term_rate': 0.22,  # 短期 (不满1年)
                'long_term_rate': 0.15,   # 长期 (1年以上)
                'income_rate': 0.24        # 收入税率
            },
            'UK': {
                'short_term_rate': 0.20,
                'long_term_rate': 0.10,
                'income_rate': 0.20
            }
        }
    
    def add_transaction(self, date, type, asset, qty, price, fee=0):
        """添加交易"""
        self.transactions.append({
            'date': date,
            'type': type,  # BUY, SELL, TRADE, INCOME
            'asset': asset,
            'qty': qty,
            'price': price,
            'fee': fee,
            'proceeds': qty * price - fee if type in ['SELL', 'TRADE'] else 0,
            'cost': qty * price + fee if type == 'BUY' else 0
        })
    
    def calculate_cost_basis(self, sells):
        """计算成本基础 (FIFO)"""
        buys = []
        events = []
        
        for sell in sells:
            remaining_qty = sell['qty']
            total_cost = 0
            
            while remaining_qty > 0 and buys:
                oldest_buy = buys[0]
                
                if oldest_buy['remaining'] >= remaining_qty:
                    total_cost += oldest_buy['price'] * remaining_qty
                    oldest_buy['remaining'] -= remaining_qty
                    remaining_qty = 0
                else:
                    total_cost += oldest_buy['price'] * oldest_buy['remaining']
                    remaining_qty -= oldest_buy['remaining']
                    buys.pop(0)
            
            sell_proceeds = sell['qty'] * sell['price'] - sell.get('fee', 0)
            gain_loss = sell_proceeds - total_cost
            
            # 判断持有期限
            if buys:
                buy_date = buys[0]['date']
                holding_days = (sell['date'] - buy_date).days if hasattr(buy_date, 'days') else 365
                holding_period = 'LONG' if holding_days >= 365 else 'SHORT'
            else:
                holding_period = 'SHORT'
            
            events.append(TaxEvent(
                date=sell['date'],
                type='SELL',
                asset=sell['asset'],
                proceeds=sell_proceeds,
                cost_basis=total_cost,
                gain_loss=gain_loss
            ))
            events[-1].holding_period = holding_period
        
        return events
    
    def generate_tax_report(self):
        """生成税务报告"""
        # 按资产分组
        assets = {}
        for tx in self.transactions:
            asset = tx['asset']
            if asset not in assets:
                assets[asset] = {'buys': [], 'sells': []}
            
            if tx['type'] == 'BUY':
                assets[asset]['buys'].append({
                    **tx, 'remaining': tx['qty']
                })
            elif tx['type'] in ['SELL', 'TRADE']:
                assets[asset]['sells'].append(tx)
        
        # 计算收益
        all_events = []
        for asset, data in assets.items():
            events = self.calculate_cost_basis(data['sells'])
            all_events.extend(events)
        
        # 按日期排序
        all_events.sort(key=lambda x: x.date)
        
        # 分离短期和长期
        short_term = [e for e in all_events if e.holding_period == 'SHORT']
        long_term = [e for e in all_events if e.holding_period == 'LONG']
        
        rates = self.rates.get(self.country, self.rates['US'])
        
        # 计算税额
        short_term_gain = sum(e.gain_loss for e in short_term if e.gain_loss > 0)
        short_term_loss = sum(e.gain_loss for e in short_term if e.gain_loss < 0)
        long_term_gain = sum(e.gain_loss for e in long_term if e.gain_loss > 0)
        long_term_loss = sum(e.gain_loss for e in long_term if e.gain_loss < 0)
        
        net_short = short_term_gain + short_term_loss
        net_long = long_term_gain + long_term_loss
        
        short_term_tax = max(0, net_short * rates['short_term_rate'])
        long_term_tax = max(0, net_long * rates['long_term_rate'])
        
        total_tax = short_term_tax + long_term_tax
        
        return {
            'tax_year': self.tax_year,
            'country': self.country,
            'cost_basis_method': self.cost_basis_method,
            'summary': {
                'total_transactions': len(self.transactions),
                'total_proceeds': sum(e.proceeds for e in all_events),
                'total_cost_basis': sum(e.cost_basis for e in all_events),
                'total_gain_loss': sum(e.gain_loss for e in all_events)
            },
            'short_term': {
                'transactions': len(short_term),
                'gains': short_term_gain,
                'losses': abs(short_term_loss),
                'net': net_short,
                'tax': short_term_tax
            },
            'long_term': {
                'transactions': len(long_term),
                'gains': long_term_gain,
                'losses': abs(long_term_loss),
                'net': net_long,
                'tax': long_term_tax
            },
            'total_tax_liability': total_tax,
            'events': [{
                'date': e.date.isoformat() if hasattr(e.date, 'isoformat') else str(e.date),
                'type': e.type,
                'asset': e.asset,
                'proceeds': e.proceeds,
                'cost_basis': e.cost_basis,
                'gain_loss': e.gain_loss,
                'holding_period': e.holding_period
            } for e in all_events]
        }
    
    def export_csv(self, filepath):
        """导出CSV"""
        report = self.generate_tax_report()
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Date', 'Type', 'Asset', 'Proceeds', 'Cost Basis', 'Gain/Loss', 'Holding Period'])
            
            for event in report['events']:
                writer.writerow([
                    event['date'],
                    event['type'],
                    event['asset'],
                    f"{event['proceeds']:.2f}",
                    f"{event['cost_basis']:.2f}",
                    f"{event['gain_loss']:.2f}",
                    event['holding_period']
                ])
        
        print(f"[Tax] CSV导出: {filepath}")
    
    def export_json(self, filepath):
        """导出JSON"""
        report = self.generate_tax_report()
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"[Tax] JSON导出: {filepath}")
    
    def get_audit_summary(self):
        """获取审计摘要"""
        report = self.generate_tax_report()
        return {
            'transactions_count': report['summary']['total_transactions'],
            'assets_traded': len(set(t['asset'] for t in self.transactions)),
            'taxable_events': len([e for e in report['events'] if e['gain_loss'] != 0]),
            'estimated_tax': report['total_tax_liability']
        }
