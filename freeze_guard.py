"""
QuantMaster 防僵死系统 v8.5
自动监控 + 故障检测 + 自我修复
"""
import sys
import time
import psutil
import signal
import traceback
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime

sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

@dataclass
class HealthCheck:
    component: str
    status: str
    latency_ms: float
    last_check: float
    error: Optional[str]

class FreezeGuard:
    """
    防僵死守护系统
    监控 → 检测 → 修复 → 记录
    """
    
    def __init__(self, hub=None):
        self.hub = hub
        self.running = False
        self.health_checks: List[HealthCheck] = []
        
        # Thresholds
        self.cpu_threshold = 80  # %
        self.memory_threshold = 85  # %
        self.latency_threshold = 5000  # ms
        self.cycle_timeout = 300  # seconds
        
        # Stats
        self.restart_count = 0
        self.last_restart = 0
        self.total_cycles = 0
        self.frozen_count = 0
        
        # Callbacks
        self.on_frozen_callback: Optional[Callable] = None
        self.on_recovered_callback: Optional[Callable] = None
    
    def start(self):
        """启动守护"""
        self.running = True
        print("🛡️ FreezeGuard started")
    
    def stop(self):
        """停止守护"""
        self.running = False
        print("🛡️ FreezeGuard stopped")
    
    # =========================================================================
    # HEALTH CHECKS
    # =========================================================================
    
    def check_hub(self) -> HealthCheck:
        """检查Hub状态"""
        t0 = time.time()
        try:
            if self.hub and hasattr(self.hub, 'get_status'):
                status = self.hub.get_status()
                return HealthCheck(
                    component='hub',
                    status='OK' if status.get('running') else 'STOPPED',
                    latency_ms=(time.time() - t0) * 1000,
                    last_check=time.time(),
                    error=None
                )
            return HealthCheck(
                component='hub', status='NO_HUB',
                latency_ms=(time.time() - t0) * 1000,
                last_check=time.time(),
                error='No hub attached'
            )
        except Exception as e:
            return HealthCheck(
                component='hub', status='ERROR',
                latency_ms=(time.time() - t0) * 1000,
                last_check=time.time(),
                error=str(e)
            )
    
    def check_system(self) -> HealthCheck:
        """检查系统资源"""
        t0 = time.time()
        try:
            cpu = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory().percent
            
            if cpu > self.cpu_threshold:
                status = 'WARNING'
                error = f'CPU high: {cpu:.1f}%'
            elif memory > self.memory_threshold:
                status = 'WARNING'
                error = f'Memory high: {memory:.1f}%'
            else:
                status = 'OK'
                error = None
            
            return HealthCheck(
                component='system',
                status=status,
                latency_ms=(time.time() - t0) * 1000,
                last_check=time.time(),
                error=error
            )
        except Exception as e:
            return HealthCheck(
                component='system', status='ERROR',
                latency_ms=(time.time() - t0) * 1000,
                last_check=time.time(),
                error=str(e)
            )
    
    def check_modules(self) -> List[HealthCheck]:
        """检查所有模块"""
        checks = []
        
        if not self.hub or not hasattr(self.hub, 'modules'):
            return checks
        
        for name, module in self.hub.modules.items():
            t0 = time.time()
            try:
                if hasattr(module, 'get_status'):
                    module.get_status()
                status = 'OK'
                error = None
            except Exception as e:
                status = 'ERROR'
                error = str(e)
            
            checks.append(HealthCheck(
                component=f'module:{name}',
                status=status,
                latency_ms=(time.time() - t0) * 1000,
                last_check=time.time(),
                error=error
            ))
        
        return checks
    
    def check_scanner(self) -> HealthCheck:
        """检查扫描器"""
        t0 = time.time()
        try:
            if not self.hub or 'prediction' not in self.hub.modules:
                return HealthCheck(
                    component='scanner', status='NO_MODULE',
                    latency_ms=(time.time() - t0) * 1000,
                    last_check=time.time(),
                    error='Scanner module not found'
                )
            
            scanner = self.hub.modules.get('prediction')
            if hasattr(scanner, 'predict'):
                scanner.predict('BTC')
            
            return HealthCheck(
                component='scanner', status='OK',
                latency_ms=(time.time() - t0) * 1000,
                last_check=time.time(),
                error=None
            )
        except Exception as e:
            return HealthCheck(
                component='scanner', status='ERROR',
                latency_ms=(time.time() - t0) * 1000,
                last_check=time.time(),
                error=str(e)
            )
    
    # =========================================================================
    # FROZEN DETECTION
    # =========================================================================
    
    def is_frozen(self) -> bool:
        """检测是否僵死"""
        checks = self.run_all_checks()
        
        for check in checks:
            if check.status == 'ERROR':
                return True
            if check.latency_ms > self.latency_threshold:
                return True
        
        return False
    
    def run_all_checks(self) -> List[HealthCheck]:
        """运行所有检查"""
        checks = [
            self.check_system(),
            self.check_hub(),
            self.check_scanner()
        ]
        checks.extend(self.check_modules())
        return checks
    
    # =========================================================================
    # AUTO RECOVERY
    # =========================================================================
    
    def recover(self) -> Dict:
        """执行恢复"""
        print("🔄 Attempting recovery...")
        
        recovery_actions = []
        
        # 1. Garbage collect
        try:
            import gc
            gc.collect()
            recovery_actions.append('gc_collected')
        except: pass
        
        # 2. Restart hub if possible
        try:
            if self.hub:
                if hasattr(self.hub, 'stop'):
                    self.hub.stop()
                if hasattr(self.hub, 'start'):
                    self.hub.start()
                recovery_actions.append('hub_restarted')
        except Exception as e:
            recovery_actions.append(f'hub_restart_failed: {e}')
        
        self.restart_count += 1
        self.last_restart = time.time()
        
        return {
            'recovered': True,
            'actions': recovery_actions,
            'restart_count': self.restart_count,
            'timestamp': time.time()
        }
    
    # =========================================================================
    # WATCHDOG LOOP
    # =========================================================================
    
    def watch_loop(self, interval: int = 30):
        """守护循环"""
        print(f"🛡️ Watch loop started (interval: {interval}s)")
        
        last_cycle = time.time()
        
        while self.running:
            try:
                # Check if frozen
                if self.is_frozen():
                    self.frozen_count += 1
                    print(f"⚠️ Frozen detected! Count: {self.frozen_count}")
                    
                    # Try recovery
                    result = self.recover()
                    print(f"🔄 Recovery: {result}")
                    
                    # Callback
                    if self.on_frozen_callback:
                        self.on_frozen_callback(self.frozen_count)
                
                # Check cycle time
                elapsed = time.time() - last_cycle
                if elapsed > self.cycle_timeout:
                    print(f"⚠️ Cycle timeout: {elapsed:.0f}s")
                
                last_cycle = time.time()
                self.total_cycles += 1
                
                # Status report
                if self.total_cycles % 10 == 0:
                    self.print_status()
                
            except Exception as e:
                print(f"❌ Watch loop error: {e}")
                traceback.print_exc()
            
            time.sleep(interval)
    
    def print_status(self):
        """打印状态"""
        checks = self.run_all_checks()
        
        print(f"\n{'='*50}")
        print(f"🛡️ FREEZE GUARD STATUS")
        print(f"{'='*50}")
        print(f"Cycles: {self.total_cycles}")
        print(f"Frozen Count: {self.frozen_count}")
        print(f"Restart Count: {self.restart_count}")
        print(f"\nComponents:")
        
        for check in checks[:10]:
            emoji = '✅' if check.status == 'OK' else '⚠️' if check.status == 'WARNING' else '❌'
            latency = f"{check.latency_ms:.1f}ms"
            error = f"({check.error})" if check.error else ""
            print(f"  {emoji} {check.component}: {check.status} {latency} {error}")
        
        print(f"{'='*50}\n")
    
    # =========================================================================
    # GET STATUS
    # =========================================================================
    
    def get_status(self) -> Dict:
        """获取守护状态"""
        return {
            'running': self.running,
            'total_cycles': self.total_cycles,
            'frozen_count': self.frozen_count,
            'restart_count': self.restart_count,
            'last_restart': self.last_restart,
            'thresholds': {
                'cpu': self.cpu_threshold,
                'memory': self.memory_threshold,
                'latency': self.latency_threshold,
                'cycle_timeout': self.cycle_timeout
            }
        }

# ============================================================================
# WATCHDOG PROCESS
# ============================================================================

def start_watchdog(hub=None, interval: int = 30):
    """启动独立看门狗进程"""
    guard = FreezeGuard(hub)
    guard.start()
    guard.watch_loop(interval)

if __name__ == '__main__':
    from quant_master_hub import QuantMasterHub
    
    print("=== FreezeGuard Test ===\n")
    
    hub = QuantMasterHub()
    hub.start()
    
    guard = FreezeGuard(hub)
    guard.start()
    
    print("\nRunning checks...")
    checks = guard.run_all_checks()
    
    print("\nResults:")
    for check in checks:
        status = '✅' if check.status == 'OK' else '⚠️' if check.status == 'WARNING' else '❌'
        print(f"  {status} {check.component}: {check.latency_ms:.1f}ms - {check.error or 'OK'}")
    
    print(f"\nStatus: {guard.get_status()}")
    
    print("\n✅ FreezeGuard test complete")
