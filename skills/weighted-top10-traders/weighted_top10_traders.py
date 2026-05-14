#!/usr/bin/env python3
"""
Weighted Top 10 Traders Module v2.0
==================================
蒸馏全球顶级交易员的交易模式和风格，形成加权组合系统

Trader Personas (金融界公认Top10):
1. George Soros - 索罗斯
2. Stanley Druckenmiller - 德鲁肯米勒
3. Bruce Kovner - 柯夫纳
4. Michael Marcus - 马库斯
5. Paul Tudor Jones - 琼斯
6. Richard Dennis - 丹尼斯
7. Martin Schwartz - 舒华兹
8. Bill Lipschutz - 利普舒茨
9. Jesse Livermore - 利弗莫尔
10. Jim Rogers - 罗杰斯
"""

import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class TraderProfile:
    name: str
    name_cn: str
    style: str
    achievement: str
    strength: List[str]
    weakness: List[str]
    best_market: str
    signals: List[str]
    base_weight: float

@dataclass
class MarketSignal:
    trend: str  # bull/bear/sideways
    volatility: str  # high/medium/low
    liquidity: str  # high/medium/low
    macro_outlook: str  # risk_on/risk_off
    technical_score: float  # 0.0-1.0
    fundamental_score: float  # 0.0-1.0
    momentum_score: float  # 0.0-1.0
    sentiment_score: float  # 0.0-1.0

@dataclass
class TradingDecision:
    primary_trader: str
    primary_trader_cn: str
    confidence: float
    direction: str  # long/short/neutral
    position_size: float
    stop_loss: float
    take_profit: float
    weighted_score: float
    reasoning: str
    all_weights: Dict[str, float]

class WeightedTop10Traders:
    """加权Top10交易员组合系统 v2.0"""
    
    # 十个蒸馏交易员配置
    TRADERS = {
        "soros": TraderProfile(
            name="George Soros",
            name_cn="乔治·索罗斯",
            style="宏观对冲/反身性理论",
            achievement="1992年狙击英镑赚取超10亿美元，'打败英格兰银行的人'",
            strength=["宏观趋势洞察", "重仓出击", "识别反转点", "反身性理论"],
            weakness=["需要大资金", "高风险敞口", "机会难得"],
            best_market="央行政策变化, 汇率战争, 信贷市场异常",
            signals=["央行干预", "汇率异动", "信贷利差扩大"],
            base_weight=0.12
        ),
        "druckenmiller": TraderProfile(
            name="Stanley Druckenmiller",
            name_cn="斯坦利·德鲁肯米勒",
            style="流动性狩猎/政策驱动",
            achievement="量子基金核心操盘手，策划东南亚金融风暴",
            strength=["流动性分析", "央行政策解读", "激进进攻", "快速执行"],
            weakness=["高风险", "需要流动性环境", "波动大"],
            best_market="央行放水, 流动性宽松, 政策驱动行情",
            signals=["央行资产负债表扩张", "流动性注入", "利率决议"],
            base_weight=0.12
        ),
        "kovner": TraderProfile(
            name="Bruce Kovner",
            name_cn="布鲁斯·柯夫纳",
            style="外汇期货/趋势跟踪",
            achievement="1978-1988年年均回报87%，创立卡克斯顿资管",
            strength=["外汇专精", "宏观+技术结合", "持仓能力", "纪律严明"],
            weakness=["需要耐心", "趋势假突破多"],
            best_market="外汇, 利率期货, 货币危机",
            signals=["央行政策", "技术突破", "趋势线假突破"],
            base_weight=0.10
        ),
        "marcus": TraderProfile(
            name="Michael Marcus",
            name_cn="迈克尔·马库斯",
            style="商品期货/趋势跟踪",
            achievement="10年将3万变8000万(2500倍)",
            strength=["趋势跟踪", "高杠杆", "持仓耐心", "商品专精"],
            weakness=["回撤大", "需要严格止损", "趋势逆转时痛苦"],
            best_market="大宗商品, 农产品, 金属",
            signals=["供需变化", "天气影响", "库存数据"],
            base_weight=0.08
        ),
        "jones": TraderProfile(
            name="Paul Tudor Jones",
            name_cn="保罗·都铎·琼斯",
            style="趋势跟踪/风险管理",
            achievement="成功预测1987年黑色星期一股市崩盘",
            strength=["择时精准", "风险管理", "宏观分析", "5%止损"],
            weakness=["盘整期亏损", "需要严格纪律", "短线压力大"],
            best_market="股指期货, 债券, 外汇, 单边趋势",
            signals=["均线突破", "RSI极端值", "趋势线破坏"],
            base_weight=0.12
        ),
        "dennis": TraderProfile(
            name="Richard Dennis",
            name_cn="理查德·丹尼斯",
            style="系统化交易/趋势跟踪",
            achievement="从400美元赚到2亿美元，'海龟交易实验'创始人",
            strength=["可复制系统", "趋势跟踪", "规则明确", "可教授"],
            weakness=["需要耐心等待", "趋势假突破", "参数敏感"],
            best_market="大宗商品, 金融期货, 趋势明确的任何市场",
            signals=["唐奇安通道突破", "趋势延续确认", "20日高低点突破"],
            base_weight=0.08
        ),
        "schwartz": TraderProfile(
            name="Martin Schwartz",
            name_cn="马丁·舒华兹",
            style="技术分析/短线交易",
            achievement="9次全美投资冠军，4万变2000万(210%平均回报)",
            strength=["K线形态", "快速认错", "灵活切换", "短线精准"],
            weakness=["交易成本高", "需要专注", "压力大的时期表现差"],
            best_market="股票, 期权, 波动性交易, 日内",
            signals=["K线形态", "支撑阻力", "成交量萎缩突破"],
            base_weight=0.10
        ),
        "lipschutz": TraderProfile(
            name="Bill Lipschutz",
            name_cn="比尔·利普舒茨",
            style="外汇专精/大额订单",
            achievement="所罗门兄弟外汇主管，单笔数十亿美元，创造利润超5亿",
            strength=["外汇专精", "大额订单执行", "流动性分析", "订单隐藏"],
            weakness=["专注外汇单一市场", "大资金限制"],
            best_market="外汇现货, 利率货币对, 新兴市场货币",
            signals=["汇率政策", "流动性供需", "央行干预信号"],
            base_weight=0.08
        ),
        "livermore": TraderProfile(
            name="Jesse Livermore",
            name_cn="杰西·利弗莫尔",
            style="价格行为/板块轮动",
            achievement="1929年崩盘前做空成名，'股票大作手'",
            strength=["价格阅读", "板块轮动", "择时大师", "趋势跟随"],
            weakness=["情绪控制难", "需要经验", "逆势危险"],
            best_market="股票, 期货, 所有流动性市场",
            signals=["价格创新高/低", "板块领涨/领跌", "突破回踩"],
            base_weight=0.10
        ),
        "rogers": TraderProfile(
            name="Jim Rogers",
            name_cn="吉姆·罗杰斯",
            style="商品期货/长期趋势",
            achievement="量子基金10年收益4200%，'商品大王'",
            strength=["商品专精", "长期趋势", "宏观视野", "耐心持有"],
            weakness=["需要长期资金", "短期波动痛苦", "不频繁交易"],
            best_market="大宗商品, 农产品, 能源,指数基金",
            signals=["供需拐点", "商品库存", "美元走势"],
            base_weight=0.10
        )
    }
    
    def __init__(self, state_file: str = None):
        self.state_file = state_file or "/home/goose/.openclaw/workspace/.wtt_state.json"
        self.performance_history = []
        self.current_weights = {k: v.base_weight for k, v in self.TRADERS.items()}
        self.load_state()
    
    def load_state(self):
        """加载优化状态"""
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
                self.performance_history = state.get('performance_history', [])
                self.current_weights = state.get('weights', self.current_weights)
        except: pass
    
    def save_state(self):
        """保存优化状态"""
        state = {
            'weights': self.current_weights,
            'performance_history': self.performance_history[-100:],
            'last_update': time.time()
        }
        with open(self.state_file, 'w') as f:
            json.dump(state, f)
    
    def analyze_market(self, signals: Dict) -> MarketSignal:
        """分析市场信号"""
        return MarketSignal(
            trend=signals.get('trend', 'sideways'),
            volatility=signals.get('volatility', 'medium'),
            liquidity=signals.get('liquidity', 'medium'),
            macro_outlook=signals.get('macro', 'neutral'),
            technical_score=signals.get('technical_score', 0.5),
            fundamental_score=signals.get('fundamental_score', 0.5),
            momentum_score=signals.get('momentum', 0.5),
            sentiment_score=signals.get('sentiment', 0.5)
        )
    
    def calculate_weights(self, market: MarketSignal) -> Dict[str, float]:
        """根据市场状态计算权重"""
        base = {k: v.base_weight for k, v in self.TRADERS.items()}
        
        # 趋势+波动率分析
        if market.trend == "bull" and market.volatility == "high":
            boosts = ["jones", "druckenmiller", "marcus", "livermore"]
        elif market.trend == "bull" and market.volatility == "low":
            boosts = ["rogers", "dennis", "schwartz", "kovner"]
        elif market.trend == "bear" and market.volatility == "high":
            boosts = ["soros", "druckenmiller", "livermore"]
        elif market.trend == "bear":
            boosts = ["kovner", "rogers", "soros"]
        elif market.trend == "sideways":
            boosts = ["dennis", "schwartz", "lipschutz"]
        else:
            boosts = ["kovner"]
        
        boost_factor = 1.4
        for t in boosts:
            if t in base:
                base[t] *= boost_factor
        
        # 动量评分影响
        if market.momentum_score > 0.7:
            base["jones"] *= 1.3
            base["marcus"] *= 1.2
            base["livermore"] *= 1.1
        elif market.momentum_score < 0.3:
            base["rogers"] *= 1.3
            base["kovner"] *= 1.2
        
        # 技术评分影响
        if market.technical_score > 0.7:
            base["schwartz"] *= 1.3
            base["livermore"] *= 1.2
            base["jones"] *= 1.1
        
        # 基本面评分影响
        if market.fundamental_score > 0.7:
            base["soros"] *= 1.3
            base["kovner"] *= 1.2
            base["druckenmiller"] *= 1.2
        
        # 流动性影响
        if market.liquidity == "high":
            base["druckenmiller"] *= 1.4
            base["soros"] *= 1.2
            base["lipschutz"] *= 1.1
        elif market.liquidity == "low":
            base["rogers"] *= 1.3
            base["kovner"] *= 1.1
        
        # 宏观风险偏好
        if market.macro_outlook == "risk_on":
            base["jones"] *= 1.3
            base["marcus"] *= 1.2
            base["druckenmiller"] *= 1.1
        elif market.macro_outlook == "risk_off":
            base["soros"] *= 1.4
            base["rogers"] *= 1.2
            base["kovner"] *= 1.1
        
        # 归一化
        total = sum(base.values())
        weights = {k: v/total for k, v in base.items()}
        self.current_weights = weights
        
        return weights
    
    def generate_decision(self, weights: Dict[str, float], market: MarketSignal) -> TradingDecision:
        """生成交易决策"""
        sorted_traders = sorted(weights.items(), key=lambda x: -x[1])
        primary = sorted_traders[0][0]
        primary_cn = self.TRADERS[primary].name_cn
        
        top3_weight = sum(w for _, w in sorted_traders[:3])
        confidence = top3_weight
        
        # 决策逻辑
        if market.trend == "bull":
            direction = "long"
            position_size = 0.30 if market.momentum_score > 0.6 else 0.20
        elif market.trend == "bear":
            direction = "short"
            position_size = 0.20
        else:
            direction = "neutral"
            position_size = 0.10
        
        # 止损止盈
        if market.volatility == "high":
            stop_loss = 0.08
            take_profit = 0.25
        else:
            stop_loss = 0.05
            take_profit = 0.15
        
        # 生成推理
        top_traders = [self.TRADERS[t].name_cn for t, _ in sorted_traders[:3]]
        reasoning = f"市场{market.trend} + {', '.join(top_traders)}模式"
        
        return TradingDecision(
            primary_trader=primary,
            primary_trader_cn=primary_cn,
            confidence=confidence,
            direction=direction,
            position_size=position_size,
            stop_loss=stop_loss,
            take_profit=take_profit,
            weighted_score=weights[primary],
            reasoning=reasoning,
            all_weights=weights
        )
    
    def record_performance(self, decision: TradingDecision, result: float):
        """记录表现用于优化"""
        self.performance_history.append({
            'trader': decision.primary_trader,
            'result': result,
            'timestamp': time.time()
        })
        
        if len(self.performance_history) >= 10:
            recent = self.performance_history[-10:]
            for trader in set(r['trader'] for r in recent):
                wins = sum(1 for r in recent if r['trader'] == trader and r['result'] > 0)
                if wins < 3:
                    self.current_weights[trader] *= 0.9
        
        self.save_state()
    
    def run(self, market_signals: Dict) -> TradingDecision:
        """主运行函数"""
        market = self.analyze_market(market_signals)
        weights = self.calculate_weights(market)
        decision = self.generate_decision(weights, market)
        return decision
    
    def get_trader_info(self, trader_id: str) -> Optional[TraderProfile]:
        """获取交易员详情"""
        return self.TRADERS.get(trader_id)
    
    def list_traders(self) -> Dict[str, str]:
        """列出所有交易员"""
        return {k: f"{v.name_cn} ({v.name})" for k, v in self.TRADERS.items()}

def main():
    """测试函数"""
    wtt = WeightedTop10Traders()
    
    print("=" * 70)
    print("Weighted Top 10 Traders v2.0 - 十大交易员蒸馏系统")
    print("=" * 70)
    
    # 列出交易员
    print("\n【十大蒸馏交易员】")
    for tid, name in wtt.list_traders().items():
        t = wtt.get_trader_info(tid)
        print(f"  {tid}: {name}")
        print(f"       风格: {t.style}")
    
    # 测试信号
    test_cases = [
        {
            'name': '牛市高波动',
            'signals': {'trend': 'bull', 'volatility': 'high', 'liquidity': 'high', 'macro': 'risk_on', 'technical_score': 0.8, 'fundamental_score': 0.6, 'momentum': 0.85, 'sentiment': 0.7}
        },
        {
            'name': '熊市高波动',
            'signals': {'trend': 'bear', 'volatility': 'high', 'liquidity': 'low', 'macro': 'risk_off', 'technical_score': 0.3, 'fundamental_score': 0.3, 'momentum': 0.2, 'sentiment': 0.2}
        },
        {
            'name': '盘整市',
            'signals': {'trend': 'sideways', 'volatility': 'medium', 'liquidity': 'medium', 'macro': 'neutral', 'technical_score': 0.5, 'fundamental_score': 0.5, 'momentum': 0.5, 'sentiment': 0.5}
        }
    ]
    
    for tc in test_cases:
        print(f"\n{'='*70}")
        print(f"测试场景: {tc['name']}")
        print(f"{'='*70}")
        
        result = wtt.run(tc['signals'])
        
        print(f"\n【权重分配】")
        for trader, weight in sorted(result.all_weights.items(), key=lambda x: -x[1]):
            t = wtt.get_trader_info(trader)
            print(f"  {t.name_cn}: {weight:.1%}")
        
        print(f"\n【交易决策】")
        print(f"  主要交易员: {result.primary_trader_cn} ({result.primary_trader})")
        print(f"  信心度: {result.confidence:.1%}")
        print(f"  方向: {result.direction}")
        print(f"  仓位: {result.position_size:.0%}")
        print(f"  止损: {result.stop_loss:.0%}")
        print(f"  止盈: {result.take_profit:.0%}")
        print(f"  推理: {result.reasoning}")

if __name__ == "__main__":
    main()
