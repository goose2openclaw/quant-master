# Code-Registry Skill 测试用例

**创建时间**：2026-04-19
**状态**：待执行

---

## 测试环境

- 测试目录：`/tmp/code-registry-test`
- OpenClaw 版本：当前

---

## 测试用例 1：简单项目扫描

### 描述
测试扫描包含 3 个 JavaScript 文件的简单项目。

### 准备
```bash
mkdir -p /tmp/code-registry-test/test1
cd /tmp/code-registry-test/test1

# 创建文件
cat > fibonacci.js << 'EOF'
function fibonacci(n) {
  if (n <= 1) return n;
  return fibonacci(n - 1) + fibonacci(n - 2);
}
module.exports = { fibonacci };
EOF

cat > utils.js << 'EOF'
function add(a, b) {
  return a + b;
}

function multiply(a, b) {
  return a * b;
}

module.exports = { add, multiply };
EOF

cat > app.js << 'EOF'
const { fibonacci } = require('./fibonacci.js');
const { add, multiply } = require('./utils.js');

console.log(fibonacci(10));
console.log(add(5, 3));
console.log(multiply(4, 3));
EOF
```

### 预期结果
- [ ] 扫描 3 个文件
- [ ] 识别 4 个函数（fibonacci, add, multiply, 可能还有模块导出）
- [ ] 计算每个函数的复杂度
- [ ] 生成完整的报告

### 验证
```bash
# 检查 JSON 输出
cat knowledge/code-registry.json | grep '"totalFiles"'
cat knowledge/code-registry.json | grep '"totalEntities"'

# 检查 Markdown 报告
cat knowledge/code-registry-report.md | grep "Total Files"
cat knowledge/code-registry-report.md | grep "Summary"
```

---

## 测试用例 2：BS 检测

### 描述
测试检测各种 BS 问题。

### 准备
```bash
mkdir -p /tmp/code-registry-test/test2
cd /tmp/code-registry-test/test2

# 创建包含 BS 问题的代码
cat > buggy.js << 'EOF'
// CRITICAL: 硬编码密钥
const API_KEY = 'sk-1234567890abcdef';

// HIGH: 空的 catch 块
function dangerousOperation() {
  try {
    doSomething();
  } catch (error) {
    // 空的 catch 块
  }
}

// HIGH: console.log 未清理
function debugFunction(x) {
  console.log('Debug:', x);
  return x * 2;
}

// MEDIUM: 过长函数
function veryLongFunction(a, b, c, d, e, f, g, h) {
  // 50+ 行函数
  let result = 0;
  for (let i = 0; i < 100; i++) {
    for (let j = 0; j < 100; j++) {
      for (let k = 0; k < 100; k++) {
        result += a * i + b * j + c * k;
        // ... 更多代码
      }
    }
  }
  return result;
}

// LOW: 未使用的变量
const unusedVariable = 'not used';

function usedFunction() {
  return 'used';
}

module.exports = { dangerousOperation, debugFunction, veryLongFunction, usedFunction };
EOF
```

### 预期结果
- [ ] 检测到硬编码密钥（CRITICAL）
- [ ] 检测到空的 catch 块（HIGH）
- [ ] 检测到 console.log（HIGH）
- [ ] 检测到过长函数（MEDIUM）
- [ ] 检测到未使用的变量（LOW）
- [ ] 正确分类严重级别
- [ ] 提供修复建议

### 验证
```bash
# 检查 BS 问题数量
cat knowledge/code-registry.json | grep '"CRITICAL"'
cat knowledge/code-registry.json | grep '"HIGH"'
cat knowledge/code-registry.json | grep '"MEDIUM"'
cat knowledge/code-registry.json | grep '"LOW"'

# 检查具体问题
cat knowledge/code-registry-report.md | grep "hardcoded"
cat knowledge/code-registry-report.md | grep "empty catch"
cat knowledge/code-registry-report.md | grep "console.log"
```

---

## 测试用例 3：复杂度计算

### 描述
测试不同复杂度函数的复杂度计算。

### 准备
```bash
mkdir -p /tmp/code-registry-test/test3
cd /tmp/code-registry-test/test3

cat > complexity.js << 'EOF'
// 简单函数（圈复杂度 1）
function simple() {
  return 1 + 1;
}

// 中等函数（圈复杂度 3）
function medium(x) {
  if (x > 0) {
    return x;
  } else if (x < 0) {
    return -x;
  }
  return 0;
}

// 复杂函数（圈复杂度 10+）
function complex(a, b, c) {
  if (a > 0) {
    if (b > 0) {
      if (c > 0) {
        return a + b + c;
      } else {
        return a + b;
      }
    } else {
      if (c > 0) {
        return a + c;
      } else {
        return a;
      }
    }
  } else {
    if (b > 0) {
      if (c > 0) {
        return b + c;
      } else {
        return b;
      }
    } else {
      if (c > 0) {
        return c;
      } else {
        return 0;
      }
    }
  }
}

module.exports = { simple, medium, complex };
EOF
```

### 预期结果
- [ ] simple: 圈复杂度 1, 综合评分 ~98
- [ ] medium: 圈复杂度 3, 综合评分 ~94
- [ ] complex: 圈复杂度 10+, 综合评分 < 80

### 验证
```bash
# 检查复杂度
cat knowledge/code-registry.json | grep -A 5 '"name": "simple"'
cat knowledge/code-registry.json | grep -A 5 '"name": "medium"'
cat knowledge/code-registry.json | grep -A 5 '"name": "complex"'
```

---

## 测试用例 4：排除目录

### 描述
测试排除目录功能。

### 准备
```bash
mkdir -p /tmp/code-registry-test/test4
cd /tmp/code-registry-test/test4

# 创建主目录文件
cat > main.js << 'EOF'
function main() {
  console.log('Main');
}
module.exports = { main };
EOF

# 创建 node_modules 目录
mkdir -p node_modules/library
cat > node_modules/library/index.js << 'EOF'
function libraryFunction() {
  console.log('Library');
}
module.exports = { libraryFunction };
EOF

# 创建 .git 目录
mkdir -p .git/hooks
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
echo "Pre-commit hook"
EOF
```

### 预期结果
- [ ] 只扫描 main.js
- [ ] 不扫描 node_modules 目录
- [ ] 不扫描 .git 目录
- [ ] totalFiles = 1

### 验证
```bash
cat knowledge/code-registry.json | grep '"totalFiles"'
# 应该是 1

cat knowledge/code-registry-report.md
# 不应该包含 library 或 pre-commit
```

---

## 测试用例 5：多语言支持

### 描述
测试扫描多种语言的文件。

### 准备
```bash
mkdir -p /tmp/code-registry-test/test5
cd /tmp/code-registry-test/test5

# JavaScript
cat > app.js << 'EOF'
function jsFunction() {
  return 'JS';
}
EOF

# Python
cat > app.py << 'EOF'
def python_function():
    return 'Python'
EOF

# Java
cat > App.java << 'EOF'
public class App {
    public static String javaFunction() {
        return "Java";
    }
}
EOF
```

### 预期结果
- [ ] 识别 3 个文件
- [ ] 识别 3 个函数
- [ ] 正确处理不同语言的语法

### 验证
```bash
cat knowledge/code-registry.json | grep '"totalFiles"'
# 应该是 3
```

---

## 测试用例 6：输出格式

### 描述
测试不同输出格式。

### 预期结果
- [ ] JSON 格式：有效的 JSON，包含所有必需字段
- [ ] Markdown 格式：结构清晰，包含表格和列表
- [ ] 两种格式包含相同的信息

### 验证
```bash
# JSON 格式
code-registry --outputFormat json
python -m json.tool knowledge/code-registry.json > /dev/null
# 应该没有错误

# Markdown 格式
code-registry --outputFormat markdown
cat knowledge/code-registry-report.md | grep "# Code Registry Report"
cat knowledge/code-registry-report.md | grep "## Summary"
```

---

## 执行流程

### 1. 准备环境
```bash
mkdir -p /tmp/code-registry-test
cd /tmp/code-registry-test

# 创建测试结果记录
echo "# Code-Registry 测试结果" > test-results.md
echo "" >> test-results.md
echo "**测试时间**: $(date)" >> test-results.md
```

### 2. 执行测试
对于每个测试用例：
1. 准备测试环境
2. 触发 code-registry skill
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

### 问题 1：AST 解析器依赖
**解决**：使用内置的简单解析器，或要求用户安装对应语言的解析器

### 问题 2：大型项目内存
**解决**：分批扫描，使用流式处理

### 问题 3：不同语言的复杂度计算
**解决**：实现语言特定的复杂度算法

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
