#!/usr/bin/env python3
"""
Go2Se Skill for OpenClaw
"""

import sys
import json
import subprocess
import requests
from typing import Dict, Any

# Web UI URL
WEB_URL = "http://localhost:5000"

class Go2SeSkill:
    """Go2Se OpenClaw Skill"""
    
    def __init__(self):
        self.commands = {
            "start": self.start_platform,
            "markets": self.get_markets,
            "signals": self.get_signals,
            "strategies": self.get_strategies,
            "oracle": self.get_oracle,
            "airdrop": self.hunt_airdrop,
            "backtest": self.run_backtest,
            "portfolio": self.get_portfolio,
            "preset": self.apply_preset,
            "services": self.get_services,
            "status": self.get_status,
        }
    
    def api_call(self, endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
        """API调用"""
        try:
            url = f"{WEB_URL}{endpoint}"
            if method == "GET":
                resp = requests.get(url, timeout=10)
            else:
                resp = requests.post(url, json=data, timeout=10)
            return resp.json() if resp.status_code == 200 else {}
        except:
            return {"error": "Web UI未启动，请先运行 go2se start"}
    
    def start_platform(self, args: list = None) -> str:
        """启动平台"""
        # 启动Web UI
        subprocess.Popen(
            ["python3", "/root/.openclaw/workspace/skills/go2se/web/server.py"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return f"""
🪿 Go2Se Platform 启动中...

📍 Web UI: http://localhost:5000

功能:
- 7连环市场
- 12竞品策略
- 多源信号
- 预言机
- 薅羊毛
- 回测工具
"""
    
    def get_markets(self, args: list = None) -> str:
        """获取市场数据"""
        data = self.api_call("/api/markets")
        if "error" in data:
            return data["error"]
        
        result = "🎯 7连环市场\n" + "="*50 + "\n\n"
        
        for m in data.get("markets", []):
            daily = m.get("performance", {}).get("daily", 0)
            sign = "+" if daily >= 0 else ""
            result += f"{m['icon']} {m['name']}\n"
            result += f"   描述: {m['description']}\n"
            result += f"   日: {sign}{daily}%\n"
            result += f"   PnL: ${m.get('pnl', 0)}\n\n"
        
        return result
    
    def get_signals(self, args: list = None) -> str:
        """获取信号"""
        data = self.api_call("/api/signals")
        if "error" in data:
            return data["error"]
        
        result = "📡 交易信号\n" + "="*50 + "\n\n"
        
        for s in data.get("signals", []):
            action = "🟢买入" if s["action"] == "BUY" else "🟡持有"
            result += f"{s['coin']} | {action} | 置信度:{s['confidence']} | 收益:+{s['potential']}%\n"
            if s.get("sources"):
                result += f"   来源: {','.join(s['sources'])}\n"
            result += "\n"
        
        return result
    
    def get_strategies(self, args: list = None) -> str:
        """获取策略"""
        data = self.api_call("/api/strategies")
        if "error" in data:
            return data["error"]
        
        result = "♟️ 12竞品策略整合\n" + "="*50 + "\n\n"
        
        for i, s in enumerate(data.get("strategies", []), 1):
            result += f"{i}. {s['name']} [{s['source']}]\n"
            result += f"   {s['description']}\n\n"
        
        return result
    
    def get_oracle(self, args: list = None) -> str:
        """获取预言机"""
        data = self.api_call("/api/oracle")
        if "error" in data:
            return data["error"]
        
        result = "🔗 预言机事件\n" + "="*50 + "\n\n"
        
        for e in data.get("events", []):
            impact = e.get("impact", 0)
            sign = "+" if impact >= 0 else ""
            result += f"{e['type']} → {e['symbol']}\n"
            result += f"   影响: {sign}{impact}% | 来源: {e['source']}\n"
            result += f"   {e.get('description', '')}\n\n"
        
        return result
    
    def hunt_airdrop(self, args: list = None) -> str:
        """薅羊毛"""
        data = self.api_call("/api/airdrop/hunt")
        if "error" in data:
            return data["error"]
        
        result = "🐑 薅羊毛\n" + "="*50 + "\n\n"
        
        if data.get("success"):
            for a in data.get("airdrops", []):
                result += f"✅ 发现 {a['coin']}: +${a['amount']}\n"
            result += f"\n累计收益: ${data.get('total', 0)}"
        else:
            result = "未发现新空投"
        
        return result
    
    def run_backtest(self, args: list = None) -> str:
        """回测"""
        capital = 10000
        days = 30
        
        if args:
            try:
                capital = int(args[0]) if len(args) > 0 else 10000
                days = int(args[1]) if len(args) > 1 else 30
            except:
                pass
        
        data = self.api_call("/api/backtest", "POST", {"capital": capital, "days": days})
        if "error" in data:
            return data["error"]
        
        r = data.get("result", {})
        return f"""
🔬 回测结果
{'='*50}

初始资金: ${r.get('initial', 0)}
最终资金: ${r.get('final', 0)}
盈亏: ${r.get('pnl', 0)} ({r.get('pnl_percent', 0)}%)
胜率: {r.get('win_rate', 0)}%
最大回撤: {r.get('max_drawdown', 0)}%
"""
    
    def get_portfolio(self, args: list = None) -> str:
        """投资组合"""
        data = self.api_call("/api/portfolio")
        if "error" in data:
            return data["error"]
        
        p = data.get("portfolio", {})
        perf = data.get("performance", {})
        
        result = "💼 投资组合\n" + "="*50 + "\n\n"
        
        for name, conf in p.items():
            result += f"{name}: {conf.get('weight', 0)}% | PnL: ${conf.get('pnl', 0)}\n"
        
        result += f"\n总盈亏: ${perf.get('total_pnl', 0)}"
        
        return result
    
    def apply_preset(self, args: list = None) -> str:
        """应用预设"""
        if not args:
            return "请指定预设: conservative / balanced / aggressive"
        
        preset = args[0]
        data = self.api_call(f"/api/preset/{preset}")
        
        if data.get("success"):
            return f"✅ 已应用预设: {preset}"
        return "❌ 预设应用失败"
    
    def get_services(self, args: list = None) -> str:
        """服务模式"""
        data = self.api_call("/api/services")
        if "error" in data:
            return data["error"]
        
        result = "👑 服务模式\n" + "="*50 + "\n\n"
        
        for name, info in data.items():
            result += f"{info['name']}: ¥{info['price']}/月\n"
            result += f"   功能: {', '.join(info['features'])}\n\n"
        
        return result
    
    def get_status(self, args: list = None) -> str:
        """状态"""
        data = self.api_call("/api/trading/status")
        if "error" in data:
            return data["error"]
        
        running = "🔴 已停止" if not data.get("running") else "🟢 运行中"
        
        return f"""
🪿 Go2Se 状态
{'='*50}

交易: {running}
总盈亏: ${data.get('total_pnl', 0)}
胜率: {data.get('win_rate', 0)}%

📍 Web UI: http://localhost:5000
"""
    
    def run(self, command: str, args: list = None) -> str:
        """运行命令"""
        if command in self.commands:
            return self.commands[command](args)
        
        return f"""
🪿 Go2Se 命令帮助

可用命令:
- go2se start        启动平台
- go2se markets      查看市场
- go2se signals     查看信号
- go2se strategies  查看策略
- go2se oracle      预言机
- go2se airdrop    薅羊毛
- go2se backtest   回测
- go2se portfolio  组合
- go2se services   服务
- go2se status     状态
- go2se preset     预设 (conservative/balanced/aggressive)

📍 Web UI: http://localhost:5000
"""


def main():
    skill = Go2SeSkill()
    
    if len(sys.argv) < 2:
        print(skill.run("help"))
        return
    
    command = sys.argv[1]
    args = sys.argv[2:] if len(sys.argv) > 2 else None
    
    result = skill.run(command, args)
    print(result)


if __name__ == "__main__":
    main()
