"""
网格交易API接口
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database.connection import get_db_session
from ..strategies.grid_config import GridConfig, GridTradingState, create_default_grid_config
from ..strategies.grid_trading_strategy import GridTradingStrategy
from ..strategies.grid_signal_generator import GridSignalGenerator
from ..execution.order_manager import global_order_manager
from ..risk.realtime_risk_manager import RealtimeRiskManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/grid-trading", tags=["网格交易"])

# 全局网格策略实例
grid_strategies: Dict[str, GridTradingStrategy] = {}


class GridConfigRequest(BaseModel):
    """网格配置请求"""
    strategy_name: str = Field(..., description="策略名称")
    symbol: str = Field(..., description="交易对")
    base_quantity: float = Field(..., description="基础交易数量")
    grid_type: str = Field("ARITHMETIC", description="网格类型")
    grid_direction: str = Field("BOTH", description="网格方向")
    grid_count: int = Field(10, description="网格数量")
    grid_spacing: float = Field(0.01, description="网格间距")
    center_price: Optional[float] = Field(None, description="中心价格")
    upper_price: Optional[float] = Field(None, description="上限价格")
    lower_price: Optional[float] = Field(None, description="下限价格")
    max_position: float = Field(1000, description="最大持仓")
    stop_loss_price: Optional[float] = Field(None, description="止损价格")
    take_profit_price: Optional[float] = Field(None, description="止盈价格")
    max_drawdown: float = Field(0.05, description="最大回撤限制")
    total_capital: float = Field(10000, description="总资金")
    position_ratio: float = Field(0.8, description="仓位比例")
    reserve_ratio: float = Field(0.2, description="预留比例")
    commission_rate: float = Field(0.001, description="手续费率")
    slippage: float = Field(0.0005, description="滑点")
    min_trade_amount: float = Field(10, description="最小交易金额")
    enable_dynamic_adjustment: bool = Field(True, description="启用动态调整")
    adjustment_threshold: float = Field(0.02, description="调整阈值")
    rebalance_interval: int = Field(3600, description="重新平衡间隔(秒)")
    enable_trailing_stop: bool = Field(False, description="启用跟踪止损")
    trailing_stop_distance: float = Field(0.02, description="跟踪止损距离")
    enable_partial_fill: bool = Field(True, description="启用部分成交")
    max_partial_fills: int = Field(3, description="最大部分成交次数")


class GridConfigResponse(BaseModel):
    """网格配置响应"""
    strategy_id: str
    strategy_name: str
    symbol: str
    config: Dict[str, Any]
    created_at: str
    status: str


class GridTradingStateResponse(BaseModel):
    """网格交易状态响应"""
    strategy_id: str
    current_price: float
    total_position: float
    total_pnl: float
    realized_pnl: float
    unrealized_pnl: float
    total_commission: float
    active_orders: int
    filled_orders: int
    grid_levels: List[Dict[str, Any]]
    last_update_time: str


class GridPerformanceResponse(BaseModel):
    """网格性能响应"""
    strategy_id: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    realized_pnl: float
    unrealized_pnl: float
    total_commission: float
    max_drawdown: float
    current_position: float
    active_grids: int
    total_grids: int


class GridSignalResponse(BaseModel):
    """网格信号响应"""
    signal_type: str
    price: float
    quantity: float
    grid_level: int
    confidence: float
    reason: str
    timestamp: str


@router.post("/configs", response_model=GridConfigResponse)
async def create_grid_config(
    config_request: GridConfigRequest,
    db: Session = Depends(get_db_session)
):
    """创建网格交易配置"""
    try:
        # 创建配置对象
        config = GridConfig(
            strategy_id=f"grid_{config_request.symbol.lower()}_{int(datetime.now().timestamp())}",
            strategy_name=config_request.strategy_name,
            symbol=config_request.symbol,
            base_quantity=Decimal(str(config_request.base_quantity)),
            grid_type=config_request.grid_type,
            grid_direction=config_request.grid_direction,
            grid_count=config_request.grid_count,
            grid_spacing=Decimal(str(config_request.grid_spacing)),
            center_price=Decimal(str(config_request.center_price)) if config_request.center_price else None,
            upper_price=Decimal(str(config_request.upper_price)) if config_request.upper_price else None,
            lower_price=Decimal(str(config_request.lower_price)) if config_request.lower_price else None,
            max_position=Decimal(str(config_request.max_position)),
            stop_loss_price=Decimal(str(config_request.stop_loss_price)) if config_request.stop_loss_price else None,
            take_profit_price=Decimal(str(config_request.take_profit_price)) if config_request.take_profit_price else None,
            max_drawdown=Decimal(str(config_request.max_drawdown)),
            total_capital=Decimal(str(config_request.total_capital)),
            position_ratio=Decimal(str(config_request.position_ratio)),
            reserve_ratio=Decimal(str(config_request.reserve_ratio)),
            commission_rate=Decimal(str(config_request.commission_rate)),
            slippage=Decimal(str(config_request.slippage)),
            min_trade_amount=Decimal(str(config_request.min_trade_amount)),
            enable_dynamic_adjustment=config_request.enable_dynamic_adjustment,
            adjustment_threshold=Decimal(str(config_request.adjustment_threshold)),
            rebalance_interval=config_request.rebalance_interval,
            enable_trailing_stop=config_request.enable_trailing_stop,
            trailing_stop_distance=Decimal(str(config_request.trailing_stop_distance)),
            enable_partial_fill=config_request.enable_partial_fill,
            max_partial_fills=config_request.max_partial_fills
        )
        
        # 保存配置到数据库（这里简化处理）
        # 实际应该保存到数据库
        
        return GridConfigResponse(
            strategy_id=config.strategy_id,
            strategy_name=config.strategy_name,
            symbol=config.symbol,
            config=config.to_dict(),
            created_at=datetime.now().isoformat(),
            status="created"
        )
        
    except Exception as e:
        logger.error(f"创建网格配置失败: {e}")
        raise HTTPException(status_code=400, detail=f"创建网格配置失败: {str(e)}")


@router.get("/configs", response_model=List[GridConfigResponse])
async def get_grid_configs(
    symbol: Optional[str] = Query(None, description="交易对过滤"),
    db: Session = Depends(get_db_session)
):
    """获取网格交易配置列表"""
    try:
        # 模拟配置数据
        configs = [
            GridConfigResponse(
                strategy_id="grid_btc_usdt_001",
                strategy_name="BTC-USDT网格策略",
                symbol="BTC-USDT",
                config=create_default_grid_config("BTC-USDT", Decimal("10000")).to_dict(),
                created_at=datetime.now().isoformat(),
                status="active"
            ),
            GridConfigResponse(
                strategy_id="grid_eth_usdt_001",
                strategy_name="ETH-USDT网格策略",
                symbol="ETH-USDT",
                config=create_default_grid_config("ETH-USDT", Decimal("5000")).to_dict(),
                created_at=datetime.now().isoformat(),
                status="inactive"
            )
        ]
        
        if symbol:
            configs = [c for c in configs if c.symbol == symbol]
        
        return configs
        
    except Exception as e:
        logger.error(f"获取网格配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取网格配置失败: {str(e)}")


@router.get("/configs/{strategy_id}", response_model=GridConfigResponse)
async def get_grid_config(
    strategy_id: str,
    db: Session = Depends(get_db_session)
):
    """获取特定网格配置"""
    try:
        # 模拟配置数据
        config = GridConfigResponse(
            strategy_id=strategy_id,
            strategy_name="BTC-USDT网格策略",
            symbol="BTC-USDT",
            config=create_default_grid_config("BTC-USDT", Decimal("10000")).to_dict(),
            created_at=datetime.now().isoformat(),
            status="active"
        )
        
        return config
        
    except Exception as e:
        logger.error(f"获取网格配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取网格配置失败: {str(e)}")


@router.post("/strategies/{strategy_id}/start")
async def start_grid_strategy(
    strategy_id: str,
    current_price: float = Query(..., description="当前价格"),
    db: Session = Depends(get_db_session)
):
    """启动网格交易策略"""
    try:
        # 创建风险管理器
        risk_manager = RealtimeRiskManager()
        
        # 创建网格策略实例
        config = create_default_grid_config("BTC-USDT", Decimal("10000"))
        strategy = GridTradingStrategy(config, global_order_manager, risk_manager)
        
        # 初始化策略
        success = await strategy.initialize(Decimal(str(current_price)))
        if not success:
            raise HTTPException(status_code=400, detail="策略初始化失败")
        
        # 启动策略
        await strategy.start()
        
        # 保存策略实例
        grid_strategies[strategy_id] = strategy
        
        return {
            "success": True,
            "message": "网格交易策略启动成功",
            "strategy_id": strategy_id,
            "current_price": current_price
        }
        
    except Exception as e:
        logger.error(f"启动网格策略失败: {e}")
        raise HTTPException(status_code=400, detail=f"启动网格策略失败: {str(e)}")


@router.post("/strategies/{strategy_id}/stop")
async def stop_grid_strategy(
    strategy_id: str,
    db: Session = Depends(get_db_session)
):
    """停止网格交易策略"""
    try:
        if strategy_id not in grid_strategies:
            raise HTTPException(status_code=404, detail="策略不存在")
        
        strategy = grid_strategies[strategy_id]
        await strategy.stop()
        
        # 移除策略实例
        del grid_strategies[strategy_id]
        
        return {
            "success": True,
            "message": "网格交易策略停止成功",
            "strategy_id": strategy_id
        }
        
    except Exception as e:
        logger.error(f"停止网格策略失败: {e}")
        raise HTTPException(status_code=400, detail=f"停止网格策略失败: {str(e)}")


@router.get("/strategies/{strategy_id}/state", response_model=GridTradingStateResponse)
async def get_grid_strategy_state(
    strategy_id: str,
    db: Session = Depends(get_db_session)
):
    """获取网格交易策略状态"""
    try:
        if strategy_id not in grid_strategies:
            # 返回模拟数据
            return GridTradingStateResponse(
                strategy_id=strategy_id,
                current_price=115851.5,
                total_position=0.5,
                total_pnl=1250.75,
                realized_pnl=800.25,
                unrealized_pnl=450.50,
                total_commission=25.30,
                active_orders=8,
                filled_orders=12,
                grid_levels=[
                    {
                        "level": 0,
                        "price": 115000.0,
                        "quantity": 0.1,
                        "order_type": "buy",
                        "is_active": True,
                        "filled_quantity": 0.0,
                        "avg_fill_price": 0.0
                    },
                    {
                        "level": 1,
                        "price": 115500.0,
                        "quantity": 0.1,
                        "order_type": "buy",
                        "is_active": True,
                        "filled_quantity": 0.0,
                        "avg_fill_price": 0.0
                    },
                    {
                        "level": 2,
                        "price": 116000.0,
                        "quantity": 0.1,
                        "order_type": "sell",
                        "is_active": True,
                        "filled_quantity": 0.0,
                        "avg_fill_price": 0.0
                    }
                ],
                last_update_time=datetime.now().isoformat()
            )
        
        strategy = grid_strategies[strategy_id]
        state = strategy.state
        
        return GridTradingStateResponse(
            strategy_id=strategy_id,
            current_price=float(state.current_price),
            total_position=float(state.total_position),
            total_pnl=float(state.total_pnl),
            realized_pnl=float(state.realized_pnl),
            unrealized_pnl=float(state.unrealized_pnl),
            total_commission=float(state.total_commission),
            active_orders=state.active_orders,
            filled_orders=state.filled_orders,
            grid_levels=[{
                "level": i,
                "price": float(level.price),
                "quantity": float(level.quantity),
                "order_type": level.order_type,
                "is_active": level.is_active,
                "filled_quantity": float(level.filled_quantity),
                "avg_fill_price": float(level.avg_fill_price)
            } for i, level in enumerate(state.grid_levels)],
            last_update_time=state.last_update_time or datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"获取网格策略状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取网格策略状态失败: {str(e)}")


@router.get("/strategies/{strategy_id}/performance", response_model=GridPerformanceResponse)
async def get_grid_strategy_performance(
    strategy_id: str,
    db: Session = Depends(get_db_session)
):
    """获取网格交易策略性能"""
    try:
        if strategy_id not in grid_strategies:
            # 返回模拟数据
            return GridPerformanceResponse(
                strategy_id=strategy_id,
                total_trades=24,
                winning_trades=16,
                losing_trades=8,
                win_rate=66.67,
                total_pnl=1250.75,
                realized_pnl=800.25,
                unrealized_pnl=450.50,
                total_commission=25.30,
                max_drawdown=2.5,
                current_position=0.5,
                active_grids=8,
                total_grids=10
            )
        
        strategy = grid_strategies[strategy_id]
        metrics = strategy.get_performance_metrics()
        
        return GridPerformanceResponse(
            strategy_id=strategy_id,
            **metrics
        )
        
    except Exception as e:
        logger.error(f"获取网格策略性能失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取网格策略性能失败: {str(e)}")


@router.get("/strategies/{strategy_id}/signals", response_model=List[GridSignalResponse])
async def get_grid_strategy_signals(
    strategy_id: str,
    limit: int = Query(10, description="信号数量限制"),
    db: Session = Depends(get_db_session)
):
    """获取网格交易策略信号"""
    try:
        if strategy_id not in grid_strategies:
            # 返回模拟数据
            return [
                GridSignalResponse(
                    signal_type="buy",
                    price=115000.0,
                    quantity=0.1,
                    grid_level=0,
                    confidence=0.9,
                    reason="买入网格触发",
                    timestamp=datetime.now().isoformat()
                ),
                GridSignalResponse(
                    signal_type="sell",
                    price=116000.0,
                    quantity=0.1,
                    grid_level=2,
                    confidence=0.8,
                    reason="卖出网格触发",
                    timestamp=datetime.now().isoformat()
                )
            ]
        
        strategy = grid_strategies[strategy_id]
        # 这里应该从策略中获取信号历史
        # 暂时返回空列表
        return []
        
    except Exception as e:
        logger.error(f"获取网格策略信号失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取网格策略信号失败: {str(e)}")


@router.post("/strategies/{strategy_id}/rebalance")
async def rebalance_grid_strategy(
    strategy_id: str,
    current_price: float = Query(..., description="当前价格"),
    db: Session = Depends(get_db_session)
):
    """重新平衡网格策略"""
    try:
        if strategy_id not in grid_strategies:
            raise HTTPException(status_code=404, detail="策略不存在")
        
        strategy = grid_strategies[strategy_id]
        success = await strategy.rebalance_grid(Decimal(str(current_price)))
        
        if not success:
            raise HTTPException(status_code=400, detail="重新平衡失败")
        
        return {
            "success": True,
            "message": "网格重新平衡成功",
            "strategy_id": strategy_id,
            "current_price": current_price
        }
        
    except Exception as e:
        logger.error(f"重新平衡网格策略失败: {e}")
        raise HTTPException(status_code=400, detail=f"重新平衡网格策略失败: {str(e)}")


@router.get("/strategies", response_model=List[Dict[str, Any]])
async def get_all_grid_strategies(
    db: Session = Depends(get_db_session)
):
    """获取所有网格交易策略"""
    try:
        strategies = []
        for strategy_id, strategy in grid_strategies.items():
            metrics = strategy.get_performance_metrics()
            strategies.append({
                "strategy_id": strategy_id,
                "symbol": strategy.config.symbol,
                "strategy_name": strategy.config.strategy_name,
                "status": "running" if strategy.is_running else "stopped",
                "total_pnl": metrics["total_pnl"],
                "win_rate": metrics["win_rate"],
                "active_grids": metrics["active_grids"],
                "total_grids": metrics["total_grids"]
            })
        
        return strategies
        
    except Exception as e:
        logger.error(f"获取网格策略列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取网格策略列表失败: {str(e)}")
