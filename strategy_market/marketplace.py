"""
策略市场 - 买卖策略平台
"""
import time, json, hashlib
from datetime import datetime
from threading import Lock

class StrategyListing:
    """策略上架"""
    def __init__(self, id, name, author, strategy_type, price, description):
        self.id = id
        self.name = name
        self.author = author
        self.strategy_type = strategy_type
        self.price = price  # 价格 (0=免费)
        self.description = description
        self.rating = 0
        self.ratings_count = 0
        self.downloads = 0
        self.revenue = 0
        self.reviews = []
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.is_active = True
        self.code_hash = ""  # 策略代码哈希
        self.version = "1.0.0"
        self.tags = []

class Review:
    """评价"""
    def __init__(self, user_id, rating, comment):
        self.user_id = user_id
        self.rating = rating
        self.comment = comment
        self.time = datetime.now().isoformat()

class StrategyMarketplace:
    """
    策略市场
    支持: 策略上架、搜索、购买、评分、下载
    """
    def __init__(self):
        self.strategies = {}  # {id: StrategyListing}
        self.purchases = {}   # {user_id: [strategy_ids]}
        self.user_strategies = {}  # {user_id: [strategy_ids]} 作者发布的策略
        self.transactions = []  # 交易记录
        self.lock = Lock()
        
        # 平台设置
        self.platform_fee = 0.15  # 平台抽成 15%
        self.min_price = 0
        self.max_price = 10000
    
    def publish_strategy(self, author_id, name, strategy_type, price, description, code, tags=None):
        """发布策略"""
        with self.lock:
            strategy_id = f"STR_{len(self.strategies) + 1:06d}"
            
            strategy = StrategyListing(
                id=strategy_id,
                name=name,
                author=author_id,
                strategy_type=strategy_type,
                price=price,
                description=description
            )
            strategy.code_hash = hashlib.sha256(code.encode()).hexdigest()
            strategy.tags = tags or []
            
            self.strategies[strategy_id] = strategy
            
            if author_id not in self.user_strategies:
                self.user_strategies[author_id] = []
            self.user_strategies[author_id].append(strategy_id)
            
            print(f"[Marketplace] {author_id} 发布策略: {name} ({strategy_id})")
            return strategy_id
    
    def purchase_strategy(self, user_id, strategy_id, payment_method='balance'):
        """购买策略"""
        strategy = self.strategies.get(strategy_id)
        if not strategy or not strategy.is_active:
            return {'success': False, 'error': 'Strategy not found or inactive'}
        
        # 检查是否已购买
        if user_id in self.purchases and strategy_id in self.purchases[user_id]:
            return {'success': False, 'error': 'Already purchased'}
        
        # 免费策略
        if strategy.price == 0:
            if user_id not in self.purchases:
                self.purchases[user_id] = []
            self.purchases[user_id].append(strategy_id)
            strategy.downloads += 1
            return {'success': True, 'price': 0, 'code_hash': strategy.code_hash}
        
        # 付费策略 - 简化处理
        author_share = strategy.price * (1 - self.platform_fee)
        strategy.revenue += author_share
        
        if user_id not in self.purchases:
            self.purchases[user_id] = []
        self.purchases[user_id].append(strategy_id)
        strategy.downloads += 1
        
        self.transactions.append({
            'time': datetime.now().isoformat(),
            'user_id': user_id,
            'strategy_id': strategy_id,
            'amount': strategy.price,
            'author_share': author_share,
            'platform_fee': strategy.price * self.platform_fee
        })
        
        return {'success': True, 'price': strategy.price, 'code_hash': strategy.code_hash}
    
    def rate_strategy(self, user_id, strategy_id, rating, comment=""):
        """评价策略"""
        if user_id not in self.purchases or strategy_id not in self.purchases[user_id]:
            return {'success': False, 'error': 'Not purchased'}
        
        strategy = self.strategies.get(strategy_id)
        if not strategy:
            return {'success': False, 'error': 'Strategy not found'}
        
        review = Review(user_id, rating, comment)
        strategy.reviews.append(review)
        
        # 更新评分
        total = sum(r.rating for r in strategy.reviews)
        strategy.rating = total / len(strategy.reviews)
        strategy.ratings_count = len(strategy.reviews)
        
        return {'success': True, 'new_rating': strategy.rating}
    
    def search_strategies(self, query=None, strategy_type=None, min_price=None, 
                         max_price=None, tags=None, sort_by='rating'):
        """搜索策略"""
        results = []
        
        for strategy in self.strategies.values():
            if not strategy.is_active:
                continue
            
            # 过滤条件
            if query and query.lower() not in strategy.name.lower() and \
               query.lower() not in strategy.description.lower():
                continue
            
            if strategy_type and strategy.strategy_type != strategy_type:
                continue
            
            if min_price is not None and strategy.price < min_price:
                continue
            
            if max_price is not None and strategy.price > max_price:
                continue
            
            if tags and not any(t in strategy.tags for t in tags):
                continue
            
            results.append({
                'id': strategy.id,
                'name': strategy.name,
                'author': strategy.author,
                'type': strategy.strategy_type,
                'price': strategy.price,
                'rating': strategy.rating,
                'ratings_count': strategy.ratings_count,
                'downloads': strategy.downloads,
                'tags': strategy.tags,
                'description': strategy.description[:100] + '...' if len(strategy.description) > 100 else strategy.description
            })
        
        # 排序
        if sort_by == 'rating':
            results.sort(key=lambda x: x['rating'], reverse=True)
        elif sort_by == 'downloads':
            results.sort(key=lambda x: x['downloads'], reverse=True)
        elif sort_by == 'price_low':
            results.sort(key=lambda x: x['price'])
        elif sort_by == 'price_high':
            results.sort(key=lambda x: x['price'], reverse=True)
        elif sort_by == 'newest':
            results.sort(key=lambda x: x.get('created', ''), reverse=True)
        
        return results
    
    def get_strategy_details(self, strategy_id):
        """获取策略详情"""
        strategy = self.strategies.get(strategy_id)
        if not strategy:
            return None
        
        return {
            'id': strategy.id,
            'name': strategy.name,
            'author': strategy.author,
            'type': strategy.strategy_type,
            'price': strategy.price,
            'description': strategy.description,
            'rating': strategy.rating,
            'ratings_count': strategy.ratings_count,
            'downloads': strategy.downloads,
            'revenue': strategy.revenue,
            'tags': strategy.tags,
            'version': strategy.version,
            'created_at': strategy.created_at,
            'reviews': [{'user': r.user_id, 'rating': r.rating, 'comment': r.comment, 'time': r.time}
                      for r in strategy.reviews[-10:]]  # 最近10条评价
        }
    
    def get_user_purchases(self, user_id):
        """获取用户购买的策略"""
        if user_id not in self.purchases:
            return []
        
        return [self.get_strategy_details(sid) for sid in self.purchases[user_id]]
    
    def get_author_strategies(self, author_id):
        """获取作者发布的策略"""
        if author_id not in self.user_strategies:
            return []
        
        return [self.get_strategy_details(sid) for sid in self.user_strategies[author_id]]
    
    def get_market_stats(self):
        """获取市场统计"""
        total_strategies = len(self.strategies)
        total_downloads = sum(s.downloads for s in self.strategies.values())
        total_revenue = sum(s.revenue for s in self.strategies.values())
        avg_rating = sum(s.rating for s in self.strategies.values()) / total_strategies if total_strategies > 0 else 0
        
        return {
            'total_strategies': total_strategies,
            'total_downloads': total_downloads,
            'total_revenue': total_revenue,
            'avg_rating': avg_rating,
            'strategy_types': list(set(s.strategy_type for s in self.strategies.values()))
        }
