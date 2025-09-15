# OKX 自动交易系统 - 前端重构

## 🎨 项目概述

这是OKX自动交易系统的现代化前端界面，使用React + TypeScript + Material-UI构建，采用现代简洁的设计风格。

## ✨ 主要特性

### 🎯 核心功能
- **实时交易仪表板** - 监控交易状态和性能指标
- **策略管理** - 创建、编辑、启动/停止交易策略
- **交易界面** - 实时交易和订单管理
- **风险监控** - 实时风险指标和告警系统
- **系统设置** - 全面的配置管理

### 🎨 设计特色
- **现代简洁风格** - 采用Material-UI设计系统
- **暗色主题** - 专业的交易界面体验
- **响应式设计** - 支持各种屏幕尺寸
- **实时更新** - WebSocket实时数据推送
- **交互友好** - 直观的用户界面和操作流程

### 🛠 技术栈
- **React 18** - 现代React框架
- **TypeScript** - 类型安全的JavaScript
- **Material-UI v5** - 现代化UI组件库
- **Recharts** - 专业图表组件
- **React Query** - 数据获取和缓存
- **WebSocket** - 实时通信

## 🚀 快速开始

### 环境要求
- Node.js >= 16.0.0
- npm >= 8.0.0

### 安装和运行

1. **克隆项目**
```bash
git clone <repository-url>
cd Qokx
```

2. **安装依赖**
```bash
cd frontend
npm install
```

3. **配置环境变量**
```bash
cp env.example .env
# 编辑.env文件，配置API地址等
```

4. **启动开发服务器**
```bash
npm start
```

5. **访问应用**
打开浏览器访问 `http://localhost:3000`

### 生产构建

```bash
# 构建生产版本
npm run build

# 预览生产版本
npm run preview
```

## 📁 项目结构

```
frontend/
├── public/                 # 静态资源
│   ├── index.html         # HTML模板
│   └── manifest.json      # PWA配置
├── src/                   # 源代码
│   ├── components/        # 可复用组件
│   │   ├── Layout/        # 布局组件
│   │   ├── UI/           # 通用UI组件
│   │   ├── Charts/       # 图表组件
│   │   ├── Trading/      # 交易相关组件
│   │   └── System/       # 系统组件
│   ├── pages/            # 页面组件
│   │   ├── Dashboard/    # 仪表板
│   │   ├── StrategyManagement/ # 策略管理
│   │   ├── TradingInterface/  # 交易界面
│   │   ├── RiskMonitoring/    # 风险监控
│   │   └── Settings/     # 系统设置
│   ├── hooks/            # 自定义Hooks
│   ├── services/         # API服务
│   ├── types/            # TypeScript类型定义
│   ├── styles/           # 样式文件
│   ├── utils/            # 工具函数
│   ├── App.tsx           # 主应用组件
│   └── index.tsx         # 应用入口
├── package.json          # 项目配置
├── tsconfig.json         # TypeScript配置
└── README.md            # 项目说明
```

## 🎨 设计系统

### 主题色彩
- **主色调**: #00D4AA (青绿色)
- **辅助色**: #FF6B6B (珊瑚红)
- **背景色**: #0A0A0A (深黑)
- **卡片背景**: rgba(26, 26, 26, 0.8) (半透明深灰)

### 组件特色
- **毛玻璃效果** - backdrop-filter: blur(10px)
- **渐变按钮** - 线性渐变背景
- **圆角设计** - 统一的圆角半径
- **阴影效果** - 柔和的阴影和发光效果

## 🔧 开发指南

### 添加新页面
1. 在 `src/pages/` 下创建页面组件
2. 在 `src/App.tsx` 中添加路由
3. 在 `src/components/Layout/Sidebar.tsx` 中添加菜单项

### 添加新组件
1. 在 `src/components/` 下创建组件
2. 使用TypeScript定义props接口
3. 遵循Material-UI设计规范

### API集成
1. 在 `src/services/api.ts` 中定义API方法
2. 在 `src/hooks/` 中创建自定义Hook
3. 在组件中使用React Query进行数据管理

## 📊 功能模块

### 1. 交易仪表板
- 实时资产概览
- 性能指标展示
- 价格走势图表
- 最近交易记录
- 系统状态监控

### 2. 策略管理
- 策略列表和筛选
- 策略创建和编辑
- 策略启动/停止
- 性能对比分析
- A/B测试管理

### 3. 交易界面
- 实时价格图表
- 快速交易面板
- 订单管理
- 账户信息展示

### 4. 风险监控
- 风险指标监控
- 风险限制设置
- 风险事件记录
- 实时告警系统

### 5. 系统设置
- 交易参数配置
- 风险参数设置
- 通知偏好设置
- 界面主题配置

## 🔌 API接口

### 基础URL
- 开发环境: `http://localhost:8000/api`
- WebSocket: `ws://localhost:8000/ws`

### 主要接口
- `GET /trading/dashboard` - 获取仪表板数据
- `GET /trading/trades` - 获取交易记录
- `GET /strategies` - 获取策略列表
- `POST /strategies/{id}/start` - 启动策略
- `POST /strategies/{id}/stop` - 停止策略
- `GET /market/data` - 获取市场数据
- `WebSocket /ws` - 实时数据推送

## 🚀 部署指南

### 开发环境
```bash
# 启动前端
npm start

# 启动后端
./start_backend.sh
```

### 生产环境
```bash
# 构建前端
npm run build

# 使用Nginx等服务器托管静态文件
# 配置API代理到后端服务
```

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🆘 支持

如有问题或建议，请：
1. 查看文档
2. 搜索Issues
3. 创建新Issue
4. 联系开发团队

---

**注意**: 这是一个演示项目，请勿在生产环境中使用真实资金进行交易。
