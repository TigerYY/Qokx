"""
OKX WebSocket客户端 - 支持实时行情数据和账户事件订阅
"""

import asyncio
import json
import logging
import time
import hashlib
import hmac
import base64
from typing import Dict, List, Optional, Callable, Any
import websockets
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger(__name__)


class OKXWebSocketClient:
    """OKX WebSocket客户端"""
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 secret_key: Optional[str] = None,
                 passphrase: Optional[str] = None,
                 testnet: bool = False,
                 reconnect_interval: int = 5):
        """
        初始化OKX WebSocket客户端
        
        Args:
            api_key: OKX API密钥（私有频道需要）
            secret_key: OKX密钥密钥（私有频道需要）
            passphrase: OKX交易密码（私有频道需要）
            testnet: 是否使用测试网
            reconnect_interval: 重连间隔(秒)
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase
        self.reconnect_interval = reconnect_interval
        
        # 设置WebSocket端点
        if testnet:
            self.ws_url = "wss://wspap.okx.com:8443/ws/v5/public"
            self.private_ws_url = "wss://wspap.okx.com:8443/ws/v5/private"
            logger.info("使用OKX测试网WebSocket环境")
        else:
            self.ws_url = "wss://ws.okx.com:8443/ws/v5/public"
            self.private_ws_url = "wss://ws.okx.com:8443/ws/v5/private"
            logger.info("使用OKX主网WebSocket环境")
        
        self.public_ws = None
        self.private_ws = None
        self.is_connected = False
        self.subscriptions = {
            'public': set(),
            'private': set()
        }
        self.callbacks = {
            'tickers': {},
            'trades': {},
            'books': {},
            'candles': {},
            'account': {},
            'positions': {},
            'orders': {},
            'error': {}
        }
        
        # 连接状态监控
        self.last_pong_time = time.time()
        self.ping_interval = 20  # 每20秒发送一次ping
    
    def _sign_login(self) -> Dict[str, str]:
        """生成登录签名"""
        if not all([self.api_key, self.secret_key, self.passphrase]):
            raise ValueError("私有频道需要API密钥、密钥密钥和交易密码")
        
        timestamp = str(round(time.time() * 1000))
        
        # 构建待签名字符串
        message = timestamp + 'GET' + '/users/self/verify'
        
        # 计算签名
        signature = base64.b64encode(
            hmac.new(
                self.secret_key.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        
        return {
            'apiKey': self.api_key,
            'passphrase': self.passphrase,
            'timestamp': timestamp,
            'sign': signature
        }
    
    async def connect_public(self):
        """连接公共频道"""
        try:
            self.public_ws = await websockets.connect(self.ws_url, ping_interval=None)
            logger.info("公共WebSocket连接已建立")
            
            # 启动消息处理循环
            asyncio.create_task(self._handle_public_messages())
            
        except Exception as e:
            logger.error(f"公共WebSocket连接失败: {e}")
            raise
    
    async def connect_private(self):
        """连接私有频道"""
        try:
            self.private_ws = await websockets.connect(self.private_ws_url, ping_interval=None)
            logger.info("私有WebSocket连接已建立")
            
            # 登录
            login_data = self._sign_login()
            await self.private_ws.send(json.dumps({
                'op': 'login',
                'args': [login_data]
            }))
            
            # 启动消息处理循环
            asyncio.create_task(self._handle_private_messages())
            
        except Exception as e:
            logger.error(f"私有WebSocket连接失败: {e}")
            raise
    
    async def connect(self):
        """连接所有频道"""
        await self.connect_public()
        if self.api_key and self.secret_key and self.passphrase:
            await self.connect_private()
        
        self.is_connected = True
        
        # 启动心跳检测
        asyncio.create_task(self._heartbeat())
    
    async def disconnect(self):
        """断开连接"""
        self.is_connected = False
        
        if self.public_ws:
            await self.public_ws.close()
            self.public_ws = None
        
        if self.private_ws:
            await self.private_ws.close()
            self.private_ws = None
        
        logger.info("WebSocket连接已关闭")
    
    async def _heartbeat(self):
        """心跳检测"""
        while self.is_connected:
            try:
                # 发送ping
                if self.public_ws:
                    await self.public_ws.ping()
                if self.private_ws:
                    await self.private_ws.ping()
                
                # 检查pong响应
                current_time = time.time()
                if current_time - self.last_pong_time > self.ping_interval * 2:
                    logger.warning("WebSocket连接可能已断开，尝试重连...")
                    await self._reconnect()
                
                await asyncio.sleep(self.ping_interval)
                
            except Exception as e:
                logger.error(f"心跳检测失败: {e}")
                await asyncio.sleep(self.reconnect_interval)
    
    async def _reconnect(self):
        """重连逻辑"""
        await self.disconnect()
        await asyncio.sleep(self.reconnect_interval)
        await self.connect()
        
        # 重新订阅所有频道
        await self._resubscribe()
    
    async def _resubscribe(self):
        """重新订阅所有频道"""
        # 重新订阅公共频道
        if self.subscriptions['public']:
            await self.public_ws.send(json.dumps({
                'op': 'subscribe',
                'args': list(self.subscriptions['public'])
            }))
        
        # 重新订阅私有频道
        if self.subscriptions['private'] and self.private_ws:
            await self.private_ws.send(json.dumps({
                'op': 'subscribe',
                'args': list(self.subscriptions['private'])
            }))
    
    async def _handle_public_messages(self):
        """处理公共频道消息"""
        try:
            async for message in self.public_ws:
                await self._process_message(message, 'public')
        except ConnectionClosed:
            logger.warning("公共WebSocket连接已关闭")
            if self.is_connected:
                await self._reconnect()
        except Exception as e:
            logger.error(f"处理公共消息失败: {e}")
    
    async def _handle_private_messages(self):
        """处理私有频道消息"""
        try:
            async for message in self.private_ws:
                await self._process_message(message, 'private')
        except ConnectionClosed:
            logger.warning("私有WebSocket连接已关闭")
            if self.is_connected:
                await self._reconnect()
        except Exception as e:
            logger.error(f"处理私有消息失败: {e}")
    
    async def _process_message(self, message: str, channel_type: str):
        """处理WebSocket消息"""
        try:
            data = json.loads(message)
            
            # 处理pong响应
            if data.get('event') == 'pong':
                self.last_pong_time = time.time()
                return
            
            # 处理错误消息
            if data.get('event') == 'error':
                error_msg = data.get('msg', '未知错误')
                logger.error(f"WebSocket错误: {error_msg}")
                await self._trigger_callbacks('error', data)
                return
            
            # 处理订阅确认
            if data.get('event') == 'subscribe':
                logger.info(f"订阅成功: {data.get('arg', {})}")
                return
            
            # 处理数据消息
            if 'arg' in data and 'data' in data:
                channel = data['arg'].get('channel')
                
                if channel == 'tickers':
                    await self._trigger_callbacks('tickers', data['data'])
                elif channel == 'trades':
                    await self._trigger_callbacks('trades', data['data'])
                elif channel.startswith('books'):
                    await self._trigger_callbacks('books', data['data'])
                elif channel.startswith('candle'):
                    await self._trigger_callbacks('candles', data['data'])
                elif channel == 'account':
                    await self._trigger_callbacks('account', data['data'])
                elif channel == 'positions':
                    await self._trigger_callbacks('positions', data['data'])
                elif channel == 'orders':
                    await self._trigger_callbacks('orders', data['data'])
                
        except json.JSONDecodeError:
            logger.error(f"JSON解析失败: {message}")
        except Exception as e:
            logger.error(f"处理消息失败: {e}")
    
    async def _trigger_callbacks(self, callback_type: str, data: Any):
        """触发回调函数"""
        if callback_type in self.callbacks:
            for callback_id, callback in self.callbacks[callback_type].items():
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    logger.error(f"回调函数执行失败: {e}")
    
    # 订阅方法
    
    async def subscribe_tickers(self, inst_ids: List[str], callback: Callable):
        """订阅行情数据"""
        args = [{'channel': 'tickers', 'instId': inst_id} for inst_id in inst_ids]
        await self._subscribe('public', args, 'tickers', callback)
    
    async def subscribe_trades(self, inst_ids: List[str], callback: Callable):
        """订阅交易数据"""
        args = [{'channel': 'trades', 'instId': inst_id} for inst_id in inst_ids]
        await self._subscribe('public', args, 'trades', callback)
    
    async def subscribe_orderbook(self, inst_ids: List[str], callback: Callable, depth: str = 'books5'):
        """订阅订单簿数据"""
        args = [{'channel': depth, 'instId': inst_id} for inst_id in inst_ids]
        await self._subscribe('public', args, 'books', callback)
    
    async def subscribe_candles(self, inst_ids: List[str], callback: Callable, bar: str = '1m'):
        """订阅K线数据"""
        args = [{'channel': f'candle{bar}', 'instId': inst_id} for inst_id in inst_ids]
        await self._subscribe('public', args, 'candles', callback)
    
    async def subscribe_orders(self, callback: Callable, inst_type: str = 'SPOT'):
        """订阅订单信息"""
        args = [{'channel': 'orders', 'instType': inst_type}]
        await self._subscribe('private', args, 'orders', callback)
    
    async def _subscribe(self, channel_type: str, args: List[Dict], callback_key: str, callback: Callable):
        """通用订阅方法"""
        if channel_type == 'public' and not self.public_ws:
            raise ConnectionError("公共WebSocket未连接")
        if channel_type == 'private' and not self.private_ws:
            raise ConnectionError("私有WebSocket未连接")
        
        # 生成回调ID
        callback_id = str(hash(str(args)))
        self.callbacks[callback_key][callback_id] = callback
        
        # 发送订阅请求
        ws = self.public_ws if channel_type == 'public' else self.private_ws
        await ws.send(json.dumps({
            'op': 'subscribe',
            'args': args
        }))
        
        # 记录订阅
        for arg in args:
            self.subscriptions[channel_type].add(json.dumps(arg))
    
    # 取消订阅方法
    
    async def unsubscribe_tickers(self, inst_ids: List[str]):
        """取消订阅行情数据"""
        args = [{'channel': 'tickers', 'instId': inst_id} for inst_id in inst_ids]
        await self._unsubscribe('public', args, 'tickers')
    
    async def unsubscribe_all(self):
        """取消所有订阅"""
        # 取消公共频道订阅
        if self.subscriptions['public']:
            args = [json.loads(sub) for sub in self.subscriptions['public']]
            await self.public_ws.send(json.dumps({
                'op': 'unsubscribe',
                'args': args
            }))
            self.subscriptions['public'].clear()
        
        # 取消私有频道订阅
        if self.subscriptions['private'] and self.private_ws:
            args = [json.loads(sub) for sub in self.subscriptions['private']]
            await self.private_ws.send(json.dumps({
                'op': 'unsubscribe',
                'args': args
            }))
            self.subscriptions['private'].clear()
        
        # 清空回调
        for key in self.callbacks:
            self.callbacks[key].clear()
    
    async def _unsubscribe(self, channel_type: str, args: List[Dict], callback_key: str):
        """通用取消订阅方法"""
        ws = self.public_ws if channel_type == 'public' else self.private_ws
        await ws.send(json.dumps({
            'op': 'unsubscribe',
            'args': args
        }))
        
        # 移除订阅记录
        for arg in args:
            sub_str = json.dumps(arg)
            if sub_str in self.subscriptions[channel_type]:
                self.subscriptions[channel_type].remove(sub_str)
        
        # 移除回调
        callback_id = str(hash(str(args)))
        if callback_id in self.callbacks[callback_key]:
            del self.callbacks[callback_key][callback_id]


# 使用示例
async def websocket_example():
    """WebSocket使用示例"""
    
    # 创建客户端（公共频道不需要认证）
    client = OKXWebSocketClient()
    
    # 定义回调函数
    def on_ticker(data):
        print(f"收到行情数据: {data}")
    
    def on_trade(data):
        print(f"收到交易数据: {data}")
    
    try:
        # 连接
        await client.connect_public()
        
        # 订阅BTC-USDT行情和交易数据
        await client.subscribe_tickers(['BTC-USDT'], on_ticker)
        await client.subscribe_trades(['BTC-USDT'], on_trade)
        
        # 保持连接
        await asyncio.sleep(30)
        
    finally:
        await client.disconnect()


if __name__ == "__main__":
    # 运行示例
    asyncio.run(websocket_example())