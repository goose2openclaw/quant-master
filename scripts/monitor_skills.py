#!/usr/bin/env python3
"""
OpenClaw技能监控系统
监控技能状态、依赖和性能
"""

import os
import json
import time
from datetime import datetime
import subprocess
import sys

class SkillMonitor:
    def __init__(self, workspace_dir):
        self.workspace_dir = workspace_dir
        self.skills_dir = os.path.join(workspace_dir, "skills")
        self.log_file = os.path.join(workspace_dir, "logs", "skill_monitor.log")
        
        # 确保日志目录存在
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
    
    def log(self, message, level="INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        with open(self.log_file, "a") as f:
            f.write(log_entry)
        
        # 同时输出到控制台
        print(log_entry.strip())
    
    def check_skill_health(self):
        """检查技能健康状态"""
        self.log("开始技能健康检查...")
        
        skills = []
        if os.path.exists(self.skills_dir):
            for skill_name in os.listdir(self.skills_dir):
                skill_path = os.path.join(self.skills_dir, skill_name)
                skill_md = os.path.join(skill_path, "SKILL.md")
                
                if os.path.isdir(skill_path) and os.path.exists(skill_md):
                    skill_info = {
                        "name": skill_name,
                        "path": skill_path,
                        "has_skll_md": True,
                        "scripts_count": len([f for f in os.listdir(os.path.join(skill_path, "scripts")) 
                                            if os.path.isfile(os.path.join(skill_path, "scripts", f))]) 
                                        if os.path.exists(os.path.join(skill_path, "scripts")) else 0,
                        "last_modified": datetime.fromtimestamp(os.path.getmtime(skill_md)).strftime("%Y-%m-%d %H:%M:%S")
                    }
                    skills.append(skill_info)
        
        # 生成报告
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_skills": len(skills),
            "skills": skills,
            "health_score": min(100, len(skills) * 10)  # 简单评分
        }
        
        # 保存报告
        report_file = os.path.join(self.workspace_dir, "logs", f"skill_report_{datetime.now().strftime('%Y%m%d')}.json")
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        
        self.log(f"健康检查完成: 发现 {len(skills)} 个技能")
        return report
    
    def check_dependencies(self):
        """检查系统依赖"""
        self.log("检查系统依赖...")
        
        dependencies = {
            "python3": self.check_command("python3 --version"),
            "git": self.check_command("git --version"),
            "curl": self.check_command("curl --version"),
            "node": self.check_command("node --version"),
            "npm": self.check_command("npm --version")
        }
        
        missing = [dep for dep, exists in dependencies.items() if not exists]
        
        if missing:
            self.log(f"缺少依赖: {', '.join(missing)}", "WARNING")
        else:
            self.log("所有依赖已安装", "SUCCESS")
        
        return dependencies
    
    def check_command(self, command):
        """检查命令是否存在"""
        try:
            subprocess.run(command.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def run_monitoring_cycle(self):
        """运行监控周期"""
        self.log("=" * 50)
        self.log("开始监控周期")
        
        # 检查技能健康
        skill_report = self.check_skill_health()
        
        # 检查依赖
        deps = self.check_dependencies()
        
        # 生成摘要
        summary = {
            "time": datetime.now().isoformat(),
            "skills_count": skill_report["total_skills"],
            "health_score": skill_report["health_score"],
            "missing_deps": [dep for dep, exists in deps.items() if not exists],
            "status": "HEALTHY" if skill_report["health_score"] > 80 and not any(not exists for exists in deps.values()) else "NEEDS_ATTENTION"
        }
        
        self.log(f"监控周期完成 - 状态: {summary['status']}")
        return summary

def main():
    """主函数"""
    workspace_dir = os.path.expanduser("~/.openclaw/workspace")
    monitor = SkillMonitor(workspace_dir)
    
    print("🔍 OpenClaw技能监控系统")
    print("=" * 50)
    
    # 运行监控
    summary = monitor.run_monitoring_cycle()
    
    print("\n📊 监控摘要:")
    print(f"  技能数量: {summary['skills_count']}")
    print(f"  健康评分: {summary['health_score']}/100")
    
    if summary['missing_deps']:
        print(f"  缺少依赖: {', '.join(summary['missing_deps'])}")
    
    print(f"  总体状态: {summary['status']}")
    
    # 建议
    if summary['status'] == "NEEDS_ATTENTION":
        print("\n💡 建议:")
        if summary['health_score'] < 80:
            print("  - 运行技能安装脚本添加更多技能")
        if summary['missing_deps']:
            print(f"  - 安装缺失依赖: {', '.join(summary['missing_deps'])}")

if __name__ == "__main__":
    main()
