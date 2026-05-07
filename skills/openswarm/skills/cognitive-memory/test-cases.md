# Cognitive-Memory Skill 测试用例

**创建时间**：2026-04-19
**状态**：待执行

---

## 测试环境

- 测试目录：`/tmp/cognitive-memory-test`
- OpenClaw 版本：当前
- ChromaDB：需要运行

---

## 测试用例 1：基本检索

### 描述
测试基本的记忆检索功能。

### 准备
```bash
# 添加测试记忆
cognitive-memory add --type belief "Docker 的端口配置：前端 8889，后端 5000"
cognitive-memory add --type strategy "使用 pair-coding skill 生成代码"
cognitive-memory add --type user_model "老板喜欢简洁语气"
```

### 执行
```bash
cognitive-memory 搜索 "Docker 配置"
```

### 预期结果
- [ ] 找到相关记忆
- [ ] 按评分排序
- [ ] 包含评分详情
- [ ] 提供来源引用

### 验证
```bash
# 检查返回结果数量
grep "找到:" output.md
# 应该包含数字

# 检查评分详情
grep "相似度:" output.md
grep "重要性:" output.md
grep "近期性:" output.md
grep "频率:" output.md
```

---

## 测试用例 2：加权算法验证

### 描述
测试加权检索算法的正确性。

### 准备
```bash
# 添加测试记忆
cognitive-memory add --type belief --important "重要配置：数据库密码" --id mem-001
cognitive-memory add --type belief "普通配置：超时时间" --id mem-002
cognitive-memory add --type belief "旧记忆：2024年1月的配置" --id mem-003
```

### 执行
```bash
# 访问 mem-001 多次（增加频率）
cognitive-memory 搜索 "配置"
cognitive-memory 搜索 "配置"
cognitive-memory 搜索 "配置"

# 再次搜索
cognitive-memory 搜索 "配置"
```

### 预期结果
- [ ] mem-001 评分最高（重要 + 高频率）
- [ ] mem-002 评分中等
- [ ] mem-003 评分较低（时间衰减）

### 验证
```bash
# 检查评分排序
grep "评分:" output.md | head -1
# 应该是 mem-001（最高分）
```

---

## 测试用例 3：记忆类型过滤

### 描述
测试按记忆类型过滤的功能。

### 准备
```bash
cognitive-memory add --type belief "事实：Docker 配置"
cognitive-memory add --type strategy "策略：使用 pair-coding"
cognitive-memory add --type user_model "用户：喜欢简洁"
cognitive-memory add --type system_pattern "系统：HEARTBEAT 运行"
cognitive-memory add --type constraint "约束：不超过 3 次迭代"
```

### 执行
```bash
cognitive-memory 搜索 --memoryType strategy "代码"
```

### 预期结果
- [ ] 只返回 strategy 类型的记忆
- [ ] 不包含其他类型
- [ ] 找到 "使用 pair-coding"

### 验证
```bash
# 检查类型
grep "类型:" output.md
# 应该只有 "strategy"
```

---

## 测试用例 4：时间衰减

### 描述
测试时间衰减对评分的影响。

### 准备
```bash
# 模拟旧记忆
cognitive-memory add --type belief "2024年1月：旧的配置" --date "2024-01-01"
cognitive-memory add --type belief "2026年4月：新的配置"
```

### 执行
```bash
cognitive-memory 搜索 "配置"
```

### 预期结果
- [ ] 新记忆评分更高（recency 分数高）
- [ ] 旧记忆评分较低（recency 分数低）
- [ ] recency 分数正确显示

### 验证
```bash
# 检查近期性分数
grep "近期性:" output.md
# 新记忆应该 > 旧记忆
```

---

## 测试用例 5：JSON 输出格式

### 描述
测试 JSON 输出格式的正确性。

### 执行
```bash
cognitive-memory 搜索 --outputFormat json "Docker"
```

### 预期结果
- [ ] 输出有效的 JSON
- [ ] 包含所有必需字段
- [ ] 评分详情完整

### 验证
```bash
# 验证 JSON 格式
python -m json.tool output.json > /dev/null
# 退出码应该为 0

# 检查字段
python -c "
import json
data = json.load(open('output.json'))
assert 'query' in data
assert 'results' in data
assert 'totalResults' in data
for result in data['results']:
    assert 'score' in result
    assert 'scoreDetails' in result
    assert 'similarity' in result['scoreDetails']
"
```

---

## 测试用例 6：记忆管理

### 描述
测试记忆的添加、标记、更新和删除。

### 执行
```bash
# 添加记忆
cognitive-memory add --type belief "测试记忆" --id test-001

# 标记重要
cognitive-memory mark --id test-001 --important

# 更新记忆
cognitive-memory update --id test-001 --content "更新后的测试记忆"

# 删除记忆
cognitive-memory delete --id test-001

# 验证删除
cognitive-memory 搜索 "测试记忆"
# 应该找不到
```

### 预期结果
- [ ] 成功添加记忆
- [ ] 成功标记重要
- [ ] 成功更新内容
- [ ] 成功删除记忆
- [ ] 搜索时找不到删除的记忆

---

## 执行流程

### 1. 准备环境
```bash
mkdir -p /tmp/cognitive-memory-test
cd /tmp/cognitive-memory-test

# 确保 ChromaDB 运行
docker ps | grep chromadb

# 如果未运行，启动 ChromaDB
docker run -d -p 8000:8000 chromadb/chroma
```

### 2. 初始化记忆库
```bash
# 连接现有 ChromaDB
# 集合名称：xiao_yi_memory
```

### 3. 执行测试
对于每个测试用例：
1. 准备测试数据
2. 触发 cognitive-memory skill
3. 记录输出
4. 验证结果
5. 更新 test-results.md

### 4. 分析结果
```bash
# 统计通过率
echo -e "\n## 测试统计" >> test-results.md
echo "- 总测试数：6" >> test-results.md
echo "- 通过数：X" >> test-results.md
echo "- 失败数：Y" >> test-results.md
echo "- 通过率：Z%" >> test-results.md
```

---

## 已知问题

### 问题 1：ChromaDB 连接
**解决**：确保 ChromaDB 服务运行，端口 8000

### 问题 2：向量模型
**解决**：使用 OpenAI embeddings 或本地模型

### 问题 3：时间计算
**解决**：使用标准时间格式，统一时区

---

## 下一步

1. 启动 ChromaDB
2. 初始化记忆库
3. 执行所有测试用例
4. 记录每个测试的结果
5. 分析失败的测试用例
6. 修复发现的问题
7. 重新测试直到所有通过

---

*版本历史*：
- v1.0 (2026-04-19) - 初始版本
