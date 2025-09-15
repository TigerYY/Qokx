"""
数据库模型定义
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column, Integer, String, DateTime, 
    Boolean, Text, JSON, ForeignKey, Index, UniqueConstraint, and_
)
from sqlalchemy.types import DECIMAL as SQLDecimal
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()


class Trade(Base):
    """交易记录表"""
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_id = Column(String(50), unique=True, nullable=False, index=True)  # 交易唯一ID
    strategy_id = Column(String(50), nullable=False, index=True)  # 策略ID
    strategy_version = Column(String(20), nullable=False)  # 策略版本
    symbol = Column(String(20), nullable=False, index=True)  # 交易对
    direction = Column(String(10), nullable=False)  # 买卖方向: BUY/SELL
    order_type = Column(String(20), nullable=False)  # 订单类型: MARKET/LIMIT/STOP
    price = Column(SQLDecimal(20, 8), nullable=False)  # 成交价格
    quantity = Column(SQLDecimal(20, 8), nullable=False)  # 成交数量
    amount = Column(SQLDecimal(20, 8), nullable=False)  # 成交金额
    commission = Column(SQLDecimal(20, 8), default=0)  # 手续费
    pnl = Column(SQLDecimal(20, 8), default=0)  # 盈亏
    status = Column(String(20), default='FILLED')  # 订单状态
    timestamp = Column(DateTime, nullable=False, index=True)  # 成交时间
    created_at = Column(DateTime, default=datetime.utcnow)  # 创建时间
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 更新时间
    
    # 关联关系 - 暂时移除复杂关系，避免初始化问题
    # strategy = relationship("StrategyVersion", back_populates="trades")
    
    # 索引
    __table_args__ = (
        Index('idx_strategy_timestamp', 'strategy_id', 'timestamp'),
        Index('idx_symbol_timestamp', 'symbol', 'timestamp'),
    )


class StrategyVersion(Base):
    """策略版本表"""
    __tablename__ = 'strategy_versions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(String(50), nullable=False, index=True)  # 策略ID
    version = Column(String(20), nullable=False)  # 版本号
    name = Column(String(100), nullable=False)  # 策略名称
    description = Column(Text)  # 策略描述
    class_path = Column(String(200), nullable=False)  # 策略类路径
    config = Column(JSON)  # 策略配置
    is_active = Column(Boolean, default=False)  # 是否激活
    is_testing = Column(Boolean, default=False)  # 是否在测试中
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    # trades = relationship("Trade", back_populates="strategy")
    # performance_metrics = relationship("PerformanceMetrics", back_populates="strategy_version_rel")
    
    # 唯一约束
    __table_args__ = (
        UniqueConstraint('strategy_id', 'version', name='uq_strategy_version'),
        Index('idx_strategy_active', 'strategy_id', 'is_active'),
    )


class StrategyConfig(Base):
    """策略配置表"""
    __tablename__ = 'strategy_configs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(String(50), nullable=False, index=True)
    config_key = Column(String(100), nullable=False)  # 配置键
    config_value = Column(JSON)  # 配置值
    config_type = Column(String(20), default='strategy')  # 配置类型: strategy/risk/system
    description = Column(Text)  # 配置描述
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 唯一约束
    __table_args__ = (
        UniqueConstraint('strategy_id', 'config_key', name='uq_strategy_config'),
        Index('idx_strategy_config_type', 'strategy_id', 'config_type'),
    )


class PerformanceMetrics(Base):
    """性能指标表"""
    __tablename__ = 'performance_metrics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(String(50), nullable=False, index=True)
    strategy_version = Column(String(20), nullable=False)
    date = Column(DateTime, nullable=False, index=True)  # 统计日期
    total_return = Column(SQLDecimal(10, 6))  # 总收益率
    daily_return = Column(SQLDecimal(10, 6))  # 日收益率
    sharpe_ratio = Column(SQLDecimal(10, 6))  # 夏普比率
    max_drawdown = Column(SQLDecimal(10, 6))  # 最大回撤
    win_rate = Column(SQLDecimal(10, 6))  # 胜率
    profit_factor = Column(SQLDecimal(10, 6))  # 盈亏比
    total_trades = Column(Integer, default=0)  # 总交易数
    winning_trades = Column(Integer, default=0)  # 盈利交易数
    losing_trades = Column(Integer, default=0)  # 亏损交易数
    avg_win = Column(SQLDecimal(20, 8))  # 平均盈利
    avg_loss = Column(SQLDecimal(20, 8))  # 平均亏损
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联关系
    # strategy_version_rel = relationship("StrategyVersion", back_populates="performance_metrics")
    
    # 索引
    __table_args__ = (
        Index('idx_strategy_date', 'strategy_id', 'date'),
        Index('idx_version_date', 'strategy_version', 'date'),
    )


class SystemConfig(Base):
    """系统配置表"""
    __tablename__ = 'system_configs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(100), unique=True, nullable=False, index=True)
    config_value = Column(JSON)
    config_type = Column(String(20), default='system')  # system/risk/monitoring
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RiskEvent(Base):
    """风险事件表"""
    __tablename__ = 'risk_events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(50), unique=True, nullable=False, index=True)
    strategy_id = Column(String(50), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)  # 事件类型
    severity = Column(String(20), nullable=False)  # 严重程度: low/medium/high/critical
    message = Column(Text, nullable=False)  # 事件消息
    data = Column(JSON)  # 事件数据
    is_resolved = Column(Boolean, default=False)  # 是否已解决
    resolved_at = Column(DateTime)  # 解决时间
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # 索引
    __table_args__ = (
        Index('idx_strategy_severity', 'strategy_id', 'severity'),
        Index('idx_event_type', 'event_type'),
    )


class ABTest(Base):
    """A/B测试表"""
    __tablename__ = 'ab_tests'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    test_id = Column(String(50), unique=True, nullable=False, index=True)
    test_name = Column(String(100), nullable=False)
    strategy_a_id = Column(String(50), nullable=False)  # 策略A ID
    strategy_a_version = Column(String(20), nullable=False)
    strategy_b_id = Column(String(50), nullable=False)  # 策略B ID
    strategy_b_version = Column(String(20), nullable=False)
    traffic_split = Column(SQLDecimal(5, 4), default=0.5)  # 流量分割比例
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)
    status = Column(String(20), default='running')  # running/completed/cancelled
    results = Column(JSON)  # 测试结果
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 索引
    __table_args__ = (
        Index('idx_test_status', 'status'),
        Index('idx_test_dates', 'start_date', 'end_date'),
    )


class TradingSession(Base):
    """交易会话表"""
    __tablename__ = 'trading_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), unique=True, nullable=False, index=True)
    strategy_id = Column(String(50), nullable=False, index=True)
    strategy_version = Column(String(20), nullable=False)
    status = Column(String(20), default='running')  # running/stopped/error
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    initial_capital = Column(SQLDecimal(20, 8))  # 初始资金
    final_capital = Column(SQLDecimal(20, 8))  # 最终资金
    total_pnl = Column(SQLDecimal(20, 8), default=0)  # 总盈亏
    total_trades = Column(Integer, default=0)  # 总交易数
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 索引
    __table_args__ = (
        Index('idx_strategy_session', 'strategy_id', 'session_id'),
        Index('idx_session_status', 'status'),
    )
