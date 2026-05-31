"""
OPC配置 - 从父级导入
"""
import sys, os
sys.path.insert(0, '/home/goose/.openclaw/workspace/opc')

# API配置
API_KEY = "QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61"
API_SECRET = "BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk"
PROXY = {'http':'http://172.29.144.1:7897','https':'http://172.29.144.1:7897'}

# 交易参数
TRADE_BUDGET = 5
MAX_POSITIONS = 8
COOLDOWN = 15
MAX_HOLD_TIME = 180

# 止盈止损
TP_RATE = 0.01
SL_RATE = 0.015

# 信号参数
RSI_BUY = 35
RSI_SELL = 70
BB_BUY = 0.20
BB_SELL = 0.80

# 黑名单
BLACKLIST = ['NEIRO', 'TURBO', 'PEPE', 'FLOKI', 'BOME', 'SHIB', 'VR', 'VRQQ', 'BNB', 'AI', 'NEAR', 'INJ', 'ATOM', 'DOT']

# 扫描币种
SCAN_COINS = ['BTC','ETH','XRP','ADA','SOL','DOGE','LINK','LTC','ETC','UNI','AVAX','ARB']

# 动量参数
MOMENTUM_ENABLED = True
MOMENTUM_THRESHOLD = 5
MOMENTUM_RSI_MIN = 55
MOMENTUM_SL = 0.005
