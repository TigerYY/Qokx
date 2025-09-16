#!/bin/bash

# 后端启动脚本
# 专门用于启动后端服务，包含端口清理

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 命令未找到，请先安装 $1"
        exit 1
    fi
}

# 检查依赖
check_dependencies() {
    log_step "检查后端依赖..."
    
    # 检查Python
    check_command python3
    log_info "Python版本: $(python3 --version)"
    
    # 检查pip
    check_command pip3
    log_info "pip版本: $(pip3 --version)"
    
    log_success "后端依赖检查完成"
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
    
    log_success "环境配置文件检查完成"
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
    
    # 创建日志目录
    mkdir -p logs
    
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
        log_info "请检查日志文件: logs/backend.log"
        exit 1
    fi
}

# 显示服务状态
show_status() {
    log_step "服务状态检查..."
    
    echo -e "\n${PURPLE}=== 后端服务状态 ===${NC}"
    
    # 检查后端服务
    if check_port 8000; then
        echo -e "${GREEN}✓ 后端API服务${NC} - http://localhost:8000"
        echo -e "  API文档: http://localhost:8000/docs"
        echo -e "  WebSocket: ws://localhost:8000/ws"
    else
        echo -e "${RED}✗ 后端API服务${NC} - 未运行"
    fi
    
    echo -e "\n${PURPLE}=== 访问地址 ===${NC}"
    echo -e "API文档: ${GREEN}http://localhost:8000/docs${NC}"
    echo -e "健康检查: ${GREEN}http://localhost:8000/health${NC}"
    echo -e "日志文件: ${YELLOW}logs/backend.log${NC}"
}

# 停止服务
stop_backend() {
    log_step "停止后端服务..."
    
    # 停止后端服务
    if [ -f ".backend.pid" ]; then
        BACKEND_PID=$(cat .backend.pid)
        if kill -0 $BACKEND_PID 2>/dev/null; then
            kill $BACKEND_PID
            log_success "后端服务已停止"
        fi
        rm -f .backend.pid
    fi
    
    # 清理端口
    kill_port 8000 "后端API服务"
    
    log_success "后端服务已停止"
}

# 清理函数
cleanup() {
    log_info "正在清理..."
    stop_backend
    exit 0
}

# 信号处理
trap cleanup SIGINT SIGTERM

# 主函数
main() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                后端服务启动脚本                              ║"
    echo "║                YY自动交易系统 for OKX                        ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    # 检查参数
    case "${1:-start}" in
        "start")
            log_info "启动模式：启动后端服务"
            check_dependencies
            check_env_files
            setup_python_env
            check_database
            init_database
            start_backend
            show_status
            ;;
        "stop")
            log_info "停止模式：停止后端服务"
            stop_backend
            ;;
        "restart")
            log_info "重启模式：重启后端服务"
            stop_backend
            sleep 3
            main start
            ;;
        "status")
            show_status
            ;;
        "clean")
            log_info "清理模式：清理端口和进程"
            kill_port 8000 "后端API服务"
            ;;
        *)
            echo -e "${YELLOW}用法: $0 [start|stop|restart|status|clean]${NC}"
            echo ""
            echo "命令说明："
            echo "  start     - 启动后端服务（默认）"
            echo "  stop      - 停止后端服务"
            echo "  restart   - 重启后端服务"
            echo "  status    - 查看服务状态"
            echo "  clean     - 清理端口和进程"
            exit 1
            ;;
    esac
    
    echo -e "\n${GREEN}脚本执行完成！${NC}"
}

# 执行主函数
main "$@"