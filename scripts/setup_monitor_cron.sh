#!/bin/bash
# 设置技能监控cron任务

echo "设置技能监控cron任务..."
echo ""

# 每天8点运行监控
CRON_JOB="0 8 * * * cd $HOME/.openclaw/workspace && python3 scripts/monitor_skills.py >> logs/monitor_cron.log 2>&1"

# 添加到crontab
(crontab -l 2>/dev/null | grep -v "monitor_skills.py"; echo "$CRON_JOB") | crontab -

echo "✅ 监控cron任务已设置"
echo "任务: $CRON_JOB"
echo ""
echo "手动运行监控: python3 ~/.openclaw/workspace/scripts/monitor_skills.py"
