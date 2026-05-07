---
name: pair-coding
description: Implement Worker/Reviewer pair pattern for code generation and automated review. Ensures code quality through multiple iterations, reduces bugs, and improves maintainability.
user-invokable: true
args:
  - name: task
    description: The task description (e.g., "implement a function", "fix a bug")
    required: true
  - name: projectPath
    description: Project path (default: current directory)
    required: false
  - name: maxIterations
    description: Maximum iteration count (default: 3)
    required: false
  - name: timeout
    description: Worker timeout in seconds (default: 600)
    required: false
  - name: reviewerModel
    description: Model to use for reviewer (default: same as Worker)
    required: false
  - name: autoApprove
    description: Auto-approve low-risk changes (default: false)
    required: false
---

# Pair-Coding Skill

实现 Worker/Reviewer 对模式，用于代码生成和自动审查。通过多轮迭代确保代码质量，减少 bug，提升可维护性。

---

## 触发条件

当用户要求以下任务时触发：
- "实现功能 XXX"
- "修复 bug XXX"
- "重构 XXX"
- "优化 XXX"
- 明确的代码编写任务

**不触发**：
- 简单的一行代码修改（直接用 edit）
- 文档修改
- 配置修改

---

## 工作流程

### 1. 任务分析
1. 读取用户需求
2. 识别项目路径（默认当前目录）
3. 检查是否已有相关代码
4. 生成任务摘要

### 2. Worker 生成
1. 调用 `coding-agent` skill
2. 传递需求描述和项目路径
3. 设置合理的超时时间（默认 10 分钟）
4. 获取代码变更

### 3. Reviewer 审查
1. 调用 `check` (Waza) skill
2. 从至少 2 个角度审查：
   - 正确性：代码是否符合需求
   - 安全性：是否有安全漏洞
   - 可读性：代码是否清晰
   - 可维护性：是否易于修改
3. 生成审查报告

### 4. 决策
根据审查结果，决策：
- **APPROVE**：代码质量良好，可以提交
- **REVISE**：需要小幅修改，返回 Worker
- **REJECT**：严重问题，需要重新设计

### 5. 迭代（如需要）
如果决策不是 APPROVE：
1. 将审查意见反馈给 Worker
2. Worker 修正代码
3. 返回步骤 3（Reviewer 重新审查）
4. 最多迭代 N 次（默认 3 次）

### 6. 完成
1. 生成最终报告
2. 列出代码变更
3. 总结审查发现
4. 建议后续行动

---

## 参数配置

### 必需参数
- `task`：任务描述（字符串）

### 可选参数
- `projectPath`：项目路径（默认：当前目录）
- `maxIterations`：最大迭代次数（默认：3）
- `timeout`：Worker 超时时间（默认：600 秒）
- `reviewerModel`：审查者使用的模型（默认：与 Worker 相同）
- `autoApprove`：是否自动批准低风险修改（默认：false）

---

## 与现有 Skill 集成

### coding-agent skill
```yaml
调用方式：
  - skill: coding-agent
  - task: <用户需求>
  - projectPath: <项目路径>
  - timeout: <超时时间>

接收输出：
  - 代码变更
  - 提交信息
  - 错误（如有）
```

### check (Waza) skill
```yaml
调用方式：
  - skill: waza/check
  - changes: <代码变更>
  - angles:
    - 正确性
    - 安全性
    - 可读性

接收输出：
  - 审查报告
  - 决策（APPROVE/REVISE/REJECT）
  - 改进建议
```

---

## 输出格式

### 成功输出
```markdown
## ✅ Pair-Coding 完成

### 任务摘要
<任务描述>

### 代码变更
<文件变更列表>

### 审查结果
- 总迭代次数：X
- 最终决策：APPROVE
- 审查发现：
  - ✅ 优点 1
  - ✅ 优点 2
  - ⚠️ 注意事项 1

### 后续建议
1. <建议 1>
2. <建议 2>
```

### 失败输出
```markdown
## ❌ Pair-Coding 失败

### 任务摘要
<任务描述>

### 失败原因
<失败原因>

### 尝试次数
X / maxIterations

### 建议
1. <建议 1>
2. <建议 2>
```

---

## 错误处理

### Worker 失败
- **原因**：超时、工具错误、代码生成失败
- **处理**：记录错误，终止流程，报告用户

### Reviewer 失败
- **原因**：审查工具错误
- **处理**：重试 1 次，失败则人工审查

### 超过最大迭代次数
- **处理**：
  - 如果是 REVISE → 强制 APPROVE（附带警告）
  - 如果是 REJECT → 报告失败，建议人工干预

---

## 性能考虑

### 超时设置
- Worker：600 秒（10 分钟）
- Reviewer：180 秒（3 分钟）
- 总体：不超过 30 分钟

### 并发控制
- 同一项目：最多 1 个 pair-coding 实例
- 全局：最多 3 个实例（受 OpenClaw 并发限制）

### 资源清理
- 失败后清理临时文件
- 记录日志到 `memory/YYYY-MM-DD.md`

---

## 日志和监控

### 日志级别
- **INFO**：正常流程记录
- **WARN**：REVISE 决策、接近超时
- **ERROR**：REJECT 决策、工具失败

### 日志位置
```
memory/YYYY-MM-DD.md：会话日志
knowledge/pair-coding-log.md：专门日志
```

---

## 使用示例

### 示例 1：实现简单功能
```
用户：pair-coding 实现一个计算斐波那契数列的函数

流程：
1. Task：实现斐波那契函数
2. Worker：生成 fibonacci() 函数
3. Reviewer：审查正确性、可读性
4. 决策：APPROVE
5. 完成
```

### 示例 2：修复 Bug
```
用户：pair-coding 修复数组越界问题

流程：
1. Task：修复越界
2. Worker：添加边界检查
3. Reviewer：审查安全性、正确性
4. 决策：REVISE（缺少空值检查）
5. Worker：添加空值检查
6. Reviewer：重新审查
7. 决策：APPROVE
8. 完成
```

---

## 注意事项

1. **不要在已有大量代码的复杂项目上直接使用** - 先在小模块上测试
2. **审查是必须的** - 即使是小改动也要经过审查
3. **迭代次数不是越多越好** - 超过 3 次通常意味着需求不明确
4. **人工审查仍然是必要的** - AI 审查不能完全替代人工判断

---

## 版本历史

- v1.0 (2026-04-19) - 初始版本
