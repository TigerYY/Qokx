#!/usr/bin/env python3
"""
回测执行脚本 - 使用历史数据验证策略效果
"""

import asyncio
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.backtest.backtest_engine import BacktestEngine, BacktestResult
from src.backtest.data_loader import HistoricalDataLoader
from src.config.settings import DEFAULT_BACKTEST_CONFIG, BacktestConfig

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backtest.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


async def run_backtest(config: BacktestConfig, data_source: str = "sample") -> BacktestResult:
    """运行回测"""
    logger.info("=" * 60)
    logger.info("开始回测验证")
    logger.info("=" * 60)
    
    # 初始化数据加载器
    data_loader = HistoricalDataLoader()
    
    # 设置时间范围（默认最近3个月）
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    if config.start_date:
        start_date = config.start_date
    if config.end_date:
        end_date = config.end_date
    
    logger.info(f"时间范围: {start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}")
    logger.info(f"交易品种: {config.symbol}")
    logger.info(f"时间框架: {config.timeframes}")
    logger.info(f"初始资金: {config.initial_capital:.2f}")
    
    # 加载历史数据
    logger.info("正在加载历史数据...")
    
    if data_source == "sample":
        # 生成示例数据
        historical_data = data_loader.generate_sample_data(
            config.symbol, config.timeframes, start_date, end_date
        )
    else:
        # 从本地文件加载数据
        historical_data = await data_loader.load_data(
            config.symbol, config.timeframes, start_date, end_date, source="local"
        )
    
    # 验证数据
    if not data_loader.validate_data(historical_data):
        logger.error("数据验证失败")
        return None
    
    # 显示数据信息
    data_info = data_loader.get_data_info(historical_data)
    for timeframe, info in data_info.items():
        logger.info(f"{timeframe}: {info['num_records']} 条记录, "
                   f"价格范围: {info['price_range'][0]:.2f}-{info['price_range'][1]:.2f}")
    
    # 初始化回测引擎
    logger.info("初始化回测引擎...")
    backtest_engine = BacktestEngine(config)
    
    # 运行回测
    logger.info("开始运行回测...")
    result = await backtest_engine.run_backtest(historical_data)
    
    if result:
        logger.info("回测完成!")
        logger.info("=" * 60)
        logger.info("回测结果摘要:")
        logger.info(f"总交易次数: {result.total_trades}")
        logger.info(f"盈利交易: {result.winning_trades}")
        logger.info(f"亏损交易: {result.losing_trades}")
        logger.info(f"胜率: {result.win_rate:.2%}")
        logger.info(f"总盈亏: {result.total_pnl:.2f}")
        logger.info(f"总收益率: {result.total_return:.2f}%")
        logger.info(f"最大回撤: {result.max_drawdown:.2%}")
        logger.info(f"夏普比率: {result.sharpe_ratio:.2f}" if result.sharpe_ratio else "夏普比率: N/A")
        logger.info(f"初始资金: {result.initial_capital:.2f}")
        logger.info(f"最终资金: {result.final_capital:.2f}")
        logger.info("=" * 60)
        
        # 保存详细结果
        results_dir = project_root / "results"
        results_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = results_dir / f"backtest_result_{timestamp}.json"
        backtest_engine.save_results(result, str(result_file))
        
        logger.info(f"详细结果已保存到: {result_file}")
    
    return result


def create_backtest_config() -> BacktestConfig:
    """创建回测配置"""
    config = BacktestConfig(
        symbol="BTCUSDT",
        timeframes=["1h", "4h", "1d"],
        initial_capital=10000.0,
        risk_per_trade=0.02,
        max_position_size=0.1,
        commission_rate=0.001,
        slippage=0.0005,
        use_stop_loss=True,
        stop_loss_percent=0.02,
        take_profit_percent=0.04,
        stop_loss_atr_multiple=2.0,
        take_profit_atr_multiple=3.0,
        lookback_period=200,
        warmup_period=50,
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 12, 31)
    )
    
    return config


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="运行策略回测验证")
    parser.add_argument("--symbol", "-s", default="BTCUSDT", help="交易品种")
    parser.add_argument("--timeframes", "-t", nargs="+", default=["1h", "4h", "1d"], 
                       help="时间框架列表")
    parser.add_argument("--capital", "-c", type=float, default=10000.0, 
                       help="初始资金")
    parser.add_argument("--risk", "-r", type=float, default=0.02, 
                       help="每笔交易风险比例")
    parser.add_argument("--start-date", type=lambda s: datetime.strptime(s, '%Y-%m-%d'),
                       help="开始日期 (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=lambda s: datetime.strptime(s, '%Y-%m-%d'),
                       help="结束日期 (YYYY-MM-DD)")
    parser.add_argument("--data-source", "-d", choices=["sample", "local"], default="sample",
                       help="数据源: sample (示例数据) 或 local (本地文件)")
    parser.add_argument("--output", "-o", help="结果输出文件")
    
    args = parser.parse_args()
    
    # 创建配置
    config = BacktestConfig(
        symbol=args.symbol,
        timeframes=args.timeframes,
        initial_capital=args.capital,
        risk_per_trade=args.risk,
        start_date=args.start_date,
        end_date=args.end_date
    )
    
    try:
        # 运行回测
        result = asyncio.run(run_backtest(config, args.data_source))
        
        if result and args.output:
            # 保存结果到指定文件
            backtest_engine = BacktestEngine(config)
            backtest_engine.save_results(result, args.output)
            logger.info(f"结果已保存到: {args.output}")
        
        return 0
        
    except Exception as e:
        logger.error(f"回测执行失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    # 示例用法
    if len(sys.argv) == 1:
        # 如果没有参数，使用默认配置运行示例回测
        logger.info("使用默认配置运行示例回测...")
        
        config = create_backtest_config()
        
        # 运行回测
        result = asyncio.run(run_backtest(config, "sample"))
        
        if result:
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        sys.exit(main())