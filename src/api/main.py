#!/usr/bin/env python3
"""
FastAPI 后端服务
为React前端提供API接口
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager
import threading
import time

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

from ..database.connection import init_database, get_db_session
from ..database.repository import (
    TradeRepository, StrategyRepository, ConfigRepository, 
    PerformanceRepository, ABTestRepository
)
from ..config.dynamic_config import init_config_manager
from ..strategies.version_control import get_strategy_version_manager, get_ab_test_manager
from ..utils.okx_public_client import get_public_client
from .grid_trading import router as grid_trading_router

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WebSocket连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # 连接已断开，移除
                self.disconnect(connection)

manager = ConnectionManager()

# 实时数据缓存
price_cache = {
    "BTC-USDT": {
        "last": 0,
        "change24h": 0,
        "changePercent24h": 0,
        "volume24h": 0,
        "timestamp": 0
    }
}

# 实时数据更新任务
def update_price_data():
    """定时更新价格数据"""
    while True:
        try:
            client = get_public_client()
            
            # 更新BTC-USDT价格
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            ticker = loop.run_until_complete(client.get_ticker("BTC-USDT"))
            if ticker:
                price_cache["BTC-USDT"] = {
                    "last": float(ticker.get("last", 0)),
                    "change24h": float(ticker.get("chg", 0)),
                    "changePercent24h": float(ticker.get("chgPct", 0)),
                    "volume24h": float(ticker.get("vol24h", 0)),
                    "timestamp": int(ticker.get("ts", 0))
                }
                
                # 广播价格更新
                price_update = {
                    "type": "price_update",
                    "symbol": "BTC-USDT",
                    "data": price_cache["BTC-USDT"]
                }
                asyncio.run(manager.broadcast(str(price_update)))
                
            loop.close()
            
        except Exception as e:
            logger.error(f"更新价格数据失败: {e}")
        
        time.sleep(10)  # 每10秒更新一次

# 启动价格更新线程
price_update_thread = threading.Thread(target=update_price_data, daemon=True)

# 请求模型
class TradeCreate(BaseModel):
    strategy_id: str
    symbol: str
    direction: str
    order_type: str
    price: float
    quantity: float

class StrategyCreate(BaseModel):
    name: str
    description: str
    version: str
    class_path: str
    config: Dict[str, Any]

class StrategyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

class ConfigUpdate(BaseModel):
    config_key: str
    config_value: Any
    config_type: str = 'strategy'

class ABTestCreate(BaseModel):
    test_name: str
    strategy_a_id: str
    strategy_a_version: str
    strategy_b_id: str
    strategy_b_version: str
    traffic_split: float
    duration_days: int

# 响应模型
class ApiResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    timestamp: str = datetime.utcnow().isoformat()

class PaginatedResponse(ApiResponse):
    pagination: Optional[Dict[str, int]] = None

# 应用生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    logger.info("启动API服务...")
    init_database()
    init_config_manager()
    
    # 启动价格更新线程
    price_update_thread.start()
    logger.info("价格更新线程已启动")
    
    logger.info("API服务启动完成")
    
    yield
    
    # 关闭时
    logger.info("关闭API服务...")

# 创建FastAPI应用
app = FastAPI(
    title="OKX Trading System API",
    description="基于OKX的自动化交易系统API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 依赖注入
def get_trade_repository():
    with get_db_session() as session:
        return TradeRepository(session)

def get_strategy_repository():
    with get_db_session() as session:
        return StrategyRepository(session)

def get_config_repository():
    with get_db_session() as session:
        return ConfigRepository(session)

def get_performance_repository():
    with get_db_session() as session:
        return PerformanceRepository(session)

# 注册路由
app.include_router(grid_trading_router)

# 根路径
@app.get("/")
async def root():
    return {"message": "OKX Trading System API", "version": "1.0.0"}

# 健康检查
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# 交易相关API
@app.get("/trading/dashboard")
async def get_dashboard_data():
    """获取仪表板数据"""
    try:
        # 模拟数据
        dashboard_data = {
            "dashboardStats": {
                "totalBalance": 125000,
                "totalPnl": 8500,
                "winRate": 68.5,
                "activeStrategies": 3,
                "totalTrades": 1247,
                "riskLevel": "medium",
                "systemStatus": "healthy"
            },
            "recentTrades": [],
            "performanceData": [],
            "priceData": []
        }
        
        return ApiResponse(success=True, data=dashboard_data)
    except Exception as e:
        logger.error(f"获取仪表板数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trading/trades")
async def get_trades(
    page: int = 0,
    limit: int = 10,
    strategy_id: Optional[str] = None,
    symbol: Optional[str] = None,
    trade_repo: TradeRepository = Depends(get_trade_repository)
):
    """获取交易记录"""
    try:
        trades = trade_repo.get_trades_by_strategy(
            strategy_id or "default", 
            limit=limit, 
            offset=page * limit
        )
        
        # 转换为字典格式
        trades_data = []
        for trade in trades:
            trades_data.append({
                "id": trade.id,
                "tradeId": trade.trade_id,
                "strategyId": trade.strategy_id,
                "symbol": trade.symbol,
                "direction": trade.direction,
                "price": float(trade.price),
                "quantity": float(trade.quantity),
                "pnl": float(trade.pnl),
                "timestamp": trade.timestamp.isoformat(),
                "status": trade.status
            })
        
        return PaginatedResponse(
            success=True,
            data=trades_data,
            pagination={
                "page": page,
                "limit": limit,
                "total": len(trades_data),
                "totalPages": (len(trades_data) + limit - 1) // limit
            }
        )
    except Exception as e:
        logger.error(f"获取交易记录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trading/trades")
async def create_trade(
    trade_data: TradeCreate,
    trade_repo: TradeRepository = Depends(get_trade_repository)
):
    """创建交易记录"""
    try:
        trade_record = {
            "trade_id": f"trade_{datetime.utcnow().timestamp()}",
            "strategy_id": trade_data.strategy_id,
            "strategy_version": "1.0.0",
            "symbol": trade_data.symbol,
            "direction": trade_data.direction,
            "order_type": trade_data.order_type,
            "price": trade_data.price,
            "quantity": trade_data.quantity,
            "amount": trade_data.price * trade_data.quantity,
            "commission": 0,
            "pnl": 0,
            "status": "FILLED",
            "timestamp": datetime.utcnow()
        }
        
        trade = trade_repo.create_trade(trade_record)
        
        # 广播WebSocket消息
        await manager.broadcast(f"新交易: {trade_data.symbol} {trade_data.direction}")
        
        return ApiResponse(success=True, data={"tradeId": trade.trade_id})
    except Exception as e:
        logger.error(f"创建交易记录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 策略相关API
@app.get("/strategies")
async def get_strategies(strategy_repo: StrategyRepository = Depends(get_strategy_repository)):
    """获取策略列表"""
    try:
        strategies = strategy_repo.get_all_strategies()
        
        strategies_data = []
        for strategy in strategies:
            strategies_data.append({
                "id": strategy.id,
                "strategyId": strategy.strategy_id,
                "name": strategy.name,
                "version": strategy.version,
                "description": strategy.description,
                "isActive": strategy.is_active,
                "isTesting": strategy.is_testing,
                "createdAt": strategy.created_at.isoformat(),
                "updatedAt": strategy.updated_at.isoformat()
            })
        
        return ApiResponse(success=True, data=strategies_data)
    except Exception as e:
        logger.error(f"获取策略列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/strategies/{strategy_id}")
async def get_strategy(
    strategy_id: str,
    strategy_repo: StrategyRepository = Depends(get_strategy_repository)
):
    """获取策略详情"""
    try:
        strategy = strategy_repo.get_active_strategy(strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="策略未找到")
        
        strategy_data = {
            "id": strategy.id,
            "strategyId": strategy.strategy_id,
            "name": strategy.name,
            "version": strategy.version,
            "description": strategy.description,
            "config": strategy.config,
            "isActive": strategy.is_active,
            "isTesting": strategy.is_testing,
            "createdAt": strategy.created_at.isoformat(),
            "updatedAt": strategy.updated_at.isoformat()
        }
        
        return ApiResponse(success=True, data=strategy_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取策略详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/strategies")
async def create_strategy(
    strategy_data: StrategyCreate,
    strategy_repo: StrategyRepository = Depends(get_strategy_repository)
):
    """创建策略"""
    try:
        strategy_record = {
            "strategy_id": f"strategy_{datetime.utcnow().timestamp()}",
            "version": strategy_data.version,
            "name": strategy_data.name,
            "description": strategy_data.description,
            "class_path": strategy_data.class_path,
            "config": strategy_data.config,
            "is_active": False,
            "is_testing": False
        }
        
        strategy = strategy_repo.create_strategy_version(strategy_record)
        
        return ApiResponse(success=True, data={"strategyId": strategy.strategy_id})
    except Exception as e:
        logger.error(f"创建策略失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/strategies/{strategy_id}/start")
async def start_strategy(
    strategy_id: str,
    strategy_repo: StrategyRepository = Depends(get_strategy_repository)
):
    """启动策略"""
    try:
        # 先获取策略的最新版本
        strategy = strategy_repo.get_active_strategy(strategy_id)
        if not strategy:
            # 如果没有激活的策略，获取最新版本
            strategies = strategy_repo.get_strategy_versions(strategy_id)
            if not strategies:
                raise HTTPException(status_code=404, detail="策略未找到")
            strategy = strategies[0]  # 获取最新版本
        
        success = strategy_repo.activate_strategy_version(strategy_id, strategy.version)
        if not success:
            raise HTTPException(status_code=400, detail="启动策略失败")
        
        # 广播WebSocket消息
        await manager.broadcast(f"策略 {strategy_id} 已启动")
        
        return ApiResponse(success=True, message="策略启动成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动策略失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/strategies/{strategy_id}/stop")
async def stop_strategy(
    strategy_id: str,
    strategy_repo: StrategyRepository = Depends(get_strategy_repository)
):
    """停止策略"""
    try:
        success = strategy_repo.deactivate_strategy(strategy_id)
        if not success:
            raise HTTPException(status_code=400, detail="停止策略失败")
        
        # 广播WebSocket消息
        await manager.broadcast(f"策略 {strategy_id} 已停止")
        
        return ApiResponse(success=True, message="策略停止成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"停止策略失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 配置相关API
@app.get("/config/strategy/{strategy_id}")
async def get_strategy_config(
    strategy_id: str,
    config_repo: ConfigRepository = Depends(get_config_repository)
):
    """获取策略配置"""
    try:
        configs = config_repo.get_all_strategy_configs(strategy_id)
        return ApiResponse(success=True, data=configs)
    except Exception as e:
        logger.error(f"获取策略配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/config/strategy")
async def update_strategy_config(
    config_data: ConfigUpdate,
    config_repo: ConfigRepository = Depends(get_config_repository)
):
    """更新策略配置"""
    try:
        config = config_repo.set_strategy_config(
            strategy_id=config_data.config_key.split('_')[0],
            config_key=config_data.config_key,
            config_value=config_data.config_value,
            config_type=config_data.config_type
        )
        
        # 广播WebSocket消息
        await manager.broadcast(f"配置已更新: {config_data.config_key}")
        
        return ApiResponse(success=True, message="配置更新成功")
    except Exception as e:
        logger.error(f"更新策略配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 性能相关API
@app.get("/trading/performance")
async def get_performance_metrics(
    strategy_id: Optional[str] = None,
    days: int = 30,
    performance_repo: PerformanceRepository = Depends(get_performance_repository)
):
    """获取性能指标"""
    try:
        if strategy_id:
            metrics = performance_repo.get_performance_history(strategy_id, days)
        else:
            metrics = []
        
        metrics_data = []
        for metric in metrics:
            metrics_data.append({
                "date": metric.date.isoformat(),
                "totalReturn": float(metric.total_return),
                "dailyReturn": float(metric.daily_return),
                "sharpeRatio": float(metric.sharpe_ratio),
                "maxDrawdown": float(metric.max_drawdown),
                "winRate": float(metric.win_rate),
                "profitFactor": float(metric.profit_factor),
                "totalTrades": metric.total_trades
            })
        
        return ApiResponse(success=True, data=metrics_data)
    except Exception as e:
        logger.error(f"获取性能指标失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 市场数据API
@app.get("/market/data")
async def get_market_data(symbol: str = "BTC-USDT", timeframe: str = "1H", limit: int = 100):
    """获取市场数据 - 从OKX API获取真实数据"""
    try:
        client = get_public_client()
        
        # 获取K线数据
        candles = await client.get_candles(inst_id=symbol, bar=timeframe, limit=limit)
        
        # 转换数据格式
        data = []
        for candle in candles:
            # OKX K线数据格式: [timestamp, open, high, low, close, volume, volCcy, volCcyQuote, confirm]
            data.append({
                "timestamp": int(candle[0]),  # 时间戳(毫秒)
                "open": float(candle[1]),     # 开盘价
                "high": float(candle[2]),     # 最高价
                "low": float(candle[3]),      # 最低价
                "close": float(candle[4]),    # 收盘价
                "volume": float(candle[5]),   # 成交量
                "volCcy": float(candle[6]),   # 成交额(币种)
                "volCcyQuote": float(candle[7])  # 成交额(计价币种)
            })
        
        return ApiResponse(success=True, data=data)
    except Exception as e:
        logger.error(f"获取市场数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/market/ticker")
async def get_ticker_data(symbol: str = "BTC-USDT"):
    """获取实时价格数据"""
    try:
        # 优先使用缓存数据
        if symbol in price_cache and price_cache[symbol]["last"] > 0:
            cached_data = price_cache[symbol]
            ticker_data = {
                "symbol": symbol,
                "last": cached_data["last"],
                "change24h": cached_data["change24h"],
                "changePercent24h": cached_data["changePercent24h"],
                "volume24h": cached_data["volume24h"],
                "timestamp": cached_data["timestamp"]
            }
            return ApiResponse(success=True, data=ticker_data)
        
        # 如果缓存没有数据，则实时获取
        client = get_public_client()
        ticker = await client.get_ticker(symbol)
        
        if not ticker:
            raise HTTPException(status_code=404, detail="未找到该交易对数据")
        
        # 转换数据格式
        ticker_data = {
            "symbol": ticker.get("instId"),
            "last": float(ticker.get("last", 0)),
            "open24h": float(ticker.get("open24h", 0)),
            "high24h": float(ticker.get("high24h", 0)),
            "low24h": float(ticker.get("low24h", 0)),
            "volume24h": float(ticker.get("vol24h", 0)),
            "change24h": float(ticker.get("chg", 0)),
            "changePercent24h": float(ticker.get("chgPct", 0)),
            "timestamp": int(ticker.get("ts", 0))
        }
        
        return ApiResponse(success=True, data=ticker_data)
    except Exception as e:
        logger.error(f"获取实时价格数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/market/price-chart")
async def get_price_chart_data(symbol: str = "BTC-USDT", timeframe: str = "1H", limit: int = 24):
    """获取价格图表数据 - 专门为前端图表优化"""
    try:
        client = get_public_client()
        
        # 获取K线数据
        candles = await client.get_candles(inst_id=symbol, bar=timeframe, limit=limit)
        
        # 转换数据格式为前端图表所需格式
        chart_data = []
        for candle in candles:
            # 转换时间戳为可读格式
            timestamp = int(candle[0])
            time_str = datetime.fromtimestamp(timestamp / 1000).strftime("%H:%M")
            
            chart_data.append({
                "time": time_str,
                "price": float(candle[4]),  # 收盘价
                "open": float(candle[1]),   # 开盘价
                "high": float(candle[2]),   # 最高价
                "low": float(candle[3]),    # 最低价
                "volume": float(candle[5]), # 成交量
                "timestamp": timestamp
            })
        
        # 按时间排序（从早到晚）
        chart_data.sort(key=lambda x: x["timestamp"])
        
        return ApiResponse(success=True, data=chart_data)
    except Exception as e:
        logger.error(f"获取价格图表数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# A/B测试API
@app.get("/ab-tests")
async def get_ab_tests(ab_test_repo: ABTestRepository = Depends(get_ab_test_manager)):
    """获取A/B测试列表"""
    try:
        tests = ab_test_repo.get_active_ab_tests()
        
        tests_data = []
        for test in tests:
            tests_data.append({
                "id": test.id,
                "testId": test.test_id,
                "testName": test.test_name,
                "strategyAId": test.strategy_a_id,
                "strategyAVersion": test.strategy_a_version,
                "strategyBId": test.strategy_b_id,
                "strategyBVersion": test.strategy_b_version,
                "trafficSplit": float(test.traffic_split),
                "status": test.status,
                "startDate": test.start_date.isoformat(),
                "endDate": test.end_date.isoformat() if test.end_date else None
            })
        
        return ApiResponse(success=True, data=tests_data)
    except Exception as e:
        logger.error(f"获取A/B测试列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ab-tests")
async def create_ab_test(
    test_data: ABTestCreate,
    ab_test_repo: ABTestRepository = Depends(get_ab_test_manager)
):
    """创建A/B测试"""
    try:
        test_id = ab_test_repo.create_ab_test(
            test_name=test_data.test_name,
            strategy_a_id=test_data.strategy_a_id,
            strategy_a_version=test_data.strategy_a_version,
            strategy_b_id=test_data.strategy_b_id,
            strategy_b_version=test_data.strategy_b_version,
            traffic_split=test_data.traffic_split,
            duration_days=test_data.duration_days
        )
        
        return ApiResponse(success=True, data={"testId": test_id})
    except Exception as e:
        logger.error(f"创建A/B测试失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket连接
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # 保持连接活跃
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# 错误处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"全局异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "服务器内部错误",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
