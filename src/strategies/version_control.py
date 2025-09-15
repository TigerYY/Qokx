"""
策略版本控制系统
支持策略版本管理、A/B测试和回滚机制
"""

import logging
import uuid
import importlib
import inspect
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Type, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading
import asyncio
from abc import ABC, abstractmethod

from ..database.connection import get_db_session
from ..database.repository import StrategyRepository, ABTestRepository, TradeRepository, PerformanceRepository
from ..config.dynamic_config import get_config_manager

logger = logging.getLogger(__name__)


class StrategyStatus(Enum):
    """策略状态枚举"""
    DRAFT = "draft"
    TESTING = "testing"
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"


@dataclass
class StrategyInfo:
    """策略信息"""
    strategy_id: str
    name: str
    version: str
    class_path: str
    description: str
    status: StrategyStatus
    config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


@dataclass
class ABTestResult:
    """A/B测试结果"""
    test_id: str
    strategy_a_performance: Dict[str, float]
    strategy_b_performance: Dict[str, float]
    winner: str  # 'A', 'B', or 'tie'
    confidence_level: float
    statistical_significance: bool
    test_duration_days: int
    total_trades_a: int
    total_trades_b: int


class BaseStrategy(ABC):
    """策略基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.strategy_id = config.get('strategy_id', 'unknown')
        self.version = config.get('version', '1.0.0')
        self.name = config.get('name', self.__class__.__name__)
    
    @abstractmethod
    async def generate_signal(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成交易信号"""
        pass
    
    @abstractmethod
    def get_required_data(self) -> List[str]:
        """获取策略所需的数据类型"""
        pass
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证策略配置"""
        return True
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取策略性能指标"""
        return {}


class StrategyRegistry:
    """策略注册表"""
    
    def __init__(self):
        self._strategies: Dict[str, Type[BaseStrategy]] = {}
        self._strategy_instances: Dict[str, BaseStrategy] = {}
        self._lock = threading.RLock()
    
    def register_strategy(self, strategy_class: Type[BaseStrategy], 
                         strategy_id: str = None) -> str:
        """注册策略类"""
        if strategy_id is None:
            strategy_id = strategy_class.__name__
        
        with self._lock:
            self._strategies[strategy_id] = strategy_class
            logger.info(f"策略已注册: {strategy_id}")
        
        return strategy_id
    
    def get_strategy_class(self, strategy_id: str) -> Optional[Type[BaseStrategy]]:
        """获取策略类"""
        with self._lock:
            return self._strategies.get(strategy_id)
    
    def create_strategy_instance(self, strategy_id: str, config: Dict[str, Any]) -> Optional[BaseStrategy]:
        """创建策略实例"""
        strategy_class = self.get_strategy_class(strategy_id)
        if not strategy_class:
            logger.error(f"未找到策略类: {strategy_id}")
            return None
        
        try:
            instance = strategy_class(config)
            with self._lock:
                instance_key = f"{strategy_id}_{config.get('version', '1.0.0')}"
                self._strategy_instances[instance_key] = instance
            return instance
        except Exception as e:
            logger.error(f"创建策略实例失败: {e}")
            return None
    
    def get_strategy_instance(self, strategy_id: str, version: str) -> Optional[BaseStrategy]:
        """获取策略实例"""
        with self._lock:
            instance_key = f"{strategy_id}_{version}"
            return self._strategy_instances.get(instance_key)


class StrategyVersionManager:
    """策略版本管理器"""
    
    def __init__(self):
        self.registry = StrategyRegistry()
        self.config_manager = get_config_manager()
        self._lock = threading.RLock()
    
    def register_strategy(self, strategy_class: Type[BaseStrategy], 
                         strategy_id: str = None) -> str:
        """注册策略"""
        return self.registry.register_strategy(strategy_class, strategy_id)
    
    def create_strategy_version(self, strategy_id: str, version: str, 
                              name: str, description: str, 
                              class_path: str, config: Dict[str, Any]) -> bool:
        """创建策略版本"""
        try:
            with get_db_session() as session:
                strategy_repo = StrategyRepository(session)
                
                # 检查版本是否已存在
                existing = strategy_repo.get_strategy_version(strategy_id, version)
                if existing:
                    logger.warning(f"策略版本已存在: {strategy_id} v{version}")
                    return False
                
                # 创建策略版本
                strategy_data = {
                    'strategy_id': strategy_id,
                    'version': version,
                    'name': name,
                    'description': description,
                    'class_path': class_path,
                    'config': config,
                    'is_active': False,
                    'is_testing': False
                }
                
                strategy_repo.create_strategy_version(strategy_data)
                
                # 保存策略配置
                for key, value in config.items():
                    self.config_manager.set_strategy_config(
                        strategy_id=f"{strategy_id}_{version}",
                        config_key=key,
                        config_value=value,
                        config_type='strategy'
                    )
                
                logger.info(f"策略版本已创建: {strategy_id} v{version}")
                return True
        
        except Exception as e:
            logger.error(f"创建策略版本失败: {e}")
            return False
    
    def activate_strategy_version(self, strategy_id: str, version: str) -> bool:
        """激活策略版本"""
        try:
            with get_db_session() as session:
                strategy_repo = StrategyRepository(session)
                
                # 停用所有版本
                strategy_repo.deactivate_strategy(strategy_id)
                
                # 激活指定版本
                success = strategy_repo.activate_strategy_version(strategy_id, version)
                
                if success:
                    logger.info(f"策略版本已激活: {strategy_id} v{version}")
                
                return success
        
        except Exception as e:
            logger.error(f"激活策略版本失败: {e}")
            return False
    
    def deactivate_strategy(self, strategy_id: str) -> bool:
        """停用策略"""
        try:
            with get_db_session() as session:
                strategy_repo = StrategyRepository(session)
                success = strategy_repo.deactivate_strategy(strategy_id)
                
                if success:
                    logger.info(f"策略已停用: {strategy_id}")
                
                return success
        
        except Exception as e:
            logger.error(f"停用策略失败: {e}")
            return False
    
    def get_strategy_info(self, strategy_id: str, version: str = None) -> Optional[StrategyInfo]:
        """获取策略信息"""
        try:
            with get_db_session() as session:
                strategy_repo = StrategyRepository(session)
                
                if version:
                    strategy = strategy_repo.get_strategy_version(strategy_id, version)
                else:
                    strategy = strategy_repo.get_active_strategy(strategy_id)
                
                if not strategy:
                    return None
                
                return StrategyInfo(
                    strategy_id=strategy.strategy_id,
                    name=strategy.name,
                    version=strategy.version,
                    class_path=strategy.class_path,
                    description=strategy.description or "",
                    status=StrategyStatus.ACTIVE if strategy.is_active else StrategyStatus.INACTIVE,
                    config=strategy.config or {},
                    created_at=strategy.created_at,
                    updated_at=strategy.updated_at
                )
        
        except Exception as e:
            logger.error(f"获取策略信息失败: {e}")
            return None
    
    def get_all_strategies(self) -> List[StrategyInfo]:
        """获取所有策略"""
        try:
            with get_db_session() as session:
                strategy_repo = StrategyRepository(session)
                strategies = strategy_repo.get_all_strategies()
                
                return [
                    StrategyInfo(
                        strategy_id=s.strategy_id,
                        name=s.name,
                        version=s.version,
                        class_path=s.class_path,
                        description=s.description or "",
                        status=StrategyStatus.ACTIVE if s.is_active else StrategyStatus.INACTIVE,
                        config=s.config or {},
                        created_at=s.created_at,
                        updated_at=s.updated_at
                    )
                    for s in strategies
                ]
        
        except Exception as e:
            logger.error(f"获取所有策略失败: {e}")
            return []
    
    def create_strategy_instance(self, strategy_id: str, version: str = None) -> Optional[BaseStrategy]:
        """创建策略实例"""
        try:
            strategy_info = self.get_strategy_info(strategy_id, version)
            if not strategy_info:
                return None
            
            # 获取策略配置
            config = self.config_manager.get_strategy_config(f"{strategy_id}_{strategy_info.version}")
            config.update(strategy_info.config)
            config['strategy_id'] = strategy_id
            config['version'] = strategy_info.version
            config['name'] = strategy_info.name
            
            # 创建策略实例
            return self.registry.create_strategy_instance(strategy_id, config)
        
        except Exception as e:
            logger.error(f"创建策略实例失败: {e}")
            return None


class ABTestManager:
    """A/B测试管理器"""
    
    def __init__(self):
        self.version_manager = StrategyVersionManager()
        self._active_tests: Dict[str, ABTestResult] = {}
        self._lock = threading.RLock()
    
    def create_ab_test(self, test_name: str, strategy_a_id: str, strategy_a_version: str,
                      strategy_b_id: str, strategy_b_version: str, 
                      traffic_split: float = 0.5, duration_days: int = 7) -> str:
        """创建A/B测试"""
        try:
            test_id = str(uuid.uuid4())
            
            with get_db_session() as session:
                ab_test_repo = ABTestRepository(session)
                
                test_data = {
                    'test_id': test_id,
                    'test_name': test_name,
                    'strategy_a_id': strategy_a_id,
                    'strategy_a_version': strategy_a_version,
                    'strategy_b_id': strategy_b_id,
                    'strategy_b_version': strategy_b_version,
                    'traffic_split': traffic_split,
                    'start_date': datetime.utcnow(),
                    'status': 'running'
                }
                
                ab_test_repo.create_ab_test(test_data)
                
                logger.info(f"A/B测试已创建: {test_id}")
                return test_id
        
        except Exception as e:
            logger.error(f"创建A/B测试失败: {e}")
            return None
    
    def get_test_strategy(self, test_id: str, user_id: str) -> Tuple[str, str]:
        """根据用户ID获取测试策略"""
        try:
            with get_db_session() as session:
                ab_test_repo = ABTestRepository(session)
                test = ab_test_repo.get_ab_test_by_id(test_id)
                
                if not test or test.status != 'running':
                    return None, None
                
                # 简单的哈希分配
                hash_value = hash(user_id) % 100
                threshold = int(test.traffic_split * 100)
                
                if hash_value < threshold:
                    return test.strategy_a_id, test.strategy_a_version
                else:
                    return test.strategy_b_id, test.strategy_b_version
        
        except Exception as e:
            logger.error(f"获取测试策略失败: {e}")
            return None, None
    
    def analyze_ab_test(self, test_id: str) -> Optional[ABTestResult]:
        """分析A/B测试结果"""
        try:
            with get_db_session() as session:
                ab_test_repo = ABTestRepository(session)
                trade_repo = TradeRepository(session)
                performance_repo = PerformanceRepository(session)
                
                test = ab_test_repo.get_ab_test_by_id(test_id)
                if not test:
                    return None
                
                # 获取策略A的交易数据
                trades_a = trade_repo.get_trades_by_strategy(
                    f"{test.strategy_a_id}_{test.strategy_a_version}",
                    limit=10000
                )
                
                # 获取策略B的交易数据
                trades_b = trade_repo.get_trades_by_strategy(
                    f"{test.strategy_b_id}_{test.strategy_b_version}",
                    limit=10000
                )
                
                # 计算性能指标
                performance_a = self._calculate_performance_metrics(trades_a)
                performance_b = self._calculate_performance_metrics(trades_b)
                
                # 确定获胜者
                winner = self._determine_winner(performance_a, performance_b)
                
                # 计算统计显著性
                significance = self._calculate_statistical_significance(
                    performance_a, performance_b, len(trades_a), len(trades_b)
                )
                
                result = ABTestResult(
                    test_id=test_id,
                    strategy_a_performance=performance_a,
                    strategy_b_performance=performance_b,
                    winner=winner,
                    confidence_level=significance,
                    statistical_significance=significance > 0.95,
                    test_duration_days=(datetime.utcnow() - test.start_date).days,
                    total_trades_a=len(trades_a),
                    total_trades_b=len(trades_b)
                )
                
                # 保存结果
                ab_test_repo.update_ab_test_results(test_id, result.__dict__)
                
                return result
        
        except Exception as e:
            logger.error(f"分析A/B测试失败: {e}")
            return None
    
    def _calculate_performance_metrics(self, trades: List) -> Dict[str, float]:
        """计算性能指标"""
        if not trades:
            return {
                'total_return': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'win_rate': 0.0,
                'profit_factor': 0.0
            }
        
        # 计算基础指标
        total_pnl = sum(float(trade.pnl) for trade in trades)
        total_trades = len(trades)
        winning_trades = len([t for t in trades if float(t.pnl) > 0])
        losing_trades = len([t for t in trades if float(t.pnl) < 0])
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # 计算平均盈亏
        avg_win = sum(float(t.pnl) for t in trades if float(t.pnl) > 0) / max(winning_trades, 1)
        avg_loss = sum(float(t.pnl) for t in trades if float(t.pnl) < 0) / max(losing_trades, 1)
        
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        
        # 计算夏普比率（简化版）
        returns = [float(t.pnl) for t in trades]
        if len(returns) > 1:
            sharpe_ratio = (sum(returns) / len(returns)) / (sum((r - sum(returns)/len(returns))**2 for r in returns) / len(returns))**0.5
        else:
            sharpe_ratio = 0.0
        
        # 计算最大回撤
        cumulative_pnl = []
        running_total = 0
        for trade in trades:
            running_total += float(trade.pnl)
            cumulative_pnl.append(running_total)
        
        max_drawdown = 0
        peak = 0
        for pnl in cumulative_pnl:
            if pnl > peak:
                peak = pnl
            drawdown = peak - pnl
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return {
            'total_return': total_pnl,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'profit_factor': profit_factor
        }
    
    def _determine_winner(self, performance_a: Dict[str, float], 
                         performance_b: Dict[str, float]) -> str:
        """确定获胜者"""
        # 使用综合评分
        score_a = (
            performance_a['total_return'] * 0.3 +
            performance_a['sharpe_ratio'] * 0.3 +
            performance_a['win_rate'] * 0.2 +
            performance_a['profit_factor'] * 0.2
        )
        
        score_b = (
            performance_b['total_return'] * 0.3 +
            performance_b['sharpe_ratio'] * 0.3 +
            performance_b['win_rate'] * 0.2 +
            performance_b['profit_factor'] * 0.2
        )
        
        if abs(score_a - score_b) < 0.01:  # 差异小于1%
            return 'tie'
        elif score_a > score_b:
            return 'A'
        else:
            return 'B'
    
    def _calculate_statistical_significance(self, performance_a: Dict[str, float],
                                          performance_b: Dict[str, float],
                                          trades_a: int, trades_b: int) -> float:
        """计算统计显著性（简化版）"""
        # 这里使用简化的t检验
        # 实际应用中应该使用更严格的统计方法
        
        if trades_a < 30 or trades_b < 30:
            return 0.5  # 样本量不足
        
        # 基于夏普比率的差异
        sharpe_diff = abs(performance_a['sharpe_ratio'] - performance_b['sharpe_ratio'])
        
        # 简化的显著性计算
        if sharpe_diff > 0.5:
            return 0.95
        elif sharpe_diff > 0.3:
            return 0.85
        elif sharpe_diff > 0.1:
            return 0.70
        else:
            return 0.50


# 全局管理器实例
strategy_version_manager = StrategyVersionManager()
ab_test_manager = ABTestManager()


def get_strategy_version_manager() -> StrategyVersionManager:
    """获取策略版本管理器"""
    return strategy_version_manager


def get_ab_test_manager() -> ABTestManager:
    """获取A/B测试管理器"""
    return ab_test_manager
