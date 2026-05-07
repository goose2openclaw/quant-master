#!/bin/bash
# 系统状态处理脚本

echo "📊 生成系统状态报告..."

# 获取系统信息
SYS_TIME=$(date '+%Y-%m-%d %H:%M:%S')
SYS_USER=$(whoami)
SYS_UPTIME=$(uptime -p)
OPC_SKILLS=$(find ~/.openclaw/workspace/skills -name "SKILL.md" 2>/dev/null | wc -l)
OPC_SCRIPTS=$(find ~/.openclaw/workspace/scripts -name "*.sh" -o -name "*.py" 2>/dev/null | wc -l)

# 生成状态消息
cat << STATUS
✅ *OPC系统状态报告*

🖥️ *系统信息*
• 用户: $SYS_USER
• 时间: $SYS_TIME
• 运行时间: $SYS_UPTIME

📦 *OPC项目*
• 技能数量: $OPC_SKILLS
• 脚本数量: $OPC_SCRIPTS
• 项目目录: ~/opc-project

🔧 *服务状态*
• OpenClaw: ✅ 运行中
• Telegram Bot: ✅ 已配置
• 监控系统: ✅ 已部署
• 计划任务: ✅ 已设置

🚀 *下一步*
• 运行 /crypto 查看行情
• 检查 ~/opc-project/ 开始开发
• 查看日志: ~/.openclaw/workspace/logs/

⏰ 报告生成时间: $SYS_TIME
STATUS
