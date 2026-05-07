# Code-Registry Skill

扫描项目代码，注册所有实体，进行静态分析和复杂度评分，检测坏代码模式。

---

## 快速开始

### 基本用法
```
code-registry
```

### 指定路径
```
code-registry --path ~/my-project
```

### JSON 输出
```
code-registry --outputFormat json
```

---

## 工作原理

```
项目路径
   ↓
┌─────────────────────┐
│   扫描文件          │ 遍历目录，收集源文件
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│   解析代码          │ 提取实体（函数、类、接口）
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│   计算复杂度        │ 圈复杂度 + 认知复杂度
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│   BS 检测           │ 检测坏代码模式
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│   生成报告          │ JSON + Markdown
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│   保存注册表        │ knowledge/code-registry.json
└─────────────────────┘
```

---

## BS 检测规则

### CRITICAL（严重）
- 硬编码密钥（API key, password, token）
- SQL 注入
- 命令注入
- eval/eval-like 函数

### HIGH（高）
- 空的 catch 块
- console.log 未清理
- any 类型滥用
- 未处理的 Promise

### MEDIUM（中）
- 过长函数（> 50 行）
- 参数过多（> 5 个）
- 嵌套过深（> 4 层）
- 重复代码

### LOW（低）
- 未使用的变量
- 未使用的导入
- 命名不规范
- 缺少注释

---

## 复杂度评分

| 评分 | 等级 | 说明 |
|------|------|------|
| 90-100 | 优秀 | 代码简洁，易于维护 |
| 70-89 | 良好 | 代码质量较好 |
| 50-69 | 一般 | 有一定复杂度，建议优化 |
| < 50 | 需要重构 | 复杂度过高，建议重构 |

---

## 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `path` | 当前目录 | 项目路径 |
| `fileTypes` | js, ts, py, java, go, rs, cpp, cs | 文件类型 |
| `excludeDirs` | node_modules, .git, dist, build | 排除目录 |
| `complexityThreshold` | 50 | 复杂度警告阈值 |
| `outputFormat` | markdown | 输出格式 |

---

## 输出示例

### Markdown 报告
```markdown
# Code Registry Report

## Summary
- **Total Files**: 10
- **Total Entities**: 45
- **Average Complexity**: 35
- **BS Issues**: 23 (CRITICAL: 0, HIGH: 3, MEDIUM: 12, LOW: 8)

## High Risk Entities
| Entity | File | Complexity | BS Issues |
|--------|------|-----------|-----------|
| `processData` | app.js | 85 | 2 (HIGH) |
| `parseConfig` | config.js | 72 | 1 (HIGH) |

## BS Issues by Severity
...
```

### JSON 输出
```json
{
  "projectPath": "/path/to/project",
  "scanTime": "2026-04-19T15:00:00Z",
  "summary": {
    "totalFiles": 10,
    "totalEntities": 45,
    ...
  },
  "entities": [...],
  "bsIssues": [...]
}
```

---

## 适用场景

### ✅ 推荐
- 建立代码质量基线
- 定期代码审查
- 重构前分析
- 技术债检测
- 新项目初始化

### ❌ 不推荐
- 实时代码分析（太慢）
- 非常大的项目（考虑分批）
- 只有一个文件的小项目（收益不大）

---

## 输出位置

- **注册表**：`knowledge/code-registry.json`
- **报告**：`knowledge/code-registry-report.md`
- **日志**：`knowledge/code-registry-log.md`

---

## 故障排除

### 扫描太慢
- 增加 `excludeDirs`
- 限制 `fileTypes`
- 分批扫描大型项目

### 内存不足
- 减少扫描文件数
- 使用增量扫描
- 分批处理

### 解析失败
- 检查文件语法
- 确认文件类型支持
- 查看详细错误日志

---

## 与其他 Skill 集成

### pair-coding
pair-coding 完成后自动调用 code-registry，注册新代码并检测 BS 问题。

### HEARTBEAT
HEARTBEAT 定期调用 code-registry，跟踪代码变化和质量趋势。

---

## 版本

- v1.0 (2026-04-19) - 初始版本

---

## 相关文档

- [SKILL.md](./SKILL.md) - 完整技能文档
- [test-cases.md](./test-cases.md) - 测试用例
