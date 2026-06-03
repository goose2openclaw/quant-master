# Q@C v11 APK 打包说明

## 需求
- Python 3.10+
- Kivy/KivyMD 或 React Native
- 交易所API密钥

## 快速打包

### Python 方案 (PyInstaller)
```bash
cd /home/goose/.openclaw/workspace/quant_master
pip install pyinstaller
pyinstaller --onefile --name QCv11 qm/quant_master_qcv11.py
```

### React Native 方案
```bash
npx create-expo-app QCV11
cd QCV11
# 添加交易UI组件
```

## APK功能
- 启动/停止交易
- 查看持仓
- 查看信号
- 查看账户余额

## 版本
11.0.0
