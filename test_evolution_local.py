#!/usr/bin/env python3
"""
OpenClaw本地进化测试
不连接EvoMap，只在本地测试进化逻辑
"""

import sys
import json
import time
import subprocess
import os
from datetime import datetime, timezone
from pathlib import Path

class LocalOpenClawEvolver:
    """本地OpenClaw进化器"""
    
    def __init__(self):
        self.workspace = Path("/home/goose/.openclaw/workspace")
        self.memory_dir = self.workspace / "memory"
    
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
                "ps aux | grep -c '[o]penclaw'",
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
            if memory_files:
                latest_memory = max(memory_files, key=os.path.getcttime)
                with open(latest_memory, 'r', encoding='utf-8') as f:
                    content = f.read()
                    health_data["metrics"]["latest_memory_size"] = len(content)
                    health_data["metrics"]["latest_memory_lines"] = content.count('\n')
                
                print(f"✅ 内存文件数: {len(memory_files)}")
                print(f"✅ 最新内存: {latest_memory.name} ({len(content)} 字节)")
            else:
                print("⚠️  无内存文件")
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
        if skill_count < 40:
            improvements.append({
                "area": "skill_management",
                "issue": "技能生态系统可扩展",
                "current": skill_count,
                "target": 60,
                "priority": "medium",
                "solution": "探索和安装有价值的技能"
            })
            print("⚠️  识别到: 技能生态系统可扩展")
        
        # 2. 内存管理改进
        memory_lines = health_data["metrics"].get("latest_memory_lines", 0)
        if memory_lines > 800:
            improvements.append({
                "area": "memory_management",
                "issue": "内存文件需要优化",
                "current": memory_lines,
                "target": 600,
                "priority": "low",
                "solution": "执行内存压缩和清理"
            })
            print("⚠️  识别到: 内存文件需要优化")
        
        # 3. 文档完整性改进
        docs_dir = self.workspace / "docs"
        if docs_dir.exists():
            doc_files = list(docs_dir.glob("*.md"))
            if len(doc_files) < 10:
                improvements.append({
                    "area": "documentation",
                    "issue": "文档系统不完整",
                    "current": len(doc_files),
                    "target": 15,
                    "priority": "medium",
                    "solution": "创建系统使用文档和指南"
                })
                print("⚠️  识别到: 文档系统不完整")
        
        # 4. 自动化改进
        scripts_dir = self.workspace / "scripts"
        if scripts_dir.exists():
            script_files = list(scripts_dir.glob("*.sh")) + list(scripts_dir.glob("*.py"))
            if len(script_files) < 5:
                improvements.append({
                    "area": "automation",
                    "issue": "自动化脚本不足",
                    "current": len(script_files),
                    "target": 10,
                    "priority": "medium",
                    "solution": "创建常用任务的自动化脚本"
                })
                print("⚠️  识别到: 自动化脚本不足")
        
        if not improvements:
            improvements.append({
                "area": "system_maintenance",
                "issue": "常规系统维护",
                "current": "stable",
                "target": "optimized",
                "priority": "low",
                "solution": "执行常规清理和优化"
            })
            print("✅ 系统状态良好，执行常规优化")
        
        return improvements
    
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
                print(f"执行: {improvement['solution']}")
                
                # 搜索技能但不安装
                search_cmd = f"cd {self.workspace} && npx skills find openclaw 2>/dev/null | head -3"
                output = subprocess.run(search_cmd, shell=True, capture_output=True, text=True)
                
                result["output"] = f"找到相关技能:\n{output.stdout[:300]}"
                result["status"] = "analyzed"
                result["score"] = 0.7
                result["confidence"] = 0.8
                result["files_affected"] = 0
                result["lines_changed"] = 0
                
            elif improvement["area"] == "memory_management":
                print(f"执行: {improvement['solution']}")
                
                # 分析内存文件但不修改
                memory_file = self.memory_dir / "2026-03-01.md"
                if memory_file.exists():
                    with open(memory_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    lines = content.split('\n')
                    empty_lines = sum(1 for line in lines if not line.strip())
                    duplicate_lines = len(lines) - len(set(lines))
                    
                    result["output"] = f"分析结果: {len(lines)} 行, {empty_lines} 空行, {duplicate_lines} 重复行"
                    result["status"] = "analyzed"
                    result["score"] = 0.6
                    result["confidence"] = 0.7
                    result["files_affected"] = 0
                    result["lines_changed"] = 0
                else:
                    result["output"] = "内存文件不存在"
                    result["status"] = "skipped"
                    result["score"] = 0.3
            
            elif improvement["area"] == "documentation":
                print(f"执行: {improvement['solution']}")
                
                # 检查文档目录
                docs_dir = self.workspace / "docs"
                docs_dir.mkdir(exist_ok=True)
                
                # 创建文档模板
                doc_template = f"""# OpenClaw系统文档

## 系统概览
- **版本**: 2026.2.25
- **技能数量**: {health_data['metrics'].get('skill_count', 0)}
- **分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 改进建议
{improvement['solution']}

---
*自动生成于进化周期*
"""
                
                doc_file = docs_dir / f"evolution_{int(time.time())}.md"
                with open(doc_file, 'w', encoding='utf-8') as f:
                    f.write(doc_template)
                
                result["output"] = f"创建文档: {doc_file.name}"
                result["status"] = "success"
                result["score"] = 0.8
                result["confidence"] = 0.75
                result["files_affected"] = 1
                result["lines_changed"] = len(doc_template.split('\n'))
            
            elif improvement["area"] == "automation":
                print(f"执行: {improvement['solution']}")
                
                # 创建自动化脚本目录
                scripts_dir = self.workspace / "scripts"
                scripts_dir.mkdir(exist_ok=True)
                
                # 创建简单的健康检查脚本
                health_script = scripts_dir / "health_check.sh"
                script_content = """#!/bin/bash
# OpenClaw健康检查脚本
echo "=== OpenClaw健康检查 $(date) ==="
echo "进程检查:"
ps aux | grep -c "[o]penclaw" && echo "✅ OpenClaw运行中" || echo "❌ OpenClaw未运行"
echo "技能检查:"
ls -la ~/.openclaw/workspace/.agents/skills/ | grep -c "^d" | xargs echo "技能数量:"
echo "内存检查:"
ls -la ~/.openclaw/workspace/memory/*.md | wc -l | xargs echo "内存文件:"
"""
                
                with open(health_script, 'w', encoding='utf-8') as f:
                    f.write(script_content)
                
                os.chmod(health_script, 0o755)
                
                result["output"] = f"创建自动化脚本: {health_script.name}"
                result["status"] = "success"
                result["score"] = 0.85
                result["confidence"] = 0.8
                result["files_affected"] = 1
                result["lines_changed"] = len(script_content.split('\n'))
            
            else:
                # 常规维护
                print(f"执行: {improvement['solution']}")
                
                # 清理临时文件
                tmp_dir = self.workspace / "tmp"
                tmp_dir.mkdir(exist_ok=True)
                
                # 创建清理记录
                cleanup_log = tmp_dir / f"cleanup_{int(time.time())}.log"
                with open(cleanup_log, 'w', encoding='utf-8') as f:
                    f.write(f"清理时间: {datetime.now()}\n")
                    f.write(f"改进类型: {improvement['area']}\n")
                    f.write(f"解决方案: {improvement['solution']}\n")
                
                result["output"] = f"执行常规维护，日志: {cleanup_log.name}"
                result["status"] = "success"
                result["score"] = 0.6
                result["confidence"] = 0.7
                result["files_affected"] = 1
                result["lines_changed"] = 4
            
            print(f"✅ 执行完成: {result['status']} (分数: {result['score']:.2f})")
            
        except Exception as e:
            result["output"] = f"执行错误: {e}"
            result["status"] = "error"
            result["score"] = 0.1
            result["confidence"] = 0.3
            print(f"❌ 执行失败: {e}")
        
        return result
    
    def run_evolution_cycle(self):
        """运行一个完整的进化周期"""
        print("=" * 60)
        print("OpenClaw本地进化系统")
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
            
            # 执行改进
            execution_result = self.execute_improvement(improvement)
            
            # 记录结果
            evolution_results.append({
                "improvement": improvement,
                "execution_result": execution_result
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
            "cycle_id": f"local_cycle_{int(time.time())}",
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
                "output_preview": exec_result["output"][:100] + "..." if len(exec_result["output"]) > 100 else exec_result["output"]
            }
            
            report["evolution_results"].append(summary)
            
            print(f"\n改进 #{i+1}: {improvement['area']}")
            print(f"  问题: {improvement['issue']}")
            print(f"  方案: {improvement['solution']}")
            print(f"  执行: {exec_result['status']} (分数: {exec_result['score']:.2f})")
        
        # 保存报告
        reports_dir = self.workspace / "evolution_reports"
        reports_dir.mkdir(exist_ok=True)
        
        report_file = reports_dir / f"local_cycle_{int(time.time())}.json"
        
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
## 本地自动进化记录 ({datetime.now().strftime('%H:%M')})

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
- **输出**: {result['output_preview']}
"""
            
            evolution_entry += f"""
### 系统快照
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

def main():
    """主函数"""
    print("OpenClaw本地进化系统")
    print("=" * 50)
    
    evolver = LocalOpenClawEvolver()
    results = evolver.run_evolution_cycle()
    
    print(f"\n{'='*50}")
    print(f"✅ 进化周期完成!")
    print(f"   处理了 {len(results)} 个改进")
    print(f"   报告已保存到 evolution_reports/ 目录")
    print(f"   内存文件已更新")

if __name__ == "__main__":
    main()