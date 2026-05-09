#!/usr/bin/env python3
"""
G12 规划器 - 调用Ralph-loop进行架构规划
仅用于规划，不影响实盘交易
"""
import subprocess, json, os
from datetime import datetime

RALPH_SKILL = '~/.openclaw/workspace/.agents/skills/ralph-loop/SKILL.md'

def read_ralph_skill():
    path = os.path.expanduser(RALPH_SKILL)
    if os.path.exists(path):
        with open(path) as f:
            return f.read()
    return None

def ask_ralph_planning(task_description):
    """调用Ralph进行规划"""
    print("🤖 正在咨询Ralph-loop架构规划...")
    
    # 读取ralph-loop skill指引
    skill_content = read_ralph_skill()
    
    planning_prompt = f"""
# G12 开发规划请求

## 任务描述
{task_description}

## 当前G12系统状态
- 最优参数: RSI 28/70, TP 15%, 仓位 35%, 5x杠杆
- 回测收益: +168.82%, 胜率 71.4%
- 核心文件: unified.py, god_mode.py, trader.py

## Ralph-loop指引
{skill_content[:2000] if skill_content else 'Ralph-loop skill未找到'}

## 请按Ralph-loop方法论:
1. 定义用户故事和验收标准
2. 规划开发流程
3. 设置测试验证
4. 执行迭代

请给出架构建议和开发计划。
"""
    
    print(f"\n📋 规划任务: {task_description}")
    print("💡 Ralph-loop规划模式已启动")
    print("   (仅规划不执行,实盘保护)")
    
    return planning_prompt

def plan_feature(feature_name, description):
    """规划新功能"""
    print(f"\n{'='*60}")
    print(f"📐 G12 功能规划: {feature_name}")
    print('='*60)
    
    prompt = ask_ralph_planning(f"功能: {feature_name}\n描述: {description}")
    
    # 这里可以调用实际的AI规划
    # 当前先打印规划模板
    print("""
    规划模板:
    1. 📝 用户故事
       作为一个... 我想要... 以便...
    
    2. ✅ 验收标准
       - [ ] 标准1
       - [ ] 标准2
    
    3. 🔄 开发流程
       Step 1: 
       Step 2: 
       Step 3: 
    
    4. 🧪 测试验证
       测试用例1:
       测试用例2:
    
    5. ⚡ 实施计划
       优先级: P0/P1/P2
       预计时间:
    """)
    
    print(f"\n💡 规划完成! 建议先创建快照再实施变更。")
    print(f"   快照命令: python3 g12_governance/g12_snapshot.py snap '{feature_name}规划前'")

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        feature = sys.argv[1]
        desc = sys.argv[2] if len(sys.argv) > 2 else ""
        plan_feature(feature, desc)
    else:
        print("""
        G12 规划器 - Ralph-loop架构规划
        
        用法:
          python3 g12_planner.py "<功能名称>" "<功能描述>"
        
        示例:
          python3 g12_planner.py "增加止损优化" "在原有SL基础上增加动态止损"
        
        注意: 此工具仅用于规划阶段,不影响实盘交易
        """)
