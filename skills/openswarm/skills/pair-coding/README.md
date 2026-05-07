# Pair-Coding Skill

Worker/Reviewer 对模式 - 通过多轮迭代确保代码质量。

---

## 快速开始

### 基本用法
```
pair-coding 实现一个计算斐波那契数列的函数
```

### 指定项目路径
```
pair-coding 修复登录页面的样式问题 --projectPath ~/my-project
```

### 限制迭代次数
```
pair-coding 重构用户模块 --maxIterations 2
```

---

## 工作原理

```
用户需求
   ↓
┌─────────────┐
│   Worker    │ 生成代码
│ (coding-    │
│   agent)    │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│  Reviewer   │ 审查代码
│ (Waza/      │ (正确性/安全性/
│   check)    │  可读性/可维护性)
└──────┬──────┘
       │
       ↓
   决策
   ├─ APPROVE → 完成
   ├─ REVISE → 返回 Worker
   └─ REJECT → 报告失败
       │
       ↓
  [迭代 N 次]
```

---

## 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `projectPath` | 当前目录 | 项目路径 |
| `maxIterations` | 3 | 最大迭代次数 |
| `timeout` | 600秒 | Worker 超时时间 |
| `reviewerModel` | 与 Worker 相同 | Reviewer 使用的模型 |
| `autoApprove` | false | 是否自动批准低风险修改 |

---

## 输出示例

### 成功
```markdown
## ✅ Pair-Coding 完成

### 任务摘要
实现一个计算斐波那契数列的函数

### 代码变更
- 新增：fibonacci.js

### 审查结果
- 总迭代次数：1
- 最终决策：APPROVE
- 审查发现：
  - ✅ 逻辑正确
  - ✅ 代码清晰
  - ✅ 性能良好

### 后续建议
1. 添加单元测试
2. 添加 JSDoc 注释
```

### 失败
```markdown
## ❌ Pair-Coding 失败

### 任务摘要
实现一个不可能的功能

### 失败原因
超过最大迭代次数仍未满足要求

### 尝试次数
3 / 3

### 建议
1. 简化需求
2. 分步骤实现
3. 人工介入
```

---

## 适用场景

### ✅ 推荐
- 实现新功能
- 修复复杂 bug
- 重构代码
- 性能优化

### ❌ 不推荐
- 简单的一行修改
- 文档修改
- 配置修改
- 紧急热修复

---

## 依赖

- **coding-agent** skill：用于代码生成
- **check** (Waza) skill：用于代码审查

确保这些 skill 已正确安装和配置。

---

## 故障排除

### Worker 超时
- 增加 `timeout` 参数
- 简化任务描述
- 检查项目路径是否正确

### Reviewer 失败
- 检查 Waza skill 是否正确配置
- 查看详细错误日志

### 迭代次数过多
- 检查需求是否明确
- 增加更多上下文信息
- 考虑人工介入

---

## 日志位置

- 会话日志：`memory/YYYY-MM-DD.md`
- 专门日志：`knowledge/pair-coding-log.md`

---

## 版本

- v1.0 (2026-04-19) - 初始版本

---

## 相关文档

- [SKILL.md](./SKILL.md) - 完整技能文档
- [test-cases.md](./test-cases.md) - 测试用例
