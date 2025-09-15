#!/usr/bin/env python3
"""
测试真实OKX数据连接
"""

import os
import asyncio
import pandas as pd
from dotenv import load_dotenv
from src.utils.okx_rest_client import OKXRESTClient

# 加载环境变量
load_dotenv()

async def test_okx_connection():
    """测试OKX API连接"""
    try:
        # 获取API配置
        api_key = os.getenv('OKX_API_KEY')
        secret_key = os.getenv('OKX_SECRET_KEY')
        passphrase = os.getenv('OKX_PASSPHRASE')
        testnet = os.getenv('OKX_TESTNET', 'true').lower() == 'true'
        
        print("🔌 测试OKX API连接...")
        print(f"API Key: {api_key[:10]}...")
        print(f"测试网模式: {testnet}")
        
        if not all([api_key, secret_key, passphrase]):
            print("❌ API配置不完整，请检查.env文件")
            return False
        
        # 创建客户端
        client = OKXRESTClient(
            api_key=api_key,
            secret_key=secret_key,
            passphrase=passphrase,
            testnet=testnet
        )
        
        print("✅ OKX客户端创建成功")
        
        # 测试获取交易对信息
        print("\n📊 获取交易对信息...")
        instruments = await client.get_instruments('SPOT')
        btc_instruments = [inst for inst in instruments if inst.get('instId') == 'BTC-USDT']
        
        if btc_instruments:
            print(f"✅ 找到BTC-USDT交易对: {btc_instruments[0]}")
        else:
            print("❌ 未找到BTC-USDT交易对")
            return False
        
        # 测试获取K线数据
        print("\n📈 获取K线数据...")
        candles = await client.get_candles('BTC-USDT', '1H', 10)
        
        if candles:
            print(f"✅ 获取到 {len(candles)} 条K线数据")
            # 显示最新的一条K线
            latest_candle = candles[-1]
            print(f"最新K线: 时间={pd.to_datetime(int(latest_candle[0])/1000, unit='s')}, "
                  f"开盘={latest_candle[1]}, 最高={latest_candle[2]}, "
                  f"最低={latest_candle[3]}, 收盘={latest_candle[4]}, "
                  f"成交量={latest_candle[5]}")
        else:
            print("❌ 获取K线数据失败")
            return False
        
        # 测试获取实时价格
        print("\n💰 获取实时价格...")
        ticker = await client.get_ticker('BTC-USDT')
        
        if ticker:
            print(f"✅ 实时价格: {ticker}")
            if 'last' in ticker:
                print(f"当前价格: {ticker['last']} USDT")
        else:
            print("❌ 获取实时价格失败")
            return False
        
        print("\n🎉 所有测试通过！OKX API连接正常")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_okx_connection())
    
    if result:
        print("\n🚀 现在您可以运行Streamlit应用来查看真实市场数据了！")
        print("运行命令: source venv/bin/activate && streamlit run app.py")
    else:
        print("\n⚠️  API连接测试失败，请检查:")
        print("1. API密钥是否正确")
        print("2. 网络连接是否正常") 
        print("3. OKX API服务状态")
        print("4. .env文件配置")