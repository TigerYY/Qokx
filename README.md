# 🚀 OKX自动交易系统 (Qokx)

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32.0-red.svg)](https://streamlit.io/)
[![OKX](https://img.shields.io/badge/OKX-API-orange.svg)](https://www.okx.com/docs-v5/)

一个基于OKX官方API的专业级加密货币现货自动化交易系统，提供完整的量化交易解决方案。

## 📋 项目概述

**Qokx** 是一个功能完整的加密货币自动交易系统，专为量化交易者、策略研究者和小型量化团队设计。系统通过接入OKX官方REST和WebSocket API，实现稳定、低延迟、低成本的自动化交易能力。

### 🎯 核心价值

- **🔄 自动化交易**: 完整的信号生成→订单执行→风险控制流程
- **📊 实时监控**: 多维度市场数据分析和账户状态监控
- **🛡️ 风险管理**: 机构级风险控制和资金管理系统
- **📈 策略框架**: 支持多策略组合和市场状态自适应
- **🎨 可视化界面**: 基于Streamlit的现代化Web界面
- **🔍 回测验证**: 专业级回测引擎和性能分析

## ✨ 功能特性

### 📊 实时数据与监控
- **多时间框架行情**: 1m/5m/15m/1h/4h/1d K线数据
- **实时账户监控**: 余额、持仓、订单状态实时更新
- **市场深度分析**: 订单簿深度和流动性监控
- **技术指标计算**: EMA、MACD、布林带、RSI等50+指标

### 🤖 智能交易策略
- **多策略融合**: 趋势跟踪、均值回归、动量策略组合
- **市场状态识别**: 牛市/熊市/震荡市场自动识别
- **信号确认机制**: 成交量确认、价格行为过滤
- **动态参数优化**: 根据市场波动率自动调整策略参数

### 🛡️ 专业风险管理
- **实时VaR计算**: 投资组合在险价值监控
- **动态止损止盈**: ATR追踪止损、浮盈回撤止损
- **仓位管理**: 基于凯利公式和波动率的智能仓位计算
- **风险等级评估**: 多维度风险评估和预警系统

### 📈 执行与优化
- **智能订单路由**: 最优价格执行和冲击成本控制
- **订单类型支持**: 限价单、市价单、算法单(TWAP、冰山)
- **滑点控制**: 实时滑点监控和执行成本优化
- **失败处理**: 自动重试、退避机制、断线重连

### 🎨 可视化界面
- **实时仪表板**: 账户概览、市场数据、交易统计
- **策略性能分析**: 权益曲线、回撤分析、风险指标
- **交易记录管理**: 完整的交易历史和订单跟踪
- **风险监控面板**: 实时风险等级和预警信息

## 🚀 快速开始

### 环境要求

- **Python**: 3.8 或更高版本
- **操作系统**: macOS / Linux / Windows
- **内存**: 建议 4GB 以上
- **网络**: 稳定的互联网连接

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/TigerYY/Qokx.git
cd Qokx
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate     # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置API密钥**
```bash
cp .env.example .env
# 编辑 .env 文件，填入您的OKX API密钥
```

5. **启动应用**
```bash
streamlit run app.py
```

应用将在 `http://localhost:8501` 启动

### 配置说明

在 `.env` 文件中配置您的OKX API信息：

```env
# OKX API 配置
OKX_API_KEY=your_api_key
OKX_SECRET_KEY=your_secret_key
OKX_PASSPHRASE=your_passphrase
OKX_SANDBOX=false  # 生产环境设为false，测试环境设为true

# 交易配置
DEFAULT_SYMBOL=BTC-USDT
MAX_POSITION_SIZE=1000
RISK_LEVEL=medium
```

## 📁 项目结构

```
Qokx/
├── app.py                      # Streamlit主应用
├── requirements.txt            # 项目依赖
├── .env.example               # 环境变量模板
├── README.md                  # 项目说明
├── docs/                      # 文档目录
│   └── okx_api_guide.md      # OKX API使用指南
├── src/                       # 核心源码
│   ├── strategies/           # 交易策略模块
│   │   ├── market_state_detector.py
│   │   └── signal_fusion_engine.py
│   ├── execution/            # 订单执行模块
│   │   ├── execution_engine.py
│   │   └── order_manager.py
│   ├── risk/                 # 风险管理模块
│   │   ├── risk_manager.py
│   │   └── position_sizer.py
│   ├── backtest/             # 回测引擎
│   │   ├── backtest_engine.py
│   │   ├── data_loader.py
│   │   └── result_analyzer.py
│   ├── utils/                # 工具类
│   │   ├── okx_rest_client.py
│   │   ├── okx_websocket_client.py
│   │   └── okx_public_client.py
│   ├── config/               # 配置管理
│   │   ├── api_config.py
│   │   └── settings.py
│   └── data/                 # 数据管理
│       └── multi_timeframe_manager.py
├── scripts/                   # 脚本工具
│   ├── run_backtest.py       # 回测脚本
│   └── backtest_validation.py
├── examples/                  # 使用示例
│   └── api_usage_example.py
└── tests/                     # 测试用例
```

## 🎯 使用指南

### 基础使用

1. **启动系统**: 运行 `streamlit run app.py`
2. **配置策略**: 在策略页面选择和配置交易策略
3. **设置风控**: 在风控页面设置风险参数
4. **开始交易**: 启动自动交易或手动执行
5. **监控状态**: 通过仪表板实时监控交易状态

### 高级功能

#### 策略开发
```python
from src.strategies.signal_fusion_engine import SignalFusionEngine

# 创建策略引擎
engine = SignalFusionEngine()

# 添加自定义策略
engine.add_strategy('my_strategy', my_strategy_function)

# 运行策略
signals = engine.generate_signals(market_data)
```

#### 回测验证
```bash
# 运行回测
python scripts/run_backtest.py --strategy=trend_following --start=2024-01-01 --end=2024-12-31

# 验证回测结果
python scripts/backtest_validation.py --result_file=backtest_results.json
```

## 📊 性能指标

系统设计目标：

- **夏普比率**: > 1.5
- **最大回撤**: < 15%
- **年化收益**: > 20%
- **胜率**: > 55%
- **盈亏比**: > 1.2
- **延迟**: < 100ms (WebSocket)

## 🛡️ 安全说明

- **API密钥安全**: 请妥善保管您的API密钥，不要提交到版本控制系统
- **权限设置**: 建议只开启必要的API权限（交易、查看账户）
- **网络安全**: 建议在安全的网络环境中运行
- **资金安全**: 建议先在模拟环境中测试，确认无误后再使用实盘

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📝 更新日志

### v1.0.0 (2024-12-20)
- ✨ 初始版本发布
- 🚀 完整的自动交易系统
- 📊 Streamlit可视化界面
- 🛡️ 专业级风险管理
- 📈 多策略支持
- 🔍 回测验证系统

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 联系方式

- **项目主页**: https://github.com/TigerYY/Qokx
- **问题反馈**: https://github.com/TigerYY/Qokx/issues
- **邮箱**: [您的邮箱]

## ⚠️ 免责声明

本软件仅供学习和研究使用。加密货币交易存在高风险，可能导致资金损失。使用本软件进行实盘交易的所有风险由用户自行承担。开发者不对任何交易损失承担责任。

请在充分了解风险的情况下谨慎使用，建议先在模拟环境中充分测试。

---

⭐ 如果这个项目对您有帮助，请给我们一个星标！

**Happy Trading! 🚀**
>>>>>>> e938a6d (docs: 添加完整的README.md文档)
