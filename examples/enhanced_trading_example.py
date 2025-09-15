#!/usr/bin/env python3
"""
增强版交易系统使用示例
展示如何使用新的数据持久化和配置管理功能
"""

import asyncio
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入增强版组件
from src.database.connection import init_database
from src.config.dynamic_config import init_config_manager
from src.strategies.version_control import get_strategy_version_manager, get_ab_test_manager
from src.trading.enhanced_trading_engine import EnhancedTradingEngine
from src.migration.data_migrator import migrate_session_data


async def main():
    """主函数"""
    try:
        logger.info("启动增强版交易系统示例...")
        
        # 1. 初始化数据库
        logger.info("初始化数据库...")
        init_database()
        
        # 2. 初始化配置管理器
        logger.info("初始化配置管理器...")
        init_config_manager()
        
        # 3. 创建策略版本
        logger.info("创建策略版本...")
        strategy_manager = get_strategy_version_manager()
        
        # 注册示例策略
        from src.strategies.signal_fusion_engine import SignalFusionEngine
        strategy_manager.register_strategy(SignalFusionEngine, "signal_fusion_strategy")
        
        # 创建策略版本
        strategy_config = {
            'name': '信号融合策略',
            'version': '1.0.0',
            'description': '基于多时间框架信号融合的交易策略',
            'max_position_size': 0.2,
            'risk_multiplier': 1.0,
            'commission_rate': 0.001,
            'slippage': 0.0005,
            'timeframes': ['1m', '5m', '15m', '1h', '4h', '1d']
        }
        
        success = strategy_manager.create_strategy_version(
            strategy_id="signal_fusion_strategy",
            version="1.0.0",
            name="信号融合策略",
            description="基于多时间框架信号融合的交易策略",
            class_path="src.strategies.signal_fusion_engine.SignalFusionEngine",
            config=strategy_config
        )
        
        if success:
            logger.info("策略版本创建成功")
            
            # 激活策略版本
            strategy_manager.activate_strategy_version("signal_fusion_strategy", "1.0.0")
            logger.info("策略版本已激活")
        
        # 4. 创建A/B测试示例
        logger.info("创建A/B测试...")
        ab_test_manager = get_ab_test_manager()
        
        # 创建策略B版本
        strategy_b_config = strategy_config.copy()
        strategy_b_config['risk_multiplier'] = 1.5  # 不同的风险参数
        
        strategy_manager.create_strategy_version(
            strategy_id="signal_fusion_strategy",
            version="1.1.0",
            name="信号融合策略(高风险版)",
            description="基于多时间框架信号融合的交易策略(高风险版)",
            class_path="src.strategies.signal_fusion_engine.SignalFusionEngine",
            config=strategy_b_config
        )
        
        # 创建A/B测试
        test_id = ab_test_manager.create_ab_test(
            test_name="风险参数A/B测试",
            strategy_a_id="signal_fusion_strategy",
            strategy_a_version="1.0.0",
            strategy_b_id="signal_fusion_strategy", 
            strategy_b_version="1.1.0",
            traffic_split=0.5,
            duration_days=7
        )
        
        if test_id:
            logger.info(f"A/B测试已创建: {test_id}")
        
        # 5. 动态配置管理示例
        logger.info("动态配置管理示例...")
        from src.config.dynamic_config import get_config_manager
        config_manager = get_config_manager()
        
        # 设置策略配置
        config_manager.set_strategy_config(
            strategy_id="signal_fusion_strategy_1.0.0",
            config_key="max_position_size",
            config_value=0.15,  # 降低最大仓位
            config_type="strategy"
        )
        
        # 设置风险配置
        config_manager.set_strategy_config(
            strategy_id="signal_fusion_strategy_1.0.0",
            config_key="stop_loss",
            config_value=0.02,  # 2%止损
            config_type="risk"
        )
        
        logger.info("配置已更新")
        
        # 6. 获取配置
        current_config = config_manager.get_strategy_config("signal_fusion_strategy_1.0.0")
        logger.info(f"当前策略配置: {current_config}")
        
        # 7. 模拟交易数据迁移
        logger.info("模拟数据迁移...")
        sample_session_data = {
            'trades': [
                {
                    'direction': 'BUY',
                    'price': 95000.0,
                    'quantity': 0.01,
                    'pnl': 50.0,
                    'status': 'FILLED',
                    'timestamp': datetime.utcnow()
                },
                {
                    'direction': 'SELL',
                    'price': 95500.0,
                    'quantity': 0.01,
                    'pnl': 25.0,
                    'status': 'FILLED',
                    'timestamp': datetime.utcnow()
                }
            ],
            'equity_curve': [
                (datetime.utcnow(), 10000.0),
                (datetime.utcnow(), 10050.0),
                (datetime.utcnow(), 10075.0)
            ],
            'risk_limits': {
                'max_position_size': 0.2,
                'max_daily_loss': 0.05,
                'max_drawdown': 0.15,
                'stop_loss': 0.02,
                'take_profit': 0.04
            },
            'trading_symbol': 'BTC-USDT',
            'current_timeframe': '1H',
            'api_connected': True,
            'trading_status': 'stopped',
            'risk_level': 'medium'
        }
        
        # 迁移数据
        migrate_session_data(sample_session_data)
        logger.info("数据迁移完成")
        
        # 8. 查询交易数据
        logger.info("查询交易数据...")
        from src.database.repository import TradeRepository
        from src.database.connection import get_db_session
        
        with get_db_session() as session:
            trade_repo = TradeRepository(session)
            trades = trade_repo.get_trades_by_strategy("signal_fusion_strategy_1.0.0")
            logger.info(f"找到 {len(trades)} 条交易记录")
            
            for trade in trades:
                logger.info(f"交易: {trade.direction} {trade.quantity} @ {trade.price} PnL: {trade.pnl}")
        
        # 9. 性能分析
        logger.info("性能分析...")
        stats = trade_repo.get_trade_statistics("signal_fusion_strategy_1.0.0")
        logger.info(f"交易统计: {stats}")
        
        logger.info("增强版交易系统示例完成！")
        
    except Exception as e:
        logger.error(f"示例运行失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
