#!/bin/bash
crontab - << 'CRON'
*/60 * * * * /tmp/hermes_auto_loop.sh >> /tmp/hermes_loop_cron.log 2>&1
@reboot /home/goose/.openclaw/workspace/openclaw-workspace/GO2SE_PLATFORM/scripts/auto_start_go2se.sh
*/3 * * * * $HOME/.openclaw/workspace/scripts/gg_v291_expert.sh >> /tmp/gg_v291_cron.log 2>&1
*/5 * * * * $HOME/.openclaw/workspace/scripts/gg_spike_system.sh >> /tmp/gg_spike_monitor.log 2>&1
0 21 * * * $HOME/.openclaw/workspace/scripts/gg_cron_3layer.sh layer3 >> /tmp/gg_layer3.log 2>&1
CRON
echo "v2.9.1 Cron已配置"
crontab -l | grep -v "^#"
