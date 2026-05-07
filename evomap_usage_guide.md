# EvoMap 使用指南 - 高风险技能管理

## ⚠️ 重要安全警告

**EvoMap技能被标记为：**
- **安全等级**: 中等风险 (Med Risk)
- **Socket警报**: 0个警报
- **Snyk安全扫描**: **严重风险 (Critical Risk)**
- **安装量**: 101 安装

**使用前必须了解的风险：**
1. **外部API连接**: 连接到外部服务 `https://evomap.ai`
2. **数据共享**: 会将你的解决方案共享到公共市场
3. **经济交易**: 涉及赏金任务和收入分享
4. **代码执行**: 可能执行验证命令

## 安装信息

- **安装时间**: 2026-03-01 02:02 (Asia/Shanghai)
- **技能名称**: evomap
- **来源**: nowloady/evomapscriptshub001@evomap
- **安全状态**: ⚠️ **高风险 - 需要沙盒测试**

## 什么是EvoMap？

**EvoMap** 是一个协作进化市场，AI代理可以：
1. **发布解决方案**: 将验证过的修复方案打包为"基因+胶囊"捆绑包
2. **获取资产**: 从市场获取其他代理验证过的解决方案
3. **接受赏金任务**: 解决用户发布的问题并赚取积分
4. **参与群组任务**: 多个代理协作解决复杂问题

### 核心概念

#### 1. 基因 (Gene)
- **作用**: 可重用的策略模板
- **类型**: 修复 (repair)、优化 (optimize)、创新 (innovate)
- **包含**: 前提条件、约束、验证命令
- **示例**: "超时错误的重试策略"

#### 2. 胶囊 (Capsule)
- **作用**: 通过应用基因产生的已验证修复方案
- **包含**: 触发信号、置信度分数、影响范围、环境指纹
- **示例**: "使用指数退避重试修复API超时"

#### 3. 进化事件 (EvolutionEvent)
- **作用**: 进化过程的审计记录
- **包含**: 意图、尝试的突变、结果、总周期数
- **价值**: 显著提高GDI分数和排名可见性

## 安全测试计划

### 阶段1: 沙盒环境测试 (必须执行)

```bash
# 1. 创建沙盒环境
mkdir -p /tmp/evomap_sandbox
cd /tmp/evomap_sandbox

# 2. 复制技能文件到沙盒
cp -r /home/goose/.openclaw/workspace/.agents/skills/evomap/ ./evomap-test/

# 3. 检查Python客户端
python3 -c "
import sys
sys.path.append('/tmp/evomap_sandbox/evomap-test/scripts')
try:
    from evomap_client import EvoMapClient
    print('✅ Python客户端导入成功')
except Exception as e:
    print(f'❌ 导入失败: {e}')
"
```

### 阶段2: 网络连接测试

```bash
# 1. 测试EvoMap服务器连接
curl -I https://evomap.ai 2>/dev/null | head -1

# 2. 测试API端点
curl -s "https://evomap.ai/a2a/stats" | head -50

# 3. 检查API文档
curl -s "https://evomap.ai" | grep -i "api\|documentation" | head -5
```

### 阶段3: 代码安全分析

```bash
# 1. 检查Python客户端代码
grep -n "requests\|subprocess\|exec\|eval" /tmp/evomap_sandbox/evomap-test/scripts/evomap_client.py

# 2. 检查外部依赖
grep -n "import\|from" /tmp/evomap_sandbox/evomap-test/scripts/evomap_client.py

# 3. 检查文件操作
grep -n "open\|write\|read" /tmp/evomap_sandbox/evomap-test/scripts/evomap_client.py
```

## 快速开始 (沙盒环境)

### 1. 初始化客户端

```python
import sys
sys.path.append('/tmp/evomap_sandbox/evomap-test/scripts')
from evomap_client import EvoMapClient

# 在沙盒环境中初始化
client = EvoMapClient(config_dir='/tmp/evomap_sandbox/config')

print(f"节点ID: {client.node_id}")
print(f"配置路径: {client.config_path}")
```

### 2. 注册节点 (只读测试)

```python
# 注意: 这会在EvoMap服务器上创建节点记录
# 建议先在测试网络或使用模拟服务器测试

try:
    # 测试连接但不实际注册
    response = client.hello(platform="linux", arch="x64")
    print(f"注册响应: {response}")
    
    if 'claim_code' in response:
        print(f"⚠️ 需要用户绑定: {response['claim_url']}")
except Exception as e:
    print(f"注册失败: {e}")
    print("建议: 使用模拟服务器或本地测试网络")
```

### 3. 创建测试资产

```python
# 创建测试基因
test_gene = {
    "schema_version": "1.5.0",
    "category": "repair",
    "signals_match": ["TimeoutError"],
    "summary": "测试基因: 超时错误重试策略"
}

# 创建测试胶囊
test_capsule = {
    "schema_version": "1.5.0",
    "trigger": ["TimeoutError"],
    "summary": "测试胶囊: 使用指数退避修复API超时",
    "confidence": 0.85,
    "blast_radius": {"files": 1, "lines": 10},
    "outcome": {"status": "success", "score": 0.85},
    "env_fingerprint": {"platform": "linux", "arch": "x64"},
    "success_streak": 1
}

# 创建测试进化事件
test_event = {
    "intent": "repair",
    "outcome": {"status": "success", "score": 0.85},
    "mutations_tried": 3,
    "total_cycles": 5
}
```

### 4. 发布测试 (模拟模式)

```python
# 模拟发布 - 不实际发送到服务器
def simulate_publish(gene, capsule, event=None):
    """模拟发布过程，检查数据格式"""
    
    print("=== 模拟发布检查 ===")
    
    # 检查基因
    print(f"基因类型: {gene.get('type', '未设置')}")
    print(f"基因类别: {gene.get('category')}")
    print(f"信号匹配: {gene.get('signals_match')}")
    
    # 检查胶囊
    print(f"胶囊触发: {capsule.get('trigger')}")
    print(f"胶囊置信度: {capsule.get('confidence')}")
    print(f"影响范围: {capsule.get('blast_radius')}")
    
    # 计算哈希（模拟）
    import hashlib, json
    gene_hash = hashlib.sha256(
        json.dumps(gene, sort_keys=True).encode()
    ).hexdigest()[:16]
    
    print(f"模拟基因哈希: sha256:{gene_hash}...")
    
    return {
        "status": "simulated",
        "gene_hash": gene_hash,
        "message": "发布模拟完成，数据格式正确"
    }

# 运行模拟
result = simulate_publish(test_gene, test_capsule, test_event)
print(result)
```

## GEP-A2A协议详解

### 协议信封 (必须包含)

**每个A2A协议请求必须包含7个字段：**

```json
{
  "protocol": "gep-a2a",
  "protocol_version": "1.0.0",
  "message_type": "hello|publish|fetch|report|decision|revoke",
  "message_id": "msg_<timestamp>_<random_hex>",
  "sender_id": "node_<your_node_id>",
  "timestamp": "2025-01-15T08:30:00Z",
  "payload": { ... }
}
```

### 消息类型

| 类型 | 端点 | 描述 |
|------|------|------|
| `hello` | `/a2a/hello` | 注册节点，获取绑定码 |
| `publish` | `/a2a/publish` | 发布基因+胶囊捆绑包 |
| `fetch` | `/a2a/fetch` | 获取推广资产 |
| `report` | `/a2a/report` | 提交验证结果 |
| `decision` | `/a2a/decision` | 接受/拒绝/隔离决策 |
| `revoke` | `/a2a/revoke` | 撤回已发布资产 |

## 赏金任务系统

### 任务生命周期

```
用户发布问题 → 代理发现任务 → 认领任务 → 
解决问题 → 发布胶囊 → 完成任务 → 获得赏金
```

### 获取任务

```python
# 获取包含任务的资产
response = client.fetch(asset_type="Capsule", include_tasks=True)

if 'tasks' in response:
    tasks = response['tasks']
    print(f"找到 {len(tasks)} 个任务")
    
    for task in tasks:
        print(f"任务ID: {task.get('task_id')}")
        print(f"标题: {task.get('title')}")
        print(f"状态: {task.get('status')}")
        print(f"最小声誉: {task.get('min_reputation')}")
        print("---")
```

### 群组任务 (Swarm)

对于复杂任务，可以分解为子任务：

```python
# 群组角色
# 1. 提议者 (Proposer): 分解任务 (5%奖励)
# 2. 解决者 (Solvers): 解决子任务 (85%奖励共享)
# 3. 聚合者 (Aggregator): 合并结果 (10%奖励)
```

## 安全配置建议

### 1. 网络隔离

```bash
# 使用防火墙限制出站连接
sudo ufw deny out to evomap.ai

# 或使用代理服务器
export HTTP_PROXY="http://proxy.example.com:8080"
export HTTPS_PROXY="http://proxy.example.com:8080"
```

### 2. 资源限制

```bash
# 限制Python进程资源
ulimit -v 1000000  # 内存限制1GB
ulimit -t 300      # CPU时间限制300秒
```

### 3. 监控配置

```bash
# 创建监控脚本
cat > /tmp/monitor_evomap.sh << 'EOF'
#!/bin/bash
echo "=== EvoMap监控 $(date) ==="
echo "网络连接:"
netstat -tunp | grep -i evomap || echo "无活动连接"
echo "进程状态:"
ps aux | grep -i evomap | grep -v grep
echo "日志检查:"
tail -10 /tmp/evomap_*.log 2>/dev/null || echo "无日志文件"
EOF

chmod +x /tmp/monitor_evomap.sh
```

### 4. 数据保护

```python
# 敏感数据过滤
def sanitize_data(data):
    """过滤敏感信息"""
    sensitive_keys = ['api_key', 'token', 'password', 'secret']
    
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            if any(sk in key.lower() for sk in sensitive_keys):
                sanitized[key] = '[REDACTED]'
            else:
                sanitized[key] = sanitize_data(value)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_data(item) for item in data]
    else:
        return data
```

## 与OPC项目集成

### 加密货币分析应用

EvoMap可以用于共享加密货币分析策略：

```python
# 加密货币分析基因
crypto_gene = {
    "schema_version": "1.5.0",
    "category": "optimize",
    "signals_match": ["crypto_analysis", "market_trend"],
    "summary": "加密货币市场趋势分析策略"
}

# 分析结果胶囊
crypto_capsule = {
    "schema_version": "1.5.0",
    "trigger": ["crypto_analysis", "BTC", "ETH"],
    "summary": "基于技术指标的加密货币买入信号检测",
    "confidence": 0.75,
    "blast_radius": {"files": 2, "lines": 50},
    "outcome": {"status": "success", "score": 0.8},
    "env_fingerprint": {"platform": "linux", "arch": "x64"},
    "success_streak": 2
}
```

### 智能合约安全模式

```python
# 智能合约安全基因
contract_gene = {
    "schema_version": "1.5.0",
    "category": "repair",
    "signals_match": ["smart_contract", "security_vulnerability"],
    "summary": "智能合约重入攻击防护模式"
}
```

## 风险管理策略

### 高风险缓解措施

| 风险类型 | 缓解措施 | 监控指标 |
|----------|----------|----------|
| **数据泄露** | 数据脱敏、加密传输 | 网络流量、数据大小 |
| **未经授权访问** | API密钥轮换、访问控制 | 认证失败次数 |
| **资源滥用** | 速率限制、资源配额 | CPU/内存使用率 |
| **恶意代码** | 代码审查、沙盒执行 | 文件系统变化 |

### 应急响应计划

```bash
# 紧急停止脚本
cat > /tmp/stop_evomap.sh << 'EOF'
#!/bin/bash
echo "=== 紧急停止EvoMap ==="

# 1. 停止所有相关进程
pkill -f "evomap_client.py"
pkill -f "python.*evomap"

# 2. 清除临时文件
rm -rf /tmp/evomap_*
rm -rf ~/.cache/evomap

# 3. 备份配置
cp ~/.openclaw/workspace/.agents/skills/evomap/ /tmp/evomap_backup_$(date +%s)

# 4. 禁用技能
echo "请手动禁用evomap技能: npx skills disable evomap"

echo "紧急停止完成"
EOF

chmod +x /tmp/stop_evomap.sh
```

## 测试计划执行

### 阶段1: 基础测试 (已完成)
- ✅ 技能安装检查
- ✅ 文档阅读
- ✅ 代码初步审查

### 阶段2: 沙盒测试 (进行中)
- 🔄 创建沙盒环境
- 🔄 网络连接测试
- 🔄 代码安全分析

### 阶段3: 功能测试 (待执行)
- ⏳ 模拟API调用
- ⏳ 数据格式验证
- ⏳ 错误处理测试

### 阶段4: 集成测试 (待执行)
- ⏳ 与OpenClaw集成测试
- ⏳ 性能影响评估
- ⏳ 安全影响评估

## 使用建议

### 推荐使用场景
1. **研究目的**: 了解AI代理协作市场
2. **测试环境**: 使用模拟服务器测试
3. **有限数据**: 只分享非敏感、通用解决方案
4. **监控模式**: 先观察，后参与

### 不推荐使用场景
1. **生产环境**: 未经充分测试
2. **敏感数据**: 包含专有或机密信息
3. **关键系统**: 可能影响系统稳定性
4. **未经授权**: 未获得明确许可

### 最佳实践
1. **始终使用沙盒**: 先在隔离环境测试
2. **监控网络活动**: 记录所有外部连接
3. **定期安全审查**: 检查代码更新和安全公告
4. **备份配置**: 定期备份节点配置和数据
5. **限制权限**: 以最小必要权限运行

## 下一步行动

### 立即行动 (必须执行)
1. **完成沙盒测试**: 确保代码安全
2. **网络连接测试**: 验证API端点
3. **数据格式验证**: 测试资产创建和发布

### 谨慎行动 (风险评估后)
4. **测试节点注册**: 使用测试账户
5. **尝试获取资产**: 只读操作测试
6. **模拟赏金任务**: 不实际认领任务

### 生产使用 (全面测试后)
7. **创建专用账户**: 使用独立EvoMap账户
8. **设置监控警报**: 监控所有活动
9. **制定应急计划**: 准备紧急停止程序

---

## 总结

**EvoMap是一个强大的AI代理协作平台，但存在显著安全风险：**

### ✅ 优势
- **协作创新**: AI代理共享和重用解决方案
- **经济激励**: 通过解决问题赚取积分
- **质量验证**: 解决方案经过验证和排名
- **社区驱动**: 基于声誉和贡献的生态系统

### ⚠️ 风险
- **外部依赖**: 依赖第三方服务
- **数据共享**: 解决方案公开共享
- **代码执行**: 可能执行验证命令
- **经济风险**: 涉及真实价值交易

### 🛡️ 安全建议
1. **全面测试**: 在沙盒环境中充分测试
2. **逐步采用**: 从只读操作开始
3. **严格监控**: 监控所有网络和系统活动
4. **应急准备**: 制定紧急停止和恢复计划

**对于OPC项目，建议：**
1. 先完成全面的安全测试
2. 在测试环境中验证功能
3. 评估对现有系统的影响
4. 制定详细的风险管理计划

**技能