"""
Investor Reports - 投资者报告生成
月报/年报
"""
from datetime import datetime, timedelta
from typing import Dict, List
import json

class ReportGenerator:
    """报告生成器"""
    def __init__(self):
        self.templates = {
            'monthly': self._monthly_template,
            'quarterly': self._quarterly_template,
            'annual': self._annual_template
        }
    
    def generate(self, report_type: str, data: Dict) -> str:
        """生成报告"""
        template = self.templates.get(report_type, self._monthly_template)
        return template(data)
    
    def _monthly_template(self, data: Dict) -> str:
        """月报模板"""
        return f"""
# 月度投资报告
## {data.get('period', datetime.now().strftime('%Y-%m'))}

### 概览
- 总收益: {data.get('total_return', 0):.2f}%
- 基准收益: {data.get('benchmark_return', 0):.2f}%
- 超额收益: {data.get('excess_return', 0):.2f}%

### 持仓摘要
{self._format_holdings(data.get('holdings', []))}

### 交易活动
- 总交易次数: {data.get('trade_count', 0)}
- 胜率: {data.get('win_rate', 0):.1f}%
- 平均持仓时间: {data.get('avg_holding_days', 0):.1f}天

### 风险指标
- 最大回撤: {data.get('max_drawdown', 0):.2f}%
- 夏普比率: {data.get('sharpe_ratio', 0):.2f}
- 波幅: {data.get('volatility', 0):.2f}%
"""
    
    def _quarterly_template(self, data: Dict) -> str:
        """季报模板"""
        return f"""
# 季度投资报告
## Q{self._get_quarter()} {datetime.now().year}

### 业绩表现
- 季度收益: {data.get('quarterly_return', 0):.2f}%
- 年化收益: {data.get('annualized_return', 0):.2f}%
- 相对基准: {data.get('excess_return', 0):.2f}%

### 组合构成
{self._format_holdings(data.get('holdings', []))}

### 归因分析
{self._format_attribution(data.get('attribution', {}))}
"""
    
    def _annual_template(self, data: Dict) -> str:
        """年报模板"""
        return f"""
# 年度投资报告
## {datetime.now().year} 年度报告

### 业绩概览
- 年度收益: {data.get('annual_return', 0):.2f}%
- 累计收益: {data.get('cumulative_return', 0):.2f}%

### 资产配置
{self._format_allocation(data.get('allocation', {}))}

### 风险调整收益
- 夏普比率: {data.get('sharpe_ratio', 0):.2f}
- 索提诺比率: {data.get('sortino_ratio', 0):.2f}
- 卡玛比率: {data.get('calmar_ratio', 0):.2f}
"""
    
    def _format_holdings(self, holdings: List[Dict]) -> str:
        lines = []
        for h in holdings:
            lines.append(f"- {h.get('symbol')}: {h.get('qty')} ({h.get('weight', 0):.1f}%)")
        return '\n'.join(lines) if lines else "无持仓"
    
    def _format_attribution(self, attr: Dict) -> str:
        return f"- 配置效应: {attr.get('allocation', 0):.2f}%\n- 选择效应: {attr.get('selection', 0):.2f}%"
    
    def _format_allocation(self, alloc: Dict) -> str:
        lines = []
        for asset, pct in alloc.items():
            lines.append(f"- {asset}: {pct:.1f}%")
        return '\n'.join(lines) if lines else "无数据"
    
    def _get_quarter(self) -> int:
        return (datetime.now().month - 1) // 3 + 1

class PDFReportExporter:
    """PDF报告导出"""
    def __init__(self):
        self.reports = []
    
    def export(self, content: str, filename: str) -> str:
        """导出PDF (简化)"""
        # 实际应使用weasyprint/reportlab
        filepath = f"/tmp/reports/{filename}.txt"
        with open(filepath, 'w') as f:
            f.write(content)
        self.reports.append({'filename': filename, 'content': content})
        return filepath

class PerformanceAttributionReport:
    """业绩归因报告"""
    def __init__(self):
        self.alloc_effect = 0
        self.selection_effect = 0
        self.interaction_effect = 0
    
    def calculate(self, portfolio: Dict, benchmark: Dict) -> Dict:
        """计算归因"""
        for symbol in set(list(portfolio.keys()) + list(benchmark.keys())):
            p_weight = portfolio.get(symbol, {}).get('weight', 0)
            b_weight = benchmark.get(symbol, {}).get('weight', 0)
            p_return = portfolio.get(symbol, {}).get('return', 0)
            b_return = benchmark.get(symbol, {}).get('return', 0)
            
            # 配置效应
            self.alloc_effect += (p_weight - b_weight) * b_return
            # 选择效应
            self.selection_effect += b_weight * (p_return - b_return)
        
        return {
            'allocation_effect': self.alloc_effect * 100,
            'selection_effect': self.selection_effect * 100,
            'total_effect': (self.alloc_effect + self.selection_effect) * 100
        }
