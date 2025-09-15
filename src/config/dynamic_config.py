"""
动态配置管理系统
支持实时配置更新、版本控制和配置验证
"""

import logging
import json
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from contextlib import asynccontextmanager

from ..database.connection import get_db_session
from ..database.repository import ConfigRepository, StrategyRepository

logger = logging.getLogger(__name__)


class ConfigType(Enum):
    """配置类型枚举"""
    STRATEGY = "strategy"
    RISK = "risk"
    SYSTEM = "system"
    MONITORING = "monitoring"


@dataclass
class ConfigChange:
    """配置变更记录"""
    config_key: str
    old_value: Any
    new_value: Any
    change_type: str  # create/update/delete
    timestamp: datetime
    user: str = "system"
    reason: str = ""


@dataclass
class ConfigValidationResult:
    """配置验证结果"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class ConfigValidator:
    """配置验证器"""
    
    @staticmethod
    def validate_strategy_config(config: Dict[str, Any]) -> ConfigValidationResult:
        """验证策略配置"""
        errors = []
        warnings = []
        
        # 必需字段检查
        required_fields = ['name', 'version', 'class_path']
        for field in required_fields:
            if field not in config:
                errors.append(f"缺少必需字段: {field}")
        
        # 数值范围检查
        if 'max_position_size' in config:
            size = config['max_position_size']
            if not isinstance(size, (int, float)) or size <= 0 or size > 1:
                errors.append("max_position_size 必须在 0-1 之间")
        
        if 'risk_multiplier' in config:
            multiplier = config['risk_multiplier']
            if not isinstance(multiplier, (int, float)) or multiplier <= 0:
                errors.append("risk_multiplier 必须大于 0")
        
        # 时间框架检查
        if 'timeframes' in config:
            valid_timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d']
            for tf in config['timeframes']:
                if tf not in valid_timeframes:
                    warnings.append(f"未知时间框架: {tf}")
        
        return ConfigValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    @staticmethod
    def validate_risk_config(config: Dict[str, Any]) -> ConfigValidationResult:
        """验证风险配置"""
        errors = []
        warnings = []
        
        # 风险参数检查
        risk_params = ['max_drawdown', 'stop_loss', 'take_profit', 'max_daily_loss']
        for param in risk_params:
            if param in config:
                value = config[param]
                if not isinstance(value, (int, float)) or value <= 0 or value > 1:
                    errors.append(f"{param} 必须在 0-1 之间")
        
        # 仓位限制检查
        if 'max_position_size' in config:
            size = config['max_position_size']
            if not isinstance(size, (int, float)) or size <= 0 or size > 1:
                errors.append("max_position_size 必须在 0-1 之间")
        
        return ConfigValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )


class DynamicConfigManager:
    """动态配置管理器"""
    
    def __init__(self):
        self._config_cache: Dict[str, Dict[str, Any]] = {}
        self._change_listeners: List[Callable] = []
        self._lock = threading.RLock()
        self._validator = ConfigValidator()
        
        # 启动配置同步任务
        self._sync_task = None
        self._running = False
    
    def start(self):
        """启动配置管理器"""
        if self._running:
            return
        
        self._running = True
        self._sync_task = threading.Thread(target=self._sync_loop, daemon=True)
        self._sync_task.start()
        logger.info("动态配置管理器已启动")
    
    def stop(self):
        """停止配置管理器"""
        self._running = False
        if self._sync_task:
            self._sync_task.join(timeout=5)
        logger.info("动态配置管理器已停止")
    
    def add_change_listener(self, callback: Callable[[str, Any, Any], None]):
        """添加配置变更监听器"""
        with self._lock:
            self._change_listeners.append(callback)
    
    def remove_change_listener(self, callback: Callable[[str, Any, Any], None]):
        """移除配置变更监听器"""
        with self._lock:
            if callback in self._change_listeners:
                self._change_listeners.remove(callback)
    
    def _notify_change(self, config_key: str, old_value: Any, new_value: Any):
        """通知配置变更"""
        with self._lock:
            for callback in self._change_listeners:
                try:
                    callback(config_key, old_value, new_value)
                except Exception as e:
                    logger.error(f"配置变更通知失败: {e}")
    
    def _sync_loop(self):
        """配置同步循环"""
        while self._running:
            try:
                self._sync_configs()
                threading.Event().wait(10)  # 每10秒同步一次
            except Exception as e:
                logger.error(f"配置同步失败: {e}")
                threading.Event().wait(30)  # 出错时等待30秒
    
    def _sync_configs(self):
        """同步配置到缓存"""
        try:
            with get_db_session() as session:
                config_repo = ConfigRepository(session)
                
                # 获取所有策略配置
                strategies = config_repo.session.query(StrategyRepository(session).get_all_strategies())
                for strategy in strategies:
                    strategy_id = strategy.strategy_id
                    configs = config_repo.get_all_strategy_configs(strategy_id)
                    
                    with self._lock:
                        old_config = self._config_cache.get(strategy_id, {})
                        self._config_cache[strategy_id] = configs
                        
                        # 检查配置变更
                        for key, value in configs.items():
                            if key not in old_config or old_config[key] != value:
                                self._notify_change(f"{strategy_id}.{key}", 
                                                  old_config.get(key), value)
        
        except Exception as e:
            logger.error(f"同步配置失败: {e}")
    
    def get_strategy_config(self, strategy_id: str, config_key: str = None, 
                          use_cache: bool = True) -> Union[Dict[str, Any], Any]:
        """获取策略配置"""
        try:
            if use_cache:
                with self._lock:
                    strategy_configs = self._config_cache.get(strategy_id, {})
                    if config_key:
                        return strategy_configs.get(config_key)
                    return strategy_configs
            
            # 从数据库获取
            with get_db_session() as session:
                config_repo = ConfigRepository(session)
                if config_key:
                    config = config_repo.get_strategy_config(strategy_id, config_key)
                    return config.config_value if config else None
                else:
                    return config_repo.get_all_strategy_configs(strategy_id)
        
        except Exception as e:
            logger.error(f"获取策略配置失败: {e}")
            return {} if config_key is None else None
    
    def set_strategy_config(self, strategy_id: str, config_key: str, 
                          config_value: Any, config_type: str = 'strategy',
                          validate: bool = True) -> bool:
        """设置策略配置"""
        try:
            # 验证配置
            if validate:
                validation_result = self._validate_config(config_type, {config_key: config_value})
                if not validation_result.is_valid:
                    logger.error(f"配置验证失败: {validation_result.errors}")
                    return False
            
            # 保存到数据库
            with get_db_session() as session:
                config_repo = ConfigRepository(session)
                config_repo.set_strategy_config(
                    strategy_id=strategy_id,
                    config_key=config_key,
                    config_value=config_value,
                    config_type=config_type
                )
            
            # 更新缓存
            with self._lock:
                if strategy_id not in self._config_cache:
                    self._config_cache[strategy_id] = {}
                
                old_value = self._config_cache[strategy_id].get(config_key)
                self._config_cache[strategy_id][config_key] = config_value
                
                # 通知变更
                self._notify_change(f"{strategy_id}.{config_key}", old_value, config_value)
            
            logger.info(f"策略配置已更新: {strategy_id}.{config_key}")
            return True
        
        except Exception as e:
            logger.error(f"设置策略配置失败: {e}")
            return False
    
    def update_strategy_configs(self, strategy_id: str, configs: Dict[str, Any],
                              config_type: str = 'strategy', validate: bool = True) -> bool:
        """批量更新策略配置"""
        try:
            # 验证配置
            if validate:
                validation_result = self._validate_config(config_type, configs)
                if not validation_result.is_valid:
                    logger.error(f"配置验证失败: {validation_result.errors}")
                    return False
            
            # 保存到数据库
            with get_db_session() as session:
                config_repo = ConfigRepository(session)
                for key, value in configs.items():
                    config_repo.set_strategy_config(
                        strategy_id=strategy_id,
                        config_key=key,
                        config_value=value,
                        config_type=config_type
                    )
            
            # 更新缓存
            with self._lock:
                if strategy_id not in self._config_cache:
                    self._config_cache[strategy_id] = {}
                
                old_config = self._config_cache[strategy_id].copy()
                self._config_cache[strategy_id].update(configs)
                
                # 通知变更
                for key, value in configs.items():
                    old_value = old_config.get(key)
                    self._notify_change(f"{strategy_id}.{key}", old_value, value)
            
            logger.info(f"策略配置已批量更新: {strategy_id}")
            return True
        
        except Exception as e:
            logger.error(f"批量更新策略配置失败: {e}")
            return False
    
    def delete_strategy_config(self, strategy_id: str, config_key: str) -> bool:
        """删除策略配置"""
        try:
            with get_db_session() as session:
                config_repo = ConfigRepository(session)
                success = config_repo.delete_strategy_config(strategy_id, config_key)
            
            if success:
                # 更新缓存
                with self._lock:
                    if strategy_id in self._config_cache:
                        old_value = self._config_cache[strategy_id].pop(config_key, None)
                        self._notify_change(f"{strategy_id}.{config_key}", old_value, None)
                
                logger.info(f"策略配置已删除: {strategy_id}.{config_key}")
            
            return success
        
        except Exception as e:
            logger.error(f"删除策略配置失败: {e}")
            return False
    
    def get_system_config(self, config_key: str, default_value: Any = None) -> Any:
        """获取系统配置"""
        try:
            with get_db_session() as session:
                config_repo = ConfigRepository(session)
                config = config_repo.get_system_config(config_key)
                return config.config_value if config else default_value
        
        except Exception as e:
            logger.error(f"获取系统配置失败: {e}")
            return default_value
    
    def set_system_config(self, config_key: str, config_value: Any, 
                         config_type: str = 'system') -> bool:
        """设置系统配置"""
        try:
            with get_db_session() as session:
                config_repo = ConfigRepository(session)
                config_repo.set_system_config(
                    config_key=config_key,
                    config_value=config_value,
                    config_type=config_type
                )
            
            logger.info(f"系统配置已更新: {config_key}")
            return True
        
        except Exception as e:
            logger.error(f"设置系统配置失败: {e}")
            return False
    
    def _validate_config(self, config_type: str, config: Dict[str, Any]) -> ConfigValidationResult:
        """验证配置"""
        if config_type == ConfigType.STRATEGY.value:
            return self._validator.validate_strategy_config(config)
        elif config_type == ConfigType.RISK.value:
            return self._validator.validate_risk_config(config)
        else:
            return ConfigValidationResult(is_valid=True)
    
    def get_config_history(self, strategy_id: str, config_key: str, 
                          limit: int = 10) -> List[ConfigChange]:
        """获取配置变更历史"""
        # TODO: 实现配置变更历史记录
        return []
    
    def export_config(self, strategy_id: str) -> Dict[str, Any]:
        """导出策略配置"""
        return self.get_strategy_config(strategy_id)
    
    def import_config(self, strategy_id: str, config: Dict[str, Any], 
                     overwrite: bool = False) -> bool:
        """导入策略配置"""
        try:
            if not overwrite:
                # 检查是否已存在配置
                existing = self.get_strategy_config(strategy_id)
                if existing:
                    logger.warning(f"策略 {strategy_id} 已存在配置，跳过导入")
                    return False
            
            return self.update_strategy_configs(strategy_id, config)
        
        except Exception as e:
            logger.error(f"导入策略配置失败: {e}")
            return False


# 全局配置管理器实例
config_manager = DynamicConfigManager()


def get_config_manager() -> DynamicConfigManager:
    """获取配置管理器实例"""
    return config_manager


def init_config_manager():
    """初始化配置管理器"""
    config_manager.start()
    logger.info("配置管理器初始化完成")
