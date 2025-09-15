#!/usr/bin/env python3
"""
数据库初始化脚本
创建数据库表结构和默认数据
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.connection import init_database, get_database_manager
from src.config.dynamic_config import init_config_manager
from src.migration.data_migrator import create_default_strategy_configs

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """主函数"""
    try:
        logger.info("开始初始化数据库...")
        
        # 检查数据库连接
        db_manager = get_database_manager()
        if not db_manager.test_connection():
            logger.error("数据库连接失败，请检查配置")
            return False
        
        # 初始化数据库表
        init_database()
        logger.info("数据库表创建完成")
        
        # 初始化配置管理器
        init_config_manager()
        logger.info("配置管理器初始化完成")
        
        # 创建默认策略配置
        if create_default_strategy_configs():
            logger.info("默认策略配置创建完成")
        else:
            logger.warning("默认策略配置创建失败")
        
        logger.info("数据库初始化完成！")
        return True
    
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
