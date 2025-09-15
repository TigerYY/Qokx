"""\nOKX公共API客户端 - 无需API密钥，获取公开市场数据\n"""

import aiohttp
import asyncio
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class OKXPublicClient:
    """OKX公共API客户端 - 无需认证"""
    
    def __init__(self, timeout: int = 30):
        """
        初始化OKX公共API客户端
        
        Args:
            timeout: 请求超时时间(秒)
        """
        self.base_url = "https://www.okx.com"
        self.timeout = timeout
        logger.info("初始化OKX公共API客户端")
    
    async def _request(self, path: str, params: Optional[Dict] = None) -> Dict:
        """
        发送HTTP请求
        
        Args:
            path: API路径
            params: 查询参数
            
        Returns:
            响应数据
        """
        url = f"{self.base_url}{path}"
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
            try:
                async with session.get(url, params=params) as response:
                    return await self._handle_response(response)
            except asyncio.TimeoutError:
                logger.error(f"请求超时: {url}")
                raise Exception("请求超时")
            except Exception as e:
                logger.error(f"请求失败: {url}, 错误: {e}")
                raise
    
    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict:
        """
        处理HTTP响应
        
        Args:
            response: HTTP响应对象
            
        Returns:
            解析后的JSON数据
        """
        try:
            data = await response.json()
            
            if response.status != 200:
                error_msg = data.get('msg', f'HTTP {response.status}')
                logger.error(f"API错误: {error_msg}")
                raise Exception(f"API请求失败: {error_msg}")
            
            if data.get('code') != '0':
                error_msg = data.get('msg', '未知错误')
                logger.error(f"OKX API错误: {error_msg}")
                raise Exception(f"OKX API错误: {error_msg}")
            
            return data
            
        except Exception as e:
            logger.error(f"响应解析失败: {e}")
            raise
    
    async def get_ticker(self, inst_id: str) -> Optional[Dict]:
        """
        获取单个产品行情信息
        
        Args:
            inst_id: 产品ID，如 BTC-USDT
            
        Returns:
            行情数据
        """
        params = {'instId': inst_id}
        response = await self._request('/api/v5/market/ticker', params)
        data = response.get('data', [])
        return data[0] if data else None
    
    async def get_candles(self, inst_id: str, bar: str = '1H', limit: int = 100) -> List[List]:
        """
        获取K线数据
        
        Args:
            inst_id: 产品ID，如 BTC-USDT
            bar: K线周期，如 1m, 5m, 15m, 30m, 1H, 2H, 4H, 6H, 12H, 1D, 1W, 1M, 3M
            limit: 返回数据条数，最大300
            
        Returns:
            K线数据列表，每个元素为 [timestamp, open, high, low, close, volume, volCcy, volCcyQuote, confirm]
        """
        params = {
            'instId': inst_id,
            'bar': bar,
            'limit': str(limit)
        }
        response = await self._request('/api/v5/market/candles', params)
        return response.get('data', [])
    
    async def get_orderbook(self, inst_id: str, depth: int = 20) -> Optional[Dict]:
        """
        获取产品深度
        
        Args:
            inst_id: 产品ID
            depth: 深度档位数量，最大400
            
        Returns:
            深度数据
        """
        params = {
            'instId': inst_id,
            'sz': str(depth)
        }
        response = await self._request('/api/v5/market/books', params)
        data = response.get('data', [])
        return data[0] if data else None
    
    async def get_trades(self, inst_id: str, limit: int = 100) -> List[Dict]:
        """
        获取成交数据
        
        Args:
            inst_id: 产品ID
            limit: 返回数据条数，最大500
            
        Returns:
            成交数据列表
        """
        params = {
            'instId': inst_id,
            'limit': str(limit)
        }
        response = await self._request('/api/v5/market/trades', params)
        return response.get('data', [])
    
    async def get_24hr_ticker(self, inst_id: str) -> Optional[Dict]:
        """
        获取24小时成交量数据
        
        Args:
            inst_id: 产品ID
            
        Returns:
            24小时数据
        """
        params = {'instId': inst_id}
        response = await self._request('/api/v5/market/ticker', params)
        data = response.get('data', [])
        return data[0] if data else None
    
    async def get_instruments(self, inst_type: str = 'SPOT') -> List[Dict]:
        """
        获取交易产品基础信息
        
        Args:
            inst_type: 产品类型，SPOT：币币
            
        Returns:
            产品信息列表
        """
        params = {'instType': inst_type}
        response = await self._request('/api/v5/public/instruments', params)
        return response.get('data', [])


# 创建全局公共客户端实例
_public_client = None

def get_public_client() -> OKXPublicClient:
    """
    获取OKX公共API客户端实例（单例模式）
    
    Returns:
        OKXPublicClient实例
    """
    global _public_client
    if _public_client is None:
        _public_client = OKXPublicClient()
    return _public_client