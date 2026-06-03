"""Q@C v10 Daemon - 修复版"""
import sys, time, signal
sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

LOG = '/home/goose/.openclaw/workspace/qcv10_daemon.log'

class Daemon:
    def __init__(self):
        self.running = True
        signal.signal(signal.SIGTERM, lambda *a: setattr(self, 'running', False))
        signal.signal(signal.SIGINT, lambda *a: setattr(self, 'running', False))
        print("=" * 50)
        print("🚀 Q@C v10.1.1 Daemon (修复版)")
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
                from qm.quant_master_qcv10 import QuantMasterQCV10
                qm = QuantMasterQCV10(10000, 'LIVE')
                self.log(f"📦 启动 v10.1.1 (V8 50% + G12 30% + Miro 20%)")
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
    Daemon().run()
