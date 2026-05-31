"""
策略决策模块 - 整合所有策略
"""
from .config import RSI_BUY, RSI_SELL, BB_BUY, BB_SELL, MOMENTUM_THRESHOLD, MOMENTUM_RSI_MIN, MOMENTUM_SL
from .market import get_market_signal, get_24h_stats

def signal_strategy(symbol, prices):
    """逆势策略 - RSI超卖买入"""
    result = get_market_signal(symbol)
    if result[0] is None:
        return None
    
    price, rsi, bb_pos, momentum = result
    
    # 买入信号
    if rsi < RSI_BUY and bb_pos < BB_BUY:
        return {
            'type': 'oversold_buy',
            'sym': symbol,
            'price': price,
            'signal': 0.5,
            'rsi': rsi,
            'bb': bb_pos,
            'tp': 0.01,  # 1%
            'sl': 0.015  # 1.5%
        }
    
    # 卖出信号
    if rsi > RSI_SELL or bb_pos > BB_SELL:
        return {
            'type': 'overbought_sell',
            'sym': symbol,
            'price': price,
            'signal': -0.2
        }
    
    return None

def momentum_strategy(symbol, prices):
    """动量策略 - 追涨杀跌"""
    stats = get_24h_stats(symbol)
    if stats is None:
        return None
    
    # 检查24h涨幅
    if stats['change'] < MOMENTUM_THRESHOLD:
        return None
    
    # 检查RSI
    result = get_market_signal(symbol)
    if result[0] is None:
        return None
    
    price, rsi, bb_pos, momentum = result
    
    if rsi < MOMENTUM_RSI_MIN:
        return None
    
    # 动量买入信号
    return {
        'type': 'momentum_buy',
        'sym': symbol,
        'price': price,
        'change_24h': stats['change'],
        'rsi': rsi,
        'tp': 0.02,   # 2%
        'sl': MOMENTUM_SL  # 0.5%
    }

def scan_markets(symbols, prices, mode='all'):
    """扫描市场，返回所有信号"""
    signals = {'buy': [], 'sell': []}
    
    for sym in symbols:
        # 跳过黑名单
        from .config import BLACKLIST
        if sym in BLACKLIST:
            continue
        
        # 逆势信号
        sig = signal_strategy(sym, prices)
        if sig:
            if sig['type'] == 'oversold_buy':
                signals['buy'].append(sig)
            elif sig['type'] == 'overbought_sell':
                signals['sell'].append(sig)
        
        # 动量信号
        if mode in ['all', 'momentum']:
            mom = momentum_strategy(sym, prices)
            if mom:
                signals['buy'].append(mom)
    
    # 排序
    signals['buy'].sort(key=lambda x: -x.get('signal', 0))
    
    return signals
