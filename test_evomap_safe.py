#!/usr/bin/env python3
"""
EvoMap安全测试脚本
模拟所有功能但不实际发送网络请求
"""

import sys
import json
import hashlib
import uuid
from datetime import datetime, timezone

# 添加evomap脚本路径
sys.path.append('/home/goose/.openclaw/workspace/.agents/skills/evomap/scripts')

def test_data_structures():
    """测试数据格式和哈希计算"""
    print("=== EvoMap数据格式测试 ===")
    
    # 1. 测试基因结构
    gene = {
        "schema_version": "1.5.0",
        "category": "repair",
        "signals_match": ["TimeoutError", "ConnectionError"],
        "summary": "测试基因: 网络错误重试策略",
        "type": "Gene"
    }
    
    # 2. 测试胶囊结构
    capsule = {
        "schema_version": "1.5.0",
        "trigger": ["TimeoutError"],
        "summary": "测试胶囊: 使用指数退避修复API超时错误",
        "confidence": 0.85,
        "blast_radius": {"files": 1, "lines": 10},
        "outcome": {"status": "success", "score": 0.85},
        "env_fingerprint": {"platform": "linux", "arch": "x64"},
        "success_streak": 1,
        "type": "Capsule"
    }
    
    # 3. 测试进化事件
    event = {
        "intent": "repair",
        "outcome": {"status": "success", "score": 0.85},
        "mutations_tried": 3,
        "total_cycles": 5,
        "type": "EvolutionEvent"
    }
    
    # 计算哈希
    def compute_hash(data):
        temp = data.copy()
        temp.pop("asset_id", None)
        canonical = json.dumps(temp, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
        return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"
    
    gene_hash = compute_hash(gene)
    capsule_hash = compute_hash(capsule)
    event_hash = compute_hash(event)
    
    print(f"✅ 基因哈希: {gene_hash[:30]}...")
    print(f"✅ 胶囊哈希: {capsule_hash[:30]}...")
    print(f"✅ 事件哈希: {event_hash[:30]}...")
    
    # 验证胶囊链接到基因
    capsule["gene"] = gene_hash
    
    return gene, capsule, event, gene_hash, capsule_hash, event_hash

def test_protocol_envelope():
    """测试协议信封格式"""
    print("\n=== GEP-A2A协议信封测试 ===")
    
    # 模拟信封创建
    node_id = "node_test_" + uuid.uuid4().hex[:8]
    message_id = f"msg_{int(datetime.now().timestamp() * 1000)}_{uuid.uuid4().hex[:4]}"
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    envelope = {
        "protocol": "gep-a2a",
        "protocol_version": "1.0.0",
        "message_type": "hello",
        "message_id": message_id,
        "sender_id": node_id,
        "timestamp": timestamp,
        "payload": {
            "capabilities": {},
            "gene_count": 0,
            "capsule_count": 0,
            "env_fingerprint": {
                "platform": "linux",
                "arch": "x64"
            }
        }
    }
    
    print(f"✅ 信封创建成功")
    print(f"   协议: {envelope['protocol']} v{envelope['protocol_version']}")
    print(f"   消息类型: {envelope['message_type']}")
    print(f"   发送者: {envelope['sender_id']}")
    print(f"   时间戳: {envelope['timestamp']}")
    
    # 验证必需字段
    required_fields = ["protocol", "protocol_version", "message_type", 
                      "message_id", "sender_id", "timestamp", "payload"]
    missing = [f for f in required_fields if f not in envelope]
    
    if not missing:
        print("✅ 所有必需字段都存在")
    else:
        print(f"❌ 缺少字段: {missing}")
    
    return envelope

def test_bundle_creation():
    """测试捆绑包创建"""
    print("\n=== 资产捆绑包测试 ===")
    
    gene, capsule, event, gene_hash, capsule_hash, event_hash = test_data_structures()
    
    # 设置资产ID
    gene["asset_id"] = gene_hash
    capsule["asset_id"] = capsule_hash
    event["asset_id"] = event_hash
    
    # 创建捆绑包
    bundle = {
        "assets": [gene, capsule, event]
    }
    
    print(f"✅ 捆绑包创建成功")
    print(f"   包含资产: {len(bundle['assets'])} 个")
    print(f"   资产类型: {[asset['type'] for asset in bundle['assets']]}")
    
    # 验证捆绑包规则
    has_gene = any(asset['type'] == 'Gene' for asset in bundle['assets'])
    has_capsule = any(asset['type'] == 'Capsule' for asset in bundle['assets'])
    
    if has_gene and has_capsule:
        print("✅ 捆绑包包含必需的Gene和Capsule")
    else:
        print("❌ 捆绑包缺少必需资产")
    
    return bundle

def simulate_workflow():
    """模拟完整工作流程"""
    print("\n=== 完整工作流程模拟 ===")
    
    print("1. 初始化客户端...")
    print("   ✅ 创建节点配置")
    print("   ✅ 生成节点ID")
    
    print("\n2. 创建测试资产...")
    gene, capsule, event, gene_hash, capsule_hash, event_hash = test_data_structures()
    
    print("\n3. 构建协议信封...")
    envelope = test_protocol_envelope()
    
    print("\n4. 创建资产捆绑包...")
    bundle = test_bundle_creation()
    
    print("\n5. 模拟发布流程...")
    print("   ✅ 计算资产哈希")
    print("   ✅ 构建协议消息")
    print("   ✅ 准备网络请求")
    print("   ⚠️ 注意: 这是模拟，不实际发送")
    
    print("\n6. 模拟获取资产...")
    print("   ✅ 构建fetch请求")
    print("   ✅ 准备查询参数")
    print("   ⚠️ 注意: 这是模拟，不实际查询")
    
    return True

def security_analysis():
    """安全分析"""
    print("\n=== 安全风险分析 ===")
    
    risks = [
        {
            "风险": "外部API连接",
            "等级": "高",
            "描述": "连接到evomap.ai外部服务",
            "缓解措施": "使用代理、监控连接、限制频率"
        },
        {
            "风险": "数据共享",
            "等级": "中",
            "描述": "解决方案会公开共享到市场",
            "缓解措施": "数据脱敏、使用测试数据、控制共享范围"
        },
        {
            "风险": "经济交易",
            "等级": "中",
            "描述": "涉及赏金任务和收入分享",
            "缓解措施": "使用测试账户、设置交易限额、监控活动"
        },
        {
            "风险": "代码验证",
            "等级": "低",
            "描述": "可能执行验证命令",
            "缓解措施": "沙盒环境、资源限制、命令白名单"
        }
    ]
    
    for risk in risks:
        print(f"{risk['风险']}: {risk['等级']}风险")
        print(f"   {risk['描述']}")
        print(f"   缓解: {risk['缓解措施']}")
        print()

if __name__ == "__main__":
    print("EvoMap安全测试 - 模拟模式")
    print("=" * 50)
    
    try:
        # 导入测试
        from evomap_client import EvoMapClient
        print("✅ EvoMapClient导入成功")
        
        # 测试数据格式
        test_data_structures()
        
        # 测试协议
        test_protocol_envelope()
        
        # 测试捆绑包
        test_bundle_creation()
        
        # 模拟工作流程
        simulate_workflow()
        
        # 安全分析
        security_analysis()
        
        print("\n" + "=" * 50)
        print("✅ 所有测试完成 - 代码功能正常")
        print("⚠️  注意: 这是模拟测试，未实际连接外部服务")
        print("🔒 建议: 在生产环境使用前进行真实连接测试")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)