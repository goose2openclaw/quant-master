# Top 10 Trader to Crypto Skill

## 概述
将全球十大顶级交易员的交易策略适配到加密货币市场，形成自适应、自选择、智能迭代的交易员组合系统。

## 十大交易员（加密货币适配版）

### 1. 乔治·索罗斯 (Soros)
- **原风格**: 宏观对冲/反身性理论
- **加密适配**: ETF溢价、期货基差、资金费率异常
- **擅长**: BTC, ETH, GBTC, ETHE
- **止损/止盈**: 8%/25%

### 2. 斯坦利·德鲁肯米勒 (Druckenmiller)
- **原风格**: 流动性狩猎
- **加密适配**: 链上流动性、交易所余额、稳定币流量
- **擅长**: BTC, ETH, LINK
- **止损/止盈**: 6%/20%

### 3. 布鲁斯·柯夫纳 (Kovner)
- **原风格**: 外汇期货
- **加密适配**: 技术突破、预言机数据、DeFi TVL
- **擅长**: LINK, BAND, AAVE
- **止损/止盈**: 5%/18%

### 4. 迈克尔·马库斯 (Marcus)
- **原风格**: 商品期货/趋势跟踪
- **加密适配**: 趋势形成、持仓量增加、供需变化
- **擅长**: BTC, ETH, SOL
- **止损/止盈**: 10%/30%

### 5. 保罗·都铎·琼斯 (Jones)
- **原风格**: 趋势跟踪
- **加密适配**: 均线多头排列、RSI极端、趋势线突破
- **擅长**: BTC, ETH, DOGE, PEPE
- **止损/止盈**: 5%/20%

### 6. 理查德·丹尼斯 (Dennis)
- **原风格**: 系统化交易
- **加密适配**: 唐奇安通道、规则化信号、20日突破
- **擅长**: BTC, ETH, SOL
- **止损/止盈**: 5%/15%

### 7. 马丁·舒华兹 (Schwartz)
- **原风格**: 技术分析/K线形态
- **加密适配**: Meme叙事、社交热度、K线组合
- **擅长**: DOGE, SHIB, PEPE, BONK
- **止损/止盈**: 8%/25%

### 8. 比尔·利普舒茨 (Lipschutz)
- **原风格**: 外汇专精
- **加密适配**: 预言机数据、DeFi相关币种
- **擅长**: LINK, BAND, API3
- **止损/止盈**: 5%/18%

### 9. 杰西·利弗莫尔 (Livermore)
- **原风格**: 价格行为
- **加密适配**: 龙头效应、板块轮动、价格新高/低
- **擅长**: BTC, ETH, SOL, DOGE
- **止损/止盈**: 6%/22%

### 10. 吉姆·罗杰斯 (Rogers)
- **原风格**: 商品期货
- **加密适配**: 机构持仓、ETF流入、美元走势
- **擅长**: BTC, ETH, LINK
- **止损/止盈**: 8%/25%

## 币种分类

### Mainstream (主流币)
BTC, ETH, BNB, SOL, XRP, ADA, AVAX, DOGE, DOT, MATIC

### Meme (Meme币)
DOGE, SHIB, PEPE, BONK, FLOKI, BOME, TURBO, NEIRO, WIF, MOG

### ETF (ETF相关)
GBTC, ETHE, FBTC, IBIT, ARKB

### Oracle (预言机)
LINK, BAND, API3, POKT, TRAC

## 核心模块

### 1. 市场信号分析器
```python
signal = {
    'trend': 'bull/bear/sideways',
    'volatility': 'high/medium/low',
    'momentum': -1.0 to 1.0,
    'volume_change': percentage,
    'funding_rate': decimal,
    'coin_type': 'mainstream/meme/etf/oracle'
}
```

### 2. 加权组合引擎
- 根据币种类型调整权重
- 根据市场状态动态调整
- 持续优化学习

### 3. 自主优化模块
- 记录交易结果
- 调整权重系数
- 防止过拟合

## 使用方法

### 基本调用
```python
from top10_trader_crypto import Top10TraderCrypto

system = Top10TraderCrypto()

# 分析单个币种
decision = system.analyze('BTC')
print(f"交易员: {decision.trader_cn}")
print(f"方向: {decision.direction}")
print(f"仓位: {decision.position_size:.0%}")

# 运行30天回测
results = system.run_backtest_30d()
```

### 输出格式
```python
{
    'symbol': 'BTC',
    'trader': 'jones',
    'trader_cn': '琼斯',
    'direction': 'long',
    'confidence': 0.85,
    'position_size': 0.25,
    'stop_loss': 0.05,
    'take_profit': 0.20,
    'reasoning': 'mainstream+bull+琼斯+利弗莫尔+罗杰斯'
}
```

## 回测结果

### 30天回测矩阵格式
```
| Coin Type  | WinRate | AvgReturn | TotalReturn |
|------------|---------|-----------|-------------|
| mainstream | 62%     | +3.2%     | +28.5%      |
| meme       | 55%     | +5.8%     | +45.2%      |
| oracle     | 58%     | +2.1%     | +18.3%      |
| etf        | 65%     | +4.5%     | +32.1%      |
```

## 版本
- v1.0: 初始版本，支持四大币种分类
- v1.1: 增加30天回测模块
