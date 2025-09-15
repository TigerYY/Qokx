"""
API密钥管理和安全配置
"""

import os
import json
import base64
import logging
from typing import Dict, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class APIConfigManager:
    """API配置管理器 - 安全的密钥存储和管理"""
    
    def __init__(self, config_file: str = "api_config.enc", master_key: Optional[str] = None):
        """
        初始化API配置管理器
        
        Args:
            config_file: 加密配置文件路径
            master_key: 主密钥（如果为None，则从环境变量获取）
        """
        self.config_file = config_file
        self.master_key = master_key or os.getenv('API_MASTER_KEY')
        
        if not self.master_key:
            raise ValueError("需要设置主密钥（环境变量API_MASTER_KEY或构造函数参数）")
        
        # 派生加密密钥
        self.fernet = self._derive_encryption_key(self.master_key)
    
    def _derive_encryption_key(self, master_key: str) -> Fernet:
        """从主密钥派生加密密钥"""
        # 使用PBKDF2派生密钥
        salt = b'okx_api_salt_'  # 固定salt（生产环境应使用随机salt）
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
        return Fernet(key)
    
    def save_config(self, config_data: Dict, profile: str = 'default') -> bool:
        """
        保存加密的API配置
        
        Args:
            config_data: 配置数据（包含api_key, secret_key, passphrase）
            profile: 配置profile名称
        
        Returns:
            bool: 是否保存成功
        """
        try:
            # 验证必要字段
            required_fields = ['api_key', 'secret_key', 'passphrase']
            for field in required_fields:
                if field not in config_data:
                    raise ValueError(f"缺少必要字段: {field}")
            
            # 读取现有配置
            existing_config = self._load_all_configs()
            
            # 更新配置
            existing_config[profile] = config_data
            
            # 加密并保存
            encrypted_data = self.fernet.encrypt(json.dumps(existing_config).encode())
            
            with open(self.config_file, 'wb') as f:
                f.write(encrypted_data)
            
            logger.info(f"API配置已保存到profile: {profile}")
            return True
            
        except Exception as e:
            logger.error(f"保存API配置失败: {e}")
            return False
    
    def load_config(self, profile: str = 'default') -> Optional[Dict]:
        """
        加载指定profile的API配置
        
        Args:
            profile: 配置profile名称
        
        Returns:
            Optional[Dict]: 配置数据，如果不存在则返回None
        """
        try:
            all_configs = self._load_all_configs()
            return all_configs.get(profile)
            
        except Exception as e:
            logger.error(f"加载API配置失败: {e}")
            return None
    
    def _load_all_configs(self) -> Dict:
        """加载所有加密的配置"""
        if not os.path.exists(self.config_file):
            return {}
        
        try:
            with open(self.config_file, 'rb') as f:
                encrypted_data = f.read()
            
            # 解密数据
            decrypted_data = self.fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
            
        except Exception as e:
            logger.error(f"解密配置数据失败: {e}")
            return {}
    
    def delete_config(self, profile: str) -> bool:
        """删除指定profile的配置"""
        try:
            all_configs = self._load_all_configs()
            if profile in all_configs:
                del all_configs[profile]
                
                # 重新加密保存
                encrypted_data = self.fernet.encrypt(json.dumps(all_configs).encode())
                with open(self.config_file, 'wb') as f:
                    f.write(encrypted_data)
                
                logger.info(f"已删除profile: {profile}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"删除配置失败: {e}")
            return False
    
    def list_profiles(self) -> list:
        """列出所有可用的配置profile"""
        all_configs = self._load_all_configs()
        return list(all_configs.keys())
    
    def validate_config(self, profile: str) -> bool:
        """验证配置是否完整有效"""
        config = self.load_config(profile)
        if not config:
            return False
        
        required_fields = ['api_key', 'secret_key', 'passphrase']
        return all(field in config for field in required_fields)


class EnvironmentConfig:
    """环境变量配置管理"""
    
    @staticmethod
    def load_from_env() -> Optional[Dict]:
        """从环境变量加载配置"""
        try:
            api_key = os.getenv('OKX_API_KEY')
            secret_key = os.getenv('OKX_SECRET_KEY')
            passphrase = os.getenv('OKX_PASSPHRASE')
            testnet = os.getenv('OKX_TESTNET', 'false').lower() == 'true'
            
            if not all([api_key, secret_key, passphrase]):
                return None
            
            return {
                'api_key': api_key,
                'secret_key': secret_key,
                'passphrase': passphrase,
                'testnet': testnet
            }
            
        except Exception as e:
            logger.error(f"从环境变量加载配置失败: {e}")
            return None
    
    @staticmethod
    def validate_env_config() -> bool:
        """验证环境变量配置是否完整"""
        config = EnvironmentConfig.load_from_env()
        return config is not None


def get_api_config(profile: str = 'default') -> Dict:
    """
    获取API配置（优先使用环境变量，其次使用加密配置文件）
    
    Args:
        profile: 配置profile名称
    
    Returns:
        Dict: API配置
    """
    # 首先尝试环境变量
    env_config = EnvironmentConfig.load_from_env()
    if env_config:
        logger.info("使用环境变量配置")
        return env_config
    
    # 其次尝试加密配置文件
    try:
        master_key = os.getenv('API_MASTER_KEY')
        if not master_key:
            raise ValueError("需要设置API_MASTER_KEY环境变量")
        
        config_manager = APIConfigManager(master_key=master_key)
        config = config_manager.load_config(profile)
        
        if config:
            logger.info(f"使用加密配置文件profile: {profile}")
            return config
        
    except Exception as e:
        logger.warning(f"加载加密配置失败: {e}")
    
    # 都没有配置
    raise ValueError(
        "未找到API配置。请选择以下方式之一：\n"
        "1. 设置环境变量: OKX_API_KEY, OKX_SECRET_KEY, OKX_PASSPHRASE\n"
        "2. 使用APIConfigManager保存加密配置，并设置API_MASTER_KEY环境变量"
    )


# 安全工具函数
def mask_secret(secret: str, visible_chars: int = 4) -> str:
    """掩码显示敏感信息"""
    if not secret or len(secret) <= visible_chars:
        return "*" * 8
    
    visible_part = secret[:visible_chars]
    masked_part = "*" * (len(secret) - visible_chars)
    return visible_part + masked_part


def validate_api_permissions(config: Dict) -> bool:
    """验证API密钥权限（需要实际调用API验证）"""
    # 这里只是示例，实际应该调用OKX API验证权限
    required_permissions = ['读取', '交易']
    logger.info(f"API密钥权限验证: 需要{required_permissions}")
    return True


# 配置示例
if __name__ == "__main__":
    # 示例：保存配置到加密文件
    config_data = {
        'api_key': 'your_api_key_here',
        'secret_key': 'your_secret_key_here', 
        'passphrase': 'your_passphrase_here',
        'testnet': True
    }
    
    # 需要先设置主密钥
    os.environ['API_MASTER_KEY'] = 'your_strong_master_password_here'
    
    manager = APIConfigManager()
    if manager.save_config(config_data, 'test_profile'):
        print("配置保存成功")
        
        # 加载配置
        loaded_config = manager.load_config('test_profile')
        print(f"加载的配置: {mask_secret(str(loaded_config))}")
    
    # 使用环境变量示例
    os.environ['OKX_API_KEY'] = 'your_api_key'
    os.environ['OKX_SECRET_KEY'] = 'your_secret_key'
    os.environ['OKX_PASSPHRASE'] = 'your_passphrase'
    
    env_config = get_api_config()
    print(f"环境变量配置: {mask_secret(str(env_config))}")