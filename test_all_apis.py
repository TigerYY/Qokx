#!/usr/bin/env python3
"""
测试所有API接口
"""
import asyncio
import aiohttp
import json
from datetime import datetime

async def test_api_endpoint(session, url, name):
    """测试单个API端点"""
    try:
        print(f"\n🔍 测试 {name}...")
        print(f"URL: {url}")
        
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ {name} 成功")
                print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
                return True
            else:
                print(f"❌ {name} 失败 - HTTP {response.status}")
                return False
    except Exception as e:
        print(f"❌ {name} 错误: {e}")
        return False

async def test_all_apis():
    """测试所有API接口"""
    print("🚀 开始测试所有API接口...")
    
    # API端点列表
    endpoints = [
        ("http://localhost:8000/health", "健康检查"),
        ("http://localhost:8000/market/ticker?symbol=BTC-USDT", "实时价格"),
        ("http://localhost:8000/market/price-chart?symbol=BTC-USDT&timeframe=1H&limit=5", "价格图表"),
        ("http://localhost:8000/market/data?symbol=BTC-USDT&timeframe=1H&limit=5", "市场数据"),
        ("http://localhost:8000/api/strategies", "策略列表"),
        ("http://localhost:8000/api/trades", "交易记录"),
        ("http://localhost:8000/api/performance", "性能指标"),
    ]
    
    async with aiohttp.ClientSession() as session:
        results = []
        for url, name in endpoints:
            result = await test_api_endpoint(session, url, name)
            results.append((name, result))
    
    # 汇总结果
    print("\n" + "="*50)
    print("📊 API测试结果汇总:")
    print("="*50)
    
    success_count = 0
    for name, success in results:
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{name}: {status}")
        if success:
            success_count += 1
    
    print(f"\n总计: {success_count}/{len(results)} 个API正常")
    
    if success_count == len(results):
        print("🎉 所有API测试通过！")
    else:
        print("⚠️  部分API存在问题，请检查后端服务")

if __name__ == "__main__":
    asyncio.run(test_all_apis())
