"""
期权交易引擎 - 币权期权
"""
import hashlib, hmac, time, requests
from enum import Enum

class OptionType(Enum):
    CALL = "CALL"
    PUT = "PUT"

class OptionStyle(Enum):
    EUROPEAN = "EUROPEAN"
    AMERICAN = "AMERICAN"

class OptionPosition:
    """期权持仓"""
    def __init__(self, symbol, option_type, strike, expiry, qty, premium):
        self.symbol = symbol
        self.option_type = option_type
        self.strike = strike
        self.expiry = expiry
        self.qty = qty
        self.premium = premium
        self.unrealized_pnl = 0
        self.mark_price = 0

class OptionsTrading:
    """
    期权交易引擎
    支持: 买入期权、卖出期权、行使、平仓
    """
    def __init__(self, api_key, api_secret, proxy):
        self.api_key = api_key
        self.api_secret = api_secret
        self.proxy = proxy
        self.base_url = "https://api.binance.com"
        self.positions = {}
        self.orders = {}
    
    def get_option_chain(self, symbol='BTCUSDT'):
        """获取期权链"""
        try:
            r = requests.get(
                f"{self.base_url}/vapi/v1/optionChainInfo",
                params={'symbol': symbol},
                proxies=self.proxy, timeout=10
            )
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            print(f"[Options] Get chain error: {e}")
        return None
    
    def get_symbol_info(self, symbol):
        """获取标的信息"""
        try:
            r = requests.get(
                f"{self.base_url}/vapi/v1/accountInfo",
                params={'timestamp': int(time.time()*1000)},
                proxies=self.proxy, timeout=10
            )
            if r.status_code == 200:
                return r.json()
        except:
            pass
        return None
    
    def buy_option(self, symbol, option_type, strike_price, expiry_date, qty):
        """买入期权 (开多看涨或开空看跌)"""
        try:
            params = {
                'symbol': symbol,
                'side': 'BUY',
                'positionSide': 'LONG' if option_type == OptionType.CALL else 'SHORT',
                'strikePrice': strike_price,
                'expiryDate': expiry_date,
                'qty': qty,
                'optionsType': option_type.value,
                'timestamp': int(time.time()*1000)
            }
            sig = self._sign(params)
            r = requests.post(
                f"{self.base_url}/vapi/v1/order",
                params={**params, 'signature': sig},
                headers={'X-MBX-APIKEY': self.api_key},
                proxies=self.proxy, timeout=10
            )
            if r.status_code == 200:
                data = r.json()
                if 'orderId' in data:
                    order_id = str(data['orderId'])
                    self.orders[order_id] = data
                    return {'success': True, 'order_id': order_id, 'data': data}
            return {'success': False, 'msg': r.text}
        except Exception as e:
            return {'success': False, 'msg': str(e)}
    
    def sell_option(self, symbol, option_type, strike_price, expiry_date, qty):
        """卖出期权"""
        try:
            params = {
                'symbol': symbol,
                'side': 'SELL',
                'positionSide': 'LONG' if option_type == OptionType.CALL else 'SHORT',
                'strikePrice': strike_price,
                'expiryDate': expiry_date,
                'qty': qty,
                'optionsType': option_type.value,
                'timestamp': int(time.time()*1000)
            }
            sig = self._sign(params)
            r = requests.post(
                f"{self.base_url}/vapi/v1/order",
                params={**params, 'signature': sig},
                headers={'X-MBX-APIKEY': self.api_key},
                proxies=self.proxy, timeout=10
            )
            if r.status_code == 200:
                return {'success': True, 'data': r.json()}
            return {'success': False, 'msg': r.text}
        except Exception as e:
            return {'success': False, 'msg': str(e)}
    
    def exercise_option(self, symbol, position_id, qty):
        """行使期权"""
        try:
            params = {
                'symbol': symbol,
                'positionId': position_id,
                'qty': qty,
                'timestamp': int(time.time()*1000)
            }
            sig = self._sign(params)
            r = requests.post(
                f"{self.base_url}/vapi/v1/exercise",
                params={**params, 'signature': sig},
                headers={'X-MBX-APIKEY': self.api_key},
                proxies=self.proxy, timeout=10
            )
            return r.status_code == 200
        except:
            return False
    
    def get_positions(self):
        """获取期权持仓"""
        try:
            params = {'timestamp': int(time.time()*1000)}
            sig = self._sign(params)
            r = requests.get(
                f"{self.base_url}/vapi/v1/position",
                params={**params, 'signature': sig},
                headers={'X-MBX-APIKEY': self.api_key},
                proxies=self.proxy, timeout=10
            )
            if r.status_code == 200:
                return r.json()
        except:
            pass
        return None
    
    def calculate_greeks(self, S, K, T, r, sigma, option_type='call'):
        """计算Greeks (简化版)"""
        import math
        
        # 简化: 使用Black-Scholes近似
        if T <= 0:
            return {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0}
        
        # 简化delta
        if option_type == 'call':
            delta = 0.5 if S == K else (1 if S > K else 0)
        else:
            delta = -0.5 if S == K else (-1 if S < K else 0)
        
        # 简化gamma, theta, vega
        gamma = 0.01
        theta = -0.001 * (1/365)
        vega = 0.1 * sigma / 100
        
        return {
            'delta': delta,
            'gamma': gamma,
            'theta': theta,
            'vega': vega
        }
    
    def _sign(self, params):
        q_str = '&'.join(f"{k}={v}" for k, v in sorted(params.items()))
        return hmac.new(self.api_secret.encode(), q_str.encode(), hashlib.sha256).hexdigest()
