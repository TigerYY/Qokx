# OKX 自动交易系统 Dockerfile
# 多阶段构建，优化镜像大小

# 阶段1: 构建前端
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# 复制前端依赖文件
COPY frontend/package*.json ./

# 安装前端依赖
RUN npm ci --only=production

# 复制前端源代码
COPY frontend/ ./

# 构建前端
RUN npm run build

# 阶段2: 构建后端
FROM python:3.11-slim AS backend-builder

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制Python依赖文件
COPY requirements.txt ./

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 阶段3: 最终镜像
FROM python:3.11-slim

WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制Python依赖
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# 复制后端源代码
COPY src/ ./src/
COPY *.py ./
COPY *.md ./

# 复制前端构建结果
COPY --from=frontend-builder /app/frontend/build ./frontend/build

# 创建非root用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 创建日志目录
RUN mkdir -p logs

# 暴露端口
EXPOSE 8000 3000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
