#!/usr/bin/env python3
"""
测试OKX API连接和价格数据获取
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.okx_public_client import get_public_client

async def test_okx_api():
    """测试OKX API连接"""
    print("🚀 开始测试OKX API连接...")
    
    try:
        client = get_public_client()
        
        # 测试获取BTC-USDT价格
        print("\n📊 获取BTC-USDT实时价格...")
        ticker = await client.get_ticker("BTC-USDT")
        if ticker:
            print(f"✅ 当前价格: ${float(ticker.get('last', 0)):,.2f}")
            print(f"📈 24h变化: {float(ticker.get('chgPct', 0)) * 100:.2f}%")
            print(f"📊 24h成交量: {float(ticker.get('vol24h', 0)):,.2f} BTC")
        else:
            print("❌ 获取价格数据失败")
        
        # 测试获取K线数据
        print("\n📈 获取BTC-USDT K线数据...")
        candles = await client.get_candles("BTC-USDT", "1H", 5)
        if candles:
            print(f"✅ 获取到 {len(candles)} 条K线数据")
            for i, candle in enumerate(candles[-3:]):  # 显示最近3条
                timestamp = int(candle[0])
                open_price = float(candle[1])
                high_price = float(candle[2])
                low_price = float(candle[3])
                close_price = float(candle[4])
                volume = float(candle[5])
                
                from datetime import datetime
                time_str = datetime.fromtimestamp(timestamp / 1000).strftime("%H:%M")
                print(f"  {time_str}: 开盘${open_price:,.2f} 最高${high_price:,.2f} 最低${low_price:,.2f} 收盘${close_price:,.2f} 成交量{volume:,.2f}")
        else:
            print("❌ 获取K线数据失败")
        
        # 测试获取交易对信息
        print("\n🔍 获取交易对信息...")
        instruments = await client.get_instruments("SPOT")
        btc_pairs = [inst for inst in instruments if "BTC" in inst.get("instId", "")]
        print(f"✅ 找到 {len(btc_pairs)} 个BTC相关交易对")
        for pair in btc_pairs[:5]:  # 显示前5个
            print(f"  - {pair.get('instId')}: {pair.get('baseCcy')}/{pair.get('quoteCcy')}")
        
        print("\n🎉 OKX API测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_okx_api())

