"""
仓位管理模块
提供仓位相关的数据模型和管理逻辑
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass
from decimal import Decimal


class PositionSide(Enum):
    """仓位方向"""
    LONG = "long"
    SHORT = "short"


class PositionStatus(Enum):
    """仓位状态"""
    OPEN = "open"
    CLOSED = "closed"
    PARTIALLY_CLOSED = "partially_closed"


@dataclass
class Position:
    """仓位数据模型"""
    position_id: str
    symbol: str
    side: PositionSide
    size: Decimal
    entry_price: Decimal
    current_price: Decimal
    unrealized_pnl: Decimal = Decimal('0')
    realized_pnl: Decimal = Decimal('0')
    status: PositionStatus = PositionStatus.OPEN
    leverage: Decimal = Decimal('1')
    margin: Decimal = Decimal('0')
    created_at: datetime = None
    updated_at: datetime = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        self._calculate_unrealized_pnl()

    def _calculate_unrealized_pnl(self):
        """计算未实现盈亏"""
        if self.side == PositionSide.LONG:
            self.unrealized_pnl = (self.current_price - self.entry_price) * self.size
        else:  # SHORT
            self.unrealized_pnl = (self.entry_price - self.current_price) * self.size

    def update_price(self, new_price: Decimal):
        """更新当前价格"""
        self.current_price = new_price
        self._calculate_unrealized_pnl()
        self.updated_at = datetime.utcnow()

    def close_position(self, close_price: Decimal, close_size: Optional[Decimal] = None):
        """平仓"""
        if close_size is None:
            close_size = self.size
        
        # 计算已实现盈亏
        if self.side == PositionSide.LONG:
            realized_pnl = (close_price - self.entry_price) * close_size
        else:  # SHORT
            realized_pnl = (self.entry_price - close_price) * close_size
        
        self.realized_pnl += realized_pnl
        self.size -= close_size
        
        # 更新状态
        if self.size <= 0:
            self.status = PositionStatus.CLOSED
        else:
            self.status = PositionStatus.PARTIALLY_CLOSED
        
        self.updated_at = datetime.utcnow()
        return realized_pnl

    def get_total_pnl(self) -> Decimal:
        """获取总盈亏"""
        return self.unrealized_pnl + self.realized_pnl

    def get_pnl_percentage(self) -> float:
        """获取盈亏百分比"""
        if self.entry_price == 0:
            return 0.0
        return float(self.get_total_pnl() / (self.entry_price * self.size) * 100)

    def get_margin_ratio(self) -> float:
        """获取保证金比例"""
        if self.margin == 0:
            return 0.0
        return float(abs(self.unrealized_pnl) / self.margin * 100)


class PositionManager:
    """仓位管理器"""
    
    def __init__(self):
        self.positions: Dict[str, Position] = {}
        self.position_counter = 0

    def create_position(
        self,
        symbol: str,
        side: PositionSide,
        size: Decimal,
        entry_price: Decimal,
        current_price: Optional[Decimal] = None,
        leverage: Decimal = Decimal('1'),
        **kwargs
    ) -> Position:
        """创建新仓位"""
        self.position_counter += 1
        position_id = f"pos_{self.position_counter}_{int(datetime.utcnow().timestamp())}"
        
        if current_price is None:
            current_price = entry_price
        
        position = Position(
            position_id=position_id,
            symbol=symbol,
            side=side,
            size=size,
            entry_price=entry_price,
            current_price=current_price,
            leverage=leverage,
            **kwargs
        )
        
        self.positions[position_id] = position
        return position

    def get_position(self, position_id: str) -> Optional[Position]:
        """获取仓位"""
        return self.positions.get(position_id)

    def get_positions_by_symbol(self, symbol: str) -> List[Position]:
        """获取指定交易对的仓位"""
        return [pos for pos in self.positions.values() if pos.symbol == symbol]

    def get_open_positions(self) -> List[Position]:
        """获取开放仓位"""
        return [pos for pos in self.positions.values() if pos.status == PositionStatus.OPEN]

    def get_positions_by_side(self, side: PositionSide) -> List[Position]:
        """根据方向获取仓位"""
        return [pos for pos in self.positions.values() if pos.side == side]

    def update_position_price(self, position_id: str, new_price: Decimal) -> bool:
        """更新仓位价格"""
        position = self.positions.get(position_id)
        if position:
            position.update_price(new_price)
            return True
        return False

    def close_position(self, position_id: str, close_price: Decimal, close_size: Optional[Decimal] = None) -> Optional[Decimal]:
        """平仓"""
        position = self.positions.get(position_id)
        if position and position.status == PositionStatus.OPEN:
            realized_pnl = position.close_position(close_price, close_size)
            return realized_pnl
        return None

    def get_total_pnl(self) -> Decimal:
        """获取总盈亏"""
        return sum(pos.get_total_pnl() for pos in self.positions.values())

    def get_total_unrealized_pnl(self) -> Decimal:
        """获取总未实现盈亏"""
        return sum(pos.unrealized_pnl for pos in self.positions.values())

    def get_total_realized_pnl(self) -> Decimal:
        """获取总已实现盈亏"""
        return sum(pos.realized_pnl for pos in self.positions.values())

    def get_position_statistics(self) -> Dict[str, Any]:
        """获取仓位统计信息"""
        total_positions = len(self.positions)
        open_positions = len(self.get_open_positions())
        closed_positions = len([pos for pos in self.positions.values() if pos.status == PositionStatus.CLOSED])
        
        total_pnl = self.get_total_pnl()
        total_unrealized_pnl = self.get_total_unrealized_pnl()
        total_realized_pnl = self.get_total_realized_pnl()
        
        return {
            "total_positions": total_positions,
            "open_positions": open_positions,
            "closed_positions": closed_positions,
            "total_pnl": float(total_pnl),
            "total_unrealized_pnl": float(total_unrealized_pnl),
            "total_realized_pnl": float(total_realized_pnl),
            "average_pnl_per_position": float(total_pnl / total_positions) if total_positions > 0 else 0.0
        }

    def get_risk_metrics(self) -> Dict[str, Any]:
        """获取风险指标"""
        open_positions = self.get_open_positions()
        if not open_positions:
            return {
                "max_drawdown": 0.0,
                "max_margin_ratio": 0.0,
                "total_exposure": 0.0,
                "risk_score": 0.0
            }
        
        # 计算最大回撤
        pnls = [pos.get_total_pnl() for pos in open_positions]
        max_pnl = max(pnls) if pnls else 0
        min_pnl = min(pnls) if pnls else 0
        max_drawdown = float(max_pnl - min_pnl) if max_pnl > 0 else 0.0
        
        # 计算最大保证金比例
        margin_ratios = [pos.get_margin_ratio() for pos in open_positions if pos.margin > 0]
        max_margin_ratio = max(margin_ratios) if margin_ratios else 0.0
        
        # 计算总敞口
        total_exposure = sum(float(pos.size * pos.current_price) for pos in open_positions)
        
        # 计算风险评分 (0-100)
        risk_score = min(100.0, max_margin_ratio * 0.5 + max_drawdown * 0.3)
        
        return {
            "max_drawdown": max_drawdown,
            "max_margin_ratio": max_margin_ratio,
            "total_exposure": total_exposure,
            "risk_score": risk_score
        }
