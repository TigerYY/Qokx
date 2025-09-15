"""
执行引擎 - 负责订单的实际执行和交易逻辑
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
import numpy as np
from .order_manager import Order, OrderSide, OrderType, OrderStatus, global_order_manager

logger = logging.getLogger(__name__)


class ExecutionEngine:
    """执行引擎"""
    
    def __init__(self, commission_rate: float = 0.001, slippage: float = 0.0005):
        self.commission_rate = commission_rate
        self.slippage = slippage
        self.order_manager = global_order_manager
        self.position_size = 0.0  # 当前持仓数量
        self.avg_entry_price = 0.0  # 平均入场价格
        self.unrealized_pnl = 0.0  # 未实现盈亏
        self.realized_pnl = 0.0  # 已实现盈亏
        self.total_commission = 0.0  # 总手续费
        self.trade_count = 0  # 交易次数
    
    def calculate_position_size(self, capital: float, current_price: float, risk_per_trade: float = 0.02, 
                               stop_loss_price: Optional[float] = None, atr: Optional[float] = None, 
                               atr_multiplier: float = 2.0) -> float:
        """
        计算合理的仓位大小
        
        Args:
            capital: 可用资金
            current_price: 当前价格
            risk_per_trade: 每笔交易风险比例
            stop_loss_price: 止损价格
            atr: ATR值
            atr_multiplier: ATR倍数
        """
        if stop_loss_price is not None:
            # 基于固定止损计算
            risk_per_share = abs(current_price - stop_loss_price)
        elif atr is not None:
            # 基于ATR计算
            risk_per_share = atr * atr_multiplier
        else:
            # 默认使用2%的价格波动作为风险
            risk_per_share = current_price * 0.02
        
        if risk_per_share <= 0:
            return 0.0
        
        # 计算最大风险金额
        max_risk_amount = capital * risk_per_trade
        
        # 计算仓位大小
        position_size = max_risk_amount / risk_per_share
        
        # 确保不会超过可用资金
        max_position_by_capital = capital / current_price
        position_size = min(position_size, max_position_by_capital)
        
        return round(position_size, 6)  # 保留6位小数
    
    def execute_buy(self, symbol: str, quantity: float, current_price: float, 
                   stop_loss: Optional[float] = None, take_profit: Optional[float] = None) -> Optional[Order]:
        """执行买入操作"""
        try:
            # 创建市价买入单
            order = self.order_manager.create_market_order(symbol, OrderSide.BUY, quantity)
            
            # 执行订单
            success = self.order_manager.execute_market_order(
                order, current_price, self.commission_rate, self.slippage
            )
            
            if success:
                # 更新持仓信息
                self._update_position_after_buy(order.quantity, order.avg_fill_price)
                
                # 创建止损止盈单
                if stop_loss is not None:
                    self.order_manager.create_stop_order(symbol, OrderSide.SELL, quantity, stop_loss)
                
                if take_profit is not None:
                    self.order_manager.create_take_profit_order(symbol, OrderSide.SELL, quantity, take_profit)
                
                self.trade_count += 1
                logger.info(f"买入执行成功: {quantity} {symbol} @ {order.avg_fill_price:.2f}")
                return order
            
        except Exception as e:
            logger.error(f"买入执行失败: {e}")
        
        return None
    
    def execute_sell(self, symbol: str, quantity: float, current_price: float) -> Optional[Order]:
        """执行卖出操作"""
        try:
            # 检查是否有足够的持仓
            if self.position_size < quantity:
                logger.warning(f"卖出数量超过持仓: 持仓 {self.position_size}, 尝试卖出 {quantity}")
                quantity = self.position_size  # 最多卖出全部持仓
            
            if quantity <= 0:
                return None
            
            # 创建市价卖出单
            order = self.order_manager.create_market_order(symbol, OrderSide.SELL, quantity)
            
            # 执行订单
            success = self.order_manager.execute_market_order(
                order, current_price, self.commission_rate, self.slippage
            )
            
            if success:
                # 更新持仓信息
                self._update_position_after_sell(order.quantity, order.avg_fill_price)
                
                self.trade_count += 1
                logger.info(f"卖出执行成功: {quantity} {symbol} @ {order.avg_fill_price:.2f}")
                return order
            
        except Exception as e:
            logger.error(f"卖出执行失败: {e}")
        
        return None
    
    def _update_position_after_buy(self, quantity: float, price: float):
        """买入后更新持仓"""
        total_cost = self.position_size * self.avg_entry_price + quantity * price
        self.position_size += quantity
        
        if self.position_size > 0:
            self.avg_entry_price = total_cost / self.position_size
        else:
            self.avg_entry_price = 0.0
    
    def _update_position_after_sell(self, quantity: float, price: float):
        """卖出后更新持仓"""
        # 计算盈亏
        pnl = quantity * (price - self.avg_entry_price)
        commission = quantity * price * self.commission_rate
        
        self.realized_pnl += pnl - commission
        self.total_commission += commission
        self.position_size -= quantity
        
        # 如果全部卖出，重置平均入场价格
        if self.position_size <= 0:
            self.avg_entry_price = 0.0
            self.position_size = 0.0
    
    def update_unrealized_pnl(self, current_price: float):
        """更新未实现盈亏"""
        if self.position_size > 0:
            self.unrealized_pnl = self.position_size * (current_price - self.avg_entry_price)
        else:
            self.unrealized_pnl = 0.0
    
    def check_stop_loss_take_profit(self, current_price: float, symbol: str) -> List[Order]:
        """检查止损止盈单是否触发"""
        return self.order_manager.check_stop_orders(current_price)
    
    def check_limit_orders(self, current_price: float) -> List[Order]:
        """检查限价单是否触发"""
        return self.order_manager.check_limit_orders(current_price)
    
    def close_all_positions(self, current_price: float, symbol: str) -> List[Order]:
        """平掉所有持仓"""
        orders = []
        
        if self.position_size > 0:
            # 取消所有未成交的止损止盈单
            open_orders = self.order_manager.get_open_orders()
            for order in open_orders:
                if order.symbol == symbol and order.order_type in [OrderType.STOP, OrderType.TAKE_PROFIT]:
                    self.order_manager.cancel_order(order.order_id)
            
            # 市价卖出全部持仓
            sell_order = self.execute_sell(symbol, self.position_size, current_price)
            if sell_order:
                orders.append(sell_order)
        
        return orders
    
    def get_position_info(self) -> Dict:
        """获取持仓信息"""
        return {
            'position_size': self.position_size,
            'avg_entry_price': self.avg_entry_price,
            'unrealized_pnl': self.unrealized_pnl,
            'realized_pnl': self.realized_pnl,
            'total_commission': self.total_commission,
            'trade_count': self.trade_count
        }
    
    def reset(self):
        """重置执行引擎"""
        self.position_size = 0.0
        self.avg_entry_price = 0.0
        self.unrealized_pnl = 0.0
        self.realized_pnl = 0.0
        self.total_commission = 0.0
        self.trade_count = 0
        self.order_manager.clear_orders()
        logger.info("执行引擎已重置")


# 单例模式
global_execution_engine = ExecutionEngine()