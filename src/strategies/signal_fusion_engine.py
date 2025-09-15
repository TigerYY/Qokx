"""
信号融合引擎 - 多时间框架信号融合和策略选择
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum, auto
import logging

from ..data.multi_timeframe_manager import OHLCVData
from .market_state_detector import MarketRegime, MarketStateDetector
from ..config.settings import StrategyConfig, TimeframeConfig

logger = logging.getLogger(__name__)


class TradingSignal(Enum):
    """交易信号枚举"""
    STRONG_BUY = auto()
    BUY = auto()
    NEUTRAL = auto()
    SELL = auto()
    STRONG_SELL = auto()


class StrategyType(Enum):
    """策略类型枚举"""
    TREND_FOLLOWING = auto()
    MEAN_REVERSION = auto()
    BREAKOUT = auto()


@dataclass
class SignalStrength:
    """信号强度"""
    value: float  # -1.0 到 1.0 之间的值
    confidence: float  # 置信度 0.0 到 1.0
    timeframe: str
    strategy_type: StrategyType


@dataclass
class FusedSignal:
    """融合后的信号"""
    final_signal: TradingSignal
    signal_strength: float  # -1.0 到 1.0
    confidence: float
    market_regime: Dict[str, MarketRegime]
    strategy_weights: Dict[StrategyType, float]
    timeframe_signals: Dict[str, SignalStrength]


class SignalFusionEngine:
    """信号融合引擎"""
    
    def __init__(self, config: StrategyConfig):
        self.config = config
        self.market_detector = MarketStateDetector(config.market_state)
    
    async def generate_signals(self, multi_timeframe_data: Dict[str, OHLCVData]) -> FusedSignal:
        """生成融合信号"""
        # 检测市场状态
        market_regimes = {}
        for timeframe, data in multi_timeframe_data.items():
            regimes = self.market_detector.detect_market_state(data)
            if regimes:
                market_regimes[timeframe] = regimes
        
        # 生成各时间框架信号
        timeframe_signals = {}
        for timeframe, data in multi_timeframe_data.items():
            signals = self._generate_timeframe_signals(timeframe, data, market_regimes.get(timeframe, {}))
            timeframe_signals[timeframe] = signals
        
        # 融合信号
        fused_signal = self._fuse_signals(timeframe_signals, market_regimes)
        
        return fused_signal
    
    def _generate_timeframe_signals(self, timeframe: str, ohlc_data: OHLCVData, 
                                  market_regimes: Dict[str, MarketRegime]) -> List[SignalStrength]:
        """生成单个时间框架的信号"""
        signals = []
        
        # 趋势跟踪策略信号
        trend_signal = self._generate_trend_signal(ohlc_data, market_regimes)
        if trend_signal:
            signals.append(trend_signal)
        
        # 均值回归策略信号
        mean_reversion_signal = self._generate_mean_reversion_signal(ohlc_data, market_regimes)
        if mean_reversion_signal:
            signals.append(mean_reversion_signal)
        
        # 突破策略信号
        breakout_signal = self._generate_breakout_signal(ohlc_data, market_regimes)
        if breakout_signal:
            signals.append(breakout_signal)
        
        return signals
    
    def _generate_trend_signal(self, ohlc_data: OHLCVData, 
                             market_regimes: Dict[str, MarketRegime]) -> Optional[SignalStrength]:
        """生成趋势跟踪信号"""
        if len(ohlc_data.close) < 50:
            return None
        
        close = ohlc_data.close
        
        # 计算EMA交叉信号
        ema_12 = pd.Series(close).ewm(span=12).mean().values
        ema_26 = pd.Series(close).ewm(span=26).mean().values
        
        if len(ema_12) > 0 and len(ema_26) > 0:
            # EMA金叉死叉信号
            ema_signal = 1.0 if ema_12[-1] > ema_26[-1] else -1.0
            
            # 趋势强度（基于价格与EMA的距离）
            trend_strength = abs(close[-1] - ema_26[-1]) / ema_26[-1]
            confidence = min(trend_strength * 10, 1.0)  # 标准化到0-1
            
            return SignalStrength(
                value=ema_signal,
                confidence=confidence,
                timeframe=ohlc_data.timeframe,
                strategy_type=StrategyType.TREND_FOLLOWING
            )
        
        return None
    
    def _generate_mean_reversion_signal(self, ohlc_data: OHLCVData, 
                                      market_regimes: Dict[str, MarketRegime]) -> Optional[SignalStrength]:
        """生成均值回归信号"""
        if len(ohlc_data.close) < 20:
            return None
        
        close = ohlc_data.close
        
        # 计算RSI
        rsi = self._calculate_rsi(close, 14)
        if rsi is None or len(rsi) == 0:
            return None
        
        current_rsi = rsi[-1]
        
        # RSI超买超卖信号
        if current_rsi > 70:
            signal_value = -1.0  # 超卖，做空信号
            confidence = (current_rsi - 70) / 30  # 70-100映射到0-1
        elif current_rsi < 30:
            signal_value = 1.0   # 超买，做多信号
            confidence = (30 - current_rsi) / 30  # 0-30映射到0-1
        else:
            return None
        
        return SignalStrength(
            value=signal_value,
            confidence=confidence,
            timeframe=ohlc_data.timeframe,
            strategy_type=StrategyType.MEAN_REVERSION
        )
    
    def _generate_breakout_signal(self, ohlc_data: OHLCVData, 
                               market_regimes: Dict[str, MarketRegime]) -> Optional[SignalStrength]:
        """生成突破信号"""
        if len(ohlc_data.close) < 55:
            return None
        
        high = ohlc_data.high
        low = ohlc_data.low
        
        # 计算唐奇安通道
        donchian_high = pd.Series(high).rolling(window=20).max().values
        donchian_low = pd.Series(low).rolling(window=20).min().values
        
        if len(donchian_high) > 0 and len(donchian_low) > 0:
            current_high = high[-1]
            current_low = low[-1]
            
            # 突破上轨
            if current_high > donchian_high[-2]:
                breakout_strength = (current_high - donchian_high[-2]) / donchian_high[-2]
                return SignalStrength(
                    value=1.0,
                    confidence=min(breakout_strength * 10, 1.0),
                    timeframe=ohlc_data.timeframe,
                    strategy_type=StrategyType.BREAKOUT
                )
            # 突破下轨
            elif current_low < donchian_low[-2]:
                breakout_strength = (donchian_low[-2] - current_low) / donchian_low[-2]
                return SignalStrength(
                    value=-1.0,
                    confidence=min(breakout_strength * 10, 1.0),
                    timeframe=ohlc_data.timeframe,
                    strategy_type=StrategyType.BREAKOUT
                )
        
        return None
    
    def _fuse_signals(self, timeframe_signals: Dict[str, List[SignalStrength]],
                     market_regimes: Dict[str, Dict[str, MarketRegime]]) -> FusedSignal:
        """融合多时间框架信号"""
        # 计算各策略类型的加权信号
        strategy_signals = {}
        strategy_confidences = {}
        
        for timeframe, signals in timeframe_signals.items():
            timeframe_config = next((tf for tf in self.config.timeframes if tf.interval == timeframe), None)
            if not timeframe_config:
                continue
            
            for signal in signals:
                weight = timeframe_config.weight
                
                if signal.strategy_type not in strategy_signals:
                    strategy_signals[signal.strategy_type] = 0.0
                    strategy_confidences[signal.strategy_type] = 0.0
                
                strategy_signals[signal.strategy_type] += signal.value * weight * signal.confidence
                strategy_confidences[signal.strategy_type] += signal.confidence * weight
        
        # 应用策略权重
        final_signal = 0.0
        final_confidence = 0.0
        strategy_weights = {}
        
        for strategy_type, signal in strategy_signals.items():
            strategy_weight = self.config.fusion_weights.get(strategy_type.name.lower(), 0.3)
            confidence = strategy_confidences.get(strategy_type, 0.0)
            
            weighted_signal = signal * strategy_weight
            weighted_confidence = confidence * strategy_weight
            
            final_signal += weighted_signal
            final_confidence += weighted_confidence
            strategy_weights[strategy_type] = strategy_weight
        
        # 标准化最终信号
        if final_confidence > 0:
            final_signal /= final_confidence
            final_confidence = min(final_confidence, 1.0)
        
        # 转换为交易信号枚举
        trading_signal = self._convert_to_trading_signal(final_signal, final_confidence)
        
        return FusedSignal(
            final_signal=trading_signal,
            signal_strength=final_signal,
            confidence=final_confidence,
            market_regime=market_regimes,
            strategy_weights=strategy_weights,
            timeframe_signals=timeframe_signals
        )
    
    def _convert_to_trading_signal(self, signal_strength: float, confidence: float) -> TradingSignal:
        """将信号强度转换为交易信号"""
        if confidence < 0.3:  # 低置信度
            return TradingSignal.NEUTRAL
        
        if signal_strength > 0.6:
            return TradingSignal.STRONG_BUY
        elif signal_strength > 0.2:
            return TradingSignal.BUY
        elif signal_strength < -0.6:
            return TradingSignal.STRONG_SELL
        elif signal_strength < -0.2:
            return TradingSignal.SELL
        else:
            return TradingSignal.NEUTRAL
    
    def _calculate_rsi(self, data: np.ndarray, period: int) -> Optional[np.ndarray]:
        """计算RSI"""
        try:
            delta = pd.Series(data).diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs)).values
        except Exception as e:
            logger.error(f"RSI calculation error: {e}")
            return None
    
    def get_signal_description(self, signal: TradingSignal) -> str:
        """获取信号描述"""
        descriptions = {
            TradingSignal.STRONG_BUY: "强烈买入",
            TradingSignal.BUY: "买入",
            TradingSignal.NEUTRAL: "中性",
            TradingSignal.SELL: "卖出", 
            TradingSignal.STRONG_SELL: "强烈卖出"
        }
        return descriptions.get(signal, "未知")
    
    def should_trade(self, fused_signal: FusedSignal) -> bool:
        """判断是否应该交易"""
        # 只有强烈信号才交易
        return fused_signal.final_signal in [TradingSignal.STRONG_BUY, TradingSignal.STRONG_SELL]
    
    def get_position_size(self, fused_signal: FusedSignal, account_balance: float) -> float:
        """计算仓位大小"""
        if not self.should_trade(fused_signal):
            return 0.0
        
        # 基于信号强度和置信度的仓位计算
        base_size = account_balance * 0.02  # 2%的基础仓位
        
        # 信号强度调整
        strength_multiplier = abs(fused_signal.signal_strength)
        
        # 置信度调整
        confidence_multiplier = fused_signal.confidence
        
        position_size = base_size * strength_multiplier * confidence_multiplier
        
        # 限制最大仓位
        max_position = account_balance * 0.1  # 最大10%
        return min(position_size, max_position)