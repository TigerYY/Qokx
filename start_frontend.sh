#!/bin/bash

# 启动React前端服务
echo "启动React前端服务..."

# 检查Node.js是否安装
if ! command -v node &> /dev/null; then
    echo "错误: 未找到Node.js，请先安装Node.js"
    exit 1
fi

# 检查npm是否安装
if ! command -v npm &> /dev/null; then
    echo "错误: 未找到npm，请先安装npm"
    exit 1
fi

# 进入前端目录
cd frontend

# 检查package.json是否存在
if [ ! -f "package.json" ]; then
    echo "错误: 未找到package.json文件"
    exit 1
fi

# 安装依赖（如果node_modules不存在）
if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi

# 复制环境变量文件
if [ ! -f ".env" ]; then
    echo "创建环境变量文件..."
    cp env.example .env
fi

# 启动开发服务器
echo "启动React开发服务器..."
npm start
