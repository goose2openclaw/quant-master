# G41 Enhanced - go技能调度 + Polymarket

## 版本
**v1.1 Enhanced** - go技能调度集成

## 核心架构

```
G41 Enhanced = go技能调度 + Polymarket
         |
         +-- GoSkillDispatcher (10个go技能)
         |       |
         |       +-- go-core: 20% (趋势核心)
         |       +-- go-pool: 15% (流动性)
         |       +-- go-rotate: 12% (轮转)
         |       +-- go-long-short: 12% (多空)
         |       +-- go-detect: 10% (机构检测)
         |       +-- go-etf: 8% (ETF)
         |       +-- go-contrarian: 8% (反向)
         |       +-- go-noise: 5% (噪音)
         |       +-- go-fit: 5% (拟合)
         |       +-- go-thermo: 5% (热力学)
         |
         +-- Polymarket预测 (30%权重)
         |       |
         |       +-- BTC: +0.42
         |       +-- ETH: +0.35
         |       +-- SOL: +0.28
         |       +-- DOGE: +0.22
         |
         +-- 市场自适应
                 |
                 +-- 趋势/震荡/突破/中性
```

## 信号公式

```
综合信号 = go技能加权 x 70% + Polymarket x 30%
```

## go技能权重

| 技能 | 权重 | 功能 |
|------|------|------|
| go-core | 20% | 趋势核心 |
| go-pool | 15% | 流动性分析 |
| go-rotate | 12% | 轮转策略 |
| go-long-short | 12% | 多空策略 |
| go-detect | 10% | 机构检测 |
| go-etf | 8% | ETF分析 |
| go-contrarian | 8% | 反向分析 |
| go-noise | 5% | 噪音过滤 |
| go-fit | 5% | 趋势拟合 |
| go-thermo | 5% | 热力学分析 |

## 启动

```bash
./start_g41.sh
./status_g41.sh
./stop_g41.sh
```

## GitHub
- Branch: g12branch
- 版本: v1.1 Enhanced
