"""
OKX REST API客户端 - 支持现货交易和行情数据获取
"""

import hashlib
import hmac
import base64
import time
import json
from typing import Dict, List, Optional, Any
import aiohttp
import asyncio
from urllib.parse import urljoin
import logging

logger = logging.getLogger(__name__)


class OKXRESTClient:
    """OKX REST API客户端"""
    
    def __init__(self, 
                 api_key: str, 
                 secret_key: str, 
                 passphrase: str, 
                 testnet: bool = False,
                 timeout: int = 30):
        """
        初始化OKX REST客户端
        
        Args:
            api_key: OKX API密钥
            secret_key: OKX密钥密钥
            passphrase: OKX交易密码
            testnet: 是否使用测试网
            timeout: 请求超时时间(秒)
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase
        self.timeout = timeout
        
        # 设置API端点
        if testnet:
            self.base_url = "https://www.okx.com"
            logger.info("使用OKX测试网环境")
        else:
            self.base_url = "https://www.okx.com"
            logger.info("使用OKX主网环境")
    
    def _sign_request(self, method: str, path: str, body: Optional[Dict] = None) -> Dict[str, str]:
        """生成请求签名"""
        timestamp = str(round(time.time() * 1000))
        
        if body is None:
            body = {}
        
        # 构建待签名字符串
        message = timestamp + method.upper() + path
        if body:
            message += json.dumps(body, separators=(',', ':'), ensure_ascii=False)
        
        # 计算签名
        signature = base64.b64encode(
            hmac.new(
                self.secret_key.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        
        return {
            'OK-ACCESS-KEY': self.api_key,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        }
    
    async def _request(self, method: str, path: str, params: Optional[Dict] = None, 
                      data: Optional[Dict] = None) -> Dict:
        """发送HTTP请求"""
        url = urljoin(self.base_url, path)
        
        headers = {}
        if path.startswith('/api/v5/trade') or path.startswith('/api/v5/account'):
            headers = self._sign_request(method, path, data)
        
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                if method.upper() == 'GET':
                    async with session.get(url, params=params, headers=headers) as response:
                        return await self._handle_response(response)
                elif method.upper() == 'POST':
                    async with session.post(url, json=data, headers=headers) as response:
                        return await self._handle_response(response)
                else:
                    raise ValueError(f"不支持的HTTP方法: {method}")
        except asyncio.TimeoutError:
            logger.error(f"请求超时: {url}")
            raise
        except Exception as e:
            logger.error(f"请求失败: {url}, 错误: {e}")
            raise
    
    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict:
        """处理API响应"""
        try:
            text = await response.text()
            result = json.loads(text)
            
            if response.status != 200:
                logger.error(f"API错误: 状态码={response.status}, 响应={text}")
                raise Exception(f"API错误: {response.status}")
            
            if result.get('code') != '0':
                logger.warning(f"业务错误: 代码={result.get('code')}, 消息={result.get('msg')}")
                # 仍然返回结果，让调用方处理业务错误
                
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}, 响应文本: {text}")
            raise
        except Exception as e:
            logger.error(f"响应处理失败: {e}")
            raise
    
    # 公共API方法
    
    async def get_instruments(self, inst_type: str = 'SPOT') -> List[Dict]:
        """获取交易产品信息"""
        path = "/api/v5/public/instruments"
        params = {'instType': inst_type}
        result = await self._request('GET', path, params=params)
        return result.get('data', [])
    
    async def get_ticker(self, inst_id: str) -> Optional[Dict]:
        """获取单个产品行情"""
        path = "/api/v5/market/ticker"
        params = {'instId': inst_id}
        result = await self._request('GET', path, params=params)
        return result.get('data', [{}])[0] if result.get('data') else None
    
    async def get_candles(self, inst_id: str, bar: str = '1m', limit: int = 100) -> List[Dict]:
        """获取K线数据"""
        path = "/api/v5/market/candles"
        params = {
            'instId': inst_id,
            'bar': bar,
            'limit': limit
        }
        result = await self._request('GET', path, params=params)
        return result.get('data', [])
    
    async def get_orderbook(self, inst_id: str, depth: int = 20) -> Optional[Dict]:
        """获取订单簿"""
        path = "/api/v5/market/books"
        params = {
            'instId': inst_id,
            'sz': depth
        }
        result = await self._request('GET', path, params=params)
        return result.get('data', [{}])[0] if result.get('data') else None
    
    # 私有API方法
    
    async def get_account_balance(self, ccy: Optional[str] = None) -> List[Dict]:
        """获取账户余额"""
        path = "/api/v5/account/balance"
        params = {}
        if ccy:
            params['ccy'] = ccy
        result = await self._request('GET', path, params=params)
        return result.get('data', [])
    
    async def get_positions(self, inst_type: str = 'SPOT') -> List[Dict]:
        """获取持仓信息"""
        path = "/api/v5/account/positions"
        params = {'instType': inst_type}
        result = await self._request('GET', path, params=params)
        return result.get('data', [])
    
    async def place_order(self, 
                         inst_id: str, 
                         td_mode: str, 
                         side: str, 
                         ord_type: str, 
                         sz: str,
                         px: Optional[str] = None,
                         cl_ord_id: Optional[str] = None) -> Dict:
        """下单"""
        path = "/api/v5/trade/order"
        
        data = {
            'instId': inst_id,
            'tdMode': td_mode,
            'side': side,
            'ordType': ord_type,
            'sz': sz
        }
        
        if px:
            data['px'] = px
        if cl_ord_id:
            data['clOrdId'] = cl_ord_id
        
        result = await self._request('POST', path, data=data)
        return result.get('data', [{}])[0] if result.get('data') else {}
    
    async def cancel_order(self, inst_id: str, ord_id: Optional[str] = None, 
                          cl_ord_id: Optional[str] = None) -> Dict:
        """撤单"""
        path = "/api/v5/trade/cancel-order"
        
        data = {'instId': inst_id}
        if ord_id:
            data['ordId'] = ord_id
        if cl_ord_id:
            data['clOrdId'] = cl_ord_id
        
        result = await self._request('POST', path, data=data)
        return result.get('data', [{}])[0] if result.get('data') else {}
    
    async def get_order_info(self, inst_id: str, ord_id: Optional[str] = None,
                           cl_ord_id: Optional[str] = None) -> Optional[Dict]:
        """获取订单信息"""
        path = "/api/v5/trade/order"
        
        params = {'instId': inst_id}
        if ord_id:
            params['ordId'] = ord_id
        if cl_ord_id:
            params['clOrdId'] = cl_ord_id
        
        result = await self._request('GET', path, params=params)
        return result.get('data', [{}])[0] if result.get('data') else None
    
    async def get_order_history(self, inst_type: str = 'SPOT', limit: int = 100) -> List[Dict]:
        """获取订单历史"""
        path = "/api/v5/trade/orders-history"
        params = {
            'instType': inst_type,
            'limit': limit
        }
        result = await self._request('GET', path, params=params)
        return result.get('data', [])
    
    # 批量操作
    
    async def place_batch_orders(self, orders: List[Dict]) -> List[Dict]:
        """批量下单"""
        path = "/api/v5/trade/batch-orders"
        data = orders
        result = await self._request('POST', path, data=data)
        return result.get('data', [])
    
    async def cancel_batch_orders(self, orders: List[Dict]) -> List[Dict]:
        """批量撤单"""
        path = "/api/v5/trade/cancel-batch-orders"
        data = orders
        result = await self._request('POST', path, data=data)
        return result.get('data', [])
    
    # 工具方法
    
    async def get_server_time(self) -> Dict:
        """获取服务器时间"""
        path = "/api/v5/public/time"
        result = await self._request('GET', path)
        return result.get('data', [{}])[0] if result.get('data') else {}
    
    async def get_max_avail_size(self, inst_id: str, td_mode: str, ccy: Optional[str] = None) -> Dict:
        """获取最大可用数量"""
        path = "/api/v5/account/max-size"
        params = {
            'instId': inst_id,
            'tdMode': td_mode
        }
        if ccy:
            params['ccy'] = ccy
        result = await self._request('GET', path, params=params)
        return result.get('data', [{}])[0] if result.get('data') else {}


# 简化使用示例
async def create_okx_client() -> OKXRESTClient:
    """创建OKX客户端实例"""
    # 从环境变量获取配置
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_key = os.getenv('OKX_API_KEY')
    secret_key = os.getenv('OKX_SECRET_KEY')
    passphrase = os.getenv('OKX_PASSPHRASE')
    testnet = os.getenv('OKX_TESTNET', 'false').lower() == 'true'
    
    if not all([api_key, secret_key, passphrase]):
        raise ValueError("请设置OKX_API_KEY, OKX_SECRET_KEY, OKX_PASSPHRASE环境变量")
    
    return OKXRESTClient(api_key, secret_key, passphrase, testnet)