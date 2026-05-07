#!/usr/bin/env python3
"""
简单任务调度器（替代cron技能）
"""

import schedule
import time
from datetime import datetime

def job():
    print(f"任务执行时间: {datetime.now()}")

# 设置定时任务
schedule.every(10).minutes.do(job)
schedule.every().hour.do(job)
schedule.every().day.at("10:30").do(job)

print("任务调度器已启动...")
while True:
    schedule.run_pending()
    time.sleep(1)
