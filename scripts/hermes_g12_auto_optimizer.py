#!/usr/bin/env python3
"""
Hermes G12 - 自主优化持续迭代系统
自动监测 → 智能诊断 → 参数调优 → 策略切换 → 持续进化
"""
import requests, time, json, numpy as np
from datetime import datetime
from collections import deque

PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}
COINS = ['BTC','ETH','SOL','XRP','ADA','DOGE','LINK']

# ========== 核心配置 ==========
CONFIG = {
    'version': 'G12-AutoOptimizer-v1.0',
    # G12最优参数
    'rsi_buy': 43, 'rsi_sell': 53,
    'bb_buy': 25, 'bb_sell': 75,
    'take_profit': 0.08, 'stop_loss': 0.035,
    'position': 0.35, 'leverage': 3,
    'short_rsi': 70, 'short_bb': 85,
    'decision_threshold': 0.70,
    'rsi_period': 7,
}

# ========== 迭代历史 ==========
ITERATION_LOG = '/tmp/g12_iteration_log.json'

# ========== 指标计算 ==========
def get_klines(sym, interval='1h', limit=720):
    end = int(time.time()*1000)
    start = end - limit * 3600 * 1000
    url = f'https://api.binance.com/api/v3/klines?symbol={sym}&interval={interval}&startTime={start}&endTime={end}&limit={limit}'
    try:
        r = requests.get(url, proxies=PROXIES, timeout=30)
        return [{'close':float(k[4]),'high':float(k[2]),'low':float(k[3])} for k in r.json()]
    except: return []

def get_rsi(prices, period=7):
    if len(prices) < period+1: return 50
    deltas = np.diff(prices)
    gain = np.where(deltas>0, deltas, 0)
    loss = np.where(deltas<0, -deltas, 0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    return 100-(100/(1+avg_gain/avg_loss)) if avg_loss!=0 else 100

def bollinger_pos(price, highs, lows, period=20):
    if len(highs) < period: return 50
    bb_high = np.mean(highs[-period:]) + 2*np.std(highs[-period:])
    bb_low = np.mean(lows[-period:]) - 2*np.std(lows[-period:])
    return (price - bb_low) / (bb_high - bb_low) * 100 if bb_high > bb_low else 50

def get_macd(prices):
    if len(prices) < 26: return 0
    return np.mean(prices[-12:]) - np.mean(prices[-26:])

# ========== 市场状态检测 ==========
def detect_market_regime(price_data):
    """检测市场状态: 趋势/震荡/高波动"""
    regimes = {}
    for c in COINS:
        if c not in price_data or len(price_data[c]) < 100:
            regimes[c] = 'unknown'
            continue
        
        closes = [k['close'] for k in price_data[c][-100:]]
        highs = [k['high'] for k in price_data[c][-100:]]
        lows = [k['low'] for k in price_data[c][-100:]]
        
        # 波动率
        volatility = np.std(closes[-30:]) / np.mean(closes[-30:]) * 100
        
        # 趋势 (简单移动平均)
        sma_20 = np.mean(closes[-20:])
        sma_50 = np.mean(closes[-50:])
        trend = 'up' if sma_20 > sma_50 else 'down'
        
        # 市场状态
        if volatility > 5:
            regime = 'high_volatility'
        elif abs(closes[-1] - closes[0]) / closes[0] > 0.1:
            regime = trend
        else:
            regime = 'sideways'
        
        regimes[c] = regime
    
    return regimes

# ========== 模拟交易 ==========
def simulate_trade(initial_capital, price_data, cfg):
    valid_coins = [c for c in COINS if c in price_data and len(price_data[c]) > 100]
    if not valid_coins: return None
    min_days = min(len(price_data[c]) for c in valid_coins)
    
    capital = initial_capital
    positions = {c: 0 for c in valid_coins}
    entry_prices = {c: 0 for c in valid_coins}
    short_qtys = {c: 0 for c in valid_coins}
    short_entries = {c: 0 for c in valid_coins}
    trades = []
    equity_curve = [initial_capital]
    
    leverage = cfg.get('leverage', 3)
    position_ratio = cfg.get('position', 0.35)
    
    for day_idx in range(min_days):
        day_data = {c: price_data[c][day_idx] for c in valid_coins}
        
        for c in valid_coins:
            d = day_data[c]
            highs = [price_data[c][i]['high'] for i in range(max(0, day_idx-19), day_idx+1)]
            lows = [price_data[c][i]['low'] for i in range(max(0, day_idx-19), day_idx+1)]
            closes = [price_data[c][i]['close'] for i in range(max(0, day_idx-14), day_idx+1)]
            
            rsi = get_rsi(closes, cfg.get('rsi_period', 7))
            bb_pos = bollinger_pos(d['close'], highs, lows, 20)
            macd = get_macd(closes)
            
            decision = 0.30 * (50 - min(rsi, 50)) / 50
            decision += 0.25 * (100 - bb_pos) / 100
            decision += 0.20 * min(macd / (d['close'] * 0.005), 1)
            
            # 做多
            if (rsi < cfg.get('rsi_buy', 43) and bb_pos < cfg.get('bb_buy', 25) and
                decision > cfg.get('decision_threshold', 0.70) and
                capital > 10 and positions[c] == 0 and short_qtys[c] == 0):
                invest = capital * position_ratio * leverage
                qty = invest / d['close']
                capital -= invest * 0.001
                positions[c] = qty
                entry_prices[c] = d['close']
                trades.append({'type':'LONG_OPEN','coin':c})
            
            # 平多
            if positions[c] > 0:
                pnl_ratio = (d['close'] - entry_prices[c]) / entry_prices[c] * leverage
                sell = (rsi > cfg.get('rsi_sell', 53) and bb_pos > cfg.get('bb_sell', 75))
                sell = sell or pnl_ratio >= cfg.get('take_profit', 0.08) or pnl_ratio <= -cfg.get('stop_loss', 0.035)
                
                if sell:
                    pnl = (d['close'] - entry_prices[c]) * positions[c] * leverage
                    capital += pnl - positions[c] * d['close'] * 0.001
                    positions[c] = 0
                    entry_prices[c] = 0
                    trades.append({'type':'LONG_CLOSE','coin':c,'pnl_ratio':pnl_ratio})
            
            # 做空
            if (rsi > cfg.get('short_rsi', 70) and bb_pos > cfg.get('short_bb', 85) and
                capital > 20 and short_qtys[c] == 0 and positions[c] == 0):
                qty = (capital * position_ratio * leverage) / d['close']
                capital -= qty * d['close'] * 0.001
                short_qtys[c] = qty
                short_entries[c] = d['close']
                trades.append({'type':'SHORT_OPEN','coin':c})
            
            # 平空
            if short_qtys[c] > 0:
                pnl_ratio = (short_entries[c] - d['close']) / short_entries[c] * leverage
                cover = (rsi < cfg.get('rsi_buy', 43) or bb_pos < cfg.get('bb_buy', 25))
                cover = cover or pnl_ratio >= cfg.get('take_profit', 0.08) or pnl_ratio <= -cfg.get('stop_loss', 0.035)
                
                if cover:
                    pnl = (short_entries[c] - d['close']) * short_qtys[c] * leverage
                    capital += pnl - short_qtys[c] * d['close'] * 0.001
                    short_qtys[c] = 0
                    short_entries[c] = 0
                    trades.append({'type':'SHORT_CLOSE','coin':c,'pnl_ratio':pnl_ratio})
        
        # 权益记录
        day_value = capital
        for c in valid_coins:
            day_value += positions[c] * day_data[c]['close']
            day_value += short_qtys[c] * (short_entries[c] - day_data[c]['close'])
        equity_curve.append(day_value)
    
    # 统计
    closed = [t for t in trades if t['type'] in ['LONG_CLOSE','SHORT_CLOSE']]
    wins = sum(1 for t in closed if t.get('pnl_ratio', 0) > 0)
    win_rate = wins / len(closed) * 100 if closed else 0
    
    peak = initial_capital
    max_dd = 0
    for v in equity_curve:
        peak = max(peak, v)
        max_dd = max(max_dd, (peak - v) / peak * 100)
    
    return {
        'return': (equity_curve[-1] - initial_capital) / initial_capital * 100,
        'win_rate': win_rate,
        'trades': len(trades),
        'max_drawdown': max_dd,
        'equity_curve': equity_curve[-30:]  # 最近30天
    }

# ========== 参数优化器 ==========
class G12AutoOptimizer:
    def __init__(self):
        self.current_config = CONFIG.copy()
        self.best_config = CONFIG.copy()
        self.best_return = 0
        self.iteration_count = 0
        self.history = []
        self.performance_window = deque(maxlen=10)  # 最近10次表现
        
    def load_history(self):
        try:
            with open(ITERATION_LOG, 'r') as f:
                data = json.load(f)
                self.history = data.get('history', [])
                self.best_config = data.get('best_config', CONFIG)
                self.best_return = data.get('best_return', 0)
                self.iteration_count = len(self.history)
        except: pass
    
    def save_history(self):
        data = {
            'history': self.history[-100:],  # 保留最近100条
            'best_config': self.best_config,
            'best_return': self.best_return,
            'last_update': datetime.now().isoformat()
        }
        with open(ITERATION_LOG, 'w') as f:
            json.dump(data, f, indent=2)
    
    def evaluate_config(self, price_data, cfg):
        """评估配置表现"""
        stats = simulate_trade(1000, price_data, cfg)
        if not stats:
            return {'score': 0, 'return': 0, 'risk_adjusted': 0}
        
        # 风险调整收益 (夏普比替代)
        returns = np.diff(stats['equity_curve']) / stats['equity_curve'][:-1]
        sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        
        # 综合评分
        score = stats['return'] * 0.6 + stats['win_rate'] * 0.2 + sharpe * 10 * 0.2
        score -= stats['max_drawdown'] * 0.5  # 回撤惩罚
        
        return {
            'return': stats['return'],
            'win_rate': stats['win_rate'],
            'max_drawdown': stats['max_drawdown'],
            'sharpe': sharpe,
            'score': score
        }
    
    def generate_variations(self, base_cfg):
        """生成参数变体"""
        variations = []
        
        # RSI变体
        for rsi_buy in [38, 40, 43, 45, 48]:
            for rsi_sell in [52, 55, 58, 60, 63]:
                if rsi_buy >= rsi_sell: continue
                cfg = base_cfg.copy()
                cfg['rsi_buy'] = rsi_buy
                cfg['rsi_sell'] = rsi_sell
                cfg['name'] = f"RSI{rsi_buy}/{rsi_sell}"
                variations.append(cfg)
        
        # 布林变体
        for bb_buy in [20, 25, 30]:
            for bb_sell in [70, 75, 80]:
                if bb_buy >= bb_sell: continue
                cfg = base_cfg.copy()
                cfg['bb_buy'] = bb_buy
                cfg['bb_sell'] = bb_sell
                cfg['name'] = f"BB{bb_buy}/{bb_sell}"
                variations.append(cfg)
        
        # 止盈止损变体
        for tp in [0.06, 0.08, 0.10]:
            for sl in [0.03, 0.035, 0.04]:
                if tp <= sl: continue
                cfg = base_cfg.copy()
                cfg['take_profit'] = tp
                cfg['stop_loss'] = sl
                cfg['name'] = f"TP{int(tp*100)}SL{int(sl*100)}"
                variations.append(cfg)
        
        # 仓位变体
        for pos in [0.25, 0.30, 0.35, 0.40]:
            cfg = base_cfg.copy()
            cfg['position'] = pos
            cfg['name'] = f"Pos{int(pos*100)}"
            variations.append(cfg)
        
        return variations[:50]  # 限制数量
    
    def optimize(self, price_data, market_regime):
        """执行优化"""
        self.iteration_count += 1
        print(f"\n{'='*70}")
        print(f"【第{self.iteration_count}次迭代】市场状态: {market_regime}")
        print(f"{'='*70}")
        
        # 评估当前配置
        current_score = self.evaluate_config(price_data, self.current_config)
        print(f"\n📊 当前配置评分: {current_score['score']:.2f}")
        print(f"   收益: {current_score['return']:+.2f}% | 胜率: {current_score['win_rate']:.1f}% | 回撤: {current_score['max_drawdown']:.1f}%")
        
        # 记录表现
        self.performance_window.append(current_score['return'])
        
        # 生成并测试变体
        print(f"\n🔍 测试参数变体...")
        variations = self.generate_variations(self.current_config)
        
        best_var = None
        best_var_score = current_score['score']
        
        for i, cfg in enumerate(variations[:30]):
            score = self.evaluate_config(price_data, cfg)
            cfg['eval'] = score
            
            if score['score'] > best_var_score:
                best_var_score = score['score']
                best_var = cfg
                print(f"  🆕 新最优: {cfg.get('name','?')} → 收益:{score['return']:+.2f}% 评分:{score['score']:.2f}")
        
        # 更新配置
        if best_var:
            improvement = best_var['eval']['return'] - current_score['return']
            self.current_config = {k:v for k,v in best_var.items() if k != 'eval' and k != 'name'}
            self.current_config['name'] = best_var.get('name', f"iter{self.iteration_count}")
            
            print(f"\n✅ 配置更新: {best_var.get('name','?')}")
            print(f"   收益改进: {improvement:+.2f}%")
            print(f"   新参数: RSI:{self.current_config['rsi_buy']}/{self.current_config['rsi_sell']} BB:{self.current_config['bb_buy']}/{self.current_config['bb_sell']}")
            
            # 更新历史
            self.history.append({
                'iteration': self.iteration_count,
                'timestamp': datetime.now().isoformat(),
                'config': self.current_config.copy(),
                'score': best_var['eval'],
                'market_regime': market_regime,
                'improvement': improvement
            })
            
            # 更新最优
            if best_var['eval']['return'] > self.best_return:
                self.best_return = best_var['eval']['return']
                self.best_config = self.current_config.copy()
                print(f"🏆 新历史最优: {self.best_return:.2f}%")
        else:
            print(f"\n⚠️ 未找到更优配置,保持当前设置")
        
        self.save_history()
        return self.current_config

# ========== 主程序 ==========
def main():
    print("="*70)
    print("Hermes G12 - 自主优化持续迭代系统")
    print("="*70)
    
    # 获取数据
    print("\n📥 获取市场数据...")
    price_data = {}
    for c in COINS:
        data = get_klines(f'{c}USDT', '1h', 720)
        if data and len(data) > 100:
            price_data[c] = data
            print(f"  {c}: {len(data)}条")
        time.sleep(0.1)
    
    if len(price_data) < 3:
        print("❌ 数据不足")
        return
    
    # 检测市场状态
    print("\n🔍 检测市场状态...")
    regime = detect_market_regime(price_data)
    dominant_regime = max(set(regime.values()), key=list(regime.values()).count)
    print(f"  市场状态: {dominant_regime}")
    for c, r in regime.items():
        print(f"    {c}: {r}")
    
    # 初始化优化器
    optimizer = G12AutoOptimizer()
    optimizer.load_history()
    
    print(f"\n📈 历史迭代: {optimizer.iteration_count}次")
    print(f"🏆 历史最优: {optimizer.best_return:.2f}%")
    
    # 执行优化
    new_config = optimizer.optimize(price_data, dominant_regime)
    
    # 显示结果
    print("\n" + "="*70)
    print("【优化结果】")
    print("="*70)
    print(f"\n📋 当前最优配置:")
    print(f"  RSI: {new_config['rsi_buy']}/{new_config['rsi_sell']}")
    print(f"  布林: {new_config['bb_buy']}/{new_config['bb_sell']}")
    print(f"  止盈: {new_config['take_profit']*100:.0f}% | 止损: {new_config['stop_loss']*100:.1f}%")
    print(f"  仓位: {new_config['position']*100:.0f}% | 杠杆: {new_config['leverage']}x")
    
    # 评估最终表现
    final_eval = optimizer.evaluate_config(price_data, new_config)
    print(f"\n📊 预期表现:")
    print(f"  收益: {final_eval['return']:+.2f}%")
    print(f"  胜率: {final_eval['win_rate']:.1f}%")
    print(f"  最大回撤: {final_eval['max_drawdown']:.1f}%")
    
    print("\n" + "="*70)
    print(f"✅ 迭代完成! 第{optimizer.iteration_count}次 → 评分:{final_eval['score']:.2f}")
    print("="*70)

if __name__ == '__main__':
    main()
