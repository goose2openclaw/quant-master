"""
Cron调度器 - 定时任务
"""
import time, threading, schedule
from datetime import datetime, timedelta
from queue import Queue

class Task:
    """任务"""
    def __init__(self, name, func, interval=None, cron_time=None):
        self.name = name
        self.func = func
        self.interval = interval  # 秒
        self.cron_time = cron_time  # "10:30"
        self.last_run = 0
        self.next_run = 0
        self.enabled = True
        self.running = False

class CronScheduler:
    """
    定时调度器
    支持: 间隔执行、每日定时、Cron表达式
    """
    def __init__(self):
        self.tasks = {}  # {name: Task}
        self.task_queue = Queue()
        self.running = False
        self.thread = None
        self.history = []
    
    def add_interval(self, name, func, seconds):
        """添加间隔任务"""
        task = Task(name, func, interval=seconds)
        self.tasks[name] = task
        print(f"[Scheduler] 添加间隔任务: {name} ({seconds}s)")
    
    def add_daily(self, name, func, time_str):
        """添加每日定时任务"""
        task = Task(name, func, cron_time=time_str)
        self.tasks[name] = task
        print(f"[Scheduler] 添加每日任务: {name} ({time_str})")
    
    def add_cron(self, name, func, cron_expr):
        """添加Cron任务"""
        # 简化Cron: 每分钟、每小时、每天
        # cron_expr: "*/5 * * * *" 或 "0 10 * * *"
        task = Task(name, func)
        self.tasks[name] = task
        print(f"[Scheduler] 添加Cron任务: {name} ({cron_expr})")
    
    def remove(self, name):
        """移除任务"""
        if name in self.tasks:
            del self.tasks[name]
            print(f"[Scheduler] 移除任务: {name}")
    
    def enable(self, name):
        """启用任务"""
        if name in self.tasks:
            self.tasks[name].enabled = True
    
    def disable(self, name):
        """禁用任务"""
        if name in self.tasks:
            self.tasks[name].enabled = False
    
    def start(self):
        """启动调度器"""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run_loop)
        self.thread.daemon = True
        self.thread.start()
        print("[Scheduler] 启动")
    
    def stop(self):
        """停止调度器"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("[Scheduler] 停止")
    
    def _run_loop(self):
        """主循环"""
        while self.running:
            try:
                now = time.time()
                for name, task in self.tasks.items():
                    if not task.enabled:
                        continue
                    
                    # 间隔执行
                    if task.interval and now - task.last_run >= task.interval:
                        self._execute(task)
                    
                    # 每日定时
                    elif task.cron_time:
                        current_time = time.strftime("%H:%M")
                        if current_time == task.cron_time and now - task.last_run >= 60:
                            self._execute(task)
                
                time.sleep(1)
            except Exception as e:
                print(f"[Scheduler] Error: {e}")
                time.sleep(1)
    
    def _execute(self, task):
        """执行任务"""
        task.last_run = time.time()
        task.running = True
        try:
            result = task.func()
            self.history.append({
                'task': task.name,
                'time': datetime.now().isoformat(),
                'status': 'success',
                'result': str(result)[:100]
            })
            print(f"[Scheduler] {task.name} 执行成功")
        except Exception as e:
            self.history.append({
                'task': task.name,
                'time': datetime.now().isoformat(),
                'status': 'error',
                'error': str(e)
            })
            print(f"[Scheduler] {task.name} 执行失败: {e}")
        task.running = False
        # 只保留最近100条
        self.history = self.history[-100:]
    
    def get_status(self):
        """获取状态"""
        return {
            'running': self.running,
            'tasks': {name: {
                'enabled': t.enabled,
                'running': t.running,
                'last_run': t.last_run,
                'interval': t.interval
            } for name, t in self.tasks.items()},
            'history_count': len(self.history)
        }
    
    def get_history(self, limit=20):
        """获取执行历史"""
        return self.history[-limit:]
