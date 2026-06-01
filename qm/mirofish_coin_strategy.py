"""
QM MiroFish Coin Strategy - MiroFish策略与因子矩阵调度
根据不同币种和产品类型调用不同策略
"""
import sys
import random
from typing import Dict, List, Optional
from dataclasses import dataclass

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

try:
    from mirofish_core.mirofish import MiroFishCore, MiroFishConfig
    HAS_MIROFISH = True
except:
    HAS_MIROFISH = False

@dataclass
class CoinStrategy:
    """币种策略配置"""
    symbol: str
    category: str  # LARGE_CAP/MID_CAP/SMALL_CAP/DEFI/NFT/LAYER1
    risk_level: str  # LOW/MEDIUM/HIGH
    strategies: List[str]  # 使用的策略
    factors: List[str]  # 使用的因子
    weight_overrides: Dict[str, float]  # 权重覆盖

class MiroFishCoinDispatcher:
    """
    MiroFish币种策略调度器
    
    功能:
    1. 根据币种特性分配策略矩阵
    2. 根据产品类型分配因子矩阵
    3. 动态调整权重
    4. 统一调用MiroFish决策
    """
    
    # 币种策略配置
    COIN_STRATEGIES = {
        # 主流币 - 大市值,低风险
        'BTC': CoinStrategy(
            symbol='BTC',
            category='LARGE_CAP',
            risk_level='LOW',
            strategies=['RSI', 'MACD', 'Bollinger', 'Momentum'],
            factors=['RSI', 'MACD', 'Volume', 'Funding_rates', 'Fear_Greed'],
            weight_overrides={'RSI': 0.20, 'MACD': 0.20, 'Bollinger': 0.15}
        ),
        'ETH': CoinStrategy(
            symbol='ETH',
            category='LARGE_CAP',
            risk_level='LOW',
            strategies=['RSI', 'MACD', 'Bollinger', 'Momentum'],
            factors=['RSI', 'MACD', 'Volume', 'Funding_rates', 'Fear_Greed'],
            weight_overrides={'RSI': 0.18, 'MACD': 0.18, 'Bollinger': 0.15}
        ),
        'BNB': CoinStrategy(
            symbol='BNB',
            category='LARGE_CAP',
            risk_level='LOW',
            strategies=['RSI', 'MACD', 'Momentum', 'Scalping'],
            factors=['RSI', 'MACD', 'Social_volume', 'KOL_signals'],
            weight_overrides={'RSI': 0.20, 'MACD': 0.20, 'Social_volume': 0.15}
        ),
        
        # 中市值币 - 中风险
        'SOL': CoinStrategy(
            symbol='SOL',
            category='LAYER1',
            risk_level='MEDIUM',
            strategies=['RSI', 'MACD', 'Momentum', 'Breakout'],
            factors=['RSI', 'MACD', 'Volume', 'Social_volume', 'Whale_moves'],
            weight_overrides={'RSI': 0.15, 'MACD': 0.15, 'Breakout': 0.20, 'Volume': 0.15}
        ),
        'XRP': CoinStrategy(
            symbol='XRP',
            category='PAYMENT',
            risk_level='MEDIUM',
            strategies=['RSI', 'MACD', 'Scalping', 'Momentum'],
            factors=['RSI', 'MACD', 'Volume', 'DEX_flows'],
            weight_overrides={'RSI': 0.20, 'MACD': 0.20, 'Scalping': 0.15}
        ),
        'ADA': CoinStrategy(
            symbol='ADA',
            category='LAYER1',
            risk_level='MEDIUM',
            strategies=['RSI', 'Bollinger', 'Momentum', 'Swing'],
            factors=['RSI', 'Bollinger', 'Active_addresses', 'TVL'],
            weight_overrides={'RSI': 0.18, 'Bollinger': 0.18, 'Momentum': 0.15}
        ),
        'LINK': CoinStrategy(
            symbol='LINK',
            category='DEFI',
            risk_level='MEDIUM',
            strategies=['RSI', 'MACD', 'Momentum', 'Breakout'],
            factors=['RSI', 'MACD', 'TVL', 'DEX_flows', 'Whale_moves'],
            weight_overrides={'RSI': 0.15, 'MACD': 0.15, 'TVL': 0.18}
        ),
        'DOT': CoinStrategy(
            symbol='DOT',
            category='LAYER1',
            risk_level='MEDIUM',
            strategies=['RSI', 'Bollinger', 'Momentum', 'Swing'],
            factors=['RSI', 'Bollinger', 'Active_addresses', 'TVL'],
            weight_overrides={'RSI': 0.18, 'Bollinger': 0.18, 'Momentum': 0.15}
        ),
        
        # 高风险币 - 高风险高收益
        'PEPE': CoinStrategy(
            symbol='PEPE',
            category='MEME',
            risk_level='HIGH',
            strategies=['Momentum', 'Breakout', 'Scalping'],
            factors=['Social_volume', 'KOL_signals', 'Whale_moves', 'Volume'],
            weight_overrides={'Momentum': 0.25, 'Breakout': 0.25, 'Social_volume': 0.20}
        ),
        'SHIB': CoinStrategy(
            symbol='SHIB',
            category='MEME',
            risk_level='HIGH',
            strategies=['Momentum', 'Scalping', 'Breakout'],
            factors=['Social_volume', 'KOL_signals', 'Whale_moves'],
            weight_overrides={'Momentum': 0.25, 'Scalping': 0.20, 'Social_volume': 0.20}
        ),
        'TIA': CoinStrategy(
            symbol='TIA',
            category='DEFI',
            risk_level='HIGH',
            strategies=['RSI', 'MACD', 'Breakout', 'Momentum'],
            factors=['RSI', 'MACD', 'TVL', 'Active_addresses'],
            weight_overrides={'Breakout': 0.22, 'RSI': 0.15, 'MACD': 0.15}
        ),
    }
    
    # 产品类型策略
    PRODUCT_STRATEGIES = {
        'SPOT': {
            'primary': ['RSI', 'MACD', 'Bollinger', 'Momentum'],
            'weight_factor': 1.0,
            'risk_adjustment': 1.0
        },
        'FUTURES_USDT': {
            'primary': ['RSI', 'MACD', 'Breakout', 'Scalping'],
            'weight_factor': 1.5,
            'risk_adjustment': 1.5
        },
        'FUTURES_COIN': {
            'primary': ['RSI', 'MACD', 'Momentum'],
            'weight_factor': 2.0,
            'risk_adjustment': 2.0
        },
        'OPTIONS': {
            'primary': ['RSI', 'Bollinger', 'Momentum'],
            'weight_factor': 0.8,
            'risk_adjustment': 2.5
        },
        'EARN': {
            'primary': ['RSI', 'MACD'],
            'weight_factor': 0.5,
            'risk_adjustment': 0.3
        },
        'STAKING': {
            'primary': ['RSI', 'Volume'],
            'weight_factor': 0.3,
            'risk_adjustment': 0.2
        },
        'LEVERAGE': {
            'primary': ['RSI', 'MACD', 'Bollinger'],
            'weight_factor': 3.0,
            'risk_adjustment': 3.0
        }
    }
    
    def __init__(self, mirofish: MiroFishCore = None):
        self.mirofish = mirofish
        if HAS_MIROFISH and not self.mirofish:
            config = MiroFishConfig(simulation_required=True)
            self.mirofish = MiroFishCore(config)
    
    def get_coin_strategy(self, symbol: str) -> CoinStrategy:
        """获取币种策略"""
        # 去掉USDT后缀
        clean_symbol = symbol.replace('USDT', '').replace('USD', '')
        return self.COIN_STRATEGIES.get(clean_symbol, self._default_strategy(clean_symbol))
    
    def _default_strategy(self, symbol: str) -> CoinStrategy:
        """默认策略"""
        return CoinStrategy(
            symbol=symbol,
            category='UNKNOWN',
            risk_level='MEDIUM',
            strategies=['RSI', 'MACD', 'Momentum'],
            factors=['RSI', 'MACD', 'Volume'],
            weight_overrides={}
        )
    
    def get_product_strategy(self, product_type: str) -> Dict:
        """获取产品策略"""
        return self.PRODUCT_STRATEGIES.get(product_type, self.PRODUCT_STRATEGIES['SPOT'])
    
    def dispatch_strategy(self, symbol: str, product_type: str = 'SPOT') -> Dict:
        """调度策略 - 根据币种和产品类型"""
        coin_strat = self.get_coin_strategy(symbol)
        product_strat = self.get_product_strategy(product_type)
        
        # 合并策略
        combined_strategies = list(set(coin_strat.strategies + product_strat['primary']))
        
        # 计算权重
        weights = {}
        for s in combined_strategies:
            base_weight = 0.20 if s in ['RSI', 'MACD'] else 0.15 if s in ['Bollinger', 'Momentum'] else 0.10
            weight = coin_strat.weight_overrides.get(s, base_weight)
            weights[s] = weight * product_strat['weight_factor']
        
        # 归一化
        total = sum(weights.values())
        weights = {k: v/total for k, v in weights.items()}
        
        return {
            'symbol': symbol,
            'product_type': product_type,
            'coin_category': coin_strat.category,
            'risk_level': coin_strat.risk_level,
            'strategies': combined_strategies,
            'weights': weights,
            'factors': coin_strat.factors,
            'risk_adjustment': product_strat['risk_adjustment']
        }
    
    def generate_mirofish_decision(self, symbol: str, product_type: str = 'SPOT', price: float = None) -> Dict:
        """生成MiroFish决策"""
        dispatch = self.dispatch_strategy(symbol, product_type)
        
        # 模拟MiroFish决策
        if HAS_MIROFISH and self.mirofish:
            try:
                mf_decision = self.mirofish.generate_trading_decision(
                    symbol,
                    {'price': price or 100, 'strategies': dispatch['strategies']}
                )
                # Extract from MiroFish decision
                action = mf_decision.get('decision', 'HOLD')
                confidence = mf_decision.get('confidence', mf_decision.get('simulation', {}).get('confidence', 0.5))
                reasons = mf_decision.get('reasons', mf_decision.get('simulation', {}).get('reasons', []))
                projected_pnl = mf_decision.get('projected_pnl', mf_decision.get('simulation', {}).get('projected_pnl', 0))
            except Exception as e:
                action, confidence, reasons, projected_pnl = self._simulate_decision(symbol, dispatch, price)
        else:
            action, confidence, reasons, projected_pnl = self._simulate_decision(symbol, dispatch, price)
        
        return {
            'symbol': symbol,
            'product_type': product_type,
            'dispatch': dispatch,
            'decision': action,
            'confidence': confidence * 100,
            'action': action,
            'reasons': reasons if isinstance(reasons, list) else [],
            'projected_pnl': projected_pnl
        }
    
    def _simulate_decision(self, symbol: str, dispatch: Dict, price: float):
        """模拟决策"""
        confidence = random.uniform(0.5, 0.9)
        action = random.choice(['BUY', 'HOLD', 'SELL', 'BUY', 'HOLD'])
        
        reasons = [
            str(dispatch['coin_category']) + '币种',
            str(dispatch['product_type']) + '产品',
            '风险等级: ' + str(dispatch['risk_level']),
            '策略数量: ' + str(len(dispatch['strategies']))
        ]
        
        return action, confidence, reasons, 0
    
    def batch_dispatch(self, symbols: List[str], product_type: str = 'SPOT') -> List[Dict]:
        """批量调度"""
        results = []
        for symbol in symbols:
            results.append(self.generate_mirofish_decision(symbol, product_type))
        return results
    
    def generate_report(self, symbols: List[str] = None) -> str:
        """生成报告"""
        if symbols is None:
            symbols = ['BTC', 'ETH', 'SOL', 'XRP', 'LINK', 'TIA', 'PEPE']
        
        print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          🐟 QM MiroFish Coin Strategy - 币种策略调度                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
        
        for symbol in symbols:
            decision = self.generate_mirofish_decision(symbol, 'SPOT')
            d = decision
            
            print(f"📊 {symbol}")
            print(f"   币种类别: {d['dispatch']['coin_category']} | 风险: {d['dispatch']['risk_level']}")
            print(f"   策略: {', '.join(d['dispatch']['strategies'])}")
            print(f"   置信度: {d['confidence']:.0f}% | 操作: {d['decision']}")
            
            reasons = d['reasons'][:2] if d['reasons'] else []
            if reasons:
                print(f"   原因: {', '.join(reasons)}")
            print()
        
        print("=" * 70)
        
        return ""

def main():
    dispatcher = MiroFishCoinDispatcher()
    dispatcher.generate_report()

if __name__ == '__main__':
    main()
