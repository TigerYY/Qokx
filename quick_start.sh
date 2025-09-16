#!/bin/bash

# OKX 自动交易系统快速启动脚本
# 简化版本，适合日常开发使用

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🚀 启动 OKX 自动交易系统...${NC}"

# 清理端口
echo -e "${YELLOW}清理端口...${NC}"
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

# 创建日志目录
mkdir -p logs

# 检查环境变量
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}创建环境变量文件...${NC}"
    cp env.example .env
fi

if [ ! -f "frontend/.env" ]; then
    echo -e "${YELLOW}创建前端环境变量文件...${NC}"
    cat > frontend/.env << EOF
REACT_APP_API_BASE_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws
REACT_APP_NAME=YY自动交易系统 for OKX
REACT_APP_VERSION=2.0.0
REACT_APP_DEBUG=true
REACT_APP_LOG_LEVEL=info
PORT=3000
EOF
fi

# 启动后端
echo -e "${BLUE}启动后端服务...${NC}"
source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt >/dev/null 2>&1
nohup python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload > logs/backend.log 2>&1 &
echo $! > .backend.pid

# 等待后端启动
sleep 3

# 启动前端
echo -e "${BLUE}启动前端服务...${NC}"
cd frontend
npm install >/dev/null 2>&1
PORT=3000 nohup npm start > ../logs/frontend.log 2>&1 &
echo $! > ../.frontend.pid
cd ..

# 等待前端启动
sleep 5

echo -e "${GREEN}✅ 系统启动完成！${NC}"
echo -e "${GREEN}前端地址: http://localhost:3000${NC}"
echo -e "${GREEN}后端API: http://localhost:8000${NC}"
echo -e "${GREEN}API文档: http://localhost:8000/docs${NC}"

# 保持脚本运行
echo -e "${YELLOW}按 Ctrl+C 停止服务${NC}"
trap 'echo -e "\n${YELLOW}停止服务...${NC}"; kill $(cat .backend.pid) 2>/dev/null; kill $(cat .frontend.pid) 2>/dev/null; rm -f .backend.pid .frontend.pid; exit 0' INT
wait
