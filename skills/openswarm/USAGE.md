# OpenSwarm 龙虾版 - 使用说明

## 快速开始

### 1. 安装

```bash
# 克隆项目
git clone https://github.com/your-username/openswarm-lobster-version.git
cd openswarm-lobster-version

# 一键安装
chmod +x install.sh
./install.sh
```

### 2. 重启 OpenClaw

安装后需要重启 OpenClaw 让 skills 生效。

### 3. 开始使用

---

## 使用 Skills

### 1. pair-coding - Worker/Reviewer 对模式

**用途**：生成代码时自动进行安全检查和性能验证

**使用方法**：
```
你：帮我写一个函数，计算斐波那契数列
```

**工作流程**：
1. Worker 生成代码
2. Reviewer 审查代码
3. 自动检测安全问题
4. 自动验证性能
5. 如果有问题，自动修复
6. 返回最终代码

**示例输出**：
```
Worker 生成了斐波那契函数
Reviewer 检查通过：
✓ 安全检查：无安全问题
✓ 性能验证：O(n) 时间复杂度
✓ 代码质量：符合规范

最终代码：
function fibonacci(n) {
  if (n <= 1) return n;
  return fibonacci(n - 1) + fibonacci(n - 2);
}
```

**触发条件**：
- 要求生成/修改代码
- 请求代码审查
- 询问代码安全性或性能

---

### 2. code-registry - 代码注册表 + BS 检测器

**用途**：扫描代码库，检测坏代码模式（Bullshit），计算复杂度

**使用方法**：
```
你：扫描我的项目，检查代码质量
```

**工作流程**：
1. 扫描项目目录
2. 识别所有代码实体
3. 检测 BS 问题
4. 计算复杂度
5. 生成报告

**BS 问题分级**：
- **CRITICAL**（严重）：硬编码密钥、安全问题
- **HIGH**（高）：空 catch 块、console.log
- **MEDIUM**（中）：参数过多、函数过长
- **LOW**（低）：未使用的变量

**示例输出**：
```markdown
# 代码质量报告

**项目**: /path/to/project
**扫描时间**: 2026-04-19

## 摘要
- **总文件数**: 10
- **总实体数**: 25
- **BS 问题**: 3

## BS 问题

### CRITICAL (1)
- app.js:15 - 硬编码密钥

### HIGH (2)
- utils.js:42 - 空 catch 块
- main.js:8 - console.log

## 复杂度分析
- 平均分数: 78
- 最高分数: 95
- 最低分数: 45
```

**触发条件**：
- 要求扫描项目
- 询问代码质量
- 检查技术债

---

### 3. cognitive-memory - 认知记忆系统

**用途**：智能检索记忆，结合相似度、重要性、近期性、频率

**使用方法**：
```
你：搜索我之前提到的 Docker 配置
```

**工作流程**：
1. 分析查询
2. 使用 ChromaDB 检索
3. 计算加权分数
4. 排序和过滤
5. 返回结果

**加权算法**：
```
score = 0.55 × 相似度
      + 0.20 × 重要性
      + 0.15 × 近期性
      + 0.10 × 频率
```

**示例输出**：
```markdown
# 记忆检索结果

**查询**: "Docker 配置"
**找到**: 2 条相关记忆

## 记忆 1 (评分: 0.85)

**类型**: belief
**时间**: 2026-04-18
**来源**: MEMORY.md#L45-L50

**内容**:
Docker 的端口配置：
- 前端：8889
- 后端：5000

**评分详情**:
- 相似度: 0.90 (55% = 0.50)
- 重要性: 0.80 (20% = 0.16)
- 近期性: 0.97 (15% = 0.15)
- 频率: 0.50 (10% = 0.05)
```

**触发条件**：
- 搜索历史信息
- 查找之前的内容
- 回顾记忆

---

## HEARTBEAT 自动化

HEARTBEAT 会自动执行以下任务：

### 每日任务
- **09:00** - 代码质量检查
- **12:00** - 系统状态检查
- **18:00** - 记忆更新
- **23:59** - 每日摘要

### 每周任务
- **周一 10:00** - 技术债汇总
- **周日 20:00** - 记忆清理
- **周日 23:59** - 周摘要

### 每月任务
- **1 日 09:00** - 系统优化
- **15 日 10:00** - 技能评估

### 配置 HEARTBEAT

编辑 `~/.openclaw/workspace/HEARTBEAT.md`：
```yaml
heartbeat:
  enabled: true
  timezone: "Asia/Shanghai"

daily_tasks:
  - name: code-quality-check
    time: "09:00"
    skill: code-registry
    # ...
```

---

## 典型工作流

### 场景 1：开发新功能

```
你：帮我写一个用户认证系统

# 自动执行：
1. pair-coding 生成代码
2. code-registry 扫描代码
3. cognitive-memory 检索相关记忆
4. Reviewer 审查代码
5. 返回高质量的代码

输出：
✅ 生成了用户认证代码
✅ 安全检查通过
✅ 性能验证通过
✅ 代码质量报告已生成
```

### 场景 2：代码审查

```
你：帮我审查这个 PR

# 自动执行：
1. 使用 Waza/check 审查代码
2. code-registry 检测 BS 问题
3. pair-coding Reviewer 模式
4. 生成审查报告

输出：
✅ 代码审查完成
✅ 发现 2 个 HIGH 级别问题
✅ 建议修复方案已提供
```

### 场景 3：查找信息

```
你：我记得之前配置过什么，帮我找一下

# 自动执行：
1. cognitive-memory 搜索记忆
2. 加权检索返回最相关的结果
3. 提供来源和置信度

输出：
✅ 找到 3 条相关记忆
✅ 最高评分：0.85
✅ 来源：MEMORY.md
```

---

## 进阶使用

### 自定义 BS 规则

编辑 `~/.agents/skills/code-registry/SKILL.md`，添加自定义规则：

```markdown
### 自定义规则
```javascript
if (code.includes('TODO')) {
  return {
    severity: 'MEDIUM',
    message: '包含 TODO 注释'
  };
}
```

### 调整记忆权重

编辑 `~/.agents/skills/cognitive-memory/SKILL.md`，修改权重：

```markdown
### 加权检索算法
```javascript
score = 0.60 * similarity  // 增加相似度权重
      + 0.20 * importance
      + 0.10 * recency
      + 0.10 * frequency
```

### 添加自动化任务

编辑 `~/.openclaw/workspace/HEARTBEAT.md`，添加任务：

```yaml
daily_tasks:
  - name: my-task
    time: "10:00"
    action: my-action
```

---

## 故障排除

### Skill 不生效

**问题**：安装后 skill 不生效

**解决**：
```bash
# 1. 确认安装成功
ls ~/.agents/skills/pair-coding

# 2. 重启 OpenClaw
# 3. 检查日志
tail -f ~/.openclaw/logs/*.log
```

### ChromaDB 连接失败

**问题**：cognitive-memory 提示 ChromaDB 连接失败

**解决**：
```bash
# 启动 ChromaDB
docker run -d -p 8000:8000 chromadb/chroma

# 验证连接
curl http://localhost:8000/api/v1/heartbeat
```

### HEARTBEAT 不执行

**问题**：HEARTBEAT 任务不执行

**解决**：
```bash
# 1. 检查配置
cat ~/.openclaw/workspace/HEARTBEAT.md

# 2. 启用 HEARTBEAT
# 编辑 HEARTBEAT.md，设置 enabled: true

# 3. 检查日志
cat ~/.openclaw/workspace/knowledge/heartbeat.log
```

---

## 性能优化

### 大型项目扫描

对于大型项目，建议：
```yaml
# 在 code-registry 调用时指定排除目录
code-registry --path ~/my-project --exclude node_modules,dist,build
```

### 记忆检索优化

对于大量记忆，建议：
```yaml
# 限制返回数量
cognitive-memory --topK 3 "搜索内容"

# 提高最小评分阈值
cognitive-memory --minScore 0.5 "搜索内容"
```

---

## 更多帮助

- **文档**：`docs/` 目录
- **Skill 文档**：`skills/<name>/README.md`
- **测试用例**：`skills/<name>/test-cases.md`
- **GitHub Issues**：https://github.com/your-username/openswarm-lobster-version/issues

---

**Happy Coding! 🌊**
