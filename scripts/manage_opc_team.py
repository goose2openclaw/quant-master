#!/usr/bin/env python3
"""
OPC多智能体团队管理脚本
用于启动、停止、监控和管理团队中的各个Agent
"""

import json
import os
import sys
import time
from datetime import datetime
import subprocess

class OPCTeamManager:
    def __init__(self):
        self.config_path = "/home/goose/.openclaw/workspace/config/opc_team_config.json"
        self.status_path = "/home/goose/.openclaw/workspace/memory/team_status.json"
        self.log_path = "/home/goose/.openclaw/workspace/logs/team_activity.log"
        
        # 确保目录存在
        os.makedirs(os.path.dirname(self.status_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        
        self.load_config()
        self.init_status()
    
    def load_config(self):
        """加载团队配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            self.log("配置加载成功")
        except FileNotFoundError:
            print(f"❌ 配置文件不存在: {self.config_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ 配置文件格式错误: {e}")
            sys.exit(1)
    
    def init_status(self):
        """初始化团队状态"""
        if not os.path.exists(self.status_path):
            self.status = {
                "team": self.config["team_name"],
                "started_at": None,
                "last_updated": None,
                "status": "stopped",
                "agents": {}
            }
            self.save_status()
        else:
            self.load_status()
    
    def load_status(self):
        """加载团队状态"""
        try:
            with open(self.status_path, 'r', encoding='utf-8') as f:
                self.status = json.load(f)
        except:
            self.init_status()
    
    def save_status(self):
        """保存团队状态"""
        self.status["last_updated"] = datetime.now().isoformat()
        with open(self.status_path, 'w', encoding='utf-8') as f:
            json.dump(self.status, f, indent=2, ensure_ascii=False)
    
    def log(self, message, level="INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        if level == "ERROR":
            print(f"❌ {message}")
        elif level == "WARNING":
            print(f"⚠️  {message}")
        else:
            print(f"📝 {message}")
    
    def start_agent(self, agent_id):
        """启动单个Agent"""
        if agent_id not in self.config["agents"]:
            self.log(f"Agent不存在: {agent_id}", "ERROR")
            return False
        
        agent_info = self.config["agents"][agent_id]
        self.log(f"启动Agent: {agent_info['name']}")
        
        # 检查技能依赖
        for skill in agent_info["skills_required"]:
            skill_path = f"/home/goose/.openclaw/workspace/skills/{skill}"
            if not os.path.exists(skill_path):
                self.log(f"缺少技能: {skill}", "WARNING")
        
        # 模拟启动Agent（实际实现时会调用相应的技能脚本）
        self.status["agents"][agent_id] = {
            "name": agent_info["name"],
            "status": "running",
            "started_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "tasks_completed": 0,
            "errors": 0
        }
        
        self.status["status"] = "running"
        if not self.status["started_at"]:
            self.status["started_at"] = datetime.now().isoformat()
        
        self.save_status()
        self.log(f"Agent启动成功: {agent_info['name']}")
        return True
    
    def stop_agent(self, agent_id):
        """停止单个Agent"""
        if agent_id not in self.status["agents"]:
            self.log(f"Agent未运行: {agent_id}", "WARNING")
            return False
        
        agent_name = self.status["agents"][agent_id]["name"]
        self.log(f"停止Agent: {agent_name}")
        
        self.status["agents"][agent_id]["status"] = "stopped"
        self.status["agents"][agent_id]["stopped_at"] = datetime.now().isoformat()
        
        # 检查是否所有Agent都停止了
        all_stopped = all(
            agent["status"] == "stopped" 
            for agent in self.status["agents"].values()
        )
        
        if all_stopped:
            self.status["status"] = "stopped"
        
        self.save_status()
        self.log(f"Agent停止成功: {agent_name}")
        return True
    
    def start_all_agents(self):
        """启动所有Agent"""
        self.log("启动所有Agent...")
        
        success_count = 0
        for agent_id in self.config["agents"]:
            if self.start_agent(agent_id):
                success_count += 1
            time.sleep(0.5)  # 避免同时启动
        
        self.log(f"启动完成: {success_count}/{len(self.config['agents'])} 个Agent成功")
        return success_count
    
    def stop_all_agents(self):
        """停止所有Agent"""
        self.log("停止所有Agent...")
        
        success_count = 0
        for agent_id in list(self.status["agents"].keys()):
            if self.stop_agent(agent_id):
                success_count += 1
            time.sleep(0.5)
        
        self.log(f"停止完成: {success_count} 个Agent已停止")
        return success_count
    
    def show_status(self):
        """显示团队状态"""
        print("\n" + "="*60)
        print(f"🏢 团队: {self.status['team']}")
        print(f"📅 状态: {self.status['status'].upper()}")
        print(f"⏰ 启动时间: {self.status.get('started_at', '未启动')}")
        print(f"🔄 最后更新: {self.status.get('last_updated', '从未')}")
        print("="*60)
        
        if self.status["agents"]:
            print("\n👥 运行中的Agent:")
            print("-"*40)
            for agent_id, agent_data in self.status["agents"].items():
                status_emoji = "🟢" if agent_data["status"] == "running" else "🔴"
                print(f"{status_emoji} {agent_data['name']}")
                print(f"   状态: {agent_data['status']}")
                print(f"   运行时间: {agent_data.get('started_at', '未知')}")
                print(f"   完成任务: {agent_data.get('tasks_completed', 0)}")
                print(f"   错误数: {agent_data.get('errors', 0)}")
                print()
        else:
            print("\n📭 没有运行中的Agent")
        
        print(f"\n📊 日志文件: {self.log_path}")
        print(f"📁 状态文件: {self.status_path}")
        print("="*60)
    
    def health_check(self):
        """运行健康检查"""
        self.log("运行团队健康检查...")
        
        checks = []
        
        # 检查1: 配置文件
        checks.append(("配置文件", os.path.exists(self.config_path), "配置文件存在"))
        
        # 检查2: 技能目录
        skill_dir = "/home/goose/.openclaw/workspace/skills"
        checks.append(("技能目录", os.path.exists(skill_dir), "技能目录存在"))
        
        # 检查3: 日志目录
        log_dir = os.path.dirname(self.log_path)
        checks.append(("日志目录", os.path.exists(log_dir), "日志目录存在"))
        
        # 检查4: 网络连接（简单测试）
        try:
            subprocess.run(["ping", "-c", "1", "8.8.8.8"], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL, 
                         timeout=5)
            checks.append(("网络连接", True, "网络连接正常"))
        except:
            checks.append(("网络连接", False, "网络连接失败"))
        
        # 显示检查结果
        print("\n🧪 健康检查结果:")
        print("-"*40)
        
        all_passed = True
        for check_name, passed, message in checks:
            status = "✅" if passed else "❌"
            print(f"{status} {check_name}: {message}")
            if not passed:
                all_passed = False
        
        print("-"*40)
        if all_passed:
            print("🎉 所有检查通过！")
        else:
            print("⚠️  部分检查失败，请查看详细信息")
        
        return all_passed

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python manage_opc_team.py <命令>")
        print("命令:")
        print("  start-all    启动所有Agent")
        print("  stop-all     停止所有Agent")
        print("  status       显示团队状态")
        print("  health       运行健康检查")
        print("  start <id>   启动指定Agent")
        print("  stop <id>    停止指定Agent")
        print("  list         列出所有Agent")
        return
    
    manager = OPCTeamManager()
    command = sys.argv[1]
    
    if command == "start-all":
        manager.start_all_agents()
    elif command == "stop-all":
        manager.stop_all_agents()
    elif command == "status":
        manager.show_status()
    elif command == "health":
        manager.health_check()
    elif command == "start" and len(sys.argv) > 2:
        manager.start_agent(sys.argv[2])
    elif command == "stop" and len(sys.argv) > 2:
        manager.stop_agent(sys.argv[2])
    elif command == "list":
        print("\n📋 可用的Agent:")
        print("-"*40)
        for agent_id, agent_info in manager.config["agents"].items():
            print(f"• {agent_id}: {agent_info['name']}")
            print(f"  描述: {agent_info['description']}")
            print(f"  技能: {', '.join(agent_info['skills_required'])}")
            print()
    else:
        print(f"❌ 未知命令: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()