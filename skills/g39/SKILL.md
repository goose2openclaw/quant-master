# G39 - 全集成自主量化交易系统

## 版本
- **版本**: v3.2 (修复版)
- **日期**: 2026-05-15
- **状态**: 实盘运行中

## 概述
G39是全集成自主量化交易系统，整合9大策略模块 + Top10交易员策略，支持四大账户全自动交易。

## 核心架构
- go-core (20%) - Mirofish 300智能体共识
- go-pool (15%) - 撞球周期策略
- go-long-short (15%) - 多空双向
- go-detect (12%) - 机构侦测
- go-rotate (12%) - 板块轮动
- go-etf (10%) - ETF流动性
- Top10交易员 (15%) - 顶级策略蒸馏

## 交易参数
| 参数 | 值 |
|------|-----|
| SCAN_INTERVAL | 30秒 |
| STOP_LOSS | 5% |
| TAKE_PROFIT | 20% |
| KELLY_BASE | 30% |
| LONG_THRESHOLD | 0.08 |

## 币种
- 主流: BTC, ETH, SOL, XRP, ADA, DOT
- Meme: PEPE, BONK, DOGE, SHIB, FLOKI, BOME, TURBO, NEIRO

## v3.2修复
1. get_price重复USDT后缀
2. place_order hmac/hashlib导入
3. format_quantity整数精度
4. quantity字符串格式化

## 使用
```bash
python3 skills/g39/g39.py
```

---

*G39 v3.2 - 2026-05-15*
