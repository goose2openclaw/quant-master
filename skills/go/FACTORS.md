# go 因子库 - 完整量化交易因子列表

## 📊 因子总览

| 类别 | 名称 | 因子数量 |
|------|------|----------|
| 1 | 技术因子 | 80+ |
| 2 | 链上因子 | 30+ |
| 3 | 情绪因子 | 20+ |
| 4 | 宏观因子 | 20+ |
| 5 | 结构因子 | 20+ |
| 6 | DeFi因子 | 15+ |
| 7 | 期权/衍生品因子 | 15+ |
| 8 | 时间因子 | 15+ |
| 9 | 玄学因子 | 25+ |
| 10 | 组合因子 | 13 |
| **总计** | | **200+** |

---

## 【1】技术因子 (TECHNICAL FACTORS)

### [1.1] 趋势类因子
| 因子ID | 名称 | 计算公式 |
|--------|------|----------|
| trend_ma5 | 5日均线 | MA(Close,5) |
| trend_ma10 | 10日均线 | MA(Close,10) |
| trend_ma20 | 20日均线 | MA(Close,20) |
| trend_ma50 | 50日均线 | MA(Close,50) |
| trend_ma100 | 100日均线 | MA(Close,100) |
| trend_ma200 | 200日均线 | MA(Close,200) |
| trend_ema20 | 20日指数均线 | EMA(Close,20) |
| trend_ema50 | 50日指数均线 | EMA(Close,50) |
| trend_ema200 | 200日指数均线 | EMA(Close,200) |
| trend_ma_cross | MA交叉信号 | MA5 vs MA20 |
| trend_golden_cross | 金叉信号 | MA50上穿MA200 |
| trend_death_cross | 死叉信号 | MA50下穿MA200 |
| trend_adx | ADX趋势强度 | ADX(14) |
| trend_adx_plus | ADX+方向指标 | DI+(14) |
| trend_adx_minus | ADX-方向指标 | DI-(14) |
| trend_aroon_up | Aroon上升线 | AroonUp(25) |
| trend_aroon_down | Aroon下降线 | AroonDown(25) |
| trend_supertrend | 超级趋势 | SuperTrend(10,3) |
| trend_ichimoku_a | 一目均衡线A | (Tenkan+Kijun)/2 |
| trend_ichimoku_b | 一目均衡线B | (Highest+Lowest)/2 |

### [1.2] 动量类因子
| 因子ID | 名称 | 计算公式 |
|--------|------|----------|
| momentum_rsi | RSI相对强弱 | RSI(14) |
| momentum_stoch_k | 随机指标K | Stochastic %K(14) |
| momentum_stoch_d | 随机指标D | Stochastic %D(3) |
| momentum_cci | CCI商品通道 | CCI(20) |
| momentum_momentum | 动量 | Close - Close(10) |
| momentum_roc | 变化率 | (Close - Close(10))/Close(10) |
| momentum_williams_r | 威廉指标 | Williams %R(14) |
| momentum_mfi | 资金流量 | MFI(14) |
| momentum_ultimate_osc | 终极振荡器 | UO(7,14,28) |
| momentum_ppo | 价格振荡百分比 | (EMA12-EMA26)/EMA26 |

### [1.3] 波动类因子
| 因子ID | 名称 | 计算公式 |
|--------|------|----------|
| volatility_atr | 平均真实波幅 | ATR(14) |
| volatility_atr_percent | ATR百分比 | ATR/Close × 100 |
| volatility_stddev | 标准差 | StdDev(Close,20) |
| volatility_bb_width | 布林带宽度 | (Upper-Lower)/Middle |
| volatility_bb_position | 布林带位置 | (Close-Lower)/(Upper-Lower) |
| volatility_kc_width | 肯特纳宽度 | (UpperKelt-LowerKelt)/Middle |
| volatility_donchian | 唐奇安波幅 | (High20-Low20)/Mid |

### [1.4] 成交量类因子
| 因子ID | 名称 | 计算公式 |
|--------|------|----------|
| volume_obv | 能量潮 | Cum(Vol × Sign(ΔClose)) |
| volume_vwap | 成交量加权均价 | Cum(Price×Vol)/Cum(Vol) |
| volume_mfi | 资金流量指数 | MFI(14) |
| volume_adi | 积累分配指标 | ADI |
| volume_cm_f | Chaikin资金流 | CMF(20) |
| volume_vol_roc | 成交量变化率 | (Vol-Vol(10))/Vol(10) |

### [1.5] 振荡器类因子
| 因子ID | 名称 | 计算公式 |
|--------|------|----------|
| oscillator_rsi | RSI | RSI(14) |
| oscillator_stoch | 随机指标 | Stochastic(14,3) |
| oscillator_cci | CCI | CCI(20) |
| oscillator_williams | 威廉指标 | Williams %R(14) |
| oscillator_smi | 随机动量指数 | SMI(14,3,5) |

---

## 【2】链上因子 (ON-CHAIN FACTORS)

### [2.1] 地址类因子
| 因子ID | 名称 | 数据源 |
|--------|------|--------|
| onchain_active_addr | 活跃地址数 | Blockchain.com |
| onchain_new_addr | 新增地址数 | Glassnode |
| onchain_addr_growth | 地址增长率 | (New-Active)/Active |
| onchain_whale_count | 巨鲸数量 | WhaleAlert |

### [2.2] 交易所类因子
| 因子ID | 名称 | 数据源 |
|--------|------|--------|
| onchain_ex_inflow | 交易所净流入 | CryptoQuant |
| onchain_ex_outflow | 交易所净流出 | CryptoQuant |
| onchain_ex_balance | 交易所余额 | Glassnode |

### [2.3] 质押/借贷类因子
| 因子ID | 名称 | 数据源 |
|--------|------|--------|
| onchain_staking_rate | 质押率 | Staking Rewards |
| onchain_lending_rate | 借贷利率 | DeFi Pulse |
| onchain_liquidation | 清算量 | DeBank |

---

## 【3】情绪因子 (SENTIMENT FACTORS)

| 因子ID | 名称 | 数据源 |
|--------|------|--------|
| sentiment_fear_greed | 恐惧贪婪指数 | Alternative.me |
| sentiment_funding_rate | 资金费率 | Binance API |
| sentiment_open_interest | 未平仓量 | Coinglass |
| sentiment_long_short | 多空比 | Binance |

---

## 【4】宏观因子 (MACRO FACTORS)

### [4.1] 加密市场类
| 因子ID | 名称 | 数据源 |
|--------|------|--------|
| macro_btc_dominance | BTC主导地位 | CoinMarketCap |
| macro_altseason_idx | 山寨季指数 | BlockChainCenter |
| macro_total_cap | 加密总市值 | CoinGecko |

### [4.2] 传统市场类
| 因子ID | 名称 | 数据源 |
|--------|------|--------|
| macro_sp500 | 标普500 | Yahoo Finance |
| macro_vix | VIX恐慌指数 | CBOE |
| macro_dxy | 美元指数 | ICE |

---

## 【5】结构因子 (STRUCTURAL FACTORS)

| 因子ID | 名称 | 计算 |
|--------|------|------|
| structure_support_1 | 一级支撑 | S1 = P - (H-L) |
| structure_resist_1 | 一级阻力 | R1 = P + (H-L) |
| structure_fib_382 | 斐波38.2% | H - (H-L)×0.382 |
| structure_fib_618 | 斐波61.8% | H - (H-L)×0.618 |
| structure_poc | 成交量集中点 | Mode(Price×Vol) |

---

## 【6】DeFi因子 (DEFI FACTORS)

| 因子ID | 名称 | 数据源 |
|--------|------|--------|
| defi_tvl | 总锁仓量 | DeFiLlama |
| defi_apr | 年化收益率 | DeFi Saver |
| defi_lending_rate | 借贷利率 | Aave |

---

## 【7】期权/衍生品因子

| 因子ID | 名称 | 数据源 |
|--------|------|--------|
| option_iv_call | 看涨IV | Deribit |
| option_put_call_ratio | 看跌看涨比 | Coinglass |
| futures_basis | 期货基差 | Binance |

---

## 【8】时间因子

| 因子ID | 名称 | 值域 |
|--------|------|------|
| time_hour_of_day | 小时周期 | 0-23 |
| time_day_of_week | 星期周期 | 0-6 |
| time_btc_halving | BTC减半周期 | 0-4年 |

---

## 【9】玄学因子 (MYSTICAL FACTORS)

### [9.1] 天文类
| 因子ID | 名称 | 计算 |
|--------|------|------|
| mystic_moon_phase | 月相 | (Date - 2000-01-06) % 29.53 / 29.53 |
| mystic_moon_full | 是否满月 | 0.4 < Phase < 0.6 |

### [9.2] 江恩/斐波类
| 因子ID | 名称 | 计算 |
|--------|------|------|
| mystic_gann_angle | 江恩角度 | 1×1, 2×1, 3×1, 4×1, 8×1 |
| mystic_fib_time | 斐波那契时间 | 1,2,3,5,8,13,21... |

### [9.3] 中国传统类
| 因子ID | 名称 | 计算 |
|--------|------|------|
| mystic_iching_hex | 易经卦象 | Date → Hexagram |
| mystic_bagua | 八卦方位 | Date → Trigram |
| mystic_wuxing | 五行 | Date → Element |

---

## 【10】组合因子

| 因子ID | 名称 | 计算 |
|--------|------|------|
| composite_sharpe | 夏普比率 | (Return-Rf)/StdDev |
| composite_sortino | 索提诺比率 | (Return-Rf)/DownsideDev |
| composite_calmar | 卡玛比率 | Return/MaxDrawdown |
| composite_max_dd | 最大回撤 | Peak-Trough |
| composite_win_rate | 胜率 | Wins/Total |
| composite_beta | Beta | Cov(R,Rm)/Var(Rm) |

---

## 因子权重配置 (示例)

```python
FACTOR_WEIGHTS = {
    # 技术因子 (70%)
    'rsi': 0.12,
    'momentum': 0.10,
    'volume': 0.10,
    'trend': 0.08,
    'volatility': 0.08,
    'bollinger': 0.06,
    'macd': 0.06,
    'atr': 0.05,
    
    # 链上因子 (10%)
    'onchain_active_addr': 0.04,
    'onchain_ex_flow': 0.03,
    'onchain_whale': 0.03,
    
    # 情绪因子 (8%)
    'sentiment_fear_greed': 0.03,
    'sentiment_funding': 0.03,
    'sentiment_oi': 0.02,
    
    # 宏观因子 (7%)
    'macro_btc_dom': 0.03,
    'macro_vix': 0.02,
    'macro_dxy': 0.02,
    
    # 玄学因子 (5%)
    'mystic_moon': 0.02,
    'mystic_dayofweek': 0.015,
    'mystic_halving': 0.015,
}
```

---

**最后更新**: 2026-05-12
**版本**: 1.0.0
