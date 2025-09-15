"""
风险管理系统 - 负责止损止盈、仓位控制和风险管理
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime
import logging
import numpy as np

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """风险等级"""
    LOW = auto()      # 低风险
    MEDIUM = auto()   # 中等风险
    HIGH = auto()     # 高风险
    EXTREME = auto()  # 极端风险


class StopLossType(Enum):
    """止损类型"""
    FIXED_PERCENT = auto()  # 固定百分比止损
    ATR_BASED = auto()     # ATR倍数止损
    TRAILING = auto()      # 移动止损
    VOLATILITY = auto()    # 波动率止损


class TakeProfitType(Enum):
    """止盈类型"""
    FIXED_PERCENT = auto()  # 固定百分比止盈
    ATR_BASED = auto()     # ATR倍数止盈
    RISK_REWARD = auto()   # 风险回报比止盈
    TRAILING = auto()      # 移动止盈


@dataclass
class RiskConfig:
    """风险配置"""
    # 全局风险控制
    max_drawdown: float = 0.2  # 最大回撤限制 (20%)
    max_position_size: float = 0.1  # 最大仓位比例 (10%)
    max_daily_loss: float = 0.05  # 单日最大损失 (5%)
    
    # 止损配置
    stop_loss_type: StopLossType = StopLossType.ATR_BASED
    fixed_stop_loss: float = 0.02  # 固定止损比例 (2%)
    atr_stop_multiplier: float = 2.0  # ATR止损倍数
    trailing_stop_activation: float = 0.03  # 移动止损激活阈值 (3%)
    trailing_stop_distance: float = 0.015  # 移动止损距离 (1.5%)
    
    # 止盈配置
    take_profit_type: TakeProfitType = TakeProfitType.RISK_REWARD
    fixed_take_profit: float = 0.04  # 固定止盈比例 (4%)
    atr_take_profit_multiplier: float = 3.0  # ATR止盈倍数
    risk_reward_ratio: float = 2.0  # 风险回报比
    
    # 波动率控制
    max_volatility_exposure: float = 0.3  # 最大波动率暴露
    volatility_lookback: int = 20  # 波动率计算回溯期
    
    # 市场状态风险调整
    risk_adjustment_enabled: bool = True  # 是否启用市场状态风险调整


@dataclass
class PositionRisk:
    """持仓风险信息"""
    symbol: str
    position_size: float
    entry_price: float
    current_price: float
    stop_loss_price: float
    take_profit_price: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    risk_amount: float
    atr_value: Optional[float] = None
    volatility: Optional[float] = None
    risk_level: RiskLevel = RiskLevel.LOW


class RiskManager:
    """风险管理器"""
    
    def __init__(self, config: Optional[RiskConfig] = None):
        self.config = config or RiskConfig()
        self.daily_pnl_history: List[float] = []
        self.current_day = datetime.now().date()
        self.today_realized_pnl = 0.0
        self.today_unrealized_pnl = 0.0
    
    def calculate_stop_loss_price(self, entry_price: float, atr: Optional[float] = None, 
                                 current_price: Optional[float] = None, is_long: bool = True) -> float:
        """计算止损价格"""
        
        if self.config.stop_loss_type == StopLossType.FIXED_PERCENT:
            # 固定百分比止损
            if is_long:
                return entry_price * (1 - self.config.fixed_stop_loss)
            else:
                return entry_price * (1 + self.config.fixed_stop_loss)
        
        elif self.config.stop_loss_type == StopLossType.ATR_BASED and atr is not None:
            # ATR倍数止损
            if is_long:
                return entry_price - (atr * self.config.atr_stop_multiplier)
            else:
                return entry_price + (atr * self.config.atr_stop_multiplier)
        
        elif self.config.stop_loss_type == StopLossType.TRAILING and current_price is not None:
            # 移动止损
            if is_long:
                # 计算移动止损价格
                if current_price >= entry_price * (1 + self.config.trailing_stop_activation):
                    trailing_stop = current_price * (1 - self.config.trailing_stop_distance)
                    return max(trailing_stop, entry_price * (1 - self.config.fixed_stop_loss))
                else:
                    return entry_price * (1 - self.config.fixed_stop_loss)
            else:
                if current_price <= entry_price * (1 - self.config.trailing_stop_activation):
                    trailing_stop = current_price * (1 + self.config.trailing_stop_distance)
                    return min(trailing_stop, entry_price * (1 + self.config.fixed_stop_loss))
                else:
                    return entry_price * (1 + self.config.fixed_stop_loss)
        
        else:
            # 默认使用固定百分比止损
            if is_long:
                return entry_price * (1 - self.config.fixed_stop_loss)
            else:
                return entry_price * (1 + self.config.fixed_stop_loss)
    
    def calculate_take_profit_price(self, entry_price: float, stop_loss_price: float, 
                                   atr: Optional[float] = None, is_long: bool = True) -> float:
        """计算止盈价格"""
        
        if self.config.take_profit_type == TakeProfitType.FIXED_PERCENT:
            # 固定百分比止盈
            if is_long:
                return entry_price * (1 + self.config.fixed_take_profit)
            else:
                return entry_price * (1 - self.config.fixed_take_profit)
        
        elif self.config.take_profit_type == TakeProfitType.ATR_BASED and atr is not None:
            # ATR倍数止盈
            if is_long:
                return entry_price + (atr * self.config.atr_take_profit_multiplier)
            else:
                return entry_price - (atr * self.config.atr_take_profit_multiplier)
        
        elif self.config.take_profit_type == TakeProfitType.RISK_REWARD:
            # 风险回报比止盈
            risk_amount = abs(entry_price - stop_loss_price)
            if is_long:
                return entry_price + (risk_amount * self.config.risk_reward_ratio)
            else:
                return entry_price - (risk_amount * self.config.risk_reward_ratio)
        
        elif self.config.take_profit_type == TakeProfitType.TRAILING:
            # 移动止盈（与移动止损类似，但更激进）
            if is_long:
                return entry_price * (1 + self.config.fixed_take_profit * 1.5)  # 比固定止盈更激进
            else:
                return entry_price * (1 - self.config.fixed_take_profit * 1.5)
        
        else:
            # 默认使用风险回报比
            risk_amount = abs(entry_price - stop_loss_price)
            if is_long:
                return entry_price + (risk_amount * self.config.risk_reward_ratio)
            else:
                return entry_price - (risk_amount * self.config.risk_reward_ratio)
    
    def check_position_risk(self, position_info: Dict, market_data: Dict, 
                           total_capital: float) -> PositionRisk:
        """检查持仓风险"""
        
        symbol = position_info.get('symbol', '')
        position_size = position_info.get('position_size', 0.0)
        entry_price = position_info.get('entry_price', 0.0)
        current_price = position_info.get('current_price', 0.0)
        
        # 计算未实现盈亏
        unrealized_pnl = position_size * (current_price - entry_price)
        unrealized_pnl_percent = (current_price / entry_price - 1) * 100
        
        # 获取ATR和波动率数据
        atr = market_data.get('atr')
        volatility = market_data.get('volatility')
        
        # 计算止损价格
        is_long = position_size > 0
        stop_loss_price = self.calculate_stop_loss_price(entry_price, atr, current_price, is_long)
        
        # 计算止盈价格
        take_profit_price = self.calculate_take_profit_price(entry_price, stop_loss_price, atr, is_long)
        
        # 计算风险金额
        risk_per_share = abs(entry_price - stop_loss_price)
        risk_amount = position_size * risk_per_share
        
        # 评估风险等级
        risk_level = self._assess_risk_level(
            position_size, total_capital, unrealized_pnl_percent, 
            risk_amount, total_capital, volatility
        )
        
        return PositionRisk(
            symbol=symbol,
            position_size=position_size,
            entry_price=entry_price,
            current_price=current_price,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price,
            unrealized_pnl=unrealized_pnl,
            unrealized_pnl_percent=unrealized_pnl_percent,
            risk_amount=risk_amount,
            atr_value=atr,
            volatility=volatility,
            risk_level=risk_level
        )
    
    def _assess_risk_level(self, position_size: float, total_capital: float, 
                          pnl_percent: float, risk_amount: float, 
                          available_capital: float, volatility: Optional[float]) -> RiskLevel:
        """评估风险等级"""
        
        # 仓位大小风险
        position_ratio = position_size * (pnl_percent > 0 and 1 or -1) / total_capital
        
        # 风险金额比例
        risk_ratio = risk_amount / available_capital
        
        # 波动率风险
        volatility_risk = 0.0
        if volatility is not None:
            volatility_risk = volatility / self.config.max_volatility_exposure
        
        # 综合风险评估
        risk_score = (abs(position_ratio) * 0.4 + 
                     risk_ratio * 0.3 + 
                     abs(pnl_percent) * 0.2 + 
                     volatility_risk * 0.1)
        
        if risk_score < 0.1:
            return RiskLevel.LOW
        elif risk_score < 0.3:
            return RiskLevel.MEDIUM
        elif risk_score < 0.5:
            return RiskLevel.HIGH
        else:
            return RiskLevel.EXTREME
    
    def check_drawdown_limit(self, total_capital: float, initial_capital: float) -> bool:
        """检查是否超过最大回撤限制"""
        drawdown = (initial_capital - total_capital) / initial_capital
        return drawdown > self.config.max_drawdown
    
    def check_daily_loss_limit(self, realized_pnl: float, unrealized_pnl: float) -> bool:
        """检查是否超过单日损失限制"""
        today = datetime.now().date()
        
        # 如果是新的一天，重置当日盈亏
        if today != self.current_day:
            self.daily_pnl_history.append(self.today_realized_pnl + self.today_unrealized_pnl)
            self.today_realized_pnl = 0.0
            self.today_unrealized_pnl = 0.0
            self.current_day = today
        
        # 更新当日盈亏
        self.today_realized_pnl = realized_pnl
        self.today_unrealized_pnl = unrealized_pnl
        
        total_daily_pnl = realized_pnl + unrealized_pnl
        
        # 检查是否超过单日损失限制
        return total_daily_pnl < -self.config.max_daily_loss
    
    def get_risk_adjustment_factor(self, market_state: str, volatility: float) -> float:
        """根据市场状态和波动率获取风险调整因子"""
        if not self.config.risk_adjustment_enabled:
            return 1.0
        
        # 根据市场状态调整风险
        adjustment = 1.0
        
        if market_state == "high_volatility":
            adjustment *= 0.5  # 高波动率市场，降低风险暴露
        elif market_state == "trending":
            adjustment *= 0.8  # 趋势市场，适度降低风险
        elif market_state == "ranging":
            adjustment *= 1.2  # 震荡市场，适度增加风险
        elif market_state == "low_volatility":
            adjustment *= 1.5  # 低波动率市场，增加风险暴露
        
        # 根据波动率进一步调整
        volatility_ratio = volatility / self.config.max_volatility_exposure
        if volatility_ratio > 1.0:
            adjustment *= 0.7  # 波动率过高，降低风险
        elif volatility_ratio > 0.7:
            adjustment *= 0.9  # 波动率较高，适度降低风险
        
        return max(0.1, min(2.0, adjustment))  # 限制在0.1-2.0范围内
    
    def get_risk_report(self) -> Dict:
        """生成风险报告"""
        return {
            'daily_realized_pnl': self.today_realized_pnl,
            'daily_unrealized_pnl': self.today_unrealized_pnl,
            'total_daily_pnl': self.today_realized_pnl + self.today_unrealized_pnl,
            'daily_loss_limit': self.config.max_daily_loss,
            'max_drawdown_limit': self.config.max_drawdown,
            'max_position_size_limit': self.config.max_position_size,
            'daily_pnl_history': self.daily_pnl_history[-30:]  # 最近30天的盈亏历史
        }


# 单例模式
global_risk_manager = RiskManager()