"""
回测引擎 - 使用历史数据验证策略效果
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import asyncio
from enum import Enum, auto
import json

from ..data.multi_timeframe_manager import MultiTimeframeManager, OHLCVData
from ..strategies.signal_fusion_engine import SignalFusionEngine, FusedSignal, TradingSignal
from ..config.settings import BacktestConfig, StrategyConfig, TimeframeConfig
from ..execution import ExecutionEngine, global_execution_engine
from ..risk import RiskManager, PositionSizer, global_risk_manager, global_position_sizer

logger = logging.getLogger(__name__)


class TradeDirection(Enum):
    """交易方向"""
    LONG = auto()
    SHORT = auto()


@dataclass
class Trade:
    """交易记录"""
    id: str
    symbol: str
    direction: TradeDirection
    entry_price: float
    entry_time: datetime
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    quantity: float = 0.0
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    signal_strength: Optional[float] = None
    signal_confidence: Optional[float] = None
    strategy_type: Optional[str] = None


@dataclass
class BacktestResult:
    """回测结果"""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    total_return: float
    max_drawdown: float
    sharpe_ratio: Optional[float]
    sortino_ratio: Optional[float]
    calmar_ratio: Optional[float]
    average_trade_pnl: float
    average_win: float
    average_loss: float
    profit_factor: float
    trades: List[Trade]
    equity_curve: pd.Series
    drawdown_curve: pd.Series
    daily_returns: pd.Series
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float


class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.strategy_config = StrategyConfig()
        self.signal_engine = SignalFusionEngine(self.strategy_config)
        
        # 初始化多时间框架管理器
        timeframe_configs = [
            TimeframeConfig(interval=tf, lookback_period=config.lookback_period)
            for tf in config.timeframes
        ]
        self.data_manager = MultiTimeframeManager(config.symbol, timeframe_configs)
        
        # 回测状态
        self.current_capital = config.initial_capital
        self.equity_curve = []
        self.trades: List[Trade] = []
        self.current_trade: Optional[Trade] = None
        self.timestamps = []
        
        # 初始化执行引擎和风险管理系统
        self.execution_engine = global_execution_engine
        self.risk_manager = global_risk_manager
        self.position_sizer = global_position_sizer
        
        # 配置执行引擎参数
        self.execution_engine.commission_rate = config.commission_rate
        self.execution_engine.slippage = config.slippage
        
    async def initialize(self, historical_data: Dict[str, pd.DataFrame]):
        """初始化回测引擎"""
        await self.data_manager.initialize_data(historical_data)
        logger.info(f"回测引擎初始化完成，初始资金: {self.config.initial_capital}")
    
    async def run_backtest(self, data: Dict[str, pd.DataFrame]) -> BacktestResult:
        """运行回测"""
        await self.initialize(data)
        
        # 获取主要时间框架数据
        main_timeframe = self.config.timeframes[0]
        main_data = data[main_timeframe]
        
        logger.info(f"开始回测，数据长度: {len(main_data)}")
        
        for i, (timestamp, row) in enumerate(main_data.iterrows()):
            # 更新所有时间框架数据
            await self._update_all_timeframes(timestamp, row, data)
            
            # 生成交易信号
            signal = await self._generate_signal()
            
            # 执行交易逻辑
            await self._execute_trading_logic(signal, timestamp, row['close'])
            
            # 更新权益曲线
            self._update_equity_curve(timestamp)
            
            # 记录时间戳
            self.timestamps.append(timestamp)
            
            # 进度日志
            if (i + 1) % 1000 == 0:
                logger.info(f"回测进度: {i + 1}/{len(main_data)}")
        
        # 平仓所有未平仓交易
        if self.current_trade:
            await self._close_trade(self.timestamps[-1], main_data.iloc[-1]['close'])
        
        # 计算回测结果
        result = self._calculate_results()
        
        logger.info(f"回测完成，最终资金: {self.current_capital:.2f}")
        return result
    
    async def _update_all_timeframes(self, timestamp: datetime, current_row: pd.Series, 
                                   all_data: Dict[str, pd.DataFrame]):
        """更新所有时间框架数据"""
        for timeframe, df in all_data.items():
            # 找到当前时间戳对应的数据
            timeframe_data = df[df.index <= timestamp]
            if not timeframe_data.empty:
                latest_candle = timeframe_data.iloc[-1]
                candle_dict = {
                    'timestamp': timestamp.timestamp() * 1000,
                    'open': latest_candle['open'],
                    'high': latest_candle['high'],
                    'low': latest_candle['low'],
                    'close': latest_candle['close'],
                    'volume': latest_candle.get('volume', 0)
                }
                await self.data_manager.update_candle(timeframe, candle_dict)
    
    async def _generate_signal(self) -> Optional[FusedSignal]:
        """生成交易信号"""
        try:
            multi_timeframe_data = self.data_manager.get_all_timeframes_data()
            if not multi_timeframe_data:
                return None
            
            signal = await self.signal_engine.generate_signals(multi_timeframe_data)
            return signal
        except Exception as e:
            logger.error(f"生成信号错误: {e}")
            return None
    
    async def _execute_trading_logic(self, signal: Optional[FusedSignal], 
                                   timestamp: datetime, current_price: float):
        """执行交易逻辑"""
        if not signal:
            return
        
        # 检查是否有未平仓交易
        if self.current_trade:
            # 检查止损止盈
            if await self._check_exit_conditions(current_price, timestamp):
                return
            
            # 持有中的交易不执行新信号
            return
        
        # 执行开仓逻辑
        if signal.final_signal in [TradingSignal.STRONG_BUY, TradingSignal.BUY]:
            await self._open_trade(TradeDirection.LONG, timestamp, current_price, signal)
        elif signal.final_signal in [TradingSignal.STRONG_SELL, TradingSignal.SELL]:
            await self._open_trade(TradeDirection.SHORT, timestamp, current_price, signal)
    
    async def _open_trade(self, direction: TradeDirection, timestamp: datetime, 
                         price: float, signal: FusedSignal):
        """开仓"""
        # 使用风险管理系统计算仓位大小和止损止盈
        risk_config = RiskConfig(
            risk_per_trade=self.config.risk_per_trade,
            max_position_size=self.config.max_position_size,
            stop_loss_atr_multiple=self.config.stop_loss_atr_multiple,
            take_profit_atr_multiple=self.config.take_profit_atr_multiple,
            stop_loss_percent=self.config.stop_loss_percent,
            take_profit_percent=self.config.take_profit_percent
        )
        
        # 计算仓位大小
        position_size = self.position_sizer.calculate_position_size(
            price=price,
            capital=self.current_capital,
            risk_config=risk_config
        )
        
        if position_size <= 0:
            return
        
        # 计算止损止盈价格
        stop_loss, take_profit = self.risk_manager.calculate_stop_loss_take_profit(
            direction=direction,
            entry_price=price,
            risk_config=risk_config
        )
        
        # 创建交易记录
        trade = Trade(
            id=f"trade_{len(self.trades) + 1}",
            symbol=self.config.symbol,
            direction=direction,
            entry_price=price,
            entry_time=timestamp,
            quantity=position_size,
            signal_strength=signal.signal_strength,
            signal_confidence=signal.confidence,
            strategy_type=str(signal.strategy_weights),
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        # 使用执行引擎执行订单
        order_side = OrderSide.BUY if direction == TradeDirection.LONG else OrderSide.SELL
        order = self.execution_engine.create_market_order(
            symbol=self.config.symbol,
            side=order_side,
            quantity=position_size,
            price=price
        )
        
        # 执行订单
        executed_order = self.execution_engine.execute_order(order)
        
        if executed_order.status == OrderStatus.FILLED:
            self.current_trade = trade
            self.trades.append(trade)
            logger.info(f"开仓成功: {direction.name} {position_size:.4f} @ {executed_order.avg_price:.2f}")
        else:
            logger.warning(f"开仓失败: {executed_order.status.name}")
    
    async def _close_trade(self, timestamp: datetime, price: float):
        """平仓"""
        if not self.current_trade:
            return
        
        trade = self.current_trade
        
        # 使用执行引擎执行平仓订单
        order_side = OrderSide.SELL if trade.direction == TradeDirection.LONG else OrderSide.BUY
        order = self.execution_engine.create_market_order(
            symbol=self.config.symbol,
            side=order_side,
            quantity=trade.quantity,
            price=price
        )
        
        # 执行订单
        executed_order = self.execution_engine.execute_order(order)
        
        if executed_order.status == OrderStatus.FILLED:
            trade.exit_price = executed_order.avg_price
            trade.exit_time = timestamp
            
            # 计算盈亏（考虑手续费和滑点）
            if trade.direction == TradeDirection.LONG:
                trade.pnl = (executed_order.avg_price - trade.entry_price) * trade.quantity
            else:
                trade.pnl = (trade.entry_price - executed_order.avg_price) * trade.quantity
            
            trade.pnl_percent = (trade.pnl / (trade.entry_price * trade.quantity)) * 100
            
            # 更新资金
            self.current_capital += trade.pnl
            
            logger.info(f"平仓成功: PNL {trade.pnl:.2f} ({trade.pnl_percent:.2f}%)")
            self.current_trade = None
        else:
            logger.warning(f"平仓失败: {executed_order.status.name}")
    
    async def _check_exit_conditions(self, current_price: float, timestamp: datetime) -> bool:
        """检查退出条件"""
        if not self.current_trade:
            return False
        
        trade = self.current_trade
        
        # 检查止损
        if trade.stop_loss and self._is_stop_loss_hit(trade, current_price):
            await self._close_trade(timestamp, current_price)
            return True
        
        # 检查止盈
        if trade.take_profit and self._is_take_profit_hit(trade, current_price):
            await self._close_trade(timestamp, current_price)
            return True
        
        return False
    
    def _is_stop_loss_hit(self, trade: Trade, current_price: float) -> bool:
        """检查是否触发止损"""
        if trade.direction == TradeDirection.LONG:
            return current_price <= trade.stop_loss
        else:
            return current_price >= trade.stop_loss
    
    def _is_take_profit_hit(self, trade: Trade, current_price: float) -> bool:
        """检查是否触发止盈"""
        if trade.direction == TradeDirection.LONG:
            return current_price >= trade.take_profit
        else:
            return current_price <= trade.take_profit
    
    def _calculate_position_size(self, price: float) -> float:
        """计算仓位大小（兼容旧版本）"""
        # 使用固定比例的风险管理
        risk_amount = self.current_capital * self.config.risk_per_trade
        position_size = risk_amount / price
        
        # 确保不超过最大仓位限制
        max_position = self.current_capital * self.config.max_position_size / price
        return min(position_size, max_position)
    
    def _calculate_stop_loss_take_profit(self, direction: TradeDirection, price: float, 
                                       signal: FusedSignal) -> Tuple[Optional[float], Optional[float]]:
        """计算止损止盈（兼容旧版本）"""
        if not self.config.use_stop_loss:
            return None, None
        
        # 基于ATR或固定百分比计算止损止盈
        atr = self._get_current_atr()
        if atr:
            if direction == TradeDirection.LONG:
                stop_loss = price - atr * self.config.stop_loss_atr_multiple
                take_profit = price + atr * self.config.take_profit_atr_multiple
            else:
                stop_loss = price + atr * self.config.stop_loss_atr_multiple
                take_profit = price - atr * self.config.take_profit_atr_multiple
        else:
            # 备用：使用固定百分比
            if direction == TradeDirection.LONG:
                stop_loss = price * (1 - self.config.stop_loss_percent)
                take_profit = price * (1 + self.config.take_profit_percent)
            else:
                stop_loss = price * (1 + self.config.stop_loss_percent)
                take_profit = price * (1 - self.config.take_profit_percent)
        
        return stop_loss, take_profit
    
    def _get_current_atr(self) -> Optional[float]:
        """获取当前ATR值"""
        # 从数据管理器获取技术指标
        main_timeframe = self.config.timeframes[0]
        indicators = self.data_manager.calculate_technical_indicators(main_timeframe)
        
        if 'atr' in indicators and len(indicators['atr']) > 0:
            return indicators['atr'][-1]
        return None
    
    def _update_equity_curve(self, timestamp: datetime):
        """更新权益曲线"""
        # 计算当前权益（包括未实现盈亏）
        unrealized_pnl = 0.0
        if self.current_trade:
            current_price = self._get_current_price()
            if current_price and self.current_trade:
                trade = self.current_trade
                if trade.direction == TradeDirection.LONG:
                    unrealized_pnl = (current_price - trade.entry_price) * trade.quantity
                else:
                    unrealized_pnl = (trade.entry_price - current_price) * trade.quantity
        
        total_equity = self.current_capital + unrealized_pnl
        self.equity_curve.append((timestamp, total_equity))
    
    def _get_current_price(self) -> Optional[float]:
        """获取当前价格"""
        main_timeframe = self.config.timeframes[0]
        ohlc_data = self.data_manager.get_ohlc_data(main_timeframe)
        if ohlc_data and len(ohlc_data.close) > 0:
            return ohlc_data.close[-1]
        return None
    
    def _calculate_results(self) -> BacktestResult:
        """计算回测结果"""
        # 计算基本统计
        winning_trades = [t for t in self.trades if t.pnl and t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl and t.pnl <= 0]
        
        total_pnl = sum(t.pnl for t in self.trades if t.pnl)
        total_return = (self.current_capital / self.config.initial_capital - 1) * 100
        
        # 计算权益曲线和回撤
        equity_series = pd.Series(
            [equity for _, equity in self.equity_curve],
            index=pd.DatetimeIndex([ts for ts, _ in self.equity_curve])
        )
        
        drawdown_series = self._calculate_drawdown(equity_series)
        daily_returns = equity_series.pct_change().dropna()
        
        # 计算风险调整收益
        sharpe = self._calculate_sharpe_ratio(daily_returns)
        sortino = self._calculate_sortino_ratio(daily_returns)
        calmar = self._calculate_calmar_ratio(equity_series, drawdown_series)
        
        result = BacktestResult(
            total_trades=len(self.trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            win_rate=len(winning_trades) / len(self.trades) if self.trades else 0,
            total_pnl=total_pnl,
            total_return=total_return,
            max_drawdown=drawdown_series.min(),
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            calmar_ratio=calmar,
            average_trade_pnl=total_pnl / len(self.trades) if self.trades else 0,
            average_win=sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0,
            average_loss=sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0,
            profit_factor=abs(sum(t.pnl for t in winning_trades) / sum(t.pnl for t in losing_trades)) 
                         if losing_trades else float('inf'),
            trades=self.trades,
            equity_curve=equity_series,
            drawdown_curve=drawdown_series,
            daily_returns=daily_returns,
            start_date=self.timestamps[0] if self.timestamps else datetime.now(),
            end_date=self.timestamps[-1] if self.timestamps else datetime.now(),
            initial_capital=self.config.initial_capital,
            final_capital=self.current_capital
        )
        
        return result
    
    def _calculate_drawdown(self, equity_curve: pd.Series) -> pd.Series:
        """计算回撤"""
        rolling_max = equity_curve.expanding().max()
        drawdown = (equity_curve - rolling_max) / rolling_max
        return drawdown
    
    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> Optional[float]:
        """计算夏普比率"""
        if len(returns) < 2:
            return None
        
        excess_returns = returns - risk_free_rate / 252  # 年化无风险利率
        sharpe = excess_returns.mean() / excess_returns.std() * np.sqrt(252)
        return sharpe
    
    def _calculate_sortino_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> Optional[float]:
        """计算索提诺比率"""
        if len(returns) < 2:
            return None
        
        negative_returns = returns[returns < 0]
        if len(negative_returns) == 0:
            return float('inf')
        
        excess_returns = returns - risk_free_rate / 252
        sortino = excess_returns.mean() / negative_returns.std() * np.sqrt(252)
        return sortino
    
    def _calculate_calmar_ratio(self, equity_curve: pd.Series, drawdown_curve: pd.Series) -> Optional[float]:
        """计算卡尔玛比率"""
        if len(equity_curve) < 2:
            return None
        
        total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0] - 1)
        max_drawdown = abs(drawdown_curve.min())
        
        if max_drawdown == 0:
            return float('inf')
        
        calmar = total_return / max_drawdown
        return calmar

    def save_results(self, result: BacktestResult, filename: str):
        """保存回测结果"""
        # 保存详细结果到JSON文件
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
            'initial_capital': result.initial_capital,
            'final_capital': result.final_capital,
            'start_date': result.start_date.isoformat(),
            'end_date': result.end_date.isoformat(),
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
                    'take_profit': trade.take_profit
                }
                for trade in result.trades
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(result_dict, f, indent=2)
        
        logger.info(f"回测结果已保存到: {filename}")