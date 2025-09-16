# 启动脚本使用指南

## 📋 脚本概览

本项目提供了多个启动脚本，用于不同的使用场景：

| 脚本名称 | 功能描述 | 使用场景 |
|---------|---------|---------|
| `start_system.sh` | 完整系统启动 | 生产环境、完整部署 |
| `quick_start.sh` | 快速启动 | 开发环境、快速测试 |
| `start_backend.sh` | 仅启动后端 | 后端开发、API测试 |
| `start_frontend.sh` | 仅启动前端 | 前端开发、UI测试 |

## 🚀 使用方法

### 1. 完整系统启动

```bash
# 启动完整系统（推荐）
./start_system.sh

# 或者指定参数
./start_system.sh start
```

**功能包括：**
- ✅ 清理端口 8000 和 3000
- ✅ 检查系统依赖
- ✅ 设置Python和Node.js环境
- ✅ 初始化数据库
- ✅ 启动后端API服务
- ✅ 启动前端React服务
- ✅ 显示服务状态

### 2. 快速启动

```bash
# 快速启动（开发环境）
./quick_start.sh
```

**功能包括：**
- ✅ 清理端口 8000 和 3000
- ✅ 自动安装依赖
- ✅ 启动后端和前端服务
- ✅ 显示访问地址

### 3. 仅启动后端

```bash
# 启动后端服务
./start_backend.sh

# 或者指定参数
./start_backend.sh start
```

**功能包括：**
- ✅ 清理端口 8000
- ✅ 检查Python环境
- ✅ 初始化数据库
- ✅ 启动FastAPI服务

### 4. 仅启动前端

```bash
# 在frontend目录下运行
cd frontend
../start_frontend.sh

# 或者指定参数
../start_frontend.sh start
```

**功能包括：**
- ✅ 清理端口 3000
- ✅ 检查Node.js环境
- ✅ 安装前端依赖
- ✅ 启动React服务

## 🛠️ 脚本参数

所有脚本都支持以下参数：

| 参数 | 功能 | 示例 |
|------|------|------|
| `start` | 启动服务（默认） | `./start_system.sh start` |
| `stop` | 停止服务 | `./start_system.sh stop` |
| `restart` | 重启服务 | `./start_system.sh restart` |
| `status` | 查看状态 | `./start_system.sh status` |
| `clean` | 清理端口 | `./start_system.sh clean` |

## 🔧 端口配置

| 服务 | 端口 | 访问地址 |
|------|------|---------|
| 后端API | 8000 | http://localhost:8000 |
| 前端React | 3000 | http://localhost:3000 |
| API文档 | 8000/docs | http://localhost:8000/docs |
| WebSocket | 8000/ws | ws://localhost:8000/ws |

## 📁 目录结构

```
Qokx/
├── start_system.sh          # 完整系统启动脚本
├── quick_start.sh           # 快速启动脚本
├── start_backend.sh         # 后端启动脚本
├── start_frontend.sh        # 前端启动脚本
├── frontend/                # 前端代码目录
│   ├── package.json
│   ├── src/
│   └── .env                 # 前端环境变量
├── src/                     # 后端代码目录
│   ├── api/
│   ├── database/
│   └── utils/
├── .env                     # 后端环境变量
├── logs/                    # 日志目录
│   ├── backend.log
│   └── frontend.log
└── .backend.pid             # 后端进程ID
└── .frontend.pid            # 前端进程ID
```

## 🔍 故障排除

### 1. 端口被占用

```bash
# 清理所有端口
./start_system.sh clean

# 或者手动清理
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9
```

### 2. 服务启动失败

```bash
# 查看日志
tail -f logs/backend.log
tail -f logs/frontend.log

# 检查服务状态
./start_system.sh status
```

### 3. 依赖问题

```bash
# 重新安装Python依赖
source venv/bin/activate
pip install -r requirements.txt

# 重新安装前端依赖
cd frontend
npm install
```

### 4. 数据库问题

```bash
# 检查PostgreSQL状态
brew services list | grep postgresql

# 启动PostgreSQL
brew services start postgresql
```

## 📝 环境变量

### 后端环境变量 (.env)

```env
# 数据库配置
DATABASE_URL=postgresql://postgres:password@localhost:5432/trading_system
DB_HOST=localhost
DB_PORT=5432
DB_NAME=trading_system
DB_USER=postgres
DB_PASSWORD=password

# API配置
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
```

### 前端环境变量 (frontend/.env)

```env
# API配置
REACT_APP_API_BASE_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws

# 应用配置
REACT_APP_NAME=YY自动交易系统 for OKX
REACT_APP_VERSION=2.0.0
REACT_APP_DEBUG=true
REACT_APP_LOG_LEVEL=info

# 端口配置
PORT=3000
```

## 🎯 最佳实践

### 1. 开发环境

```bash
# 使用快速启动脚本
./quick_start.sh
```

### 2. 生产环境

```bash
# 使用完整启动脚本
./start_system.sh
```

### 3. 调试模式

```bash
# 分别启动后端和前端
./start_backend.sh
cd frontend && ../start_frontend.sh
```

### 4. 停止服务

```bash
# 停止所有服务
./start_system.sh stop

# 或者使用Ctrl+C（在快速启动模式下）
```

## 📊 服务监控

### 查看服务状态

```bash
# 查看所有服务状态
./start_system.sh status

# 查看后端状态
./start_backend.sh status

# 查看前端状态
cd frontend && ../start_frontend.sh status
```

### 查看日志

```bash
# 实时查看后端日志
tail -f logs/backend.log

# 实时查看前端日志
tail -f logs/frontend.log

# 查看所有日志
tail -f logs/*.log
```

## 🔄 自动重启

所有脚本都支持自动重启功能：

```bash
# 重启完整系统
./start_system.sh restart

# 重启后端服务
./start_backend.sh restart

# 重启前端服务
cd frontend && ../start_frontend.sh restart
```

## ⚠️ 注意事项

1. **端口冲突**：确保端口8000和3000没有被其他服务占用
2. **权限问题**：确保脚本有执行权限 `chmod +x *.sh`
3. **环境变量**：确保.env文件配置正确
4. **依赖安装**：首次运行会自动安装依赖，可能需要一些时间
5. **数据库连接**：确保PostgreSQL服务正在运行
6. **网络连接**：确保可以访问OKX API

## 🆘 获取帮助

如果遇到问题，可以：

1. 查看日志文件
2. 检查服务状态
3. 清理端口和进程
4. 重新安装依赖
5. 检查环境变量配置

```bash
# 获取脚本帮助
./start_system.sh help
./start_backend.sh help
cd frontend && ../start_frontend.sh help
```
