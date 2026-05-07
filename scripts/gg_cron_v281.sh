#!/bin/bash
# GG v2.8.1 Cron 任务配置
# 日期: 2026-05-06

crontab - << 'CRON'
# Hermes自动循环 (每小时)
*/60 * * * * /tmp/hermes_auto_loop.sh >> /tmp/hermes_loop_cron.log 2>&1

# 开机启动
@reboot /home/goose/.openclaw/workspace/openclaw-workspace/GO2SE_PLATFORM/scripts/auto_start_go2se.sh

# v2.8.1专家模式 (每3分钟) - 强化版
*/3 * * * * $HOME/.openclaw/workspace/scripts/gg_v281_expert.sh >> /tmp/gg_v281_expert_cron.log 2>&1

# 插针检测 (每5分钟)
*/5 * * * * $HOME/.openclaw/workspace/scripts/gg_spike_system.sh >> /tmp/gg_spike_monitor.log 2>&1

# 日终报告 (每天21:00)
0 21 * * * $HOME/.openclaw/workspace/scripts/gg_cron_3layer.sh layer3 >> /tmp/gg_layer3.log 2>&1
CRON

echo "✅ v2.8.1 Cron已配置"
crontab -l | grep -v "^#"
