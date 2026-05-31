"""
DMA - Direct Market Access
交易所直连
"""
import socket, struct
from typing import Dict, List

class DMAConnection:
    """
    DMA直连
    低延迟交易所直连
    """
    def __init__(self, exchange: str, host: str, port: int):
        self.exchange = exchange
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
    
    def connect(self) -> bool:
        """建立连接"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.connected = True
            return True
        except Exception as e:
            print(f"[DMA] Connection failed: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.socket:
            self.socket.close()
            self.connected = False
    
    def send_order(self, order: Dict) -> Dict:
        """发送订单"""
        if not self.connected:
            return {'success': False, 'error': 'Not connected'}
        
        try:
            # 编码订单
            packet = self._encode_order(order)
            self.socket.sendall(packet)
            
            # 接收确认
            response = self.socket.recv(1024)
            
            return self._decode_response(response)
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _encode_order(self, order: Dict) -> bytes:
        """编码订单"""
        # 简化: 实际应使用二进制协议
        import json
        return json.dumps(order).encode()
    
    def _decode_response(self, data: bytes) -> Dict:
        """解码响应"""
        import json
        return json.loads(data.decode())
    
    def cancel_order(self, order_id: str) -> Dict:
        """取消订单"""
        return self.send_order({'type': 'cancel', 'order_id': order_id})
    
    def get_order_status(self, order_id: str) -> Dict:
        """查询订单状态"""
        return self.send_order({'type': 'status', 'order_id': order_id})

class DMAGateway:
    """DMA网关"""
    def __init__(self):
        self.connections = {}  # {exchange: DMAConnection}
        self.order_routes = {}   # {symbol: exchange}
    
    def add_connection(self, exchange: str, host: str, port: int):
        """添加连接"""
        conn = DMAConnection(exchange, host, port)
        if conn.connect():
            self.connections[exchange] = conn
            return True
        return False
    
    def route_order(self, symbol: str, order: Dict) -> Dict:
        """路由订单"""
        exchange = self.order_routes.get(symbol, 'binance')
        conn = self.connections.get(exchange)
        
        if conn:
            return conn.send_order(order)
        return {'success': False, 'error': 'No route'}
