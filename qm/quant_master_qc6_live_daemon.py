"""
QuantMaster Q@C v6 LIVE Daemon - 实盘自动重启版
"""
import sys
import time
import signal
import os

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

RESTART_DELAY = 5
MAX_RESTARTS_PER_HOUR = 10
LOG_FILE = '/home/goose/.openclaw/workspace/qc6_live_daemon.log'

class QCV6LiveDaemon:
    def __init__(self):
        self.running = True
        self.restart_count = 0
        self.restart_times = []
        self.cycle_count = 0
        
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        signal.signal(signal.SIGINT, self.handle_shutdown)
        
        self.log("🚀 Q@C v6 LIVE Daemon 启动")
    
    def log(self, msg):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {msg}")
        try:
            with open(LOG_FILE, 'a') as f:
                f.write(f"[{timestamp}] {msg}\n")
        except:
            pass
    
    def handle_shutdown(self, signum, frame):
        self.running = False
        self.log("📤 收到停止信号,正在关闭...")
    
    def should_restart(self):
        now = time.time()
        self.restart_times = [t for t in self.restart_times if now - t < 3600]
        return len(self.restart_times) < MAX_RESTARTS_PER_HOUR
    
    def run_cycle(self):
        try:
            from qm.quant_master_qc6 import QuantMasterQC6
            
            qm = QuantMasterQC6(10000)
            qm.mode = 'LIVE'
            
            self.log("📊 开始运行周期...")
            
            # 运行一个完整周期
            result = qm.run_full_cycle()
            self.cycle_count += 1
            
            self.log(f"✅ 周期 #{self.cycle_count} 完成: {len(result['signals'])} 信号")
            
            return True
            
        except Exception as e:
            self.log(f"❌ 运行错误: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run(self):
        while self.running:
            if not self.should_restart():
                self.log(f"⚠️ 重启过于频繁,等待60秒...")
                time.sleep(60)
                continue
            
            self.log("📦 启动LIVE周期...")
            
            success = self.run_cycle()
            
            if not self.running:
                break
            
            if not success:
                self.restart_times.append(time.time())
                self.restart_count += 1
                self.log(f"🔄 {RESTART_DELAY}秒后重启 (第{self.restart_count}次)")
                time.sleep(RESTART_DELAY)
            else:
                # 正常运行,等待60秒后继续
                self.log("⏳ 等待60秒...")
                for i in range(60):
                    if not self.running:
                        break
                    time.sleep(1)
        
        self.log("✅ Q@C v6 LIVE Daemon 已关闭")
    
    def get_status(self):
        return {
            'running': self.running,
            'restarts': self.restart_count,
            'cycles': self.cycle_count,
            'version': '6.0.0'
        }

def main():
    print("=" * 60)
    print("🚀 QuantMaster Q@C v6 LIVE Daemon")
    print("=" * 60)
    print("模式: LIVE (实盘)")
    print("重启延迟: 5秒")
    print("每小时最大重启: 10次")
    print("=" * 60)
    
    daemon = QCV6LiveDaemon()
    daemon.run()

if __name__ == "__main__":
    main()
