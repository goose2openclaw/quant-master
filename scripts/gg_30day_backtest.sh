#!/bin/bash
LOG_FILE="/tmp/gg_30day_backtest.log"
exec >> $LOG_FILE 2>&1
echo "=========================================="
echo "GO2SE Genius 30天回测系统 $(date)"
echo "=========================================="

python3 << 'PYEOF'
import requests, random

API_KEY='QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET='BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES={'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

COINS=['BTC','ETH','BNB','SOL','XRP','ADA','DOGE','LINK']
N_AGENTS=1000
INITIAL_CAPITAL=1000

NORMAL={'name':'NORMAL','rsi_short':75,'rsi_long':30,'wr_short':0.90,'wr_long':0.86,'tp':0.12,'sl':0.015,'position':0.20,'leverage':5,'proactivity':0.50}
EXPERT={'name':'EXPERT','rsi_short':71,'rsi_long':32,'wr_short':0.93,'wr_long':0.89,'tp':0.08,'sl':0.015,'position':0.25,'leverage':5,'proactivity':0.90}

def get_price(sym):
    try:
        r=requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={sym}', proxies=PROXIES, timeout=5)
        return float(r.json()['price'])
    except: return 0

def get_klines(symbol, interval='1h', limit=720):
    try:
        r=requests.get(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}', proxies=PROXIES, timeout=10)
        return [(float(d[2]),float(d[3]),float(d[4])) for d in r.json()]
    except: return None

def calc_rsi(closes, period=14):
    if len(closes)<2: return 50
    deltas=[closes[i]-closes[i-1] for i in range(1,len(closes))]
    gains=[d if d>0 else 0 for d in deltas]
    losses=[-d if d<0 else 0 for d in deltas]
    avg_gain=sum(gains[-period:])/period if len(gains)>=period else sum(gains)/len(gains)
    avg_loss=sum(losses[-period:])/period if len(losses)>=period else sum(losses)/len(losses)
    rs=avg_gain/(avg_loss+0.0001)
    return 100-(100/(1+rs))

def get_prices(coin, days=35):
    klines=get_klines(f'{coin}USDT','1h',min(days*24,720))
    return [k[0] for k in klines] if klines else []

def simulate(config, prices):
    capital=INITIAL_CAPITAL; position=0; entry=0; wins=0; losses=0
    for i in range(len(prices)):
        price=prices[i]
        if position==0:
            if random.random()<config['proactivity']:
                rsi=calc_rsi(prices[max(0,i-14):i]) if i>=14 else 50
                if rsi<config['rsi_long'] and random.random()<config['wr_long']:
                    size=capital*config['position']*config['leverage']
                    position=size/price
                    entry=price
                    capital-=size*0.001
        elif position>0:
            pnl=(price-entry)/entry
            if pnl>=config['tp'] or pnl<=-config['sl']:
                proceeds=position*price
                capital=proceeds-proceeds*0.001
                if pnl>=config['tp']: wins+=1
                else: losses+=1
                position=0
    if position>0: capital=position*prices[-1]
    total=wins+losses
    return {'return':(capital-INITIAL_CAPITAL)/INITIAL_CAPITAL*100,'win_rate':wins/total*100 if total>0 else 0,'trades':total}

print("\n"+"="*60)
print("GO2SE Genius 30天回测 - Normal vs Expert")
print("="*60)

print("\n获取历史数据...")
coin_prices={}
for coin in COINS:
    p=get_prices(coin,35)
    coin_prices[coin]=p
    print(f"  {coin}: {len(p)}条")

# 回测
normal_results=[]; expert_results=[]
for coin in COINS:
    prices=coin_prices.get(coin,[])
    if not prices: prices=[100+random.gauss(0,2)+i*0.1 for i in range(720)]
    
    n_results=[]; e_results=[]
    for _ in range(N_AGENTS):
        n_results.append(simulate(NORMAL,prices))
        e_results.append(simulate(EXPERT,prices))
    
    normal_results.append({
        'coin':coin,
        'return':sum(r['return'] for r in n_results)/N_AGENTS,
        'win_rate':sum(r['win_rate'] for r in n_results)/N_AGENTS,
        'trades':sum(r['trades'] for r in n_results)/N_AGENTS,
    })
    expert_results.append({
        'coin':coin,
        'return':sum(r['return'] for r in e_results)/N_AGENTS,
        'win_rate':sum(r['win_rate'] for r in e_results)/N_AGENTS,
        'trades':sum(r['trades'] for r in e_results)/N_AGENTS,
    })

# 汇总
n_avg_return=sum(r['return'] for r in normal_results)/len(normal_results)
n_avg_wr=sum(r['win_rate'] for r in normal_results)/len(normal_results)
n_avg_trades=sum(r['trades'] for r in normal_results)/len(normal_results)
n_capital_util=NORMAL['position']*NORMAL['leverage']*(n_avg_wr/100)

e_avg_return=sum(r['return'] for r in expert_results)/len(expert_results)
e_avg_wr=sum(r['win_rate'] for r in expert_results)/len(expert_results)
e_avg_trades=sum(r['trades'] for r in expert_results)/len(expert_results)
e_capital_util=EXPERT['position']*EXPERT['leverage']*(e_avg_wr/100)

# 打印结果
print("\n"+"="*60)
print("NORMAL模式")
print("="*60)
print(f"  RSI: {NORMAL['rsi_short']}/{NORMAL['rsi_long']}")
print(f"  TP/SL: {NORMAL['tp']*100:.0f}%/{NORMAL['sl']*100:.1f}%")
print(f"  WR: {NORMAL['wr_short']*100:.0f}%/{NORMAL['wr_long']*100:.0f}%")
print(f"  仓位: {NORMAL['position']*100:.0f}%  杠杆: {NORMAL['leverage']}x  主动性: {NORMAL['proactivity']*100:.0f}%")
print(f"  30天收益: {n_avg_return:+.1f}%")
print(f"  平均胜率: {n_avg_wr:.1f}%")
print(f"  平均交易: {n_avg_trades:.1f}次")
print(f"  资金利用率: {n_capital_util:.2f}")

print("\n"+"="*60)
print("EXPERT模式")
print("="*60)
print(f"  RSI: {EXPERT['rsi_short']}/{EXPERT['rsi_long']}")
print(f"  TP/SL: {EXPERT['tp']*100:.0f}%/{EXPERT['sl']*100:.1f}%")
print(f"  WR: {EXPERT['wr_short']*100:.0f}%/{EXPERT['wr_long']*100:.0f}%")
print(f"  仓位: {EXPERT['position']*100:.0f}%  杠杆: {EXPERT['leverage']}x  主动性: {EXPERT['proactivity']*100:.0f}%")
print(f"  30天收益: {e_avg_return:+.1f}%")
print(f"  平均胜率: {e_avg_wr:.1f}%")
print(f"  平均交易: {e_avg_trades:.1f}次")
print(f"  资金利用率: {e_capital_util:.2f}")

print("\n"+"="*60)
print("对比分析")
print("="*60)
print(f"  收益: {n_avg_return:+.1f}% vs {e_avg_return:+.1f}%")
print(f"  胜率: {n_avg_wr:.1f}% vs {e_avg_wr:.1f}%")
print(f"  交易次数: {n_avg_trades:.1f} vs {e_avg_trades:.1f}")
print(f"  资金利用率: {n_capital_util:.2f} vs {e_capital_util:.2f}")

print("\n"+"="*60)
print("推荐模式")
print("="*60)
if e_avg_return>n_avg_return:
    print(f"  推荐: EXPERT (收益更高: {e_avg_return:+.1f}%)")
else:
    print(f"  推荐: NORMAL (收益更高: {n_avg_return:+.1f}%)")
if e_avg_wr>n_avg_wr:
    print(f"  EXPERT胜率更优")
else:
    print(f"  NORMAL胜率更优")
if e_capital_util>n_capital_util:
    print(f"  EXPERT资金效率更优")
else:
    print(f"  NORMAL资金效率更优")

print("\n优化建议:")
sug=[]
if NORMAL['proactivity']<0.70: sug.append("  • NORMAL主动性50%->70%")
if EXPERT['proactivity']>0.95: sug.append("  • EXPERT主动性90%可能过度交易")
if NORMAL['tp']>0.10: sug.append("  • NORMAL TP12%->8-10%")
if sug: [print(x) for x in sug]
else: print("  ✅ 配置已较优")

print("\n"+"="*60)
print("回测完成")
print("="*60)
PYEOF
