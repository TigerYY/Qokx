#!/usr/bin/env python3
"""
安全配置检查脚本
验证所有敏感信息都得到适当保护，不会被意外提交到GitHub
"""

import os
import re
from pathlib import Path

def check_gitignore():
    """检查.gitignore文件配置"""
    gitignore_path = Path('.gitignore')
    
    if not gitignore_path.exists():
        print("❌ 未找到.gitignore文件")
        return False
    
    with open(gitignore_path, 'r') as f:
        content = f.read()
    
    # 检查关键模式
    patterns_to_check = [
        r'\.env',
        r'\.env\.',
        r'api_config\.enc',
        r'logs/',
        r'__pycache__/',
        r'\.DS_Store'
    ]
    
    missing_patterns = []
    for pattern in patterns_to_check:
        if not re.search(pattern, content):
            missing_patterns.append(pattern)
    
    if missing_patterns:
        print(f"❌ .gitignore中缺少以下模式: {missing_patterns}")
        return False
    
    print("✅ .gitignore文件配置正确")
    return True

def check_sensitive_files():
    """检查敏感文件是否存在"""
    sensitive_files = [
        '.env',
        'api_config.enc',
        'logs/',
        '__pycache__/'
    ]
    
    existing_files = []
    for file in sensitive_files:
        if Path(file).exists():
            existing_files.append(file)
    
    if existing_files:
        print(f"⚠️  发现敏感文件/目录: {existing_files}")
        print("   请确保这些文件在.gitignore中已被正确忽略")
        return False
    
    print("✅ 未发现暴露的敏感文件")
    return True

def check_env_example():
    """检查.env.example文件是否安全"""
    env_example_path = Path('.env.example')
    
    if not env_example_path.exists():
        print("❌ 未找到.env.example文件")
        return False
    
    with open(env_example_path, 'r') as f:
        content = f.read()
    
    # 检查是否包含真实的API密钥（排除示例值）
    example_patterns = [
        r'OKX_API_KEY=your_api_key_here',
        r'OKX_SECRET_KEY=your_secret_key_here',
        r'OKX_PASSPHRASE=your_passphrase_here',
        r'API_MASTER_KEY=your_strong_master_password_here'
    ]
    
    # 检查是否包含看起来像真实密钥的值
    real_key_patterns = [
        r'OKX_API_KEY=[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}',  # UUID格式
        r'OKX_SECRET_KEY=[A-F0-9]{32}',  # 32位十六进制
        r'OKX_PASSPHRASE=[^\n]{5,}'  # 任何非示例的密码
    ]
    
    # 检查是否包含示例值
    has_example_values = all(re.search(pattern, content) for pattern in example_patterns[:3])
    
    # 检查是否包含真实密钥
    has_real_keys = any(re.search(pattern, content) for pattern in real_key_patterns)
    
    if not has_example_values:
        print("⚠️  .env.example文件中缺少标准示例值")
        
    if has_real_keys:
        print("❌ .env.example文件中可能包含真实的API密钥")
        return False
    
    print("✅ .env.example文件安全（只包含示例值）")
    return True

def check_hardcoded_secrets():
    """检查代码中是否硬编码了敏感信息"""
    python_files = list(Path('.').rglob('*.py'))
    
    hardcoded_secrets = []
    
    secret_patterns = [
        r'api[_-]?key[\s\t]*=[\s\t]*["\'][^"\']{10,}["\']',
        r'secret[\s\t]*=[\s\t]*["\'][^"\']{10,}["\']',
        r'passphrase[\s\t]*=[\s\t]*["\'][^"\']{5,}["\']',
        r'password[\s\t]*=[\s\t]*["\'][^"\']{5,}["\']'
    ]
    
    for py_file in python_files:
        # 跳过测试文件和示例文件
        if 'test' in str(py_file) or 'example' in str(py_file):
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for pattern in secret_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    hardcoded_secrets.append(f"{py_file}: 可能包含硬编码密钥")
                    
        except Exception as e:
            print(f"无法读取文件 {py_file}: {e}")
    
    if hardcoded_secrets:
        print("❌ 发现可能硬编码的敏感信息:")
        for secret in hardcoded_secrets:
            print(f"   - {secret}")
        return False
    
    print("✅ 未发现硬编码的敏感信息")
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("🔒 安全配置检查")
    print("=" * 60)
    
    checks = [
        ("GitIgnore配置", check_gitignore),
        ("敏感文件检查", check_sensitive_files),
        ("环境示例文件", check_env_example),
        ("硬编码密钥检查", check_hardcoded_secrets)
    ]
    
    results = []
    
    for check_name, check_func in checks:
        print(f"\n📋 检查: {check_name}")
        result = check_func()
        results.append(result)
    
    print("\n" + "=" * 60)
    print("📊 检查结果汇总")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print("✅ 所有安全检查通过！")
        print("✅ 您的API密钥和敏感信息得到适当保护")
        print("✅ 可以安全地使用Git进行版本控制")
    else:
        print(f"⚠️  安全检查: {passed}/{total} 项通过")
        print("❌ 请修复上述问题后再提交代码到GitHub")
    
    print("=" * 60)
    
    # 提供安全建议
    print("\n🔐 安全建议:")
    print("1. 永远不要将真实的.env文件提交到版本控制")
    print("2. 使用环境变量或加密配置文件存储密钥")
    print("3. 定期轮换API密钥")
    print("4. 使用不同的密钥用于测试和生产环境")
    print("5. 为API密钥设置最小必要权限")

if __name__ == "__main__":
    main()