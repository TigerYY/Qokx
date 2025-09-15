#!/usr/bin/env python3
"""
交易状态监控系统
实时监控交易状态、性能指标和系统健康状况
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path


class MonitorEventType(Enum):
    """监控事件类型"""
    TRADE_EXECUTED = "trade_executed"
    STRATEGY_SIGNAL = "strategy_signal"
    RISK_EVENT = "risk_event"
    SYSTEM_ERROR = "system_error"
    PERFORMANCE_UPDATE = "performance_update"
    CONNECTION_STATUS = "connection_status"


class SystemStatus(Enum):
    """系统状态"""
    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    OFFLINE = "offline"


@dataclass
class MonitorEvent:
    """监控事件"""
    event_type: MonitorEventType
    timestamp: datetime
    data: Dict[str, Any]
    severity: str = "info"  # info, warning, error, critical
    source: str = "system"
    message: str = ""


@dataclass
class PerformanceMetrics:
    """性能指标"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class SystemHealth:
    """系统健康状况"""
    overall_status: SystemStatus = SystemStatus.HEALTHY
    api_connection: bool = True
    strategy_engine: bool = True
    execution_engine: bool = True
    risk_manager: bool = True
    data_feed: bool = True
    last_heartbeat: datetime = field(default_factory=datetime.now)
    error_count: int = 0
    warning_count: int = 0


class TradingMonitor:
    """交易监控系统"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # 设置日志
        self.setup_logging()
        
        # 监控状态
        self.is_running = False
        self.events: List[MonitorEvent] = []
        self.performance = PerformanceMetrics()
        self.system_health = SystemHealth()
        
        # 事件回调
        self.event_callbacks: Dict[MonitorEventType, List[callable]] = {
            event_type: [] for event_type in MonitorEventType
        }
        
        # 监控配置
        self.max_events = 10000  # 最大事件数量
        self.heartbeat_interval = 30  # 心跳间隔（秒）
        self.performance_update_interval = 60  # 性能更新间隔（秒）
    
    def setup_logging(self):
        """设置日志系统"""
        # 创建日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 交易日志
        self.trade_logger = logging.getLogger('trading')
        self.trade_logger.setLevel(logging.INFO)
        trade_handler = logging.FileHandler(
            self.log_dir / f"trading_{datetime.now().strftime('%Y%m%d')}.log"
        )
        trade_handler.setFormatter(formatter)
        self.trade_logger.addHandler(trade_handler)
        
        # 系统日志
        self.system_logger = logging.getLogger('system')
        self.system_logger.setLevel(logging.INFO)
        system_handler = logging.FileHandler(
            self.log_dir / f"system_{datetime.now().strftime('%Y%m%d')}.log"
        )
        system_handler.setFormatter(formatter)
        self.system_logger.addHandler(system_handler)
        
        # 错误日志
        self.error_logger = logging.getLogger('error')
        self.error_logger.setLevel(logging.ERROR)
        error_handler = logging.FileHandler(
            self.log_dir / f"error_{datetime.now().strftime('%Y%m%d')}.log"
        )
        error_handler.setFormatter(formatter)
        self.error_logger.addHandler(error_handler)
    
    async def start(self):
        """启动监控系统"""
        if self.is_running:
            return
        
        self.is_running = True
        self.system_logger.info("交易监控系统启动")
        
        # 启动监控任务
        await asyncio.gather(
            self.heartbeat_task(),
            self.performance_update_task(),
            self.cleanup_task()
        )
    
    async def stop(self):
        """停止监控系统"""
        self.is_running = False
        self.system_logger.info("交易监控系统停止")
    
    def log_event(self, event: MonitorEvent):
        """记录监控事件"""
        # 添加到事件列表
        self.events.append(event)
        
        # 限制事件数量
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events//2:]
        
        # 记录到日志文件
        log_message = f"{event.source} - {event.message} - {json.dumps(event.data, default=str)}"
        
        if event.event_type == MonitorEventType.TRADE_EXECUTED:
            self.trade_logger.info(log_message)
        elif event.severity == "error" or event.severity == "critical":
            self.error_logger.error(log_message)
            self.system_health.error_count += 1
        elif event.severity == "warning":
            self.system_logger.warning(log_message)
            self.system_health.warning_count += 1
        else:
            self.system_logger.info(log_message)
        
        # 触发回调
        for callback in self.event_callbacks.get(event.event_type, []):
            try:
                callback(event)
            except Exception as e:
                self.error_logger.error(f"事件回调执行失败: {e}")
    
    def log_trade(self, trade_data: Dict[str, Any]):
        """记录交易事件"""
        event = MonitorEvent(
            event_type=MonitorEventType.TRADE_EXECUTED,
            timestamp=datetime.now(),
            data=trade_data,
            source="execution_engine",
            message=f"交易执行: {trade_data.get('symbol', 'Unknown')} {trade_data.get('side', 'Unknown')} {trade_data.get('quantity', 0)}"
        )
        self.log_event(event)
        
        # 更新性能指标
        self.update_performance_from_trade(trade_data)
    
    def log_strategy_signal(self, signal_data: Dict[str, Any]):
        """记录策略信号"""
        event = MonitorEvent(
            event_type=MonitorEventType.STRATEGY_SIGNAL,
            timestamp=datetime.now(),
            data=signal_data,
            source="strategy_engine",
            message=f"策略信号: {signal_data.get('signal', 'Unknown')} - {signal_data.get('symbol', 'Unknown')}"
        )
        self.log_event(event)
    
    def log_risk_event(self, risk_data: Dict[str, Any]):
        """记录风险事件"""
        severity = "warning" if risk_data.get('risk_level', 'low') in ['medium', 'high'] else "error"
        event = MonitorEvent(
            event_type=MonitorEventType.RISK_EVENT,
            timestamp=datetime.now(),
            data=risk_data,
            severity=severity,
            source="risk_manager",
            message=f"风险事件: {risk_data.get('event_type', 'Unknown')} - {risk_data.get('description', '')}"
        )
        self.log_event(event)
    
    def log_system_error(self, error_data: Dict[str, Any]):
        """记录系统错误"""
        event = MonitorEvent(
            event_type=MonitorEventType.SYSTEM_ERROR,
            timestamp=datetime.now(),
            data=error_data,
            severity="error",
            source=error_data.get('source', 'system'),
            message=f"系统错误: {error_data.get('error', 'Unknown error')}"
        )
        self.log_event(event)
    
    def update_performance_from_trade(self, trade_data: Dict[str, Any]):
        """从交易数据更新性能指标"""
        pnl = trade_data.get('pnl', 0.0)
        
        self.performance.total_trades += 1
        self.performance.total_pnl += pnl
        
        if pnl > 0:
            self.performance.winning_trades += 1
        elif pnl < 0:
            self.performance.losing_trades += 1
        
        # 计算胜率
        if self.performance.total_trades > 0:
            self.performance.win_rate = self.performance.winning_trades / self.performance.total_trades
        
        # 计算平均盈亏
        if self.performance.winning_trades > 0:
            winning_pnl = sum(t.get('pnl', 0) for t in [trade_data] if t.get('pnl', 0) > 0)
            self.performance.avg_win = winning_pnl / self.performance.winning_trades
        
        if self.performance.losing_trades > 0:
            losing_pnl = sum(abs(t.get('pnl', 0)) for t in [trade_data] if t.get('pnl', 0) < 0)
            self.performance.avg_loss = losing_pnl / self.performance.losing_trades
        
        # 计算盈亏比
        if self.performance.avg_loss > 0:
            self.performance.profit_factor = self.performance.avg_win / self.performance.avg_loss
        
        self.performance.last_updated = datetime.now()
    
    def update_system_health(self, component: str, status: bool, error_msg: str = None):
        """更新系统健康状况"""
        setattr(self.system_health, component, status)
        self.system_health.last_heartbeat = datetime.now()
        
        if not status and error_msg:
            self.log_system_error({
                'component': component,
                'error': error_msg,
                'source': 'health_monitor'
            })
        
        # 更新整体状态
        components = [
            self.system_health.api_connection,
            self.system_health.strategy_engine,
            self.system_health.execution_engine,
            self.system_health.risk_manager,
            self.system_health.data_feed
        ]
        
        if all(components):
            self.system_health.overall_status = SystemStatus.HEALTHY
        elif any(components):
            self.system_health.overall_status = SystemStatus.WARNING
        else:
            self.system_health.overall_status = SystemStatus.ERROR
    
    def add_event_callback(self, event_type: MonitorEventType, callback: callable):
        """添加事件回调"""
        self.event_callbacks[event_type].append(callback)
    
    def get_recent_events(self, event_type: Optional[MonitorEventType] = None, 
                         limit: int = 100) -> List[MonitorEvent]:
        """获取最近的事件"""
        events = self.events
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        return sorted(events, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        return {
            'total_trades': self.performance.total_trades,
            'win_rate': round(self.performance.win_rate * 100, 2),
            'total_pnl': round(self.performance.total_pnl, 2),
            'avg_win': round(self.performance.avg_win, 2),
            'avg_loss': round(self.performance.avg_loss, 2),
            'profit_factor': round(self.performance.profit_factor, 2),
            'max_drawdown': round(self.performance.max_drawdown, 2),
            'last_updated': self.performance.last_updated.isoformat()
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'overall_status': self.system_health.overall_status.value,
            'components': {
                'api_connection': self.system_health.api_connection,
                'strategy_engine': self.system_health.strategy_engine,
                'execution_engine': self.system_health.execution_engine,
                'risk_manager': self.system_health.risk_manager,
                'data_feed': self.system_health.data_feed
            },
            'error_count': self.system_health.error_count,
            'warning_count': self.system_health.warning_count,
            'last_heartbeat': self.system_health.last_heartbeat.isoformat()
        }
    
    async def heartbeat_task(self):
        """心跳任务"""
        while self.is_running:
            try:
                # 更新心跳时间
                self.system_health.last_heartbeat = datetime.now()
                
                # 检查组件状态（这里可以添加实际的健康检查逻辑）
                # 例如：检查API连接、数据库连接等
                
                await asyncio.sleep(self.heartbeat_interval)
                
            except Exception as e:
                self.error_logger.error(f"心跳任务错误: {e}")
                await asyncio.sleep(5)
    
    async def performance_update_task(self):
        """性能更新任务"""
        while self.is_running:
            try:
                # 记录性能更新事件
                event = MonitorEvent(
                    event_type=MonitorEventType.PERFORMANCE_UPDATE,
                    timestamp=datetime.now(),
                    data=self.get_performance_summary(),
                    source="monitor",
                    message="性能指标更新"
                )
                self.log_event(event)
                
                await asyncio.sleep(self.performance_update_interval)
                
            except Exception as e:
                self.error_logger.error(f"性能更新任务错误: {e}")
                await asyncio.sleep(10)
    
    async def cleanup_task(self):
        """清理任务"""
        while self.is_running:
            try:
                # 清理旧的日志文件（保留30天）
                cutoff_date = datetime.now() - timedelta(days=30)
                
                for log_file in self.log_dir.glob("*.log"):
                    if log_file.stat().st_mtime < cutoff_date.timestamp():
                        log_file.unlink()
                        self.system_logger.info(f"删除旧日志文件: {log_file}")
                
                # 每天执行一次清理
                await asyncio.sleep(24 * 3600)
                
            except Exception as e:
                self.error_logger.error(f"清理任务错误: {e}")
                await asyncio.sleep(3600)  # 出错时1小时后重试


# 全局监控实例
trading_monitor = TradingMonitor()