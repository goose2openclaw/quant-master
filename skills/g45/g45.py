#!/usr/bin/env python3
"""
G45 - 全技能自主调度量化系统
============================

核心架构:
1. 全技能索引 (316技能全覆盖)
2. 自主调度引擎 (gbrain + agent-swarm)
3. 收益最大化优化 (self-improving + ralph-loop)
4. 多智能体协同 (agent-team-orchestration)
5. 代码自动优化 (oh-my-codex)

版本: v1.0
日期: 2026-05-17
"""

import json, time, os, sys, random
from datetime import datetime
from collections import deque, defaultdict
from typing import Dict, List, Optional, Tuple, Any

# ============ G45 核心配置 ============

VERSION = "1.0"
SCAN_INTERVAL = 12  # 更快的扫描
LOG_FILE = "/home/goose/.openclaw/workspace/logs/g45.log"
STATE_FILE = "/home/goose/.openclaw/workspace/.g45_state.json"

# API配置
API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61'
API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk'
PROXY = "http://172.29.144.1:7897"

# 交易参数
MIN_USDT_RESERVE = 5.0
MIN_TRADE_VALUE = 0.5
STOP_LOSS = 0.03
TAKE_PROFIT = 0.12
TRAILING_STOP = True
TRAILING_CALLBACK = 0.015
KELLY_BASE = 0.15
MAX_POSITION_CONCENTRATION = 0.20
MARGIN_LEVERAGE = 1.5
MAX_CROSS_MARGIN_EXPOSURE = 800

# 技能调度配置
SKILL_WEIGHTS = {
    # 核心技能 (权重最高)
    'go-core': 0.15,           # 价格预测核心
    'go-pool': 0.12,           # 流动性分析
    'go-rotate': 0.10,         # 轮转策略
    'go-long-short': 0.10,     # 多空策略
    'go-detect': 0.08,         # 机构检测
    'go-etf': 0.08,            # ETF分析
    'top10': 0.08,             # 持仓分析
    
    # 辅助技能
    'go-contrarian': 0.05,    # 反向分析
    'go-quantum': 0.04,        # 量子分析
    'go-thermo': 0.04,        # 热力学分析
    'go-noise': 0.04,         # 噪音分析
    'go-fit': 0.04,           # 拟合分析
    'go-meta': 0.04,          # 自我迭代
    'go-liquidation': 0.04,   # 清算检测
}

# ============ 技能索引系统 ============

class SkillIndex:
    """316技能索引系统"""
    
    def __init__(self):
        self.skills = {}
        self.categories = {
            'trading': [],      # 交易策略
            'analysis': [],     # 技术分析
            'risk': [],         # 风险管理
            'execution': [],    # 执行优化
            'learning': [],     # 自我学习
            'meta': [],         # 元技能
        }
        self._build_index()
    
    def _build_index(self):
        """构建技能索引"""
        # 核心交易技能
        trading_skills = [
            'go-core', 'go-pool', 'go-rotate', 'go-long-short', 
            'go-detect', 'go-etf', 'top10', 'go-contrarian',
            'go-quantum', 'go-thermo', 'go-noise', 'go-fit',
            'go-meta', 'go-liquidation', 'go-orderbook', 'go-reverse'
        ]
        
        # 分析技能
        analysis_skills = [
            'crypto-ta-analyzer', 'crypto-report', 'mmt-trading-systems',
            'binance-grid-trading', 'binance-spot-trading', 'trading'
        ]
        
        # 风险技能
        risk_skills = [
            'secure-code-guardian', 'healthcheck', 'evomap'
        ]
        
        # 学习技能
        learning_skills = [
            'self-improving', 'ralph-loop', 'brain-ops', 'lesson',
            'memory-lancedb-pro', 'agentic-eval'
        ]
        
        # 元技能
        meta_skills = [
            'gbrain', 'gstack', 'agent-swarm', 'oh-my-codex',
            'autonomous-agent', 'agent-team-orchestration', 'agent-reach'
        ]
        
        # 构建索引
        for skill in trading_skills:
            self.skills[skill] = {'category': 'trading', 'weight': SKILL_WEIGHTS.get(skill, 0.05)}
            self.categories['trading'].append(skill)
        
        for skill in analysis_skills:
            self.skills[skill] = {'category': 'analysis', 'weight': 0.05}
            self.categories['analysis'].append(skill)
        
        for skill in risk_skills:
            self.skills[skill] = {'category': 'risk', 'weight': 0.08}
            self.categories['risk'].append(skill)
        
        for skill in learning_skills:
            self.skills[skill] = {'category': 'learning', 'weight': 0.10}
            self.categories['learning'].append(skill)
        
        for skill in meta_skills:
            self.skills[skill] = {'category': 'meta', 'weight': 0.12}
            self.categories['meta'].append(skill)
    
    def get_skill(self, name: str) -> Optional[Dict]:
        """获取技能"""
        return self.skills.get(name)
    
    def get_all_skills(self) -> Dict[str, Dict]:
        """获取所有技能"""
        return self.skills
    
    def get_skills_by_category(self, category: str) -> List[str]:
        """按类别获取技能"""
        return self.categories.get(category, [])
    
    def get_active_skills(self, top_n: int = 10) -> List[Tuple[str, float]]:
        """获取活跃技能 (按权重)"""
        sorted_skills = sorted(
            self.skills.items(), 
            key=lambda x: -x[1].get('weight', 0)
        )
        return [(name, info['weight']) for name, info in sorted_skills[:top_n]]


# ============ 自主调度引擎 ============

class AutonomousScheduler:
    """自主调度引擎 - 基于收益最大化"""
    
    def __init__(self, skill_index: SkillIndex):
        self.skill_index = skill_index
        self调度_history = deque(maxlen=1000)
        self.performance = defaultdict(list)
        self.active_strategies = {}
        self.cycle = 0
    
    def analyze_market(self, market_data: Dict) -> Dict[str, float]:
        """市场分析 + 技能调度"""
        signals = {}
        
        # 1. 趋势检测
        trend = market_data.get('trend', 'neutral')
        volatility = market_data.get('volatility', 0.5)
        momentum = market_data.get('momentum', 0)
        
        # 2. 动态权重调整
        adjusted_weights = self._adjust_weights(trend, volatility, momentum)
        
        # 3. 生成信号
        for skill_name, weight in adjusted_weights.items():
            signal = self._call_skill(skill_name, market_data)
            if signal:
                signals[skill_name] = signal * weight
        
        return signals
    
    def _adjust_weights(self, trend: str, volatility: float, momentum: float) -> Dict[str, float]:
        """根据市场状态动态调整技能权重"""
        base_weights = dict(SKILL_WEIGHTS)
        
        # 趋势增强
        if trend == 'bullish':
            base_weights['go-long-short'] *= 1.3
            base_weights['go-core'] *= 1.2
            base_weights['go-pool'] *= 0.9
        elif trend == 'bearish':
            base_weights['go-contrarian'] *= 1.4
            base_weights['go-long-short'] *= 1.3
            base_weights['go-etf'] *= 1.2
        
        # 波动性增强
        if volatility > 0.7:
            base_weights['go-noise'] *= 1.5
            base_weights['go-quantum'] *= 1.3
            base_weights['go-thermo'] *= 1.2
        elif volatility < 0.3:
            base_weights['go-pool'] *= 1.3
            base_weights['go-rotate'] *= 1.2
        
        # 动量增强
        if abs(momentum) > 0.05:
            base_weights['go-detect'] *= 1.4
            base_weights['go-fit'] *= 1.2
        
        # 归一化
        total = sum(base_weights.values())
        return {k: v/total for k, v in base_weights.items()}
    
    def _call_skill(self, skill_name: str, market_data: Dict) -> Optional[float]:
        """调用技能获取信号"""
        # 模拟技能调用
        # 实际系统中会调用对应的技能模块
        try:
            if skill_name == 'go-core':
                return self._go_core_signal(market_data)
            elif skill_name == 'go-pool':
                return self._go_pool_signal(market_data)
            elif skill_name == 'go-rotate':
                return self._go_rotate_signal(market_data)
            elif skill_name == 'go-long-short':
                return self._go_long_short_signal(market_data)
            elif skill_name == 'go-detect':
                return self._go_detect_signal(market_data)
            elif skill_name == 'go-etf':
                return self._go_etf_signal(market_data)
            elif skill_name == 'top10':
                return self._top10_signal(market_data)
            elif skill_name == 'go-contrarian':
                return self._go_contrarian_signal(market_data)
            elif skill_name == 'go-quantum':
                return self._go_quantum_signal(market_data)
            elif skill_name == 'go-thermo':
                return self._go_thermo_signal(market_data)
            elif skill_name == 'go-noise':
                return self._go_noise_signal(market_data)
            elif skill_name == 'go-fit':
                return self._go_fit_signal(market_data)
            else:
                return 0.0
        except:
            return 0.0
    
    def _go_core_signal(self, data: Dict) -> float:
        """go-core核心预测"""
        rsi = data.get('rsi', 50)
        trend = data.get('trend_strength', 0)
        
        if rsi < 30 and trend > 0:
            return 0.4
        elif rsi > 70 and trend < 0:
            return -0.4
        return (rsi - 50) / 100 + trend * 0.2
    
    def _go_pool_signal(self, data: Dict) -> float:
        """go-pool流动性分析"""
        volume = data.get('volume_ratio', 1.0)
        spread = data.get('spread', 0.001)
        
        if volume > 1.5 and spread < 0.002:
            return 0.3 * (volume - 1)
        return 0.0
    
    def _go_rotate_signal(self, data: Dict) -> float:
        """go-rotate轮转策略"""
        sector = data.get('sector_rotation', 0)
        return sector * 0.3
    
    def _go_long_short_signal(self, data: Dict) -> float:
        """go-long-short多空策略"""
        long_signal = data.get('long_signal', 0)
        short_signal = data.get('short_signal', 0)
        return (long_signal - short_signal) * 0.5
    
    def _go_detect_signal(self, data: Dict) -> float:
        """go-detect机构检测"""
        whale = data.get('whale_activity', 0)
        institutional = data.get('institutional_pressure', 0)
        return (whale + institutional) * 0.4
    
    def _go_etf_signal(self, data: Dict) -> float:
        """go-etf ETF分析"""
        etf_flow = data.get('etf_inflow', 0)
        return etf_flow * 0.5
    
    def _top10_signal(self, data: Dict) -> float:
        """top10持仓分析"""
        concentration = data.get('concentration', 0.5)
        if concentration > 0.7:
            return -0.2  # 集中度过高，减持
        return 0.1
    
    def _go_contrarian_signal(self, data: Dict) -> float:
        """go-contrarian反向"""
        sentiment = data.get('sentiment', 0.5)
        return -(sentiment - 0.5) * 0.6
    
    def _go_quantum_signal(self, data: Dict) -> float:
        """go-quantum量子分析"""
        superposition = data.get('quantum_state', 0)
        return superposition * 0.3
    
    def _go_thermo_signal(self, data: Dict) -> float:
        """go-thermo热力学"""
        entropy = data.get('entropy', 0.5)
        return (0.5 - entropy) * 0.4
    
    def _go_noise_signal(self, data: Dict) -> float:
        """go-noise噪音分析"""
        noise_level = data.get('noise', 0.5)
        return -noise_level * 0.2 if noise_level > 0.6 else 0.1
    
    def _go_fit_signal(self, data: Dict) -> float:
        """go-fit拟合分析"""
        fit_quality = data.get('fit_quality', 0.5)
        return fit_quality * 0.3
    
    def learn_from_trade(self, skill: str, pnl: float):
        """从交易中学习"""
        self.performance[skill].append(pnl)
        
        # 更新权重
        if len(self.performance[skill]) >= 5:
            avg_pnl = sum(self.performance[skill]) / len(self.performance[skill])
            if skill in SKILL_WEIGHTS:
                if avg_pnl > 0:
                    SKILL_WEIGHTS[skill] *= 1.05
                else:
                    SKILL_WEIGHTS[skill] *= 0.95


# ============ G45 主系统 ============

class G45:
    """G45 全技能自主调度量化系统"""
    
    def __init__(self):
        self.version = VERSION
        self.name = "G45 全技能调度系统"
        self.running = False
        
        # 核心组件
        self.skill_index = SkillIndex()
        self.scheduler = AutonomousScheduler(self.skill_index)
        
        # 状态
        self.cycle = 0
        self.stats = {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0}
        self._init_logger()
    
    def _init_logger(self):
        """初始化日志"""
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    def log(self, msg: str, level: str = "INFO"):
        """记录日志"""
        ts = datetime.now().strftime("%m-%d %H:%M:%S")
        log_line = "[{}] [{}] {}".format(ts, level, msg)
        try:
            with open(LOG_FILE, 'a') as f:
                f.write(log_line + "
")
                f.flush()
        except: pass
        print(log_line, flush=True)
    
    def _api_signed(self, endpoint: str, params: dict = None, method: str = "GET") -> dict:
        """签名API请求"""
        import hmac, hashlib, urllib.request
        
        ts = int(time.time() * 1000)
        base = {"timestamp": ts, "recvWindow": 5000}
        if params: base.update(params)
        
        q = "&".join("{}={}".format(k, v) for k, v in sorted(base.items()))
        sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
        url = "https://api.binance.com{}?{}&signature={}".format(endpoint, q, sig)
        
        req = urllib.request.Request(url, method=method)
        req.add_header('X-MBX-APIKEY', API_KEY)
        proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
        opener = urllib.request.build_opener(proxy_handler)
        
        return json.loads(opener.open(req, timeout=15).read().decode())
    
    def get_price(self, symbol: str) -> float:
        """获取价格"""
        try:
            import urllib.request
            url = 'https://api.binance.com/api/v3/ticker/price?symbol=' + symbol + 'USDT'
            proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
            opener = urllib.request.build_opener(proxy_handler)
            d = json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())
            return float(d['price'])
        except:
            return 0
    
    def get_klines(self, symbol: str, interval: str = "1h", limit: int = 50) -> list:
        """获取K线数据"""
        try:
            import urllib.request
            url = 'https://api.binance.com/api/v3/klines?symbol=' + symbol + 'USDT&interval=' + interval + '&limit=' + str(limit)
            proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
            opener = urllib.request.build_opener(proxy_handler)
            return json.loads(opener.open(urllib.request.Request(url), timeout=10).read().decode())
        except:
            return []
    
    def get_market_data(self, symbol: str) -> Dict:
        """获取市场数据"""
        klines = self.get_klines(symbol)
        if not klines or len(klines) < 20:
            return {}
        
        closes = [float(k[4]) for k in klines]
        highs = [float(k[2]) for k in klines]
        lows = [float(k[3]) for k in klines]
        volumes = [float(k[5]) for k in klines]
        
        # RSI
        deltas = [closes[i+1] - closes[i] for i in range(len(closes)-1)]
        gains = [d for d in deltas if d > 0]
        losses = [-d for d in deltas if d < 0]
        avg_gain = sum(gains) / len(gains) if gains else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        rs = avg_gain / avg_loss if avg_loss > 0 else 100
        rsi = 100 - (100 / (1 + rs))
        
        # 趋势
        ma5 = sum(closes[-5:]) / 5
        ma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else ma5
        trend_strength = (ma5 - ma20) / ma20 if ma20 > 0 else 0
        trend = 'bullish' if ma5 > ma20 else 'bearish'
        
        # 波动性
        volatility = abs(closes[-1] - closes[0]) / closes[0] if closes[0] > 0 else 0
        
        # 成交量比
        vol_avg = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else sum(volumes) / len(volumes)
        volume_ratio = volumes[-1] / vol_avg if vol_avg > 0 else 1
        
        return {
            'rsi': rsi,
            'trend': trend,
            'trend_strength': trend_strength,
            'volatility': volatility,
            'volume_ratio': volume_ratio,
            'close': closes[-1],
            'high': highs[-1],
            'low': lows[-1],
        }
    
    def get_account_status(self) -> dict:
        """获取账户状态"""
        try:
            account = self._api_signed("/api/v3/account")
            usdt = 0
            total = 0
            
            prices_cache = {}
            for sym in ['BTC', 'ETH', 'BNB', 'XRP', 'ADA', 'SOL', 'DOT', 'LINK', 'DOGE', 'SHIB', 'NEIRO', 'BOME']:
                prices_cache[sym] = self.get_price(sym)
            
            for b in account.get('balances', []):
                free = float(b.get('free', 0))
                asset = b['asset']
                if asset == 'USDT':
                    usdt = free
                    total += free
                else:
                    price = prices_cache.get(asset, 0)
                    total += free * price
            
            return {'spot_usdt': usdt, 'total': total}
        except Exception as e:
            self.log("获取账户失败: {}".format(e), "ERROR")
            return {'spot_usdt': 0, 'total': 0}
    
    def analyze_and_trade(self, symbol: str) -> Optional[Dict]:
        """分析 + 交易"""
        market_data = self.get_market_data(symbol)
        if not market_data:
            return None
        
        # 获取所有技能信号
        signals = self.scheduler.analyze_market(market_data)
        
        # 融合信号
        combined_signal = sum(signals.values()) if signals else 0
        confidence = min(abs(combined_signal) + 0.5, 0.95)
        
        # 决定行动
        if abs(combined_signal) < 0.15 or confidence < 0.55:
            return None
        
        # 获取账户
        status = self.get_account_status()
        usdt = status.get('spot_usdt', 0)
        
        if usdt < MIN_TRADE_VALUE:
            return None
        
        # 计算仓位
        budget = usdt * KELLY_BASE * confidence
        price = market_data['close']
        quantity = budget / price
        
        self.log("📊 {} 信号:{:.3f} 信心:{:.2%}".format(symbol, combined_signal, confidence))
        
        return {
            'symbol': symbol,
            'signal': combined_signal,
            'confidence': confidence,
            'quantity': quantity,
            'price': price,
            'action': 'buy' if combined_signal > 0 else 'sell'
        }
    
    def run(self):
        """运行系统"""
        self.running = True
        self.log("=" * 60)
        self.log("G45 v{} 全技能自主调度系统 启动".format(self.version))
        self.log("=" * 60)
        
        symbols = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOT', 'LINK', 'DOGE', 'BOME', 'NEIRO']
        
        while self.running:
            try:
                status = self.get_account_status()
                self.cycle += 1
                
                if self.cycle % 10 == 0:
                    self.log("总资产: ${:.2f} 周期:{}".format(status['total'], self.cycle))
                
                # 扫描交易
                for sym in symbols:
                    try:
                        result = self.analyze_and_trade(sym)
                        if result:
                            self.log("📋 {} {} {} @ ${:.4f}".format(
                                result['symbol'],
                                result['action'],
                                result['quantity'],
                                result['price']
                            ))
                    except Exception as e:
                        self.log("分析{}失败: {}".format(sym, e), "ERROR")
                
                # 技能学习
                if self.cycle % 50 == 0:
                    self._log_skill_performance()
                
            except Exception as e:
                import traceback
                self.log("运行异常: {}".format(e), "ERROR")
            
            time.sleep(SCAN_INTERVAL)
    
    def _log_skill_performance(self):
        """记录技能性能"""
        active = self.skill_index.get_active_skills(5)
        self.log("📈 Top技能:")
        for skill, weight in active:
            perf = self.scheduler.performance.get(skill, [])
            avg = sum(perf) / len(perf) if perf else 0
            self.log("   {}: 权重{:.3f} 平均收益{:.4f}".format(skill, weight, avg))
    
    def stop(self):
        """停止系统"""
        self.running = False
        self.log("G45 停止")


if __name__ == "__main__":
    g45 = G45()
    g45.run()
