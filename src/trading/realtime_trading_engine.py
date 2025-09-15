#!/usr/bin/env python3
"""
实时交易引擎 - 整合策略、执行、风险管理的核心交易系统
"""

import asyncio
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum, auto
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor

from ..strategies.signal_fusion_engine import SignalFusionEngine, FusedSignal, TradingSignal
from ..strategies.market_state_detector import MarketStateDetector, MarketRegime
from ..execution.execution_engine import ExecutionEngine
from ..risk.risk_manager import RiskManager
from ..risk.position_sizer import PositionSizer
from ..utils.okx_websocket_client import OKXWebSocketClient
from ..utils.okx_rest_client import OKXRESTClient
from ..data.multi_timeframe_manager import MultiTimeframeManager, OHLCVData
from ..config.settings import TradingConfig, StrategyConfig, RiskConfig

logger = logging.getLogger(__name__)


class TradingStatus(Enum):
    """交易状态枚举"""
    STOPPED = auto()
    STARTING = auto()
    RUNNING = auto()
    PAUSED = auto()
    STOPPING = auto()
    ERROR = auto()


@dataclass
class TradingState:
    """交易状态数据"""
    status: TradingStatus = TradingStatus.STOPPED
    start_time: Optional[datetime] = None
    last_signal_time: Optional[datetime] = None
    last_trade_time: Optional[datetime] = None
    total_trades: int = 0
    current_position: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    account_balance: float = 0.0
    error_message: Optional[str] = None
    last_price: Optional[float] = None
    market_regimes: Dict[str, MarketRegime] = field(default_factory=dict)
    current_signal: Optional[FusedSignal] = None


@dataclass
class TradingMetrics:
    """交易指标"""
    win_rate: float = 0.0
    profit_factor: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    total_return: float = 0.0
    average_trade_duration: timedelta = timedelta()
    signals_generated: int = 0
    signals_executed: int = 0


class RealtimeTradingEngine:
    """实时交易引擎"""
    
    def __init__(self, 
                 config: TradingConfig,
                 okx_client: OKXRESTClient,
                 symbol: str = "BTC-USDT"):
        self.config = config
        self.okx_client = okx_client
        self.symbol = symbol
        
        # 核心组件
        self.signal_engine = SignalFusionEngine(config.strategy_config)
        self.market_detector = MarketStateDetector(config.market_state_config)
        self.execution_engine = ExecutionEngine(
            commission_rate=config.commission_rate,
            slippage=config.slippage
        )
        self.risk_manager = RiskManager(config.risk_config)
        self.position_sizer = PositionSizer(config.position_config)
        
        # 数据管理
        self.data_manager = MultiTimeframeManager(config.timeframe_config)
        self.ws_client = None
        
        # 状态管理
        self.state = TradingState()
        self.metrics = TradingMetrics()
        
        # 异步控制
        self.loop = None
        self.trading_task = None
        self.data_task = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # 回调函数
        self.on_signal_callback: Optional[Callable] = None
        self.on_trade_callback: Optional[Callable] = None
        self.on_error_callback: Optional[Callable] = None
        self.on_state_change_callback: Optional[Callable] = None
        
        # 交易控制
        self._stop_event = asyncio.Event()
        self._pause_event = asyncio.Event()
        
        logger.info(f"实时交易引擎初始化完成 - 交易对: {symbol}")
    
    async def start_trading(self) -> bool:
        """启动实时交易"""
        try:
            if self.state.status != TradingStatus.STOPPED:
                logger.warning("交易引擎已在运行中")
                return False
            
            logger.info("启动实时交易引擎...")
            self._update_status(TradingStatus.STARTING)
            
            # 初始化WebSocket连接
            await self._initialize_websocket()
            
            # 初始化账户信息
            await self._initialize_account()
            
            # 启动数据流
            self.data_task = asyncio.create_task(self._data_stream_loop())
            
            # 启动交易逻辑
            self.trading_task = asyncio.create_task(self._trading_loop())
            
            self.state.start_time = datetime.now()
            self._update_status(TradingStatus.RUNNING)
            
            logger.info("实时交易引擎启动成功")
            return True
            
        except Exception as e:
            logger.error(f"启动交易引擎失败: {e}")
            self._update_status(TradingStatus.ERROR, str(e))
            return False
    
    async def stop_trading(self) -> bool:
        """停止实时交易"""
        try:
            if self.state.status == TradingStatus.STOPPED:
                return True
            
            logger.info("停止实时交易引擎...")
            self._update_status(TradingStatus.STOPPING)
            
            # 设置停止事件
            self._stop_event.set()
            
            # 关闭所有持仓
            if self.state.current_position != 0:
                await self._close_all_positions()
            
            # 停止任务
            if self.trading_task:
                self.trading_task.cancel()
            if self.data_task:
                self.data_task.cancel()
            
            # 关闭WebSocket
            if self.ws_client:
                await self.ws_client.close()
            
            self._update_status(TradingStatus.STOPPED)
            logger.info("实时交易引擎已停止")
            return True
            
        except Exception as e:
            logger.error(f"停止交易引擎失败: {e}")
            self._update_status(TradingStatus.ERROR, str(e))
            return False
    
    async def pause_trading(self):
        """暂停交易"""
        if self.state.status == TradingStatus.RUNNING:
            self._pause_event.set()
            self._update_status(TradingStatus.PAUSED)
            logger.info("交易已暂停")
    
    async def resume_trading(self):
        """恢复交易"""
        if self.state.status == TradingStatus.PAUSED:
            self._pause_event.clear()
            self._update_status(TradingStatus.RUNNING)
            logger.info("交易已恢复")
    
    async def _initialize_websocket(self):
        """初始化WebSocket连接"""
        self.ws_client = OKXWebSocketClient(
            api_key=self.okx_client.api_key,
            secret_key=self.okx_client.secret_key,
            passphrase=self.okx_client.passphrase,
            testnet=self.okx_client.testnet
        )
        
        # 订阅实时数据
        await self.ws_client.subscribe_ticker(self.symbol, self._on_ticker_update)
        await self.ws_client.subscribe_kline(self.symbol, "1m", self._on_kline_update)
        
        logger.info("WebSocket连接已建立")
    
    async def _initialize_account(self):
        """初始化账户信息"""
        try:
            account_info = await self.okx_client.get_account_balance()
            if account_info and 'data' in account_info:
                balance_data = account_info['data'][0]['details'][0]
                self.state.account_balance = float(balance_data['availBal'])
                logger.info(f"账户余额: {self.state.account_balance} USDT")
        except Exception as e:
            logger.error(f"获取账户信息失败: {e}")
            raise
    
    async def _data_stream_loop(self):
        """数据流处理循环"""
        try:
            while not self._stop_event.is_set():
                # 更新多时间框架数据
                await self._update_timeframe_data()
                
                # 等待下一次更新
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            logger.info("数据流任务已取消")
        except Exception as e:
            logger.error(f"数据流处理错误: {e}")
            self._update_status(TradingStatus.ERROR, str(e))
    
    async def _trading_loop(self):
        """主交易循环"""
        try:
            while not self._stop_event.is_set():
                # 检查暂停状态
                if self._pause_event.is_set():
                    await asyncio.sleep(1)
                    continue
                
                # 生成交易信号
                signal = await self._generate_trading_signal()
                
                if signal:
                    self.state.current_signal = signal
                    self.state.last_signal_time = datetime.now()
                    self.metrics.signals_generated += 1
                    
                    # 执行交易逻辑
                    await self._execute_trading_signal(signal)
                    
                    # 触发信号回调
                    if self.on_signal_callback:
                        await self._safe_callback(self.on_signal_callback, signal)
                
                # 更新持仓和PnL
                await self._update_position_status()
                
                # 检查风险管理
                await self._check_risk_management()
                
                # 等待下一次循环
                await asyncio.sleep(self.config.signal_interval)
                
        except asyncio.CancelledError:
            logger.info("交易循环任务已取消")
        except Exception as e:
            logger.error(f"交易循环错误: {e}")
            self._update_status(TradingStatus.ERROR, str(e))
    
    async def _generate_trading_signal(self) -> Optional[FusedSignal]:
        """生成交易信号"""
        try:
            # 获取多时间框架数据
            multi_data = self.data_manager.get_all_timeframe_data()
            
            if not multi_data:
                return None
            
            # 检测市场状态
            market_regimes = {}
            for timeframe, data in multi_data.items():
                regimes = self.market_detector.detect_market_state(data)
                market_regimes[timeframe] = regimes
            
            self.state.market_regimes = market_regimes
            
            # 生成融合信号
            signal = await self.signal_engine.generate_signals(multi_data)
            
            return signal
            
        except Exception as e:
            logger.error(f"生成交易信号失败: {e}")
            return None
    
    async def _execute_trading_signal(self, signal: FusedSignal):
        """执行交易信号"""
        try:
            # 风险检查
            if not self.risk_manager.check_signal_risk(signal, self.state.current_position):
                logger.warning("信号未通过风险检查")
                return
            
            # 计算仓位大小
            position_size = self.position_sizer.calculate_position_size(
                signal=signal,
                account_balance=self.state.account_balance,
                current_price=self.state.last_price
            )
            
            if position_size == 0:
                return
            
            # 执行交易
            if signal.final_signal in [TradingSignal.BUY, TradingSignal.STRONG_BUY]:
                await self._execute_buy_signal(position_size, signal)
            elif signal.final_signal in [TradingSignal.SELL, TradingSignal.STRONG_SELL]:
                await self._execute_sell_signal(position_size, signal)
            
        except Exception as e:
            logger.error(f"执行交易信号失败: {e}")
    
    async def _execute_buy_signal(self, position_size: float, signal: FusedSignal):
        """执行买入信号"""
        try:
            # 计算止损止盈
            stop_loss, take_profit = self._calculate_stop_loss_take_profit(
                'buy', self.state.last_price, signal
            )
            
            # 执行买入
            order = self.execution_engine.execute_buy(
                symbol=self.symbol,
                quantity=position_size,
                current_price=self.state.last_price,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
            if order:
                self.state.total_trades += 1
                self.state.last_trade_time = datetime.now()
                self.metrics.signals_executed += 1
                
                logger.info(f"执行买入订单: {position_size} @ {self.state.last_price}")
                
                # 触发交易回调
                if self.on_trade_callback:
                    await self._safe_callback(self.on_trade_callback, order)
            
        except Exception as e:
            logger.error(f"执行买入失败: {e}")
    
    async def _execute_sell_signal(self, position_size: float, signal: FusedSignal):
        """执行卖出信号"""
        try:
            # 只有在有持仓时才能卖出
            if self.state.current_position <= 0:
                return
            
            # 计算实际卖出数量
            sell_quantity = min(position_size, self.state.current_position)
            
            # 执行卖出
            order = self.execution_engine.execute_sell(
                symbol=self.symbol,
                quantity=sell_quantity,
                current_price=self.state.last_price
            )
            
            if order:
                self.state.total_trades += 1
                self.state.last_trade_time = datetime.now()
                self.metrics.signals_executed += 1
                
                logger.info(f"执行卖出订单: {sell_quantity} @ {self.state.last_price}")
                
                # 触发交易回调
                if self.on_trade_callback:
                    await self._safe_callback(self.on_trade_callback, order)
            
        except Exception as e:
            logger.error(f"执行卖出失败: {e}")
    
    def _calculate_stop_loss_take_profit(self, direction: str, price: float, 
                                       signal: FusedSignal) -> tuple:
        """计算止损止盈价格"""
        atr_multiplier = 2.0
        risk_reward_ratio = 2.0
        
        # 简化的止损止盈计算
        price_change = price * 0.02  # 2%的价格变动
        
        if direction == 'buy':
            stop_loss = price - price_change
            take_profit = price + (price_change * risk_reward_ratio)
        else:
            stop_loss = price + price_change
            take_profit = price - (price_change * risk_reward_ratio)
        
        return stop_loss, take_profit
    
    async def _update_timeframe_data(self):
        """更新多时间框架数据"""
        try:
            # 获取最新K线数据
            kline_data = await self.okx_client.get_kline_data(
                symbol=self.symbol,
                timeframe='1m',
                limit=100
            )
            
            if kline_data and 'data' in kline_data:
                # 更新数据管理器
                await self.data_manager.update_data(self.symbol, kline_data['data'])
            
        except Exception as e:
            logger.error(f"更新时间框架数据失败: {e}")
    
    async def _update_position_status(self):
        """更新持仓状态"""
        try:
            # 更新持仓信息
            position_info = self.execution_engine.get_position_info()
            self.state.current_position = position_info['position_size']
            self.state.unrealized_pnl = position_info['unrealized_pnl']
            self.state.realized_pnl = position_info['realized_pnl']
            
            # 更新未实现盈亏
            if self.state.last_price:
                self.execution_engine.update_unrealized_pnl(self.state.last_price)
            
        except Exception as e:
            logger.error(f"更新持仓状态失败: {e}")
    
    async def _check_risk_management(self):
        """检查风险管理"""
        try:
            # 检查止损止盈
            if self.state.last_price and self.state.current_position != 0:
                orders = self.execution_engine.check_stop_loss_take_profit(
                    self.state.last_price, self.symbol
                )
                
                for order in orders:
                    logger.info(f"触发止损止盈: {order}")
            
            # 检查最大回撤
            if self.risk_manager.check_max_drawdown(self.state.unrealized_pnl):
                logger.warning("触发最大回撤保护")
                await self._close_all_positions()
            
        except Exception as e:
            logger.error(f"风险管理检查失败: {e}")
    
    async def _close_all_positions(self):
        """关闭所有持仓"""
        try:
            if self.state.current_position != 0:
                orders = self.execution_engine.close_all_positions(
                    self.state.last_price, self.symbol
                )
                
                for order in orders:
                    logger.info(f"关闭持仓: {order}")
            
        except Exception as e:
            logger.error(f"关闭持仓失败: {e}")
    
    async def _on_ticker_update(self, data: dict):
        """处理实时价格更新"""
        try:
            if 'data' in data:
                ticker_data = data['data'][0]
                self.state.last_price = float(ticker_data['last'])
        except Exception as e:
            logger.error(f"处理价格更新失败: {e}")
    
    async def _on_kline_update(self, data: dict):
        """处理实时K线更新"""
        try:
            if 'data' in data:
                kline_data = data['data'][0]
                # 更新数据管理器
                await self.data_manager.update_realtime_data(self.symbol, kline_data)
        except Exception as e:
            logger.error(f"处理K线更新失败: {e}")
    
    def _update_status(self, status: TradingStatus, error_msg: str = None):
        """更新交易状态"""
        old_status = self.state.status
        self.state.status = status
        self.state.error_message = error_msg
        
        if old_status != status:
            logger.info(f"交易状态变更: {old_status.name} -> {status.name}")
            
            # 触发状态变更回调
            if self.on_state_change_callback:
                asyncio.create_task(
                    self._safe_callback(self.on_state_change_callback, self.state)
                )
    
    async def _safe_callback(self, callback: Callable, *args):
        """安全执行回调函数"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(*args)
            else:
                callback(*args)
        except Exception as e:
            logger.error(f"回调函数执行失败: {e}")
    
    def get_trading_state(self) -> TradingState:
        """获取交易状态"""
        return self.state
    
    def get_trading_metrics(self) -> TradingMetrics:
        """获取交易指标"""
        # 更新指标
        if self.state.total_trades > 0:
            self.metrics.signals_executed = self.state.total_trades
            
        return self.metrics
    
    def set_callbacks(self, 
                     on_signal: Optional[Callable] = None,
                     on_trade: Optional[Callable] = None,
                     on_error: Optional[Callable] = None,
                     on_state_change: Optional[Callable] = None):
        """设置回调函数"""
        if on_signal:
            self.on_signal_callback = on_signal
        if on_trade:
            self.on_trade_callback = on_trade
        if on_error:
            self.on_error_callback = on_error
        if on_state_change:
            self.on_state_change_callback = on_state_change


# 全局实例
global_trading_engine: Optional[RealtimeTradingEngine] = None


def get_trading_engine() -> Optional[RealtimeTradingEngine]:
    """获取全局交易引擎实例"""
    return global_trading_engine


def initialize_trading_engine(config: TradingConfig, 
                            okx_client: OKXRESTClient, 
                            symbol: str = "BTC-USDT") -> RealtimeTradingEngine:
    """初始化全局交易引擎"""
    global global_trading_engine
    global_trading_engine = RealtimeTradingEngine(config, okx_client, symbol)
    return global_trading_engine