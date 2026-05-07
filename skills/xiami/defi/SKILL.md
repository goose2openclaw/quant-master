# XIAMI DeFi Suite - 全流程 DeFi + 预测市场解决方案

## 概述
XIAMI DeFi Suite 提供完整的去中心化金融服务，包含发币、智能合约、预言机、焚烧、资金池，做市、二级交易、社区工具、KOL 管理、DApp 集成和预测市场。

## 快速开始

```bash
cd skills/xiami/defi/scripts

# === DeFi 功能 ===

# 发币
python defi_token.py create "MyToken" "MTK" 1000000

# 预言机价格
python defi_oracle.py price BTC/USDT

# 做市
python defi_liquidity.py mm BTC/USDT 10000

# KOL 跟单
python defi_community.py kol add vitalik 0x742d...
python defi_community.py kol signal vitalik ETH

# 收益率查询
python defi_community.py yield aave ETH

# === Polymarket 预测市场 ===

# 获取热门市场
python polymarket.py trending

# 扫描交易机会
python polymarket.py scan

# 获取预测信号
python polymarket.py signals
```

## 核心模块

### 1. 发币 → `defi_token.py`
- ERC-20 / BEP-20 代币生成
- 智能合约代码生成

### 2. 预言机 → `defi_oracle.py`
- 多源价格聚合 (Binance/Bybit/OKX)
- TWAP 价格计算
- 价格异常监控

### 3. 流动性 & 做市 → `defi_liquidity.py`
- 资金池信息查询
- 自动化做市策略

### 4. 社区 & KOL → `defi_community.py`
- 社区成员管理
- KOL 钱包追踪
- 跟单信号
- 收益率查询
- 跨链桥接

### 5. 预测市场 → `polymarket.py`
- 热门市场查询
- 交易机会扫描
- 预测信号生成

### 6. 反向Trump币 → `anti_trump.py`

```bash
# 完整研究报告
python anti_trump.py research

# Trump代币价格
python anti_trump.py prices

# 反向预言机
python anti_trump.py oracle

# 社交情绪
python anti_trump.py sentiment

# 创建Polymarket话题
python anti_trump.py topic

# 生成代币配置
python anti_trump.py token
```

## 风险提示
- DeFi 投资风险高
- 智能合约存在漏洞风险
- 预测市场不确定性大
- 建议先在测试网验证
