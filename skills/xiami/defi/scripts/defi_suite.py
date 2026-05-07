#!/usr/bin/env python3
"""
XIAMI DeFi Suite - 全流程 DeFi 管理器
"""

import sys
import os

# 添加脚本目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

def main():
    if len(sys.argv) < 2:
        print("""
╔════════════════════════════════════════════════════════════╗
║         🔱 XIAMI DeFi Suite - 全流程 DeFi 管理器           ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  发币 (Token)                                              ║
║    python defi_token.py create <name> <symbol> <supply>   ║
║    python defi_token.py list                               ║
║                                                            ║
║  预言机 (Oracle)                                           ║
║    python defi_oracle.py price <symbol>                   ║
║    python defi_oracle.py twap <symbol>                   ║
║    python defi_oracle.py monitor <symbol>...              ║
║                                                            ║
║  流动性 & 做市 (Liquidity & MM)                           ║
║    python defi_liquidity.py pool <exchange> <pair>        ║
║    python defi_liquidity.py add <ex> <pair> <base> <quote>║
║    python defi_liquidity.py mm <symbol> <balance>        ║
║                                                            ║
║  社区 & KOL                                                ║
║    python defi_community.py add <platform> <id> <name>   ║
║    python defi_community.py kol add <name> <wallet>       ║
║    python defi_community.py kol signal <name> <symbol>   ║
║    python defi_community.py yield <protocol> <token>     ║
║                                                            ║
║  完整示例:                                                 ║
║    1. 发币: python defi_token.py create MyToken MTK 1000000║
║    2. 预言机: python defi_oracle.py price BTC/USDT        ║
║    3. 做市: python defi_liquidity.py mm BTC/USDT 10000   ║
║    4. 添加KOL: python defi_community.py kol add vitalik 0x..║
║    5. 跟单: python defi_community.py kol signal vitalik ETH║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
""")
        return
    
    # 路由到对应模块
    module = sys.argv[1]
    
    if module == 'token':
        from defi_token import main as token_main
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        token_main()
    elif module == 'oracle':
        from defi_oracle import main as oracle_main
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        oracle_main()
    elif module == 'liquidity':
        from defi_liquidity import main as liquidity_main
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        liquidity_main()
    elif module == 'community':
        from defi_community import main as community_main
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        community_main()
    else:
        print(f"未知模块: {module}")
        print("可用模块: token, oracle, liquidity, community")

if __name__ == '__main__':
    main()
