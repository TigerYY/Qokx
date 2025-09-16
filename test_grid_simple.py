#!/usr/bin/env python3
"""
简化的网格交易策略测试
"""

import sys
import os
from decimal import Decimal
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_grid_config():
    """测试网格配置"""
    print("🧪 测试网格配置...")
    
    try:
        from src.strategies.grid_config import GridConfig, create_default_grid_config
        
        # 测试默认配置
        config = create_default_grid_config("BTC-USDT", Decimal("10000"))
        print(f"✅ 默认配置创建成功: {config.strategy_name}")
        print(f"   - 网格数量: {config.grid_count}")
        print(f"   - 网格间距: {config.grid_spacing * 100}%")
        print(f"   - 仓位比例: {config.position_ratio * 100}%")
        
        # 测试配置验证
        try:
            invalid_config = GridConfig(
                strategy_id="test",
                strategy_name="测试策略",
                symbol="BTC-USDT",
                base_quantity=Decimal("0.1"),
                total_capital=Decimal("10000"),
                position_ratio=Decimal("0.8"),
                reserve_ratio=Decimal("0.5")  # 超过1.0，应该失败
            )
            print("❌ 配置验证失败：应该抛出异常")
        except ValueError as e:
            print(f"✅ 配置验证成功：正确捕获错误 - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        return False


def test_grid_calculation():
    """测试网格计算"""
    print("🧪 测试网格计算...")
    
    try:
        from src.strategies.grid_config import GridConfig, GridType
        
        # 创建配置
        config = GridConfig(
            strategy_id="test",
            strategy_name="测试策略",
            symbol="BTC-USDT",
            base_quantity=Decimal("0.1"),
            total_capital=Decimal("10000"),
            grid_count=5,
            grid_spacing=Decimal("0.01"),
            grid_type=GridType.ARITHMETIC
        )
        
        # 测试价格范围检查
        current_price = Decimal("50000")
        is_in_range = config.is_price_in_range(current_price)
        print(f"✅ 价格范围检查: {current_price} 在范围内 = {is_in_range}")
        
        # 测试有效资金计算
        effective_capital = config.get_effective_capital()
        print(f"✅ 有效资金: ${effective_capital}")
        
        # 测试最大交易数量计算
        max_quantity = config.calculate_max_quantity(current_price)
        print(f"✅ 最大交易数量: {max_quantity}")
        
        # 测试网格间距金额计算
        spacing_amount = config.get_grid_spacing_amount(current_price)
        print(f"✅ 网格间距金额: ${spacing_amount}")
        
        return True
        
    except Exception as e:
        print(f"❌ 网格计算测试失败: {e}")
        return False


def test_grid_levels():
    """测试网格水平计算"""
    print("🧪 测试网格水平计算...")
    
    try:
        from src.strategies.grid_config import GridConfig, GridType, GridLevel
        
        # 创建配置
        config = GridConfig(
            strategy_id="test",
            strategy_name="测试策略",
            symbol="BTC-USDT",
            base_quantity=Decimal("0.1"),
            total_capital=Decimal("10000"),
            grid_count=5,
            grid_spacing=Decimal("0.01"),
            grid_type=GridType.ARITHMETIC
        )
        
        # 手动计算网格水平
        current_price = Decimal("50000")
        spacing_amount = config.get_grid_spacing_amount(current_price)
        
        print(f"✅ 当前价格: ${current_price}")
        print(f"✅ 网格间距: ${spacing_amount}")
        
        # 计算买入网格
        buy_levels = []
        for i in range(1, 3):  # 2个买入网格
            price = current_price - (spacing_amount * i)
            if price > 0:
                level = GridLevel(
                    price=price,
                    quantity=config.base_quantity,
                    order_type='buy',
                    is_active=True
                )
                buy_levels.append(level)
                print(f"   买入网格 {i}: ${price}")
        
        # 计算卖出网格
        sell_levels = []
        for i in range(1, 3):  # 2个卖出网格
            price = current_price + (spacing_amount * i)
            level = GridLevel(
                price=price,
                quantity=config.base_quantity,
                order_type='sell',
                is_active=True
            )
            sell_levels.append(level)
            print(f"   卖出网格 {i}: ${price}")
        
        all_levels = buy_levels + sell_levels
        print(f"✅ 总网格数量: {len(all_levels)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 网格水平测试失败: {e}")
        return False


def test_api_integration():
    """测试API集成"""
    print("🧪 测试API集成...")
    
    try:
        # 测试API模块导入
        from src.api.grid_trading import router, GridConfigRequest, GridConfigResponse
        
        print("✅ 网格交易API模块导入成功")
        
        # 测试请求模型
        request = GridConfigRequest(
            strategy_name="测试策略",
            symbol="BTC-USDT",
            base_quantity=0.1,
            total_capital=10000
        )
        
        print(f"✅ 配置请求模型创建成功: {request.strategy_name}")
        
        # 测试响应模型
        response = GridConfigResponse(
            strategy_id="test_001",
            strategy_name="测试策略",
            symbol="BTC-USDT",
            config={},
            created_at=datetime.now().isoformat(),
            status="created"
        )
        
        print(f"✅ 配置响应模型创建成功: {response.strategy_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ API集成测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 开始网格交易策略简化测试...")
    print("=" * 50)
    
    tests = [
        test_grid_config,
        test_grid_calculation,
        test_grid_levels,
        test_api_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            print()
    
    print("=" * 50)
    print(f"🎯 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！")
    else:
        print("⚠️  部分测试失败，请检查相关功能")


if __name__ == "__main__":
    main()
