#!/bin/bash

# OKX 自动交易系统停止脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🛑 停止 OKX 自动交易系统...${NC}"

# 停止后端服务
if [ -f ".backend.pid" ]; then
    BACKEND_PID=$(cat .backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        kill $BACKEND_PID
        echo -e "${GREEN}✓ 后端服务已停止${NC}"
    fi
    rm -f .backend.pid
fi

# 停止前端服务
if [ -f ".frontend.pid" ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        kill $FRONTEND_PID
        echo -e "${GREEN}✓ 前端服务已停止${NC}"
    fi
    rm -f .frontend.pid
fi

# 清理端口
echo -e "${YELLOW}清理端口...${NC}"
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

echo -e "${GREEN}✅ 系统已完全停止${NC}"
