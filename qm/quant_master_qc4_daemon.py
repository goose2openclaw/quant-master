"""
QuantMaster Q@C v4 Daemon - 常驻版
"""
import sys
import time
import signal

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

from qm.quant_master_qc4 import QuantMasterQC4

def signal_handler(signum, frame):
    print("\n收到停止信号,正在关闭...")
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

def main():
    print("=" * 70)
    print("🚀 QuantMaster Q@C v4 Daemon 启动")
    print("=" * 70)
    
    qm = QuantMasterQC4(10000)
    cycle = 0
    
    while True:
        cycle += 1
        print(f"\n{'='*70}")
        print(f"🔄 周期 #{cycle}")
        print(f"{'='*70}")
        
        try:
            qm.run()
        except Exception as e:
            print(f"错误: {e}")
        
        print(f"\n等待60秒后进入下一个周期...")
        time.sleep(60)

if __name__ == '__main__':
    main()
