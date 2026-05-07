#!/bin/bash
# 自主问题解决脚本 v1.1
# 发现问题 → 分析原因 → 自动修复 → 验证结果

LOG_FILE="/tmp/gg_auto_fixer.log"
exec >> $LOG_FILE 2>&1

echo "=========================================="
echo "🔧 自主问题解决 $(date)"
echo "=========================================="

python3 << 'INNER'
import requests, hmac, hashlib, time, json
from datetime import datetime

API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXIES = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

def log(msg):
    print(f"  {msg}")

def get_precision():
    log("获取Binance精度...")
    r = requests.get('https://api.binance.com/api/v3/exchangeInfo', proxies=PROXIES, timeout=10)
    p = {}
    for s in r.json()['symbols']:
        if s['symbol'].endswith('USDT'):
            for f in s['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    step = float(f['stepSize'])
                    p[s['symbol'].replace('USDT','')] = 0 if step >= 1 else len(str(step).split('.')[1].rstrip('0'))
    return p

def fix_hermes():
    log("检查并修复hermes_v54...")
    try:
        with open('/home/goose/.openclaw/workspace/scripts/hermes_v54.sh') as f:
            c = f.read()
        
        # 修复精度
        fixes = {"ETH":4}
        for coin, p in fixes.items():
            old = f"\'{coin}\':5,"
            new = f"\'{coin}\':{p},"
            if old in c:
                c = c.replace(old, new)
                log(f"  修复 {coin}: 5 -> {p}")
        
        with open('/home/goose/.openclaw/workspace/scripts/hermes_v54.sh', 'w') as f:
            f.write(c)
        return True
    except Exception as e:
        log(f"修复失败: {e}")
        return False

def analyze_failures():
    log("分析订单失败...")
    try:
        with open('/tmp/hermes_v54.log') as f:
            content = f.read()
        failures = [l for l in content.split('\n') if '❌' in l and 'Filter' in l]
        log(f"发现 {len(failures)} 个失败")
        return failures
    except:
        return []

def check_network():
    log("检查网络...")
    try:
        r = requests.get('https://api.binance.com/api/v3/ping', proxies=PROXIES, timeout=5)
        log("  ✅ Binance连接正常" if r.status_code == 200 else "  ❌ 连接失败")
        return r.status_code == 200
    except Exception as e:
        log(f"  ❌ {str(e)[:40]}")
        return False

def check_funds():
    log("检查资金状态...")
    try:
        ts = int(time.time()*1000)
        params = f'timestamp={ts}&recvWindow=5000'
        sig = hmac.new(API_SECRET.encode(), params.encode(), hashlib.sha256).hexdigest()
        
        r = requests.get(f'https://api.binance.com/api/v3/account?{params}&signature={sig}', headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
        spot_usdt = float([b for b in r.json()['balances'] if b['asset']=='USDT'][0]['free'])
        
        r = requests.get(f'https://api.binance.com/sapi/v1/margin/account?{params}&signature={sig}', headers={'X-MBX-APIKEY':API_KEY}, proxies=PROXIES, timeout=10)
        cross_usdt = float([a for a in r.json()['userAssets'] if a['asset']=='USDT'][0]['free'])
        
        log(f"  SPOT: ${spot_usdt:.2f}, CROSS: ${cross_usdt:.2f}")
        
        if spot_usdt > 200 and cross_usdt < 50:
            log(f"  💡 建议转账 SPOT->CROSS")
        
        return True
    except Exception as e:
        log(f"  检查失败: {e}")
        return False

# 主程序
print("\n🔍 自主诊断:")
check_network()
analyze_failures()
fix_hermes()
check_funds()
print("\n✅ 自主问题解决完成")
INNER
