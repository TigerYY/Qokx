"""
市场状态识别器 - 检测趋势、震荡、波动率状态
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from enum import Enum, auto
import logging

from ..data.multi_timeframe_manager import OHLCVData
from ..config.settings import MarketStateConfig

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """市场状态枚举"""
    TREND_UP = auto()  # 上升趋势
    TREND_DOWN = auto()  # 下降趋势
    RANGING = auto()  # 震荡
    HIGH_VOLATILITY = auto()  # 高波动
    LOW_VOLATILITY = auto()  # 低波动
    BREAKOUT = auto()  # 突破


class MarketStateDetector:
    """市场状态识别器"""
    
    def __init__(self, config: MarketStateConfig):
        self.config = config
    
    def detect_market_state(self, ohlc_data: OHLCVData) -> Dict[str, MarketRegime]:
        """检测市场状态"""
        if not ohlc_data or len(ohlc_data.close) < 50:
            return {}
        
        states = {}
        
        # 趋势检测
        trend_state = self._detect_trend(ohlc_data)
        if trend_state:
            states['trend'] = trend_state
        
        # 波动率检测
        volatility_state = self._detect_volatility(ohlc_data)
        if volatility_state:
            states['volatility'] = volatility_state
        
        # 震荡检测
        ranging_state = self._detect_ranging(ohlc_data)
        if ranging_state:
            states['ranging'] = ranging_state
        
        # 突破检测
        breakout_state = self._detect_breakout(ohlc_data)
        if breakout_state:
            states['breakout'] = breakout_state
        
        return states
    
    def _detect_trend(self, ohlc_data: OHLCVData) -> Optional[MarketRegime]:
        """检测趋势状态"""
        close = ohlc_data.close
        
        # 使用ADX检测趋势强度
        adx = self._calculate_adx(ohlc_data)
        if adx is None or len(adx) == 0:
            return None
        
        current_adx = adx[-1]
        
        # 计算价格动量
        sma_20 = pd.Series(close).rolling(window=20).mean().values
        sma_50 = pd.Series(close).rolling(window=50).mean().values
        
        if len(sma_20) > 0 and len(sma_50) > 0:
            current_price = close[-1]
            price_above_sma20 = current_price > sma_20[-1]
            price_above_sma50 = current_price > sma_50[-1]
            sma20_above_sma50 = sma_20[-1] > sma_50[-1]
            
            if current_adx > self.config.adx_threshold:
                if price_above_sma20 and price_above_sma50 and sma20_above_sma50:
                    return MarketRegime.TREND_UP
                elif not price_above_sma20 and not price_above_sma50 and not sma20_above_sma50:
                    return MarketRegime.TREND_DOWN
        
        return None
    
    def _detect_volatility(self, ohlc_data: OHLCVData) -> Optional[MarketRegime]:
        """检测波动率状态"""
        close = ohlc_data.close
        
        if len(close) < 20:
            return None
        
        # 计算ATR（平均真实范围）
        atr = self._calculate_atr(ohlc_data)
        if atr is None or len(atr) == 0:
            return None
        
        current_atr = atr[-1]
        current_price = close[-1]
        
        # 计算波动率（ATR相对于价格的比例）
        volatility_ratio = current_atr / current_price
        
        if volatility_ratio > self.config.volatility_threshold:
            return MarketRegime.HIGH_VOLATILITY
        elif volatility_ratio < self.config.volatility_threshold * 0.5:
            return MarketRegime.LOW_VOLATILITY
        
        return None
    
    def _detect_ranging(self, ohlc_data: OHLCVData) -> Optional[MarketRegime]:
        """检测震荡状态"""
        close = ohlc_data.close
        
        if len(close) < 20:
            return None
        
        # 使用布林带宽度检测震荡
        bb_width = self._calculate_bollinger_band_width(ohlc_data)
        if bb_width is None or len(bb_width) == 0:
            return None
        
        current_bb_width = bb_width[-1]
        
        # 低布林带宽度通常表示震荡
        if current_bb_width < 0.1:  # 经验阈值
            return MarketRegime.RANGING
        
        return None
    
    def _detect_breakout(self, ohlc_data: OHLCVData) -> Optional[MarketRegime]:
        """检测突破状态"""
        close = ohlc_data.close
        high = ohlc_data.high
        low = ohlc_data.low
        
        if len(close) < 55:  # 需要足够的数据计算通道
            return None
        
        # 计算唐奇安通道
        donchian_high = pd.Series(high).rolling(window=20).max().values
        donchian_low = pd.Series(low).rolling(window=20).min().values
        
        if len(donchian_high) > 0 and len(donchian_low) > 0:
            current_high = high[-1]
            current_low = low[-1]
            
            # 突破上轨
            if current_high > donchian_high[-2]:  # 与前一个周期的上轨比较
                return MarketRegime.BREAKOUT
            # 突破下轨
            elif current_low < donchian_low[-2]:
                return MarketRegime.BREAKOUT
        
        return None
    
    def _calculate_adx(self, ohlc_data: OHLCVData) -> Optional[np.ndarray]:
        """计算ADX指标"""
        try:
            high = ohlc_data.high
            low = ohlc_data.low
            close = ohlc_data.close
            
            if len(high) < 14:
                return None
            
            # 简化版ADX计算
            tr = np.maximum(high - low, np.maximum(np.abs(high - close), np.abs(low - close)))
            atr = pd.Series(tr).rolling(window=14).mean().values
            
            # 方向运动
            up_move = high - np.roll(high, 1)
            down_move = np.roll(low, 1) - low
            
            pos_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
            neg_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
            
            pos_di = 100 * pd.Series(pos_dm).rolling(window=14).mean().values / atr
            neg_di = 100 * pd.Series(neg_dm).rolling(window=14).mean().values / atr
            
            dx = 100 * np.abs(pos_di - neg_di) / (pos_di + neg_di)
            adx = pd.Series(dx).rolling(window=14).mean().values
            
            return adx
        except Exception as e:
            logger.error(f"ADX calculation error: {e}")
            return None
    
    def _calculate_atr(self, ohlc_data: OHLCVData) -> Optional[np.ndarray]:
        """计算ATR指标"""
        try:
            high = ohlc_data.high
            low = ohlc_data.low
            close = ohlc_data.close
            
            tr = np.maximum(high - low, 
                          np.maximum(np.abs(high - np.roll(close, 1)), 
                                   np.abs(low - np.roll(close, 1))))
            atr = pd.Series(tr).rolling(window=14).mean().values
            return atr
        except Exception as e:
            logger.error(f"ATR calculation error: {e}")
            return None
    
    def _calculate_bollinger_band_width(self, ohlc_data: OHLCVData) -> Optional[np.ndarray]:
        """计算布林带宽度"""
        try:
            close = ohlc_data.close
            
            sma = pd.Series(close).rolling(window=20).mean().values
            std = pd.Series(close).rolling(window=20).std().values
            
            upper_band = sma + 2 * std
            lower_band = sma - 2 * std
            
            band_width = (upper_band - lower_band) / sma
            return band_width
        except Exception as e:
            logger.error(f"Bollinger Band calculation error: {e}")
            return None
    
    def get_market_state_summary(self, states: Dict[str, MarketRegime]) -> str:
        """获取市场状态摘要"""
        if not states:
            return "UNKNOWN"
        
        state_descriptions = []
        
        for state_type, regime in states.items():
            if regime == MarketRegime.TREND_UP:
                state_descriptions.append("强劲上升趋势")
            elif regime == MarketRegime.TREND_DOWN:
                state_descriptions.append("强劲下降趋势")
            elif regime == MarketRegime.RANGING:
                state_descriptions.append("横盘震荡")
            elif regime == MarketRegime.HIGH_VOLATILITY:
                state_descriptions.append("高波动市场")
            elif regime == MarketRegime.LOW_VOLATILITY:
                state_descriptions.append("低波动市场")
            elif regime == MarketRegime.BREAKOUT:
                state_descriptions.append("突破行情")
        
        return ", ".join(state_descriptions) if state_descriptions else "UNKNOWN"