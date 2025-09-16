"""
网格交易策略配置
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from decimal import Decimal
from enum import Enum, auto
import logging

logger = logging.getLogger(__name__)


class GridType(Enum):
    """网格类型"""
    ARITHMETIC = auto()  # 等差数列网格
    GEOMETRIC = auto()   # 等比数列网格
    FIBONACCI = auto()   # 斐波那契网格
    CUSTOM = auto()      # 自定义网格


class GridDirection(Enum):
    """网格方向"""
    BOTH = auto()        # 双向网格
    UP_ONLY = auto()     # 仅向上网格
    DOWN_ONLY = auto()   # 仅向下网格


@dataclass
class GridLevel:
    """网格价格水平"""
    price: Decimal
    quantity: Decimal
    order_type: str  # 'buy' or 'sell'
    is_active: bool = True
    order_id: Optional[str] = None
    filled_quantity: Decimal = Decimal('0')
    avg_fill_price: Decimal = Decimal('0')
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class GridConfig:
    """网格交易策略配置"""
    
    # 基础配置
    strategy_id: str
    strategy_name: str
    symbol: str
    base_quantity: Decimal  # 基础交易数量
    
    # 网格配置
    grid_type: GridType = GridType.ARITHMETIC
    grid_direction: GridDirection = GridDirection.BOTH
    grid_count: int = 10  # 网格数量
    grid_spacing: Decimal = Decimal('0.01')  # 网格间距（百分比）
    center_price: Optional[Decimal] = None  # 中心价格
    
    # 价格范围
    upper_price: Optional[Decimal] = None  # 上限价格
    lower_price: Optional[Decimal] = None  # 下限价格
    
    # 风险控制
    max_position: Decimal = Decimal('1000')  # 最大持仓
    stop_loss_price: Optional[Decimal] = None  # 止损价格
    take_profit_price: Optional[Decimal] = None  # 止盈价格
    max_drawdown: Decimal = Decimal('0.05')  # 最大回撤限制
    
    # 资金管理
    total_capital: Decimal = Decimal('10000')  # 总资金
    position_ratio: Decimal = Decimal('0.8')  # 仓位比例
    reserve_ratio: Decimal = Decimal('0.2')  # 预留比例
    
    # 交易参数
    commission_rate: Decimal = Decimal('0.001')  # 手续费率
    slippage: Decimal = Decimal('0.0005')  # 滑点
    min_trade_amount: Decimal = Decimal('10')  # 最小交易金额
    
    # 动态调整
    enable_dynamic_adjustment: bool = True  # 启用动态调整
    adjustment_threshold: Decimal = Decimal('0.02')  # 调整阈值
    rebalance_interval: int = 3600  # 重新平衡间隔（秒）
    
    # 高级配置
    enable_trailing_stop: bool = False  # 启用跟踪止损
    trailing_stop_distance: Decimal = Decimal('0.02')  # 跟踪止损距离
    enable_partial_fill: bool = True  # 启用部分成交
    max_partial_fills: int = 3  # 最大部分成交次数
    
    # 自定义参数
    custom_params: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """配置验证"""
        self._validate_config()
    
    def _validate_config(self):
        """验证配置参数"""
        if self.grid_count <= 0:
            raise ValueError("网格数量必须大于0")
        
        if self.grid_spacing <= 0:
            raise ValueError("网格间距必须大于0")
        
        if self.base_quantity <= 0:
            raise ValueError("基础交易数量必须大于0")
        
        if self.total_capital <= 0:
            raise ValueError("总资金必须大于0")
        
        if self.position_ratio <= 0 or self.position_ratio > 1:
            raise ValueError("仓位比例必须在0-1之间")
        
        if self.reserve_ratio < 0 or self.reserve_ratio > 1:
            raise ValueError("预留比例必须在0-1之间")
        
        if self.position_ratio + self.reserve_ratio > 1:
            raise ValueError("仓位比例和预留比例之和不能超过1")
        
        if self.commission_rate < 0 or self.commission_rate > 1:
            raise ValueError("手续费率必须在0-1之间")
        
        if self.slippage < 0 or self.slippage > 1:
            raise ValueError("滑点必须在0-1之间")
        
        if self.max_drawdown < 0 or self.max_drawdown > 1:
            raise ValueError("最大回撤限制必须在0-1之间")
        
        if self.adjustment_threshold < 0 or self.adjustment_threshold > 1:
            raise ValueError("调整阈值必须在0-1之间")
        
        if self.trailing_stop_distance < 0 or self.trailing_stop_distance > 1:
            raise ValueError("跟踪止损距离必须在0-1之间")
        
        # 价格范围验证
        if self.upper_price and self.lower_price:
            if self.upper_price <= self.lower_price:
                raise ValueError("上限价格必须大于下限价格")
        
        # 止损止盈验证
        if self.stop_loss_price and self.take_profit_price:
            if self.stop_loss_price >= self.take_profit_price:
                raise ValueError("止损价格必须小于止盈价格")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {}
        for field_name, field_value in self.__dict__.items():
            if isinstance(field_value, Decimal):
                result[field_name] = float(field_value)
            elif isinstance(field_value, Enum):
                result[field_name] = field_value.name
            else:
                result[field_name] = field_value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GridConfig':
        """从字典创建配置"""
        # 处理枚举类型
        if 'grid_type' in data and isinstance(data['grid_type'], str):
            data['grid_type'] = GridType[data['grid_type']]
        
        if 'grid_direction' in data and isinstance(data['grid_direction'], str):
            data['grid_direction'] = GridDirection[data['grid_direction']]
        
        # 处理Decimal类型
        decimal_fields = [
            'base_quantity', 'grid_spacing', 'center_price', 'upper_price', 'lower_price',
            'max_position', 'stop_loss_price', 'take_profit_price', 'max_drawdown',
            'total_capital', 'position_ratio', 'reserve_ratio', 'commission_rate',
            'slippage', 'min_trade_amount', 'adjustment_threshold', 'trailing_stop_distance'
        ]
        
        for field in decimal_fields:
            if field in data and data[field] is not None:
                data[field] = Decimal(str(data[field]))
        
        return cls(**data)
    
    def get_effective_capital(self) -> Decimal:
        """获取有效交易资金"""
        return self.total_capital * self.position_ratio
    
    def get_reserve_capital(self) -> Decimal:
        """获取预留资金"""
        return self.total_capital * self.reserve_ratio
    
    def calculate_max_quantity(self, price: Decimal) -> Decimal:
        """计算最大交易数量"""
        effective_capital = self.get_effective_capital()
        max_quantity = effective_capital / price
        return min(max_quantity, self.max_position)
    
    def is_price_in_range(self, price: Decimal) -> bool:
        """检查价格是否在交易范围内"""
        if self.upper_price and price > self.upper_price:
            return False
        if self.lower_price and price < self.lower_price:
            return False
        return True
    
    def get_grid_spacing_amount(self, price: Decimal) -> Decimal:
        """计算网格间距金额"""
        return price * self.grid_spacing


@dataclass
class GridTradingState:
    """网格交易状态"""
    current_price: Decimal
    total_position: Decimal = Decimal('0')
    total_pnl: Decimal = Decimal('0')
    realized_pnl: Decimal = Decimal('0')
    unrealized_pnl: Decimal = Decimal('0')
    total_commission: Decimal = Decimal('0')
    active_orders: int = 0
    filled_orders: int = 0
    grid_levels: List[GridLevel] = field(default_factory=list)
    last_update_time: Optional[str] = None
    
    def update_pnl(self, current_price: Decimal, avg_cost: Decimal):
        """更新盈亏"""
        if self.total_position != 0:
            self.unrealized_pnl = (current_price - avg_cost) * self.total_position
        else:
            self.unrealized_pnl = Decimal('0')
        
        self.total_pnl = self.realized_pnl + self.unrealized_pnl
    
    def add_trade(self, quantity: Decimal, price: Decimal, commission: Decimal):
        """添加交易记录"""
        self.total_position += quantity
        self.total_commission += commission
        
        if self.total_position == 0:
            # 平仓，计算已实现盈亏
            self.realized_pnl += self.unrealized_pnl
            self.unrealized_pnl = Decimal('0')
        else:
            # 更新未实现盈亏
            avg_cost = self.get_average_cost()
            self.update_pnl(price, avg_cost)
    
    def get_average_cost(self) -> Decimal:
        """计算平均成本"""
        if self.total_position == 0:
            return Decimal('0')
        
        # 简化计算，实际应该基于历史交易记录
        return self.current_price
    
    def get_position_ratio(self) -> Decimal:
        """获取当前仓位比例"""
        if self.total_position == 0:
            return Decimal('0')
        
        # 简化计算，实际应该基于总资金
        return Decimal('0.5')  # 临时值


def create_default_grid_config(symbol: str, total_capital: Decimal) -> GridConfig:
    """创建默认网格配置"""
    return GridConfig(
        strategy_id=f"grid_{symbol.lower()}_{int(total_capital)}",
        strategy_name=f"网格交易策略-{symbol}",
        symbol=symbol,
        base_quantity=Decimal('0.1'),
        total_capital=total_capital,
        grid_count=10,
        grid_spacing=Decimal('0.01'),
        position_ratio=Decimal('0.8'),
        reserve_ratio=Decimal('0.2'),
        commission_rate=Decimal('0.001'),
        slippage=Decimal('0.0005'),
        max_drawdown=Decimal('0.05'),
        enable_dynamic_adjustment=True,
        adjustment_threshold=Decimal('0.02'),
        rebalance_interval=3600
    )


def create_aggressive_grid_config(symbol: str, total_capital: Decimal) -> GridConfig:
    """创建激进网格配置"""
    config = create_default_grid_config(symbol, total_capital)
    config.grid_count = 20
    config.grid_spacing = Decimal('0.005')
    config.position_ratio = Decimal('0.9')
    config.reserve_ratio = Decimal('0.1')
    config.max_drawdown = Decimal('0.08')
    config.adjustment_threshold = Decimal('0.01')
    return config


def create_conservative_grid_config(symbol: str, total_capital: Decimal) -> GridConfig:
    """创建保守网格配置"""
    config = create_default_grid_config(symbol, total_capital)
    config.grid_count = 5
    config.grid_spacing = Decimal('0.02')
    config.position_ratio = Decimal('0.6')
    config.reserve_ratio = Decimal('0.4')
    config.max_drawdown = Decimal('0.03')
    config.adjustment_threshold = Decimal('0.05')
    return config
