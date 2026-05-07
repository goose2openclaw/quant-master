#!/usr/bin/env python3
"""
XIAMI Notification System - 通知系统
支持 Telegram, Discord, Email 通知
"""

import os
import json
import requests
from datetime import datetime
from typing import Optional

class NotificationSystem:
    """通知系统"""
    
    def __init__(self):
        self.telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        self.discord_webhook = os.environ.get('DISCORD_WEBHOOK')
        
    def send_telegram(self, message: str, parse_mode: str = "Markdown") -> dict:
        """发送 Telegram 消息"""
        if not self.telegram_token or not self.telegram_chat_id:
            return {"status": "error", "message": "Telegram not configured"}
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            data = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": parse_mode
            }
            resp = requests.post(url, json=data, timeout=10)
            return {"status": "ok", "response": resp.json()}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def send_discord(self, message: str, embed: dict = None) -> dict:
        """发送 Discord 消息"""
        if not self.discord_webhook:
            return {"status": "error", "message": "Discord not configured"}
        
        try:
            payload = {"content": message}
            if embed:
                payload["embeds"] = [embed]
            
            resp = requests.post(self.discord_webhook, json=payload, timeout=10)
            return {"status": "ok", "status_code": resp.status_code}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def notify_signal(self, signal: dict) -> dict:
        """通知交易信号"""
        emoji = "🟢" if signal.get("action") == "BUY" else "🔴"
        
        message = f"""
{emoji} **{signal.get('symbol', 'N/A')}** {signal.get('action', 'N/A')}

📊 置信度: {signal.get('confidence', 'N/A')}/10
💰 价格: ${signal.get('price', 'N/A')}
📈 止盈: {signal.get('take_profit', 'N/A')}
🛡️ 止损: {signal.get('stop_loss', 'N/A')}
"""
        
        # Discord embed
        embed = {
            "title": f"{emoji} {signal.get('symbol')} {signal.get('action')}",
            "color": 65280 if signal.get("action") == "BUY" else 16711680,
            "fields": [
                {"name": "置信度", "value": f"{signal.get('confidence')}/10", "inline": True},
                {"name": "价格", "value": f"${signal.get('price')}", "inline": True},
                {"name": "止盈", "value": signal.get('take_profit', 'N/A'), "inline": True},
                {"name": "止损", "value": signal.get('stop_loss', 'N/A'), "inline": True},
            ],
            "footer": {"text": f"XIAMI v4.0 • {datetime.now().strftime('%Y-%m-%d %H:%M')}"}
        }
        
        results = []
        if self.telegram_token:
            results.append(self.send_telegram(message))
        if self.discord_webhook:
            results.append(self.send_discord(message, embed))
        
        return {"status": "sent", "methods": results}
    
    def notify_alert(self, title: str, message: str, level: str = "info") -> dict:
        """通知告警"""
        emoji = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "🔴",
            "success": "✅"
        }.get(level, "ℹ️")
        
        full_message = f"{emoji} **{title}**\n{message}"
        
        color_map = {
            "info": 3447003,
            "warning": 16776960,
            "error": 15158332,
            "success": 3066993
        }
        
        embed = {
            "title": f"{emoji} {title}",
            "description": message,
            "color": color_map.get(level, 3447003),
            "footer": {"text": f"XIAMI • {datetime.now().strftime('%Y-%m-%d %H:%M')}"}
        }
        
        results = []
        if self.telegram_token:
            results.append(self.send_telegram(full_message))
        if self.discord_webhook:
            results.append(self.send_discord(full_message, embed))
        
        return {"status": "sent", "methods": results}
    
    def notify_performance(self, stats: dict) -> dict:
        """通知性能报告"""
        message = f"""
📊 **XIAMI 性能日报**

🔥 交易次数: {stats.get('trades', 0)}
✅ 胜率: {stats.get('win_rate', 'N/A')}
💰 盈亏: {stats.get('pnl', 'N/A')}
🛡️ 最大回撤: {stats.get('max_drawdown', 'N/A')}
"""
        
        embed = {
            "title": "📊 XIAMI 性能日报",
            "color": 3066993,
            "fields": [
                {"name": "交易次数", "value": str(stats.get('trades', 0)), "inline": True},
                {"name": "胜率", "value": stats.get('win_rate', 'N/A'), "inline": True},
                {"name": "盈亏", "value": stats.get('pnl', 'N/A'), "inline": True},
                {"name": "最大回撤", "value": stats.get('max_drawdown', 'N/A'), "inline": True},
            ],
            "footer": {"text": f"XIAMI v4.0 • {datetime.now().strftime('%Y-%m-%d')}"}
        }
        
        results = []
        if self.telegram_token:
            results.append(self.send_telegram(message))
        if self.discord_webhook:
            results.append(self.send_discord(message, embed))
        
        return {"status": "sent", "methods": results}
    
    def test_notification(self) -> dict:
        """测试通知"""
        return self.notify_alert(
            "🔔 XIAMI 通知测试",
            "通知系统配置成功！\nTelegram: ✅\nDiscord: ✅",
            "success"
        )


def main():
    import sys
    
    notifier = NotificationSystem()
    
    if len(sys.argv) < 2:
        print("""
📋 XIAMI 通知系统

用法:
  python notification_system.py test
  python notification_system.py signal <symbol> <action> <confidence>
  python notification_system.py alert <title> <message> <level>
  python notification_system.py performance

示例:
  python notification_system.py test
  python notification_system.py signal BTC BUY 8.5
  python notification_system.py alert "交易信号" "BTC买入信号" info
""")
        return
    
    cmd = sys.argv[1]
    
    if cmd == 'test':
        result = notifier.test_notification()
        print(json.dumps(result, indent=2))
    
    elif cmd == 'signal':
        signal = {
            "symbol": sys.argv[2] if len(sys.argv) > 2 else "BTC",
            "action": sys.argv[3] if len(sys.argv) > 3 else "BUY",
            "confidence": float(sys.argv[4]) if len(sys.argv) > 4 else 8.5,
            "price": "69,000",
            "take_profit": "5%",
            "stop_loss": "2%"
        }
        result = notifier.notify_signal(signal)
        print(json.dumps(result, indent=2))
    
    elif cmd == 'alert':
        title = sys.argv[2] if len(sys.argv) > 2 else "Test"
        message = sys.argv[3] if len(sys.argv) > 3 else "Test message"
        level = sys.argv[4] if len(sys.argv) > 4 else "info"
        result = notifier.notify_alert(title, message, level)
        print(json.dumps(result, indent=2))
    
    elif cmd == 'performance':
        stats = {
            "trades": 8,
            "win_rate": "75%",
            "pnl": "+$156.00",
            "max_drawdown": "-3.2%"
        }
        result = notifier.notify_performance(stats)
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
