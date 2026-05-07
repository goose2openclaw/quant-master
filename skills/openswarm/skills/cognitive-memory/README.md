# Cognitive-Memory Skill

实现认知记忆系统，提供加权检索算法，结合相似度、重要性、近期性和访问频率。

---

## 快速开始

### 基本搜索
```
cognitive-memory 搜索 Docker 配置
```

### 指定记忆类型
```
cognitive-memory 搜索 --memoryType belief 项目架构
```

### JSON 输出
```
cognitive-memory 搜索 --outputFormat json
```

---

## 加权检索算法

### 核心公式
```
score = 0.55 × similarity
      + 0.20 × importance
      + 0.15 × recency
      + 0.10 × frequency
```

### 权重说明
- **similarity (55%)**：向量相似度
- **importance (20%)**：重要性
- **recency (15%)**：近期性
- **frequency (10%)**：访问频率

---

## 记忆类型

| 类型 | 说明 | 示例 |
|------|------|------|
| belief | 信念 | "Docker 的端口配置" |
| strategy | 策略 | "使用 pair-coding skill" |
| user_model | 用户模型 | "老板喜欢简洁语气" |
| system_pattern | 系统模式 | "HEARTBEAT 每天运行" |
| constraint | 约束 | "不超过 3 次迭代" |

---

## 工作原理

```
查询分析 → 向量检索 → 加权评分 → 排序过滤 → 更新统计 → 返回结果
```

### 详细流程
1. **查询分析**：分析查询，生成向量
2. **向量检索**：使用 ChromaDB 检索相似记忆
3. **加权评分**：计算综合评分
4. **排序过滤**：按评分排序，应用阈值
5. **更新统计**：增加访问频率
6. **返回结果**：格式化结果

---

## 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `query` | - | 查询文本（必需）|
| `memoryType` | - | 记忆类型过滤 |
| `topK` | 5 | 返回结果数量 |
| `minScore` | 0.3 | 最小评分阈值 |
| `outputFormat` | markdown | 输出格式 |

---

## 输出示例

### Markdown 报告
```markdown
# 记忆检索结果

**查询**: "Docker 配置"
**找到**: 2 条相关记忆

---

## 记忆 1 (评分: 0.85)

**类型**: belief
**时间**: 2026-04-18
**来源**: MEMORY.md#L45-L50

**内容**:
Docker 的端口配置需要注意：
- 前端：8889
- 后端：5000

**评分详情**:
- 相似度: 0.90 (55% = 0.50)
- 重要性: 0.80 (20% = 0.16)
- 近期性: 0.97 (15% = 0.15)
- 频率: 0.50 (10% = 0.05)
```

### JSON 输出
```json
{
  "query": "Docker 配置",
  "retrievedAt": "2026-04-19T16:00:00Z",
  "totalResults": 2,
  "results": [...]
}
```

---

## 记忆管理

### 添加记忆
```
cognitive-memory add --type belief --important "重要信息"
```

### 标记重要
```
cognitive-memory mark --id mem-001 --important
```

### 更新记忆
```
cognitive-memory update --id mem-001 --content "更新内容"
```

### 删除记忆
```
cognitive-memory delete --id mem-001
```

---

## 与 ChromaDB 集成

### 现有系统
- **位置**：`/Users/fuigui/.openclaw/workspace/memory/chroma`
- **集合名称**：`xiao_yi_memory`

### 元数据
- `importance`：重要性（0-1）
- `frequency`：访问次数
- `last_accessed`：最后访问时间

---

## 适用场景

### ✅ 推荐
- 搜索历史信息
- 回顾项目配置
- 查找用户偏好
- 跨会话知识复用

### ❌ 不推荐
- 实时数据查询（太慢）
- 大规模批量检索
- 需要事务的场景

---

## 性能指标

| 集合大小 | 检索时间 |
|---------|---------|
| < 1000 条 | < 1 秒 |
| 1000-10000 条 | 1-5 秒 |
| > 10000 条 | > 5 秒 |

---

## 故障排除

### ChromaDB 连接失败
**解决**：确保 ChromaDB 服务运行
```bash
docker ps | grep chromadb
```

### 检索结果为空
**解决**：
- 检查查询是否合理
- 降低 minScore 阈值
- 增加 topK 数量

### 评分异常
**解决**：
- 检查时间格式
- 检查向量相似度
- 检查元数据完整性

---

## 版本

- v1.0 (2026-04-19) - 初始版本

---

## 相关文档

- [SKILL.md](./SKILL.md) - 完整技能文档
- [test-cases.md](./test-cases.md) - 测试用例
