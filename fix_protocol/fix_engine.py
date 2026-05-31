"""
FIX Protocol - 金融信息交换协议
机构级标准协议
"""
import struct, hashlib
from enum import Enum

class FIXVersion(Enum):
    FIX_4_0 = "FIX.4.0"
    FIX_4_2 = "FIX.4.2"
    FIX_4_4 = "FIX.4.4"
    FIX_5_0 = "FIX.5.0"

class FIXMsgType(Enum):
    NEW_ORDER_SINGLE = "D"
    ORDER_CANCEL_REQUEST = "F"
    ORDER_CANCEL_REPLACE = "G"
    ORDER_STATUS_REQUEST = "H"
    ORDER_MASS_CANCEL = "q"
    EXECUTION_REPORT = "8"
    ORDER_CANCEL_REJECT = "9"
    BUSINESS_MESSAGE_REJECT = "j"

class FIXSession:
    """FIX会话"""
    def __init__(self, sender_id, target_id, version=FIXVersion.FIX_4_4):
        self.sender_id = sender_id
        self.target_id = target_id
        self.version = version
        self.heartbeat_int = 30
        self.next_seq_num = 1
        self.last_seq_num = 0
        self.last_time = 0
        self.reset_time = 0
    
    def pack_message(self, msg_type, fields):
        """打包FIX消息"""
        # 构造消息体
        body = []
        body.append(f"35={msg_type.value}")  # MsgType
        body.append(f"49={self.sender_id}")  # SenderCompID
        body.append(f"56={self.target_id}")  # TargetCompID
        body.append(f"34={self.next_seq_num}")  # MsgSeqNum
        body.append(f"52={self._timestamp()}")  # SendingTime
        
        for tag, value in fields.items():
            body.append(f"{tag}={value}")
        
        # 计算Checksum
        soh = chr(1)
        msg_str = soh.join(body) + soh
        checksum = self._checksum(msg_str)
        msg_str += f"10={checksum}{soh}"
        
        self.next_seq_num += 1
        return msg_str
    
    def unpack_message(self, raw_msg):
        """解包FIX消息"""
        parts = raw_msg.split(chr(1))
        fields = {}
        
        for part in parts:
            if '=' in part:
                tag, value = part.split('=', 1)
                fields[int(tag)] = value
        
        return fields
    
    def _checksum(self, msg):
        """计算Checksum"""
        return hashlib.md5(msg.encode()).hexdigest()[:4].upper()
    
    def _timestamp(self):
        """生成时间戳"""
        from datetime import datetime
        return datetime.utcnow().strftime("%Y%m%d-%H:%M:%S")
    
    def logon(self, password=None):
        """登录消息"""
        fields = {
            96: password,  # EncryptData
            108: self.heartbeat_int,  # HeartBtInt
        }
        return self.pack_message(FIXMsgType.NEW_ORDER_SINGLE, fields)
    
    def logout(self):
        """登出消息"""
        return self.pack_message(FIXMsgType.EXECUTION_REPORT, {})
    
    def heartbeat(self):
        """心跳消息"""
        return self.pack_message(FIXMsgType.EXECUTION_REPORT, {})

class FIXMessageBuilder:
    """FIX消息构造器"""
    @staticmethod
    def new_order_single(order_id, symbol, side, qty, order_type='1'):
        """构造新订单"""
        return {
            11: order_id,      # ClOrdID
            55: symbol,        # Symbol
            54: side,          # Side (1=Buy, 2=Sell)
            38: qty,           # OrderQty
            40: order_type,     # OrdType (1=Market, 2=Limit)
            59: "0",           # TimeInForce (0=Day)
        }
    
    @staticmethod
    def order_cancel(order_id, orig_order_id):
        """取消订单"""
        return {
            11: order_id,      # ClOrdID
            41: orig_order_id,  # OrigClOrdID
        }
    
    @staticmethod
    def order_replace(order_id, orig_order_id, new_qty=None, new_price=None):
        """替换订单"""
        fields = {
            11: order_id,
            41: orig_order_id,
        }
        if new_qty:
            fields[38] = new_qty
        if new_price:
            fields[44] = new_price
        return fields
    
    @staticmethod
    def order_status(order_id):
        """查询订单状态"""
        return {11: order_id}

class FIXParser:
    """FIX消息解析器"""
    def __init__(self):
        self.handlers = {}
    
    def register_handler(self, msg_type, handler):
        """注册消息处理器"""
        self.handlers[msg_type] = handler
    
    def parse(self, raw_msg, session):
        """解析消息"""
        fields = session.unpack_message(raw_msg)
        
        msg_type = fields.get(35)
        if msg_type in self.handlers:
            return self.handlers[msg_type](fields)
        
        return None

class FIXProtocol:
    """
    FIX Protocol 完整实现
    """
    def __init__(self, config):
        self.config = config
        self.session = FIXSession(
            sender_id=config.get('sender_id'),
            target_id=config.get('target_id'),
            version=FIXVersion[config.get('version', 'FIX_4_4')]
        )
        self.parser = FIXParser()
        self.connected = False
    
    def connect(self):
        """建立连接"""
        print(f"[FIX] Connecting to {self.config.get('target_id')}")
        self.connected = True
    
    def disconnect(self):
        """断开连接"""
        self.connected = False
        print("[FIX] Disconnected")
    
    def send_order(self, symbol, side, qty, price=None, order_type='market'):
        """发送订单"""
        if not self.connected:
            return None
        
        order_id = f"O{int(time.time()*1000000)}"
        fields = FIXMessageBuilder.new_order_single(
            order_id, symbol, side, qty, 
            '1' if order_type == 'market' else '2'
        )
        
        if price and order_type == 'limit':
            fields[44] = price
        
        msg = self.session.pack_message(FIXMsgType.NEW_ORDER_SINGLE, fields)
        
        return {'raw': msg, 'order_id': order_id}
    
    def cancel_order(self, order_id, orig_order_id):
        """取消订单"""
        if not self.connected:
            return None
        
        fields = FIXMessageBuilder.order_cancel(order_id, orig_order_id)
        msg = self.session.pack_message(FIXMsgType.ORDER_CANCEL_REQUEST, fields)
        return {'raw': msg}
    
    def replace_order(self, order_id, orig_order_id, new_qty=None, new_price=None):
        """替换订单"""
        if not self.connected:
            return None
        
        fields = FIXMessageBuilder.order_replace(order_id, orig_order_id, new_qty, new_price)
        msg = self.session.pack_message(FIXMsgType.ORDER_CANCEL_REPLACE, fields)
        return {'raw': msg}

import time
