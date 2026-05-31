#!/usr/bin/env python3
"""
OPC Trader - One Powerful Core Trader
整合系统主程序
"""
import sys, os, time, signal, math
sys.path.insert(0, '/home/goose/.openclaw/workspace/opc')

from core import (
    get_prices, get_all_balances, get_market_signal,
    scan_markets, execute_buy, execute_sell,
    save_trade, analyze_performance, log_learning,
    TRADE_BUDGET, MAX_POSITIONS, COOLDOWN, MAX_HOLD_TIME,
    SCAN_COINS, BLACKLIST, TP_RATE, SL_RATE, MOMENTUM_ENABLED
)

LOG_FILE = '/home/goose/.openclaw/workspace/opc/logs/opc.log'
os.makedirs('/home/goose/.openclaw/workspace/opc/logs', exist_ok=True)

def log(msg):
    ts = time.strftime('%m-%d %H:%M:%S')
    line = f'[{ts}] {msg}'
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

class OPCTader:
    def __init__(self):
        self.running = True
        self.positions = {}  # {sym: {'qty', 'entry', 'entry_time', 'tp', 'sl', 'source'}}
        self.last_trade_time = 0
        self.daily_trades = 0
        self.trade_stats = {'buy': 0, 'sell': 0, 'tp': 0, 'sl': 0}
        signal.signal(signal.SIGTERM, lambda s,f: self.shutdown())
        signal.signal(signal.SIGINT, lambda s,f: self.shutdown())
    
    def shutdown(self):
        log('OPC shutting down...')
        self.running = False
    
    def get_holdings(self):
        """获取持仓"""
        balances = get_all_balances()
        holdings = {}
        prices = get_prices(SCAN_COINS)
        usdt = 0.0
        
        for sym, bal in balances.items():
            if sym == 'USDT':
                usdt = bal['free']
                continue
            if sym not in SCAN_COINS:
                continue
            price = prices.get(sym, 0)
            if price > 0 and bal['free'] > 0:
                value = bal['free'] * price
                if value > 1:
                    holdings[sym] = {'qty': bal['free'], 'value': value, 'price': price}
        
        return holdings, usdt, prices
    
    def check_positions(self):
        """检查持仓状态"""
        for sym in list(self.positions.keys()):
            pos = self.positions[sym]
            price_data = get_market_signal(sym)
            if price_data[0] is None:
                continue
            
            current_price, rsi, bb_pos, momentum = price_data
            hold_time = time.time() - pos['entry_time']
            
            pnl_pct = (current_price - pos['entry']) / pos['entry']
            
            # 检查止损/止盈
            exit_reason = None
            if pnl_pct >= pos.get('tp_rate', TP_RATE):
                exit_reason = f'TP {pnl_pct*100:.2f}%'
                self.trade_stats['tp'] += 1
            elif pnl_pct <= -pos.get('sl_rate', SL_RATE):
                exit_reason = f'SL {pnl_pct*100:.2f}%'
                self.trade_stats['sl'] += 1
            elif hold_time > MAX_HOLD_TIME:
                exit_reason = f'超时 {hold_time:.0f}s'
            elif rsi > 70 or bb_pos > 0.85:
                exit_reason = f'RSI/BB超买'
            
            if exit_reason:
                log(f'🚪 {sym} 退出: {exit_reason} ({(pnl_pct)*100:+.2f}%)')
                result = execute_sell(sym, pos['qty'])
                if result['success']:
                    self.trade_stats['sell'] += 1
                    save_trade({
                        'sym': sym,
                        'type': 'sell',
                        'pnl_pct': pnl_pct,
                        'reason': exit_reason,
                        'hold_time': hold_time
                    })
                del self.positions[sym]
    
    def run(self):
        """主循环"""
        log('='*50)
        log('OPC Trader - One Powerful Core')
        log(f'Momentum: {MOMENTUM_ENABLED} | TP: {TP_RATE*100}% | SL: {SL_RATE*100}%')
        log('='*50)
        
        cycle = 0
        while self.running:
            cycle += 1
            
            try:
                # 获取数据
                holdings, usdt, prices = self.get_holdings()
                total_value = usdt + sum(h.get('value', 0) for h in holdings.values() if isinstance(h, dict))
                
                log(f'')
                log(f'=== OPC周期{cycle} | 总资产:${total_value:.2f} | USDT:${usdt:.2f} | 持仓:{len(self.positions)} ===')
                
                # 检查持仓
                self.check_positions()
                
                # 冷却检查
                if time.time() - self.last_trade_time < COOLDOWN:
                    time.sleep(5)
                    continue
                
                # 扫描信号
                signals = scan_markets(SCAN_COINS, prices, mode='all' if MOMENTUM_ENABLED else 'signal')
                
                if signals['buy']:
                    # 执行买入
                    for sig in signals['buy'][:2]:  # 最多2个
                        sym = sig['sym']
                        if sym in self.positions:
                            continue
                        if len(self.positions) >= MAX_POSITIONS:
                            log(f'⚠️ 满仓')
                            break
                        if usdt < TRADE_BUDGET:
                            log(f'⚠️ USDT不足')
                            break
                        
                        budget = min(TRADE_BUDGET, usdt * 0.9)
                        
                        if sig['type'] == 'momentum_buy':
                            log(f'🚀 动量买入 {sym} {sig.get("change_24h",0):+.1f}% RSI={sig["rsi"]:.0f}')
                            tp = sig.get('tp', 0.02)
                            sl = sig.get('sl', 0.005)
                        else:
                            log(f'📥 超卖买入 {sym} RSI={sig["rsi"]:.0f} BB={sig["bb"]:.2f}')
                            tp = TP_RATE
                            sl = SL_RATE
                        
                        result = execute_buy(sym, budget, sig['price'], tp, sl)
                        if result['success']:
                            self.positions[sym] = {
                                'qty': result['qty'],
                                'entry': result['price'],
                                'entry_time': result['entry_time'],
                                'tp': result['tp'],
                                'sl': result['sl'],
                                'tp_rate': tp,
                                'sl_rate': sl,
                                'source': sig['type']
                            }
                            self.last_trade_time = time.time()
                            self.trade_stats['buy'] += 1
                            usdt -= budget
                            log(f'  ✅ {sym} 买入成功 @ ${result["price"]:.4f}')
                
                # 显示状态
                if self.positions:
                    for sym, pos in self.positions.items():
                        hold_time = time.time() - pos['entry_time']
                        log(f'  💼 {sym} | 持仓{int(hold_time)}s')
                
                # 每20周期报告统计
                if cycle % 20 == 0:
                    log(f'📊 统计: 买{self.trade_stats["buy"]} 卖{self.trade_stats["sell"]} 止盈{self.trade_stats["tp"]} 止损{self.trade_stats["sl"]}')
                    perf = analyze_performance()
                    if perf['total'] > 0:
                        log(f'📈 胜率: {perf["win_rate"]:.1f}% | 平均PnL: {perf["avg_pnl"]:.2f}%')
                
            except Exception as e:
                log(f'异常: {str(e)[:80]}')
                time.sleep(5)
            
            # 等待
            for _ in range(10):
                if not self.running:
                    break
                time.sleep(1)
        
        log(f'OPC停止 - {self.trade_stats}')

if __name__ == '__main__':
    trader = OPCTader()
    trader.run()
