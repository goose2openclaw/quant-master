# HEARTBEAT 配置

**创建时间**：2026-04-19
**版本**：v1.0

---

## 自动化任务配置

```yaml
heartbeat:
  enabled: true
  timezone: "Asia/Shanghai"
  log_file: "knowledge/heartbeat.log"
  notification_channel: "qqbot"

# 每日任务
daily_tasks:
  - name: code-quality-check
    time: "09:00"
    description: "检查代码质量和技术债"
    skill: code-registry
    params:
      path: "~/projects"
      outputFormat: "markdown"
    on_failure: notify
    on_success: log

  - name: system-check
    time: "12:00"
    description: "检查系统状态"
    action: system-status
    params:
      checks: ["disk", "memory", "docker"]
    on_failure: notify

  - name: memory-update
    time: "18:00"
    description: "更新记忆系统"
    skill: cognitive-memory
    params:
      files: ["MEMORY.md", "memory/TODAY.md"]
      action: "index"
    on_failure: log

  - name: daily-summary
    time: "23:59"
    description: "生成每日摘要"
    action: generate-summary
    params:
      type: "daily"
    on_failure: log

# 每周任务
weekly_tasks:
  - name: tech-debt-summary
    day: "monday"
    time: "10:00"
    description: "生成技术债汇总报告"
    skill: code-registry
    params:
      action: "tech-debt-report"
      days: 7
    on_failure: notify

  - name: memory-cleanup
    day: "sunday"
    time: "20:00"
    description: "清理过时记忆"
    skill: cognitive-memory
    params:
      action: "cleanup"
      days_ago: 90
    on_failure: log

  - name: weekly-summary
    day: "sunday"
    time: "23:59"
    description: "生成周摘要"
    action: generate-summary
    params:
      type: "weekly"
    on_failure: log

# 每月任务
monthly_tasks:
  - name: system-optimization
    day: 1
    time: "09:00"
    description: "系统优化"
    action: optimize-system
    params:
      actions: ["clean-temp", "optimize-db", "update-deps"]
    on_failure: notify

  - name: skill-evaluation
    day: 15
    time: "10:00"
    description: "评估技能使用情况"
    action: evaluate-skills
    params:
      period: 30  # 天
    on_failure: log

  - name: monthly-summary
    day: 1
    time: "23:59"
    description: "生成月摘要"
    action: generate-summary
    params:
      type: "monthly"
    on_failure: log

# 通知配置
notifications:
  enabled: true
  channels:
    - type: "qqbot"
      priority: "all"
    - type: "email"
      priority: ["CRITICAL", "HIGH"]

  levels:
    CRITICAL:
      immediate: true
      channels: ["qqbot", "email"]
      summary: true

    HIGH:
      immediate: false
      channels: ["qqbot"]
      summary: true
      schedule: "daily"

    MEDIUM:
      immediate: false
      channels: ["qqbot"]
      summary: true
      schedule: "weekly"

    LOW:
      immediate: false
      channels: ["qqbot"]
      summary: true
      schedule: "monthly"

# 监控指标
monitoring:
  system:
    - name: "cpu_usage"
      threshold: 80
      unit: "%"
      check_interval: "5m"

    - name: "memory_usage"
      threshold: 85
      unit: "%"
      check_interval: "5m"

    - name: "disk_usage"
      threshold: 90
      unit: "%"
      check_interval: "1h"

  skills:
    - name: "pair-coding"
      metric: "success_rate"
      threshold: 90
      unit: "%"

    - name: "code-registry"
      metric: "scan_time"
      threshold: 60
      unit: "s"

    - name: "cognitive-memory"
      metric: "recall_time"
      threshold: 5
      unit: "s"

  memory:
    - name: "total_memories"
      threshold: 10000
      unit: "count"

    - name: "memory_size"
      threshold: 1000
      unit: "MB"

# 自动记忆巩固
memory_consolidation:
  enabled: true
  auto_index:
    - paths: ["MEMORY.md", "memory/*.md"]
    - triggers: ["file_change", "schedule"]
    - schedule: "*/30 * * * *"  # 每 30 分钟

  importance_update:
    - access_boost: 0.05
    - reference_boost: 0.10
    - decay_rate: 0.01
    - decay_interval: "1d"

  conflict_detection:
    enabled: true
    check_interval: "1h"
    action: "log"
    notify: true

  summary_generation:
    daily: "23:59"
    weekly: "sunday 23:59"
    monthly: "1 23:59"

# SOUL.md/IDENTITY.md 联动
soul_identity_integration:
  enabled: true

  pair-coding:
    read_soul: true
    check_principles: true
    check_must: true
    check_never: true
    update_identity: true

  auto_update:
    triggers:
      - "task_completed"
      - "new_pattern_learned"
      - "preference_discovered"

    updates:
      soul:
        - "add_must_rule"
        - "add_never_rule"
        - "update_work_style"

      identity:
        - "bump_version"
        - "add_learning_record"
        - "update_values"
        - "update_growth"
```

---

## 使用说明

### 启用/禁用 HEARTBEAT
```yaml
heartbeat:
  enabled: true  # 或 false
```

### 添加/修改任务
```yaml
daily_tasks:
  - name: "my-task"
    time: "HH:MM"
    description: "任务描述"
    skill: "skill-name"
    params:
      key: value
```

### 修改通知配置
```yaml
notifications:
  enabled: true
  channels: [...]
  levels: {...}
```

---

## 日志位置

- **HEARTBEAT 日志**：`knowledge/heartbeat.log`
- **自动化日志**：`knowledge/automation.log`
- **巩固日志**：`knowledge/consolidation.log`

---

*版本历史*：
- v1.0 (2026-04-19) - 初始版本
