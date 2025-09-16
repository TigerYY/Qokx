"""
系统配置设置 - 多时间框架、市场状态识别和回测配置
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class TimeframeConfig:
    """时间框架配置"""
    name: str
    interval: str  # 1m, 5m, 15m, 1h, 4h, 1d
    weight: float  # 在信号融合中的权重
    lookback_period: int  # 回溯周期


@dataclass
class DataConfig:
    """数据配置"""
    # 数据源配置
    data_source: str = "okx"  # 数据源
    update_interval: int = 1  # 更新间隔(秒)
    max_retries: int = 3  # 最大重试次数
    retry_delay: int = 5  # 重试延迟(秒)
    
    # 数据存储配置
    enable_caching: bool = True  # 启用缓存
    cache_size: int = 1000  # 缓存大小
    cache_ttl: int = 300  # 缓存TTL(秒)
    
    # 数据质量配置
    enable_data_validation: bool = True  # 启用数据验证
    min_volume_threshold: float = 0.0  # 最小成交量阈值
    max_price_change: float = 0.1  # 最大价格变化阈值
    
    # WebSocket配置
    ws_reconnect_interval: int = 5  # WebSocket重连间隔(秒)
    ws_heartbeat_interval: int = 30  # 心跳间隔(秒)
    ws_max_reconnect_attempts: int = 10  # 最大重连尝试次数


@dataclass
class MarketStateConfig:
    """市场状态识别配置"""
    adx_threshold: float = 25.0  # ADX趋势阈值
    volatility_threshold: float = 0.02  # 波动率阈值
    trend_strength_window: int = 20  # 趋势强度计算窗口


@dataclass
class TradingConfig:
    """交易配置"""
    # 基础交易配置
    default_symbol: str = "BTC-USDT"
    max_position_size: float = 0.1  # 最大仓位比例
    min_order_size: float = 0.001  # 最小订单大小
    max_order_size: float = 1.0  # 最大订单大小
    
    # 风险控制配置
    max_daily_loss: float = 0.05  # 最大日亏损比例
    max_drawdown: float = 0.15  # 最大回撤比例
    stop_loss_percent: float = 0.02  # 止损百分比
    take_profit_percent: float = 0.04  # 止盈百分比
    
    # 订单配置
    order_timeout: int = 30  # 订单超时时间(秒)
    max_retry_attempts: int = 3  # 最大重试次数
    retry_delay: float = 1.0  # 重试延迟(秒)
    
    # 滑点控制
    max_slippage: float = 0.001  # 最大滑点
    slippage_tolerance: float = 0.0005  # 滑点容忍度
    
    # 杠杆配置
    max_leverage: float = 1.0  # 最大杠杆
    default_leverage: float = 1.0  # 默认杠杆
    
    # 手续费配置
    maker_fee: float = 0.001  # Maker手续费
    taker_fee: float = 0.001  # Taker手续费


@dataclass
class StrategyConfig:
    """策略配置"""
    # 多时间框架配置
    timeframes: List[TimeframeConfig] = None
    
    # 市场状态配置
    market_state: MarketStateConfig = None
    
    # 信号融合权重
    fusion_weights: Dict[str, float] = None
    
    # 趋势跟踪策略参数
    trend_ema_fast: int = 20
    trend_ema_slow: int = 50
    trend_adx_threshold: float = 25.0
    trend_atr_multiplier: float = 2.0
    
    # 均值回归策略参数
    mean_reversion_rsi_period: int = 14
    mean_reversion_rsi_oversold: float = 30.0
    mean_reversion_rsi_overbought: float = 70.0
    mean_reversion_bollinger_period: int = 20
    mean_reversion_bollinger_std: float = 2.0
    
    # 突破策略参数
    breakout_donchian_period: int = 20
    breakout_volume_multiplier: float = 1.5
    
    # 信号强度阈值
    strong_signal_threshold: float = 0.7
    weak_signal_threshold: float = 0.4
    
    def __post_init__(self):
        if self.timeframes is None:
            self.timeframes = [
                TimeframeConfig("1min", "1m", 0.1, 100),
                TimeframeConfig("5min", "5m", 0.15, 80),
                TimeframeConfig("15min", "15m", 0.2, 60),
                TimeframeConfig("1hour", "1h", 0.25, 40),
                TimeframeConfig("4hour", "4h", 0.2, 30),
                TimeframeConfig("1day", "1d", 0.1, 20),
            ]
        
        if self.market_state is None:
            self.market_state = MarketStateConfig()
        
        if self.fusion_weights is None:
            self.fusion_weights = {
                "trend_following": 0.4,
                "mean_reversion": 0.3,
                "breakout": 0.3,
            }


@dataclass
class BacktestConfig:
    """回测配置"""
    symbol: str  # 交易品种
    timeframes: List[str]  # 使用的时间框架列表
    initial_capital: float = 10000.0  # 初始资金
    risk_per_trade: float = 0.02  # 每笔交易风险比例
    max_position_size: float = 0.1  # 最大仓位比例
    commission_rate: float = 0.001  # 交易手续费率
    slippage: float = 0.0005  # 滑点
    
    # 止损止盈配置
    use_stop_loss: bool = True
    stop_loss_percent: float = 0.02  # 固定百分比止损
    take_profit_percent: float = 0.04  # 固定百分比止盈
    stop_loss_atr_multiple: float = 2.0  # ATR倍数止损
    take_profit_atr_multiple: float = 3.0  # ATR倍数止盈
    
    # 数据配置
    lookback_period: int = 200  # 数据回看周期
    warmup_period: int = 50  # 预热周期
    
    # 时间范围
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    # 策略配置
    strategy_config: StrategyConfig = field(default_factory=StrategyConfig)


# 默认配置
DEFAULT_CONFIG = StrategyConfig()

# 默认回测配置
DEFAULT_BACKTEST_CONFIG = BacktestConfig(
    symbol="BTCUSDT",
    timeframes=["1h", "4h", "1d"],
    initial_capital=10000.0,
    risk_per_trade=0.02,
    max_position_size=0.1,
    commission_rate=0.001,
    slippage=0.0005,
    use_stop_loss=True,
    stop_loss_percent=0.02,
    take_profit_percent=0.04,
    stop_loss_atr_multiple=2.0,
    take_profit_atr_multiple=3.0,
    lookback_period=200,
    warmup_period=50
)