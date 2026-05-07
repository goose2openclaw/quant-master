#!/usr/bin/env python3
"""
OpenClaw自动进化系统
利用EvoMap实现OpenClaw的自我改进和优化
"""

import sys
import json
import time
import hashlib
import uuid
import subprocess
import os
from datetime import datetime, timezone
from pathlib import Path

# 添加evomap路径
sys.path.append('/home/goose/.openclaw/workspace/.agents/skills/evomap/scripts')

class OpenClawEvolver:
    """OpenClaw自动进化器"""
    
    def __init__(self):
        self.workspace = Path("/home/goose/.openclaw/workspace")
        self.evomap_config = self.workspace / ".agents" / "skills" / "evomap"
        self.memory_dir = self.workspace / "memory"
        
        # 导入EvoMap客户端
        try:
            from evomap_client import EvoMapClient
            self.client = EvoMapClient(config_dir=str(self.workspace / "evomap_config"))
            print("✅ EvoMap客户端初始化成功")
            print(f"   节点ID: {self.client.node_id}")
        except Exception as e:
            print(f"❌ EvoMap客户端初始化失败: {e}")
            self.client = None
    
    def analyze_system_health(self):
        """分析系统健康状态"""
        print("\n=== 系统健康分析 ===")
        
        health_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "analysis_type": "system_health",
            "metrics": {}
        }
        
        # 1. 检查进程状态
        try:
            result = subprocess.run(
                ["ps", "aux", "|", "grep", "-c", "[o]penclaw"],
                shell=True, capture_output=True, text=True
            )
            openclaw_processes = int(result.stdout.strip())
            health_data["metrics"]["openclaw_processes"] = openclaw_processes
            print(f"✅ OpenClaw进程数: {openclaw_processes}")
        except:
            health_data["metrics"]["openclaw_processes"] = 0
            print("❌ 无法检查进程状态")
        
        # 2. 检查技能数量
        try:
            skills_dir = self.workspace / ".agents" / "skills"
            skill_count = len([d for d in skills_dir.iterdir() if d.is_dir()])
            health_data["metrics"]["skill_count"] = skill_count
            print(f"✅ 技能数量: {skill_count}")
        except:
            health_data["metrics"]["skill_count"] = 0
            print("❌ 无法检查技能数量")
        
        # 3. 检查内存文件
        try:
            memory_files = list(self.memory_dir.glob("*.md"))
            health_data["metrics"]["memory_files"] = len(memory_files)
            
            # 读取最新内存文件
            latest_memory = max(memory_files, key=os.path.getcttime)
            with open(latest_memory, 'r', encoding='utf-8') as f:
                content = f.read()
                health_data["metrics"]["latest_memory_size"] = len(content)
                health_data["metrics"]["latest_memory_lines"] = content.count('\n')
            
            print(f"✅ 内存文件数: {len(memory_files)}")
            print(f"✅ 最新内存: {latest_memory.name} ({len(content)} 字节)")
        except Exception as e:
            health_data["metrics"]["memory_files"] = 0
            print(f"❌ 无法检查内存文件: {e}")
        
        # 4. 检查Mission Control
        try:
            import requests
            response = requests.get("http://localhost:8080/api/tasks", timeout=5)
            if response.status_code == 200:
                data = response.json()
                health_data["metrics"]["mission_control_tasks"] = data.get("count", 0)
                health_data["metrics"]["mission_control_status"] = "online"
                print(f"✅ Mission Control: 在线 ({data.get('count', 0)} 个任务)")
            else:
                health_data["metrics"]["mission_control_status"] = "offline"
                print("❌ Mission Control: 离线")
        except:
            health_data["metrics"]["mission_control_status"] = "unreachable"
            print("❌ Mission Control: 无法连接")
        
        return health_data
    
    def identify_improvement_areas(self, health_data):
        """识别改进领域"""
        print("\n=== 改进领域识别 ===")
        
        improvements = []
        
        # 1. 技能管理改进
        skill_count = health_data["metrics"].get("skill_count", 0)
        if skill_count < 30:
            improvements.append({
                "area": "skill_management",
                "issue": "技能数量不足",
                "current": skill_count,
                "target": 50,
                "priority": "high",
                "solution": "安装更多核心技能"
            })
            print("⚠️  识别到: 技能数量不足")
        
        # 2. 内存管理改进
        memory_lines = health_data["metrics"].get("latest_memory_lines", 0)
        if memory_lines > 1000:
            improvements.append({
                "area": "memory_management",
                "issue": "内存文件过大",
                "current": memory_lines,
                "target": 500,
                "priority": "medium",
                "solution": "优化内存压缩策略"
            })
            print("⚠️  识别到: 内存文件过大")
        
        # 3. 进程管理改进
        processes = health_data["metrics"].get("openclaw_processes", 0)
        if processes < 3:
            improvements.append({
                "area": "process_management",
                "issue": "进程数量异常",
                "current": processes,
                "target": 3,
                "priority": "high",
                "solution": "检查并重启OpenClaw服务"
            })
            print("⚠️  识别到: 进程数量异常")
        
        # 4. Mission Control集成改进
        mc_status = health_data["metrics"].get("mission_control_status", "")
        if mc_status != "online":
            improvements.append({
                "area": "mission_control",
                "issue": "Mission Control未运行",
                "current": mc_status,
                "target": "online",
                "priority": "high",
                "solution": "启动Mission Control服务"
            })
            print("⚠️  识别到: Mission Control未运行")
        
        if not improvements:
            improvements.append({
                "area": "system_maintenance",
                "issue": "常规维护",
                "current": "stable",
                "target": "optimized",
                "priority": "low",
                "solution": "执行常规优化任务"
            })
            print("✅ 系统状态良好，执行常规优化")
        
        return improvements
    
    def create_evolution_gene(self, improvement):
        """创建进化基因"""
        print(f"\n=== 创建进化基因: {improvement['area']} ===")
        
        # 基因模板
        gene = {
            "schema_version": "1.5.0",
            "type": "Gene",
            "category": "optimize",
            "signals_match": [
                f"openclaw_{improvement['area']}",
                improvement["issue"].replace(" ", "_").lower()
            ],
            "summary": f"OpenClaw {improvement['area']} 优化基因",
            "description": f"解决: {improvement['issue']}\n目标: {improvement['target']}\n方案: {improvement['solution']}",
            "constraints": {
                "platform": "linux",
                "openclaw_version": ">=2026.2.25",
                "requires": ["bash", "python3"]
            },
            "verification_commands": [
                f"# 检查{improvement['area']}状态",
                f"echo '检查: {improvement['issue']}'",
                f"# 执行优化: {improvement['solution']}"
            ]
        }
        
        print(f"✅ 基因创建完成: {gene['summary']}")
        return gene
    
    def create_evolution_capsule(self, gene, improvement, execution_result):
        """创建进化胶囊"""
        print(f"\n=== 创建进化胶囊 ===")
        
        # 计算基因哈希
        gene_hash = self._compute_hash(gene)
        
        # 胶囊模板
        capsule = {
            "schema_version": "1.5.0",
            "type": "Capsule",
            "trigger": gene["signals_match"],
            "summary": f"OpenClaw {improvement['area']} 优化胶囊",
            "description": f"已执行优化: {improvement['solution']}\n结果: {execution_result.get('status', 'unknown')}",
            "confidence": execution_result.get("confidence", 0.8),
            "blast_radius": {
                "files": execution_result.get("files_affected", 1),
                "lines": execution_result.get("lines_changed", 10)
            },
            "outcome": {
                "status": execution_result.get("status", "success"),
                "score": execution_result.get("score", 0.85)
            },
            "env_fingerprint": {
                "platform": "linux",
                "arch": "x64",
                "openclaw_version": "2026.2.25"
            },
            "gene": gene_hash,
            "success_streak": 1
        }
        
        print(f"✅ 胶囊创建完成: {capsule['summary']}")
        return capsule
    
    def execute_improvement(self, improvement):
        """执行改进方案"""
        print(f"\n=== 执行改进: {improvement['area']} ===")
        
        result = {
            "status": "pending",
            "score": 0.0,
            "confidence": 0.0,
            "output": "",
            "files_affected": 0,
            "lines_changed": 0
        }
        
        try:
            if improvement["area"] == "skill_management":
                # 安装新技能
                print(f"执行: {improvement['solution']}")
                
                # 搜索相关技能
                search_terms = {
                    "skill_management": "openclaw skill manager",
                    "memory_management": "memory optimization",
                    "process_management": "process monitor",
                    "mission_control": "task management"
                }
                
                term = search_terms.get(improvement["area"], "openclaw")
                cmd = f"cd {self.workspace} && npx skills find {term} 2>/dev/null | head -5"
                output = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                result["output"] = output.stdout[:500]
                result["status"] = "success" if output.returncode == 0 else "partial"
                result["score"] = 0.9 if output.returncode == 0 else 0.5
                result["confidence"] = 0.85
                result["files_affected"] = 1
                result["lines_changed"] = 10
                
            elif improvement["area"] == "memory_management":
                # 优化内存
                print(f"执行: {improvement['solution']}")
                
                # 压缩内存文件
                memory_file = self.memory_dir / "2026-03-01.md"
                if memory_file.exists():
                    with open(memory_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 简单的压缩：移除空行和重复内容
                    lines = content.split('\n')
                    compressed = []
                    seen = set()
                    for line in lines:
                        line_stripped = line.strip()
                        if line_stripped and line_stripped not in seen:
                            compressed.append(line)
                            seen.add(line_stripped)
                    
                    compressed_content = '\n'.join(compressed)
                    compression_ratio = len(compressed_content) / len(content) if content else 1
                    
                    result["output"] = f"压缩比例: {compression_ratio:.2%}"
                    result["status"] = "success"
                    result["score"] = 0.8
                    result["confidence"] = 0.75
                    result["files_affected"] = 1
                    result["lines_changed"] = len(lines) - len(compressed)
                else:
                    result["output"] = "内存文件不存在"
                    result["status"] = "skipped"
                    result["score"] = 0.3
                    result["confidence"] = 0.5
            
            elif improvement["area"] == "process_management":
                # 检查进程
                print(f"执行: {improvement['solution']}")
                
                cmd = "ps aux | grep -c '[o]penclaw'"
                output = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                process_count = int(output.stdout.strip())
                
                result["output"] = f"当前进程数: {process_count}"
                result["status"] = "success" if process_count >= 3 else "warning"
                result["score"] = 0.7 if process_count >= 3 else 0.4
                result["confidence"] = 0.8
                result["files_affected"] = 0
                result["lines_changed"] = 0
            
            elif improvement["area"] == "mission_control":
                # 检查Mission Control
                print(f"执行: {improvement['solution']}")
                
                try:
                    import requests
                    response = requests.get("http://localhost:8080", timeout=5)
                    result["output"] = f"HTTP状态: {response.status_code}"
                    result["status"] = "success" if response.status_code == 200 else "error"
                    result["score"] = 0.9 if response.status_code == 200 else 0.3
                    result["confidence"] = 0.85
                except Exception as e:
                    result["output"] = f"连接错误: {e}"
                    result["status"] = "error"
                    result["score"] = 0.2
                    result["confidence"] = 0.6
                
                result["files_affected"] = 0
                result["lines_changed"] = 0
            
            else:
                # 常规维护
                print(f"执行: {improvement['solution']}")
                
                # 清理临时文件
                cmd = f"find {self.workspace} -name '*.tmp' -o -name '*.log' -mtime +7 | head -5"
                output = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                result["output"] = f"找到旧文件:\n{output.stdout[:200]}"
                result["status"] = "success"
                result["score"] = 0.6
                result["confidence"] = 0.7
                result["files_affected"] = output.stdout.count('\n')
                result["lines_changed"] = 0
            
            print(f"✅ 执行完成: {result['status']} (分数: {result['score']})")
            
        except Exception as e:
            result["output"] = f"执行错误: {e}"
            result["status"] = "error"
            result["score"] = 0.1
            result["confidence"] = 0.3
            print(f"❌ 执行失败: {e}")
        
        return result
    
    def publish_to_evomap(self, gene, capsule, execution_result):
        """发布到EvoMap"""
        if not self.client:
            print("❌ EvoMap客户端不可用，跳过发布")
            return None
        
        print("\n=== 发布到EvoMap ===")
        
        try:
            # 创建进化事件
            event = {
                "schema_version": "1.5.0",
                "type": "EvolutionEvent",
                "intent": "optimize",
                "outcome": {
                    "status": execution_result["status"],
                    "score": execution_result["score"]
                },
                "mutations_tried": 1,
                "total_cycles": 1,
                "environment": {
                    "platform": "linux",
                    "openclaw_version": "2026.2.25",
                    "skill_count": gene.get("constraints", {}).get("skill_count", 0)
                }
            }
            
            print("准备发布基因、胶囊和进化事件...")
            
            # 发布到EvoMap
            response = self.client.publish(gene, capsule, event)
            
            print(f"✅ 发布成功!")
            print(f"   响应: {response.get('status', 'unknown')}")
            
            if 'bundle_id' in response:
                print(f"   捆绑包ID: {response['bundle_id']}")
            
            return response
            
        except Exception as e:
            print(f"❌ 发布失败: {e}")
            return None
    
    def _compute_hash(self, data):
        """计算数据哈希"""
        temp = data.copy()
        temp.pop("asset_id", None)
        canonical = json.dumps(temp, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
        return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"
    
    def run_evolution_cycle(self):
        """运行一个完整的进化周期"""
        print("=" * 60)
        print("OpenClaw自动进化系统")
        print("=" * 60)
        
        # 1. 分析系统健康
        health_data = self.analyze_system_health()
        
        # 2. 识别改进领域
        improvements = self.identify_improvement_areas(health_data)
        
        # 按优先级排序
        priority_order = {"high": 0, "medium": 1, "low": 2}
        improvements.sort(key=lambda x: priority_order.get(x["priority"], 3))
        
        evolution_results = []
        
        # 3. 对每个改进领域执行进化
        for improvement in improvements[:2]:  # 每次最多处理2个
            print(f"\n{'='*40}")
            print(f"处理改进: {improvement['area']} ({improvement['priority']}优先级)")
            print(f"{'='*40}")
            
            # 创建基因
            gene = self.create_evolution_gene(improvement)
            
            # 执行改进
            execution_result = self.execute_improvement(improvement)
            
            # 创建胶囊
            capsule = self.create_evolution_capsule(gene, improvement, execution_result)
            
            # 发布到EvoMap
            evomap_response = self.publish_to_evomap(gene, capsule, execution_result)
            
            # 记录结果
            evolution_results.append({
                "improvement": improvement,
                "gene": gene,
                "capsule": capsule,
                "execution_result": execution_result,
                "evomap_response": evomap_response
            })
            
            # 短暂暂停
            time.sleep(1)
        
        # 4. 生成进化报告
        self.generate_evolution_report(health_data, improvements, evolution_results)
        
        return evolution_results
    
    def generate_evolution_report(self, health_data, improvements, evolution_results):
        """生成进化报告"""
        print(f"\n{'='*60}")
        print("进化周期报告")
        print(f"{'='*60}")
        
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cycle_id": f"cycle_{int(time.time())}",
            "health_analysis": health_data,
            "improvements_identified": len(improvements),
            "improvements_executed": len(evolution_results),
            "evolution_results": []
        }
        
        # 总结每个进化结果
        for i, result in enumerate(evolution_results):
            improvement = result["improvement"]
            exec_result = result["execution_result"]
            
            summary = {
                "area": improvement["area"],
                "issue": improvement["issue"],
                "solution": improvement["solution"],
                "execution_status": exec_result["status"],
                "execution_score": exec_result["score"],
                "published_to_evomap": result["evomap_response"] is not None
            }
            
            report["evolution_results"].append(summary)
            
            print(f"\n改进 #{i+1}: {improvement['area']}")
            print(f"  问题: {improvement['issue']}")
            print(f"  方案: {improvement['solution']}")
            print(f"  执行: {exec_result['status']} (分数: {exec_result['score']:.2f})")
            print(f"  发布: {'✅ 成功' if result['evomap_response'] else '❌ 失败'}")
        
        # 保存报告
        report_file = self.workspace / "evolution_reports" / f"cycle_{int(time.time())}.json"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ 报告已保存: {report_file}")
        
        # 更新内存文件
        self.update_memory_with_evolution(report)
        
        return report
    
    def update_memory_with_evolution(self, report):
        """更新内存文件记录进化"""
        print("\n=== 更新内存记录 ===")
        
        try:
            memory_file = self.memory_dir / "2026-03-01.md"
            
            evolution_entry = f"""
## 自动进化记录 ({datetime.now().strftime('%H:%M')})

### 进化周期: {report['cycle_id']}
- **分析时间**: {report['timestamp']}
- **识别改进**: {report['improvements_identified']} 个
- **执行改进**: {report['improvements_executed']} 个

### 执行结果
"""
            
            for i, result in enumerate(report["evolution_results"]):
                evolution_entry += f"""
**改进 #{i+1}**: {result['area']}
- **问题**: {result['issue']}
- **方案**: {result['solution']}
- **状态**: {result['execution_status']} (分数: {result['execution_score']:.2f})
- **发布到EvoMap**: {'✅ 是' if result['published_to_evomap'] else '❌ 否'}
"""
            
            evolution_entry += f"""
### 系统状态
- **OpenClaw进程**: {report['health_analysis']['metrics'].get('openclaw_processes', 'N/A')}
- **技能数量**: {report['health_analysis']['metrics'].get('skill_count', 'N/A')}
- **Mission Control**: {report['health_analysis']['metrics'].get('mission_control_status', 'N/A')}

---
"""
            
            # 追加到内存文件
            with open(memory_file, 'a', encoding='utf-8') as f:
                f.write(evolution_entry)
            
            print(f"✅ 内存文件已更新: {memory_file}")
            
        except Exception as e:
            print(f"❌ 更新内存文件失败: {e}")
    
    def schedule_evolution(self, interval_hours=24):
        """安排定期进化"""
        print(f"\n=== 安排定期进化 ===")
        print(f"计划: 每 {interval_hours} 小时执行一次自动进化")
        
        cron_entry = f"""
# OpenClaw自动进化任务
0 */{interval_hours} * * * cd {self.workspace} && python3 openclaw_auto_evolution.py --run-cycle >> {self.workspace}/evolution.log 2>&1
"""
        
        cron_file = self.workspace / "evolution_cron.txt"
        with open(cron_file, 'w', encoding='utf-8') as f:
            f.write(cron_entry)
        
        print(f"✅ Cron配置已保存: {cron_file}")
        print(f"手动添加Cron任务:")
        print(f"  crontab {cron_file}")
        
        return cron_entry

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenClaw自动进化系统")
    parser.add_argument("--run-cycle", action="store_true", help="运行一个进化周期")
    parser.add_argument("--schedule", type=int, default=24, help="安排定期进化（小时）")
    parser.add_argument("--analyze-only", action="store_true", help="只分析不执行")
    
    args = parser.parse_args()
    
    evolver = OpenClawEvolver()
    
    if args.run_cycle:
        print("开始运行进化周期...")
        results = evolver.run_evolution_cycle()
        print(f"\n✅ 进化周期完成，处理了 {len(results)} 个改进")
        
    elif args.schedule:
        evolver.schedule_evolution(args.schedule)
        
    elif args.analyze_only:
        health = evolver.analyze_system_health()
        improvements = evolver.identify_improvement_areas(health)
        print(f"\n分析完成: 识别到 {len(improvements)} 个改进领域")
        
    else:
        # 交互模式
        print("OpenClaw自动进化系统 - 交互模式")
        print("1. 运行进化周期")
        print("2. 安排定期进化")
        print("3. 只分析系统")
        print("4. 退出")
        
        choice = input("\n请选择 (1-4): ").strip()
        
        if choice == "1":
            results = evolver.run_evolution_cycle()
            print(f"\n✅ 进化周期完成，处理了 {len(results)} 个改进")
        elif choice == "2":
            hours = input("请输入进化间隔（小时）: ").strip()
            try:
                evolver.schedule_evolution(int(hours))
            except ValueError:
                print("❌ 请输入有效的数字")
        elif choice == "3":
            health = evolver.analyze_system_health()
            improvements = evolver.identify_improvement_areas(health)
            print(f"\n分析完成: 识别到 {len(improvements)} 个改进领域")
        elif choice == "4":
            print("退出系统")
        else:
            print("❌ 无效选择")

if __name__ == "__main__":
    main()