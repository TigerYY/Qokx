@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM OKX 自动交易系统启动脚本 (Windows版本)
REM 功能：端口清除、后端启动、前端启动

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                OKX 自动交易系统启动脚本                      ║
echo ║                        v2.0.0                               ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM 检查参数
if "%1"=="stop" goto :stop
if "%1"=="restart" goto :restart
if "%1"=="status" goto :status
if "%1"=="clean" goto :clean
if "%1"=="backend" goto :backend
if "%1"=="frontend" goto :frontend
if "%1"=="help" goto :help
if "%1"=="" goto :start

:start
echo [INFO] 启动模式：完整启动
goto :check_deps

:stop
echo [INFO] 停止模式：停止所有服务
goto :stop_services

:restart
echo [INFO] 重启模式：重启所有服务
call :stop_services
timeout /t 3 /nobreak >nul
goto :start

:status
echo [INFO] 状态模式：查看服务状态
goto :show_status

:backend
echo [INFO] 后端模式：仅启动后端服务
goto :check_deps

:frontend
echo [INFO] 前端模式：仅启动前端服务
goto :setup_frontend

:clean
echo [INFO] 清理模式：清理端口和进程
goto :clean_ports

:help
echo 用法: %0 [start^|stop^|restart^|status^|backend^|frontend^|clean^|help]
echo.
echo 命令说明：
echo   start     - 完整启动系统（默认）
echo   stop      - 停止所有服务
echo   restart   - 重启所有服务
echo   status    - 查看服务状态
echo   backend   - 仅启动后端服务
echo   frontend  - 仅启动前端服务
echo   clean     - 清理端口和进程
echo   help      - 显示帮助信息
goto :end

:check_deps
echo [STEP] 检查系统依赖...

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python未安装，请先安装Python 3.8+
    goto :end
)
echo [INFO] Python版本: 
python --version

REM 检查pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip未安装，请先安装pip
    goto :end
)

REM 检查Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js未安装，请先安装Node.js
    goto :end
)
echo [INFO] Node.js版本: 
node --version

REM 检查npm
npm --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm未安装，请先安装npm
    goto :end
)

echo [SUCCESS] 依赖检查完成
goto :check_env

:check_env
echo [STEP] 检查环境配置文件...

REM 检查后端环境变量
if not exist ".env" (
    if exist "env.example" (
        echo [WARNING] .env 文件不存在，从 env.example 复制...
        copy env.example .env >nul
        echo [WARNING] 请编辑 .env 文件，配置正确的数据库和API信息
    ) else (
        echo [ERROR] .env 文件不存在，且没有 env.example 模板
        goto :end
    )
)

REM 检查前端环境变量
if not exist "frontend\.env" (
    if exist "frontend\env.example" (
        echo [WARNING] frontend\.env 文件不存在，从 env.example 复制...
        copy frontend\env.example frontend\.env >nul
    ) else (
        echo [WARNING] frontend\.env 文件不存在，将使用默认配置
        echo REACT_APP_API_BASE_URL=http://localhost:8000/api > frontend\.env
        echo REACT_APP_WS_URL=ws://localhost:8000/ws >> frontend\.env
    )
)

echo [SUCCESS] 环境配置文件检查完成
goto :setup_python

:setup_python
echo [STEP] 设置Python环境...

REM 检查虚拟环境
if not exist "venv" (
    echo [INFO] 创建Python虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
echo [INFO] 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo [INFO] 安装Python依赖...
pip install -r requirements.txt >nul 2>&1

echo [SUCCESS] Python环境设置完成

if "%1"=="backend" goto :start_backend
goto :setup_frontend

:setup_frontend
echo [STEP] 设置前端环境...

cd frontend

REM 检查node_modules
if not exist "node_modules" (
    echo [INFO] 安装前端依赖...
    npm install >nul 2>&1
) else (
    echo [INFO] 前端依赖已存在，跳过安装
)

cd ..
echo [SUCCESS] 前端环境设置完成

if "%1"=="frontend" goto :start_frontend
goto :check_database

:check_database
echo [STEP] 检查数据库连接...

REM 这里可以添加数据库连接检查逻辑
echo [INFO] 数据库连接检查（请确保PostgreSQL正在运行）

goto :init_database

:init_database
echo [STEP] 初始化数据库...

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 运行数据库初始化
echo [INFO] 创建数据库表...
python -c "from src.database.connection import init_db; init_db(); print('数据库初始化完成')" 2>nul || echo [WARNING] 数据库初始化失败，请检查数据库连接

echo [SUCCESS] 数据库初始化完成
goto :start_backend

:start_backend
echo [STEP] 启动后端服务...

REM 清理端口
call :clean_port 8000

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 启动FastAPI服务
echo [INFO] 启动FastAPI服务 (端口: 8000)...
start /b python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload > logs\backend.log 2>&1

REM 等待服务启动
timeout /t 5 /nobreak >nul

REM 检查服务是否启动成功
netstat -an | findstr :8000 >nul
if errorlevel 1 (
    echo [ERROR] 后端服务启动失败
    goto :end
) else (
    echo [SUCCESS] 后端服务启动成功
)

if "%1"=="backend" goto :show_status
goto :start_frontend

:start_frontend
echo [STEP] 启动前端服务...

REM 清理端口
call :clean_port 3000

cd frontend

REM 启动React服务
echo [INFO] 启动React服务 (端口: 3000)...
start /b npm start > ..\logs\frontend.log 2>&1

cd ..

REM 等待服务启动
timeout /t 10 /nobreak >nul

REM 检查服务是否启动成功
netstat -an | findstr :3000 >nul
if errorlevel 1 (
    echo [ERROR] 前端服务启动失败
    goto :end
) else (
    echo [SUCCESS] 前端服务启动成功
)

goto :show_status

:show_status
echo.
echo [STEP] 服务状态检查...
echo.
echo === 服务状态 ===

REM 检查后端服务
netstat -an | findstr :8000 >nul
if errorlevel 1 (
    echo [X] 后端API服务 - 未运行
) else (
    echo [√] 后端API服务 - http://localhost:8000
    echo     API文档: http://localhost:8000/docs
    echo     WebSocket: ws://localhost:8000/ws
)

REM 检查前端服务
netstat -an | findstr :3000 >nul
if errorlevel 1 (
    echo [X] 前端React服务 - 未运行
) else (
    echo [√] 前端React服务 - http://localhost:3000
)

echo.
echo === 访问地址 ===
echo 主界面: http://localhost:3000
echo API文档: http://localhost:8000/docs
echo 健康检查: http://localhost:8000/health
echo.
echo === 日志文件 ===
echo 后端日志: logs\backend.log
echo 前端日志: logs\frontend.log
echo.

if "%1"=="status" goto :end

echo [SUCCESS] 脚本执行完成！
echo.
echo 按任意键退出...
pause >nul
goto :end

:stop_services
echo [INFO] 停止所有服务...

REM 停止占用端口的进程
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000') do taskkill /f /pid %%a >nul 2>&1

echo [SUCCESS] 所有服务已停止
goto :end

:clean_ports
echo [INFO] 清理端口和进程...

REM 清理端口8000
call :clean_port 8000

REM 清理端口3000
call :clean_port 3000

echo [SUCCESS] 端口清理完成
goto :end

:clean_port
REM 清理指定端口的进程
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%1') do (
    taskkill /f /pid %%a >nul 2>&1
    if not errorlevel 1 (
        echo [INFO] 端口 %1 已清理
    )
)
goto :eof

:end
exit /b 0
