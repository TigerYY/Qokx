"""
网格交易信号生成器
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
import numpy as np

from .grid_config import GridConfig, GridLevel, GridTradingState
from .grid_trading_strategy import GridSignal
from ..data.multi_timeframe_manager import OHLCVData

logger = logging.getLogger(__name__)


@dataclass
class GridAnalysis:
    """网格分析结果"""
    current_price: Decimal
    grid_density: float  # 网格密度
    price_coverage: float  # 价格覆盖度
    risk_level: str  # 风险等级
    recommendation: str  # 建议
    confidence: float  # 置信度


class GridSignalGenerator:
    """网格交易信号生成器"""
    
    def __init__(self, config: GridConfig):
        self.config = config
        self.signal_history: List[GridSignal] = []
        self.analysis_cache: Dict[str, GridAnalysis] = {}
        
        logger.info(f"初始化网格信号生成器: {config.strategy_name}")
    
    def generate_signals(self, 
                        price_data: OHLCVData, 
                        grid_levels: List[GridLevel],
                        current_state: GridTradingState) -> List[GridSignal]:
        """生成网格交易信号"""
        if not price_data or len(price_data.close) == 0:
            return []
        
        current_price = Decimal(str(price_data.close[-1]))
        signals = []
        
        # 基础网格信号
        grid_signals = self._generate_grid_signals(current_price, grid_levels)
        signals.extend(grid_signals)
        
        # 趋势调整信号
        trend_signals = self._generate_trend_signals(price_data, current_price, grid_levels)
        signals.extend(trend_signals)
        
        # 波动率调整信号
        volatility_signals = self._generate_volatility_signals(price_data, current_price, grid_levels)
        signals.extend(volatility_signals)
        
        # 风险控制信号
        risk_signals = self._generate_risk_signals(current_price, current_state)
        signals.extend(risk_signals)
        
        # 动态调整信号
        if self.config.enable_dynamic_adjustment:
            adjustment_signals = self._generate_adjustment_signals(price_data, current_price, grid_levels)
            signals.extend(adjustment_signals)
        
        # 过滤和排序信号
        filtered_signals = self._filter_and_rank_signals(signals, current_state)
        
        # 记录信号历史
        self.signal_history.extend(filtered_signals)
        
        return filtered_signals
    
    def _generate_grid_signals(self, current_price: Decimal, grid_levels: List[GridLevel]) -> List[GridSignal]:
        """生成基础网格信号"""
        signals = []
        
        for i, level in enumerate(grid_levels):
            if not level.is_active:
                continue
            
            signal = self._check_grid_trigger(level, current_price, i)
            if signal:
                signals.append(signal)
        
        return signals
    
    def _check_grid_trigger(self, level: GridLevel, current_price: Decimal, level_index: int) -> Optional[GridSignal]:
        """检查网格触发"""
        # 买入网格触发
        if level.order_type == 'buy' and current_price <= level.price:
            # 计算触发强度
            trigger_strength = self._calculate_trigger_strength(current_price, level.price, 'buy')
            
            return GridSignal(
                signal_type='buy',
                price=level.price,
                quantity=level.quantity,
                grid_level=level_index,
                confidence=trigger_strength,
                reason=f"买入网格触发，价格{current_price} <= {level.price}",
                timestamp=datetime.now()
            )
        
        # 卖出网格触发
        elif level.order_type == 'sell' and current_price >= level.price:
            # 计算触发强度
            trigger_strength = self._calculate_trigger_strength(current_price, level.price, 'sell')
            
            return GridSignal(
                signal_type='sell',
                price=level.price,
                quantity=level.quantity,
                grid_level=level_index,
                confidence=trigger_strength,
                reason=f"卖出网格触发，价格{current_price} >= {level.price}",
                timestamp=datetime.now()
            )
        
        return None
    
    def _calculate_trigger_strength(self, current_price: Decimal, grid_price: Decimal, order_type: str) -> float:
        """计算触发强度"""
        if order_type == 'buy':
            # 买入：价格越低，触发强度越高
            strength = float((grid_price - current_price) / grid_price)
        else:
            # 卖出：价格越高，触发强度越高
            strength = float((current_price - grid_price) / grid_price)
        
        # 限制在0-1之间
        return max(0.0, min(1.0, strength))
    
    def _generate_trend_signals(self, price_data: OHLCVData, current_price: Decimal, grid_levels: List[GridLevel]) -> List[GridSignal]:
        """生成趋势调整信号"""
        signals = []
        
        if len(price_data.close) < 20:
            return signals
        
        # 计算趋势指标
        trend_strength = self._calculate_trend_strength(price_data)
        
        # 趋势调整网格
        if abs(trend_strength) > 0.3:  # 强趋势
            adjustment_signal = self._generate_trend_adjustment_signal(
                current_price, trend_strength, grid_levels
            )
            if adjustment_signal:
                signals.append(adjustment_signal)
        
        return signals
    
    def _calculate_trend_strength(self, price_data: OHLCVData) -> float:
        """计算趋势强度"""
        closes = np.array(price_data.close)
        
        # 计算移动平均线
        short_ma = np.mean(closes[-5:])  # 5期移动平均
        long_ma = np.mean(closes[-20:])  # 20期移动平均
        
        # 计算趋势强度
        if long_ma == 0:
            return 0.0
        
        trend_strength = (short_ma - long_ma) / long_ma
        return float(trend_strength)
    
    def _generate_trend_adjustment_signal(self, current_price: Decimal, trend_strength: float, grid_levels: List[GridLevel]) -> Optional[GridSignal]:
        """生成趋势调整信号"""
        # 强上升趋势：增加卖出网格
        if trend_strength > 0.3:
            return GridSignal(
                signal_type='adjust',
                price=current_price,
                quantity=Decimal('0'),
                grid_level=-1,
                confidence=0.7,
                reason=f"强上升趋势，建议增加卖出网格，趋势强度: {trend_strength:.2f}",
                timestamp=datetime.now()
            )
        
        # 强下降趋势：增加买入网格
        elif trend_strength < -0.3:
            return GridSignal(
                signal_type='adjust',
                price=current_price,
                quantity=Decimal('0'),
                grid_level=-1,
                confidence=0.7,
                reason=f"强下降趋势，建议增加买入网格，趋势强度: {trend_strength:.2f}",
                timestamp=datetime.now()
            )
        
        return None
    
    def _generate_volatility_signals(self, price_data: OHLCVData, current_price: Decimal, grid_levels: List[GridLevel]) -> List[GridSignal]:
        """生成波动率调整信号"""
        signals = []
        
        if len(price_data.close) < 20:
            return signals
        
        # 计算波动率
        volatility = self._calculate_volatility(price_data)
        
        # 高波动率：增加网格密度
        if volatility > 0.05:  # 5%以上波动率
            adjustment_signal = GridSignal(
                signal_type='adjust',
                price=current_price,
                quantity=Decimal('0'),
                grid_level=-1,
                confidence=0.8,
                reason=f"高波动率环境，建议增加网格密度，波动率: {volatility:.2%}",
                timestamp=datetime.now()
            )
            signals.append(adjustment_signal)
        
        # 低波动率：减少网格密度
        elif volatility < 0.01:  # 1%以下波动率
            adjustment_signal = GridSignal(
                signal_type='adjust',
                price=current_price,
                quantity=Decimal('0'),
                grid_level=-1,
                confidence=0.6,
                reason=f"低波动率环境，建议减少网格密度，波动率: {volatility:.2%}",
                timestamp=datetime.now()
            )
            signals.append(adjustment_signal)
        
        return signals
    
    def _calculate_volatility(self, price_data: OHLCVData) -> float:
        """计算波动率"""
        closes = np.array(price_data.close)
        
        # 计算收益率
        returns = np.diff(closes) / closes[:-1]
        
        # 计算波动率（标准差）
        volatility = np.std(returns)
        
        return float(volatility)
    
    def _generate_risk_signals(self, current_price: Decimal, current_state: GridTradingState) -> List[GridSignal]:
        """生成风险控制信号"""
        signals = []
        
        # 检查止损
        if self.config.stop_loss_price and current_price <= self.config.stop_loss_price:
            signal = GridSignal(
                signal_type='sell',
                price=current_price,
                quantity=abs(current_state.total_position),
                grid_level=-1,
                confidence=1.0,
                reason=f"止损触发，价格{current_price} <= {self.config.stop_loss_price}",
                timestamp=datetime.now()
            )
            signals.append(signal)
        
        # 检查止盈
        if self.config.take_profit_price and current_price >= self.config.take_profit_price:
            signal = GridSignal(
                signal_type='sell',
                price=current_price,
                quantity=abs(current_state.total_position),
                grid_level=-1,
                confidence=1.0,
                reason=f"止盈触发，价格{current_price} >= {self.config.take_profit_price}",
                timestamp=datetime.now()
            )
            signals.append(signal)
        
        # 检查最大回撤
        if current_state.total_pnl < 0:
            current_drawdown = abs(current_state.total_pnl) / self.config.total_capital
            if current_drawdown > self.config.max_drawdown:
                signal = GridSignal(
                    signal_type='sell',
                    price=current_price,
                    quantity=abs(current_state.total_position),
                    grid_level=-1,
                    confidence=1.0,
                    reason=f"最大回撤触发，当前回撤{current_drawdown:.2%}",
                    timestamp=datetime.now()
                )
                signals.append(signal)
        
        # 检查仓位限制
        if abs(current_state.total_position) > self.config.max_position:
            signal = GridSignal(
                signal_type='sell',
                price=current_price,
                quantity=abs(current_state.total_position) - self.config.max_position,
                grid_level=-1,
                confidence=0.9,
                reason=f"仓位超限，当前持仓{current_state.total_position}",
                timestamp=datetime.now()
            )
            signals.append(signal)
        
        return signals
    
    def _generate_adjustment_signals(self, price_data: OHLCVData, current_price: Decimal, grid_levels: List[GridLevel]) -> List[GridSignal]:
        """生成动态调整信号"""
        signals = []
        
        # 分析网格状态
        analysis = self._analyze_grid_status(current_price, grid_levels)
        
        # 根据分析结果生成调整信号
        if analysis.recommendation == 'increase_density':
            signal = GridSignal(
                signal_type='adjust',
                price=current_price,
                quantity=Decimal('0'),
                grid_level=-1,
                confidence=analysis.confidence,
                reason=f"建议增加网格密度，当前密度: {analysis.grid_density:.2f}",
                timestamp=datetime.now()
            )
            signals.append(signal)
        
        elif analysis.recommendation == 'decrease_density':
            signal = GridSignal(
                signal_type='adjust',
                price=current_price,
                quantity=Decimal('0'),
                grid_level=-1,
                confidence=analysis.confidence,
                reason=f"建议减少网格密度，当前密度: {analysis.grid_density:.2f}",
                timestamp=datetime.now()
            )
            signals.append(signal)
        
        elif analysis.recommendation == 'rebalance':
            signal = GridSignal(
                signal_type='adjust',
                price=current_price,
                quantity=Decimal('0'),
                grid_level=-1,
                confidence=analysis.confidence,
                reason=f"建议重新平衡网格，价格覆盖度: {analysis.price_coverage:.2f}",
                timestamp=datetime.now()
            )
            signals.append(signal)
        
        return signals
    
    def _analyze_grid_status(self, current_price: Decimal, grid_levels: List[GridLevel]) -> GridAnalysis:
        """分析网格状态"""
        # 计算网格密度
        grid_density = self._calculate_grid_density(current_price, grid_levels)
        
        # 计算价格覆盖度
        price_coverage = self._calculate_price_coverage(current_price, grid_levels)
        
        # 评估风险等级
        risk_level = self._assess_risk_level(grid_density, price_coverage)
        
        # 生成建议
        recommendation = self._generate_recommendation(grid_density, price_coverage, risk_level)
        
        # 计算置信度
        confidence = self._calculate_analysis_confidence(grid_density, price_coverage)
        
        return GridAnalysis(
            current_price=current_price,
            grid_density=grid_density,
            price_coverage=price_coverage,
            risk_level=risk_level,
            recommendation=recommendation,
            confidence=confidence
        )
    
    def _calculate_grid_density(self, current_price: Decimal, grid_levels: List[GridLevel]) -> float:
        """计算网格密度"""
        if not grid_levels:
            return 0.0
        
        # 计算价格范围内的网格数量
        price_range = self._get_price_range(current_price)
        active_grids = [g for g in grid_levels if g.is_active and price_range[0] <= g.price <= price_range[1]]
        
        # 密度 = 网格数量 / 价格范围
        if price_range[1] - price_range[0] == 0:
            return 0.0
        
        density = len(active_grids) / float(price_range[1] - price_range[0]) * float(current_price)
        return density
    
    def _calculate_price_coverage(self, current_price: Decimal, grid_levels: List[GridLevel]) -> float:
        """计算价格覆盖度"""
        if not grid_levels:
            return 0.0
        
        # 计算价格范围
        prices = [float(g.price) for g in grid_levels if g.is_active]
        if not prices:
            return 0.0
        
        min_price = min(prices)
        max_price = max(prices)
        price_range = max_price - min_price
        
        # 覆盖度 = 价格范围 / 当前价格
        coverage = price_range / float(current_price)
        return coverage
    
    def _assess_risk_level(self, grid_density: float, price_coverage: float) -> str:
        """评估风险等级"""
        if grid_density > 0.1 and price_coverage > 0.2:
            return 'HIGH'
        elif grid_density > 0.05 and price_coverage > 0.1:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _generate_recommendation(self, grid_density: float, price_coverage: float, risk_level: str) -> str:
        """生成建议"""
        if risk_level == 'HIGH':
            return 'decrease_density'
        elif risk_level == 'LOW':
            return 'increase_density'
        elif price_coverage < 0.05:
            return 'rebalance'
        else:
            return 'maintain'
    
    def _calculate_analysis_confidence(self, grid_density: float, price_coverage: float) -> float:
        """计算分析置信度"""
        # 基于数据质量计算置信度
        confidence = 0.5  # 基础置信度
        
        # 网格密度影响
        if 0.02 <= grid_density <= 0.08:
            confidence += 0.2
        elif 0.01 <= grid_density <= 0.1:
            confidence += 0.1
        
        # 价格覆盖度影响
        if 0.1 <= price_coverage <= 0.3:
            confidence += 0.2
        elif 0.05 <= price_coverage <= 0.5:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _get_price_range(self, current_price: Decimal) -> Tuple[float, float]:
        """获取价格范围"""
        # 基于配置的价格范围
        if self.config.upper_price and self.config.lower_price:
            return (float(self.config.lower_price), float(self.config.upper_price))
        
        # 基于当前价格的默认范围
        range_ratio = 0.1  # 10%范围
        lower = float(current_price) * (1 - range_ratio)
        upper = float(current_price) * (1 + range_ratio)
        
        return (lower, upper)
    
    def _filter_and_rank_signals(self, signals: List[GridSignal], current_state: GridTradingState) -> List[GridSignal]:
        """过滤和排序信号"""
        # 过滤信号
        filtered_signals = []
        for signal in signals:
            if self._should_include_signal(signal, current_state):
                filtered_signals.append(signal)
        
        # 按置信度排序
        filtered_signals.sort(key=lambda x: x.confidence, reverse=True)
        
        # 限制信号数量
        max_signals = 5
        return filtered_signals[:max_signals]
    
    def _should_include_signal(self, signal: GridSignal, current_state: GridTradingState) -> bool:
        """判断是否应该包含信号"""
        # 基础过滤条件
        if signal.confidence < 0.3:
            return False
        
        # 风险控制信号优先
        if signal.signal_type in ['sell'] and signal.grid_level == -1:
            return True
        
        # 网格信号检查
        if signal.grid_level >= 0:
            # 检查是否已有相同网格的活跃信号
            for existing_signal in self.signal_history[-10:]:  # 检查最近10个信号
                if (existing_signal.grid_level == signal.grid_level and 
                    existing_signal.signal_type == signal.signal_type and
                    (datetime.now() - existing_signal.timestamp).total_seconds() < 300):  # 5分钟内
                    return False
        
        return True
    
    def get_signal_statistics(self) -> Dict[str, Any]:
        """获取信号统计"""
        if not self.signal_history:
            return {}
        
        total_signals = len(self.signal_history)
        buy_signals = len([s for s in self.signal_history if s.signal_type == 'buy'])
        sell_signals = len([s for s in self.signal_history if s.signal_type == 'sell'])
        adjust_signals = len([s for s in self.signal_history if s.signal_type == 'adjust'])
        
        avg_confidence = sum(s.confidence for s in self.signal_history) / total_signals
        
        return {
            'total_signals': total_signals,
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'adjust_signals': adjust_signals,
            'avg_confidence': avg_confidence,
            'recent_signals': len([s for s in self.signal_history if (datetime.now() - s.timestamp).total_seconds() < 3600])
        }
