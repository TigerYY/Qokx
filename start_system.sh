#!/bin/bash

# OKX 自动交易系统启动脚本
# 功能：端口清除、后端启动、前端启动

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 命令未找到，请先安装 $1"
        exit 1
    fi
}

# 检查端口是否被占用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # 端口被占用
    else
        return 1  # 端口空闲
    fi
}

# 杀死占用指定端口的进程
kill_port() {
    local port=$1
    local service_name=$2
    
    if check_port $port; then
        log_warning "端口 $port 被占用，正在清理 $service_name 服务..."
        local pids=$(lsof -ti:$port)
        if [ ! -z "$pids" ]; then
            echo $pids | xargs kill -9
            sleep 2
            if check_port $port; then
                log_error "无法清理端口 $port，请手动处理"
                exit 1
            else
                log_success "端口 $port 已清理完成"
            fi
        fi
    else
        log_info "端口 $port 空闲"
    fi
}

# 检查环境变量文件
check_env_files() {
    log_step "检查环境配置文件..."
    
    # 检查后端环境变量
    if [ ! -f ".env" ]; then
        if [ -f "env.example" ]; then
            log_warning ".env 文件不存在，从 env.example 复制..."
            cp env.example .env
            log_warning "请编辑 .env 文件，配置正确的数据库和API信息"
        else
            log_error ".env 文件不存在，且没有 env.example 模板"
            exit 1
        fi
    fi
    
    # 检查前端环境变量
    if [ ! -f "frontend/.env" ]; then
        if [ -f "frontend/env.example" ]; then
            log_warning "frontend/.env 文件不存在，从 env.example 复制..."
            cp frontend/env.example frontend/.env
        else
            log_warning "frontend/.env 文件不存在，将使用默认配置"
        fi
    fi
    
    log_success "环境配置文件检查完成"
}

# 检查依赖
check_dependencies() {
    log_step "检查系统依赖..."
    
    # 检查Python
    check_command python3
    log_info "Python版本: $(python3 --version)"
    
    # 检查pip
    check_command pip3
    log_info "pip版本: $(pip3 --version)"
    
    # 检查Node.js
    check_command node
    log_info "Node.js版本: $(node --version)"
    
    # 检查npm
    check_command npm
    log_info "npm版本: $(npm --version)"
    
    # 检查PostgreSQL
    if ! command -v psql &> /dev/null; then
        log_warning "PostgreSQL客户端未找到，请确保PostgreSQL已安装"
    else
        log_info "PostgreSQL客户端版本: $(psql --version)"
    fi
    
    log_success "依赖检查完成"
}

# 设置Python环境
setup_python_env() {
    log_step "设置Python环境..."
    
    # 检查虚拟环境
    if [ ! -d "venv" ]; then
        log_info "创建Python虚拟环境..."
        python3 -m venv venv
    fi
    
    # 激活虚拟环境
    log_info "激活虚拟环境..."
    source venv/bin/activate
    
    # 安装依赖
    log_info "安装Python依赖..."
    pip install -r requirements.txt
    
    log_success "Python环境设置完成"
}

# 设置前端环境
setup_frontend_env() {
    log_step "设置前端环境..."
    
    cd frontend
    
    # 检查node_modules
    if [ ! -d "node_modules" ]; then
        log_info "安装前端依赖..."
        npm install
    else
        log_info "前端依赖已存在，跳过安装"
    fi
    
    cd ..
    log_success "前端环境设置完成"
}

# 检查数据库连接
check_database() {
    log_step "检查数据库连接..."
    
    # 从.env文件读取数据库配置
    if [ -f ".env" ]; then
        source .env
        export DATABASE_URL
    fi
    
    # 检查PostgreSQL是否运行
    if command -v pg_isready &> /dev/null; then
        if pg_isready -h ${DB_HOST:-localhost} -p ${DB_PORT:-5432} >/dev/null 2>&1; then
            log_success "PostgreSQL数据库连接正常"
        else
            log_warning "PostgreSQL数据库连接失败，请检查数据库服务"
            log_info "尝试启动PostgreSQL服务..."
            if command -v brew &> /dev/null; then
                brew services start postgresql
            elif command -v systemctl &> /dev/null; then
                sudo systemctl start postgresql
            else
                log_warning "请手动启动PostgreSQL服务"
            fi
        fi
    else
        log_warning "无法检查数据库连接，请确保PostgreSQL正在运行"
    fi
}

# 初始化数据库
init_database() {
    log_step "初始化数据库..."
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 设置环境变量
    if [ -f ".env" ]; then
        source .env
        export DATABASE_URL
    fi
    
    # 运行数据库初始化
    log_info "创建数据库表..."
    python -c "
from src.database.connection import init_db
init_db()
print('数据库初始化完成')
"
    
    log_success "数据库初始化完成"
}

# 启动后端服务
start_backend() {
    log_step "启动后端服务..."
    
    # 清理端口
    kill_port 8000 "后端API服务"
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 设置环境变量
    if [ -f ".env" ]; then
        source .env
        export DATABASE_URL
    fi
    
    # 启动FastAPI服务
    log_info "启动FastAPI服务 (端口: 8000)..."
    nohup python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload > logs/backend.log 2>&1 &
    BACKEND_PID=$!
    
    # 等待服务启动
    sleep 5
    
    # 检查服务是否启动成功
    if check_port 8000; then
        log_success "后端服务启动成功 (PID: $BACKEND_PID)"
        echo $BACKEND_PID > .backend.pid
    else
        log_error "后端服务启动失败"
        exit 1
    fi
}

# 启动前端服务
start_frontend() {
    log_step "启动前端服务..."
    
    # 清理端口
    kill_port 3000 "前端React服务"
    
    cd frontend
    
    # 检查环境变量
    if [ ! -f ".env" ]; then
        log_info "创建前端环境变量文件..."
        cat > .env << EOF
REACT_APP_API_BASE_URL=http://localhost:8000/api
REACT_APP_WS_URL=ws://localhost:8000/ws
REACT_APP_NAME=OKX Trading System
REACT_APP_VERSION=2.0.0
REACT_APP_DEBUG=true
REACT_APP_LOG_LEVEL=info
EOF
    fi
    
    # 启动React服务
    log_info "启动React服务 (端口: 3000)..."
    nohup npm start > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    
    cd ..
    
    # 等待服务启动
    sleep 10
    
    # 检查服务是否启动成功
    if check_port 3000; then
        log_success "前端服务启动成功 (PID: $FRONTEND_PID)"
        echo $FRONTEND_PID > .frontend.pid
    else
        log_error "前端服务启动失败"
        exit 1
    fi
}

# 显示服务状态
show_status() {
    log_step "服务状态检查..."
    
    echo -e "\n${CYAN}=== 服务状态 ===${NC}"
    
    # 检查后端服务
    if check_port 8000; then
        echo -e "${GREEN}✓ 后端API服务${NC} - http://localhost:8000"
        echo -e "  API文档: http://localhost:8000/docs"
        echo -e "  WebSocket: ws://localhost:8000/ws"
    else
        echo -e "${RED}✗ 后端API服务${NC} - 未运行"
    fi
    
    # 检查前端服务
    if check_port 3000; then
        echo -e "${GREEN}✓ 前端React服务${NC} - http://localhost:3000"
    else
        echo -e "${RED}✗ 前端React服务${NC} - 未运行"
    fi
    
    echo -e "\n${CYAN}=== 访问地址 ===${NC}"
    echo -e "主界面: ${GREEN}http://localhost:3000${NC}"
    echo -e "API文档: ${GREEN}http://localhost:8000/docs${NC}"
    echo -e "健康检查: ${GREEN}http://localhost:8000/health${NC}"
    
    echo -e "\n${CYAN}=== 日志文件 ===${NC}"
    echo -e "后端日志: ${YELLOW}logs/backend.log${NC}"
    echo -e "前端日志: ${YELLOW}logs/frontend.log${NC}"
}

# 停止服务
stop_services() {
    log_step "停止所有服务..."
    
    # 停止后端服务
    if [ -f ".backend.pid" ]; then
        BACKEND_PID=$(cat .backend.pid)
        if kill -0 $BACKEND_PID 2>/dev/null; then
            kill $BACKEND_PID
            log_success "后端服务已停止"
        fi
        rm -f .backend.pid
    fi
    
    # 停止前端服务
    if [ -f ".frontend.pid" ]; then
        FRONTEND_PID=$(cat .frontend.pid)
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            kill $FRONTEND_PID
            log_success "前端服务已停止"
        fi
        rm -f .frontend.pid
    fi
    
    # 清理端口
    kill_port 8000 "后端API服务"
    kill_port 3000 "前端React服务"
    
    log_success "所有服务已停止"
}

# 清理函数
cleanup() {
    log_info "正在清理..."
    stop_services
    exit 0
}

# 信号处理
trap cleanup SIGINT SIGTERM

# 主函数
main() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                OKX 自动交易系统启动脚本                      ║"
    echo "║                        v2.0.0                               ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    # 创建日志目录
    mkdir -p logs
    
    # 检查参数
    case "${1:-start}" in
        "start")
            log_info "启动模式：完整启动"
            check_dependencies
            check_env_files
            setup_python_env
            setup_frontend_env
            check_database
            init_database
            start_backend
            start_frontend
            show_status
            ;;
        "stop")
            log_info "停止模式：停止所有服务"
            stop_services
            ;;
        "restart")
            log_info "重启模式：重启所有服务"
            stop_services
            sleep 3
            main start
            ;;
        "status")
            show_status
            ;;
        "backend")
            log_info "后端模式：仅启动后端服务"
            check_dependencies
            check_env_files
            setup_python_env
            check_database
            init_database
            start_backend
            show_status
            ;;
        "frontend")
            log_info "前端模式：仅启动前端服务"
            check_dependencies
            setup_frontend_env
            start_frontend
            show_status
            ;;
        "clean")
            log_info "清理模式：清理端口和进程"
            kill_port 8000 "后端API服务"
            kill_port 3000 "前端React服务"
            ;;
        *)
            echo -e "${YELLOW}用法: $0 [start|stop|restart|status|backend|frontend|clean]${NC}"
            echo ""
            echo "命令说明："
            echo "  start     - 完整启动系统（默认）"
            echo "  stop      - 停止所有服务"
            echo "  restart   - 重启所有服务"
            echo "  status    - 查看服务状态"
            echo "  backend   - 仅启动后端服务"
            echo "  frontend  - 仅启动前端服务"
            echo "  clean     - 清理端口和进程"
            exit 1
            ;;
    esac
    
    echo -e "\n${GREEN}脚本执行完成！${NC}"
}

# 执行主函数
main "$@"
