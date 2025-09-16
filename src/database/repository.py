"""
数据访问层 - Repository模式实现
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from sqlalchemy.exc import SQLAlchemyError

from .models import (
    Trade, StrategyVersion, StrategyConfig, PerformanceMetrics, 
    SystemConfig, RiskEvent, ABTest, TradingSession
)

logger = logging.getLogger(__name__)


class BaseRepository:
    """基础Repository类"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def _handle_exception(self, e: Exception, operation: str):
        """统一异常处理"""
        logger.error(f"{operation}失败: {e}")
        raise e


class TradeRepository(BaseRepository):
    """交易记录Repository"""
    
    def create_trade(self, trade_data: Dict[str, Any]) -> Trade:
        """创建交易记录"""
        try:
            trade = Trade(**trade_data)
            self.session.add(trade)
            self.session.flush()  # 获取ID但不提交
            return trade
        except SQLAlchemyError as e:
            self._handle_exception(e, "创建交易记录")
    
    def get_trade_by_id(self, trade_id: str) -> Optional[Trade]:
        """根据交易ID获取交易记录"""
        try:
            return self.session.query(Trade).filter(Trade.trade_id == trade_id).first()
        except SQLAlchemyError as e:
            self._handle_exception(e, "获取交易记录")
    
    def get_trades_by_strategy(self, strategy_id: str, limit: int = 100, 
                              offset: int = 0) -> List[Trade]:
        """获取策略的交易记录"""
        try:
            return (self.session.query(Trade)
                    .filter(Trade.strategy_id == strategy_id)
                    .order_by(desc(Trade.timestamp))
                    .offset(offset)
                    .limit(limit)
                    .all())
        except SQLAlchemyError as e:
            self._handle_exception(e, "获取策略交易记录")
    
    def get_trades_by_symbol(self, symbol: str, start_date: datetime = None, 
                           end_date: datetime = None, limit: int = 100) -> List[Trade]:
        """获取交易对的交易记录"""
        try:
            query = self.session.query(Trade).filter(Trade.symbol == symbol)
            
            if start_date:
                query = query.filter(Trade.timestamp >= start_date)
            if end_date:
                query = query.filter(Trade.timestamp <= end_date)
            
            return (query.order_by(desc(Trade.timestamp))
                    .limit(limit)
                    .all())
        except SQLAlchemyError as e:
            self._handle_exception(e, "获取交易对交易记录")
    
    def get_trades_by_date_range(self, start_date: datetime, end_date: datetime, 
                                strategy_id: str = None) -> List[Trade]:
        """获取日期范围内的交易记录"""
        try:
            query = self.session.query(Trade).filter(
                and_(Trade.timestamp >= start_date, Trade.timestamp <= end_date)
            )
            
            if strategy_id:
                query = query.filter(Trade.strategy_id == strategy_id)
            
            return query.order_by(desc(Trade.timestamp)).all()
        except SQLAlchemyError as e:
            self._handle_exception(e, "获取日期范围交易记录")
    
    def update_trade_status(self, trade_id: str, status: str, pnl: Decimal = None) -> bool:
        """更新交易状态"""
        try:
            trade = self.get_trade_by_id(trade_id)
            if trade:
                trade.status = status
                if pnl is not None:
                    trade.pnl = pnl
                trade.updated_at = datetime.utcnow()
                return True
            return False
        except SQLAlchemyError as e:
            self._handle_exception(e, "更新交易状态")
    
    def get_trade_statistics(self, strategy_id: str, start_date: datetime = None, 
                           end_date: datetime = None) -> Dict[str, Any]:
        """获取交易统计信息"""
        try:
            query = self.session.query(Trade).filter(Trade.strategy_id == strategy_id)
            
            if start_date:
                query = query.filter(Trade.timestamp >= start_date)
            if end_date:
                query = query.filter(Trade.timestamp <= end_date)
            
            # 基础统计
            total_trades = query.count()
            total_pnl = query.with_entities(func.sum(Trade.pnl)).scalar() or Decimal('0')
            total_volume = query.with_entities(func.sum(Trade.amount)).scalar() or Decimal('0')
            
            # 盈利/亏损统计
            winning_trades = query.filter(Trade.pnl > 0).count()
            losing_trades = query.filter(Trade.pnl < 0).count()
            
            # 平均统计
            avg_win = query.filter(Trade.pnl > 0).with_entities(func.avg(Trade.pnl)).scalar() or Decimal('0')
            avg_loss = query.filter(Trade.pnl < 0).with_entities(func.avg(Trade.pnl)).scalar() or Decimal('0')
            
            return {
                'total_trades': total_trades,
                'total_pnl': float(total_pnl),
                'total_volume': float(total_volume),
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': float(winning_trades / total_trades) if total_trades > 0 else 0,
                'avg_win': float(avg_win),
                'avg_loss': float(avg_loss),
                'profit_factor': float(abs(avg_win / avg_loss)) if avg_loss != 0 else 0
            }
        except SQLAlchemyError as e:
            self._handle_exception(e, "获取交易统计")


class StrategyRepository(BaseRepository):
    """策略Repository"""
    
    def create_strategy_version(self, strategy_data: Dict[str, Any]) -> StrategyVersion:
        """创建策略版本"""
        try:
            strategy = StrategyVersion(**strategy_data)
            self.session.add(strategy)
            self.session.commit()  # 提交事务
            return strategy
        except SQLAlchemyError as e:
            self.session.rollback()  # 回滚事务
            self._handle_exception(e, "创建策略版本")
    
    def get_strategy_version(self, strategy_id: str, version: str) -> Optional[StrategyVersion]:
        """获取指定版本的策略"""
        try:
            return (self.session.query(StrategyVersion)
                    .filter(and_(StrategyVersion.strategy_id == strategy_id,
                                StrategyVersion.version == version))
                    .first())
        except SQLAlchemyError as e:
            self._handle_exception(e, "获取策略版本")
    
    def get_active_strategy(self, strategy_id: str) -> Optional[StrategyVersion]:
        """获取激活的策略版本"""
        try:
            return (self.session.query(StrategyVersion)
                    .filter(and_(StrategyVersion.strategy_id == strategy_id,
                                StrategyVersion.is_active == True))
                    .first())
        except SQLAlchemyError as e:
            self._handle_exception(e, "获取激活策略")
    
    def get_all_strategies(self) -> List[StrategyVersion]:
        """获取所有策略"""
        try:
            return (self.session.query(StrategyVersion)
                    .order_by(desc(StrategyVersion.created_at))
                    .all())
        except SQLAlchemyError as e:
            self._handle_exception(e, "获取所有策略")
    
    def activate_strategy_version(self, strategy_id: str, version: str) -> bool:
        """激活策略版本"""
        try:
            # 先停用所有版本
            self.session.query(StrategyVersion).filter(
                StrategyVersion.strategy_id == strategy_id
            ).update({'is_active': False})
            
            # 激活指定版本
            result = (self.session.query(StrategyVersion)
                     .filter(and_(StrategyVersion.strategy_id == strategy_id,
                                 StrategyVersion.version == version))
                     .update({'is_active': True}))
            
            self.session.commit()  # 提交事务
            return result > 0
        except SQLAlchemyError as e:
            self.session.rollback()  # 回滚事务
            self._handle_exception(e, "激活策略版本")
    
    def deactivate_strategy(self, strategy_id: str) -> bool:
        """停用策略"""
        try:
            result = (self.session.query(StrategyVersion)
                     .filter(StrategyVersion.strategy_id == strategy_id)
                     .update({'is_active': False}))
            return result > 0
        except SQLAlchemyError as e:
            self._handle_exception(e, "停用策略")
    
    def get_strategy_versions(self, strategy_id: str) -> List[StrategyVersion]:
        """获取策略的所有版本"""
        try:
            return (self.session.query(StrategyVersion)
                    .filter(StrategyVersion.strategy_id == strategy_id)
                    .order_by(desc(StrategyVersion.created_at))
                    .all())
        except SQLAlchemyError as e:
            self._handle_exception(e, "获取策略版本列表")


class ConfigRepository(BaseRepository):
    """配置Repository"""
    
    def get_strategy_config(self, strategy_id: str, config_key: str) -> Optional[StrategyConfig]:
        """获取策略配置"""
        try:
            return (self.session.query(StrategyConfig)
                    .filter(and_(StrategyConfig.strategy_id == strategy_id,
                                StrategyConfig.config_key == config_key,
                                StrategyConfig.is_active == True))
                    .first())
        except SQLAlchemyError as e:
            self._handle_exception(e, "获取策略配置")
    
    def set_strategy_config(self, strategy_id: str, config_key: str, 
                          config_value: Any, config_type: str = 'strategy',
                          description: str = None) -> StrategyConfig:
        """设置策略配置"""
        try:
            # 查找现有配置
            existing_config = self.get_strategy_config(strategy_id, config_key)
            
            if existing_config:
                # 更新现有配置
                existing_config.config_value = config_value
                existing_config.updated_at = datetime.utcnow()
                if description:
                    existing_config.description = description
                return existing_config
            else:
                # 创建新配置
                config = StrategyConfig(
                    strategy_id=strategy_id,
                    config_key=config_key,
                    config_value=config_value,
                    config_type=config_type,
                    description=description
                )
                self.session.add(config)
                self.session.flush()
                return config
        except SQLAlchemyError as e:
            self._handle_exception(e, "设置策略配置")
    
    def get_all_strategy_configs(self, strategy_id: str) -> Dict[str, Any]:
        """获取策略的所有配置"""
        try:
            configs = (self.session.query(StrategyConfig)
                      .filter(and_(StrategyConfig.strategy_id == strategy_id,
                                  StrategyConfig.is_active == True))
                      .all())
            
            return {config.config_key: config.config_value for config in configs}
        except SQLAlchemyError as e:
            self._handle_exception(e, "获取策略所有配置")
    
    def delete_strategy_config(self, strategy_id: str, config_key: str) -> bool:
        """删除策略配置"""
        try:
            result = (self.session.query(StrategyConfig)
                     .filter(and_(StrategyConfig.strategy_id == strategy_id,
                                 StrategyConfig.config_key == config_key))
                     .update({'is_active': False}))
            return result > 0
        except SQLAlchemyError as e:
            self._handle_exception(e, "删除策略配置")
    
    def get_system_config(self, config_key: str) -> Optional[SystemConfig]:
        """获取系统配置"""
        try:
            return (self.session.query(SystemConfig)
                    .filter(and_(SystemConfig.config_key == config_key,
                                SystemConfig.is_active == True))
                    .first())
        except SQLAlchemyError as e:
            self._handle_exception(e, "获取系统配置")
    
    def set_system_config(self, config_key: str, config_value: Any, 
                         config_type: str = 'system', description: str = None) -> SystemConfig:
        """设置系统配置"""
        try:
            existing_config = self.get_system_config(config_key)
            
            if existing_config:
                existing_config.config_value = config_value
                existing_config.updated_at = datetime.utcnow()
                if description:
                    existing_config.description = description
                return existing_config
            else:
                config = SystemConfig(
                    config_key=config_key,
                    config_value=config_value,
                    config_type=config_type,
                    description=description
                )
                self.session.add(config)
                self.session.flush()
                return config
        except SQLAlchemyError as e:
            self._handle_exception(e, "设置系统配置")


class PerformanceRepository(BaseRepository):
    """性能指标Repository"""
    
    def create_performance_metrics(self, metrics_data: Dict[str, Any]) -> PerformanceMetrics:
        """创建性能指标记录"""
        try:
            metrics = PerformanceMetrics(**metrics_data)
            self.session.add(metrics)
            self.session.flush()
            return metrics
        except SQLAlchemyError as e:
            self._handle_exception(e, "创建性能指标")
    
    def get_latest_performance(self, strategy_id: str) -> Optional[PerformanceMetrics]:
        """获取最新性能指标"""
        try:
            return (self.session.query(PerformanceMetrics)
                    .filter(PerformanceMetrics.strategy_id == strategy_id)
                    .order_by(desc(PerformanceMetrics.date))
                    .first())
        except SQLAlchemyError as e:
            self._handle_exception(e, "获取最新性能指标")
    
    def get_performance_history(self, strategy_id: str, days: int = 30) -> List[PerformanceMetrics]:
        """获取性能历史"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            return (self.session.query(PerformanceMetrics)
                    .filter(and_(PerformanceMetrics.strategy_id == strategy_id,
                                PerformanceMetrics.date >= start_date))
                    .order_by(asc(PerformanceMetrics.date))
                    .all())
        except SQLAlchemyError as e:
            self._handle_exception(e, "获取性能历史")
    
    def update_performance_metrics(self, strategy_id: str, date: datetime, 
                                 metrics_data: Dict[str, Any]) -> PerformanceMetrics:
        """更新性能指标"""
        try:
            # 查找现有记录
            existing = (self.session.query(PerformanceMetrics)
                       .filter(and_(PerformanceMetrics.strategy_id == strategy_id,
                                   PerformanceMetrics.date == date))
                       .first())
            
            if existing:
                # 更新现有记录
                for key, value in metrics_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                return existing
            else:
                # 创建新记录
                metrics_data['strategy_id'] = strategy_id
                metrics_data['date'] = date
                return self.create_performance_metrics(metrics_data)
        except SQLAlchemyError as e:
            self._handle_exception(e, "更新性能指标")


class ABTestRepository(BaseRepository):
    """A/B测试Repository"""
    
    def create_ab_test(self, test_data: Dict[str, Any]) -> ABTest:
        """创建A/B测试"""
        try:
            ab_test = ABTest(**test_data)
            self.session.add(ab_test)
            self.session.flush()
            return ab_test
        except SQLAlchemyError as e:
            self._handle_exception(e, "创建A/B测试")
    
    def get_active_ab_tests(self) -> List[ABTest]:
        """获取活跃的A/B测试"""
        try:
            return (self.session.query(ABTest)
                    .filter(ABTest.status == 'running')
                    .all())
        except SQLAlchemyError as e:
            self._handle_exception(e, "获取活跃A/B测试")
    
    def get_ab_test_by_id(self, test_id: str) -> Optional[ABTest]:
        """根据ID获取A/B测试"""
        try:
            return self.session.query(ABTest).filter(ABTest.test_id == test_id).first()
        except SQLAlchemyError as e:
            self._handle_exception(e, "获取A/B测试")
    
    def update_ab_test_results(self, test_id: str, results: Dict[str, Any]) -> bool:
        """更新A/B测试结果"""
        try:
            result = (self.session.query(ABTest)
                     .filter(ABTest.test_id == test_id)
                     .update({'results': results, 'status': 'completed'}))
            return result > 0
        except SQLAlchemyError as e:
            self._handle_exception(e, "更新A/B测试结果")
