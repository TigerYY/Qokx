"""
网格交易策略核心实现
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
import numpy as np

from .grid_config import GridConfig, GridLevel, GridTradingState, GridType, GridDirection
from ..data.multi_timeframe_manager import OHLCVData
from ..execution.order_manager import Order, OrderSide, OrderType, OrderStatus
from ..risk.position_sizer import PositionSizer
from ..risk.realtime_risk_manager import RealtimeRiskManager

logger = logging.getLogger(__name__)


@dataclass
class GridSignal:
    """网格交易信号"""
    signal_type: str  # 'buy', 'sell', 'adjust'
    price: Decimal
    quantity: Decimal
    grid_level: int
    confidence: float
    reason: str
    timestamp: datetime


@dataclass
class GridTradingResult:
    """网格交易结果"""
    success: bool
    message: str
    signal: Optional[GridSignal] = None
    order: Optional[Order] = None
    error: Optional[str] = None


class GridTradingStrategy:
    """网格交易策略核心类"""
    
    def __init__(self, config: GridConfig, order_manager, risk_manager: RealtimeRiskManager):
        self.config = config
        self.order_manager = order_manager
        self.risk_manager = risk_manager
        self.position_sizer = PositionSizer()
        
        # 交易状态
        self.state = GridTradingState(current_price=Decimal('0'))
        self.grid_levels: List[GridLevel] = []
        self.is_running = False
        self.last_rebalance_time = datetime.now()
        
        # 性能统计
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.max_drawdown = Decimal('0')
        self.peak_equity = Decimal('0')
        
        logger.info(f"初始化网格交易策略: {config.strategy_name}")
    
    async def initialize(self, current_price: Decimal) -> bool:
        """初始化策略"""
        try:
            self.state.current_price = current_price
            
            # 计算网格价格水平
            self.grid_levels = self._calculate_grid_levels(current_price)
            
            # 初始化状态
            self.state.grid_levels = self.grid_levels
            self.state.last_update_time = datetime.now().isoformat()
            
            logger.info(f"网格策略初始化完成，共{len(self.grid_levels)}个网格水平")
            return True
            
        except Exception as e:
            logger.error(f"网格策略初始化失败: {e}")
            return False
    
    def _calculate_grid_levels(self, current_price: Decimal) -> List[GridLevel]:
        """计算网格价格水平"""
        levels = []
        
        if self.config.grid_type == GridType.ARITHMETIC:
            levels = self._calculate_arithmetic_grid(current_price)
        elif self.config.grid_type == GridType.GEOMETRIC:
            levels = self._calculate_geometric_grid(current_price)
        elif self.config.grid_type == GridType.FIBONACCI:
            levels = self._calculate_fibonacci_grid(current_price)
        elif self.config.grid_type == GridType.CUSTOM:
            levels = self._calculate_custom_grid(current_price)
        
        # 过滤价格范围
        filtered_levels = []
        for level in levels:
            if self.config.is_price_in_range(level.price):
                filtered_levels.append(level)
        
        return filtered_levels
    
    def _calculate_arithmetic_grid(self, current_price: Decimal) -> List[GridLevel]:
        """计算等差数列网格"""
        levels = []
        spacing_amount = self.config.get_grid_spacing_amount(current_price)
        
        # 计算网格数量
        total_levels = self.config.grid_count
        buy_levels = total_levels // 2
        sell_levels = total_levels - buy_levels
        
        # 生成买入网格
        for i in range(1, buy_levels + 1):
            price = current_price - (spacing_amount * i)
            if price > 0:
                level = GridLevel(
                    price=price,
                    quantity=self.config.base_quantity,
                    order_type='buy',
                    is_active=True
                )
                levels.append(level)
        
        # 生成卖出网格
        for i in range(1, sell_levels + 1):
            price = current_price + (spacing_amount * i)
            level = GridLevel(
                price=price,
                quantity=self.config.base_quantity,
                order_type='sell',
                is_active=True
            )
            levels.append(level)
        
        return levels
    
    def _calculate_geometric_grid(self, current_price: Decimal) -> List[GridLevel]:
        """计算等比数列网格"""
        levels = []
        spacing_ratio = 1 + self.config.grid_spacing
        
        # 计算网格数量
        total_levels = self.config.grid_count
        buy_levels = total_levels // 2
        sell_levels = total_levels - buy_levels
        
        # 生成买入网格
        for i in range(1, buy_levels + 1):
            price = current_price / (spacing_ratio ** i)
            if price > 0:
                level = GridLevel(
                    price=price,
                    quantity=self.config.base_quantity,
                    order_type='buy',
                    is_active=True
                )
                levels.append(level)
        
        # 生成卖出网格
        for i in range(1, sell_levels + 1):
            price = current_price * (spacing_ratio ** i)
            level = GridLevel(
                price=price,
                quantity=self.config.base_quantity,
                order_type='sell',
                is_active=True
            )
            levels.append(level)
        
        return levels
    
    def _calculate_fibonacci_grid(self, current_price: Decimal) -> List[GridLevel]:
        """计算斐波那契网格"""
        levels = []
        
        # 斐波那契数列
        fib_ratios = [0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.272, 1.618, 2.0, 2.618]
        
        # 计算网格数量
        total_levels = min(self.config.grid_count, len(fib_ratios))
        buy_levels = total_levels // 2
        sell_levels = total_levels - buy_levels
        
        # 生成买入网格
        for i in range(buy_levels):
            ratio = fib_ratios[i]
            price = current_price * (1 - ratio * self.config.grid_spacing)
            if price > 0:
                level = GridLevel(
                    price=price,
                    quantity=self.config.base_quantity,
                    order_type='buy',
                    is_active=True
                )
                levels.append(level)
        
        # 生成卖出网格
        for i in range(sell_levels):
            ratio = fib_ratios[i]
            price = current_price * (1 + ratio * self.config.grid_spacing)
            level = GridLevel(
                price=price,
                quantity=self.config.base_quantity,
                order_type='sell',
                is_active=True
            )
            levels.append(level)
        
        return levels
    
    def _calculate_custom_grid(self, current_price: Decimal) -> List[GridLevel]:
        """计算自定义网格"""
        levels = []
        
        # 从配置中获取自定义网格参数
        custom_levels = self.config.custom_params.get('grid_levels', [])
        
        for level_config in custom_levels:
            price = Decimal(str(level_config['price']))
            quantity = Decimal(str(level_config['quantity']))
            order_type = level_config['order_type']
            
            level = GridLevel(
                price=price,
                quantity=quantity,
                order_type=order_type,
                is_active=True
            )
            levels.append(level)
        
        return levels
    
    async def generate_signals(self, price_data: OHLCVData) -> List[GridSignal]:
        """生成网格交易信号"""
        if not price_data or len(price_data.close) == 0:
            return []
        
        current_price = Decimal(str(price_data.close[-1]))
        signals = []
        
        # 更新当前价格
        self.state.current_price = current_price
        
        # 检查网格触发
        for i, level in enumerate(self.grid_levels):
            if not level.is_active:
                continue
            
            signal = self._check_grid_trigger(level, current_price, i)
            if signal:
                signals.append(signal)
        
        # 检查动态调整
        if self.config.enable_dynamic_adjustment:
            adjustment_signal = self._check_dynamic_adjustment(current_price)
            if adjustment_signal:
                signals.append(adjustment_signal)
        
        # 检查风险控制
        risk_signal = self._check_risk_control(current_price)
        if risk_signal:
            signals.append(risk_signal)
        
        return signals
    
    def _check_grid_trigger(self, level: GridLevel, current_price: Decimal, level_index: int) -> Optional[GridSignal]:
        """检查网格触发"""
        if level.order_type == 'buy' and current_price <= level.price:
            # 买入网格触发
            return GridSignal(
                signal_type='buy',
                price=level.price,
                quantity=level.quantity,
                grid_level=level_index,
                confidence=1.0,
                reason=f"买入网格触发，价格{current_price} <= {level.price}",
                timestamp=datetime.now()
            )
        
        elif level.order_type == 'sell' and current_price >= level.price:
            # 卖出网格触发
            return GridSignal(
                signal_type='sell',
                price=level.price,
                quantity=level.quantity,
                grid_level=level_index,
                confidence=1.0,
                reason=f"卖出网格触发，价格{current_price} >= {level.price}",
                timestamp=datetime.now()
            )
        
        return None
    
    def _check_dynamic_adjustment(self, current_price: Decimal) -> Optional[GridSignal]:
        """检查动态调整"""
        # 检查是否需要重新平衡
        time_since_rebalance = datetime.now() - self.last_rebalance_time
        if time_since_rebalance.total_seconds() < self.config.rebalance_interval:
            return None
        
        # 检查价格偏离中心价格的程度
        if self.config.center_price:
            price_deviation = abs(current_price - self.config.center_price) / self.config.center_price
            if price_deviation > self.config.adjustment_threshold:
                return GridSignal(
                    signal_type='adjust',
                    price=current_price,
                    quantity=Decimal('0'),
                    grid_level=-1,
                    confidence=0.8,
                    reason=f"价格偏离中心价格{price_deviation:.2%}，需要重新平衡",
                    timestamp=datetime.now()
                )
        
        return None
    
    def _check_risk_control(self, current_price: Decimal) -> Optional[GridSignal]:
        """检查风险控制"""
        # 检查止损
        if self.config.stop_loss_price and current_price <= self.config.stop_loss_price:
            return GridSignal(
                signal_type='sell',
                price=current_price,
                quantity=abs(self.state.total_position),
                grid_level=-1,
                confidence=1.0,
                reason=f"止损触发，价格{current_price} <= {self.config.stop_loss_price}",
                timestamp=datetime.now()
            )
        
        # 检查止盈
        if self.config.take_profit_price and current_price >= self.config.take_profit_price:
            return GridSignal(
                signal_type='sell',
                price=current_price,
                quantity=abs(self.state.total_position),
                grid_level=-1,
                confidence=1.0,
                reason=f"止盈触发，价格{current_price} >= {self.config.take_profit_price}",
                timestamp=datetime.now()
            )
        
        # 检查最大回撤
        if self.state.total_pnl < 0:
            current_drawdown = abs(self.state.total_pnl) / self.config.total_capital
            if current_drawdown > self.config.max_drawdown:
                return GridSignal(
                    signal_type='sell',
                    price=current_price,
                    quantity=abs(self.state.total_position),
                    grid_level=-1,
                    confidence=1.0,
                    reason=f"最大回撤触发，当前回撤{current_drawdown:.2%}",
                    timestamp=datetime.now()
                )
        
        return None
    
    async def execute_signal(self, signal: GridSignal) -> GridTradingResult:
        """执行交易信号"""
        try:
            # 风险检查
            if not await self._risk_check(signal):
                return GridTradingResult(
                    success=False,
                    message="信号未通过风险检查",
                    signal=signal,
                    error="风险检查失败"
                )
            
            # 创建订单
            order = await self._create_order(signal)
            if not order:
                return GridTradingResult(
                    success=False,
                    message="创建订单失败",
                    signal=signal,
                    error="订单创建失败"
                )
            
            # 执行订单
            success = await self._execute_order(order)
            if not success:
                return GridTradingResult(
                    success=False,
                    message="订单执行失败",
                    signal=signal,
                    order=order,
                    error="订单执行失败"
                )
            
            # 更新状态
            await self._update_state_after_trade(signal, order)
            
            return GridTradingResult(
                success=True,
                message="交易执行成功",
                signal=signal,
                order=order
            )
            
        except Exception as e:
            logger.error(f"执行信号失败: {e}")
            return GridTradingResult(
                success=False,
                message=f"执行信号失败: {e}",
                signal=signal,
                error=str(e)
            )
    
    async def _risk_check(self, signal: GridSignal) -> bool:
        """风险检查"""
        try:
            # 检查仓位限制
            if signal.signal_type == 'buy':
                new_position = self.state.total_position + signal.quantity
                if abs(new_position) > self.config.max_position:
                    logger.warning(f"买入信号被拒绝：超过最大仓位限制")
                    return False
            
            # 检查资金充足性
            required_capital = signal.price * signal.quantity
            available_capital = self.config.get_effective_capital() - abs(self.state.total_position) * signal.price
            if required_capital > available_capital:
                logger.warning(f"买入信号被拒绝：资金不足")
                return False
            
            # 检查风险管理
            if not self.risk_manager.check_signal_risk(signal, self.state.total_position):
                logger.warning(f"信号被风险管理器拒绝")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"风险检查失败: {e}")
            return False
    
    async def _create_order(self, signal: GridSignal) -> Optional[Order]:
        """创建订单"""
        try:
            if signal.signal_type == 'buy':
                order = self.order_manager.create_market_order(
                    symbol=self.config.symbol,
                    side=OrderSide.BUY,
                    quantity=float(signal.quantity)
                )
            elif signal.signal_type == 'sell':
                order = self.order_manager.create_market_order(
                    symbol=self.config.symbol,
                    side=OrderSide.SELL,
                    quantity=float(signal.quantity)
                )
            else:
                logger.warning(f"未知信号类型: {signal.signal_type}")
                return None
            
            return order
            
        except Exception as e:
            logger.error(f"创建订单失败: {e}")
            return None
    
    async def _execute_order(self, order: Order) -> bool:
        """执行订单"""
        try:
            # 执行市价单
            success = self.order_manager.execute_market_order(
                order=order,
                current_price=float(self.state.current_price),
                commission_rate=float(self.config.commission_rate),
                slippage=float(self.config.slippage)
            )
            
            return success
            
        except Exception as e:
            logger.error(f"执行订单失败: {e}")
            return False
    
    async def _update_state_after_trade(self, signal: GridSignal, order: Order):
        """交易后更新状态"""
        try:
            # 更新持仓
            if signal.signal_type == 'buy':
                self.state.total_position += signal.quantity
            elif signal.signal_type == 'sell':
                self.state.total_position -= signal.quantity
            
            # 更新手续费
            self.state.total_commission += order.commission
            
            # 更新交易统计
            self.total_trades += 1
            if order.pnl and order.pnl > 0:
                self.winning_trades += 1
            elif order.pnl and order.pnl < 0:
                self.losing_trades += 1
            
            # 更新盈亏
            self.state.add_trade(
                quantity=signal.quantity,
                price=Decimal(str(order.avg_fill_price)),
                commission=Decimal(str(order.commission))
            )
            
            # 更新网格状态
            if signal.grid_level >= 0 and signal.grid_level < len(self.grid_levels):
                self.grid_levels[signal.grid_level].is_active = False
                self.grid_levels[signal.grid_level].filled_quantity += signal.quantity
                self.grid_levels[signal.grid_level].avg_fill_price = order.avg_fill_price
            
            # 更新峰值权益
            current_equity = self.config.total_capital + self.state.total_pnl
            if current_equity > self.peak_equity:
                self.peak_equity = current_equity
            
            # 更新最大回撤
            if current_equity < self.peak_equity:
                current_drawdown = (self.peak_equity - current_equity) / self.peak_equity
                if current_drawdown > self.max_drawdown:
                    self.max_drawdown = current_drawdown
            
            # 更新最后更新时间
            self.state.last_update_time = datetime.now().isoformat()
            
            logger.info(f"交易状态更新完成: 持仓={self.state.total_position}, 盈亏={self.state.total_pnl}")
            
        except Exception as e:
            logger.error(f"更新交易状态失败: {e}")
    
    async def rebalance_grid(self, current_price: Decimal) -> bool:
        """重新平衡网格"""
        try:
            logger.info(f"开始重新平衡网格，当前价格: {current_price}")
            
            # 更新中心价格
            self.config.center_price = current_price
            
            # 重新计算网格
            new_grid_levels = self._calculate_grid_levels(current_price)
            
            # 更新网格状态
            self.grid_levels = new_grid_levels
            self.state.grid_levels = new_grid_levels
            
            # 更新重新平衡时间
            self.last_rebalance_time = datetime.now()
            
            logger.info(f"网格重新平衡完成，新网格数量: {len(self.grid_levels)}")
            return True
            
        except Exception as e:
            logger.error(f"重新平衡网格失败: {e}")
            return False
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        
        return {
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': win_rate,
            'total_pnl': float(self.state.total_pnl),
            'realized_pnl': float(self.state.realized_pnl),
            'unrealized_pnl': float(self.state.unrealized_pnl),
            'total_commission': float(self.state.total_commission),
            'max_drawdown': float(self.max_drawdown),
            'current_position': float(self.state.total_position),
            'active_grids': len([g for g in self.grid_levels if g.is_active]),
            'total_grids': len(self.grid_levels)
        }
    
    def get_grid_status(self) -> List[Dict[str, Any]]:
        """获取网格状态"""
        status = []
        for i, level in enumerate(self.grid_levels):
            status.append({
                'level': i,
                'price': float(level.price),
                'quantity': float(level.quantity),
                'order_type': level.order_type,
                'is_active': level.is_active,
                'filled_quantity': float(level.filled_quantity),
                'avg_fill_price': float(level.avg_fill_price)
            })
        return status
    
    async def stop(self):
        """停止策略"""
        self.is_running = False
        logger.info("网格交易策略已停止")
    
    async def start(self):
        """启动策略"""
        self.is_running = True
        logger.info("网格交易策略已启动")
