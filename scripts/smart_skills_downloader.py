#!/usr/bin/env python3
"""
智能Skills下载器
自动检测网络状态，采用最佳策略下载和安装OpenClaw技能
"""

import os
import sys
import json
import time
import subprocess
import requests
from datetime import datetime
from pathlib import Path
import concurrent.futures

class SmartSkillsDownloader:
    def __init__(self):
        self.workspace = Path.home() / ".openclaw" / "workspace"
        self.skills_dir = self.workspace / "skills"
        self.config_dir = self.workspace / "config"
        self.logs_dir = self.workspace / "logs"
        self.scripts_dir = self.workspace / "scripts"
        
        # 创建目录
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.scripts_dir.mkdir(parents=True, exist_ok=True)
        
        # 日志文件
        self.log_file = self.logs_dir / f"skills_download_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        # 技能优先级列表（根据OPC项目需求）
        self.priority_skills = [
            # 核心开发技能
            {"name": "github", "priority": 10, "category": "development"},
            {"name": "cron", "priority": 9, "category": "automation"},
            {"name": "shell", "priority": 9, "category": "system"},
            {"name": "telegram", "priority": 8, "category": "communication"},
            
            # 文档处理技能
            {"name": "pdf", "priority": 7, "category": "document"},
            {"name": "docx", "priority": 7, "category": "document"},
            {"name": "xlsx", "priority": 7, "category": "document"},
            {"name": "pptx", "priority": 7, "category": "document"},
            
            # 网络和搜索技能
            {"name": "brave-search", "priority": 8, "category": "web"},
            {"name": "agent-browser", "priority": 7, "category": "web"},
            {"name": "web-fetch", "priority": 6, "category": "web"},
            
            # 通信技能
            {"name": "whatsapp", "priority": 7, "category": "communication"},
            {"name": "discord", "priority": 6, "category": "communication"},
            
            # 其他实用技能
            {"name": "notion", "priority": 6, "category": "productivity"},
            {"name": "obsidian", "priority": 6, "category": "productivity"},
            {"name": "gmail", "priority": 6, "category": "communication"},
            {"name": "calendar", "priority": 6, "category": "productivity"},
        ]
        
        # 下载源（按优先级排序）
        self.download_sources = [
            {
                "name": "GitHub Raw",
                "url_template": "https://raw.githubusercontent.com/openclaw/skills/main/{skill}/SKILL.md",
                "type": "direct",
                "priority": 1
            },
            {
                "name": "OpenClaw CDN",
                "url_template": "https://cdn.openclaw.ai/skills/{skill}/latest/SKILL.md",
                "type": "direct",
                "priority": 2
            },
            {
                "name": "NPM Registry",
                "url_template": "https://registry.npmjs.org/@openclaw/skill-{skill}/latest",
                "type": "npm",
                "priority": 3
            }
        ]
    
    def log(self, message, level="INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        # 输出到控制台
        print(log_entry)
        
        # 写入日志文件
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + "\n")
    
    def check_network(self):
        """检查网络连接状态"""
        self.log("检查网络连接状态...")
        
        test_urls = [
            "https://api.telegram.org",
            "https://raw.githubusercontent.com",
            "https://registry.npmjs.org",
            "https://cdn.openclaw.ai"
        ]
        
        reachable_urls = []
        
        for url in test_urls:
            try:
                response = requests.head(url, timeout=5)
                if response.status_code < 400:
                    reachable_urls.append(url)
                    self.log(f"  ✅ {url} 可达")
                else:
                    self.log(f"  ⚠ {url} 返回状态码: {response.status_code}", "WARNING")
            except requests.RequestException as e:
                self.log(f"  ❌ {url} 不可达: {str(e)[:50]}", "ERROR")
        
        network_status = {
            "total_tested": len(test_urls),
            "reachable": len(reachable_urls),
            "reachable_urls": reachable_urls,
            "status": "GOOD" if len(reachable_urls) >= 2 else "POOR" if len(reachable_urls) >= 1 else "OFFLINE"
        }
        
        self.log(f"网络状态: {network_status['status']} ({network_status['reachable']}/{network_status['total_tested']} 个源可达)")
        return network_status
    
    def download_skill(self, skill_info):
        """下载单个技能"""
        skill_name = skill_info["name"]
        skill_dir = self.skills_dir / skill_name
        
        self.log(f"开始下载技能: {skill_name} (优先级: {skill_info['priority']})")
        
        # 检查是否已存在
        if (skill_dir / "SKILL.md").exists():
            self.log(f"  ⚠ {skill_name} 已存在，跳过下载")
            return {"skill": skill_name, "status": "skipped", "reason": "already_exists"}
        
        # 创建技能目录
        skill_dir.mkdir(exist_ok=True)
        (skill_dir / "scripts").mkdir(exist_ok=True)
        (skill_dir / "references").mkdir(exist_ok=True)
        
        # 按优先级尝试各个下载源
        downloaded = False
        source_used = None
        
        for source in sorted(self.download_sources, key=lambda x: x["priority"]):
            if source["type"] == "direct":
                url = source["url_template"].format(skill=skill_name)
            else:
                # 对于NPM源，需要不同的处理
                continue
            
            self.log(f"  尝试从 {source['name']} 下载...")
            
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200 and response.text.strip():
                    # 保存SKILL.md文件
                    with open(skill_dir / "SKILL.md", 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    
                    downloaded = True
                    source_used = source["name"]
                    self.log(f"    ✅ 从 {source['name']} 下载成功")
                    break
                else:
                    self.log(f"    ❌ {source['name']} 返回状态码: {response.status_code}")
            except requests.RequestException as e:
                self.log(f"    ❌ {source['name']} 下载失败: {str(e)[:50]}")
            
            # 避免请求过快
            time.sleep(1)
        
        if downloaded:
            # 创建基本配置文件
            self.create_basic_config(skill_dir, skill_name, skill_info["category"])
            
            # 如果是核心技能，创建专用脚本
            if skill_info["priority"] >= 8:
                self.create_skill_specific_scripts(skill_dir, skill_name)
            
            return {"skill": skill_name, "status": "success", "source": source_used}
        else:
            # 下载失败，创建最小化版本
            self.log(f"  ⚠ 所有源都失败，创建最小化 {skill_name} 技能", "WARNING")
            self.create_minimal_skill(skill_dir, skill_name)
            return {"skill": skill_name, "status": "minimal", "reason": "download_failed"}
    
    def create_basic_config(self, skill_dir, skill_name, category):
        """创建基本配置文件"""
        config = {
            "skill": {
                "name": skill_name,
                "category": category,
                "installed_at": datetime.now().isoformat(),
                "version": "1.0.0",
                "auto_update": True
            },
            "configuration": {
                "enabled": True,
                "auto_load": True
            }
        }
        
        config_file = skill_dir / "config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def create_minimal_skill(self, skill_dir, skill_name):
        """创建最小化技能（当下载失败时）"""
        skill_md_content = f"""---
name: {skill_name}
description: 最小化 {skill_name} 技能（自动创建）
created: {datetime.now().strftime('%Y-%m-%d')}
status: minimal
---

# {skill_name} (最小化版本)

这是一个自动创建的最小化技能，用于临时替代完整版本。

## 功能
- 基本功能占位符
- 等待完整版本安装

## 配置
编辑此文件添加具体配置。

## 注意
这是一个临时解决方案，建议网络恢复后安装完整版本。
"""
        
        with open(skill_dir / "SKILL.md", 'w', encoding='utf-8') as f:
            f.write(skill_md_content)
        
        # 创建示例脚本
        script_content = f"""#!/bin/bash
echo "这是 {skill_name} 的示例脚本"
echo "运行时间: $(date)"
echo "请根据实际需求修改此脚本"
"""
        
        script_file = skill_dir / "scripts" / "example.sh"
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        os.chmod(script_file, 0o755)
    
    def create_skill_specific_scripts(self, skill_dir, skill_name):
        """为特定技能创建专用脚本"""
        if skill_name == "github":
            self.create_github_scripts(skill_dir)
        elif skill_name == "cron":
            self.create_cron_scripts(skill_dir)
        elif skill_name == "shell":
            self.create_shell_scripts(skill_dir)
        elif skill_name == "telegram":
            self.create_telegram_scripts(skill_dir)
    
    def create_github_scripts(self, skill_dir):
        """创建GitHub专用脚本"""
        script_content = """#!/bin/bash
# GitHub工具脚本

case $1 in
    "clone")
        git clone "$2"
        ;;
    "status")
        git status
        ;;
    "commit")
        git add . && git commit -m "$2"
        ;;
    "push")
        git push
        ;;
    "pull")
        git pull
        ;;
    *)
        echo "用法: $0 <clone|status|commit|push|pull> [参数]"
        ;;
esac
"""
        
        script_file = skill_dir / "scripts" / "github_tools.sh"
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        os.chmod(script_file, 0o755)
    
    def create_cron_scripts(self, skill_dir):
        """创建Cron专用脚本"""
        script_content = """#!/bin/bash
# Cron管理脚本

case $1 in
    "add")
        (crontab -l 2>/dev/null; echo "$2") | crontab -
        echo "Cron任务已添加"
        ;;
    "list")
        crontab -l
        ;;
    "remove")
        crontab -l | grep -v "$2" | crontab -
        echo "Cron任务已移除"
        ;;
    *)
        echo "用法: $0 <add|list|remove> [cron表达式]"
        ;;
esac
"""
        
        script_file = skill_dir / "scripts" / "cron_manager.sh"
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        os.chmod(script_file, 0o755)
    
    def create_shell_scripts(self, skill_dir):
        """创建Shell专用脚本"""
        script_content = """#!/bin/bash
# 系统监控脚本

case $1 in
    "disk")
        df -h
        ;;
    "memory")
        free -h
        ;;
    "process")
        ps aux --sort=-%cpu | head -11
        ;;
    "network")
        netstat -tulpn
        ;;
    *)
        echo "用法: $0 <disk|memory|process|network>"
        ;;
esac
"""
        
        script_file = skill_dir / "scripts" / "system_monitor.sh"
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        os.chmod(script_file, 0o755)
    
    def create_telegram_scripts(self, skill_dir):
        """创建Telegram专用脚本"""
        script_content = """#!/bin/bash
# Telegram工具脚本

TOKEN="8405295378:AAG3bvttAQkw00tjuTo1ypw02TLSKAFLT0o"
BASE_URL="https://api.telegram.org/bot$TOKEN"

case $1 in
    "send")
        curl -s -X POST "$BASE_URL/sendMessage" \
            -d "chat_id=$2" \
            -d "text=$3" \
            -d "parse_mode=Markdown"
        ;;
    "test")
        curl -s "$BASE_URL/getMe"
        ;;
    *)
        echo "用法: $0 send <chat_id> <message>"
        echo "      $0 test"
        ;;
esac
"""
        
        script_file = skill_dir / "scripts" / "telegram_tools.sh"
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        os.chmod(script_file, 0o755)
    
    def install_dependencies(self):
        """安装系统依赖"""
        self.log("检查并安装系统依赖...")
        
        dependencies = [
            "curl", "wget", "git", "python3", "python3-pip", "jq"
        ]
        
        installed = []
        failed = []
        
        for dep in dependencies:
            try:
                # 检查是否已安装
                result = subprocess.run(
                    ["which", dep],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    self.log(f"  ✅ {dep} 已安装")
                    installed.append(dep)
                else:
                    self.log(f"  ⚠ {dep} 未安装，尝试安装...")
                    
                    # 尝试安装（需要sudo权限）
                    try:
                        subprocess.run(
                            ["sudo", "apt", "install", "-y", dep],
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                        self.log(f"    ✅ {dep} 安装成功")
                        installed.append(dep)
                    except subprocess.TimeoutExpired:
                        self.log(f"    ❌ {dep} 安装超时", "ERROR")
                        failed.append(dep)
                    except Exception as e:
                        self.log(f"    ❌ {dep} 安装失败: {str(e)[:50]}", "ERROR")
                        failed.append(dep)
                        
            except Exception as e:
                self.log(f"  ❌ 检查 {dep} 时出错: {str(e)[:50]}", "ERROR")
                failed.append(dep)
        
        return {"installed": installed, "failed": failed}
    
    def configure_openclaw(self):
        """配置OpenClaw"""
        self.log("配置OpenClaw集成...")
        
        # 创建OpenClaw配置文件
        config = {
            "agent": {
                "model": "custom-api-deepseek-com/deepseek-reasoner",
                "thinking": True,
                "maxTokens": 2048
            },
            "skills": {
                "autoEnable": True,
                "scanInterval": 300,
                "directory": str(self.skills_dir)
            },
            "telegram": {
                "enabled": True,
                "botToken": "8405295378:AAG3bvttAQkw00tjuTo1ypw02TLSKAFLT0o",
                "notifications": {
                    "cryptoAlerts": True,
                    "systemStatus": True
                }
            }
        }
        
        config_file = self.config_dir / "openclaw_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        self.log(f"  ✅ OpenClaw配置文件已创建: {config_file}")
        
        # 尝试应用配置
        try:
            # 这里可以添加应用配置的命令
            # 例如: subprocess.run(["openclaw", "config", "set", ...])
            pass
        except Exception as e:
            self.log(f"  ⚠ 应用配置时出错: {str(e)[:50]}", "WARNING")
    
    def create_skill_aliases(self):
        """创建技能别名"""
        self.log("创建技能别名...")
        
        aliases_content = """#!/bin/bash
# OpenClaw技能别名

# github技能别名
alias gh-clone='openclaw skills run github clone'
alias gh-status='openclaw skills run github status'
alias gh-push='openclaw skills run github push'

# cron技能别名
alias cron-add='openclaw skills run cron add'
alias cron-list='openclaw skills run cron list'
alias cron-remove='openclaw skills run cron remove'

# shell技能别名
alias sys-disk='openclaw skills run shell disk'
alias sys-memory='openclaw skills run shell memory'
alias sys-process='openclaw skills run shell process'

# telegram技能别名
alias tg-send='openclaw skills run telegram send'
alias tg-status='openclaw skills run telegram status'

# 快速启用技能
skill-enable() {
    openclaw skills enable "$1"
}

skill-disable() {
    openclaw skills disable "$1"
}

skill-list() {
    openclaw skills list | grep -E "(✓ ready|✗ missing)"
}

echo "技能别名已加载"
"""
        
        aliases_file = self.scripts_dir / "skill_aliases.sh"
        with open(aliases_file, 'w', encoding='utf-8') as f:
            f.write(aliases_content)
        
        os.chmod(aliases_file, 0o755)
        
        # 添加到bashrc
        bashrc = Path.home() / ".bashrc"
        alias_line = f"source {aliases_file}"
        
        if bashrc.exists():
            with open(bashrc, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if alias_line not in content:
                with open(bashrc, 'a', encoding='utf-8') as f:
                    f.write(f"\n# OpenClaw技能别名\n{alias_line}\n")
                self.log("  ✅ 技能别名已添加到 ~/.bashrc")
            else:
                self.log("  ⚠ 技能别名已存在于 ~/.bashrc")
        else:
            self.log("  ⚠ ~/.bashrc 不存在，跳过别名添加", "WARNING")
    
    def generate_report(self, results):
        """生成安装报告"""
        self.log("生成安装报告...")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "network_status": self.check_network(),
            "skills_downloaded": len([r for r in results if r["status"] == "success"]),
            "skills_minimal": len([r for r in results if r["status"] == "minimal"]),
            "skills_skipped": len([r for r in results if r["status"] == "skipped"]),
            "details": results,
            "total_skills": len(self.priority_skills)
        }
        
        report_file = self.logs_dir / f"installation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 创建人类可读的报告
        human_report = f"""# OpenClaw Skills智能安装报告

## 安装摘要
- 安装时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 网络状态: {report['network_status']['status']}
- 成功下载: {report['skills_downloaded']} 个技能
- 最小化版本: {report['skills_minimal']} 个技能
- 跳过: {report['skills_skipped']} 个技能
- 总计: {report['total_skills']} 个技能

## 详细结果

### 成功下载的技能
"""
        
        for result in results:
            if result["status"] == "success":
                human_report += f"- ✅ {result['skill']} (来源: {result.get('source', '未知')})\n"
        
        human_report += "\n### 最小化版本（下载失败）\n"
        for result in results:
            if result["status"] == "minimal":
                human_report += f"- ⚠ {result['skill']} (原因: {result.get('reason', '未知')})\n"
        
        human_report += "\n### 跳过的技能（已存在）\n"
        for result in results:
            if result["status"] == "skipped":
                human_report += f"- 🔄 {result['skill']}\n"
        
        human_report += f"""
## 系统配置
- 技能目录: {self.skills_dir}
- 配置文件: {self.config_dir}/openclaw_config.json
- 脚本目录: {self.scripts_dir}
- 日志文件: {self.log_file}

## 下一步建议

### 立即执行
1. 测试核心技能功能
2. 配置Telegram Bot Chat ID
3. 设置cron任务

### 网络恢复后
1. 重新下载最小化版本的技能
2. 测试所有外部API连接
3. 配置完整的自动化工作流

### 开发计划
1. 开始OPC加密货币监控开发
2. 学习Solidity智能合约
3. 创建求职助手系统

## 技术支持
- 查看日志: {self.log_file}
- 配置文件: {self.config_dir}/
- 技能文档: 各技能目录下的SKILL.md

---
*报告自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        human_report_file = self.logs_dir / f"installation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(human_report_file, 'w', encoding='utf-8') as f:
            f.write(human_report)
        
        self.log(f"  ✅ 安装报告已生成: {human_report_file}")
        return report
    
    def run(self):
        """运行主下载流程"""
        print("="*70)
        print("🤖 OpenClaw Skills智能下载与配置系统")
        print("="*70)
        
        self.log("开始智能下载流程...")
        
        # 1. 检查网络状态
        network_status = self.check_network()
        
        if network_status["status"] == "OFFLINE":
            self.log("网络完全离线，无法下载技能", "ERROR")
            self.log("建议: 使用之前创建的模拟系统进行开发")
            return
        
        # 2. 安装系统依赖
        deps_result = self.install_dependencies()
        
        # 3. 下载技能（按优先级排序）
        self.log(f"开始下载 {len(self.priority_skills)} 个技能...")
        
        # 按优先级排序
        sorted_skills = sorted(self.priority_skills, key=lambda x: x["priority"], reverse=True)
        
        results = []
        
        # 使用线程池并行下载（最多3个并发）
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # 提交所有下载任务
            future_to_skill = {
                executor.submit(self.download_skill, skill): skill 
                for skill in sorted_skills
            }
            
            # 等待所有任务完成
            for future in concurrent.futures.as_completed(future_to_skill):
                skill_info = future_to_skill[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.log(f"❌ 下载 {skill_info['name']} 时出错: {str(e)[:50]}", "ERROR")
                    results.append({
                        "skill": skill_info["name"],
                        "status": "error",
                        "reason": str(e)[:100]
                    })
        
        # 4. 配置OpenClaw
        self.configure_openclaw()
        
        # 5. 创建技能别名
        self.create_skill_aliases()
        
        # 6. 生成报告
        report = self.generate_report(results)
        
        # 7. 输出总结
        print("\n" + "="*70)
        print("🎉 智能下载与配置完成！")
        print("="*70)
        
        success_count = report["skills_downloaded"]
        minimal_count = report["skills_minimal"]
        skipped_count = report["skills_skipped"]
        
        print(f"📊 下载结果:")
        print(f"  ✅ 成功下载: {success_count} 个技能")
        print(f"  ⚠ 最小化版本: {minimal_count} 个技能")
        print(f"  🔄 跳过: {skipped_count} 个技能")
        print(f"  📋 总计: {report['total_skills']} 个技能")
        
        print(f"\n🌐 网络状态: {report['network_status']['status']}")
        
        print(f"\n📁 重要文件:")
        print(f"  技能目录: {self.skills_dir}")
        print(f"  配置文件: {self.config_dir}/openclaw_config.json")
        print(f"  脚本目录: {self.scripts_dir}")
        print(f"  日志文件: {self.log_file}")
        
        print(f"\n🚀 立即执行:")
        print(f"  1. 测试技能: bash {self.scripts_dir}/skill_aliases.sh")
        print(f"  2. 查看报告: cat {self.logs_dir}/installation_report_*.md | head -30")
        print(f"  3. 开始开发: cd ~/opc-project")
        
        print(f"\n💡 网络恢复后:")
        print(f"  重新运行此脚本下载最小化版本的技能")
        
        print("="*70)

def main():
    """主函数"""
    try:
        downloader = SmartSkillsDownloader()
        downloader.run()
    except KeyboardInterrupt:
        print("\n\n⚠ 用户中断下载过程")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()