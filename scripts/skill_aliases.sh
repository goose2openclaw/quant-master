#!/bin/bash
# OpenClaw技能别名

# github技能别名
alias gh-clone='openclaw skills run github clone'
alias gh-status='openclaw skills run github status'
alias gh-push='openclaw skills run github push'

# cron技能别名
alias cron-add='openclaw skills run cron add'
alias cron-list='openclaw skills run cron list'
alias cron-remove='openclaw skills run cron remove'

# shell技能别名
alias sys-disk='openclaw skills run shell disk'
alias sys-memory='openclaw skills run shell memory'
alias sys-process='openclaw skills run shell process'

# telegram技能别名
alias tg-send='openclaw skills run telegram send'
alias tg-status='openclaw skills run telegram status'

# 快速启用技能
skill-enable() {
    openclaw skills enable "$1"
}

skill-disable() {
    openclaw skills disable "$1"
}

skill-list() {
    openclaw skills list | grep -E "(✓ ready|✗ missing)"
}

echo "技能别名已加载"
