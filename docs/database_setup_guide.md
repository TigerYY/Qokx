# 数据库设置指南

## 概述

本指南将帮助您设置PostgreSQL数据库并配置增强版交易系统。

## 前置要求

- PostgreSQL 12 或更高版本
- Python 3.8 或更高版本
- 已安装项目依赖

## 1. 安装PostgreSQL

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

### macOS
```bash
brew install postgresql
brew services start postgresql
```

### Windows
下载并安装 [PostgreSQL官方安装包](https://www.postgresql.org/download/windows/)

## 2. 创建数据库

```bash
# 登录PostgreSQL
sudo -u postgres psql

# 创建数据库
CREATE DATABASE trading_system;

# 创建用户（可选）
CREATE USER trading_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE trading_system TO trading_user;

# 退出
\q
```

## 3. 配置环境变量

复制环境变量模板：
```bash
cp env.example .env
```

编辑 `.env` 文件，配置数据库连接：
```env
# 数据库配置
DATABASE_URL=postgresql://username:password@localhost:5432/trading_system
# 或者分别配置
DB_HOST=localhost
DB_PORT=5432
DB_USERNAME=postgres
DB_PASSWORD=your_password
DB_NAME=trading_system
DB_ECHO=false

# OKX API 配置
OKX_API_KEY=your_api_key
OKX_SECRET_KEY=your_secret_key
OKX_PASSPHRASE=your_passphrase
OKX_SANDBOX=true

# 配置管理
API_MASTER_KEY=your_master_key_for_encryption
```

## 4. 初始化数据库

运行数据库初始化脚本：
```bash
python scripts/init_database.py
```

这将：
- 创建所有必要的数据库表
- 初始化配置管理器
- 创建默认策略配置

## 5. 验证安装

运行示例程序验证安装：
```bash
python examples/enhanced_trading_example.py
```

## 数据库表结构

### 核心表

1. **trades** - 交易记录表
   - 存储所有交易记录
   - 包含策略ID、版本、价格、数量等信息

2. **strategy_versions** - 策略版本表
   - 存储策略版本信息
   - 支持策略版本控制

3. **strategy_configs** - 策略配置表
   - 存储策略配置参数
   - 支持动态配置更新

4. **performance_metrics** - 性能指标表
   - 存储策略性能数据
   - 支持历史性能分析

5. **ab_tests** - A/B测试表
   - 存储A/B测试信息
   - 支持策略对比测试

6. **trading_sessions** - 交易会话表
   - 存储交易会话信息
   - 支持会话管理

7. **risk_events** - 风险事件表
   - 存储风险事件记录
   - 支持风险监控

8. **system_configs** - 系统配置表
   - 存储系统级配置
   - 支持系统参数管理

## 6. 数据迁移

如果您有现有的交易数据，可以使用数据迁移工具：

```python
from src.migration.data_migrator import migrate_session_data

# 迁移会话数据
session_data = {
    'trades': [...],  # 交易数据
    'equity_curve': [...],  # 权益曲线
    'risk_limits': {...},  # 风险限制
    # ... 其他数据
}

migrate_session_data(session_data)
```

## 7. 配置管理

### 动态配置更新

```python
from src.config.dynamic_config import get_config_manager

config_manager = get_config_manager()

# 更新策略配置
config_manager.set_strategy_config(
    strategy_id="signal_fusion_strategy_1.0.0",
    config_key="max_position_size",
    config_value=0.15,
    config_type="strategy"
)

# 获取配置
config = config_manager.get_strategy_config("signal_fusion_strategy_1.0.0")
```

### 配置变更监听

```python
def on_config_change(config_key, old_value, new_value):
    print(f"配置变更: {config_key} = {new_value}")

config_manager.add_change_listener(on_config_change)
```

## 8. 策略版本控制

### 创建策略版本

```python
from src.strategies.version_control import get_strategy_version_manager

strategy_manager = get_strategy_version_manager()

# 创建策略版本
strategy_manager.create_strategy_version(
    strategy_id="my_strategy",
    version="1.0.0",
    name="我的策略",
    description="策略描述",
    class_path="my_module.MyStrategy",
    config={"param1": "value1"}
)

# 激活策略版本
strategy_manager.activate_strategy_version("my_strategy", "1.0.0")
```

### A/B测试

```python
from src.strategies.version_control import get_ab_test_manager

ab_test_manager = get_ab_test_manager()

# 创建A/B测试
test_id = ab_test_manager.create_ab_test(
    test_name="风险参数测试",
    strategy_a_id="my_strategy",
    strategy_a_version="1.0.0",
    strategy_b_id="my_strategy",
    strategy_b_version="1.1.0",
    traffic_split=0.5,
    duration_days=7
)

# 分析测试结果
result = ab_test_manager.analyze_ab_test(test_id)
```

## 9. 监控和维护

### 性能监控

系统会自动收集和存储性能指标：
- 总收益率
- 夏普比率
- 最大回撤
- 胜率
- 盈亏比

### 数据备份

建议定期备份数据库：
```bash
pg_dump trading_system > backup_$(date +%Y%m%d).sql
```

### 日志管理

系统日志存储在 `logs/` 目录下：
- `trading_YYYYMMDD.log` - 交易日志
- `system_YYYYMMDD.log` - 系统日志
- `error_YYYYMMDD.log` - 错误日志

## 10. 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查PostgreSQL服务是否运行
   - 验证连接参数是否正确
   - 确认数据库用户权限

2. **表创建失败**
   - 检查数据库用户是否有CREATE权限
   - 确认数据库名称正确

3. **配置加载失败**
   - 检查环境变量是否正确设置
   - 确认配置文件格式正确

### 日志查看

```bash
# 查看系统日志
tail -f logs/system_$(date +%Y%m%d).log

# 查看错误日志
tail -f logs/error_$(date +%Y%m%d).log
```

## 11. 性能优化

### 数据库优化

1. **索引优化**
   - 系统已为常用查询字段创建索引
   - 可根据实际使用情况添加额外索引

2. **连接池配置**
   - 默认连接池大小为10
   - 可根据并发需求调整

3. **数据清理**
   - 系统会自动清理30天前的日志文件
   - 可配置数据保留策略

### 监控指标

系统提供以下监控指标：
- 数据库连接数
- 查询响应时间
- 交易执行延迟
- 内存使用情况

## 总结

通过以上步骤，您已经成功设置了增强版交易系统的数据库环境。系统现在支持：

- ✅ 数据持久化存储
- ✅ 动态配置管理
- ✅ 策略版本控制
- ✅ A/B测试框架
- ✅ 性能监控
- ✅ 风险事件记录

接下来您可以开始使用增强版交易系统进行策略开发和测试。
