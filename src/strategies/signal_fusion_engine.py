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
        high = ohlc_data.high
        low = ohlc_data.low
        volume = ohlc_data.volume
        
        # 计算多种趋势指标
        ema_12 = pd.Series(close).ewm(span=12).mean().values
        ema_26 = pd.Series(close).ewm(span=26).mean().values
        ema_50 = pd.Series(close).ewm(span=50).mean().values
        
        # 计算MACD
        macd_line = ema_12 - ema_26
        signal_line = pd.Series(macd_line).ewm(span=9).mean().values
        macd_histogram = macd_line - signal_line
        
        # 计算ADX (趋势强度)
        adx = self._calculate_adx(high, low, close, 14)
        
        # 计算成交量加权平均价格 (VWAP)
        vwap = self._calculate_vwap(high, low, close, volume)
        
        if len(ema_12) > 0 and len(ema_26) > 0 and len(ema_50) > 0:
            # 多重EMA排列信号
            ema_alignment = 0.0
            if ema_12[-1] > ema_26[-1] > ema_50[-1]:  # 多头排列
                ema_alignment = 1.0
            elif ema_12[-1] < ema_26[-1] < ema_50[-1]:  # 空头排列
                ema_alignment = -1.0
            
            # MACD信号
            macd_signal = 0.0
            if len(macd_histogram) > 1:
                if macd_line[-1] > signal_line[-1] and macd_histogram[-1] > macd_histogram[-2]:
                    macd_signal = 1.0
                elif macd_line[-1] < signal_line[-1] and macd_histogram[-1] < macd_histogram[-2]:
                    macd_signal = -1.0
            
            # 价格相对于VWAP的位置
            vwap_signal = 0.0
            if vwap is not None and len(vwap) > 0:
                if close[-1] > vwap[-1]:
                    vwap_signal = 1.0
                else:
                    vwap_signal = -1.0
            
            # 综合趋势信号
            trend_signals = [ema_alignment, macd_signal, vwap_signal]
            final_signal = np.mean([s for s in trend_signals if s != 0.0])
            
            # 计算置信度
            confidence = 0.5  # 基础置信度
            
            # ADX增强置信度
            if adx is not None and len(adx) > 0:
                adx_strength = min(adx[-1] / 50.0, 1.0)  # ADX > 25表示强趋势
                confidence *= (0.5 + adx_strength * 0.5)
            
            # 信号一致性增强置信度
            signal_consistency = sum(1 for s in trend_signals if s != 0.0 and np.sign(s) == np.sign(final_signal))
            consistency_bonus = signal_consistency / len([s for s in trend_signals if s != 0.0]) if any(trend_signals) else 0
            confidence *= (0.7 + consistency_bonus * 0.3)
            
            # 趋势强度（基于价格与EMA的距离）
            trend_strength = abs(close[-1] - ema_26[-1]) / ema_26[-1]
            confidence *= min(trend_strength * 5 + 0.5, 1.0)
            
            if abs(final_signal) > 0.1:  # 只有明确信号才返回
                return SignalStrength(
                    value=final_signal,
                    confidence=min(confidence, 1.0),
                    timeframe=ohlc_data.timeframe,
                    strategy_type=StrategyType.TREND_FOLLOWING
                )
        
        return None
    
    def _generate_mean_reversion_signal(self, ohlc_data: OHLCVData, 
                                      market_regimes: Dict[str, MarketRegime]) -> Optional[SignalStrength]:
        """生成均值回归信号"""
        if len(ohlc_data.close) < 30:
            return None
        
        close = ohlc_data.close
        high = ohlc_data.high
        low = ohlc_data.low
        
        # 计算多种均值回归指标
        rsi = self._calculate_rsi(close, 14)
        stoch_k, stoch_d = self._calculate_stochastic(high, low, close, 14, 3)
        bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(close, 20, 2)
        williams_r = self._calculate_williams_r(high, low, close, 14)
        
        if rsi is None or len(rsi) == 0:
            return None
        
        current_rsi = rsi[-1]
        signals = []
        confidences = []
        
        # RSI信号
        if current_rsi > 75:
            signals.append(-1.0)
            confidences.append((current_rsi - 75) / 25)
        elif current_rsi < 25:
            signals.append(1.0)
            confidences.append((25 - current_rsi) / 25)
        
        # 随机指标信号
        if stoch_k is not None and len(stoch_k) > 0:
            current_stoch_k = stoch_k[-1]
            if current_stoch_k > 80:
                signals.append(-1.0)
                confidences.append((current_stoch_k - 80) / 20)
            elif current_stoch_k < 20:
                signals.append(1.0)
                confidences.append((20 - current_stoch_k) / 20)
        
        # 布林带信号
        if bb_upper is not None and len(bb_upper) > 0:
            if close[-1] > bb_upper[-1]:  # 价格突破上轨
                signals.append(-1.0)
                confidences.append(min((close[-1] - bb_upper[-1]) / bb_upper[-1], 1.0))
            elif close[-1] < bb_lower[-1]:  # 价格突破下轨
                signals.append(1.0)
                confidences.append(min((bb_lower[-1] - close[-1]) / bb_lower[-1], 1.0))
        
        # 威廉指标信号
        if williams_r is not None and len(williams_r) > 0:
            current_wr = williams_r[-1]
            if current_wr > -20:  # 超买
                signals.append(-1.0)
                confidences.append((current_wr + 20) / 20)
            elif current_wr < -80:  # 超卖
                signals.append(1.0)
                confidences.append((-80 - current_wr) / 20)
        
        if not signals:
            return None
        
        # 计算综合信号
        weighted_signal = np.average(signals, weights=confidences)
        avg_confidence = np.mean(confidences)
        
        # 信号一致性检查
        signal_consistency = sum(1 for s in signals if np.sign(s) == np.sign(weighted_signal)) / len(signals)
        final_confidence = avg_confidence * signal_consistency
        
        # 只有在明确的超买超卖情况下才发出信号
        if abs(weighted_signal) > 0.3 and final_confidence > 0.4:
            return SignalStrength(
                value=weighted_signal,
                confidence=min(final_confidence, 1.0),
                timeframe=ohlc_data.timeframe,
                strategy_type=StrategyType.MEAN_REVERSION
            )
        
        return None
    
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
    
    def _calculate_adx(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int) -> Optional[np.ndarray]:
        """计算ADX (平均趋向指数)"""
        try:
            high_s = pd.Series(high)
            low_s = pd.Series(low)
            close_s = pd.Series(close)
            
            # 计算真实波幅 (TR)
            tr1 = high_s - low_s
            tr2 = abs(high_s - close_s.shift(1))
            tr3 = abs(low_s - close_s.shift(1))
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            
            # 计算方向性移动 (DM)
            plus_dm = high_s.diff()
            minus_dm = low_s.diff()
            
            plus_dm[plus_dm < 0] = 0
            minus_dm[minus_dm > 0] = 0
            minus_dm = abs(minus_dm)
            
            # 计算平滑的TR和DM
            atr = tr.rolling(window=period).mean()
            plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
            minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
            
            # 计算ADX
            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
            adx = dx.rolling(window=period).mean()
            
            return adx.values
        except Exception as e:
            logger.error(f"ADX calculation error: {e}")
            return None
    
    def _calculate_vwap(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, volume: np.ndarray) -> Optional[np.ndarray]:
        """计算成交量加权平均价格 (VWAP)"""
        try:
            typical_price = (high + low + close) / 3
            vwap = np.cumsum(typical_price * volume) / np.cumsum(volume)
            return vwap
        except Exception as e:
            logger.error(f"VWAP calculation error: {e}")
            return None
    
    def _calculate_stochastic(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, 
                            k_period: int, d_period: int) -> tuple:
        """计算随机指标 (Stochastic)"""
        try:
            high_s = pd.Series(high)
            low_s = pd.Series(low)
            close_s = pd.Series(close)
            
            lowest_low = low_s.rolling(window=k_period).min()
            highest_high = high_s.rolling(window=k_period).max()
            
            k_percent = 100 * ((close_s - lowest_low) / (highest_high - lowest_low))
            d_percent = k_percent.rolling(window=d_period).mean()
            
            return k_percent.values, d_percent.values
        except Exception as e:
            logger.error(f"Stochastic calculation error: {e}")
            return None, None
    
    def _calculate_bollinger_bands(self, data: np.ndarray, period: int, std_dev: float) -> tuple:
        """计算布林带"""
        try:
            close_s = pd.Series(data)
            sma = close_s.rolling(window=period).mean()
            std = close_s.rolling(window=period).std()
            
            upper_band = sma + (std * std_dev)
            lower_band = sma - (std * std_dev)
            
            return upper_band.values, sma.values, lower_band.values
        except Exception as e:
            logger.error(f"Bollinger Bands calculation error: {e}")
            return None, None, None
    
    def _calculate_williams_r(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int) -> Optional[np.ndarray]:
        """计算威廉指标 (Williams %R)"""
        try:
            high_s = pd.Series(high)
            low_s = pd.Series(low)
            close_s = pd.Series(close)
            
            highest_high = high_s.rolling(window=period).max()
            lowest_low = low_s.rolling(window=period).min()
            
            williams_r = -100 * ((highest_high - close_s) / (highest_high - lowest_low))
            
            return williams_r.values
        except Exception as e:
            logger.error(f"Williams %R calculation error: {e}")
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