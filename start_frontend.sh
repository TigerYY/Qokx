#!/bin/bash

# 前端启动脚本
# 专门用于启动前端服务，包含端口清理

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

# 检查Node.js和npm
check_dependencies() {
    log_step "检查前端依赖..."
    
    if ! command -v node &> /dev/null; then
        log_error "Node.js 未安装，请先安装 Node.js"
        exit 1
    fi
    
    if ! command -v npm &> /dev/null; then
        log_error "npm 未安装，请先安装 npm"
        exit 1
    fi
    
    log_info "Node.js版本: $(node --version)"
    log_info "npm版本: $(npm --version)"
    log_success "前端依赖检查完成"
}

# 设置前端环境
setup_frontend_env() {
    log_step "设置前端环境..."
    
    # 检查是否在正确的目录
    if [ ! -f "package.json" ]; then
        log_error "未找到 package.json 文件，请在 frontend 目录下运行此脚本"
        exit 1
    fi
    
    # 检查node_modules
    if [ ! -d "node_modules" ]; then
        log_info "安装前端依赖..."
        npm install
    else
        log_info "前端依赖已存在，跳过安装"
    fi
    
    # 检查环境变量文件
    if [ ! -f ".env" ]; then
        log_info "创建前端环境变量文件..."
        cat > .env << EOF
REACT_APP_API_BASE_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws
REACT_APP_NAME=YY自动交易系统 for OKX
REACT_APP_VERSION=2.0.0
REACT_APP_DEBUG=true
REACT_APP_LOG_LEVEL=info
PORT=3000
EOF
        log_success "环境变量文件已创建"
    else
        log_info "环境变量文件已存在"
    fi
    
    log_success "前端环境设置完成"
}

# 启动前端服务
start_frontend() {
    log_step "启动前端服务..."
    
    # 清理端口
    kill_port 3000 "前端React服务"
    
    # 创建日志目录
    mkdir -p ../logs
    
    # 启动React服务
    log_info "启动React服务 (端口: 3000)..."
    PORT=3000 nohup npm start > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    
    # 等待服务启动
    sleep 10
    
    # 检查服务是否启动成功
    if check_port 3000; then
        log_success "前端服务启动成功 (PID: $FRONTEND_PID)"
        echo $FRONTEND_PID > ../.frontend.pid
    else
        log_error "前端服务启动失败"
        log_info "请检查日志文件: ../logs/frontend.log"
        exit 1
    fi
}

# 显示服务状态
show_status() {
    log_step "服务状态检查..."
    
    echo -e "\n${PURPLE}=== 前端服务状态 ===${NC}"
    
    # 检查前端服务
    if check_port 3000; then
        echo -e "${GREEN}✓ 前端React服务${NC} - http://localhost:3000"
    else
        echo -e "${RED}✗ 前端React服务${NC} - 未运行"
    fi
    
    echo -e "\n${PURPLE}=== 访问地址 ===${NC}"
    echo -e "前端界面: ${GREEN}http://localhost:3000${NC}"
    echo -e "日志文件: ${YELLOW}../logs/frontend.log${NC}"
}

# 停止服务
stop_frontend() {
    log_step "停止前端服务..."
    
    # 停止前端服务
    if [ -f "../.frontend.pid" ]; then
        FRONTEND_PID=$(cat ../.frontend.pid)
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            kill $FRONTEND_PID
            log_success "前端服务已停止"
        fi
        rm -f ../.frontend.pid
    fi
    
    # 清理端口
    kill_port 3000 "前端React服务"
    
    log_success "前端服务已停止"
}

# 清理函数
cleanup() {
    log_info "正在清理..."
    stop_frontend
    exit 0
}

# 信号处理
trap cleanup SIGINT SIGTERM

# 主函数
main() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                前端服务启动脚本                              ║"
    echo "║                YY自动交易系统 for OKX                        ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    # 检查参数
    case "${1:-start}" in
        "start")
            log_info "启动模式：启动前端服务"
            check_dependencies
            setup_frontend_env
            start_frontend
            show_status
            ;;
        "stop")
            log_info "停止模式：停止前端服务"
            stop_frontend
            ;;
        "restart")
            log_info "重启模式：重启前端服务"
            stop_frontend
            sleep 3
            main start
            ;;
        "status")
            show_status
            ;;
        "clean")
            log_info "清理模式：清理端口和进程"
            kill_port 3000 "前端React服务"
            ;;
        *)
            echo -e "${YELLOW}用法: $0 [start|stop|restart|status|clean]${NC}"
            echo ""
            echo "命令说明："
            echo "  start     - 启动前端服务（默认）"
            echo "  stop      - 停止前端服务"
            echo "  restart   - 重启前端服务"
            echo "  status    - 查看服务状态"
            echo "  clean     - 清理端口和进程"
            exit 1
            ;;
    esac
    
    echo -e "\n${GREEN}脚本执行完成！${NC}"
}

# 执行主函数
main "$@"