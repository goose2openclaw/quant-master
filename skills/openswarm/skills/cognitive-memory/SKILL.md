---
name: cognitive-memory
description: Implement cognitive memory system with weighted retrieval algorithm combining similarity, importance, recency, and frequency. Integrate with existing ChromaDB memory system for cross-session knowledge reuse.
user-invokable: true
args:
  - name: query
    description: Search query text
    required: true
  - name: memoryType
    description: Memory type filter (belief, strategy, user_model, system_pattern, constraint)
    required: false
  - name: topK
    description: Number of results to return (default: 5)
    required: false
  - name: minScore
    description: Minimum score threshold (default: 0.3)
    required: false
  - name: outputFormat
    description: Output format: json, markdown (default: markdown)
    required: false
---

# Cognitive-Memory Skill

实现认知记忆系统，提供加权检索算法，结合相似度、重要性、近期性和访问频率。与现有记忆系统（ChromaDB）集成，实现跨会话的知识复用。

---

## 触发条件

当用户要求以下任务时触发：
- "搜索记忆"
- "查找之前的信息"
- "我之前说过..."
- "回顾历史"
- 任何需要访问历史信息的请求

---

## 加权检索算法

### 核心公式
```javascript
score = 0.55 * similarity      // 向量相似度
      + 0.20 * importance      // 重要性
      + 0.15 * recency        // 近期性（时间衰减）
      + 0.10 * frequency      // 访问频率
```

### 权重说明
- **similarity (55%)**：向量相似度是最重要的因素
- **importance (20%)**：手动标记或高引用次数的记忆更重要
- **recency (15%)**：近期的记忆更有可能相关
- **frequency (10%)**：频繁访问的记忆更重要

### 时间衰减计算
```javascript
// 以天为单位的时间衰减
function recency_score(last_accessed_days) {
  const half_life = 30;  // 半衰期 30 天
  return Math.pow(0.5, last_accessed_days / half_life);
}
```

### 访问频率计算
```javascript
// 基于访问次数的频率分数
function frequency_score(access_count) {
  const max_count = 100;
  return Math.min(access_count, max_count) / max_count;
}
```

### 重要性计算
```javascript
// 基于手动标记和引用次数
function importance_score(item) {
  let score = 0.5;  // 基础分数
  if (item.is_important) score += 0.3;
  if (item.reference_count > 10) score += 0.2;
  return Math.min(score, 1.0);
}
```

---

## 记忆类型

### belief（信念）
对事实的信念和确认的知识。

### strategy（策略）
解决问题的方法和策略。

### user_model（用户模型）
对用户偏好和习惯的理解。

### system_pattern（系统模式）
系统行为模式和规则。

### constraint（约束）
限制条件和约束。

---

## 工作流程

### 1. 查询分析
- 分析用户查询
- 识别关键词
- 确定记忆类型
- 生成查询向量

### 2. 向量检索
- 使用 ChromaDB 进行向量检索
- 获取相似度分数
- 返回候选记忆

### 3. 加权评分
- 计算综合评分
- 应用时间衰减
- 应用频率加权
- 应用重要性加权

### 4. 排序和过滤
- 按评分排序
- 应用最小评分阈值
- 限制返回数量（topK）

### 5. 更新统计
- 增加访问频率
- 更新访问时间
- 更新重要性分数

### 6. 返回结果
- 格式化结果
- 提供来源引用
- 提供置信度

---

## 与 ChromaDB 集成

### 现有系统
- **位置**：`/Users/fuigui/.openclaw/workspace/memory/chroma`
- **集合名称**：`xiao_yi_memory`
- **向量模型**：OpenAI embeddings 或本地模型

### 集成方式
```yaml
查询：
  - 使用 ChromaDB 的 query() 方法
  - 传入查询向量
  - 获取相似度分数

存储：
  - 使用现有的 ChromaDB 集合
  - 添加元数据：importance, frequency, last_accessed
  - 保持向后兼容

更新：
  - 更新记忆的元数据
  - 增加访问频率
  - 更新访问时间
```

---

## 与现有文件集成

### MEMORY.md
- 自动索引 MEMORY.md
- 提取关键信息
- 生成向量
- 存储到 ChromaDB

### memory/YYYY-MM-DD.md
- 自动索引最近的每日记忆
- 提取关键事件
- 生成向量
- 基于日期的检索

---

## 使用示例

### 基本搜索
```
cognitive-memory 搜索 Docker 配置
```

### 指定记忆类型
```
cognitive-memory 搜索 --memoryType belief 项目架构
```

### 限制返回数量
```
cognitive-memory 搜索 --topK 3 OpenSwarm
```

### JSON 输出
```
cognitive-memory 搜索 --outputFormat json
```

---

## 记忆管理

### 添加记忆
```
cognitive-memory add --type belief --important "OpenSwarm 的 Worker/Reviewer 模式有效"
```

### 标记重要
```
cognitive-memory mark --id mem-001 --important
```

### 更新记忆
```
cognitive-memory update --id mem-001 --content "更新后的内容"
```

### 删除记忆
```
cognitive-memory delete --id mem-001
```

---

## 输出格式

### Markdown 格式（默认）
```markdown
# 记忆检索结果

**查询**: "Docker 配置"
**检索时间**: 2026-04-19T16:00:00Z
**找到**: 3 条相关记忆

---

## 记忆 1 (评分: 0.85)

**类型**: belief
**时间**: 2026-04-18
**来源**: MEMORY.md#L45-L50

**内容**:
Docker 的端口配置需要注意：
- 前端：8889
- 后端：5000

**置信度**: 85%

**评分详情**:
- 相似度: 0.90 (55% = 0.50)
- 重要性: 0.80 (20% = 0.16)
- 近期性: 0.97 (15% = 0.15)
- 频率: 0.50 (10% = 0.05)
```

### JSON 格式
```json
{
  "query": "Docker 配置",
  "retrievedAt": "2026-04-19T16:00:00Z",
  "totalResults": 3,
  "results": [...]
}
```

---

## 性能考虑

### 检索速度
- 小型集合（< 1000 条）：< 1 秒
- 中型集合（1000-10000 条）：1-5 秒
- 大型集合（> 10000 条）：> 5 秒

### 优化策略
- 缓存常用查询
- 预计算时间衰减
- 批量更新统计
- 索引优化

---

## 注意事项

1. **ChromaDB 连接**：确保 ChromaDB 服务运行
2. **向量模型**：需要配置向量嵌入模型
3. **元数据管理**：保持元数据的一致性
4. **性能优化**：大型集合需要优化策略

---

## 输出位置

- 检索结果：实时返回
- 更新的统计：存储在 ChromaDB 元数据中
- 日志：`knowledge/cognitive-memory-log.md`

---

## 版本历史

- v1.0 (2026-04-19) - 初始版本
