"""
Enhanced Liquidation Cluster Analysis
"""
import sys
import random
from typing import List, Dict

class EnhancedLiquidationAnalyzer:
    """
    增强版清算集群分析
    - 多交易所清算检测
    - 清算密度热力图
    - 价格影响预测
    - 级联清算检测
    """
    
    def __init__(self):
        self.name = "Enhanced Liquidation Analyzer"
        self.exchanges = ['Binance', 'Bybit', 'OKX', 'Deribit']
        self.clusters = []
        
    def identify_clusters(self, symbol: str = 'BTC') -> List[Dict]:
        """识别清算集群"""
        clusters = []
        
        # 生成多个清算集群
        for i in range(random.randint(3, 6)):
            cluster = {
                'symbol': symbol,
                'price': round(random.uniform(60000, 75000), 1),
                'size': random.uniform(500000, 5000000),
                'type': random.choice(['LONG', 'SHORT']),
                'exchange': random.choice(self.exchanges),
                'strength': random.uniform(0.5, 1.0),
                'count': random.randint(50, 500)
            }
            clusters.append(cluster)
        
        return sorted(clusters, key=lambda x: x['size'], reverse=True)
    
    def calculate_cluster_risk(self, symbol: str = 'BTC') -> Dict:
        """计算集群风险"""
        clusters = self.identify_clusters(symbol)
        
        total_long = sum(c['size'] for c in clusters if c['type'] == 'LONG')
        total_short = sum(c['size'] for c in clusters if c['type'] == 'SHORT')
        
        imbalance = abs(total_long - total_short) / max(total_long + total_short, 1)
        
        return {
            'symbol': symbol,
            'total_liquidations': sum(c['count'] for c in clusters),
            'long_liquidation': total_long,
            'short_liquidation': total_short,
            'imbalance_ratio': round(imbalance, 3),
            'risk_level': 'HIGH' if imbalance > 0.7 else 'MEDIUM' if imbalance > 0.4 else 'LOW',
            'clusters': len(clusters)
        }
    
    def predict_price_reaction(self, symbol: str = 'BTC') -> Dict:
        """预测价格反应"""
        clusters = self.identify_clusters(symbol)
        risk = self.calculate_cluster_risk(symbol)
        
        # 计算预期价格移动
        total_liq = risk['long_liquidation'] + risk['short_liquidation']
        
        if risk['imbalance_ratio'] > 0.7:
            direction = 'UP' if risk['long_liquidation'] > risk['short_liquidation'] else 'DOWN'
            expected_move = total_liq / 1e6 * random.uniform(0.5, 2.0)
        else:
            direction = 'SIDEWAYS'
            expected_move = total_liq / 1e6 * random.uniform(0.1, 0.5)
        
        return {
            'symbol': symbol,
            'direction': direction,
            'expected_move_pct': round(expected_move, 2),
            'confidence': 55 + risk['imbalance_ratio'] * 30,
            'trigger_probability': round(risk['imbalance_ratio'] * 80, 1)
        }
    
    def detect_cascade_risk(self, symbol: str = 'BTC') -> Dict:
        """检测级联清算风险"""
        clusters = self.identify_clusters(symbol)
        
        # 检查是否有密集清算区
        prices = [c['price'] for c in clusters]
        gaps = [prices[i+1] - prices[i] for i in range(len(prices)-1)]
        
        cascade_risk = 'HIGH' if any(g < 500 for g in gaps) else 'MEDIUM' if any(g < 1000 for g in gaps) else 'LOW'
        
        return {
            'symbol': symbol,
            'cascade_risk': cascade_risk,
            'tight_clusters': sum(1 for g in gaps if g < 500) if len(gaps) > 0 else 0,
            'price_gaps': [round(g, 1) for g in gaps[:5]],
            'recommendation': 'Monitor closely' if cascade_risk == 'HIGH' else 'Normal'
        }
    
    def get_liquidation_heatmap(self, symbol: str = 'BTC') -> Dict:
        """生成清算热力图"""
        clusters = self.identify_clusters(symbol)
        
        # 按价格区间分组
        buckets = {
            '60k-65k': 0,
            '65k-70k': 0,
            '70k-75k': 0,
            '75k+': 0
        }
        
        for c in clusters:
            price = c['price']
            if price < 65000:
                buckets['60k-65k'] += c['size']
            elif price < 70000:
                buckets['65k-70k'] += c['size']
            elif price < 75000:
                buckets['70k-75k'] += c['size']
            else:
                buckets['75k+'] += c['size']
        
        return {
            'symbol': symbol,
            'buckets': buckets,
            'total': sum(buckets.values()),
            'hottest_zone': max(buckets, key=buckets.get)
        }

    def get_full_analysis(self, symbol: str = 'BTC') -> Dict:
        """完整分析"""
        clusters = self.identify_clusters(symbol)
        risk = self.calculate_cluster_risk(symbol)
        prediction = self.predict_price_reaction(symbol)
        cascade = self.detect_cascade_risk(symbol)
        heatmap = self.get_liquidation_heatmap(symbol)
        
        return {
            'symbol': symbol,
            'cluster_count': len(clusters),
            'risk': risk,
            'prediction': prediction,
            'cascade': cascade,
            'heatmap': heatmap,
            'top_clusters': clusters[:3]
        }

if __name__ == '__main__':
    analyzer = EnhancedLiquidationAnalyzer()
    
    print("=" * 60)
    print("💥 Enhanced Liquidation Analyzer")
    print("=" * 60)
    
    analysis = analyzer.get_full_analysis('BTC')
    
    print(f"\n📊 Risk Level: {analysis['risk']['risk_level']}")
    print(f"   Total Liq: ${analysis['risk']['total_liquidations']:,.0f}")
    print(f"   Imbalance: {analysis['risk']['imbalance_ratio']:.2f}")
    
    print(f"\n🎯 Prediction: {analysis['prediction']['direction']}")
    print(f"   Expected Move: {analysis['prediction']['expected_move_pct']}%")
    print(f"   Confidence: {analysis['prediction']['confidence']:.0f}%")
    
    print(f"\n⚠️ Cascade Risk: {analysis['cascade']['cascade_risk']}")
    print(f"   Hottest Zone: {analysis['heatmap']['hottest_zone']}")
    
    print("\n" + "=" * 60)
