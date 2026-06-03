"""
QuantMaster Q@C v4 Daemon - 自动重启版

特性:
1. 自动重启机制 - 进程崩溃后自动重启
2. 无限循环运行 - 持续监控
3. 优雅关闭 - 收到SIGTERM优雅退出
4. 日志记录 - 每次重启记录日志
"""
import sys
import time
import signal
import os

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

# 导入主程序
try:
    from qm.quant_master_qc4 import QuantMasterQC4
    from qm.quant_master_qc5 import QuantMasterQC5
    HAS_QC5 = True
except:
    HAS_QC5 = False

# 配置
RESTART_DELAY = 5  # 重启延迟秒数
MAX_RESTART_PER_HOUR = 10  # 每小时最大重启次数
LOG_FILE = '/home/goose/.openclaw/workspace/qc_daemon.log'

class QuantMasterDaemon:
    def __init__(self):
        self.running = True
        self.restart_count = 0
        self.last_restart_time = time.time()
        self.restart_times = []
        
        # 信号处理
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        signal.signal(signal.SIGINT, self.handle_shutdown)
        
        self.log("🚀 QuantMaster Daemon 启动")
    
    def log(self, msg):
        """记录日志"""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        log_msg = f"[{timestamp}] {msg}"
        print(log_msg)
        try:
            with open(LOG_FILE, 'a') as f:
                f.write(log_msg + '\n')
        except:
            pass
    
    def handle_shutdown(self, signum, frame):
        """处理关闭信号"""
        self.log("📤 收到停止信号,正在关闭...")
        self.running = False
    
    def should_restart(self):
        """检查是否应该重启"""
        now = time.time()
        
        # 清理1小时前的重启记录
        self.restart_times = [t for t in self.restart_times if now - t < 3600]
        
        # 检查重启次数
        if len(self.restart_times) >= MAX_RESTART_PER_HOUR:
            self.log(f"⚠️ 重启过于频繁 ({len(self.restart_times)}次/小时),等待...")
            return False
        
        return True
    
    def run_cycle(self):
        """运行一个周期"""
        try:
            self.log("🔄 启动 Q@C v4...")
            
            # 创建实例
            if HAS_QC5:
                qm = QuantMasterQC5(10000)
            else:
                qm = QuantMasterQC4(10000)
            
            qm.mode = 'LIVE'
            
            # 运行主循环 (每次运行1个完整周期)
            qm.run()
            
            return True
            
        except Exception as e:
            self.log(f"❌ 运行错误: {e}")
            return False
    
    def run(self):
        """主循环"""
        cycle = 0
        
        while self.running:
            cycle += 1
            self.log(f"📦 周期 #{cycle}")
            
            # 检查是否应该重启
            if not self.should_restart():
                time.sleep(60)
                continue
            
            # 运行周期
            success = self.run_cycle()
            
            if not self.running:
                break
            
            if not success:
                # 记录重启
                self.restart_times.append(time.time())
                self.restart_count += 1
                
                self.log(f"🔄 {RESTART_DELAY}秒后重启... (第{self.restart_count}次重启)")
                time.sleep(RESTART_DELAY)
            
            # 正常运行,等待60秒后继续
            else:
                self.log("✅ 周期完成,等待60秒...")
                for i in range(60):
                    if not self.running:
                        break
                    time.sleep(1)
        
        self.log("✅ Daemon 已关闭")
    
    def get_status(self):
        """获取状态"""
        return {
            'running': self.running,
            'restart_count': self.restart_count,
            'recent_restarts': len(self.restart_times),
            'log_file': LOG_FILE
        }

def main():
    daemon = QuantMasterDaemon()
    
    print("=" * 60)
    print("🚀 QuantMaster Q@C v4 Daemon (自动重启版)")
    print("=" * 60)
    print(f"重启延迟: {RESTART_DELAY}秒")
    print(f"每小时最大重启: {MAX_RESTART_PER_HOUR}次")
    print(f"日志文件: {LOG_FILE}")
    print("=" * 60)
    
    daemon.run()

if __name__ == '__main__':
    main()
