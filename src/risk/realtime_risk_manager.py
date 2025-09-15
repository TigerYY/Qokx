#!/usr/bin/env python3
"""
实时风险管理器 - 动态仓位控制和实时风险监控
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from collections import defaultdict, deque
import uuid

from .risk_manager import RiskManager, RiskConfig, RiskLevel, PositionRisk
from ..execution.order_execution_engine import Order, OrderSide, OrderType, OrderStatus
from ..utils.position_manager import PositionManager, Position
from ..data.realtime_data_processor import RealtimeDataProcessor, TickData
from ..config.settings import TradingConfig

logger = logging.getLogger(__name__)


class RiskAction(Enum):
    """风险行动类型"""
    ALLOW = "allow"
    REDUCE = "reduce"
    BLOCK = "block"
    EMERGENCY_CLOSE = "emergency_close"
    PAUSE_TRADING = "pause_trading"


class RiskEventType(Enum):
    """风险事件类型"""
    DRAWDOWN_WARNING = "drawdown_warning"
    DRAWDOWN_LIMIT = "drawdown_limit"
    POSITION_SIZE_WARNING = "position_size_warning"
    POSITION_SIZE_LIMIT = "position_size_limit"
    DAILY_LOSS_WARNING = "daily_loss_warning"
    DAILY_LOSS_LIMIT = "daily_loss_limit"
    VOLATILITY_SPIKE = "volatility_spike"
    CORRELATION_RISK = "correlation_risk"
    LIQUIDITY_RISK = "liquidity_risk"
    MARKET_STRESS = "market_stress"


@dataclass
class RiskCheckResult:
    """风险检查结果"""
    approved: bool
    action: RiskAction
    reason: str
    max_position_size: float = 0.0
    suggested_size: float = 0.0
    risk_score: float = 0.0
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskEvent:
    """风险事件"""
    event_id: str
    event_type: RiskEventType
    symbol: Optional[str]
    timestamp: datetime
    severity: RiskLevel
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolution_time: Optional[datetime] = None


@dataclass
class PortfolioRiskMetrics:
    """投资组合风险指标"""
    total_exposure: float = 0.0
    net_exposure: float = 0.0
    gross_exposure: float = 0.0
    leverage: float = 0.0
    var_1d: float = 0.0  # 1日风险价值
    var_5d: float = 0.0  # 5日风险价值
    expected_shortfall: float = 0.0  # 期望损失
    max_drawdown: float = 0.0
    current_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    correlation_risk: float = 0.0
    concentration_risk: float = 0.0
    liquidity_risk: float = 0.0


@dataclass
class DynamicRiskLimits:
    """动态风险限制"""
    max_position_size: float
    max_daily_loss: float
    max_drawdown: float
    max_leverage: float
    max_correlation: float
    volatility_multiplier: float = 1.0
    market_stress_multiplier: float = 1.0
    last_update: datetime = field(default_factory=datetime.now)


class RealtimeRiskManager:
    """实时风险管理器"""
    
    def __init__(self,
                 base_risk_manager: RiskManager,
                 position_manager: PositionManager,
                 data_processor: RealtimeDataProcessor,
                 config: TradingConfig):
        
        self.base_risk_manager = base_risk_manager
        self.position_manager = position_manager
        self.data_processor = data_processor
        self.config = config
        
        # 实时风险监控
        self.is_monitoring = False
        self.monitoring_tasks = []
        
        # 风险事件管理
        self.risk_events: List[RiskEvent] = []
        self.active_events: Dict[str, RiskEvent] = {}
        
        # 动态风险限制
        self.dynamic_limits = DynamicRiskLimits(
            max_position_size=config.max_position_size or 0.1,
            max_daily_loss=config.max_daily_loss or 0.05,
            max_drawdown=config.max_drawdown or 0.2,
            max_leverage=config.max_leverage or 3.0,
            max_correlation=config.max_correlation or 0.7
        )
        
        # 投资组合风险指标
        self.portfolio_metrics = PortfolioRiskMetrics()
        
        # 价格历史缓存
        self.price_history = defaultdict(lambda: deque(maxlen=100))
        self.return_history = defaultdict(lambda: deque(maxlen=100))
        
        # 相关性矩阵
        self.correlation_matrix = {}
        self.correlation_update_time = None
        
        # 市场压力指标
        self.market_stress_indicators = {
            'vix_level': 0.0,
            'spread_widening': 0.0,
            'volume_spike': 0.0,
            'correlation_breakdown': 0.0
        }
        
        # 回调函数
        self.risk_event_callbacks: List[Callable] = []
        self.limit_breach_callbacks: List[Callable] = []
        self.emergency_callbacks: List[Callable] = []
        
        # 统计信息
        self.total_risk_checks = 0
        self.blocked_trades = 0
        self.reduced_trades = 0
        self.emergency_actions = 0
        
        logger.info("实时风险管理器初始化完成")
    
    async def start_monitoring(self) -> bool:
        """启动实时风险监控"""
        try:
            if self.is_monitoring:
                logger.warning("风险监控已在运行中")
                return False
            
            logger.info("启动实时风险监控...")
            
            # 注册数据回调
            self.data_processor.add_tick_callback(self._on_price_update)
            
            # 启动监控任务
            await self._start_monitoring_tasks()
            
            self.is_monitoring = True
            
            logger.info("实时风险监控启动成功")
            return True
            
        except Exception as e:
            logger.error(f"启动风险监控失败: {e}")
            return False
    
    async def stop_monitoring(self) -> bool:
        """停止实时风险监控"""
        try:
            if not self.is_monitoring:
                return True
            
            logger.info("停止实时风险监控...")
            
            self.is_monitoring = False
            
            # 停止监控任务
            for task in self.monitoring_tasks:
                task.cancel()
            
            logger.info("实时风险监控已停止")
            return True
            
        except Exception as e:
            logger.error(f"停止风险监控失败: {e}")
            return False
    
    async def _start_monitoring_tasks(self):
        """启动监控任务"""
        # 投资组合风险监控
        self.monitoring_tasks.append(
            asyncio.create_task(self._portfolio_risk_monitor())
        )
        
        # 动态限制调整
        self.monitoring_tasks.append(
            asyncio.create_task(self._dynamic_limits_adjuster())
        )
        
        # 相关性监控
        self.monitoring_tasks.append(
            asyncio.create_task(self._correlation_monitor())
        )
        
        # 市场压力监控
        self.monitoring_tasks.append(
            asyncio.create_task(self._market_stress_monitor())
        )
        
        # 风险事件清理
        self.monitoring_tasks.append(
            asyncio.create_task(self._risk_event_cleanup())
        )
    
    async def check_trading_risk(self,
                               symbol: str,
                               side: OrderSide,
                               size: float,
                               price: float,
                               metadata: Dict[str, Any] = None) -> RiskCheckResult:
        """检查交易风险"""
        self.total_risk_checks += 1
        
        try:
            # 1. 基础风险检查
            base_result = await self._basic_risk_check(symbol, side, size, price)
            if base_result.action == RiskAction.BLOCK:
                self.blocked_trades += 1
                return base_result
            
            # 2. 动态仓位检查
            position_result = await self._dynamic_position_check(symbol, side, size, price)
            if position_result.action in [RiskAction.BLOCK, RiskAction.REDUCE]:
                if position_result.action == RiskAction.BLOCK:
                    self.blocked_trades += 1
                else:
                    self.reduced_trades += 1
                return position_result
            
            # 3. 投资组合风险检查
            portfolio_result = await self._portfolio_risk_check(symbol, side, size, price)
            if portfolio_result.action in [RiskAction.BLOCK, RiskAction.REDUCE]:
                if portfolio_result.action == RiskAction.BLOCK:
                    self.blocked_trades += 1
                else:
                    self.reduced_trades += 1
                return portfolio_result
            
            # 4. 市场条件检查
            market_result = await self._market_condition_check(symbol, side, size, price)
            if market_result.action in [RiskAction.BLOCK, RiskAction.REDUCE]:
                if market_result.action == RiskAction.BLOCK:
                    self.blocked_trades += 1
                else:
                    self.reduced_trades += 1
                return market_result
            
            # 5. 相关性风险检查
            correlation_result = await self._correlation_risk_check(symbol, side, size)
            if correlation_result.action in [RiskAction.BLOCK, RiskAction.REDUCE]:
                if correlation_result.action == RiskAction.BLOCK:
                    self.blocked_trades += 1
                else:
                    self.reduced_trades += 1
                return correlation_result
            
            # 通过所有检查
            return RiskCheckResult(
                approved=True,
                action=RiskAction.ALLOW,
                reason="通过所有风险检查",
                max_position_size=size,
                suggested_size=size,
                risk_score=self._calculate_risk_score(symbol, side, size, price)
            )
            
        except Exception as e:
            logger.error(f"风险检查失败: {e}")
            return RiskCheckResult(
                approved=False,
                action=RiskAction.BLOCK,
                reason=f"风险检查异常: {str(e)}",
                risk_score=1.0
            )
    
    async def _basic_risk_check(self, symbol: str, side: OrderSide, size: float, price: float) -> RiskCheckResult:
        """基础风险检查"""
        warnings = []
        
        # 检查账户余额
        account_balance = self.position_manager.get_total_balance()
        if account_balance <= 0:
            return RiskCheckResult(
                approved=False,
                action=RiskAction.BLOCK,
                reason="账户余额不足",
                risk_score=1.0
            )
        
        # 检查单笔交易金额
        trade_value = size * price
        max_trade_value = account_balance * self.dynamic_limits.max_position_size
        
        if trade_value > max_trade_value:
            return RiskCheckResult(
                approved=False,
                action=RiskAction.REDUCE,
                reason=f"单笔交易金额超限: {trade_value:.2f} > {max_trade_value:.2f}",
                max_position_size=max_trade_value / price,
                suggested_size=max_trade_value / price,
                risk_score=0.8
            )
        
        # 检查日内损失限制
        daily_pnl = await self._calculate_daily_pnl()
        max_daily_loss = account_balance * self.dynamic_limits.max_daily_loss
        
        if daily_pnl < -max_daily_loss:
            return RiskCheckResult(
                approved=False,
                action=RiskAction.BLOCK,
                reason=f"日内损失超限: {daily_pnl:.2f} < {-max_daily_loss:.2f}",
                risk_score=1.0
            )
        
        # 检查最大回撤
        current_drawdown = await self._calculate_current_drawdown()
        if current_drawdown > self.dynamic_limits.max_drawdown:
            return RiskCheckResult(
                approved=False,
                action=RiskAction.BLOCK,
                reason=f"回撤超限: {current_drawdown:.2%} > {self.dynamic_limits.max_drawdown:.2%}",
                risk_score=1.0
            )
        
        return RiskCheckResult(
            approved=True,
            action=RiskAction.ALLOW,
            reason="基础风险检查通过",
            max_position_size=size,
            suggested_size=size,
            warnings=warnings,
            risk_score=0.1
        )
    
    async def _dynamic_position_check(self, symbol: str, side: OrderSide, size: float, price: float) -> RiskCheckResult:
        """动态仓位检查"""
        # 获取当前仓位
        current_position = await self.position_manager.get_position(symbol)
        current_size = current_position.size if current_position else 0.0
        
        # 计算新仓位
        if side == OrderSide.BUY:
            new_size = current_size + size
        else:
            new_size = current_size - size
        
        # 获取账户总价值
        account_value = self.position_manager.get_total_balance()
        
        # 计算仓位价值
        position_value = abs(new_size * price)
        position_ratio = position_value / account_value
        
        # 检查单一仓位限制
        max_single_position = self.dynamic_limits.max_position_size
        
        if position_ratio > max_single_position:
            # 计算允许的最大仓位
            max_position_value = account_value * max_single_position
            max_size = max_position_value / price
            
            if abs(current_size) >= max_size:
                return RiskCheckResult(
                    approved=False,
                    action=RiskAction.BLOCK,
                    reason=f"仓位已达上限: {position_ratio:.2%} >= {max_single_position:.2%}",
                    risk_score=0.9
                )
            
            # 减少交易大小
            suggested_size = max_size - abs(current_size)
            if side == OrderSide.SELL:
                suggested_size = min(suggested_size, current_size)
            
            return RiskCheckResult(
                approved=True,
                action=RiskAction.REDUCE,
                reason=f"仓位超限，建议减少交易大小",
                max_position_size=max_size,
                suggested_size=suggested_size,
                risk_score=0.6
            )
        
        return RiskCheckResult(
            approved=True,
            action=RiskAction.ALLOW,
            reason="动态仓位检查通过",
            max_position_size=size,
            suggested_size=size,
            risk_score=0.2
        )
    
    async def _portfolio_risk_check(self, symbol: str, side: OrderSide, size: float, price: float) -> RiskCheckResult:
        """投资组合风险检查"""
        # 更新投资组合指标
        await self._update_portfolio_metrics()
        
        # 检查总杠杆
        if self.portfolio_metrics.leverage > self.dynamic_limits.max_leverage:
            return RiskCheckResult(
                approved=False,
                action=RiskAction.BLOCK,
                reason=f"杠杆超限: {self.portfolio_metrics.leverage:.2f} > {self.dynamic_limits.max_leverage:.2f}",
                risk_score=0.9
            )
        
        # 检查集中度风险
        if self.portfolio_metrics.concentration_risk > 0.8:
            return RiskCheckResult(
                approved=False,
                action=RiskAction.REDUCE,
                reason=f"集中度风险过高: {self.portfolio_metrics.concentration_risk:.2f}",
                suggested_size=size * 0.5,
                risk_score=0.7
            )
        
        # 检查流动性风险
        if self.portfolio_metrics.liquidity_risk > 0.7:
            return RiskCheckResult(
                approved=False,
                action=RiskAction.REDUCE,
                reason=f"流动性风险过高: {self.portfolio_metrics.liquidity_risk:.2f}",
                suggested_size=size * 0.7,
                risk_score=0.6
            )
        
        return RiskCheckResult(
            approved=True,
            action=RiskAction.ALLOW,
            reason="投资组合风险检查通过",
            max_position_size=size,
            suggested_size=size,
            risk_score=0.3
        )
    
    async def _market_condition_check(self, symbol: str, side: OrderSide, size: float, price: float) -> RiskCheckResult:
        """市场条件检查"""
        # 获取市场数据
        tick_data = self.data_processor.get_latest_tick(symbol)
        if not tick_data:
            return RiskCheckResult(
                approved=False,
                action=RiskAction.BLOCK,
                reason="无法获取市场数据",
                risk_score=0.8
            )
        
        # 检查价格波动
        volatility = await self._calculate_volatility(symbol)
        if volatility > 0.1:  # 10%的日波动率
            return RiskCheckResult(
                approved=True,
                action=RiskAction.REDUCE,
                reason=f"市场波动过大: {volatility:.2%}",
                suggested_size=size * (1 - min(volatility, 0.5)),
                risk_score=0.6
            )
        
        # 检查买卖价差
        if tick_data.bid_price > 0 and tick_data.ask_price > 0:
            spread = (tick_data.ask_price - tick_data.bid_price) / tick_data.price
            if spread > 0.01:  # 1%的价差
                return RiskCheckResult(
                    approved=True,
                    action=RiskAction.REDUCE,
                    reason=f"买卖价差过大: {spread:.2%}",
                    suggested_size=size * 0.8,
                    risk_score=0.5
                )
        
        # 检查市场压力指标
        stress_level = self._calculate_market_stress()
        if stress_level > 0.8:
            return RiskCheckResult(
                approved=False,
                action=RiskAction.BLOCK,
                reason=f"市场压力过大: {stress_level:.2f}",
                risk_score=0.9
            )
        elif stress_level > 0.6:
            return RiskCheckResult(
                approved=True,
                action=RiskAction.REDUCE,
                reason=f"市场压力较大: {stress_level:.2f}",
                suggested_size=size * 0.6,
                risk_score=0.6
            )
        
        return RiskCheckResult(
            approved=True,
            action=RiskAction.ALLOW,
            reason="市场条件检查通过",
            max_position_size=size,
            suggested_size=size,
            risk_score=0.2
        )
    
    async def _correlation_risk_check(self, symbol: str, side: OrderSide, size: float) -> RiskCheckResult:
        """相关性风险检查"""
        # 更新相关性矩阵
        await self._update_correlation_matrix()
        
        # 获取当前所有仓位
        positions = await self.position_manager.get_all_positions()
        
        # 计算与现有仓位的相关性风险
        total_correlation_risk = 0.0
        
        for pos_symbol, position in positions.items():
            if pos_symbol == symbol or position.size == 0:
                continue
            
            # 获取相关系数
            correlation = self.correlation_matrix.get((symbol, pos_symbol), 0.0)
            
            # 计算相关性风险
            if abs(correlation) > self.dynamic_limits.max_correlation:
                position_weight = abs(position.size * position.current_price) / self.position_manager.get_total_balance()
                correlation_risk = abs(correlation) * position_weight
                total_correlation_risk += correlation_risk
        
        if total_correlation_risk > 0.5:
            return RiskCheckResult(
                approved=False,
                action=RiskAction.REDUCE,
                reason=f"相关性风险过高: {total_correlation_risk:.2f}",
                suggested_size=size * (1 - total_correlation_risk),
                risk_score=0.7
            )
        
        return RiskCheckResult(
            approved=True,
            action=RiskAction.ALLOW,
            reason="相关性风险检查通过",
            max_position_size=size,
            suggested_size=size,
            risk_score=0.1
        )
    
    async def _on_price_update(self, tick_data: TickData):
        """处理价格更新"""
        try:
            symbol = tick_data.symbol
            price = tick_data.price
            
            # 更新价格历史
            self.price_history[symbol].append((tick_data.timestamp, price))
            
            # 计算收益率
            if len(self.price_history[symbol]) >= 2:
                prev_price = self.price_history[symbol][-2][1]
                return_rate = (price / prev_price - 1) if prev_price > 0 else 0.0
                self.return_history[symbol].append(return_rate)
            
            # 检查价格异常
            await self._check_price_anomaly(symbol, price)
            
            # 更新市场压力指标
            await self._update_market_stress_indicators(symbol, tick_data)
            
        except Exception as e:
            logger.error(f"处理价格更新失败: {e}")
    
    async def _check_price_anomaly(self, symbol: str, current_price: float):
        """检查价格异常"""
        if len(self.price_history[symbol]) < 10:
            return
        
        # 计算价格变化
        recent_prices = [p[1] for p in list(self.price_history[symbol])[-10:]]
        avg_price = np.mean(recent_prices)
        price_change = abs(current_price - avg_price) / avg_price
        
        # 检查异常波动
        if price_change > 0.05:  # 5%的异常波动
            event = RiskEvent(
                event_id=str(uuid.uuid4()),
                event_type=RiskEventType.VOLATILITY_SPIKE,
                symbol=symbol,
                timestamp=datetime.now(),
                severity=RiskLevel.HIGH if price_change > 0.1 else RiskLevel.MEDIUM,
                message=f"{symbol} 价格异常波动: {price_change:.2%}",
                data={'price_change': price_change, 'current_price': current_price}
            )
            
            await self._handle_risk_event(event)
    
    async def _portfolio_risk_monitor(self):
        """投资组合风险监控任务"""
        while self.is_monitoring:
            try:
                await self._update_portfolio_metrics()
                await self._check_portfolio_limits()
                await asyncio.sleep(30)  # 每30秒检查一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"投资组合风险监控错误: {e}")
                await asyncio.sleep(60)
    
    async def _update_portfolio_metrics(self):
        """更新投资组合风险指标"""
        try:
            positions = await self.position_manager.get_all_positions()
            account_balance = self.position_manager.get_total_balance()
            
            if not positions or account_balance <= 0:
                return
            
            # 计算暴露度
            long_exposure = sum(pos.size * pos.current_price for pos in positions.values() if pos.size > 0)
            short_exposure = sum(abs(pos.size * pos.current_price) for pos in positions.values() if pos.size < 0)
            
            self.portfolio_metrics.gross_exposure = (long_exposure + short_exposure) / account_balance
            self.portfolio_metrics.net_exposure = (long_exposure - short_exposure) / account_balance
            self.portfolio_metrics.leverage = self.portfolio_metrics.gross_exposure
            
            # 计算VaR
            await self._calculate_var()
            
            # 计算集中度风险
            self.portfolio_metrics.concentration_risk = self._calculate_concentration_risk(positions, account_balance)
            
            # 计算流动性风险
            self.portfolio_metrics.liquidity_risk = await self._calculate_liquidity_risk(positions)
            
            # 计算相关性风险
            self.portfolio_metrics.correlation_risk = await self._calculate_correlation_risk(positions)
            
        except Exception as e:
            logger.error(f"更新投资组合指标失败: {e}")
    
    async def _calculate_var(self, confidence: float = 0.95, horizon: int = 1):
        """计算风险价值(VaR)"""
        try:
            positions = await self.position_manager.get_all_positions()
            if not positions:
                return
            
            # 收集所有仓位的收益率
            portfolio_returns = []
            
            for symbol, position in positions.items():
                if symbol in self.return_history and len(self.return_history[symbol]) >= 20:
                    returns = list(self.return_history[symbol])[-20:]  # 最近20个收益率
                    position_weight = abs(position.size * position.current_price) / self.position_manager.get_total_balance()
                    weighted_returns = [r * position_weight for r in returns]
                    portfolio_returns.extend(weighted_returns)
            
            if len(portfolio_returns) >= 10:
                # 计算VaR
                portfolio_returns = np.array(portfolio_returns)
                var_percentile = (1 - confidence) * 100
                var_1d = np.percentile(portfolio_returns, var_percentile)
                
                self.portfolio_metrics.var_1d = abs(var_1d)
                self.portfolio_metrics.var_5d = abs(var_1d) * np.sqrt(5)  # 假设收益率独立
                
                # 计算期望损失(ES)
                tail_losses = portfolio_returns[portfolio_returns <= var_1d]
                if len(tail_losses) > 0:
                    self.portfolio_metrics.expected_shortfall = abs(np.mean(tail_losses))
            
        except Exception as e:
            logger.error(f"计算VaR失败: {e}")
    
    def _calculate_concentration_risk(self, positions: Dict[str, Position], account_balance: float) -> float:
        """计算集中度风险"""
        if not positions or account_balance <= 0:
            return 0.0
        
        # 计算各仓位权重
        weights = []
        for position in positions.values():
            weight = abs(position.size * position.current_price) / account_balance
            weights.append(weight)
        
        if not weights:
            return 0.0
        
        # 使用赫芬达尔指数衡量集中度
        herfindahl_index = sum(w**2 for w in weights)
        
        # 标准化到0-1范围
        max_concentration = 1.0  # 完全集中在一个资产
        min_concentration = 1.0 / len(weights) if weights else 0.0  # 完全分散
        
        if max_concentration > min_concentration:
            normalized_concentration = (herfindahl_index - min_concentration) / (max_concentration - min_concentration)
        else:
            normalized_concentration = 0.0
        
        return min(normalized_concentration, 1.0)
    
    async def _calculate_liquidity_risk(self, positions: Dict[str, Position]) -> float:
        """计算流动性风险"""
        if not positions:
            return 0.0
        
        total_liquidity_risk = 0.0
        total_weight = 0.0
        account_balance = self.position_manager.get_total_balance()
        
        for symbol, position in positions.items():
            # 获取最新tick数据
            tick_data = self.data_processor.get_latest_tick(symbol)
            if not tick_data:
                continue
            
            # 计算买卖价差作为流动性指标
            if tick_data.bid_price > 0 and tick_data.ask_price > 0:
                spread = (tick_data.ask_price - tick_data.bid_price) / tick_data.price
                liquidity_risk = min(spread * 10, 1.0)  # 价差越大，流动性风险越高
            else:
                liquidity_risk = 0.5  # 默认中等风险
            
            # 按仓位权重加权
            position_weight = abs(position.size * position.current_price) / account_balance
            total_liquidity_risk += liquidity_risk * position_weight
            total_weight += position_weight
        
        return total_liquidity_risk / total_weight if total_weight > 0 else 0.0
    
    async def _calculate_correlation_risk(self, positions: Dict[str, Position]) -> float:
        """计算相关性风险"""
        if len(positions) < 2:
            return 0.0
        
        await self._update_correlation_matrix()
        
        total_correlation_risk = 0.0
        pair_count = 0
        
        symbols = list(positions.keys())
        for i, symbol1 in enumerate(symbols):
            for symbol2 in symbols[i+1:]:
                correlation = self.correlation_matrix.get((symbol1, symbol2), 0.0)
                correlation_risk = abs(correlation)
                total_correlation_risk += correlation_risk
                pair_count += 1
        
        return total_correlation_risk / pair_count if pair_count > 0 else 0.0
    
    async def _update_correlation_matrix(self):
        """更新相关性矩阵"""
        try:
            # 每5分钟更新一次
            if (self.correlation_update_time and 
                datetime.now() - self.correlation_update_time < timedelta(minutes=5)):
                return
            
            symbols = list(self.return_history.keys())
            if len(symbols) < 2:
                return
            
            # 计算相关系数
            for i, symbol1 in enumerate(symbols):
                for symbol2 in symbols[i+1:]:
                    if (len(self.return_history[symbol1]) >= 20 and 
                        len(self.return_history[symbol2]) >= 20):
                        
                        returns1 = list(self.return_history[symbol1])[-20:]
                        returns2 = list(self.return_history[symbol2])[-20:]
                        
                        correlation = np.corrcoef(returns1, returns2)[0, 1]
                        if not np.isnan(correlation):
                            self.correlation_matrix[(symbol1, symbol2)] = correlation
                            self.correlation_matrix[(symbol2, symbol1)] = correlation
            
            self.correlation_update_time = datetime.now()
            
        except Exception as e:
            logger.error(f"更新相关性矩阵失败: {e}")
    
    async def _check_portfolio_limits(self):
        """检查投资组合限制"""
        try:
            # 检查杠杆限制
            if self.portfolio_metrics.leverage > self.dynamic_limits.max_leverage:
                event = RiskEvent(
                    event_id=str(uuid.uuid4()),
                    event_type=RiskEventType.POSITION_SIZE_LIMIT,
                    symbol=None,
                    timestamp=datetime.now(),
                    severity=RiskLevel.HIGH,
                    message=f"杠杆超限: {self.portfolio_metrics.leverage:.2f} > {self.dynamic_limits.max_leverage:.2f}",
                    data={'leverage': self.portfolio_metrics.leverage}
                )
                await self._handle_risk_event(event)
            
            # 检查VaR限制
            max_var = self.position_manager.get_total_balance() * 0.1  # 10%的VaR限制
            if self.portfolio_metrics.var_1d > max_var:
                event = RiskEvent(
                    event_id=str(uuid.uuid4()),
                    event_type=RiskEventType.DRAWDOWN_WARNING,
                    symbol=None,
                    timestamp=datetime.now(),
                    severity=RiskLevel.MEDIUM,
                    message=f"VaR超限: {self.portfolio_metrics.var_1d:.2f} > {max_var:.2f}",
                    data={'var_1d': self.portfolio_metrics.var_1d}
                )
                await self._handle_risk_event(event)
            
        except Exception as e:
            logger.error(f"检查投资组合限制失败: {e}")
    
    async def _dynamic_limits_adjuster(self):
        """动态限制调整任务"""
        while self.is_monitoring:
            try:
                await self._adjust_dynamic_limits()
                await asyncio.sleep(300)  # 每5分钟调整一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"动态限制调整错误: {e}")
                await asyncio.sleep(600)
    
    async def _adjust_dynamic_limits(self):
        """调整动态限制"""
        try:
            # 基于市场波动率调整
            avg_volatility = await self._calculate_average_volatility()
            if avg_volatility > 0.05:  # 高波动率
                self.dynamic_limits.volatility_multiplier = 0.7
            elif avg_volatility < 0.02:  # 低波动率
                self.dynamic_limits.volatility_multiplier = 1.2
            else:
                self.dynamic_limits.volatility_multiplier = 1.0
            
            # 基于市场压力调整
            market_stress = self._calculate_market_stress()
            if market_stress > 0.7:
                self.dynamic_limits.market_stress_multiplier = 0.5
            elif market_stress < 0.3:
                self.dynamic_limits.market_stress_multiplier = 1.1
            else:
                self.dynamic_limits.market_stress_multiplier = 1.0
            
            # 应用调整
            base_config = self.base_risk_manager.config
            self.dynamic_limits.max_position_size = (
                base_config.max_position_size * 
                self.dynamic_limits.volatility_multiplier * 
                self.dynamic_limits.market_stress_multiplier
            )
            
            self.dynamic_limits.max_daily_loss = (
                base_config.max_daily_loss * 
                self.dynamic_limits.volatility_multiplier
            )
            
            self.dynamic_limits.last_update = datetime.now()
            
        except Exception as e:
            logger.error(f"调整动态限制失败: {e}")
    
    async def _calculate_average_volatility(self) -> float:
        """计算平均波动率"""
        volatilities = []
        
        for symbol in self.return_history.keys():
            volatility = await self._calculate_volatility(symbol)
            if volatility > 0:
                volatilities.append(volatility)
        
        return np.mean(volatilities) if volatilities else 0.0
    
    async def _calculate_volatility(self, symbol: str, window: int = 20) -> float:
        """计算波动率"""
        if symbol not in self.return_history or len(self.return_history[symbol]) < window:
            return 0.0
        
        returns = list(self.return_history[symbol])[-window:]
        return np.std(returns) * np.sqrt(252)  # 年化波动率
    
    def _calculate_market_stress(self) -> float:
        """计算市场压力指标"""
        # 综合各种压力指标
        stress_components = [
            self.market_stress_indicators['vix_level'],
            self.market_stress_indicators['spread_widening'],
            self.market_stress_indicators['volume_spike'],
            self.market_stress_indicators['correlation_breakdown']
        ]
        
        return np.mean([s for s in stress_components if s > 0]) if any(s > 0 for s in stress_components) else 0.0
    
    async def _market_stress_monitor(self):
        """市场压力监控任务"""
        while self.is_monitoring:
            try:
                await self._update_market_stress_indicators()
                await asyncio.sleep(60)  # 每分钟更新一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"市场压力监控错误: {e}")
                await asyncio.sleep(120)
    
    async def _update_market_stress_indicators(self, symbol: str = None, tick_data: TickData = None):
        """更新市场压力指标"""
        try:
            # 更新价差扩大指标
            if tick_data and tick_data.bid_price > 0 and tick_data.ask_price > 0:
                spread = (tick_data.ask_price - tick_data.bid_price) / tick_data.price
                # 更新平均价差
                current_spread = self.market_stress_indicators.get('spread_widening', 0.0)
                self.market_stress_indicators['spread_widening'] = current_spread * 0.9 + spread * 0.1
            
            # 更新成交量异常指标
            if tick_data:
                # 简化的成交量异常检测
                volume_spike = min(tick_data.volume / 1000000, 1.0)  # 标准化成交量
                current_volume = self.market_stress_indicators.get('volume_spike', 0.0)
                self.market_stress_indicators['volume_spike'] = current_volume * 0.95 + volume_spike * 0.05
            
            # 更新相关性崩溃指标
            if len(self.correlation_matrix) > 0:
                correlations = list(self.correlation_matrix.values())
                avg_correlation = np.mean([abs(c) for c in correlations])
                # 相关性过高或过低都是压力信号
                correlation_stress = abs(avg_correlation - 0.3) / 0.7  # 0.3为理想相关性
                self.market_stress_indicators['correlation_breakdown'] = min(correlation_stress, 1.0)
            
        except Exception as e:
            logger.error(f"更新市场压力指标失败: {e}")
    
    async def _correlation_monitor(self):
        """相关性监控任务"""
        while self.is_monitoring:
            try:
                await self._update_correlation_matrix()
                await self._check_correlation_anomalies()
                await asyncio.sleep(300)  # 每5分钟检查一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"相关性监控错误: {e}")
                await asyncio.sleep(600)
    
    async def _check_correlation_anomalies(self):
        """检查相关性异常"""
        try:
            if not self.correlation_matrix:
                return
            
            # 检查异常高相关性
            high_correlations = [(pair, corr) for pair, corr in self.correlation_matrix.items() 
                               if abs(corr) > self.dynamic_limits.max_correlation]
            
            if high_correlations:
                for (symbol1, symbol2), correlation in high_correlations:
                    event = RiskEvent(
                        event_id=str(uuid.uuid4()),
                        event_type=RiskEventType.CORRELATION_RISK,
                        symbol=f"{symbol1}-{symbol2}",
                        timestamp=datetime.now(),
                        severity=RiskLevel.MEDIUM,
                        message=f"高相关性风险: {symbol1}-{symbol2} 相关性 {correlation:.3f}",
                        data={'correlation': correlation, 'symbols': [symbol1, symbol2]}
                    )
                    await self._handle_risk_event(event)
            
        except Exception as e:
            logger.error(f"检查相关性异常失败: {e}")
    
    async def _risk_event_cleanup(self):
        """风险事件清理任务"""
        while self.is_monitoring:
            try:
                # 清理已解决的事件
                cutoff_time = datetime.now() - timedelta(hours=24)
                self.risk_events = [
                    event for event in self.risk_events
                    if event.timestamp > cutoff_time or not event.resolved
                ]
                
                # 清理活跃事件
                expired_events = []
                for event_id, event in self.active_events.items():
                    if event.timestamp < cutoff_time:
                        expired_events.append(event_id)
                
                for event_id in expired_events:
                    self.active_events.pop(event_id, None)
                
                await asyncio.sleep(3600)  # 每小时清理一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"风险事件清理错误: {e}")
                await asyncio.sleep(1800)
    
    async def _handle_risk_event(self, event: RiskEvent):
        """处理风险事件"""
        try:
            # 记录事件
            self.risk_events.append(event)
            self.active_events[event.event_id] = event
            
            logger.warning(f"风险事件: {event.message}")
            
            # 根据事件类型和严重程度采取行动
            if event.severity == RiskLevel.EXTREME:
                await self._trigger_emergency_action(event)
                self.emergency_actions += 1
            
            # 触发回调
            await self._trigger_callbacks(self.risk_event_callbacks, event)
            
        except Exception as e:
            logger.error(f"处理风险事件失败: {e}")
    
    async def _trigger_emergency_action(self, event: RiskEvent):
        """触发紧急行动"""
        try:
            logger.critical(f"触发紧急行动: {event.message}")
            
            # 根据事件类型采取相应行动
            if event.event_type in [RiskEventType.DRAWDOWN_LIMIT, RiskEventType.DAILY_LOSS_LIMIT]:
                # 暂停所有交易
                await self._pause_all_trading()
            
            elif event.event_type == RiskEventType.POSITION_SIZE_LIMIT:
                # 强制平仓部分仓位
                await self._force_reduce_positions()
            
            elif event.event_type == RiskEventType.MARKET_STRESS:
                # 降低风险暴露
                await self._reduce_risk_exposure()
            
            # 触发紧急回调
            await self._trigger_callbacks(self.emergency_callbacks, event)
            
        except Exception as e:
            logger.error(f"执行紧急行动失败: {e}")
    
    async def _pause_all_trading(self):
        """暂停所有交易"""
        logger.critical("暂停所有交易")
        # 这里应该通知交易引擎暂停交易
        # 具体实现依赖于交易引擎的接口
    
    async def _force_reduce_positions(self):
        """强制减少仓位"""
        logger.critical("强制减少仓位")
        # 这里应该生成平仓订单
        # 具体实现依赖于执行引擎的接口
    
    async def _reduce_risk_exposure(self):
        """降低风险暴露"""
        logger.critical("降低风险暴露")
        # 调整动态限制
        self.dynamic_limits.max_position_size *= 0.5
        self.dynamic_limits.max_leverage *= 0.7
    
    def _calculate_risk_score(self, symbol: str, side: OrderSide, size: float, price: float) -> float:
        """计算风险评分"""
        try:
            risk_factors = []
            
            # 仓位大小风险
            account_balance = self.position_manager.get_total_balance()
            position_ratio = (size * price) / account_balance
            position_risk = min(position_ratio / self.dynamic_limits.max_position_size, 1.0)
            risk_factors.append(position_risk)
            
            # 波动率风险
            volatility = asyncio.create_task(self._calculate_volatility(symbol))
            # 由于是同步方法，这里使用简化计算
            vol_risk = min(len(self.return_history.get(symbol, [])) / 100, 1.0)
            risk_factors.append(vol_risk)
            
            # 市场压力风险
            market_stress = self._calculate_market_stress()
            risk_factors.append(market_stress)
            
            # 投资组合风险
            portfolio_risk = min(self.portfolio_metrics.leverage / self.dynamic_limits.max_leverage, 1.0)
            risk_factors.append(portfolio_risk)
            
            return np.mean(risk_factors)
            
        except Exception as e:
            logger.error(f"计算风险评分失败: {e}")
            return 0.5  # 默认中等风险
    
    async def _calculate_daily_pnl(self) -> float:
        """计算日内盈亏"""
        try:
            positions = await self.position_manager.get_all_positions()
            total_pnl = 0.0
            
            for position in positions.values():
                if position.size != 0:
                    unrealized_pnl = position.size * (position.current_price - position.entry_price)
                    total_pnl += unrealized_pnl
            
            # 加上已实现盈亏
            total_pnl += self.base_risk_manager.today_realized_pnl
            
            return total_pnl
            
        except Exception as e:
            logger.error(f"计算日内盈亏失败: {e}")
            return 0.0
    
    async def _calculate_current_drawdown(self) -> float:
        """计算当前回撤"""
        try:
            # 简化的回撤计算
            current_balance = self.position_manager.get_total_balance()
            # 这里应该从历史记录中获取最高净值
            # 暂时使用简化计算
            peak_balance = current_balance * 1.1  # 假设峰值比当前高10%
            
            drawdown = (peak_balance - current_balance) / peak_balance
            return max(drawdown, 0.0)
            
        except Exception as e:
            logger.error(f"计算当前回撤失败: {e}")
            return 0.0
    
    async def _trigger_callbacks(self, callbacks: List[Callable], data: Any):
        """触发回调函数"""
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            except Exception as e:
                logger.error(f"回调函数执行失败: {e}")
    
    # 公共接口方法
    
    async def update_market_price(self, symbol: str, price: float):
        """更新市场价格"""
        # 创建临时tick数据
        tick_data = TickData(
            symbol=symbol,
            timestamp=datetime.now(),
            price=price,
            volume=0.0
        )
        await self._on_price_update(tick_data)
    
    def add_risk_event_callback(self, callback: Callable):
        """添加风险事件回调"""
        self.risk_event_callbacks.append(callback)
    
    def add_limit_breach_callback(self, callback: Callable):
        """添加限制突破回调"""
        self.limit_breach_callbacks.append(callback)
    
    def add_emergency_callback(self, callback: Callable):
        """添加紧急情况回调"""
        self.emergency_callbacks.append(callback)
    
    def get_portfolio_metrics(self) -> PortfolioRiskMetrics:
        """获取投资组合风险指标"""
        return self.portfolio_metrics
    
    def get_dynamic_limits(self) -> DynamicRiskLimits:
        """获取动态风险限制"""
        return self.dynamic_limits
    
    def get_risk_events(self, limit: int = 100) -> List[RiskEvent]:
        """获取风险事件历史"""
        return self.risk_events[-limit:]
    
    def get_active_events(self) -> Dict[str, RiskEvent]:
        """获取活跃风险事件"""
        return self.active_events.copy()
    
    def get_risk_statistics(self) -> Dict[str, Any]:
        """获取风险统计信息"""
        return {
            'total_risk_checks': self.total_risk_checks,
            'blocked_trades': self.blocked_trades,
            'reduced_trades': self.reduced_trades,
            'emergency_actions': self.emergency_actions,
            'success_rate': 1 - (self.blocked_trades / max(self.total_risk_checks, 1)),
            'active_events_count': len(self.active_events),
            'portfolio_metrics': self.portfolio_metrics,
            'dynamic_limits': self.dynamic_limits
        }
    
    async def force_risk_check(self, symbol: str) -> Dict[str, Any]:
        """强制执行风险检查"""
        try:
            # 更新投资组合指标
            await self._update_portfolio_metrics()
            
            # 检查各种风险
            position = await self.position_manager.get_position(symbol)
            if position:
                # 检查仓位风险
                await self._check_price_anomaly(symbol, position.current_price)
            
            # 检查投资组合限制
            await self._check_portfolio_limits()
            
            return {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'portfolio_metrics': self.portfolio_metrics,
                'active_events': len(self.active_events),
                'market_stress': self._calculate_market_stress()
            }
            
        except Exception as e:
            logger.error(f"强制风险检查失败: {e}")
            return {'error': str(e)}


# 全局实例
global_realtime_risk_manager: Optional[RealtimeRiskManager] = None


def get_realtime_risk_manager() -> Optional[RealtimeRiskManager]:
    """获取全局实时风险管理器实例"""
    return global_realtime_risk_manager


def initialize_realtime_risk_manager(
    base_risk_manager: RiskManager,
    position_manager: PositionManager,
    data_processor: RealtimeDataProcessor,
    config: TradingConfig
) -> RealtimeRiskManager:
    """初始化全局实时风险管理器"""
    global global_realtime_risk_manager
    global_realtime_risk_manager = RealtimeRiskManager(
        base_risk_manager, position_manager, data_processor, config
    )
    return global_realtime_risk_manager