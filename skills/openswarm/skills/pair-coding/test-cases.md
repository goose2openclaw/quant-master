# Pair-Coding Skill 测试用例

**创建时间**：2026-04-19
**状态**：待执行

---

## 测试环境

- 测试目录：`/tmp/pair-coding-test`
- OpenClaw 版本：当前
- 依赖 skill：coding-agent, check (Waza)

---

## 测试用例 1：简单功能实现

### 描述
测试实现一个简单的计算斐波那契数列的函数。

### 输入
```yaml
task: "实现一个计算斐波那契数列的函数"
projectPath: "/tmp/pair-coding-test/test1"
maxIterations: 3
```

### 预期结果
- [ ] 成功生成 fibonacci 函数
- [ ] 代码逻辑正确
- [ ] 通过 Reviewer 审查
- [ ] 迭代次数 ≤ 2
- [ ] 输出格式正确

### 验证方法
```bash
# 1. 创建测试目录
mkdir -p /tmp/pair-coding-test/test1
cd /tmp/pair-coding-test/test1

# 2. 触发 pair-coding
# (通过 OpenClaw 调用)

# 3. 验证生成的代码
cat fibonacci.js  # 或其他语言

# 4. 运行测试
node -e "
  const fib = require('./fibonacci.js');
  console.assert(fib(0) === 0);
  console.assert(fib(1) === 1);
  console.assert(fib(5) === 5);
  console.assert(fib(10) === 55);
  console.log('✅ 测试通过');
"
```

---

## 测试用例 2：Bug 修复

### 描述
测试修复一个简单的数组越界问题。

### 输入
```yaml
task: "修复数组越界问题：在访问数组元素前检查索引是否有效"
projectPath: "/tmp/pair-coding-test/test2"
maxIterations: 3
```

### 初始代码
```javascript
// buggy.js
function getElement(arr, index) {
  return arr[index];  // 可能越界
}
```

### 预期结果
- [ ] 识别并修复越界问题
- [ ] 不引入新问题
- [ ] 通过 Reviewer 审查
- [ ] 添加适当的错误处理

### 验证方法
```bash
# 1. 创建测试目录和初始代码
mkdir -p /tmp/pair-coding-test/test2
cd /tmp/pair-coding-test/test2
cat > buggy.js << 'EOF'
function getElement(arr, index) {
  return arr[index];
}
module.exports = { getElement };
EOF

# 2. 触发 pair-coding
# (通过 OpenClaw 调用)

# 3. 验证修复
node -e "
  const { getElement } = require('./buggy.js');
  const arr = [1, 2, 3];

  // 正常访问
  console.assert(getElement(arr, 0) === 1);
  console.assert(getElement(arr, 2) === 3);

  // 越界访问应该安全处理
  try {
    getElement(arr, 10);
  } catch (e) {
    console.log('✅ 正确处理越界访问');
  }
"
```

---

## 测试用例 3：安全性检查

### 描述
测试 Reviewer 是否能检测到安全问题（如密码明文存储）。

### 输入
```yaml
task: "实现一个用户登录功能，验证用户名和密码"
projectPath: "/tmp/pair-coding-test/test3"
maxIterations: 3
```

### 预期结果
- [ ] Worker 生成登录代码
- [ ] Reviewer 检测到安全问题（如密码明文存储）
- [ ] 代码被 REVISE 或 REJECT
- [ ] 最终实现安全的登录（如使用 bcrypt）

### 验证方法
```bash
# 1. 创建测试目录
mkdir -p /tmp/pair-coding-test/test3
cd /tmp/pair-coding-test/test3

# 2. 触发 pair-coding
# (通过 OpenClaw 调用)

# 3. 检查最终代码
grep -i "password" *.js *.ts 2>/dev/null
# 应该没有明文密码存储
# 应该使用加密（如 bcrypt, argon2）
```

---

## 测试用例 4：迭代循环

### 描述
测试迭代循环是否正常工作。

### 输入
```yaml
task: "实现一个排序算法，要求时间复杂度优于 O(n²)"
projectPath: "/tmp/pair-coding-test/test4"
maxIterations: 2  # 限制迭代次数
```

### 预期结果
- [ ] Worker 第一次可能生成冒泡排序（O(n²)）
- [ ] Reviewer REVISE（不满足性能要求）
- [ ] Worker 生成快速排序（O(n log n)）
- [ ] Reviewer APPROVE
- [ ] 总迭代次数 ≤ maxIterations

---

## 测试用例 5：错误处理

### 描述
测试 Worker 失败时的错误处理。

### 输入
```yaml
task: "实现一个不可能的功能，例如用 JavaScript 编写操作系统内核"
projectPath: "/tmp/pair-coding-test/test5"
maxIterations: 3
timeout: 60  # 短超时
```

### 预期结果
- [ ] Worker 超时或失败
- [ ] 流程正确终止
- [ ] 输出错误信息
- [ ] 不进入无限循环

---

## 测试用例 6：输出格式验证

### 描述
测试输出格式是否符合规范。

### 输入
```yaml
task: "实现一个简单的 hello world 函数"
projectPath: "/tmp/pair-coding-test/test6"
```

### 预期结果
- [ ] 输出包含"✅ Pair-Coding 完成"或"❌ Pair-Coding 失败"
- [ ] 包含任务摘要
- [ ] 包含代码变更（如果有）
- [ ] 包含审查结果
- [ ] 格式清晰易读

---

## 执行流程

### 1. 准备环境
```bash
# 创建测试目录
mkdir -p /tmp/pair-coding-test
cd /tmp/pair-coding-test

# 创建测试结果记录文件
echo "# Pair-Coding 测试结果" > test-results.md
echo "" >> test-results.md
echo "**测试时间**: $(date)" >> test-results.md
```

### 2. 执行测试
对于每个测试用例：
1. 准备测试环境
2. 通过 OpenClaw 触发 pair-coding
3. 记录输出
4. 验证结果
5. 更新 test-results.md

### 3. 分析结果
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

### 问题 1：coding-agent skill 可能未安装
**解决**：先安装和配置 coding-agent skill

### 问题 2：check (Waza) skill 可能未配置
**解决**：先配置 Waza skill

### 问题 3：临时目录权限问题
**解决**：确保有 /tmp 的写权限

---

## 下一步

1. 执行所有测试用例
2. 记录每个测试的结果
3. 分析失败的测试用例
4. 修复发现的问题
5. 重新测试直到所有通过

---

*版本历史*：
- v1.0 (2026-04-19) - 初始版本
