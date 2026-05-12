# G28 Oracle Auto Trading Skill

## 描述
G28全自动交易系统 - Oracle智能决策 + 自主交易 + 资金自动调配

## 功能
1. Oracle决策: RSI + 动量 + Monte Carlo仿真
2. 自动交易: 检测到信号自动执行市价单
3. 资金调配: USDT不足时自动卖出高RSI币种
4. 杠杆备用: 自动转入合约账户准备杠杆
5. 失败处理: 交易失败自动重试和调整

## 核心脚本
- g28_fixed.py - 当前运行版本 (v4.1)
- g28_complete.py - 完整功能版

## 运行
python3 /home/goose/.openclaw/workspace/scripts/g28_fixed.py

## 日志
tail -f /home/goose/.openclaw/workspace/logs/g28_fixed.log

## 创建时间
2026-05-12 15:30

## 版本
v4.1 - 修复版 (自动转换功能)
