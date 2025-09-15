#!/bin/bash

# 启动FastAPI后端服务
echo "启动FastAPI后端服务..."

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查pip是否安装
if ! command -v pip3 &> /dev/null; then
    echo "错误: 未找到pip3，请先安装pip3"
    exit 1
fi

# 激活虚拟环境（如果存在）
if [ -d "venv" ]; then
    echo "激活虚拟环境..."
    source venv/bin/activate
fi

# 安装依赖
echo "安装后端依赖..."
pip install -r requirements.txt

# 设置环境变量
export DATABASE_URL="postgresql://user:password@localhost/trading_db"
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 启动FastAPI服务
echo "启动FastAPI服务..."
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
