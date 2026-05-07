#!/usr/bin/env python3
"""
简单的加密货币检查脚本
使用CoinGecko API获取前10大加密货币价格
"""

import requests
import json
from datetime import datetime

def get_crypto_prices():
    """获取前10大加密货币价格"""
    try:
        print("正在获取加密货币数据...")
        
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 10,
            "page": 1
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        print(f"\n📊 加密货币市场报告")
        print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        print(f"{'排名':<4} {'名称':<15} {'价格(USD)':<15} {'24h变化':<10} {'市值排名':<10}")
        print("-"*60)
        
        for i, coin in enumerate(data, 1):
            name = coin.get('name', 'Unknown')[:14]
            price = coin.get('current_price', 0)
            change = coin.get('price_change_percentage_24h', 0)
            market_cap_rank = coin.get('market_cap_rank', 'N/A')
            
            # 格式化变化百分比
            if change > 0:
                change_str = f"📈 +{change:.1f}%"
            elif change < 0:
                change_str = f"📉 {change:.1f}%"
            else:
                change_str = "➖ 0.0%"
            
            print(f"{i:<4} {name:<15} ${price:<14,.2f} {change_str:<10} {market_cap_rank:<10}")
        
        print("="*60)
        
        # 计算总体变化
        total_change = sum(coin.get('price_change_percentage_24h', 0) for coin in data)
        avg_change = total_change / len(data) if data else 0
        
        print(f"\n📈 前10大币种平均24h变化: {avg_change:+.1f}%")
        
        if avg_change > 2:
            print("💹 市场情绪: 积极")
        elif avg_change < -2:
            print("🔻 市场情绪: 消极")
        else:
            print("➖ 市场情绪: 中性")
        
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络错误: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析错误: {e}")
        return None
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return None

if __name__ == "__main__":
    print("🚀 OPC加密货币监控系统 - 简单检查")
    print("="*60)
    data = get_crypto_prices()
    
    if data:
        print("\n✅ 数据获取成功!")
        
        # 保存到文件
        try:
            import os
            reports_dir = "/home/goose/.openclaw/workspace/reports"
            os.makedirs(reports_dir, exist_ok=True)
            
            filename = f"crypto_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(reports_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"📁 报告已保存: {filepath}")
        except Exception as e:
            print(f"⚠️ 保存报告时出错: {e}")
    else:
        print("\n❌ 数据获取失败，请检查网络连接或API状态")