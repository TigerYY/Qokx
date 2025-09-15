"""
OKX API使用示例和测试
"""

import asyncio
import os
import logging
from dotenv import load_dotenv
from src.utils.okx_rest_client import OKXRESTClient
from src.utils.okx_websocket_client import OKXWebSocketClient
from src.config.api_config import get_api_config, APIConfigManager, mask_secret

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def rest_api_example():
    """REST API使用示例"""
    logger.info("开始REST API示例...")
    
    try:
        # 获取API配置
        config = get_api_config()
        logger.info(f"API配置加载成功（测试网: {config.get('testnet', False)}）")
        
        # 创建客户端
        client = OKXRESTClient(
            api_key=config['api_key'],
            secret_key=config['secret_key'],
            passphrase=config['passphrase'],
            testnet=config.get('testnet', False)
        )
        
        # 1. 获取服务器时间
        server_time = await client.get_server_time()
        logger.info(f"服务器时间: {server_time}")
        
        # 2. 获取交易产品信息
        instruments = await client.get_instruments('SPOT')
        logger.info(f"获取到 {len(instruments)} 个现货交易对")
        
        # 显示前5个交易对
        for i, inst in enumerate(instruments[:5]):
            logger.info(f"交易对 {i+1}: {inst.get('instId')} - {inst.get('instType')}")
        
        # 3. 获取BTC-USDT行情
        btc_ticker = await client.get_ticker('BTC-USDT')
        if btc_ticker:
            logger.info(f"BTC-USDT行情: 最新价={btc_ticker.get('last')} USDT")
        
        # 4. 获取K线数据
        candles = await client.get_candles('BTC-USDT', '1m', 10)
        logger.info(f"获取到 {len(candles)} 根K线数据")
        
        # 5. 获取账户余额（需要读取权限）
        try:
            balance = await client.get_account_balance()
            if balance:
                total_equity = balance[0].get('details', [{}])[0].get('eq', 'N/A')
                logger.info(f"账户总权益: {total_equity} USDT")
        except Exception as e:
            logger.warning(f"获取余额失败（可能缺少权限）: {e}")
        
        logger.info("REST API示例完成")
        
    except Exception as e:
        logger.error(f"REST API示例失败: {e}")
        raise


async def websocket_example():
    """WebSocket API使用示例"""
    logger.info("开始WebSocket示例...")
    
    try:
        # 获取API配置（WebSocket公共频道不需要认证）
        config = get_api_config()
        
        # 创建WebSocket客户端
        client = OKXWebSocketClient(
            api_key=config.get('api_key'),
            secret_key=config.get('secret_key'),
            passphrase=config.get('passphrase'),
            testnet=config.get('testnet', False)
        )
        
        # 定义回调函数
        def on_ticker(data):
            for ticker in data:
                inst_id = ticker.get('instId')
                last_price = ticker.get('last')
                logger.info(f"WS行情 - {inst_id}: {last_price}")
        
        def on_trade(data):
            for trade in data:
                inst_id = trade.get('instId')
                price = trade.get('px')
                side = trade.get('side')
                logger.info(f"WS交易 - {inst_id}: {side} @ {price}")
        
        # 连接并订阅
        await client.connect_public()
        
        # 订阅BTC-USDT和ETH-USDT的行情和交易数据
        await client.subscribe_tickers(['BTC-USDT', 'ETH-USDT'], on_ticker)
        await client.subscribe_trades(['BTC-USDT', 'ETH-USDT'], on_trade)
        
        logger.info("WebSocket连接已建立，开始接收实时数据...")
        logger.info("等待10秒接收数据...")
        
        # 接收10秒数据
        await asyncio.sleep(10)
        
        # 取消订阅并断开连接
        await client.unsubscribe_all()
        await client.disconnect()
        
        logger.info("WebSocket示例完成")
        
    except Exception as e:
        logger.error(f"WebSocket示例失败: {e}")
        raise


async def config_manager_example():
    """配置管理器使用示例"""
    logger.info("开始配置管理器示例...")
    
    try:
        # 创建配置管理器
        manager = APIConfigManager()
        
        # 示例配置数据
        test_config = {
            'api_key': 'test_api_key_123',
            'secret_key': 'test_secret_key_456',
            'passphrase': 'test_passphrase_789',
            'testnet': True
        }
        
        # 保存配置
        if manager.save_config(test_config, 'test_profile'):
            logger.info("配置保存成功")
        
        # 列出所有profile
        profiles = manager.list_profiles()
        logger.info(f"可用profile: {profiles}")
        
        # 加载配置
        loaded_config = manager.load_config('test_profile')
        if loaded_config:
            logger.info(f"配置加载成功: {mask_secret(str(loaded_config))}")
        
        # 验证配置
        is_valid = manager.validate_config('test_profile')
        logger.info(f"配置验证: {is_valid}")
        
        # 清理测试配置
        manager.delete_config('test_profile')
        logger.info("测试配置已清理")
        
    except Exception as e:
        logger.error(f"配置管理器示例失败: {e}")
        raise


async def main():
    """主函数"""
    # 加载环境变量
    load_dotenv()
    
    logger.info("=" * 50)
    logger.info("OKX API 使用示例")
    logger.info("=" * 50)
    
    try:
        # 运行配置管理器示例
        await config_manager_example()
        
        # 运行REST API示例
        await rest_api_example()
        
        # 运行WebSocket示例
        await websocket_example()
        
        logger.info("=" * 50)
        logger.info("所有示例运行完成！")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"示例运行失败: {e}")
        logger.info("请检查：")
        logger.info("1. 是否已复制 .env.example 为 .env 并填写正确的API信息")
        logger.info("2. API密钥是否具有必要的权限")
        logger.info("3. 网络连接是否正常")
        
        # 显示当前环境变量配置状态
        env_config = os.environ.get('OKX_API_KEY')
        if env_config:
            logger.info(f"环境变量OKX_API_KEY: {mask_secret(env_config)}")
        else:
            logger.info("环境变量OKX_API_KEY: 未设置")


if __name__ == "__main__":
    # 运行主函数
    asyncio.run(main())