"""Q@C v9 Daemon"""
import sys, time, signal
sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

LOG = '/home/goose/.openclaw/workspace/qcv9_daemon.log'

class Daemon:
    def __init__(self):
        self.running = True
        signal.signal(signal.SIGTERM, lambda *a: setattr(self, 'running', False))
        signal.signal(signal.SIGINT, lambda *a: setattr(self, 'running', False))
        self.log("🚀 Q@C v9 Daemon 启动")
    
    def log(self, msg):
        print(f"[{time.strftime('%H:%M:%S')}] {msg}")
        try:
            with open(LOG, 'a') as f: f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
        except: pass
    
    def run(self):
        while self.running:
            try:
                from qm.quant_master_qcv9 import QuantMasterQCV9
                qm = QuantMasterQCV9(10000, 'SIMULATE')
                self.log(f"📦 启动 (V8核心+G12增补)")
                r = qm.run_cycle()
                self.log(f"✅ 周期 #{r['cycle']} 完成")
            except Exception as e:
                self.log(f"❌ {e}")
            
            if self.running:
                self.log("⏳ 等待60秒...")
                for _ in range(60):
                    if not self.running: break
                    time.sleep(1)
        
        self.log("✅ 已关闭")

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Q@C v9 Daemon (V8核心+G12增补)")
    print("=" * 50)
    Daemon().run()
