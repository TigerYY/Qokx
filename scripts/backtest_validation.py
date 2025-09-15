#!/usr/bin/env python3
"""
回测验证脚本 - 完整的策略验证流程
"""

import asyncio
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
import sys
import json

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.backtest.backtest_engine import BacktestEngine
from src.backtest.data_loader import HistoricalDataLoader
from src.backtest.result_analyzer import BacktestResultAnalyzer, analyze_backtest_result, print_summary_report
from src.config.settings import BacktestConfig

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backtest_validation.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class BacktestValidator:
    """回测验证器"""
    
    def __init__(self):
        self.data_loader = HistoricalDataLoader()
    
    async def run_complete_validation(self, config: BacktestConfig, 
                                   data_source: str = "sample") -> str:
        """运行完整的回测验证流程"""
        logger.info("=" * 80)
        logger.info("开始完整的回测验证流程")
        logger.info("=" * 80)
        
        # 1. 数据准备阶段
        logger.info("阶段 1: 数据准备")
        historical_data = await self._prepare_data(config, data_source)
        if not historical_data:
            logger.error("数据准备失败")
            return None
        
        # 2. 回测执行阶段
        logger.info("阶段 2: 回测执行")
        result = await self._run_backtest(config, historical_data)
        if not result:
            logger.error("回测执行失败")
            return None
        
        # 3. 结果分析阶段
        logger.info("阶段 3: 结果分析")
        result_file = await self._analyze_results(result, config)
        
        logger.info("=" * 80)
        logger.info("回测验证流程完成!")
        logger.info("=" * 80)
        
        return result_file
    
    async def _prepare_data(self, config: BacktestConfig, data_source: str) -> dict:
        """准备数据"""
        # 设置时间范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        if config.start_date:
            start_date = config.start_date
        if config.end_date:
            end_date = config.end_date
        
        logger.info(f"数据时间范围: {start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}")
        
        # 加载数据
        if data_source == "sample":
            logger.info("使用示例数据进行回测")
            data = self.data_loader.generate_sample_data(
                config.symbol, config.timeframes, start_date, end_date
            )
        else:
            logger.info("从本地文件加载数据")
            data = await self.data_loader.load_data(
                config.symbol, config.timeframes, start_date, end_date, source="local"
            )
        
        # 验证数据质量
        if not self.data_loader.validate_data(data):
            logger.error("数据验证失败")
            return None
        
        # 显示数据信息
        data_info = self.data_loader.get_data_info(data)
        for timeframe, info in data_info.items():
            logger.info(f"{timeframe}: {info['num_records']} 条记录, "
                       f"价格范围: {info['price_range'][0]:.2f}-{info['price_range'][1]:.2f}")
        
        return data
    
    async def _run_backtest(self, config: BacktestConfig, historical_data: dict) -> dict:
        """运行回测"""
        try:
            backtest_engine = BacktestEngine(config)
            result = await backtest_engine.run_backtest(historical_data)
            
            if result:
                # 保存原始结果
                results_dir = project_root / "results"
                results_dir.mkdir(exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                result_file = results_dir / f"backtest_raw_{timestamp}.json"
                
                backtest_engine.save_results(result, str(result_file))
                logger.info(f"原始回测结果已保存: {result_file}")
                
                # 转换为字典格式
                result_dict = {
                    'total_trades': result.total_trades,
                    'winning_trades': result.winning_trades,
                    'losing_trades': result.losing_trades,
                    'win_rate': result.win_rate,
                    'total_pnl': result.total_pnl,
                    'total_return': result.total_return,
                    'max_drawdown': result.max_drawdown,
                    'sharpe_ratio': result.sharpe_ratio,
                    'sortino_ratio': result.sortino_ratio,
                    'calmar_ratio': result.calmar_ratio,
                    'average_trade_pnl': result.average_trade_pnl,
                    'average_win': result.average_win,
                    'average_loss': result.average_loss,
                    'profit_factor': result.profit_factor,
                    'trades': [
                        {
                            'id': trade.id,
                            'symbol': trade.symbol,
                            'direction': trade.direction.name,
                            'entry_price': trade.entry_price,
                            'exit_price': trade.exit_price,
                            'entry_time': trade.entry_time.isoformat(),
                            'exit_time': trade.exit_time.isoformat() if trade.exit_time else None,
                            'quantity': trade.quantity,
                            'pnl': trade.pnl,
                            'pnl_percent': trade.pnl_percent,
                            'stop_loss': trade.stop_loss,
                            'take_profit': trade.take_profit,
                            'signal_strength': trade.signal_strength,
                            'signal_confidence': trade.signal_confidence,
                            'strategy_type': trade.strategy_type
                        }
                        for trade in result.trades
                    ],
                    'equity_curve': result.equity_curve.to_dict(),
                    'drawdown_curve': result.drawdown_curve.to_dict(),
                    'daily_returns': result.daily_returns.to_dict(),
                    'start_date': result.start_date.isoformat(),
                    'end_date': result.end_date.isoformat(),
                    'initial_capital': result.initial_capital,
                    'final_capital': result.final_capital
                }
                
                return result_dict
            
        except Exception as e:
            logger.error(f"回测执行失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    async def _analyze_results(self, result: dict, config: BacktestConfig) -> str:
        """分析结果"""
        try:
            # 保存详细结果
            results_dir = project_root / "results"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_file = results_dir / f"backtest_result_{timestamp}.json"
            
            with open(result_file, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            
            logger.info(f"详细结果已保存: {result_file}")
            
            # 生成分析报告
            analyzer = BacktestResultAnalyzer(result)
            report = analyzer.generate_summary_report()
            
            # 保存报告
            report_file = result_file.with_suffix('.report.json')
            analyzer.save_report(report, str(report_file))
            
            # 创建可视化
            plots_dir = results_dir / "plots" / timestamp
            analyzer.create_visualizations(str(plots_dir))
            
            # 打印摘要
            print_summary_report(report)
            
            # 生成HTML报告
            html_report = self._generate_html_report(result, report, config, timestamp)
            
            logger.info("=" * 80)
            logger.info("回测验证完成!")
            logger.info(f"详细结果: {result_file}")
            logger.info(f"分析报告: {report_file}")
            logger.info(f"可视化图表: {plots_dir}")
            logger.info(f"HTML报告: {html_report}")
            logger.info("=" * 80)
            
            return str(result_file)
            
        except Exception as e:
            logger.error(f"结果分析失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _generate_html_report(self, result: dict, report: dict, config: BacktestConfig, timestamp: str) -> str:
        """生成HTML报告"""
        # 这里可以实现HTML报告生成
        # 暂时返回空字符串
        return ""


def create_default_config() -> BacktestConfig:
    """创建默认配置"""
    return BacktestConfig(
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


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="运行完整的回测验证流程")
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
    parser.add_argument("--output", "-o", help="结果输出目录")
    
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
        # 运行完整的验证流程
        validator = BacktestValidator()
        result_file = asyncio.run(validator.run_complete_validation(config, args.data_source))
        
        if result_file:
            logger.info(f"回测验证成功完成!")
            logger.info(f"结果文件: {result_file}")
            return 0
        else:
            logger.error("回测验证失败")
            return 1
        
    except Exception as e:
        logger.error(f"回测验证执行失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    # 示例用法
    if len(sys.argv) == 1:
        # 如果没有参数，使用默认配置运行示例验证
        logger.info("使用默认配置运行示例回测验证...")
        
        config = create_default_config()
        validator = BacktestValidator()
        
        result_file = asyncio.run(validator.run_complete_validation(config, "sample"))
        
        if result_file:
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        sys.exit(main())