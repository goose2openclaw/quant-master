#!/bin/bash
# GG Polymarket 热门预测抓取脚本 v1.3
# 功能: 使用Brave Search获取Polymarket热门预测
# 日期: 2026-05-05

LOG_DIR="/tmp/gg_polymarket"
mkdir -p $LOG_DIR
LOG_FILE="$LOG_DIR/scraper.log"

log() {
    echo "[$(date '+%H:%M:%S')] $1"
}

fetch_polymarket() {
    python3 << 'PYEOF'
import requests, json
from datetime import datetime

LOG_FILE = "/tmp/gg_polymarket/scraper.log"

def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"[{ts}] {msg}")

log("使用 Brave Search 获取 Polymarket 热门...")

# Brave Search API (如果有BRAVE_API_KEY环境变量)
brave_key = None
try:
    with open('/tmp/brave_api_key.txt', 'r') as f:
        brave_key = f.read().strip()
except: pass

markets = []

if brave_key:
    try:
        headers = {'X-Subscription-Token': brave_key}
        params = {'q': 'polymarket trending market prediction site:polymarket.com', 'count': 10}
        r = requests.get('https://api.search.brave.com/res/v1/search', 
                         headers=headers, params=params, timeout=10)
        log(f"Brave Search: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            for item in data.get('web', {}).get('results', [])[:10]:
                markets.append({
                    'title': item.get('title', '')[:80],
                    'url': item.get('url', ''),
                    'description': item.get('description', '')[:200]
                })
    except Exception as e:
        log(f"Brave Search失败: {e}")
else:
    # 使用curl via subprocess
    import subprocess
    try:
        result = subprocess.run([
            'curl', '-s', '-G', '--data-urlencode', 
            'q=polymarket trending market prediction',
            'https://html.duckduckgo.com/html/'
        ], capture_output=True, text=True, timeout=10)
        
        if 'polymarket' in result.stdout.lower():
            log("DuckDuckGo: 获取到结果")
            for line in result.stdout.split('\n'):
                if 'polymarket' in line.lower() and len(line.strip()) > 20:
                    import re
                    titles = re.findall(r'<a[^>]*>([^<]+)</a>', line)
                    for t in titles:
                        if 'polymarket' in t.lower():
                            markets.append({
                                'title': t.strip()[:80],
                                'url': '',
                                'description': ''
                            })
                            break
    except Exception as e:
        log(f"DuckDuckGo失败: {e}")

# 输出结果
log("\n" + "="*60)
log("📊 Polymarket 热门预测")
log("="*60)

if markets:
    for i, m in enumerate(markets[:5], 1):
        log(f"\n{i}. {m.get('title', 'N/A')}")
        if m.get('description'):
            log(f"   {m['description'][:100]}")
        if m.get('url'):
            log(f"   {m['url'][:60]}")
    
    result = {
        'timestamp': datetime.now().isoformat(),
        'markets': markets[:10]
    }
    with open('/tmp/gg_polymarket_trending.json', 'w') as f:
        json.dump(result, f, indent=2)
    log(f"\n✅ 保存了 {len(markets)} 个结果")
else:
    log("\n⚠️ 暂无可用数据")
    log("建议: 手动访问 polymarket.com 查看热门预测")
    result = {
        'timestamp': datetime.now().isoformat(),
        'error': 'No data - network restrictions',
        'manual_url': 'https://polymarket.com'
    }
    with open('/tmp/gg_polymarket_trending.json', 'w') as f:
        json.dump(result, f, indent=2)

log("\n✅ 完成")
print()
PYEOF
}

log "=========================================="
log "🚀 Polymarket 抓取 v1.3 (Brave Search)"
log "=========================================="

fetch_polymarket
