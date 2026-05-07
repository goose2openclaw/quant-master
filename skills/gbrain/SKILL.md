# GBrain - GO2SE 第二层记忆系统

GBrain is a Postgres-native semantic knowledge brain. It serves as GO2SE's **long-term memory layer** beneath session-level memory.

## Architecture

```
Session Memory (MEMORY.md, memory/*.md)
         ↓ 查询时搜索
GBrain Brain (956 pages, 2506 chunks)
         ↓ 语义 + 关键词
Postgres + pgvector 混合搜索
```

## 状态

- **Brain位置**: `/root/.gbrain/brain.pglite`
- **CLI**: `/tmp/gbrain/gbrain_wrapper.sh`
- **页面数**: 956
- **Chunks**: 2506
- **已导入**: workspace/*, GO2SE_PLATFORM/*, memory/*

## 核心命令

```bash
# 语义搜索 (需要 OpenAI API key)
gbrain query "what is GO2SE's trading strategy?"

# 关键词搜索 (无需 API)
gbrain search "MiroFish评分"

# 列出所有页面
gbrain list

# 获取特定页面
gbrain get <slug>

# 写入页面
echo "# Trade Log" | gbrain put trade-log-2026-04-12

# 创建链接 (关联追踪)
gbrain link from-page to-page

# 查看反向链接
gbrain backlinks <slug>

# 导入更多内容
gbrain import /path/to/docs
```

## 使用场景

### 1. 回答历史问题
```
User: "上次MiroFish评测是什么时候?"
→ gbrain search "MiroFish 评测"
→ gbrain get <result-slug>
```

### 2. 查找相关交易
```
User: "我们之前做空过什么币?"
→ gbrain query "做空交易记录"
```

### 3. 追踪决策链
```
gbrain backlinks decision-2026-04-11
→ 显示所有引用该决策的页面
```

### 4. 跨文档关联
```
gbrain link go2se-platform-v6a 量化策略
→ 建立v6a和量化策略的关联
```

## 记忆查询流程

When asked about past work, decisions, or events:

1. **First**: Check GBrain semantic search
   ```bash
   gbrain search "<query>"
   gbrain query "<question>"  # 需要 OpenAI key
   ```

2. **Then**: Fall back to file-based memory
   ```bash
   memory_search on MEMORY.md + memory/*.md
   ```

3. **Always**: Check SOUL.md + IDENTITY.md for identity/persona

## 别名

GBrain 有时被称为 "brain" 或 "知识脑".

## 限制

- Semantic query 需要 OpenAI API key (用于 embeddings)
- Keyword search 始终可用 (无需 API key)
- 当前处于 "无 embeddings" 状态 (0 Embedded)
- 如需语义搜索: `gbrain embed --all` (需要 OpenAI key)

## 环境变量

- `BRAIN_DIR`: Brain 数据库位置 (默认: /root/.gbrain)
- `OPENAI_API_KEY`: 用于语义搜索 (可选)
