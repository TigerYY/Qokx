"""
仓位大小计算器 - 基于风险管理的仓位大小计算
"""

from typing import Dict, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)


class PositionSizer:
    """仓位大小计算器"""
    
    def __init__(self, risk_per_trade: float = 0.02, max_position_size: float = 0.1):
        self.risk_per_trade = risk_per_trade  # 每笔交易风险比例
        self.max_position_size = max_position_size  # 最大仓位比例
    
    def calculate_kelly_position(self, win_rate: float, win_loss_ratio: float, 
                               total_capital: float, current_price: float) -> float:
        """
        使用凯利公式计算最优仓位大小
        
        Args:
            win_rate: 胜率 (0-1)
            win_loss_ratio: 盈亏比 (平均盈利/平均亏损)
            total_capital: 总资金
            current_price: 当前价格
        """
        if win_rate <= 0 or win_loss_ratio <= 0:
            return 0.0
        
        # 凯利公式: f* = (bp - q) / b
        # 其中: b = 盈亏比, p = 胜率, q = 败率 (1-p)
        kelly_fraction = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio
        
        # 限制凯利系数在合理范围内 (0.01 - 0.25)
        kelly_fraction = max(0.01, min(0.25, kelly_fraction))
        
        # 计算仓位大小
        position_value = total_capital * kelly_fraction
        position_size = position_value / current_price
        
        return round(position_size, 6)
    
    def calculate_volatility_position(self, volatility: float, total_capital: float, 
                                    current_price: float, max_volatility_exposure: float = 0.3) -> float:
        """
        基于波动率的仓位大小计算
        
        Args:
            volatility: 波动率 (年化)
            total_capital: 总资金
            current_price: 当前价格
            max_volatility_exposure: 最大波动率暴露
        """
        if volatility <= 0:
            return 0.0
        
        # 计算波动率调整因子
        volatility_factor = min(1.0, max_volatility_exposure / volatility)
        
        # 计算仓位大小
        position_value = total_capital * self.risk_per_trade * volatility_factor
        position_size = position_value / current_price
        
        return round(position_size, 6)
    
    def calculate_fixed_fractional_position(self, total_capital: float, current_price: float, 
                                          stop_loss_distance: float) -> float:
        """
        固定分数仓位管理
        
        Args:
            total_capital: 总资金
            current_price: 当前价格
            stop_loss_distance: 止损距离 (价格单位)
        """
        if stop_loss_distance <= 0:
            return 0.0
        
        # 计算每笔交易的风险金额
        risk_amount = total_capital * self.risk_per_trade
        
        # 计算仓位大小
        position_size = risk_amount / stop_loss_distance
        
        # 确保不超过最大仓位限制
        max_position_value = total_capital * self.max_position_size
        max_position_size = max_position_value / current_price
        
        position_size = min(position_size, max_position_size)
        
        return round(position_size, 6)
    
    def calculate_atr_position(self, atr: float, total_capital: float, current_price: float, 
                             atr_multiplier: float = 2.0) -> float:
        """
        基于ATR的仓位大小计算
        
        Args:
            atr: ATR值
            total_capital: 总资金
            current_price: 当前价格
            atr_multiplier: ATR倍数
        """
        if atr <= 0:
            return 0.0
        
        # 计算止损距离 (ATR倍数)
        stop_loss_distance = atr * atr_multiplier
        
        # 使用固定分数方法计算仓位
        return self.calculate_fixed_fractional_position(total_capital, current_price, stop_loss_distance)
    
    def calculate_optimal_position(self, total_capital: float, current_price: float, 
                                  market_data: Dict, strategy_stats: Optional[Dict] = None) -> float:
        """
        计算最优仓位大小（综合多种方法）
        
        Args:
            total_capital: 总资金
            current_price: 当前价格
            market_data: 市场数据 (包含atr, volatility等)
            strategy_stats: 策略统计信息 (包含win_rate, win_loss_ratio等)
        """
        # 获取市场数据
        atr = market_data.get('atr')
        volatility = market_data.get('volatility')
        
        # 计算不同方法的仓位大小
        positions = []
        
        # 1. ATR方法
        if atr is not None and atr > 0:
            atr_position = self.calculate_atr_position(atr, total_capital, current_price)
            positions.append(atr_position)
        
        # 2. 波动率方法
        if volatility is not None and volatility > 0:
            vol_position = self.calculate_volatility_position(volatility, total_capital, current_price)
            positions.append(vol_position)
        
        # 3. 凯利公式方法（如果有策略统计）
        if strategy_stats and 'win_rate' in strategy_stats and 'win_loss_ratio' in strategy_stats:
            kelly_position = self.calculate_kelly_position(
                strategy_stats['win_rate'], 
                strategy_stats['win_loss_ratio'], 
                total_capital, 
                current_price
            )
            positions.append(kelly_position)
        
        # 如果没有其他方法，使用固定分数方法
        if not positions:
            # 默认使用2%的价格波动作为止损距离
            default_stop_loss = current_price * 0.02
            default_position = self.calculate_fixed_fractional_position(
                total_capital, current_price, default_stop_loss
            )
            positions.append(default_position)
        
        # 取各种方法的平均值作为最终仓位
        if positions:
            optimal_position = sum(positions) / len(positions)
        else:
            optimal_position = 0.0
        
        # 确保仓位大小合理
        optimal_position = self._validate_position_size(optimal_position, total_capital, current_price)
        
        logger.debug(f"计算最优仓位: {optimal_position}, 方法数量: {len(positions)}")
        return optimal_position
    
    def _validate_position_size(self, position_size: float, total_capital: float, 
                               current_price: float) -> float:
        """验证仓位大小的合理性"""
        # 计算仓位价值
        position_value = position_size * current_price
        
        # 1. 不能为负数
        if position_size < 0:
            return 0.0
        
        # 2. 不能超过最大仓位限制
        max_position_value = total_capital * self.max_position_size
        if position_value > max_position_value:
            position_size = max_position_value / current_price
        
        # 3. 确保有足够的资金
        if position_value > total_capital:
            position_size = total_capital / current_price
        
        # 4. 确保最小交易单位（假设最小为0.001）
        if position_size > 0 and position_size < 0.001:
            position_size = 0.001
        
        return round(position_size, 6)
    
    def calculate_stop_loss_take_profit(self, entry_price: float, position_size: float, 
                                      total_capital: float, market_data: Dict) -> Dict:
        """
        计算止损和止盈价格
        
        Returns:
            Dict: 包含stop_loss和take_profit价格
        """
        atr = market_data.get('atr')
        
        if atr is not None and atr > 0:
            # 使用ATR计算止损止盈
            stop_loss = entry_price - (atr * 2.0)  # 2倍ATR止损
            take_profit = entry_price + (atr * 4.0)  # 4倍ATR止盈 (风险回报比1:2)
        else:
            # 默认使用固定百分比
            risk_per_trade_amount = total_capital * self.risk_per_trade
            risk_per_share = risk_per_trade_amount / position_size
            
            stop_loss = entry_price - risk_per_share
            take_profit = entry_price + (risk_per_share * 2)  # 风险回报比1:2
        
        return {
            'stop_loss': max(0, stop_loss),
            'take_profit': max(0, take_profit)
        }


# 单例模式
global_position_sizer = PositionSizer()