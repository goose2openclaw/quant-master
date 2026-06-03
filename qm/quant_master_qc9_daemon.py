"""
QuantMaster Q@C v9 Daemon - 自动重启版
"""
import sys
import time
import signal

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

LOG_FILE = '/home/goose/.openclaw/workspace/qc9_daemon.log'

class QCV9Daemon:
    def __init__(self):
        self.running = True
        self.restart_times = []
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        signal.signal(signal.SIGINT, self.handle_shutdown)
        self.log("🚀 Q@C v9 Daemon 启动")
    
    def log(self, msg):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {msg}")
        try:
            with open(LOG_FILE, 'a') as f:
                f.write(f"[{timestamp}] {msg}\n")
        except: pass
    
    def handle_shutdown(self, signum, frame):
        self.running = False
        self.log("📤 收到停止信号")
    
    def should_restart(self):
        now = time.time()
        self.restart_times = [t for t in self.restart_times if now - t < 3600]
        return len(self.restart_times) < 10
    
    def run(self):
        while self.running:
            if not self.should_restart():
                self.log("⚠️ 重启过于频繁,等待60秒...")
                time.sleep(60)
                continue
            
            try:
                from qm.quant_master_qc9 import QuantMasterQC9
                qm = QuantMasterQC9(10000, 'SIMULATE')
                self.log(f"📦 启动 (模式: {qm.mode})")
                result = qm.run_cycle()
                self.log(f"✅ 周期 #{result['cycle']} 完成")
            except Exception as e:
                self.log(f"❌ 错误: {e}")
                self.restart_times.append(time.time())
            
            if self.running:
                self.log("⏳ 等待60秒...")
                for _ in range(60):
                    if not self.running: break
                    time.sleep(1)
        
        self.log("✅ Q@C v9 Daemon 已关闭")

def main():
    print("=" * 60)
    print("🚀 QuantMaster Q@C v9 Daemon")
    print("=" * 60)
    daemon = QCV9Daemon()
    daemon.run()

if __name__ == "__main__":
    main()
