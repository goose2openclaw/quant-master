#!/bin/bash
# GG Cron 任务配置脚本 v2.8.0
# 日期: 2026-05-06

echo "=========================================="
echo "⚙️  GG Cron 任务配置"
echo "=========================================="

# 读取当前crontab
CURRENT_CRONTAB=$(crontab -l 2>/dev/null)

# 定义新的cron任务
NEW_CRON_TASKS="
# GG v2.8.0 定时任务

# Hermes自动循环 (每小时)
*/60 * * * * /tmp/hermes_auto_loop.sh >> /tmp/hermes_loop_cron.log 2>&1

# 开机启动
@reboot /home/goose/.openclaw/workspace/openclaw-workspace/GO2SE_PLATFORM/scripts/auto_start_go2se.sh

# 风险监控 (每分钟)
*/1 * * * * $HOME/.openclaw/workspace/scripts/gg_cron_3layer.sh layer1 >> /tmp/gg_layer1.log 2>&1

# 做空做多灵活转换 (每5分钟)
*/5 * * * * $HOME/.openclaw/workspace/scripts/gg_long_short_switch.sh >> /tmp/gg_long_short_switch_cron.log 2>&1

# 自主交易 (每5分钟)
*/5 * * * * $HOME/.openclaw/workspace/scripts/gg_autonomous_trader.sh >> /tmp/gg_autonomous_trade_cron.log 2>&1

# 插针检测 (每5分钟)
*/5 * * * * $HOME/.openclaw/workspace/scripts/gg_spike_system.sh >> /tmp/gg_spike_monitor.log 2>&1

# 日终报告 (每天21:00)
0 21 * * * $HOME/.openclaw/workspace/scripts/gg_cron_3layer.sh layer3 >> /tmp/gg_layer3.log 2>&1
"

# 更新crontab
echo "$NEW_CRON_TASKS" | crontab -

echo "✅ Cron任务已更新"
echo ""
echo "当前Cron配置:"
crontab -l | grep -v "^#"

echo ""
echo "=========================================="
