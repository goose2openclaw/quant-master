"""Q@C v13 Daemon"""
import sys, time, signal
sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

LOG = '/home/goose/.openclaw/workspace/qcv13_daemon.log'

class Daemon:
    def __init__(self):
        self.running = True
        signal.signal(signal.SIGTERM, lambda *a: setattr(self, 'running', False))
        signal.signal(signal.SIGINT, lambda *a: setattr(self, 'running', False))
        print("=" * 50)
        print("Q@C v13.0.0 Daemon - Harness重构版")
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
                from qm.quant_master_qcv13 import QuantMasterQCV13
                qm = QuantMasterQCV13(10000)
                self.log(f"📦 启动 v13.0.0")
                r = qm.run_cycle()
                self.log(f"✅ 周期 #{r['cycle']} 完成")
            except Exception as e:
                self.log(f"❌ {e}")
                import traceback
                traceback.print_exc()
            
            if self.running:
                for _ in range(60):
                    if not self.running: break
                    time.sleep(1)
        
        self.log("✅ 已关闭")

if __name__ == "__main__":
    Daemon().run()
