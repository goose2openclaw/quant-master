"""通知器 - 微信/邮件/TG"""
import requests
from threading import Thread

class Notifier:
    def __init__(self):
        self.handlers = []
    
    def add_handler(self, handler):
        self.handlers.append(handler)
    
    def send(self, msg, level='info'):
        for handler in self.handlers:
            try:
                handler.send(msg, level)
            except Exception as e:
                print(f"[Notifier] Error: {e}")

class TelegramHandler:
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
    
    def send(self, msg, level='info'):
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = {'chat_id': self.chat_id, 'text': f"[{level.upper()}] {msg}"}
        try:
            requests.post(url, data=data, timeout=10)
        except:
            pass

class WebhookHandler:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
    
    def send(self, msg, level='info'):
        try:
            requests.post(self.webhook_url, json={'text': f"[{level.upper()}] {msg}"}, timeout=10)
        except:
            pass

class LogHandler:
    def __init__(self, log_file):
        self.log_file = log_file
    
    def send(self, msg, level='info'):
        with open(self.log_file, 'a') as f:
            f.write(f"[{level.upper()}] {msg}\n")
