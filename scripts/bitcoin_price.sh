#!/bin/bash

# 比特币价格查询脚本
# 响应语音指令"比特币现在的价钱是多少"

echo "=== 比特币价格查询 ==="
echo "查询时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 使用CoinGecko API获取比特币价格
API_URL="https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd,cny&include_24hr_change=true"

echo "🔍 从CoinGecko获取实时数据..."
RESPONSE=$(curl -s "$API_URL")

# 检查API响应
if [ -z "$RESPONSE" ]; then
    echo "❌ 无法获取比特币价格数据"
    echo "请检查网络连接或稍后重试"
    exit 1
fi

# 解析JSON数据
USD_PRICE=$(echo "$RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(data['bitcoin']['usd'])
except:
    print('N/A')
")

CNY_PRICE=$(echo "$RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(data['bitcoin']['cny'])
except:
    print('N/A')
")

CHANGE_24H=$(echo "$RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    change = data['bitcoin']['usd_24h_change']
    print(f'{change:.2f}')
except:
    print('N/A')
")

echo ""
echo "📊 比特币实时价格:"
echo "========================"
echo "💰 美元价格: \$$USD_PRICE"
echo "💰 人民币价格: ¥$CNY_PRICE"
echo "📈 24小时变化: $CHANGE_24H%"

# 判断涨跌趋势
if [[ "$CHANGE_24H" != "N/A" ]]; then
    if (( $(echo "$CHANGE_24H > 0" | bc -l 2>/dev/null || echo "0") )); then
        echo "📈 趋势: 上涨 (绿色)"
        EMOJI="🟢"
    elif (( $(echo "$CHANGE_24H < 0" | bc -l 2>/dev/null || echo "0") )); then
        echo "📉 趋势: 下跌 (红色)"
        EMOJI="🔴"
    else
        echo "➡️ 趋势: 持平"
        EMOJI="🟡"
    fi
fi

echo "========================"
echo ""

# 显示价格换算
echo "💱 价格换算:"
echo "  1 BTC = \$$USD_PRICE"
echo "  1 BTC = ¥$CNY_PRICE"
echo "  1 USD ≈ ¥$(echo "scale=2; $CNY_PRICE / $USD_PRICE" | bc 2>/dev/null || echo "N/A")"

echo ""
echo "📅 数据更新时间: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "🌐 数据来源: CoinGecko API"
echo ""

# 简单建议
if [[ "$CHANGE_24H" != "N/A" ]]; then
    ABS_CHANGE=$(echo "$CHANGE_24H" | tr -d '-')
    if (( $(echo "$ABS_CHANGE > 5" | bc -l 2>/dev/null || echo "0") )); then
        echo "⚠️ 注意: 24小时波动较大 ($CHANGE_24H%)"
        echo "建议: 谨慎操作，注意风险管理"
    elif (( $(echo "$ABS_CHANGE > 2" | bc -l 2>/dev/null || echo "0") )); then
        echo "📊 市场活跃: 中等波动 ($CHANGE_24H%)"
        echo "建议: 关注市场动态"
    else
        echo "📈 市场稳定: 小幅波动 ($CHANGE_24H%)"
        echo "建议: 适合观察或小额交易"
    fi
fi

echo ""
echo "🔧 其他查询选项:"
echo "  1. 查看以太坊价格: curl -s 'https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd'"
echo "  2. 查看前10加密货币: curl -s 'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10'"
echo "  3. 技术分析: 使用crypto-ta-analyzer技能"

echo ""
echo "✅ 查询完成"