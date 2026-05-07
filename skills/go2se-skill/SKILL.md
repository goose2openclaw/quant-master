# Go2Se Skill

## Description
Go2Se Professional Trading Platform - 7连环市场 + 12竞品策略整合 + 多源信号 + 预言机

## Commands

### 启动平台
```
go2se start
```
启动Go2Se Web UI平台 (端口5000)

### 查看市场
```
go2se markets
```
查看7连环市场实时数据

### 查看信号
```
go2se signals
```
查看多源聚合交易信号

### 查看策略
```
go2se strategies
```
查看12个整合策略

### 查看预言机
```
go2se oracle
```
查看预言机事件

### 薅羊毛
```
go2se airdrop
```
搜索空投机会

### 回测
```
go2se backtest 10000 30
```
回测 (资金, 天数)

### 投资组合
```
go2se portfolio
```
查看当前投资组合

### 预设方案
```
go2se preset conservative
go2se preset balanced
go2se preset aggressive
```
应用预设方案

### 服务模式
```
go2se services
```
查看服务模式

## Integration

Web UI: http://localhost:5000

API Endpoints:
- /api/markets - 7连环市场
- /api/signals - 交易信号
- /api/strategies - 12策略
- /api/oracle - 预言机
- /api/portfolio - 投资组合
- /api/airdrop/hunt - 薅羊毛
- /api/backtest - 回测

## Skill Actions

### start_platform
启动Web UI平台

### get_markets
获取市场数据

### get_signals
获取实时信号

### get_strategies
获取策略列表

### get_oracle
获取预言机事件

### hunt_airdrop
执行薅羊毛

### run_backtest
执行回测

### update_portfolio
更新投资组合

### apply_preset
应用预设
