"""
订单管理模块 - 负责订单的创建、修改、取消和执行
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum, auto
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """订单类型"""
    MARKET = auto()  # 市价单
    LIMIT = auto()   # 限价单
    STOP = auto()    # 止损单
    TAKE_PROFIT = auto()  # 止盈单
    STOP_LIMIT = auto()   # 止损限价单


class OrderSide(Enum):
    """订单方向"""
    BUY = auto()   # 买入
    SELL = auto()  # 卖出


class OrderStatus(Enum):
    """订单状态"""
    PENDING = auto()    # 等待中
    OPEN = auto()       # 已开仓
    FILLED = auto()     # 已成交
    PARTIALLY_FILLED = auto()  # 部分成交
    CANCELLED = auto()  # 已取消
    REJECTED = auto()   # 已拒绝


@dataclass
class Order:
    """订单数据结构"""
    order_id: str  # 订单ID
    symbol: str    # 交易品种
    order_type: OrderType  # 订单类型
    side: OrderSide  # 订单方向
    quantity: float  # 数量
    price: Optional[float] = None  # 价格（限价单、止损单等）
    stop_price: Optional[float] = None  # 止损价格
    take_profit_price: Optional[float] = None  # 止盈价格
    status: OrderStatus = OrderStatus.PENDING  # 订单状态
    created_at: datetime = field(default_factory=datetime.now)  # 创建时间
    updated_at: datetime = field(default_factory=datetime.now)  # 更新时间
    filled_quantity: float = 0.0  # 已成交数量
    avg_fill_price: float = 0.0  # 平均成交价格
    commission: float = 0.0  # 手续费
    slippage: float = 0.0  # 滑点
    parent_order_id: Optional[str] = None  # 父订单ID（用于止损止盈单）
    
    def __post_init__(self):
        self.updated_at = datetime.now()


class OrderManager:
    """订单管理器"""
    
    def __init__(self):
        self.orders: Dict[str, Order] = {}  # 所有订单
        self.open_orders: List[Order] = []  # 未成交订单
        self.filled_orders: List[Order] = []  # 已成交订单
        self.order_counter = 0  # 订单计数器
    
    def generate_order_id(self) -> str:
        """生成唯一订单ID"""
        self.order_counter += 1
        return f"order_{self.order_counter:08d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def create_market_order(self, symbol: str, side: OrderSide, quantity: float) -> Order:
        """创建市价单"""
        order_id = self.generate_order_id()
        order = Order(
            order_id=order_id,
            symbol=symbol,
            order_type=OrderType.MARKET,
            side=side,
            quantity=quantity
        )
        self.orders[order_id] = order
        self.open_orders.append(order)
        logger.info(f"创建市价单: {order_id}, {side.name}, {quantity} {symbol}")
        return order
    
    def create_limit_order(self, symbol: str, side: OrderSide, quantity: float, price: float) -> Order:
        """创建限价单"""
        order_id = self.generate_order_id()
        order = Order(
            order_id=order_id,
            symbol=symbol,
            order_type=OrderType.LIMIT,
            side=side,
            quantity=quantity,
            price=price
        )
        self.orders[order_id] = order
        self.open_orders.append(order)
        logger.info(f"创建限价单: {order_id}, {side.name}, {quantity} {symbol} @ {price}")
        return order
    
    def create_stop_order(self, symbol: str, side: OrderSide, quantity: float, stop_price: float) -> Order:
        """创建止损单"""
        order_id = self.generate_order_id()
        order = Order(
            order_id=order_id,
            symbol=symbol,
            order_type=OrderType.STOP,
            side=side,
            quantity=quantity,
            stop_price=stop_price
        )
        self.orders[order_id] = order
        self.open_orders.append(order)
        logger.info(f"创建止损单: {order_id}, {side.name}, {quantity} {symbol} @ stop {stop_price}")
        return order
    
    def create_take_profit_order(self, symbol: str, side: OrderSide, quantity: float, take_profit_price: float) -> Order:
        """创建止盈单"""
        order_id = self.generate_order_id()
        order = Order(
            order_id=order_id,
            symbol=symbol,
            order_type=OrderType.TAKE_PROFIT,
            side=side,
            quantity=quantity,
            take_profit_price=take_profit_price
        )
        self.orders[order_id] = order
        self.open_orders.append(order)
        logger.info(f"创建止盈单: {order_id}, {side.name}, {quantity} {symbol} @ tp {take_profit_price}")
        return order
    
    def execute_market_order(self, order: Order, current_price: float, commission_rate: float = 0.001, slippage: float = 0.0005) -> bool:
        """执行市价单"""
        try:
            # 计算滑点影响后的价格
            slippage_amount = current_price * slippage
            if order.side == OrderSide.BUY:
                fill_price = current_price + slippage_amount
            else:
                fill_price = current_price - slippage_amount
            
            # 计算手续费
            commission = order.quantity * fill_price * commission_rate
            
            # 更新订单状态
            order.status = OrderStatus.FILLED
            order.filled_quantity = order.quantity
            order.avg_fill_price = fill_price
            order.commission = commission
            order.slippage = slippage_amount
            order.updated_at = datetime.now()
            
            # 从open_orders移动到filled_orders
            if order in self.open_orders:
                self.open_orders.remove(order)
            self.filled_orders.append(order)
            
            logger.info(f"市价单成交: {order.order_id}, 价格: {fill_price:.2f}, 手续费: {commission:.4f}")
            return True
            
        except Exception as e:
            logger.error(f"执行市价单失败: {order.order_id}, 错误: {e}")
            order.status = OrderStatus.REJECTED
            order.updated_at = datetime.now()
            return False
    
    def check_limit_orders(self, current_price: float) -> List[Order]:
        """检查限价单是否触发"""
        filled_orders = []
        
        for order in self.open_orders[:]:
            if order.order_type == OrderType.LIMIT:
                if (order.side == OrderSide.BUY and current_price <= order.price) or \
                   (order.side == OrderSide.SELL and current_price >= order.price):
                    
                    # 执行限价单
                    order.status = OrderStatus.FILLED
                    order.filled_quantity = order.quantity
                    order.avg_fill_price = order.price
                    order.updated_at = datetime.now()
                    
                    self.open_orders.remove(order)
                    self.filled_orders.append(order)
                    filled_orders.append(order)
                    
                    logger.info(f"限价单成交: {order.order_id}, 价格: {order.price}")
        
        return filled_orders
    
    def check_stop_orders(self, current_price: float) -> List[Order]:
        """检查止损止盈单是否触发"""
        filled_orders = []
        
        for order in self.open_orders[:]:
            if order.order_type in [OrderType.STOP, OrderType.TAKE_PROFIT]:
                trigger = False
                
                if order.order_type == OrderType.STOP:
                    # 止损单：价格突破止损价时触发
                    if (order.side == OrderSide.BUY and current_price >= order.stop_price) or \
                       (order.side == OrderSide.SELL and current_price <= order.stop_price):
                        trigger = True
                
                elif order.order_type == OrderType.TAKE_PROFIT:
                    # 止盈单：价格达到止盈价时触发
                    if (order.side == OrderSide.BUY and current_price <= order.take_profit_price) or \
                       (order.side == OrderSide.SELL and current_price >= order.take_profit_price):
                        trigger = True
                
                if trigger:
                    # 执行止损/止盈单（按市价执行）
                    order.status = OrderStatus.FILLED
                    order.filled_quantity = order.quantity
                    order.avg_fill_price = current_price
                    order.updated_at = datetime.now()
                    
                    self.open_orders.remove(order)
                    self.filled_orders.append(order)
                    filled_orders.append(order)
                    
                    logger.info(f"{'止损' if order.order_type == OrderType.STOP else '止盈'}单成交: {order.order_id}, 价格: {current_price}")
        
        return filled_orders
    
    def cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        if order_id in self.orders:
            order = self.orders[order_id]
            if order.status in [OrderStatus.PENDING, OrderStatus.OPEN]:
                order.status = OrderStatus.CANCELLED
                order.updated_at = datetime.now()
                
                if order in self.open_orders:
                    self.open_orders.remove(order)
                
                logger.info(f"订单已取消: {order_id}")
                return True
        
        logger.warning(f"取消订单失败: {order_id} 不存在或无法取消")
        return False
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """获取订单信息"""
        return self.orders.get(order_id)
    
    def get_open_orders(self) -> List[Order]:
        """获取所有未成交订单"""
        return self.open_orders.copy()
    
    def get_filled_orders(self) -> List[Order]:
        """获取所有已成交订单"""
        return self.filled_orders.copy()
    
    def clear_orders(self):
        """清空所有订单"""
        self.orders.clear()
        self.open_orders.clear()
        self.filled_orders.clear()
        self.order_counter = 0
        logger.info("所有订单已清空")


# 单例模式
global_order_manager = OrderManager()