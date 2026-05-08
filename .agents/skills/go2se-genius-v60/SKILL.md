# GO2SE Genius v6.0 - 最大算力优化版

## 技能描述
基于深度分析的GO2SE Genius v6.0交易系统，调用GBrain和AI算力进行优化，目标是实现100%+月收益。

## 核心功能
- 高频交易信号生成
- 智能仓位管理
- 多维度RSI/布林带分析
- CROSS杠杆做多做空
- 自动风险控制

## 版本历史
- v6.0: 最大算力优化版 (2026-05-08)
  - 仓位: 70%
  - 止盈: 15%
  - 止损: 5%
  - RSI: 35/65
  - 布林: 20/80
  - 杠杆: 3x
  - 做空: 开启

## 使用方法
```bash
bash ~/.openclaw/workspace/scripts/go2se_genius_v60.sh
```

## 配置参数
| 参数 | 值 | 说明 |
|------|-----|------|
| position_ratio | 0.70 | 仓位70% |
| take_profit | 0.15 | 止盈15% |
| stop_loss | 0.05 | 止损5% |
| rsi_buy | 35 | RSI超卖线 |
| rsi_sell | 65 | RSI超买线 |
| bb_buy | 20 | 布林下轨 |
| bb_sell | 80 | 布林上轨 |
| leverage | 3 | 3倍杠杆 |
| allow_short | true | 开启做空 |

## 技能作者
GO2SE Team
