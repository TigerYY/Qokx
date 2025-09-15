"""
增强版交易引擎
集成数据库持久化和动态配置管理
"""

import asyncio
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal

from ..database.connection import get_db_session
from ..database.repository import TradeRepository, PerformanceRepository
from ..config.dynamic_config import get_config_manager
from ..strategies.version_control import get_strategy_version_manager
from .realtime_trading_engine import RealtimeTradingEngine, TradingState, TradingMetrics

logger = logging.getLogger(__name__)


class EnhancedTradingEngine(RealtimeTradingEngine):
    """增强版交易引擎 - 支持数据持久化和动态配置"""
    
    def __init__(self, config, okx_client, symbol: str = "BTC-USDT"):
        super().__init__(config, okx_client, symbol)
        
        # 新增组件
        self.config_manager = get_config_manager()
        self.strategy_version_manager = get_strategy_version_manager()
        self.current_strategy_id = None
        self.current_strategy_version = None
        
        # 性能统计
        self.performance_metrics = {}
        self.last_performance_update = datetime.utcnow()
        
        # 启动配置监听
        self._setup_config_listeners()
    
    def _setup_config_listeners(self):
        """设置配置变更监听器"""
        def on_config_change(config_key: str, old_value: Any, new_value: Any):
            """配置变更回调"""
            logger.info(f"配置变更: {config_key} = {new_value}")
            
            # 根据配置类型处理变更
            if config_key.startswith('risk_'):
                self._update_risk_config(config_key, new_value)
            elif config_key.startswith('strategy_'):
                self._update_strategy_config(config_key, new_value)
        
        self.config_manager.add_change_listener(on_config_change)
    
    def _update_risk_config(self, config_key: str, new_value: Any):
        """更新风险配置"""
        try:
            if config_key == 'risk_max_position_size':
                self.risk_manager.max_position_size = float(new_value)
            elif config_key == 'risk_stop_loss':
                self.risk_manager.stop_loss_pct = float(new_value)
            elif config_key == 'risk_take_profit':
                self.risk_manager.take_profit_pct = float(new_value)
            
            logger.info(f"风险配置已更新: {config_key} = {new_value}")
        except Exception as e:
            logger.error(f"更新风险配置失败: {e}")
    
    def _update_strategy_config(self, config_key: str, new_value: Any):
        """更新策略配置"""
        try:
            if config_key == 'strategy_risk_multiplier':
                self.config.risk_multiplier = float(new_value)
            elif config_key == 'strategy_commission_rate':
                self.config.commission_rate = float(new_value)
            elif config_key == 'strategy_slippage':
                self.config.slippage = float(new_value)
            
            logger.info(f"策略配置已更新: {config_key} = {new_value}")
        except Exception as e:
            logger.error(f"更新策略配置失败: {e}")
    
    async def start_trading(self, strategy_id: str = None, strategy_version: str = None) -> bool:
        """启动交易"""
        try:
            # 获取策略信息
            if strategy_id:
                self.current_strategy_id = strategy_id
                self.current_strategy_version = strategy_version or "1.0.0"
                
                # 加载策略配置
                await self._load_strategy_config()
            
            # 启动父类交易引擎
            success = await super().start_trading()
            
            if success:
                # 记录交易会话
                await self._create_trading_session()
                
                # 启动性能监控
                asyncio.create_task(self._performance_monitoring_loop())
            
            return success
        
        except Exception as e:
            logger.error(f"启动增强交易引擎失败: {e}")
            return False
    
    async def _load_strategy_config(self):
        """加载策略配置"""
        try:
            if not self.current_strategy_id:
                return
            
            # 获取策略配置
            config_key = f"{self.current_strategy_id}_{self.current_strategy_version}"
            strategy_configs = self.config_manager.get_strategy_config(config_key)
            
            # 更新配置
            for key, value in strategy_configs.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
            
            logger.info(f"策略配置已加载: {config_key}")
        
        except Exception as e:
            logger.error(f"加载策略配置失败: {e}")
    
    async def _create_trading_session(self):
        """创建交易会话记录"""
        try:
            with get_db_session() as session:
                from ..database.models import TradingSession
                
                session_data = TradingSession(
                    session_id=str(uuid.uuid4()),
                    strategy_id=self.current_strategy_id or "unknown",
                    strategy_version=self.current_strategy_version or "1.0.0",
                    status='running',
                    start_time=datetime.utcnow(),
                    initial_capital=float(self.state.account_balance),
                    total_trades=0,
                    total_pnl=Decimal('0')
                )
                
                session.add(session_data)
                session.commit()
                
                logger.info("交易会话记录已创建")
        
        except Exception as e:
            logger.error(f"创建交易会话记录失败: {e}")
    
    async def _performance_monitoring_loop(self):
        """性能监控循环"""
        while self.state.status == "running":
            try:
                await asyncio.sleep(60)  # 每分钟更新一次
                await self._update_performance_metrics()
            except Exception as e:
                logger.error(f"性能监控失败: {e}")
                await asyncio.sleep(30)
    
    async def _update_performance_metrics(self):
        """更新性能指标"""
        try:
            if not self.current_strategy_id:
                return
            
            # 获取交易统计
            with get_db_session() as session:
                trade_repo = TradeRepository(session)
                performance_repo = PerformanceRepository(session)
                
                # 计算性能指标
                stats = trade_repo.get_trade_statistics(
                    f"{self.current_strategy_id}_{self.current_strategy_version}"
                )
                
                # 更新性能记录
                metrics_data = {
                    'strategy_id': self.current_strategy_id,
                    'strategy_version': self.current_strategy_version,
                    'date': datetime.utcnow().date(),
                    'total_return': Decimal(str(stats.get('total_pnl', 0) / 10000)),  # 假设初始资金10000
                    'daily_return': Decimal('0'),  # 需要计算
                    'sharpe_ratio': Decimal('0'),  # 需要计算
                    'max_drawdown': Decimal('0'),  # 需要计算
                    'win_rate': Decimal(str(stats.get('win_rate', 0))),
                    'profit_factor': Decimal(str(stats.get('profit_factor', 0))),
                    'total_trades': stats.get('total_trades', 0),
                    'winning_trades': stats.get('winning_trades', 0),
                    'losing_trades': stats.get('losing_trades', 0),
                    'avg_win': Decimal(str(stats.get('avg_win', 0))),
                    'avg_loss': Decimal(str(stats.get('avg_loss', 0)))
                }
                
                performance_repo.update_performance_metrics(
                    self.current_strategy_id,
                    datetime.utcnow().date(),
                    metrics_data
                )
                
                # 更新内存中的性能指标
                self.performance_metrics = stats
                self.last_performance_update = datetime.utcnow()
        
        except Exception as e:
            logger.error(f"更新性能指标失败: {e}")
    
    async def execute_trade(self, signal_data: Dict[str, Any]) -> bool:
        """执行交易（重写以支持数据持久化）"""
        try:
            # 调用父类方法执行交易
            success = await super().execute_trade(signal_data)
            
            if success and signal_data.get('action') in ['BUY', 'SELL']:
                # 记录交易到数据库
                await self._record_trade(signal_data)
            
            return success
        
        except Exception as e:
            logger.error(f"执行交易失败: {e}")
            return False
    
    async def _record_trade(self, signal_data: Dict[str, Any]):
        """记录交易到数据库"""
        try:
            with get_db_session() as session:
                trade_repo = TradeRepository(session)
                
                # 创建交易记录
                trade_data = {
                    'trade_id': str(uuid.uuid4()),
                    'strategy_id': self.current_strategy_id or "unknown",
                    'strategy_version': self.current_strategy_version or "1.0.0",
                    'symbol': self.symbol,
                    'direction': signal_data.get('action', 'BUY'),
                    'order_type': signal_data.get('order_type', 'MARKET'),
                    'price': Decimal(str(signal_data.get('price', 0))),
                    'quantity': Decimal(str(signal_data.get('quantity', 0))),
                    'amount': Decimal(str(signal_data.get('price', 0) * signal_data.get('quantity', 0))),
                    'commission': Decimal(str(signal_data.get('commission', 0))),
                    'pnl': Decimal(str(signal_data.get('pnl', 0))),
                    'status': signal_data.get('status', 'FILLED'),
                    'timestamp': datetime.utcnow()
                }
                
                trade_repo.create_trade(trade_data)
                logger.info(f"交易记录已保存: {trade_data['trade_id']}")
        
        except Exception as e:
            logger.error(f"记录交易失败: {e}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        try:
            with get_db_session() as session:
                trade_repo = TradeRepository(session)
                
                if not self.current_strategy_id:
                    return {}
                
                # 获取交易统计
                stats = trade_repo.get_trade_statistics(
                    f"{self.current_strategy_id}_{self.current_strategy_version}"
                )
                
                # 获取最新性能指标
                performance_repo = PerformanceRepository(session)
                latest_performance = performance_repo.get_latest_performance(self.current_strategy_id)
                
                summary = {
                    'strategy_id': self.current_strategy_id,
                    'strategy_version': self.current_strategy_version,
                    'trading_stats': stats,
                    'performance_metrics': latest_performance.__dict__ if latest_performance else {},
                    'last_update': self.last_performance_update.isoformat(),
                    'status': self.state.status.value if hasattr(self.state.status, 'value') else str(self.state.status)
                }
                
                return summary
        
        except Exception as e:
            logger.error(f"获取性能摘要失败: {e}")
            return {}
    
    async def stop_trading(self) -> bool:
        """停止交易"""
        try:
            # 停止父类交易引擎
            success = await super().stop_trading()
            
            if success:
                # 更新交易会话状态
                await self._update_trading_session_status('stopped')
                
                # 最终性能更新
                await self._update_performance_metrics()
            
            return success
        
        except Exception as e:
            logger.error(f"停止交易失败: {e}")
            return False
    
    async def _update_trading_session_status(self, status: str):
        """更新交易会话状态"""
        try:
            with get_db_session() as session:
                from ..database.models import TradingSession
                
                # 更新会话状态
                session.query(TradingSession).filter(
                    TradingSession.strategy_id == self.current_strategy_id,
                    TradingSession.status == 'running'
                ).update({
                    'status': status,
                    'end_time': datetime.utcnow(),
                    'final_capital': float(self.state.account_balance),
                    'total_pnl': Decimal(str(self.performance_metrics.get('total_pnl', 0))),
                    'total_trades': self.performance_metrics.get('total_trades', 0)
                })
                
                session.commit()
                logger.info(f"交易会话状态已更新: {status}")
        
        except Exception as e:
            logger.error(f"更新交易会话状态失败: {e}")


# 导入uuid模块
import uuid
