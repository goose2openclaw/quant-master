"""
QM Opportunity Hunter - 加强市场机会捕捉
"""
import sys
import time
import random
import math
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

try:
    from qm.binance_optimizer import BinanceAPI
    HAS_API = True
except:
    HAS_API = False

class StrategyMode(Enum):
    """策略模式"""
    CONSERVATIVE = "CONSERVATIVE"  # 保守
    BALANCED = "BALANCED"          # 平衡
    AGGRESSIVE = "AGGRESSIVE"     # 激进

@dataclass
class Opportunity:
    """机会"""
    symbol: str
    type: str           # BREAKOUT/MEAN_REVERSION/FUNDING_ARB/VOLATILITY
    action: str          # BUY/SELL/LONG/SHORT
    score: float
    confidence: float
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    reasons: List[str]

class OpportunityHunter:
    """
    机会猎手 - 加强市场机会捕捉
    
    五种机会类型:
    1. 突破 (Breakout)
    2. 均值回归 (Mean Reversion)
    3. 资金费率套利 (Funding Arbitrage)
    4. 波动率交易 (Volatility)
    5. 跨币种对冲 (Cross-Coin)
    """
    
    def __init__(self, api=None, mode: StrategyMode = StrategyMode.BALANCED):
        self.api = api or BinanceAPI()
        self.mode = mode
        self.capital = 10000
        
        # 模式配置
        self.mode_config = {
            StrategyMode.CONSERVATIVE: {
                'min_score': 75,
                'min_confidence': 80,
                'max_positions': 3,
                'position_size': 0.15,
                'stop_loss': 0.02,
                'take_profit': 0.06
            },
            StrategyMode.BALANCED: {
                'min_score': 65,
                'min_confidence': 70,
                'max_positions': 5,
                'position_size': 0.20,
                'stop_loss': 0.025,
                'take_profit': 0.08
            },
            StrategyMode.AGGRESSIVE: {
                'min_score': 55,
                'min_confidence': 60,
                'max_positions': 8,
                'position_size': 0.25,
                'stop_loss': 0.03,
                'take_profit': 0.10
            }
        }
    
    def set_mode(self, mode: StrategyMode):
        """设置策略模式"""
        self.mode = mode
    
    def detect_breakout(self, symbol: str) -> Optional[Opportunity]:
        """检测突破机会"""
        try:
            klines = self.api.get_klines(symbol, '1h', 100)
            if not klines:
                return None
            
            closes = [k['close'] for k in klines]
            highs = [k['high'] for k in klines]
            lows = [k['low'] for k in klines]
            volumes = [k['volume'] for k in klines]
            
            # 突破检测
            recent_high = max(highs[-20:-1])
            recent_low = min(lows[-20:-1])
            current = closes[-1]
            
            # 阻力位突破
            if current > recent_high * 1.01:
                volume_ratio = volumes[-1] / (sum(volumes[-20:]) / 20)
                
                score = 70 + volume_ratio * 15
                confidence = min(95, 60 + volume_ratio * 20)
                
                return Opportunity(
                    symbol=symbol.replace('USDT', ''),
                    type='BREAKOUT',
                    action='BUY',
                    score=score,
                    confidence=confidence,
                    entry_price=current,
                    stop_loss=recent_low,
                    take_profit=current * 1.08,
                    risk_reward=3.0,
                    reasons=[
                        f"突破阻力位 ${recent_high:.2f}",
                        f"成交量放大 {volume_ratio:.1f}x",
                        f"当前价 ${current:.2f}"
                    ]
                )
            
            # 支撑位突破做空
            if current < recent_low * 0.99:
                volume_ratio = volumes[-1] / (sum(volumes[-20:]) / 20)
                
                score = 70 + volume_ratio * 15
                confidence = min(95, 60 + volume_ratio * 20)
                
                return Opportunity(
                    symbol=symbol.replace('USDT', ''),
                    type='BREAKOUT',
                    action='SELL',
                    score=score,
                    confidence=confidence,
                    entry_price=current,
                    stop_loss=recent_high,
                    take_profit=current * 0.92,
                    risk_reward=3.0,
                    reasons=[
                        f"跌破支撑位 ${recent_low:.2f}",
                        f"成交量放大 {volume_ratio:.1f}x",
                        f"当前价 ${current:.2f}"
                    ]
                )
        except:
            pass
        return None
    
    def detect_mean_reversion(self, symbol: str) -> Optional[Opportunity]:
        """检测均值回归机会"""
        try:
            klines = self.api.get_klines(symbol, '1h', 100)
            if not klines:
                return None
            
            closes = [k['close'] for k in klines]
            
            # RSI均值回归
            deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
            gains = [d if d > 0 else 0 for d in deltas[-14:]]
            losses = [-d if d < 0 else 0 for d in deltas[-14:]]
            avg_gain = sum(gains) / 14
            avg_loss = sum(losses) / 14
            rs = avg_gain / avg_loss if avg_loss > 0 else 100
            rsi = 100 - (100 / (1 + rs))
            
            # 价格偏离
            ma20 = sum(closes[-20:]) / 20
            deviation = (closes[-1] - ma20) / ma20 * 100
            
            # RSI超卖 + 价格超跌 → 买入
            if rsi < 35 and deviation < -3:
                score = 75 + abs(deviation) * 5
                confidence = min(95, 70 + (35 - rsi))
                
                return Opportunity(
                    symbol=symbol.replace('USDT', ''),
                    type='MEAN_REVERSION',
                    action='BUY',
                    score=score,
                    confidence=confidence,
                    entry_price=closes[-1],
                    stop_loss=ma20 * 0.98,
                    take_profit=ma20 * 1.05,
                    risk_reward=2.5,
                    reasons=[
                        f"RSI超卖 {rsi:.1f}",
                        f"价格偏离 {deviation:+.1f}%",
                        f"均线支撑 ${ma20:.2f}"
                    ]
                )
            
            # RSI超买 + 价格超涨 → 卖出
            if rsi > 65 and deviation > 3:
                score = 75 + deviation * 5
                confidence = min(95, 70 + (rsi - 65))
                
                return Opportunity(
                    symbol=symbol.replace('USDT', ''),
                    type='MEAN_REVERSION',
                    action='SELL',
                    score=score,
                    confidence=confidence,
                    entry_price=closes[-1],
                    stop_loss=ma20 * 1.02,
                    take_profit=ma20 * 0.95,
                    risk_reward=2.5,
                    reasons=[
                        f"RSI超买 {rsi:.1f}",
                        f"价格偏离 {deviation:+.1f}%",
                        f"均线压力 ${ma20:.2f}"
                    ]
                )
        except:
            pass
        return None
    
    def detect_funding_arbitrage(self, symbol: str) -> Optional[Opportunity]:
        """检测资金费率套利"""
        try:
            funding = self.api.get_funding_rate(symbol.replace('USDT', 'USD'))
            if not funding:
                return None
            
            rate = funding.get('funding_rate', 0) * 100  # 转为百分比
            
            # 高资金费率套利
            if abs(rate) > 0.03:
                annual_rate = rate * 3 * 365  # 每天3次,一年365天
                
                if rate > 0:
                    action = 'LONG'
                    score = 80 + rate * 1000
                else:
                    action = 'SHORT'
                    score = 80 + abs(rate) * 1000
                
                confidence = min(95, 75 + abs(rate) * 500)
                
                return Opportunity(
                    symbol=symbol.replace('USDT', ''),
                    type='FUNDING_ARB',
                    action=action,
                    score=score,
                    confidence=confidence,
                    entry_price=funding.get('price', 100),
                    stop_loss=0,
                    take_profit=0,
                    risk_reward=annual_rate / 10,
                    reasons=[
                        f"资金费率 {rate:+.4f}%",
                        f"年化收益 {annual_rate:+.1f}%",
                        f"套利机会"
                    ]
                )
        except:
            pass
        return None
    
    def detect_volatility(self, symbol: str) -> Optional[Opportunity]:
        """检测波动率机会"""
        try:
            klines = self.api.get_klines(symbol, '1h', 100)
            if not klines:
                return None
            
            closes = [k['close'] for k in klines]
            highs = [k['high'] for k in klines]
            lows = [k['low'] for k in klines]
            
            # 波动率计算
            range_pct = (max(highs[-20:]) - min(lows[-20:])) / closes[-1] * 100
            
            # 低波动率后突破
            if range_pct < 5:
                current_range = (highs[-1] - lows[-1]) / closes[-1] * 100
                
                if current_range > range_pct * 1.5:
                    score = 70 + (10 - range_pct) * 5
                    confidence = min(95, 65 + (10 - range_pct) * 3)
                    
                    return Opportunity(
                        symbol=symbol.replace('USDT', ''),
                        type='VOLATILITY',
                        action='BUY',
                        score=score,
                        confidence=confidence,
                        entry_price=closes[-1],
                        stop_loss=lows[-1],
                        take_profit=highs[-1] * 1.05,
                        risk_reward=2.0,
                        reasons=[
                            f"波动率收缩 {range_pct:.1f}%",
                            f"突破在即",
                            f"当前波动 {current_range:.1f}%"
                        ]
                    )
        except:
            pass
        return None
    
    def scan_all(self) -> List[Opportunity]:
        """扫描所有机会"""
        opportunities = []
        
        symbols = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT',
            'ADAUSDT', 'LINKUSDT', 'DOTUSDT', 'AVAXUSDT', 'ATOMUSDT',
            'NEARUSDT', 'APTUSDT', 'ARBUSDT', 'OPUSDT'
        ]
        
        config = self.mode_config[self.mode]
        
        for symbol in symbols:
            # 突破
            opp = self.detect_breakout(symbol)
            if opp and opp.score >= config['min_score']:
                opportunities.append(opp)
            
            # 均值回归
            opp = self.detect_mean_reversion(symbol)
            if opp and opp.score >= config['min_score']:
                opportunities.append(opp)
            
            # 资金费率套利
            opp = self.detect_funding_arbitrage(symbol)
            if opp:
                opportunities.append(opp)
            
            # 波动率
            opp = self.detect_volatility(symbol)
            if opp and opp.score >= config['min_score']:
                opportunities.append(opp)
        
        # 过滤和排序
        opportunities = [
            o for o in opportunities
            if o.score >= config['min_score'] and o.confidence >= config['min_confidence']
        ]
        
        opportunities.sort(key=lambda x: x.score, reverse=True)
        
        return opportunities[:config['max_positions']]
    
    def generate_report(self) -> str:
        """生成报告"""
        opportunities = self.scan_all()
        
        config = self.mode_config[self.mode]
        
        mode_emoji = {
            StrategyMode.CONSERVATIVE: '🟡',
            StrategyMode.BALANCED: '🟢',
            StrategyMode.AGGRESSIVE: '🔴'
        }
        
        report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              🎯 QM Opportunity Hunter - 机会猎手                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

🌐 策略模式: {mode_emoji.get(self.mode, '⚪')} {self.mode.value}

╔══════════════════════════════════════════════════════════════════════════════╗
║                    📊 模式配置                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

   最低评分: {config['min_score']}
   最低置信: {config['min_confidence']}%
   最大持仓: {config['max_positions']}
   仓位比例: {config['position_size']*100:.0f}%
   止损:     {config['stop_loss']*100:.1f}%
   止盈:     {config['take_profit']*100:.1f}%

╔══════════════════════════════════════════════════════════════════════════════╗
║                    🎯 发现机会 ({len(opportunities)}个)                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        if not opportunities:
            report += "\n   ⚠️ 当前无满足条件的交易机会\n"
        else:
            for i, opp in enumerate(opportunities, 1):
                action_emoji = {'BUY': '🟢', 'SELL': '🔴', 'LONG': '🟢', 'SHORT': '🔴'}.get(opp.action, '⚪')
                
                report += f"""
   {i}. {action_emoji} {opp.symbol:8} {opp.type:15}
      操作: {opp.action} | 评分: {opp.score:.1f} | 置信: {opp.confidence:.0f}%
      风险回报: {opp.risk_reward:.1f}:1
      入场: ${opp.entry_price:.4f}
"""
                for reason in opp.reasons[:2]:
                    report += f"      • {reason}\n"
        
        report += "\n" + "=" * 66 + "\n"
        
        return report

def main():
    hunter = OpportunityHunter(mode=StrategyMode.BALANCED)
    print(hunter.generate_report())
    
    # 激进模式
    print("\n" + "=" * 66)
    print("激进模式扫描:")
    hunter.set_mode(StrategyMode.AGGRESSIVE)
    print(hunter.generate_report())

if __name__ == '__main__':
    main()
