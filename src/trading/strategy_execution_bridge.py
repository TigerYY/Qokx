#!/usr/bin/env python3
"""
策略执行桥接器 - 连接策略引擎与执行引擎
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid
from concurrent.futures import ThreadPoolExecutor

from ..strategies.signal_fusion_engine import SignalFusionEngine, TradingSignal, SignalType
from ..execution.order_execution_engine import OrderExecutionEngine, Order, OrderType, OrderSide, OrderStatus
from ..risk.risk_manager import RiskManager, RiskCheckResult
from ..data.realtime_data_processor import RealtimeDataProcessor, TickData
from ..utils.position_manager import PositionManager, Position
from ..config.settings import TradingConfig

logger = logging.getLogger(__name__)


class BridgeStatus(Enum):
    """桥接器状态"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class SignalExecutionRequest:
    """信号执行请求"""
    signal_id: str
    symbol: str
    signal: TradingSignal
    timestamp: datetime
    current_price: float
    position_size: float
    risk_params: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """执行结果"""
    request_id: str
    success: bool
    orders: List[Order] = field(default_factory=list)
    error_message: Optional[str] = None
    execution_time: Optional[datetime] = None
    slippage: float = 0.0
    fees: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BridgeMetrics:
    """桥接器指标"""
    total_signals_received: int = 0
    total_signals_executed: int = 0
    total_signals_rejected: int = 0
    total_orders_placed: int = 0
    total_orders_filled: int = 0
    average_execution_time_ms: float = 0.0
    success_rate: float = 0.0
    total_slippage: float = 0.0
    total_fees: float = 0.0
    last_signal_time: Optional[datetime] = None
    last_execution_time: Optional[datetime] = None


class StrategyExecutionBridge:
    """策略执行桥接器"""
    
    def __init__(self,
                 strategy_engine: SignalFusionEngine,
                 execution_engine: OrderExecutionEngine,
                 risk_manager: RiskManager,
                 position_manager: PositionManager,
                 data_processor: RealtimeDataProcessor,
                 config: TradingConfig):
        
        self.strategy_engine = strategy_engine
        self.execution_engine = execution_engine
        self.risk_manager = risk_manager
        self.position_manager = position_manager
        self.data_processor = data_processor
        self.config = config
        
        # 状态管理
        self.status = BridgeStatus.IDLE
        self.is_running = False
        
        # 执行队列
        self.signal_queue = asyncio.Queue(maxsize=1000)
        self.execution_tasks = []
        
        # 缓存和映射
        self.pending_requests: Dict[str, SignalExecutionRequest] = {}
        self.execution_history: List[ExecutionResult] = []
        self.signal_order_mapping: Dict[str, List[str]] = {}  # signal_id -> order_ids
        
        # 指标统计
        self.metrics = BridgeMetrics()
        
        # 回调函数
        self.signal_callbacks: List[Callable] = []
        self.execution_callbacks: List[Callable] = []
        self.error_callbacks: List[Callable] = []
        
        # 执行参数
        self.max_concurrent_executions = config.max_concurrent_orders or 5
        self.execution_timeout = config.execution_timeout or 30.0
        self.retry_attempts = config.retry_attempts or 3
        
        logger.info("策略执行桥接器初始化完成")
    
    async def start(self) -> bool:
        """启动桥接器"""
        try:
            if self.is_running:
                logger.warning("桥接器已在运行中")
                return False
            
            logger.info("启动策略执行桥接器...")
            
            # 注册数据回调
            self.data_processor.add_tick_callback(self._on_price_update)
            
            # 注册策略信号回调
            self.strategy_engine.add_signal_callback(self._on_signal_generated)
            
            # 注册执行引擎回调
            self.execution_engine.add_order_callback(self._on_order_update)
            
            # 启动执行任务
            await self._start_execution_tasks()
            
            self.is_running = True
            self.status = BridgeStatus.RUNNING
            
            logger.info("策略执行桥接器启动成功")
            return True
            
        except Exception as e:
            logger.error(f"启动桥接器失败: {e}")
            self.status = BridgeStatus.ERROR
            return False
    
    async def stop(self) -> bool:
        """停止桥接器"""
        try:
            if not self.is_running:
                return True
            
            logger.info("停止策略执行桥接器...")
            
            self.is_running = False
            self.status = BridgeStatus.STOPPED
            
            # 停止执行任务
            for task in self.execution_tasks:
                task.cancel()
            
            # 等待队列清空
            await self._wait_for_queue_empty(timeout=10.0)
            
            logger.info("策略执行桥接器已停止")
            return True
            
        except Exception as e:
            logger.error(f"停止桥接器失败: {e}")
            return False
    
    async def pause(self):
        """暂停桥接器"""
        if self.status == BridgeStatus.RUNNING:
            self.status = BridgeStatus.PAUSED
            logger.info("策略执行桥接器已暂停")
    
    async def resume(self):
        """恢复桥接器"""
        if self.status == BridgeStatus.PAUSED:
            self.status = BridgeStatus.RUNNING
            logger.info("策略执行桥接器已恢复")
    
    async def _start_execution_tasks(self):
        """启动执行任务"""
        # 信号处理任务
        for i in range(self.max_concurrent_executions):
            task = asyncio.create_task(self._signal_processing_worker(f"worker-{i}"))
            self.execution_tasks.append(task)
        
        # 监控任务
        self.execution_tasks.append(
            asyncio.create_task(self._monitoring_task())
        )
        
        # 清理任务
        self.execution_tasks.append(
            asyncio.create_task(self._cleanup_task())
        )
    
    async def _on_signal_generated(self, signal_data: Dict[str, Any]):
        """处理策略信号生成"""
        try:
            symbol = signal_data['symbol']
            signal = signal_data['signal']
            
            # 获取当前价格
            current_tick = self.data_processor.get_latest_tick(symbol)
            if not current_tick:
                logger.warning(f"无法获取 {symbol} 的当前价格，跳过信号执行")
                return
            
            # 获取当前仓位
            current_position = await self.position_manager.get_position(symbol)
            position_size = current_position.size if current_position else 0.0
            
            # 创建执行请求
            request = SignalExecutionRequest(
                signal_id=str(uuid.uuid4()),
                symbol=symbol,
                signal=signal,
                timestamp=datetime.now(),
                current_price=current_tick.price,
                position_size=position_size,
                metadata=signal_data.get('metadata', {})
            )
            
            # 加入执行队列
            await self.signal_queue.put(request)
            
            # 更新指标
            self.metrics.total_signals_received += 1
            self.metrics.last_signal_time = request.timestamp
            
            # 触发回调
            await self._trigger_callbacks(self.signal_callbacks, request)
            
            logger.info(f"接收到交易信号: {symbol} {signal.signal_type.value} 强度:{signal.strength:.3f}")
            
        except Exception as e:
            logger.error(f"处理信号生成失败: {e}")
            await self._trigger_callbacks(self.error_callbacks, {'error': str(e), 'context': 'signal_generation'})
    
    async def _on_price_update(self, tick_data: TickData):
        """处理价格更新"""
        try:
            # 检查是否有待执行的订单需要价格更新
            symbol = tick_data.symbol
            
            # 更新风险管理器的价格信息
            await self.risk_manager.update_market_price(symbol, tick_data.price)
            
            # 检查止损止盈触发
            await self._check_stop_loss_take_profit(symbol, tick_data.price)
            
        except Exception as e:
            logger.error(f"处理价格更新失败: {e}")
    
    async def _on_order_update(self, order: Order):
        """处理订单状态更新"""
        try:
            # 更新执行结果
            await self._update_execution_result(order)
            
            # 更新仓位
            if order.status == OrderStatus.FILLED:
                await self.position_manager.update_position_from_order(order)
                self.metrics.total_orders_filled += 1
            
            # 触发回调
            await self._trigger_callbacks(self.execution_callbacks, order)
            
        except Exception as e:
            logger.error(f"处理订单更新失败: {e}")
    
    async def _signal_processing_worker(self, worker_id: str):
        """信号处理工作线程"""
        logger.info(f"启动信号处理工作线程: {worker_id}")
        
        while self.is_running:
            try:
                # 获取信号请求
                request = await asyncio.wait_for(
                    self.signal_queue.get(), 
                    timeout=1.0
                )
                
                # 检查桥接器状态
                if self.status != BridgeStatus.RUNNING:
                    await self.signal_queue.put(request)  # 放回队列
                    await asyncio.sleep(0.1)
                    continue
                
                # 处理信号执行
                await self._process_signal_execution(request)
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"工作线程 {worker_id} 处理信号失败: {e}")
                await asyncio.sleep(1)
        
        logger.info(f"信号处理工作线程 {worker_id} 已停止")
    
    async def _process_signal_execution(self, request: SignalExecutionRequest):
        """处理信号执行"""
        start_time = datetime.now()
        
        try:
            # 添加到待处理请求
            self.pending_requests[request.signal_id] = request
            
            logger.info(f"开始处理信号执行: {request.symbol} {request.signal.signal_type.value}")
            
            # 1. 风险检查
            risk_result = await self._perform_risk_check(request)
            if not risk_result.approved:
                await self._handle_execution_rejection(request, risk_result.reason)
                return
            
            # 2. 计算订单参数
            order_params = await self._calculate_order_parameters(request, risk_result)
            if not order_params:
                await self._handle_execution_rejection(request, "无法计算订单参数")
                return
            
            # 3. 生成订单
            orders = await self._generate_orders(request, order_params)
            if not orders:
                await self._handle_execution_rejection(request, "无法生成订单")
                return
            
            # 4. 执行订单
            execution_result = await self._execute_orders(request, orders)
            
            # 5. 记录执行结果
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            execution_result.execution_time = datetime.now()
            
            # 更新指标
            self._update_execution_metrics(execution_result, execution_time)
            
            # 保存执行历史
            self.execution_history.append(execution_result)
            
            # 触发回调
            await self._trigger_callbacks(self.execution_callbacks, execution_result)
            
            logger.info(f"信号执行完成: {request.symbol} 耗时:{execution_time:.1f}ms")
            
        except Exception as e:
            logger.error(f"信号执行失败: {e}")
            await self._handle_execution_error(request, str(e))
        
        finally:
            # 清理待处理请求
            self.pending_requests.pop(request.signal_id, None)
    
    async def _perform_risk_check(self, request: SignalExecutionRequest) -> RiskCheckResult:
        """执行风险检查"""
        try:
            # 准备风险检查参数
            risk_params = {
                'symbol': request.symbol,
                'signal_type': request.signal.signal_type,
                'signal_strength': request.signal.strength,
                'current_price': request.current_price,
                'current_position': request.position_size,
                'timestamp': request.timestamp
            }
            
            # 执行风险检查
            result = await self.risk_manager.check_trading_risk(
                symbol=request.symbol,
                side=OrderSide.BUY if request.signal.signal_type == SignalType.BUY else OrderSide.SELL,
                size=abs(request.signal.strength),  # 临时使用信号强度作为大小
                price=request.current_price,
                metadata=risk_params
            )
            
            return result
            
        except Exception as e:
            logger.error(f"风险检查失败: {e}")
            return RiskCheckResult(
                approved=False,
                reason=f"风险检查异常: {str(e)}",
                max_position_size=0.0
            )
    
    async def _calculate_order_parameters(self, 
                                        request: SignalExecutionRequest, 
                                        risk_result: RiskCheckResult) -> Optional[Dict[str, Any]]:
        """计算订单参数"""
        try:
            signal = request.signal
            
            # 确定交易方向
            if signal.signal_type == SignalType.BUY:
                side = OrderSide.BUY
            elif signal.signal_type == SignalType.SELL:
                side = OrderSide.SELL
            else:  # HOLD
                return None
            
            # 计算订单大小
            base_size = self._calculate_position_size(request, risk_result)
            if base_size <= 0:
                return None
            
            # 应用信号强度调整
            adjusted_size = base_size * min(signal.strength, 1.0)
            
            # 确保不超过风险限制
            final_size = min(adjusted_size, risk_result.max_position_size)
            
            # 计算价格
            entry_price = self._calculate_entry_price(request, side)
            
            # 计算止损止盈
            stop_loss, take_profit = self._calculate_stop_levels(request, side, entry_price)
            
            return {
                'side': side,
                'size': final_size,
                'price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'order_type': self._determine_order_type(request),
                'time_in_force': 'GTC'  # Good Till Cancelled
            }
            
        except Exception as e:
            logger.error(f"计算订单参数失败: {e}")
            return None
    
    def _calculate_position_size(self, 
                               request: SignalExecutionRequest, 
                               risk_result: RiskCheckResult) -> float:
        """计算仓位大小"""
        try:
            # 基础仓位大小（基于账户资金的百分比）
            account_balance = self.position_manager.get_total_balance()
            risk_per_trade = self.config.risk_per_trade or 0.02  # 默认2%
            
            base_risk_amount = account_balance * risk_per_trade
            
            # 基于价格计算基础仓位
            base_position = base_risk_amount / request.current_price
            
            # 应用最大仓位限制
            max_position = risk_result.max_position_size
            
            return min(base_position, max_position)
            
        except Exception as e:
            logger.error(f"计算仓位大小失败: {e}")
            return 0.0
    
    def _calculate_entry_price(self, request: SignalExecutionRequest, side: OrderSide) -> float:
        """计算入场价格"""
        current_price = request.current_price
        
        # 获取最新订单簿数据
        orderbook = self.data_processor.get_latest_orderbook(request.symbol)
        
        if orderbook and orderbook.bids and orderbook.asks:
            if side == OrderSide.BUY:
                # 买入时使用ask价格或稍高价格
                best_ask = orderbook.asks[0][0]
                return min(best_ask * 1.001, current_price * 1.002)  # 最多溢价0.2%
            else:
                # 卖出时使用bid价格或稍低价格
                best_bid = orderbook.bids[0][0]
                return max(best_bid * 0.999, current_price * 0.998)  # 最多折价0.2%
        
        # 如果没有订单簿数据，使用当前价格
        return current_price
    
    def _calculate_stop_levels(self, 
                             request: SignalExecutionRequest, 
                             side: OrderSide, 
                             entry_price: float) -> Tuple[Optional[float], Optional[float]]:
        """计算止损止盈价格"""
        try:
            # 从配置获取止损止盈比例
            stop_loss_pct = self.config.default_stop_loss or 0.02  # 默认2%
            take_profit_pct = self.config.default_take_profit or 0.04  # 默认4%
            
            if side == OrderSide.BUY:
                stop_loss = entry_price * (1 - stop_loss_pct)
                take_profit = entry_price * (1 + take_profit_pct)
            else:
                stop_loss = entry_price * (1 + stop_loss_pct)
                take_profit = entry_price * (1 - take_profit_pct)
            
            return stop_loss, take_profit
            
        except Exception as e:
            logger.error(f"计算止损止盈失败: {e}")
            return None, None
    
    def _determine_order_type(self, request: SignalExecutionRequest) -> OrderType:
        """确定订单类型"""
        # 根据信号强度和市场条件确定订单类型
        if request.signal.strength > 0.8:  # 强信号使用市价单
            return OrderType.MARKET
        else:  # 弱信号使用限价单
            return OrderType.LIMIT
    
    async def _generate_orders(self, 
                             request: SignalExecutionRequest, 
                             params: Dict[str, Any]) -> List[Order]:
        """生成订单"""
        try:
            orders = []
            
            # 主订单
            main_order = Order(
                order_id=str(uuid.uuid4()),
                symbol=request.symbol,
                side=params['side'],
                order_type=params['order_type'],
                size=params['size'],
                price=params['price'] if params['order_type'] == OrderType.LIMIT else None,
                time_in_force=params['time_in_force'],
                metadata={
                    'signal_id': request.signal_id,
                    'signal_type': request.signal.signal_type.value,
                    'signal_strength': request.signal.strength
                }
            )
            orders.append(main_order)
            
            # 记录信号订单映射
            self.signal_order_mapping[request.signal_id] = [main_order.order_id]
            
            return orders
            
        except Exception as e:
            logger.error(f"生成订单失败: {e}")
            return []
    
    async def _execute_orders(self, 
                            request: SignalExecutionRequest, 
                            orders: List[Order]) -> ExecutionResult:
        """执行订单"""
        result = ExecutionResult(
            request_id=request.signal_id,
            success=False,
            orders=orders
        )
        
        try:
            executed_orders = []
            
            for order in orders:
                # 提交订单到执行引擎
                success = await self.execution_engine.place_order(order)
                
                if success:
                    executed_orders.append(order)
                    self.metrics.total_orders_placed += 1
                else:
                    result.error_message = f"订单 {order.order_id} 提交失败"
                    break
            
            if len(executed_orders) == len(orders):
                result.success = True
                self.metrics.total_signals_executed += 1
            else:
                self.metrics.total_signals_rejected += 1
            
            result.orders = executed_orders
            
        except Exception as e:
            result.error_message = str(e)
            self.metrics.total_signals_rejected += 1
            logger.error(f"执行订单失败: {e}")
        
        return result
    
    async def _handle_execution_rejection(self, request: SignalExecutionRequest, reason: str):
        """处理执行拒绝"""
        logger.warning(f"信号执行被拒绝: {request.symbol} - {reason}")
        
        result = ExecutionResult(
            request_id=request.signal_id,
            success=False,
            error_message=reason
        )
        
        self.metrics.total_signals_rejected += 1
        self.execution_history.append(result)
        
        await self._trigger_callbacks(self.execution_callbacks, result)
    
    async def _handle_execution_error(self, request: SignalExecutionRequest, error: str):
        """处理执行错误"""
        logger.error(f"信号执行错误: {request.symbol} - {error}")
        
        result = ExecutionResult(
            request_id=request.signal_id,
            success=False,
            error_message=error
        )
        
        self.metrics.total_signals_rejected += 1
        self.execution_history.append(result)
        
        await self._trigger_callbacks(self.error_callbacks, {'request': request, 'error': error})
    
    def _update_execution_metrics(self, result: ExecutionResult, execution_time_ms: float):
        """更新执行指标"""
        # 更新平均执行时间
        total_executions = self.metrics.total_signals_executed + self.metrics.total_signals_rejected
        if total_executions > 0:
            self.metrics.average_execution_time_ms = (
                (self.metrics.average_execution_time_ms * (total_executions - 1) + execution_time_ms) / total_executions
            )
        
        # 更新成功率
        if total_executions > 0:
            self.metrics.success_rate = self.metrics.total_signals_executed / total_executions
        
        # 更新最后执行时间
        self.metrics.last_execution_time = datetime.now()
    
    async def _update_execution_result(self, order: Order):
        """更新执行结果"""
        # 查找对应的执行结果
        signal_id = order.metadata.get('signal_id')
        if not signal_id:
            return
        
        for result in self.execution_history:
            if result.request_id == signal_id:
                # 更新订单状态
                for i, result_order in enumerate(result.orders):
                    if result_order.order_id == order.order_id:
                        result.orders[i] = order
                        break
                
                # 计算滑点和手续费
                if order.status == OrderStatus.FILLED and order.filled_price:
                    expected_price = order.price or order.filled_price
                    slippage = abs(order.filled_price - expected_price) / expected_price
                    result.slippage += slippage
                    
                    if order.fees:
                        result.fees += order.fees
                
                break
    
    async def _check_stop_loss_take_profit(self, symbol: str, current_price: float):
        """检查止损止盈触发"""
        try:
            # 获取当前仓位
            position = await self.position_manager.get_position(symbol)
            if not position or position.size == 0:
                return
            
            # 检查止损
            if position.stop_loss and (
                (position.size > 0 and current_price <= position.stop_loss) or
                (position.size < 0 and current_price >= position.stop_loss)
            ):
                await self._trigger_stop_loss(symbol, position, current_price)
            
            # 检查止盈
            if position.take_profit and (
                (position.size > 0 and current_price >= position.take_profit) or
                (position.size < 0 and current_price <= position.take_profit)
            ):
                await self._trigger_take_profit(symbol, position, current_price)
                
        except Exception as e:
            logger.error(f"检查止损止盈失败: {e}")
    
    async def _trigger_stop_loss(self, symbol: str, position: Position, current_price: float):
        """触发止损"""
        logger.warning(f"触发止损: {symbol} 当前价格:{current_price} 止损价格:{position.stop_loss}")
        
        # 创建止损订单
        stop_order = Order(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side=OrderSide.SELL if position.size > 0 else OrderSide.BUY,
            order_type=OrderType.MARKET,
            size=abs(position.size),
            metadata={'type': 'stop_loss', 'trigger_price': current_price}
        )
        
        # 提交止损订单
        await self.execution_engine.place_order(stop_order)
    
    async def _trigger_take_profit(self, symbol: str, position: Position, current_price: float):
        """触发止盈"""
        logger.info(f"触发止盈: {symbol} 当前价格:{current_price} 止盈价格:{position.take_profit}")
        
        # 创建止盈订单
        profit_order = Order(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side=OrderSide.SELL if position.size > 0 else OrderSide.BUY,
            order_type=OrderType.MARKET,
            size=abs(position.size),
            metadata={'type': 'take_profit', 'trigger_price': current_price}
        )
        
        # 提交止盈订单
        await self.execution_engine.place_order(profit_order)
    
    async def _monitoring_task(self):
        """监控任务"""
        while self.is_running:
            try:
                # 检查队列状态
                queue_size = self.signal_queue.qsize()
                if queue_size > 100:  # 队列积压过多
                    logger.warning(f"信号队列积压: {queue_size} 个待处理信号")
                
                # 检查执行超时
                await self._check_execution_timeouts()
                
                await asyncio.sleep(5)  # 每5秒检查一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"监控任务错误: {e}")
                await asyncio.sleep(10)
    
    async def _check_execution_timeouts(self):
        """检查执行超时"""
        current_time = datetime.now()
        timeout_threshold = timedelta(seconds=self.execution_timeout)
        
        timeout_requests = []
        
        for signal_id, request in self.pending_requests.items():
            if current_time - request.timestamp > timeout_threshold:
                timeout_requests.append(signal_id)
        
        for signal_id in timeout_requests:
            request = self.pending_requests.pop(signal_id, None)
            if request:
                await self._handle_execution_error(request, "执行超时")
                logger.warning(f"信号执行超时: {request.symbol} {signal_id}")
    
    async def _cleanup_task(self):
        """清理任务"""
        while self.is_running:
            try:
                # 清理执行历史
                cutoff_time = datetime.now() - timedelta(hours=24)
                self.execution_history = [
                    result for result in self.execution_history
                    if result.execution_time and result.execution_time > cutoff_time
                ]
                
                # 清理信号订单映射
                expired_signals = []
                for signal_id, order_ids in self.signal_order_mapping.items():
                    # 检查订单是否都已完成
                    all_completed = True
                    for order_id in order_ids:
                        order = await self.execution_engine.get_order(order_id)
                        if order and order.status not in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED]:
                            all_completed = False
                            break
                    
                    if all_completed:
                        expired_signals.append(signal_id)
                
                for signal_id in expired_signals:
                    self.signal_order_mapping.pop(signal_id, None)
                
                await asyncio.sleep(3600)  # 每小时清理一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"清理任务错误: {e}")
                await asyncio.sleep(1800)  # 出错后30分钟再试
    
    async def _wait_for_queue_empty(self, timeout: float = 10.0):
        """等待队列清空"""
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < timeout:
            if self.signal_queue.empty() and not self.pending_requests:
                return True
            await asyncio.sleep(0.1)
        
        return False
    
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
    
    def add_signal_callback(self, callback: Callable):
        """添加信号回调"""
        self.signal_callbacks.append(callback)
    
    def add_execution_callback(self, callback: Callable):
        """添加执行回调"""
        self.execution_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable):
        """添加错误回调"""
        self.error_callbacks.append(callback)
    
    def get_status(self) -> BridgeStatus:
        """获取桥接器状态"""
        return self.status
    
    def get_metrics(self) -> BridgeMetrics:
        """获取执行指标"""
        return self.metrics
    
    def get_execution_history(self, limit: int = 100) -> List[ExecutionResult]:
        """获取执行历史"""
        return self.execution_history[-limit:]
    
    def get_pending_requests(self) -> Dict[str, SignalExecutionRequest]:
        """获取待处理请求"""
        return self.pending_requests.copy()
    
    async def force_execute_signal(self, 
                                 symbol: str, 
                                 signal: TradingSignal, 
                                 override_risk: bool = False) -> bool:
        """强制执行信号（用于手动交易）"""
        try:
            # 获取当前价格
            current_tick = self.data_processor.get_latest_tick(symbol)
            if not current_tick:
                logger.error(f"无法获取 {symbol} 的当前价格")
                return False
            
            # 创建执行请求
            request = SignalExecutionRequest(
                signal_id=f"manual-{uuid.uuid4()}",
                symbol=symbol,
                signal=signal,
                timestamp=datetime.now(),
                current_price=current_tick.price,
                position_size=0.0,
                metadata={'manual': True, 'override_risk': override_risk}
            )
            
            # 直接处理执行
            await self._process_signal_execution(request)
            return True
            
        except Exception as e:
            logger.error(f"强制执行信号失败: {e}")
            return False


# 全局实例
global_bridge: Optional[StrategyExecutionBridge] = None


def get_strategy_execution_bridge() -> Optional[StrategyExecutionBridge]:
    """获取全局桥接器实例"""
    return global_bridge


def initialize_strategy_execution_bridge(
    strategy_engine: SignalFusionEngine,
    execution_engine: OrderExecutionEngine,
    risk_manager: RiskManager,
    position_manager: PositionManager,
    data_processor: RealtimeDataProcessor,
    config: TradingConfig
) -> StrategyExecutionBridge:
    """初始化全局桥接器"""
    global global_bridge
    global_bridge = StrategyExecutionBridge(
        strategy_engine, execution_engine, risk_manager, 
        position_manager, data_processor, config
    )
    return global_bridge