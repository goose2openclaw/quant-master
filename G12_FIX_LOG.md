
## 2026-05-08 修复记录

### 问题: USDT-M 合约账户 404错误
- **原因**: URL错误 - 使用了 `api.binance.com/fapi` 而不是 `fapi.binance.com/fapi`
- **影响**: god_mode无法读取合约账户状态
- **修复**: 
  - `hermes_g12_god_mode.py`: 修正合约API URL为 `https://fapi.binance.com/fapi/v2/account`
- **验证**: ✅ 合约账户连接成功 ($0.00 余额)
- **状态**: 已保存到代码

### 相关文件
- `hermes_g12_god_mode.py` - 合约URL修复
- `hermes_g12_plus_trader.py` - 无需修复
- `hermes_g12_plus_monitor.py` - 无需修复

