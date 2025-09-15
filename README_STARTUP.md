# OKX 自动交易系统启动指南

## 🚀 快速开始

### 一键启动（推荐）
```bash
# 完整启动系统
./start_system.sh

# 或者使用快速启动（简化版）
./quick_start.sh
```

### 分步启动
```bash
# 仅启动后端
./start_system.sh backend

# 仅启动前端
./start_system.sh frontend

# 查看服务状态
./start_system.sh status

# 停止所有服务
./start_system.sh stop

# 重启系统
./start_system.sh restart
```

## 📋 系统要求

### 必需软件
- **Python 3.8+** - 后端运行环境
- **Node.js 16+** - 前端运行环境
- **PostgreSQL** - 数据库服务
- **Git** - 版本控制

### 可选软件
- **Docker** - 容器化部署
- **Redis** - 缓存服务（可选）

## 🔧 环境配置

### 1. 数据库配置
确保PostgreSQL服务正在运行：
```bash
# macOS (Homebrew)
brew services start postgresql

# Ubuntu/Debian
sudo systemctl start postgresql

# Windows
# 启动PostgreSQL服务
```

### 2. 环境变量配置
复制并编辑环境变量文件：
```bash
# 后端环境变量
cp env.example .env
# 编辑 .env 文件，配置数据库和API信息

# 前端环境变量
cp frontend/env.example frontend/.env
# 编辑 frontend/.env 文件
```

### 3. 依赖安装
```bash
# Python依赖
pip install -r requirements.txt

# 前端依赖
cd frontend
npm install
cd ..
```

## 🎯 启动脚本说明

### start_system.sh - 完整启动脚本
功能最全面的启动脚本，包含：
- ✅ 依赖检查
- ✅ 环境配置检查
- ✅ 数据库连接检查
- ✅ 端口清理
- ✅ 服务启动
- ✅ 状态监控

**使用方法：**
```bash
./start_system.sh [命令]

命令选项：
  start     - 完整启动系统（默认）
  stop      - 停止所有服务
  restart   - 重启所有服务
  status    - 查看服务状态
  backend   - 仅启动后端服务
  frontend  - 仅启动前端服务
  clean     - 清理端口和进程
```

### quick_start.sh - 快速启动脚本
简化版启动脚本，适合日常开发：
- ✅ 自动端口清理
- ✅ 环境变量创建
- ✅ 服务启动
- ✅ 实时监控

**使用方法：**
```bash
./quick_start.sh
```

### stop_system.sh - 停止脚本
专门用于停止所有服务：
```bash
./stop_system.sh
```

## 🌐 访问地址

启动成功后，可以通过以下地址访问：

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端界面 | http://localhost:3000 | React现代化界面 |
| 后端API | http://localhost:8000 | FastAPI服务 |
| API文档 | http://localhost:8000/docs | 交互式API文档 |
| 健康检查 | http://localhost:8000/health | 服务健康状态 |
| WebSocket | ws://localhost:8000/ws | 实时数据推送 |

## 📊 服务监控

### 查看服务状态
```bash
# 使用启动脚本查看
./start_system.sh status

# 或直接检查端口
lsof -i :8000  # 后端服务
lsof -i :3000  # 前端服务
```

### 查看日志
```bash
# 后端日志
tail -f logs/backend.log

# 前端日志
tail -f logs/frontend.log

# 实时监控所有日志
tail -f logs/*.log
```

### 进程管理
```bash
# 查看进程ID
cat .backend.pid
cat .frontend.pid

# 手动停止进程
kill $(cat .backend.pid)
kill $(cat .frontend.pid)
```

## 🐛 故障排除

### 常见问题

#### 1. 端口被占用
```bash
# 清理端口
./start_system.sh clean

# 或手动清理
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9
```

#### 2. 数据库连接失败
```bash
# 检查PostgreSQL状态
brew services list | grep postgresql

# 启动PostgreSQL
brew services start postgresql

# 检查数据库配置
cat .env | grep DATABASE
```

#### 3. 依赖安装失败
```bash
# 更新pip
pip install --upgrade pip

# 清理缓存重新安装
pip cache purge
pip install -r requirements.txt

# 前端依赖
cd frontend
rm -rf node_modules package-lock.json
npm install
```

#### 4. 权限问题
```bash
# 给脚本添加执行权限
chmod +x *.sh

# 检查文件权限
ls -la *.sh
```

### 日志分析

#### 后端错误
```bash
# 查看错误日志
grep -i error logs/backend.log

# 查看警告日志
grep -i warning logs/backend.log
```

#### 前端错误
```bash
# 查看构建错误
grep -i error logs/frontend.log

# 查看网络错误
grep -i "network\|connection" logs/frontend.log
```

## 🔄 开发模式

### 热重载开发
```bash
# 后端热重载（已默认启用）
python -m uvicorn src.api.main:app --reload

# 前端热重载（已默认启用）
cd frontend
npm start
```

### 调试模式
```bash
# 设置调试环境变量
export DEBUG=true
export LOG_LEVEL=DEBUG

# 启动服务
./start_system.sh
```

## 🚀 生产部署

### Docker部署
```bash
# 构建镜像
docker build -t okx-trading-system .

# 运行容器
docker run -p 3000:3000 -p 8000:8000 okx-trading-system
```

### 系统服务
```bash
# 创建系统服务文件
sudo cp okx-trading.service /etc/systemd/system/

# 启用服务
sudo systemctl enable okx-trading
sudo systemctl start okx-trading
```

## 📞 技术支持

如果遇到问题，请：
1. 查看日志文件
2. 检查系统要求
3. 查看故障排除部分
4. 提交Issue到项目仓库

---

**注意**: 请确保在生产环境中使用前，仔细配置所有环境变量和安全设置。
