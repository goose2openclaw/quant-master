"""Q@C v12.1 Daemon"""
import sys, time, signal
sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

LOG = '/home/goose/.openclaw/workspace/qcv12_daemon.log'

class Daemon:
    def __init__(self):
        self.running = True
        signal.signal(signal.SIGTERM, lambda *a: setattr(self, 'running', False))
        signal.signal(signal.SIGINT, lambda *a: setattr(self, 'running', False))
        print("=" * 50)
        print("Q@C v12.1.0 Daemon - 自我纠正版")
        print("=" * 50)
    
    def log(self, msg):
        ts = time.strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{time.strftime('%H:%M:%S')}] {msg}")
        try:
            with open(LOG, 'a') as f: f.write(f"[{ts}] {msg}\n")
        except: pass
    
    def run(self):
        while self.running:
            try:
                from qm.quant_master_qcv12 import QuantMasterQCV12
                qm = QuantMasterQCV12(10000)
                self.log("📦 启动 v12.1.0 (自我纠正)")
                r = qm.run_cycle()
                self.log(f"✅ 周期 #{r['cycle']} 完成")
            except Exception as e:
                self.log(f"❌ {e}")
            
            if self.running:
                for _ in range(60):
                    if not self.running: break
                    time.sleep(1)
        
        self.log("✅ 已关闭")

if __name__ == "__main__":
    Daemon().run()
