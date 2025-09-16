#!/usr/bin/env python3
"""
网格交易策略测试脚本
"""

import asyncio
import logging
from decimal import Decimal
from datetime import datetime
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.strategies.grid_config import GridConfig, create_default_grid_config, create_aggressive_grid_config, create_conservative_grid_config
from src.strategies.grid_trading_strategy import GridTradingStrategy
from src.strategies.grid_signal_generator import GridSignalGenerator
from src.execution.order_manager import global_order_manager
from src.risk.realtime_risk_manager import RealtimeRiskManager
from src.data.multi_timeframe_manager import OHLCVData

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_grid_config():
    """测试网格配置"""
    print("🧪 测试网格配置...")
    
    # 测试默认配置
    config = create_default_grid_config("BTC-USDT", Decimal("10000"))
    print(f"✅ 默认配置创建成功: {config.strategy_name}")
    print(f"   - 网格数量: {config.grid_count}")
    print(f"   - 网格间距: {config.grid_spacing * 100}%")
    print(f"   - 仓位比例: {config.position_ratio * 100}%")
    
    # 测试激进配置
    aggressive_config = create_aggressive_grid_config("BTC-USDT", Decimal("10000"))
    print(f"✅ 激进配置创建成功: {aggressive_config.strategy_name}")
    print(f"   - 网格数量: {aggressive_config.grid_count}")
    print(f"   - 网格间距: {aggressive_config.grid_spacing * 100}%")
    
    # 测试保守配置
    conservative_config = create_conservative_grid_config("BTC-USDT", Decimal("10000"))
    print(f"✅ 保守配置创建成功: {conservative_config.strategy_name}")
    print(f"   - 网格数量: {conservative_config.grid_count}")
    print(f"   - 网格间距: {conservative_config.grid_spacing * 100}%")
    
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
    
    print()


async def test_grid_strategy():
    """测试网格交易策略"""
    print("🧪 测试网格交易策略...")
    
    # 创建配置
    config = create_default_grid_config("BTC-USDT", Decimal("10000"))
    
    # 创建风险管理器
    risk_manager = RealtimeRiskManager()
    
    # 创建策略实例
    strategy = GridTradingStrategy(config, global_order_manager, risk_manager)
    
    # 初始化策略
    current_price = Decimal("50000")
    success = await strategy.initialize(current_price)
    
    if success:
        print(f"✅ 策略初始化成功，当前价格: ${current_price}")
        print(f"   - 网格数量: {len(strategy.grid_levels)}")
        
        # 显示网格水平
        print("   - 网格水平:")
        for i, level in enumerate(strategy.grid_levels[:5]):  # 只显示前5个
            print(f"     {i}: {level.order_type} @ ${level.price}")
        
        # 启动策略
        await strategy.start()
        print("✅ 策略启动成功")
        
        # 获取性能指标
        metrics = strategy.get_performance_metrics()
        print(f"✅ 性能指标获取成功:")
        print(f"   - 总交易数: {metrics['total_trades']}")
        print(f"   - 总盈亏: ${metrics['total_pnl']}")
        print(f"   - 活跃网格: {metrics['active_grids']}")
        
        # 停止策略
        await strategy.stop()
        print("✅ 策略停止成功")
        
    else:
        print("❌ 策略初始化失败")
    
    print()


async def test_signal_generator():
    """测试信号生成器"""
    print("🧪 测试信号生成器...")
    
    # 创建配置
    config = create_default_grid_config("BTC-USDT", Decimal("10000"))
    
    # 创建信号生成器
    signal_generator = GridSignalGenerator(config)
    
    # 创建模拟价格数据
    price_data = OHLCVData(
        open=[50000, 50100, 50200, 50300, 50400],
        high=[50100, 50200, 50300, 50400, 50500],
        low=[49900, 50000, 50100, 50200, 50300],
        close=[50100, 50200, 50300, 50400, 50450],
        volume=[100, 120, 110, 130, 140],
        timestamp=[datetime.now().timestamp() - 4*3600 + i*3600 for i in range(5)]
    )
    
    # 创建网格水平
    grid_levels = [
        type('GridLevel', (), {
            'price': Decimal('50000'),
            'quantity': Decimal('0.1'),
            'order_type': 'buy',
            'is_active': True,
            'filled_quantity': Decimal('0'),
            'avg_fill_price': Decimal('0')
        })(),
        type('GridLevel', (), {
            'price': Decimal('51000'),
            'quantity': Decimal('0.1'),
            'order_type': 'sell',
            'is_active': True,
            'filled_quantity': Decimal('0'),
            'avg_fill_price': Decimal('0')
        })()
    ]
    
    # 创建交易状态
    trading_state = type('GridTradingState', (), {
        'current_price': Decimal('50450'),
        'total_position': Decimal('0'),
        'total_pnl': Decimal('0'),
        'realized_pnl': Decimal('0'),
        'unrealized_pnl': Decimal('0'),
        'total_commission': Decimal('0'),
        'active_orders': 0,
        'filled_orders': 0,
        'grid_levels': grid_levels,
        'last_update_time': datetime.now().isoformat()
    })()
    
    # 生成信号
    signals = signal_generator.generate_signals(price_data, grid_levels, trading_state)
    
    print(f"✅ 信号生成成功，共生成 {len(signals)} 个信号")
    for signal in signals:
        print(f"   - {signal.signal_type}: {signal.quantity} @ ${signal.price} (置信度: {signal.confidence:.2f})")
    
    # 获取信号统计
    stats = signal_generator.get_signal_statistics()
    print(f"✅ 信号统计: {stats}")
    
    print()


async def test_grid_rebalance():
    """测试网格重新平衡"""
    print("🧪 测试网格重新平衡...")
    
    # 创建配置
    config = create_default_grid_config("BTC-USDT", Decimal("10000"))
    
    # 创建风险管理器
    risk_manager = RealtimeRiskManager()
    
    # 创建策略实例
    strategy = GridTradingStrategy(config, global_order_manager, risk_manager)
    
    # 初始化策略
    current_price = Decimal("50000")
    await strategy.initialize(current_price)
    
    print(f"✅ 初始网格中心价格: ${current_price}")
    print(f"   - 初始网格数量: {len(strategy.grid_levels)}")
    
    # 模拟价格变化
    new_price = Decimal("52000")
    success = await strategy.rebalance_grid(new_price)
    
    if success:
        print(f"✅ 网格重新平衡成功，新价格: ${new_price}")
        print(f"   - 新网格数量: {len(strategy.grid_levels)}")
        print(f"   - 新中心价格: {strategy.config.center_price}")
        
        # 显示新的网格水平
        print("   - 新网格水平:")
        for i, level in enumerate(strategy.grid_levels[:5]):  # 只显示前5个
            print(f"     {i}: {level.order_type} @ ${level.price}")
    else:
        print("❌ 网格重新平衡失败")
    
    print()


async def test_performance_analysis():
    """测试性能分析"""
    print("🧪 测试性能分析...")
    
    # 创建配置
    config = create_default_grid_config("BTC-USDT", Decimal("10000"))
    
    # 创建风险管理器
    risk_manager = RealtimeRiskManager()
    
    # 创建策略实例
    strategy = GridTradingStrategy(config, global_order_manager, risk_manager)
    
    # 初始化策略
    current_price = Decimal("50000")
    await strategy.initialize(current_price)
    
    # 模拟一些交易
    strategy.total_trades = 10
    strategy.winning_trades = 7
    strategy.losing_trades = 3
    strategy.state.total_pnl = Decimal("500")
    strategy.state.realized_pnl = Decimal("300")
    strategy.state.unrealized_pnl = Decimal("200")
    strategy.state.total_commission = Decimal("10")
    strategy.max_drawdown = Decimal("0.05")
    
    # 获取性能指标
    metrics = strategy.get_performance_metrics()
    
    print("✅ 性能分析结果:")
    print(f"   - 总交易数: {metrics['total_trades']}")
    print(f"   - 胜率: {metrics['win_rate']:.2f}%")
    print(f"   - 总盈亏: ${metrics['total_pnl']}")
    print(f"   - 已实现盈亏: ${metrics['realized_pnl']}")
    print(f"   - 未实现盈亏: ${metrics['unrealized_pnl']}")
    print(f"   - 总手续费: ${metrics['total_commission']}")
    print(f"   - 最大回撤: {metrics['max_drawdown']:.2%}")
    print(f"   - 当前持仓: {metrics['current_position']}")
    print(f"   - 活跃网格: {metrics['active_grids']}/{metrics['total_grids']}")
    
    print()


async def main():
    """主测试函数"""
    print("🚀 开始网格交易策略测试...")
    print("=" * 50)
    
    try:
        # 测试配置
        await test_grid_config()
        
        # 测试策略
        await test_grid_strategy()
        
        # 测试信号生成器
        await test_signal_generator()
        
        # 测试网格重新平衡
        await test_grid_rebalance()
        
        # 测试性能分析
        await test_performance_analysis()
        
        print("🎉 所有测试完成！")
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        print(f"❌ 测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
