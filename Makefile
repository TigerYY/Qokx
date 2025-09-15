# OKX 自动交易系统 Makefile
# 简化常用操作

.PHONY: help install start stop restart status clean build test docker

# 默认目标
help:
	@echo "OKX 自动交易系统 - 可用命令:"
	@echo ""
	@echo "开发命令:"
	@echo "  make install     - 安装所有依赖"
	@echo "  make start       - 启动系统"
	@echo "  make stop        - 停止系统"
	@echo "  make restart     - 重启系统"
	@echo "  make status      - 查看状态"
	@echo "  make clean       - 清理端口和进程"
	@echo ""
	@echo "构建命令:"
	@echo "  make build       - 构建前端"
	@echo "  make test        - 运行测试"
	@echo ""
	@echo "Docker命令:"
	@echo "  make docker      - 构建Docker镜像"
	@echo "  make up          - 启动Docker服务"
	@echo "  make down        - 停止Docker服务"
	@echo ""
	@echo "数据库命令:"
	@echo "  make db-init     - 初始化数据库"
	@echo "  make db-reset    - 重置数据库"
	@echo ""

# 安装依赖
install:
	@echo "安装Python依赖..."
	pip install -r requirements.txt
	@echo "安装前端依赖..."
	cd frontend && npm install
	@echo "依赖安装完成"

# 启动系统
start:
	@echo "启动系统..."
	./start_system.sh

# 停止系统
stop:
	@echo "停止系统..."
	./stop_system.sh

# 重启系统
restart:
	@echo "重启系统..."
	./start_system.sh restart

# 查看状态
status:
	@echo "查看系统状态..."
	./start_system.sh status

# 清理
clean:
	@echo "清理端口和进程..."
	./start_system.sh clean

# 构建前端
build:
	@echo "构建前端..."
	cd frontend && npm run build

# 运行测试
test:
	@echo "运行测试..."
	python -m pytest tests/ -v

# Docker构建
docker:
	@echo "构建Docker镜像..."
	docker build -t okx-trading-system .

# Docker启动
up:
	@echo "启动Docker服务..."
	docker-compose up -d

# Docker停止
down:
	@echo "停止Docker服务..."
	docker-compose down

# 数据库初始化
db-init:
	@echo "初始化数据库..."
	python -c "from src.database.connection import init_db; init_db()"

# 数据库重置
db-reset:
	@echo "重置数据库..."
	python -c "from src.database.connection import engine; engine.execute('DROP SCHEMA public CASCADE; CREATE SCHEMA public;')"
	make db-init

# 快速启动（开发模式）
dev:
	@echo "开发模式启动..."
	./quick_start.sh

# 日志查看
logs:
	@echo "查看日志..."
	tail -f logs/*.log

# 系统信息
info:
	@echo "系统信息:"
	@echo "Python版本: $(shell python --version)"
	@echo "Node.js版本: $(shell node --version)"
	@echo "npm版本: $(shell npm --version)"
	@echo "Docker版本: $(shell docker --version 2>/dev/null || echo '未安装')"
	@echo "PostgreSQL版本: $(shell psql --version 2>/dev/null || echo '未安装')"
