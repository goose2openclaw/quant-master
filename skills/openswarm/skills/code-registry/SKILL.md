---
name: code-registry
description: Scan project code, register all entities (functions, classes, types), perform static analysis and complexity scoring, detect bad code smells (BS patterns). Establish code quality baseline.
user-invokable: true
args:
  - name: path
    description: Project path (default: current directory)
    required: false
  - name: fileTypes
    description: File types to scan (default: js, ts, py, java, go, rs, cpp, cs)
    required: false
  - name: excludeDirs
    description: Directories to exclude (default: node_modules, .git, dist, build)
    required: false
  - name: complexityThreshold
    description: Complexity warning threshold (default: 50)
    required: false
  - name: outputFormat
    description: Output format: json, markdown (default: markdown)
    required: false
---

# Code-Registry Skill

扫描项目代码，注册所有实体（函数、类、类型），进行静态分析和复杂度评分，检测坏代码模式（BS）。建立代码质量基线。

---

## 触发条件

当用户要求以下任务时触发：
- "扫描项目代码"
- "检查代码质量"
- "检测坏代码模式"
- "分析代码复杂度"
- "建立代码基线"

---

## 工作流程

### 1. 扫描项目
1. 识别项目路径
2. 确定支持的文件类型
3. 遍历目录，收集源文件
4. 忽略排除目录（node_modules, .git, dist, build）

### 2. 解析代码
1. 根据文件类型选择解析器
2. 提取实体（函数、类、接口等）
3. 记录位置（行号、列号）
4. 提取参数和返回值

### 3. 计算复杂度
1. 圈复杂度（Cyclomatic Complexity）
2. 认知复杂度（Cognitive Complexity）
3. 综合评分（0-100）

### 4. BS 检测
1. 应用 BS 规则
2. 记录发现的问题
3. 分配严重级别（CRITICAL, HIGH, MEDIUM, LOW）
4. 生成修复建议

### 5. 生成报告
1. 实体统计
2. 复杂度分布
3. BS 问题汇总
4. 高风险实体
5. 修复建议

### 6. 保存注册表
1. 保存到 `knowledge/code-registry.json`
2. 更新 `memory-index.md`

---

## BS 检测规则

### CRITICAL（严重）
- **硬编码密钥**：检测 API key、password、token
- **SQL 注入**：检测字符串拼接的 SQL 查询
- **命令注入**：检测直接拼接的 shell 命令
- **eval/eval-like**：检测 eval(), exec() 等危险函数

### HIGH（高）
- **空 catch 块**：捕获异常但不处理
- **console.log**：调试代码未清理
- **any 类型滥用**：TypeScript 中过度使用 any
- **未处理的 Promise**：没有 .catch() 或 try/catch

### MEDIUM（中）
- **过长函数**：超过 50 行
- **参数过多**：超过 5 个参数
- **嵌套过深**：超过 4 层嵌套
- **重复代码**：相似的代码块

### LOW（低）
- **未使用的变量**：声明但未使用
- **未使用的导入**：导入但未使用
- **命名不规范**：不符合约定
- **缺少注释**：复杂函数没有注释

---

## 复杂度评分算法

### 圈复杂度
```javascript
// 每个决策点 +1
// 决策点：if, for, while, case, catch, &&, ||, ?:
```

### 认知复杂度
```javascript
// 嵌套增加复杂度：+1（每层）
// 逻辑操作符增加复杂度：+1
// break/continue 增加：+1
```

### 综合评分（0-100）
```javascript
score = 100 - (圈复杂度 * 2 + 认知复杂度 * 1.5)
// 90-100：优秀
// 70-89：良好
// 50-69：一般
// < 50：需要重构
```

---

## 输出格式

### Markdown 格式（默认）
```markdown
# Code Registry Report

## Summary
- **Total Files**: X
- **Total Entities**: Y
- **Average Complexity**: Z
- **BS Issues**: A (CRITICAL: 0, HIGH: B, MEDIUM: C, LOW: D)

## High Risk Entities
| Entity | File | Complexity | BS Issues |
|--------|------|-----------|-----------|
...

## BS Issues by Severity
...

## Recommendations
...
```

### JSON 格式
```json
{
  "projectPath": "/path/to/project",
  "scanTime": "2026-04-19T15:00:00Z",
  "summary": { ... },
  "entities": [ ... ],
  "bsIssues": [ ... ]
}
```

---

## 使用示例

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

### 自定义文件类型
```
code-registry --fileTypes js,ts,tsx
```

---

## 依赖

- 文件系统访问
- AST 解析器（根据语言）
- 文本处理

---

## 注意事项

1. **首次扫描可能较慢**：需要解析所有文件
2. **增量扫描**：后续扫描只检查变更的文件
3. **排除目录**：自动排除 node_modules, .git, dist, build
4. **大型项目**：考虑分批扫描或增加超时时间

---

## 输出位置

- 注册表：`knowledge/code-registry.json`
- 报告：`knowledge/code-registry-report.md`
- 日志：`knowledge/code-registry-log.md`

---

## 版本历史

- v1.0 (2026-04-19) - 初始版本
