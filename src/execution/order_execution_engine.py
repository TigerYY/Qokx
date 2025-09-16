"""
订单执行引擎模块
提供订单相关的数据模型和执行逻辑
"""

from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass
from decimal import Decimal


class OrderSide(Enum):
    """订单方向"""
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """订单类型"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class Order:
    """订单数据模型"""
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: Decimal = Decimal('0')
    remaining_quantity: Optional[Decimal] = None
    average_price: Optional[Decimal] = None
    commission: Decimal = Decimal('0')
    created_at: datetime = None
    updated_at: datetime = None
    client_order_id: Optional[str] = None
    time_in_force: str = "GTC"  # Good Till Cancelled
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if self.remaining_quantity is None:
            self.remaining_quantity = self.quantity

    def update_status(self, status: OrderStatus, **kwargs):
        """更新订单状态"""
        self.status = status
        self.updated_at = datetime.utcnow()
        
        # 更新其他字段
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def is_filled(self) -> bool:
        """检查订单是否完全成交"""
        return self.status == OrderStatus.FILLED

    def is_active(self) -> bool:
        """检查订单是否活跃（未完成）"""
        return self.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED, OrderStatus.PARTIALLY_FILLED]

    def get_fill_ratio(self) -> float:
        """获取成交比例"""
        if self.quantity == 0:
            return 0.0
        return float(self.filled_quantity / self.quantity)


class OrderExecutionEngine:
    """订单执行引擎"""
    
    def __init__(self):
        self.orders: Dict[str, Order] = {}
        self.order_counter = 0

    def create_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        stop_price: Optional[Decimal] = None,
        client_order_id: Optional[str] = None,
        **kwargs
    ) -> Order:
        """创建新订单"""
        self.order_counter += 1
        order_id = f"order_{self.order_counter}_{int(datetime.utcnow().timestamp())}"
        
        order = Order(
            order_id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
            client_order_id=client_order_id,
            **kwargs
        )
        
        self.orders[order_id] = order
        return order

    def get_order(self, order_id: str) -> Optional[Order]:
        """获取订单"""
        return self.orders.get(order_id)

    def update_order(self, order_id: str, **kwargs) -> bool:
        """更新订单"""
        order = self.orders.get(order_id)
        if order:
            order.update_status(**kwargs)
            return True
        return False

    def cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        order = self.orders.get(order_id)
        if order and order.is_active():
            order.update_status(OrderStatus.CANCELLED)
            return True
        return False

    def get_orders_by_symbol(self, symbol: str) -> list[Order]:
        """获取指定交易对的订单"""
        return [order for order in self.orders.values() if order.symbol == symbol]

    def get_active_orders(self) -> list[Order]:
        """获取活跃订单"""
        return [order for order in self.orders.values() if order.is_active()]

    def get_orders_by_status(self, status: OrderStatus) -> list[Order]:
        """根据状态获取订单"""
        return [order for order in self.orders.values() if order.status == status]

    def get_order_statistics(self) -> Dict[str, Any]:
        """获取订单统计信息"""
        total_orders = len(self.orders)
        active_orders = len(self.get_active_orders())
        filled_orders = len(self.get_orders_by_status(OrderStatus.FILLED))
        cancelled_orders = len(self.get_orders_by_status(OrderStatus.CANCELLED))
        
        return {
            "total_orders": total_orders,
            "active_orders": active_orders,
            "filled_orders": filled_orders,
            "cancelled_orders": cancelled_orders,
            "fill_rate": filled_orders / total_orders if total_orders > 0 else 0.0
        }
