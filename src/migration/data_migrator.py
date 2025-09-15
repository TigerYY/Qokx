"""
数据迁移工具
将现有内存数据迁移到新的数据库系统
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from decimal import Decimal
import uuid

from ..database.connection import init_database, get_db_session
from ..database.repository import (
    TradeRepository, StrategyRepository, ConfigRepository, 
    PerformanceRepository, SystemConfig
)
from ..config.dynamic_config import get_config_manager

logger = logging.getLogger(__name__)


class DataMigrator:
    """数据迁移器"""
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self.migration_log = []
    
    def migrate_all_data(self, session_data: Dict[str, Any]) -> bool:
        """迁移所有数据"""
        try:
            logger.info("开始数据迁移...")
            
            # 初始化数据库
            init_database()
            
            # 迁移策略配置
            self._migrate_strategy_configs(session_data)
            
            # 迁移交易数据
            self._migrate_trade_data(session_data)
            
            # 迁移性能数据
            self._migrate_performance_data(session_data)
            
            # 迁移系统配置
            self._migrate_system_configs(session_data)
            
            logger.info("数据迁移完成")
            return True
        
        except Exception as e:
            logger.error(f"数据迁移失败: {e}")
            return False
    
    def _migrate_strategy_configs(self, session_data: Dict[str, Any]):
        """迁移策略配置"""
        try:
            logger.info("迁移策略配置...")
            
            with get_db_session() as session:
                strategy_repo = StrategyRepository(session)
                config_repo = ConfigRepository(session)
                
                # 创建默认策略版本
                default_strategy_id = "signal_fusion_strategy"
                default_version = "1.0.0"
                
                # 检查是否已存在
                existing = strategy_repo.get_strategy_version(default_strategy_id, default_version)
                if existing:
                    logger.info("默认策略版本已存在，跳过创建")
                    return
                
                # 创建策略版本
                strategy_data = {
                    'strategy_id': default_strategy_id,
                    'version': default_version,
                    'name': '信号融合策略',
                    'description': '基于多时间框架信号融合的交易策略',
                    'class_path': 'src.strategies.signal_fusion_engine.SignalFusionEngine',
                    'config': {
                        'name': '信号融合策略',
                        'version': default_version,
                        'description': '基于多时间框架信号融合的交易策略'
                    },
                    'is_active': True,
                    'is_testing': False
                }
                
                strategy_repo.create_strategy_version(strategy_data)
                
                # 迁移风险配置
                risk_limits = session_data.get('risk_limits', {})
                for key, value in risk_limits.items():
                    config_repo.set_strategy_config(
                        strategy_id=f"{default_strategy_id}_{default_version}",
                        config_key=key,
                        config_value=value,
                        config_type='risk'
                    )
                
                # 迁移策略配置
                strategy_configs = {
                    'max_position_size': risk_limits.get('max_position_size', 0.2),
                    'risk_multiplier': session_data.get('risk_ratio', 1.0),
                    'commission_rate': 0.001,
                    'slippage': 0.0005,
                    'timeframes': ['1m', '5m', '15m', '1h', '4h', '1d']
                }
                
                for key, value in strategy_configs.items():
                    config_repo.set_strategy_config(
                        strategy_id=f"{default_strategy_id}_{default_version}",
                        config_key=key,
                        config_value=value,
                        config_type='strategy'
                    )
                
                logger.info("策略配置迁移完成")
        
        except Exception as e:
            logger.error(f"迁移策略配置失败: {e}")
            raise
    
    def _migrate_trade_data(self, session_data: Dict[str, Any]):
        """迁移交易数据"""
        try:
            logger.info("迁移交易数据...")
            
            trades = session_data.get('trades', [])
            if not trades:
                logger.info("没有交易数据需要迁移")
                return
            
            with get_db_session() as session:
                trade_repo = TradeRepository(session)
                
                migrated_count = 0
                for trade_data in trades:
                    try:
                        # 转换交易数据格式
                        trade_record = {
                            'trade_id': str(uuid.uuid4()),
                            'strategy_id': 'signal_fusion_strategy',
                            'strategy_version': '1.0.0',
                            'symbol': 'BTC-USDT',
                            'direction': trade_data.get('direction', 'BUY'),
                            'order_type': 'MARKET',
                            'price': Decimal(str(trade_data.get('price', 0))),
                            'quantity': Decimal(str(trade_data.get('quantity', 0))),
                            'amount': Decimal(str(trade_data.get('price', 0) * trade_data.get('quantity', 0))),
                            'commission': Decimal('0'),
                            'pnl': Decimal(str(trade_data.get('pnl', 0))),
                            'status': trade_data.get('status', 'FILLED'),
                            'timestamp': trade_data.get('timestamp', datetime.utcnow()),
                            'created_at': datetime.utcnow(),
                            'updated_at': datetime.utcnow()
                        }
                        
                        trade_repo.create_trade(trade_record)
                        migrated_count += 1
                    
                    except Exception as e:
                        logger.warning(f"迁移交易记录失败: {e}")
                        continue
                
                logger.info(f"交易数据迁移完成，共迁移 {migrated_count} 条记录")
        
        except Exception as e:
            logger.error(f"迁移交易数据失败: {e}")
            raise
    
    def _migrate_performance_data(self, session_data: Dict[str, Any]):
        """迁移性能数据"""
        try:
            logger.info("迁移性能数据...")
            
            equity_curve = session_data.get('equity_curve', [])
            if not equity_curve:
                logger.info("没有性能数据需要迁移")
                return
            
            with get_db_session() as session:
                performance_repo = PerformanceRepository(session)
                
                # 计算性能指标
                if len(equity_curve) < 2:
                    logger.info("权益曲线数据不足，跳过性能数据迁移")
                    return
                
                # 按日期分组计算日收益率
                daily_returns = {}
                for timestamp, equity in equity_curve:
                    date = timestamp.date()
                    if date not in daily_returns:
                        daily_returns[date] = []
                    daily_returns[date].append(equity)
                
                # 计算每日性能指标
                for date, equities in daily_returns.items():
                    if len(equities) < 2:
                        continue
                    
                    # 计算日收益率
                    daily_return = (equities[-1] - equities[0]) / equities[0] if equities[0] != 0 else 0
                    
                    # 计算总收益率
                    initial_equity = equity_curve[0][1] if equity_curve else 10000
                    total_return = (equities[-1] - initial_equity) / initial_equity if initial_equity != 0 else 0
                    
                    # 计算最大回撤
                    max_drawdown = self._calculate_max_drawdown(equities)
                    
                    # 计算夏普比率（简化版）
                    returns = [(equities[i] - equities[i-1]) / equities[i-1] 
                             for i in range(1, len(equities)) if equities[i-1] != 0]
                    sharpe_ratio = 0
                    if returns:
                        avg_return = sum(returns) / len(returns)
                        std_return = (sum((r - avg_return)**2 for r in returns) / len(returns))**0.5
                        sharpe_ratio = avg_return / std_return if std_return != 0 else 0
                    
                    # 创建性能记录
                    metrics_data = {
                        'strategy_id': 'signal_fusion_strategy',
                        'strategy_version': '1.0.0',
                        'date': datetime.combine(date, datetime.min.time()),
                        'total_return': Decimal(str(total_return)),
                        'daily_return': Decimal(str(daily_return)),
                        'sharpe_ratio': Decimal(str(sharpe_ratio)),
                        'max_drawdown': Decimal(str(max_drawdown)),
                        'win_rate': Decimal('0'),  # 需要从交易数据计算
                        'profit_factor': Decimal('0'),  # 需要从交易数据计算
                        'total_trades': 0,  # 需要从交易数据计算
                        'winning_trades': 0,
                        'losing_trades': 0,
                        'avg_win': Decimal('0'),
                        'avg_loss': Decimal('0')
                    }
                    
                    performance_repo.create_performance_metrics(metrics_data)
                
                logger.info("性能数据迁移完成")
        
        except Exception as e:
            logger.error(f"迁移性能数据失败: {e}")
            raise
    
    def _migrate_system_configs(self, session_data: Dict[str, Any]):
        """迁移系统配置"""
        try:
            logger.info("迁移系统配置...")
            
            with get_db_session() as session:
                config_repo = ConfigRepository(session)
                
                # 迁移系统配置
                system_configs = {
                    'default_symbol': session_data.get('trading_symbol', 'BTC-USDT'),
                    'default_timeframe': session_data.get('current_timeframe', '1H'),
                    'api_connected': session_data.get('api_connected', False),
                    'trading_status': session_data.get('trading_status', 'stopped'),
                    'risk_level': session_data.get('risk_level', 'medium')
                }
                
                for key, value in system_configs.items():
                    config_repo.set_system_config(
                        config_key=key,
                        config_value=value,
                        config_type='system'
                    )
                
                logger.info("系统配置迁移完成")
        
        except Exception as e:
            logger.error(f"迁移系统配置失败: {e}")
            raise
    
    def _calculate_max_drawdown(self, equities: List[float]) -> float:
        """计算最大回撤"""
        if not equities:
            return 0.0
        
        max_drawdown = 0.0
        peak = equities[0]
        
        for equity in equities:
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak if peak != 0 else 0
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return max_drawdown
    
    def create_migration_report(self) -> Dict[str, Any]:
        """创建迁移报告"""
        return {
            'migration_time': datetime.utcnow().isoformat(),
            'migration_log': self.migration_log,
            'status': 'completed'
        }


def migrate_session_data(session_data: Dict[str, Any]) -> bool:
    """迁移会话数据到数据库"""
    migrator = DataMigrator()
    return migrator.migrate_all_data(session_data)


def create_default_strategy_configs() -> bool:
    """创建默认策略配置"""
    try:
        config_manager = get_config_manager()
        
        # 默认策略配置
        default_configs = {
            'signal_fusion_strategy_1.0.0': {
                'name': '信号融合策略',
                'version': '1.0.0',
                'description': '基于多时间框架信号融合的交易策略',
                'max_position_size': 0.2,
                'risk_multiplier': 1.0,
                'commission_rate': 0.001,
                'slippage': 0.0005,
                'timeframes': ['1m', '5m', '15m', '1h', '4h', '1d'],
                'fusion_weights': {
                    'trend': 0.4,
                    'mean_reversion': 0.3,
                    'breakout': 0.3
                }
            }
        }
        
        for strategy_id, config in default_configs.items():
            for key, value in config.items():
                config_manager.set_strategy_config(
                    strategy_id=strategy_id,
                    config_key=key,
                    config_value=value,
                    config_type='strategy'
                )
        
        logger.info("默认策略配置创建完成")
        return True
    
    except Exception as e:
        logger.error(f"创建默认策略配置失败: {e}")
        return False
