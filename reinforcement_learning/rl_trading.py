"""
Reinforcement Learning Trading - 强化学习交易
"""
import numpy as np
from typing import Dict, List, Tuple

class QLearningAgent:
    """Q-Learning交易智能体"""
    def __init__(self, state_size: int, action_size: int, learning_rate: float = 0.1,
                 discount_factor: float = 0.95, epsilon: float = 1.0):
        self.state_size = state_size
        self.action_size = action_size
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = epsilon
        self.q_table = np.zeros((state_size, action_size))
    
    def choose_action(self, state: int) -> int:
        """选择动作 (epsilon-greedy)"""
        if np.random.random() < self.epsilon:
            return np.random.randint(self.action_size)
        return np.argmax(self.q_table[state])
    
    def learn(self, state: int, action: int, reward: float, next_state: int):
        """学习"""
        current_q = self.q_table[state, action]
        max_next_q = np.max(self.q_table[next_state])
        new_q = current_q + self.lr * (reward + self.gamma * max_next_q - current_q)
        self.q_table[state, action] = new_q
    
    def decay_epsilon(self, decay: float = 0.995, min_epsilon: float = 0.01):
        """衰减探索率"""
        self.epsilon = max(self.epsilon * decay, min_epsilon)

class PolicyGradientAgent:
    """策略梯度智能体"""
    def __init__(self, state_size: int, action_size: int, hidden_size: int = 64):
        self.state_size = state_size
        self.action_size = action_size
        
        # 简化的策略网络 (策略梯度)
        np.random.seed(42)
        self.weights = {
            'W1': np.random.randn(state_size, hidden_size) * 0.1,
            'b1': np.zeros(hidden_size),
            'W2': np.random.randn(hidden_size, action_size) * 0.1,
            'b2': np.zeros(action_size)
        }
        
        self.learning_rate = 0.001
    
    def softmax(self, x: np.ndarray) -> np.ndarray:
        """Softmax激活"""
        exp_x = np.exp(x - np.max(x))
        return exp_x / np.sum(exp_x)
    
    def forward(self, state: np.ndarray) -> np.ndarray:
        """前向传播"""
        x = np.dot(state, self.weights['W1']) + self.weights['b1']
        x = np.tanh(x)
        x = np.dot(x, self.weights['W2']) + self.weights['b2']
        return self.softmax(x)
    
    def choose_action(self, state: np.ndarray) -> int:
        """选择动作"""
        probs = self.forward(state)
        return np.random.choice(self.action_size, p=probs)
    
    def update(self, states: np.ndarray, actions: np.ndarray, rewards: np.ndarray):
        """策略梯度更新"""
        for i in range(len(states)):
            state = states[i]
            action = actions[i]
            reward = rewards[i]
            
            probs = self.forward(state)
            loss = -np.log(probs[action] + 1e-8) * reward
            
            # 简化梯度更新
            delta = reward * (1 - probs[action])
            self.weights['W2'] += self.learning_rate * delta * np.tanh(
                np.dot(state, self.weights['W1'])
            ).reshape(-1, 1) @ probs.reshape(1, -1)

class RLTradingEnvironment:
    """强化学习交易环境"""
    def __init__(self, initial_balance: float = 10000):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.position = 0
        self.price_history = []
        self.trades = []
    
    def reset(self) -> np.ndarray:
        """重置环境"""
        self.balance = self.initial_balance
        self.position = 0
        self.price_history = []
        self.trades = []
        return self._get_state()
    
    def step(self, action: int, price: float) -> Tuple[np.ndarray, float, bool]:
        """执行动作,返回 (下一状态, 奖励, 是否结束)"""
        # Action: 0=Hold, 1=Buy, 2=Sell
        done = False
        
        if action == 1 and self.balance >= price:  # Buy
            self.balance -= price
            self.position += 1
            self.trades.append({'action': 'BUY', 'price': price})
        
        elif action == 2 and self.position > 0:  # Sell
            self.balance += price
            self.position -= 1
            self.trades.append({'action': 'SELL', 'price': price})
        
        self.price_history.append(price)
        
        # 奖励 = 权益变化
        new_equity = self.balance + self.position * price
        reward = (new_equity - (self.initial_balance + sum(t.get('pnl', 0) for t in self.trades))) / self.initial_balance
        
        state = self._get_state()
        
        return state, reward, done
    
    def _get_state(self) -> np.ndarray:
        """获取状态"""
        if len(self.price_history) < 20:
            return np.zeros(25)
        
        prices = self.price_history[-20:]
        returns = np.diff(prices) / prices[:-1] if len(prices) > 1 else np.zeros(19)
        
        return np.concatenate([
            [self.balance / self.initial_balance],
            [self.position],
            returns[-19:],
            [prices[-1] / prices[0] if prices[0] > 0 else 1]
        ])
    
    def get_portfolio_value(self, current_price: float) -> float:
        """获取组合价值"""
        return self.balance + self.position * current_price
