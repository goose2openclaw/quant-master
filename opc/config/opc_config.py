"""
OPC - One Powerful Core
统一配置中心
"""
import os

# === API配置 ===
API_KEY = "QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61"
API_SECRET = "BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk"
PROXY = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

# === 交易参数 ===
TRADE_BUDGET = 5           # 每笔交易预算
MAX_POSITIONS = 8          # 最大持仓数
COOLDOWN = 15              # 交易冷却(秒)
MAX_HOLD_TIME = 180        # 最大持仓时间(秒)

# === 止盈止损 ===
TP_RATE = 0.01             # 止盈 1%
SL_RATE = 0.015            # 止损 1.5%

# === 信号参数 ===
RSI_BUY = 35               # RSI超卖阈值
RSI_SELL = 70              # RSI超买阈值
BB_BUY = 0.20             # BB买入阈值(下轨附近)
BB_SELL = 0.80            # BB卖出阈值(上轨附近)

# === 黑名单 ===
BLACKLIST = [
    'NEIRO', 'TURBO', 'PEPE', 'FLOKI', 'BOME', 'SHIB', 'VR', 'VRQQ', 'BNB',
    'AI', 'NEAR', 'INJ', 'ATOM', 'DOT'  # 交易量不够的币种
]

# === 扫描币种 ===
SCAN_COINS = ['BTC','ETH','XRP','ADA','SOL','DOGE','LINK','LTC','ETC','UNI','AVAX','ARB']

# === 动量参数 (新功能) ===
MOMENTUM_ENABLED = True
MOMENTUM_THRESHOLD = 5      # 24h涨超5%触发
MOMENTUM_RSI_MIN = 55      # RSI需高于此值
MOMENTUM_SL = 0.005        # 动量止损0.5%

# === 记忆配置 ===
MEMORY_DIR = '/home/goose/.openclaw/workspace/opc/memory'
LOG_DIR = '/home/goose/.openclaw/workspace/opc/logs'

# === 风险控制 ===
MAX_DAILY_TRADES = 20      # 每日最大交易数
MAX_POSITION_PCT = 0.01     # 单笔最大仓位(1%)
