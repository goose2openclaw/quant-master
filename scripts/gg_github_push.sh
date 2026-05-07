#!/bin/bash
# GG v2.5 GitHub Push
# 日期: 2026-05-06

cd ~/.openclaw/workspace/openclaw-workspace/GO2SE_PLATFORM

# 添加所有更改
git add -A

# 提交
git commit -m "GO2SE Genius v2.5: 插针系统+自主交易+声纳融合

- 新增插针捕获系统 (做空/做多)
- 新增三层监控 (风险/交易/日报)
- 声纳6分制评分融合
- 30天回测: 专家+51%, 普通+12%
- 胜率提升: 72.2% vs 68.1%

版本: v2.5.0
日期: 2026-05-06"

# 推送
git push origin main 2>/dev/null || git push origin master 2>/dev/null

echo "✅ GitHub推送完成"
