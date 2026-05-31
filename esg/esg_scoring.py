"""
ESG Scoring - ESG评分系统
"""
from typing import Dict, List

class ESGData:
    """ESG数据"""
    def __init__(self, symbol):
        self.symbol = symbol
        self.environmental = {}
        self.social = {}
        self.governance = {}
        self.scores = {'E': 0, 'S': 0, 'G': 0, 'ESG': 0}

class ESGScorer:
    """
    ESG评分
    Environmental, Social, Governance
    """
    def __init__(self):
        self.data = {}  # {symbol: ESGData}
        
        # 评分权重
        self.weights = {'E': 0.3, 'S': 0.2, 'G': 0.5}
        
        # 数据源
        self.data_sources = ['onchain', 'news', 'sentiment']
    
    def fetch_esg_data(self, symbol: str) -> ESGData:
        """获取ESG数据"""
        data = ESGData(symbol)
        
        # 环境评分 - 基于链上能耗/碳排放
        data.environmental = {
            'energy_consumption': self._get_energy(symbol),
            'carbon_footprint': self._get_carbon(symbol),
            'renewable_ratio': self._get_renewable(symbol)
        }
        
        # 社会评分 - 基于社区活跃度/开发进度
        data.social = {
            'community_size': self._get_community(symbol),
            'developer_activity': self._get_developers(symbol),
            'adoption_rate': self._get_adoption(symbol)
        }
        
        # 治理评分 - 基于代码质量/透明度
        data.governance = {
            'code_quality': self._get_code_quality(symbol),
            'transparency': self._get_transparency(symbol),
            'decentralization': self._get_decentralization(symbol)
        }
        
        self.data[symbol] = data
        return data
    
    def calculate_scores(self, symbol: str) -> Dict:
        """计算ESG评分"""
        data = self.data.get(symbol) or self.fetch_esg_data(symbol)
        
        # E评分
        e_score = self._score_environmental(data.environmental)
        
        # S评分
        s_score = self._score_social(data.social)
        
        # G评分
        g_score = self._score_governance(data.governance)
        
        # 综合评分
        esg_score = (e_score * self.weights['E'] + 
                    s_score * self.weights['S'] + 
                    g_score * self.weights['G'])
        
        data.scores = {'E': e_score, 'S': s_score, 'G': g_score, 'ESG': esg_score}
        
        return data.scores
    
    def _score_environmental(self, env: Dict) -> float:
        """环境评分"""
        score = 50
        
        # 能耗越低越好
        energy = env.get('energy_consumption', 100)
        if energy < 50:
            score += 20
        elif energy < 100:
            score += 10
        
        # 碳排放
        carbon = env.get('carbon_footprint', 50)
        if carbon < 30:
            score += 15
        elif carbon < 60:
            score += 5
        
        # 可再生能源比例
        renewable = env.get('renewable_ratio', 0)
        score += renewable * 0.15
        
        return min(100, max(0, score))
    
    def _score_social(self, social: Dict) -> float:
        """社会评分"""
        score = 50
        
        # 社区规模
        community = social.get('community_size', 0)
        score += min(community / 1000 * 10, 20)
        
        # 开发者活跃度
        dev = social.get('developer_activity', 0)
        score += min(dev / 100 * 15, 15)
        
        # 采用率
        adoption = social.get('adoption_rate', 0)
        score += adoption * 0.15
        
        return min(100, max(0, score))
    
    def _score_governance(self, gov: Dict) -> float:
        """治理评分"""
        score = 50
        
        # 代码质量
        quality = gov.get('code_quality', 0)
        score += quality * 0.25
        
        # 透明度
        trans = gov.get('transparency', 0)
        score += trans * 0.15
        
        # 去中心化
        decent = gov.get('decentralization', 0)
        score += decent * 0.10
        
        return min(100, max(0, score))
    
    # 数据获取方法 (简化)
    def _get_energy(self, symbol): return 50
    def _get_carbon(self, symbol): return 40
    def _get_renewable(self, symbol): return 0.3
    def _get_community(self, symbol): return 50000
    def _get_developers(self, symbol): return 80
    def _get_adoption(self, symbol): return 0.5
    def _get_code_quality(self, symbol): return 70
    def _get_transparency(self, symbol): return 65
    def _get_decentralization(self, symbol): return 0.6
    
    def get_esg_rating(self, score: float) -> str:
        """获取评级"""
        if score >= 80:
            return 'AAA'
        elif score >= 70:
            return 'AA'
        elif score >= 60:
            return 'A'
        elif score >= 50:
            return 'BBB'
        elif score >= 40:
            return 'BB'
        else:
            return 'B'

class ESGPortfolioAnalyzer:
    """ESG组合分析"""
    def __init__(self):
        self.scorer = ESGScorer()
    
    def analyze_portfolio(self, symbols: List[str]) -> Dict:
        """分析组合ESG"""
        scores = {}
        
        for symbol in symbols:
            self.scorer.fetch_esg_data(symbol)
            scores[symbol] = self.scorer.calculate_scores(symbol)
        
        # 计算组合加权平均
        total_score = sum(s['ESG'] for s in scores.values())
        avg_score = total_score / len(scores) if scores else 0
        
        # 找出最优/最差
        sorted_scores = sorted(scores.items(), key=lambda x: x[1]['ESG'], reverse=True)
        
        return {
            'portfolio_esg': avg_score,
            'rating': self.scorer.get_esg_rating(avg_score),
            'holdings': scores,
            'best': sorted_scores[0] if sorted_scores else None,
            'worst': sorted_scores[-1] if sorted_scores else None,
            'compliant': [s for s, score in scores.items() if score['ESG'] >= 50]
        }
