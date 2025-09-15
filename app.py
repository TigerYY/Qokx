#!/usr/bin/env python3
"""
okx自动交易系统 - 图形化界面
基于Streamlit构建的全流程交易系统界面
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
from typing import Dict, List, Optional
import asyncio
import threading
import os
import logging
from dotenv import load_dotenv
from src.utils.okx_rest_client import OKXRESTClient
from src.utils.okx_public_client import get_public_client

# 设置页面配置 - 必须在所有Streamlit命令之前
st.set_page_config(
    page_title="okx自动交易系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 导入实时交易组件
try:
    from src.trading.realtime_trading_engine import RealtimeTradingEngine
    from src.trading.strategy_execution_bridge import StrategyExecutionBridge
    from src.risk.realtime_risk_manager import RealtimeRiskManager, RiskEvent, RiskEventType
    from src.strategies.signal_fusion_engine import SignalFusionEngine
    from src.execution.order_execution_engine import OrderExecutionEngine
    from src.utils.position_manager import PositionManager
    from src.data.realtime_data_processor import RealtimeDataProcessor
    from src.config.settings import TradingConfig
    REALTIME_TRADING_AVAILABLE = True
except ImportError as e:
    # 延迟显示警告，直到页面配置完成
    REALTIME_TRADING_AVAILABLE = False
    IMPORT_ERROR_MESSAGE = f"实时交易组件导入失败: {e}，将使用模拟模式"

# 加载环境变量
load_dotenv()

# 自定义CSS样式
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 2rem;
}
.section-header {
    font-size: 1.5rem;
    color: #2c3e50;
    margin-bottom: 1rem;
    border-bottom: 2px solid #3498db;
    padding-bottom: 0.5rem;
}
.metric-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1rem;
    border-radius: 10px;
    margin: 0.5rem;
}
.status-running { color: #27ae60; }
.status-stopped { color: #e74c3c; }
.status-warning { color: #f39c12; }
</style>
""", unsafe_allow_html=True)

class TradingDashboard:
    def __init__(self):
        self.initialize_session_state()
        self.okx_client = None
        self.initialize_okx_client()
        
        # 初始化实时交易组件
        self.realtime_engine = None
        self.strategy_bridge = None
        self.risk_manager = None
        self.initialize_realtime_components()
    
    def initialize_okx_client(self):
        """初始化OKX客户端"""
        try:
            # 从环境变量获取API配置
            api_key = os.getenv('OKX_API_KEY')
            secret_key = os.getenv('OKX_SECRET_KEY')
            passphrase = os.getenv('OKX_PASSPHRASE')
            testnet = os.getenv('OKX_TESTNET', 'true').lower() == 'true'
            
            if api_key and secret_key and passphrase:
                self.okx_client = OKXRESTClient(
                    api_key=api_key,
                    secret_key=secret_key,
                    passphrase=passphrase,
                    testnet=testnet
                )
                st.session_state.api_connected = True
                network_type = "测试网" if testnet else "主网"
                st.success(f"✅ OKX API连接成功！当前使用{network_type}")
            else:
                st.session_state.api_connected = False
                st.warning("⚠️ API密钥未配置，将使用模拟数据模式")
                
        except Exception as e:
            st.error(f"❌ OKX客户端初始化失败: {e}")
            st.session_state.api_connected = False
    
    def initialize_realtime_components(self):
        """初始化实时交易组件"""
        if not REALTIME_TRADING_AVAILABLE:
            return
        
        try:
            # 创建交易配置
            config = TradingConfig(
                api_key=os.getenv('OKX_API_KEY', ''),
                secret_key=os.getenv('OKX_SECRET_KEY', ''),
                passphrase=os.getenv('OKX_PASSPHRASE', ''),
                testnet=os.getenv('OKX_TESTNET', 'true').lower() == 'true',
                max_position_size=st.session_state.risk_limits['max_position_size'],
                max_daily_loss=st.session_state.risk_limits['max_daily_loss'],
                max_drawdown=st.session_state.risk_limits['max_drawdown'],
                stop_loss_pct=st.session_state.risk_limits['stop_loss'],
                take_profit_pct=st.session_state.risk_limits['take_profit']
            )
            
            # 初始化核心组件
            if st.session_state.api_connected and self.okx_client:
                # 使用真实API
                self.realtime_engine = RealtimeTradingEngine(
                    okx_client=self.okx_client,
                    config=config
                )
                
                # 初始化策略执行桥接器
                self.strategy_bridge = StrategyExecutionBridge(
                    strategy_engine=None,  # 将在启动时初始化
                    execution_engine=None,  # 将在启动时初始化
                    risk_manager=None,     # 将在启动时初始化
                    config=config
                )
                
                st.session_state.realtime_trading_enabled = True
                st.success("✅ 实时交易组件初始化成功")
            else:
                st.info("ℹ️ 实时交易组件已准备就绪，等待API连接")
                
        except Exception as e:
            st.error(f"❌ 实时交易组件初始化失败: {e}")
            st.session_state.realtime_trading_enabled = False
    
    def initialize_session_state(self):
        """初始化会话状态"""
        if 'initialized' not in st.session_state:
            st.session_state.initialized = True
            st.session_state.trading_status = "stopped"
            st.session_state.account_balance = 10000.0
            st.session_state.equity_curve = []
            st.session_state.trades = []
            st.session_state.signals = []
            st.session_state.risk_level = "medium"
            st.session_state.api_connected = False
            st.session_state.trading_status = "stopped"
            st.session_state.market_data = self.get_market_data('1H', 100)
            st.session_state.current_timeframe = '1H'
            
            # 实时交易状态
            st.session_state.realtime_trading_enabled = False
            st.session_state.realtime_trading_active = False
            st.session_state.strategy_running = False
            st.session_state.risk_monitoring = False
            st.session_state.risk_events = []
            st.session_state.portfolio_metrics = {}
            st.session_state.trading_statistics = {}
            st.session_state.selected_strategy = "信号融合策略"
            st.session_state.trading_active = False
            st.session_state.risk_limits = {
                'max_position_size': 0.2,
                'max_daily_loss': 0.05,
                'max_drawdown': 0.15,
                'stop_loss': 0.02,
                'take_profit': 0.04
            }
    
    def get_market_data(self, timeframe='1H', limit=100) -> Dict[str, pd.DataFrame]:
        """获取市场数据 - 优先使用公共API，然后私有API，最后使用模拟数据"""
        # 首先尝试使用公共API（无需API密钥）
        try:
            public_data = self.get_public_market_data(timeframe, limit)
            if public_data:
                # 显示数据来源提示
                if not st.session_state.get('public_api_info_shown', False):
                    st.success("✅ 正在使用OKX公共API获取实时市场数据")
                    st.session_state.public_api_info_shown = True
                return public_data
        except Exception as e:
            st.warning(f"⚠️ 公共API获取失败: {e}，尝试使用私有API")
        
        # 如果公共API失败，尝试使用私有API（需要API密钥）
        if st.session_state.api_connected and self.okx_client:
            try:
                real_data = self.get_real_market_data(timeframe, limit)
                if real_data:
                    st.info("ℹ️ 正在使用私有API获取市场数据")
                    return real_data
            except Exception as e:
                st.error(f"❌ 私有API获取失败: {e}")
        
        # 最后使用模拟数据作为后备
        st.warning("⚠️ 真实数据获取失败，使用模拟数据")
        return self.generate_sample_data()
    
    def get_public_market_data(self, timeframe='1H', limit=100) -> Dict[str, pd.DataFrame]:
        """使用公共API获取OKX市场数据（无需API密钥）"""
        try:
            # 获取公共API客户端
            public_client = get_public_client()
            
            # 获取BTC-USDT的K线数据
            candles = asyncio.run(public_client.get_candles(
                inst_id='BTC-USDT',
                bar=timeframe,
                limit=limit
            ))
            
            if not candles:
                return {}
            
            # 转换K线数据为DataFrame
            data_list = []
            for candle in candles:
                # OKX K线数据格式: [timestamp, open, high, low, close, volume, volCcy, volCcyQuote, confirm]
                data_list.append({
                    'timestamp': datetime.datetime.fromtimestamp(int(candle[0]) / 1000),
                    'open': float(candle[1]),
                    'high': float(candle[2]),
                    'low': float(candle[3]),
                    'close': float(candle[4]),
                    'volume': float(candle[5])
                })
            
            df = pd.DataFrame(data_list)
            df = df.sort_values('timestamp')
            
            return {'BTC-USDT': df}
            
        except Exception as e:
            st.error(f"❌ 获取公共市场数据失败: {e}")
            return {}
    
    def get_real_market_data(self, timeframe='1H', limit=100) -> Dict[str, pd.DataFrame]:
        """获取真实OKX市场数据（需要API密钥）"""
        try:
            # 获取BTC-USDT的K线数据
            candles = asyncio.run(self.okx_client.get_candles(
                inst_id='BTC-USDT',
                bar=timeframe,
                limit=limit
            ))
            
            if not candles:
                return {}
            
            # 转换K线数据为DataFrame
            data_list = []
            for candle in candles:
                # OKX K线数据格式: [timestamp, open, high, low, close, volume, volCcy, volCcyQuote, confirm]
                data_list.append({
                    'timestamp': datetime.datetime.fromtimestamp(int(candle[0]) / 1000),
                    'open': float(candle[1]),
                    'high': float(candle[2]),
                    'low': float(candle[3]),
                    'close': float(candle[4]),
                    'volume': float(candle[5])
                })
            
            df = pd.DataFrame(data_list)
            df = df.sort_values('timestamp')
            
            return {'BTC-USDT': df}
            
        except Exception as e:
            st.error(f"❌ 获取真实市场数据失败: {e}")
            return {}
    
    def generate_sample_data(self) -> Dict[str, pd.DataFrame]:
        """生成示例市场数据（后备方案）- 使用接近真实BTC价格的数据"""
        dates = pd.date_range(end=datetime.datetime.now(), periods=100, freq='h')
        
        # 使用接近真实BTC价格的基准价格（约95000 USDT）
        base_price = 95000
        # 生成价格波动数据（±2%的随机波动）
        price_changes = np.random.normal(0, 0.005, 100)  # 0.5%的标准差
        prices = base_price * (1 + np.cumsum(price_changes))
        
        # 确保价格在合理范围内（90000-100000）
        prices = np.clip(prices, 90000, 100000)
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices * (1 + np.random.normal(0, 0.001, 100)),
            'high': prices * (1 + np.abs(np.random.normal(0, 0.002, 100))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.002, 100))),
            'close': prices,
            'volume': np.random.randint(50, 500, 100)  # 更真实的成交量范围
        })
        
        return {'BTC-USDT': data}
    
    def render_sidebar(self):
        """渲染侧边栏"""
        with st.sidebar:
            st.markdown("<div class='main-header'>📊 okx自动交易系统</div>", unsafe_allow_html=True)
            
            # 系统状态
            st.markdown("### 🔄 系统状态")
            status_color = "status-running" if st.session_state.trading_status == "running" else "status-stopped"
            st.markdown(f"**状态:** <span class='{status_color}'>● {st.session_state.trading_status.upper()}</span>", unsafe_allow_html=True)
            
            # 交易控制
            st.markdown("### ⚙️ 交易控制")
            
            # 实时交易控制
            if REALTIME_TRADING_AVAILABLE and st.session_state.realtime_trading_enabled:
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🚀 启动实时交易", use_container_width=True, type="primary"):
                        asyncio.run(self.start_realtime_trading())
                with col2:
                    if st.button("⏹️ 停止实时交易", use_container_width=True):
                        asyncio.run(self.stop_realtime_trading())
                
                # 策略控制
                st.markdown("**策略控制**")
                col3, col4 = st.columns(2)
                with col3:
                    if st.button("📊 启动策略", use_container_width=True, disabled=not st.session_state.strategy_running):
                        self.start_strategy_monitoring()
                with col4:
                    if st.button("🛡️ 启动风控", use_container_width=True, disabled=not st.session_state.risk_monitoring):
                        self.start_risk_monitoring()
            else:
                # 模拟交易控制
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("▶️ 启动模拟交易", use_container_width=True):
                        self.start_trading()
                with col2:
                    if st.button("⏹️ 停止模拟交易", use_container_width=True):
                        self.stop_trading()
            
            # 策略配置
            st.markdown("### 🎯 策略配置")
            selected_symbol = st.selectbox("交易对", ["BTC-USDT", "ETH-USDT", "SOL-USDT"], index=0, key="trading_symbol")
            
            if REALTIME_TRADING_AVAILABLE:
                strategy_type = st.selectbox(
                    "策略类型", 
                    ["信号融合策略", "市场状态检测策略", "网格交易策略", "DCA定投策略"], 
                    index=0,
                    key="strategy_type"
                )
                st.session_state.selected_strategy = strategy_type
            
            risk_ratio = st.slider("风险比例", 0.1, 5.0, 1.0, 0.1, key="risk_ratio")
            max_position = st.slider("最大仓位", 0.1, 0.5, st.session_state.risk_limits['max_position_size'], 0.05, key="max_position")
            st.session_state.risk_limits['max_position_size'] = max_position
            
            # 风控设置
            st.markdown("### 🛡️ 风控设置")
            stop_loss = st.slider("止损比例(%)", 0.5, 10.0, st.session_state.risk_limits['stop_loss']*100, 0.5, key="stop_loss") / 100
            take_profit = st.slider("止盈比例(%)", 1.0, 20.0, st.session_state.risk_limits['take_profit']*100, 0.5, key="take_profit") / 100
            max_drawdown = st.slider("最大回撤(%)", 5.0, 30.0, st.session_state.risk_limits['max_drawdown']*100, 1.0, key="max_drawdown") / 100
            max_daily_loss = st.slider("日最大损失(%)", 1.0, 10.0, st.session_state.risk_limits['max_daily_loss']*100, 0.5, key="max_daily_loss") / 100
            
            # 更新风险限制
            st.session_state.risk_limits.update({
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'max_drawdown': max_drawdown,
                'max_daily_loss': max_daily_loss
            })
            
            # 实时状态显示
            if REALTIME_TRADING_AVAILABLE:
                st.markdown("### 📊 实时状态")
                col1, col2 = st.columns(2)
                with col1:
                    strategy_status = "🟢 运行中" if st.session_state.strategy_running else "🔴 已停止"
                    st.markdown(f"**策略状态:** {strategy_status}")
                with col2:
                    risk_status = "🟢 监控中" if st.session_state.risk_monitoring else "🔴 已停止"
                    st.markdown(f"**风控状态:** {risk_status}")
                
                # 风险事件计数
                active_events = len([e for e in st.session_state.risk_events if not e.get('resolved', False)])
                if active_events > 0:
                    st.warning(f"⚠️ 活跃风险事件: {active_events} 个")
    
    def render_header_metrics(self):
        """渲染头部指标卡片"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class='metric-card'>
                <h3>💰 账户余额</h3>
                <h2>{:,.2f} USDT</h2>
            </div>
            """.format(st.session_state.account_balance), unsafe_allow_html=True)
        
        with col2:
            win_rate = len([t for t in st.session_state.trades if t.get('pnl', 0) > 0]) / max(len(st.session_state.trades), 1)
            st.markdown("""
            <div class='metric-card'>
                <h3>📈 胜率</h3>
                <h2>{:.1%}</h2>
            </div>
            """.format(win_rate), unsafe_allow_html=True)
        
        with col3:
            total_pnl = sum(t.get('pnl', 0) for t in st.session_state.trades)
            st.markdown("""
            <div class='metric-card'>
                <h3>💹 总盈亏</h3>
                <h2>{:,.2f} USDT</h2>
            </div>
            """.format(total_pnl), unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div class='metric-card'>
                <h3>⚡ 风险等级</h3>
                <h2>{}</h2>
            </div>
            """.format(st.session_state.risk_level.upper()), unsafe_allow_html=True)
    
    def render_price_chart(self):
        """渲染价格图表"""
        st.markdown("<div class='section-header'>📊 实时价格图表</div>", unsafe_allow_html=True)
        
        # 时间周期选择器
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            timeframe = st.selectbox(
                "时间周期",
                options=['1m', '5m', '15m', '30m', '1H', '4H', '1D'],
                index=4,  # 默认选择1H
                key='timeframe_selector'
            )
        with col2:
            limit = st.selectbox(
                "数据量",
                options=[50, 100, 200, 500],
                index=1,  # 默认100
                key='limit_selector'
            )
        with col3:
            if st.button("🔄 刷新数据", use_container_width=True):
                st.session_state.market_data = self.get_market_data(timeframe, limit)
                st.rerun()
        
        # 获取当前时间周期的数据
        if 'current_timeframe' not in st.session_state or st.session_state.current_timeframe != timeframe:
            st.session_state.current_timeframe = timeframe
            st.session_state.market_data = self.get_market_data(timeframe, limit)
        
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.08,
            subplot_titles=(f'BTC-USDT K线图 ({timeframe})', '成交量'),
            row_heights=[0.7, 0.3]
        )
        
        # 添加K线图
        data = st.session_state.market_data.get('BTC-USDT', pd.DataFrame())
        if not data.empty:
            fig.add_trace(
                go.Candlestick(
                    x=data['timestamp'],
                    open=data['open'],
                    high=data['high'],
                    low=data['low'],
                    close=data['close'],
                    name='BTC-USDT',
                    increasing_line_color='#00ff88',
                    decreasing_line_color='#ff4444',
                    increasing_fillcolor='#00ff88',
                    decreasing_fillcolor='#ff4444'
                ),
                row=1, col=1
            )
            
            # 添加成交量
            colors = ['#00ff88' if close >= open else '#ff4444' 
                     for close, open in zip(data['close'], data['open'])]
            
            fig.add_trace(
                go.Bar(
                    x=data['timestamp'],
                    y=data['volume'],
                    name='成交量',
                    marker_color=colors,
                    opacity=0.7
                ),
                row=2, col=1
            )
            
            # 显示当前价格信息
            if len(data) > 0:
                latest = data.iloc[-1]
                price_change = latest['close'] - latest['open']
                price_change_pct = (price_change / latest['open']) * 100
                
                st.markdown(f"""
                <div style='background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%); 
                           color: white; padding: 1rem; border-radius: 10px; margin: 1rem 0;'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <h3 style='margin: 0; color: #fff;'>BTC-USDT</h3>
                            <h2 style='margin: 0; color: #fff;'>${latest['close']:,.2f}</h2>
                        </div>
                        <div style='text-align: right;'>
                            <div style='color: {"#00ff88" if price_change >= 0 else "#ff4444"};'>
                                {'+' if price_change >= 0 else ''}{price_change:,.2f} ({price_change_pct:+.2f}%)
                            </div>
                            <div style='font-size: 0.9em; opacity: 0.8;'>
                                最高: ${latest['high']:,.2f} | 最低: ${latest['low']:,.2f}
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        fig.update_layout(
            height=600,
            showlegend=False,
            xaxis_rangeslider_visible=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            xaxis=dict(
                gridcolor='rgba(128,128,128,0.2)',
                showgrid=True
            ),
            yaxis=dict(
                gridcolor='rgba(128,128,128,0.2)',
                showgrid=True
            ),
            xaxis2=dict(
                gridcolor='rgba(128,128,128,0.2)',
                showgrid=True
            ),
            yaxis2=dict(
                gridcolor='rgba(128,128,128,0.2)',
                showgrid=True
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_strategy_performance(self):
        """渲染策略性能"""
        st.markdown("<div class='section-header'>📈 策略性能分析</div>", unsafe_allow_html=True)
        
        # 策略选择和配置区域
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 🎯 可用策略列表")
            
            # 策略信息
            strategies = {
                "信号融合策略": {
                    "描述": "基于多种技术指标的信号融合，包括趋势、动量和波动性分析",
                    "风险等级": "中等",
                    "适用市场": "震荡和趋势市场",
                    "状态": "开发中"
                },
                "市场状态检测策略": {
                    "描述": "自动识别市场状态（趋势/震荡），动态调整交易参数",
                    "风险等级": "低",
                    "适用市场": "全市场",
                    "状态": "开发中"
                },
                "网格交易策略": {
                    "描述": "在价格区间内进行网格化买卖，适合震荡市场",
                    "风险等级": "中等",
                    "适用市场": "震荡市场",
                    "状态": "规划中"
                },
                "DCA定投策略": {
                    "描述": "定期定额投资，平摊成本，适合长期投资",
                    "风险等级": "低",
                    "适用市场": "长期上涨趋势",
                    "状态": "规划中"
                }
            }
            
            # 显示策略卡片
            for strategy_name, info in strategies.items():
                with st.expander(f"📊 {strategy_name}", expanded=False):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write(f"**描述**: {info['描述']}")
                        st.write(f"**风险等级**: {info['风险等级']}")
                    with col_b:
                        st.write(f"**适用市场**: {info['适用市场']}")
                        status_color = "🟢" if info['状态'] == "运行中" else "🟡" if info['状态'] == "开发中" else "🔴"
                        st.write(f"**状态**: {status_color} {info['状态']}")
        
        with col2:
            st.markdown("### ⚙️ 策略配置")
            selected_strategy = st.selectbox(
                "选择策略",
                list(strategies.keys()),
                help="选择要配置和运行的交易策略"
            )
            
            if st.button("🚀 启动策略", use_container_width=True):
                if REALTIME_TRADING_AVAILABLE:
                    try:
                        # 启动选定的策略
                        if self._start_selected_strategy(selected_strategy):
                            st.success(f"✅ {selected_strategy} 已成功启动！")
                            st.session_state.strategy_running = True
                            st.session_state.selected_strategy = selected_strategy
                        else:
                            st.error("❌ 策略启动失败，请检查配置")
                    except Exception as e:
                        st.error(f"❌ 策略启动异常: {str(e)}")
                        logger.error(f"策略启动异常: {e}")
                else:
                    st.warning("⚠️ 实时交易组件不可用，请检查依赖安装")
            
            if st.button("📊 回测策略", use_container_width=True):
                if REALTIME_TRADING_AVAILABLE:
                    try:
                        # 启动回测
                        if self._run_strategy_backtest(selected_strategy):
                            st.success(f"✅ {selected_strategy} 回测完成！")
                        else:
                            st.error("❌ 回测失败，请检查配置")
                    except Exception as e:
                        st.error(f"❌ 回测异常: {str(e)}")
                        logger.error(f"回测异常: {e}")
                else:
                    st.warning("⚠️ 回测组件不可用，请检查依赖安装")
        
        st.markdown("---")
        
        # 性能分析区域
        col3, col4 = st.columns(2)
        
        with col3:
            st.markdown("### 📈 权益曲线")
            # 权益曲线
            if st.session_state.equity_curve:
                equity_df = pd.DataFrame(st.session_state.equity_curve, columns=['timestamp', 'equity'])
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=equity_df['timestamp'],
                    y=equity_df['equity'],
                    mode='lines',
                    name='权益曲线',
                    line=dict(color='#3498db', width=2)
                ))
                fig.update_layout(
                    title='账户权益曲线',
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                # 显示示例权益曲线
                dates = pd.date_range(end=datetime.datetime.now(), periods=30, freq='D')
                equity_values = 10000 * (1 + np.cumsum(np.random.normal(0.001, 0.02, 30)))
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=equity_values,
                    mode='lines',
                    name='示例权益曲线',
                    line=dict(color='#95a5a6', width=2, dash='dash')
                ))
                fig.update_layout(
                    title='权益曲线（示例数据）',
                    height=300,
                    annotations=[
                        dict(
                            text="暂无实际交易数据",
                            xref="paper", yref="paper",
                            x=0.5, y=0.5, xanchor='center', yanchor='middle',
                            showarrow=False,
                            font=dict(size=16, color="gray")
                        )
                    ]
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col4:
            st.markdown("### 📊 交易统计")
            # 交易统计
            if st.session_state.trades:
                trades_df = pd.DataFrame(st.session_state.trades)
                win_trades = trades_df[trades_df['pnl'] > 0]
                loss_trades = trades_df[trades_df['pnl'] <= 0]
                
                stats_data = {
                    '指标': ['总交易数', '盈利交易', '亏损交易', '平均盈利', '平均亏损', '盈亏比'],
                    '数值': [
                        len(trades_df),
                        len(win_trades),
                        len(loss_trades),
                        win_trades['pnl'].mean() if not win_trades.empty else 0,
                        loss_trades['pnl'].mean() if not loss_trades.empty else 0,
                        abs(win_trades['pnl'].sum() / loss_trades['pnl'].sum()) if not loss_trades.empty else float('inf')
                    ]
                }
                
                st.dataframe(pd.DataFrame(stats_data), use_container_width=True)
            else:
                # 显示默认统计信息
                st.info("📋 **策略统计概览**")
                st.markdown("""
                - **总交易数**: 0
                - **盈利交易**: 0
                - **亏损交易**: 0
                - **胜率**: 0%
                - **平均盈亏比**: N/A
                - **最大回撤**: N/A
                
                💡 **提示**: 启动策略后将显示实时统计数据
                """)
    
    def render_trade_log(self):
        """渲染交易日志"""
        st.markdown("<div class='section-header'>📋 交易记录</div>", unsafe_allow_html=True)
        
        if st.session_state.trades:
            trades_df = pd.DataFrame(st.session_state.trades)
            trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'])
            trades_df = trades_df.sort_values('timestamp', ascending=False)
            
            # 样式化数据框
            def color_pnl(val):
                color = 'green' if val > 0 else 'red' if val < 0 else 'gray'
                return f'color: {color}; font-weight: bold'
            
            styled_df = trades_df.head(10).style.applymap(color_pnl, subset=['pnl'])
            st.dataframe(styled_df, use_container_width=True)
        else:
            st.info("暂无交易记录")
    
    def render_risk_dashboard(self):
        """渲染风险控制面板"""
        st.markdown("<div class='section-header'>🛡️ 风险监控</div>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("当前风险等级", st.session_state.risk_level.upper())
            st.progress(0.6 if st.session_state.risk_level == "medium" else 0.3 if st.session_state.risk_level == "low" else 0.9)
        
        with col2:
            max_drawdown = self.calculate_max_drawdown()
            st.metric("最大回撤", f"{max_drawdown:.1%}")
            st.progress(min(max_drawdown / 0.3, 1.0))  # 假设30%为最大可接受回撤
        
        with col3:
            volatility = self.calculate_volatility()
            st.metric("波动率", f"{volatility:.1%}")
            st.progress(min(volatility / 0.1, 1.0))  # 假设10%为高波动率阈值
    
    def calculate_max_drawdown(self) -> float:
        """计算最大回撤"""
        if not st.session_state.equity_curve:
            return 0.0
        
        equities = [e[1] for e in st.session_state.equity_curve]
        peak = equities[0]
        max_drawdown = 0.0
        
        for equity in equities:
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak
            max_drawdown = max(max_drawdown, drawdown)
        
        return max_drawdown
    
    def calculate_volatility(self) -> float:
        """计算波动率"""
        if len(st.session_state.equity_curve) < 2:
            return 0.0
        
        equities = [e[1] for e in st.session_state.equity_curve]
        returns = np.diff(equities) / equities[:-1]
        
        if len(returns) == 0:
            return 0.0
        
        return np.std(returns)
    
    def start_trading(self):
        """启动模拟交易"""
        if not st.session_state.get('trading_active', False):
            st.session_state.trading_active = True
            st.session_state.trading_status = "running"
            threading.Thread(target=self.simulate_trading, daemon=True).start()
            st.success("✅ 模拟交易已启动")
        else:
            st.warning("⚠️ 模拟交易已在运行中")
    
    def stop_trading(self):
        """停止模拟交易"""
        if st.session_state.get('trading_active', False):
            st.session_state.trading_active = False
            st.session_state.trading_status = "stopped"
            st.success("✅ 模拟交易已停止")
        else:
            st.warning("⚠️ 模拟交易未在运行")
    
    async def start_realtime_trading(self):
        """启动实时交易"""
        if not REALTIME_TRADING_AVAILABLE:
            st.error("❌ 实时交易组件不可用")
            return
        
        if st.session_state.get('realtime_trading_active', False):
            st.warning("⚠️ 实时交易已在运行中")
            return
        
        try:
            # 初始化实时交易引擎
            if hasattr(self, 'realtime_engine') and self.realtime_engine:
                await self.realtime_engine.start()
                st.session_state.realtime_trading_active = True
                st.session_state.strategy_running = True
                st.session_state.risk_monitoring = True
                st.success("🚀 实时交易已启动")
                
                # 启动策略执行桥接器
                if hasattr(self, 'strategy_bridge') and self.strategy_bridge:
                    await self.strategy_bridge.start()
                    st.success("📊 策略执行桥接器已启动")
            else:
                st.error("❌ 实时交易引擎未初始化")
                
        except Exception as e:
            st.error(f"❌ 启动实时交易失败: {e}")
            st.session_state.realtime_trading_active = False
    
    async def stop_realtime_trading(self):
        """停止实时交易"""
        if not st.session_state.get('realtime_trading_active', False):
            st.warning("⚠️ 实时交易未在运行")
            return
        
        try:
            # 停止策略执行桥接器
            if hasattr(self, 'strategy_bridge') and self.strategy_bridge:
                await self.strategy_bridge.stop()
                st.info("📊 策略执行桥接器已停止")
            
            # 停止实时交易引擎
            if hasattr(self, 'realtime_engine') and self.realtime_engine:
                await self.realtime_engine.stop()
                st.session_state.realtime_trading_active = False
                st.session_state.strategy_running = False
                st.session_state.risk_monitoring = False
                st.success("⏹️ 实时交易已停止")
            
        except Exception as e:
            st.error(f"❌ 停止实时交易失败: {e}")
    
    def _start_selected_strategy(self, strategy_name: str) -> bool:
        """启动选定的策略"""
        try:
            if not REALTIME_TRADING_AVAILABLE:
                return False
            
            # 获取当前配置
            symbol = st.session_state.get('trading_symbol', 'BTC-USDT')
            risk_ratio = st.session_state.get('risk_ratio', 1.0)
            max_position = st.session_state.get('max_position', 0.3)
            
            # 初始化交易引擎（如果还没有初始化）
            if not hasattr(self, 'trading_engine') or self.trading_engine is None:
                from src.trading.realtime_trading_engine import initialize_trading_engine
                from src.config.settings import TradingConfig
                
                # 创建交易配置
                config = TradingConfig(
                    commission_rate=0.001,
                    slippage=0.0005,
                    max_position_size=max_position,
                    risk_multiplier=risk_ratio
                )
                
                # 初始化交易引擎
                self.trading_engine = initialize_trading_engine(
                    config=config,
                    okx_client=self.okx_client,
                    symbol=symbol
                )
            
            # 启动交易引擎
            if self.trading_engine:
                # 在后台启动交易
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # 启动交易引擎
                success = loop.run_until_complete(self.trading_engine.start_trading())
                
                if success:
                    st.session_state.strategy_name = strategy_name
                    st.session_state.strategy_symbol = symbol
                    return True
            
            return False
            
        except Exception as e:
             logger.error(f"启动策略失败: {e}")
             return False
    
    def _run_strategy_backtest(self, strategy_name: str) -> bool:
        """运行策略回测"""
        try:
            if not REALTIME_TRADING_AVAILABLE:
                return False
            
            # 获取当前配置
            symbol = st.session_state.get('trading_symbol', 'BTC-USDT')
            risk_ratio = st.session_state.get('risk_ratio', 1.0)
            max_position = st.session_state.get('max_position', 0.3)
            
            # 显示回测进度
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text('🔄 正在准备回测数据...')
            progress_bar.progress(20)
            
            # 导入回测引擎
            from src.backtest.backtest_engine import BacktestEngine
            from src.config.settings import TradingConfig
            
            # 创建回测配置
            config = TradingConfig(
                commission_rate=0.001,
                slippage=0.0005,
                max_position_size=max_position,
                risk_multiplier=risk_ratio
            )
            
            status_text.text('📊 正在初始化回测引擎...')
            progress_bar.progress(40)
            
            # 初始化回测引擎
            backtest_engine = BacktestEngine(config)
            
            status_text.text('🚀 正在运行回测...')
            progress_bar.progress(60)
            
            # 运行回测（使用最近30天的数据）
            from datetime import datetime, timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            # 运行回测
            results = backtest_engine.run_backtest(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                strategy_name=strategy_name
            )
            
            status_text.text('📈 正在生成回测报告...')
            progress_bar.progress(80)
            
            # 显示回测结果
            if results:
                st.session_state.backtest_results = results
                self._display_backtest_results(results)
                
                progress_bar.progress(100)
                status_text.text('✅ 回测完成！')
                return True
            else:
                status_text.text('❌ 回测失败')
                return False
                
        except Exception as e:
            logger.error(f"回测失败: {e}")
            st.error(f"回测过程中出现错误: {str(e)}")
            return False
    
    def _display_backtest_results(self, results: dict):
        """显示回测结果"""
        st.markdown("### 📊 回测结果")
        
        # 创建指标展示
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_return = results.get('total_return', 0)
            st.metric("总收益率", f"{total_return:.2%}")
        
        with col2:
            sharpe_ratio = results.get('sharpe_ratio', 0)
            st.metric("夏普比率", f"{sharpe_ratio:.2f}")
        
        with col3:
            max_drawdown = results.get('max_drawdown', 0)
            st.metric("最大回撤", f"{max_drawdown:.2%}")
        
        with col4:
            win_rate = results.get('win_rate', 0)
            st.metric("胜率", f"{win_rate:.2%}")
        
        # 显示权益曲线
        if 'equity_curve' in results:
            equity_data = results['equity_curve']
            if equity_data:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=list(range(len(equity_data))),
                    y=equity_data,
                    mode='lines',
                    name='权益曲线',
                    line=dict(color='#1f77b4', width=2)
                ))
                
                fig.update_layout(
                    title='回测权益曲线',
                    xaxis_title='时间',
                    yaxis_title='权益',
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    def start_strategy_monitoring(self):
        """启动策略监控"""
        if not st.session_state.strategy_running:
            st.session_state.strategy_running = True
            st.success("📊 策略监控已启动")
        else:
            st.warning("⚠️ 策略监控已在运行中")
    
    def start_risk_monitoring(self):
        """启动风险监控"""
        if not st.session_state.risk_monitoring:
            st.session_state.risk_monitoring = True
            st.success("🛡️ 风险监控已启动")
        else:
            st.warning("⚠️ 风险监控已在运行中")
    
    def simulate_trading(self):
        """模拟交易逻辑"""
        import time
        
        while st.session_state.get('trading_active', False):
            try:
                # 更新市场数据
                st.session_state.market_data = self.get_market_data()
                
                # 模拟交易信号
                if np.random.random() < 0.2:  # 20%的概率生成交易信号
                    direction = "BUY" if np.random.random() > 0.5 else "SELL"
                    
                    # 获取当前实时价格（如果可用）
                    current_price = self.get_current_price()
                    if current_price is None:
                        # 使用最后一条K线的收盘价作为后备
                        current_price = st.session_state.market_data['BTC-USDT']['close'].iloc[-1]
                    
                    quantity = np.random.uniform(0.01, 0.1)
                    
                    trade = {
                        'timestamp': datetime.datetime.now(),
                        'direction': direction,
                        'price': current_price,
                        'quantity': quantity,
                        'pnl': np.random.normal(0, 50),
                        'status': 'FILLED'
                    }
                    
                    st.session_state.trades.append(trade)
                    
                    # 更新权益曲线
                    current_equity = st.session_state.account_balance + sum(t['pnl'] for t in st.session_state.trades)
                    st.session_state.equity_curve.append((datetime.datetime.now(), current_equity))
                
                time.sleep(5)  # 每5秒检查一次
                
            except Exception as e:
                st.error(f"交易执行错误: {e}")
                time.sleep(10)  # 出错时等待更长时间
    
    def get_current_price(self) -> Optional[float]:
        """获取当前实时价格"""
        if st.session_state.api_connected and self.okx_client:
            try:
                # 获取实时ticker数据
                ticker = asyncio.run(self.okx_client.get_ticker('BTC-USDT'))
                if ticker and 'last' in ticker:
                    return float(ticker['last'])
            except Exception as e:
                st.warning(f"获取实时价格失败: {e}")
        return None
    
    def run(self):
        """运行仪表板"""
        self.render_sidebar()
        
        # 主内容区域
        st.markdown("<div class='main-header'>🚀 okx自动交易系统仪表板</div>", unsafe_allow_html=True)
        
        # 显示延迟的导入错误消息
        if not REALTIME_TRADING_AVAILABLE and 'IMPORT_ERROR_MESSAGE' in globals():
            st.warning(IMPORT_ERROR_MESSAGE)
        
        self.render_header_metrics()
        
        # 选项卡布局
        tab1, tab2, tab3, tab4 = st.tabs(["📊 市场", "📈 策略", "📋 交易", "🛡️ 风控"])
        
        with tab1:
            self.render_price_chart()
        
        with tab2:
            self.render_strategy_performance()
        
        with tab3:
            self.render_trade_log()
        
        with tab4:
            self.render_risk_dashboard()

def main():
    """主函数"""
    dashboard = TradingDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()