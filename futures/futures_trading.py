"""
合约交易引擎 - 永续合约+杠杆
"""
import hashlib, hmac, time, requests
from enum import Enum

class PositionMode(Enum):
    ONE_WAY = "one_way"
    HEDGE = "hedge"

class FuturesOrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_MARKET = "STOP_MARKET"
    TAKE_PROFIT = "TAKE_PROFIT"
    LIQUIDATION = "LIQUIDATION"

class FuturesOrder:
    def __init__(self, symbol, side, qty, price=None, order_type='MARKET', leverage=1):
        self.symbol = symbol
        self.side = side  # OPEN_LONG, OPEN_SHORT, CLOSE_LONG, CLOSE_SHORT
        self.qty = qty
        self.price = price
        self.type = order_type
        self.leverage = leverage
        self.order_id = None
        self.status = 'pending'
        self.filled_qty = 0
        self.avg_price = 0
        self.liquidation_price = 0
        self.unrealized_pnl = 0
        self.create_time = time.time()

class FuturesPosition:
    def __init__(self, symbol):
        self.symbol = symbol
        self.size = 0  # 正=多头, 负=空头
        self.entry_price = 0
        self.leverage = 1
        self.liquidation_price = 0
        self.margin = 0
        self.unrealized_pnl = 0
        self.unrealized_pnl_pct = 0
        self.maintenance_margin = 0
        self.update_time = time.time()

class FuturesTrading:
    """
    合约交易引擎
    支持: 永续合约、杠杆、止损止盈、强平保护
    """
    def __init__(self, api_key, api_secret, proxy):
        self.api_key = api_key
        self.api_secret = api_secret
        self.proxy = proxy
        self.base_url = "https://fapi.binance.com"
        self.positions = {}  # {symbol: FuturesPosition}
        self.orders = {}
        self.leverage = 1
        self.margin_mode = 'ISOLATED'  # ISOLATED / CROSS
        self.position_mode = PositionMode.ONE_WAY
    
    def set_leverage(self, symbol, leverage):
        """设置杠杆"""
        try:
            params = {
                'symbol': symbol.upper(),
                'leverage': leverage,
                'timestamp': int(time.time()*1000)
            }
            sig = self._sign(params)
            r = requests.post(
                f"{self.base_url}/fapi/v1/leverage",
                params={**params, 'signature': sig},
                headers={'X-MBX-APIKEY': self.api_key},
                proxies=self.proxy, timeout=10
            )
            if r.status_code == 200:
                print(f"[Futures] {symbol} 杠杆设置为 {leverage}x")
                return True
        except Exception as e:
            print(f"[Futures] 设置杠杆失败: {e}")
        return False
    
    def set_margin_mode(self, symbol, mode='ISOLATED'):
        """设置保证金模式"""
        try:
            params = {
                'symbol': symbol.upper(),
                'marginType': mode,
                'timestamp': int(time.time()*1000)
            }
            sig = self._sign(params)
            r = requests.post(
                f"{self.base_url}/fapi/v1/marginType",
                params={**params, 'signature': sig},
                headers={'X-MBX-APIKEY': self.api_key},
                proxies=self.proxy, timeout=10
            )
            return r.status_code == 200
        except:
            return False
    
    def open_long(self, symbol, qty, price=None, order_type='MARKET', leverage=None):
        """开多"""
        if leverage:
            self.set_leverage(symbol, leverage)
        return self._send_order(symbol, 'BUY', qty, price, order_type)
    
    def open_short(self, symbol, qty, price=None, order_type='MARKET', leverage=None):
        """开空"""
        if leverage:
            self.set_leverage(symbol, leverage)
        return self._send_order(symbol, 'SELL', qty, price, order_type)
    
    def close_long(self, symbol, qty=None, price=None, order_type='MARKET'):
        """平多"""
        if qty is None:
            pos = self.positions.get(symbol)
            qty = abs(pos.size) if pos else 0
        return self._send_order(symbol, 'SELL', qty, price, order_type)
    
    def close_short(self, symbol, qty=None, price=None, order_type='MARKET'):
        """平空"""
        if qty is None:
            pos = self.positions.get(symbol)
            qty = abs(pos.size) if pos else 0
        return self._send_order(symbol, 'BUY', qty, price, order_type)
    
    def _send_order(self, symbol, side, qty, price, order_type):
        """发送订单"""
        try:
            params = {
                'symbol': symbol.upper(),
                'side': side,
                'type': order_type,
                'quantity': str(qty),
                'timestamp': int(time.time()*1000),
                'recvWindow': 5000
            }
            if order_type == 'LIMIT' and price:
                params['price'] = str(price)
                params['timeInForce'] = 'GTC'
            
            sig = self._sign(params)
            r = requests.post(
                f"{self.base_url}/fapi/v1/order",
                params={**params, 'signature': sig},
                headers={'X-MBX-APIKEY': self.api_key},
                proxies=self.proxy, timeout=10
            )
            data = r.json()
            if 'orderId' in data:
                return {'success': True, 'order_id': str(data['orderId']), 'data': data}
            return {'success': False, 'msg': data.get('msg', 'Error')}
        except Exception as e:
            return {'success': False, 'msg': str(e)}
    
    def set_stop_loss(self, symbol, price, qty=None):
        """设置止损"""
        try:
            params = {
                'symbol': symbol.upper(),
                'side': 'SELL' if self.positions.get(symbol, FuturesPosition(symbol)).size > 0 else 'BUY',
                'type': 'STOP_MARKET',
                'stopPrice': str(price),
                'quantity': str(qty) if qty else '',
                'closePosition': 'true' if not qty else 'false',
                'timestamp': int(time.time()*1000),
                'recvWindow': 5000
            }
            sig = self._sign(params)
            r = requests.post(
                f"{self.base_url}/fapi/v1/order",
                params={**params, 'signature': sig},
                headers={'X-MBX-APIKEY': self.api_key},
                proxies=self.proxy, timeout=10
            )
            return r.status_code == 200
        except:
            return False
    
    def set_take_profit(self, symbol, price, qty=None):
        """设置止盈"""
        try:
            params = {
                'symbol': symbol.upper(),
                'side': 'SELL' if self.positions.get(symbol, FuturesPosition(symbol)).size > 0 else 'BUY',
                'type': 'TAKE_PROFIT_MARKET',
                'stopPrice': str(price),
                'quantity': str(qty) if qty else '',
                'closePosition': 'true' if not qty else 'false',
                'timestamp': int(time.time()*1000),
                'recvWindow': 5000
            }
            sig = self._sign(params)
            r = requests.post(
                f"{self.base_url}/fapi/v1/order",
                params={**params, 'signature': sig},
                headers={'X-MBX-APIKEY': self.api_key},
                proxies=self.proxy, timeout=10
            )
            return r.status_code == 200
        except:
            return False
    
    def get_position(self, symbol):
        """获取持仓"""
        try:
            params = {'timestamp': int(time.time()*1000), 'recvWindow': 5000}
            sig = self._sign(params)
            r = requests.get(
                f"{self.base_url}/fapi/v2/positionRisk",
                params={**params, 'signature': sig},
                headers={'X-MBX-APIKEY': self.api_key},
                proxies=self.proxy, timeout=10
            )
            if r.status_code == 200:
                for p in r.json():
                    if p['symbol'] == symbol.upper():
                        pos = FuturesPosition(symbol)
                        pos.size = float(p['positionAmt'])
                        pos.entry_price = float(p['entryPrice'])
                        pos.leverage = float(p['leverage'])
                        pos.liquidation_price = float(p['liquidationPrice'])
                        pos.margin = float(p['isolatedMargin'])
                        pos.unrealized_pnl = float(p['unRealizedProfit'])
                        self.positions[symbol] = pos
                        return pos
        except Exception as e:
            print(f"[Futures] 获取持仓失败: {e}")
        return None
    
    def get_all_positions(self):
        """获取所有持仓"""
        self.positions.clear()
        try:
            params = {'timestamp': int(time.time()*1000), 'recvWindow': 5000}
            sig = self._sign(params)
            r = requests.get(
                f"{self.base_url}/fapi/v2/positionRisk",
                params={**params, 'signature': sig},
                headers={'X-MBX-APIKEY': self.api_key},
                proxies=self.proxy, timeout=10
            )
            if r.status_code == 200:
                for p in r.json():
                    if float(p['positionAmt']) != 0:
                        symbol = p['symbol']
                        pos = FuturesPosition(symbol)
                        pos.size = float(p['positionAmt'])
                        pos.entry_price = float(p['entryPrice'])
                        pos.leverage = float(p['leverage'])
                        pos.liquidation_price = float(p['liquidationPrice'])
                        pos.margin = float(p['isolatedMargin'])
                        pos.unrealized_pnl = float(p['unRealizedProfit'])
                        self.positions[symbol] = pos
        except:
            pass
        return self.positions
    
    def get_balance(self):
        """获取合约余额"""
        try:
            params = {'timestamp': int(time.time()*1000), 'recvWindow': 5000}
            sig = self._sign(params)
            r = requests.get(
                f"{self.base_url}/fapi/v2/balance",
                params={**params, 'signature': sig},
                headers={'X-MBX-APIKEY': self.api_key},
                proxies=self.proxy, timeout=10
            )
            if r.status_code == 200:
                for b in r.json():
                    if b['asset'] == 'USDT':
                        return {
                            'asset': 'USDT',
                            'balance': float(b['balance']),
                            'available': float(b['availableBalance']),
                            'unrealized_pnl': float(b['unrealizedProfit'])
                        }
        except:
            pass
        return {}
    
    def _sign(self, params):
        q_str = '&'.join(f"{k}={v}" for k, v in sorted(params.items()))
        return hmac.new(self.api_secret.encode(), q_str.encode(), hashlib.sha256).hexdigest()
    
    def get_funding_rate(self, symbol):
        """获取资金费率"""
        try:
            r = requests.get(
                f"{self.base_url}/fapi/v1/premiumIndex",
                params={'symbol': symbol.upper()},
                proxies=self.proxy, timeout=10
            )
            if r.status_code == 200:
                d = r.json()
                return {
                    'symbol': d['symbol'],
                    'funding_rate': float(d['lastFundingRate']) * 100,  # 转百分比
                    'next_funding_time': int(d['nextFundingTime'])
                }
        except:
            pass
        return {}
