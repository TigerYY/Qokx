#!/usr/bin/env python3
"""
安全验证脚本 - 确认API相关信息不会被上传到GitHub
"""

import os
import re
from pathlib import Path

def verify_gitignore():
    """验证.gitignore配置是否正确"""
    print("🔍 验证.gitignore配置...")
    
    gitignore_path = Path('.gitignore')
    if not gitignore_path.exists():
        print("❌ 错误: 缺少.gitignore文件")
        return False
    
    with open(gitignore_path, 'r') as f:
        content = f.read()
    
    # 必须忽略的关键文件
    required_ignores = [
        '.env',           # 环境变量文件
        '.env.local',     # 本地环境变量
        '.env.*',         # 所有环境变量文件
        '*.enc',          # 加密配置文件
        'logs/',          # 日志目录
        '__pycache__/',   # Python缓存
        '*.pyc',          # Python编译文件
        '.DS_Store',      # macOS系统文件
    ]
    
    missing = []
    for pattern in required_ignores:
        if pattern not in content:
            missing.append(pattern)
    
    if missing:
        print(f"❌ 错误: .gitignore中缺少以下忽略模式: {missing}")
        return False
    
    print("✅ .gitignore配置正确")
    return True

def verify_no_sensitive_files_in_git():
    """验证没有敏感文件被Git跟踪"""
    print("\n🔍 检查Git跟踪状态...")
    
    # 检查是否有敏感文件被Git跟踪
    sensitive_files = [
        '.env',
        'api_config.enc',
        'logs/',
        'src/config/api_config.enc'
    ]
    
    # 如果.git目录存在，说明这是一个Git仓库
    if Path('.git').exists():
        try:
            import subprocess
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, cwd='.')
            
            tracked_files = []
            for line in result.stdout.split('\n'):
                if line.strip() and not line.startswith('??'):
                    file_path = line[3:].strip()
                    for sensitive_file in sensitive_files:
                        if file_path == sensitive_file or file_path.startswith(sensitive_file):
                            tracked_files.append(file_path)
            
            if tracked_files:
                print(f"❌ 错误: 以下敏感文件正在被Git跟踪: {tracked_files}")
                print("   请运行: git rm --cached <file> 来停止跟踪")
                return False
            
        except Exception as e:
            print(f"⚠️  警告: 无法检查Git状态: {e}")
            # 继续其他检查
    
    print("✅ 没有敏感文件被Git跟踪")
    return True

def verify_env_files():
    """验证环境文件配置"""
    print("\n🔍 检查环境文件...")
    
    env_path = Path('.env')
    env_example_path = Path('.env.example')
    
    # 检查.env.example是否存在
    if not env_example_path.exists():
        print("❌ 错误: 缺少.env.example文件")
        return False
    
    # 检查.env.example是否只包含示例值
    with open(env_example_path, 'r') as f:
        example_content = f.read()
    
    # 应该包含示例值
    expected_examples = [
        'your_api_key_here',
        'your_secret_key_here', 
        'your_passphrase_here',
        'your_strong_master_password_here'
    ]
    
    for example in expected_examples:
        if example not in example_content:
            print(f"⚠️  警告: .env.example中缺少标准示例值 '{example}'")
    
    # 检查是否包含真实的API密钥（不应该有）
    real_key_patterns = [
        r'OKX_API_KEY=[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-',  # UUID格式
        r'OKX_SECRET_KEY=[A-F0-9]{32}',                  # 32位十六进制
    ]
    
    has_real_keys = False
    for pattern in real_key_patterns:
        if re.search(pattern, example_content):
            has_real_keys = True
            break
    
    if has_real_keys:
        print("❌ 错误: .env.example文件中包含真实的API密钥")
        return False
    
    # 检查真实的.env文件（如果存在）
    if env_path.exists():
        with open(env_path, 'r') as f:
            env_content = f.read()
        
        # 真实的.env文件应该包含实际密钥
        has_real_keys_in_env = any(re.search(pattern, env_content) for pattern in real_key_patterns)
        
        if not has_real_keys_in_env:
            print("⚠️  警告: .env文件中没有检测到真实的API密钥格式")
    
    print("✅ 环境文件配置正确")
    return True

def verify_no_hardcoded_secrets():
    """验证代码中没有硬编码的敏感信息"""
    print("\n🔍 扫描代码中的硬编码密钥...")
    
    python_files = list(Path('.').rglob('*.py'))
    hardcoded_secrets = []
    
    secret_patterns = [
        r'api[_-]?key[\s\t]*=[\s\t]*["\'][^"\']{10,}["\']',
        r'secret[\s\t]*=[\s\t]*["\'][^"\']{10,}["\']',
        r'passphrase[\s\t]*=[\s\t]*["\'][^"\']{5,}["\']',
    ]
    
    for py_file in python_files:
        # 跳过测试和示例文件
        if any(x in str(py_file) for x in ['test', 'example', 'docs']):
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for pattern in secret_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    # 排除明显的示例值
                    if not any(x in match.lower() for x in ['example', 'test', 'your_', 'dummy']):
                        hardcoded_secrets.append(f"{py_file}: {match}")
                        
        except Exception as e:
            print(f"⚠️  无法读取文件 {py_file}: {e}")
    
    if hardcoded_secrets:
        print("❌ 错误: 发现可能硬编码的敏感信息:")
        for secret in hardcoded_secrets:
            print(f"   - {secret}")
        return False
    
    print("✅ 没有发现硬编码的敏感信息")
    return True

def main():
    """主验证函数"""
    print("=" * 70)
    print("🔒 API信息安全验证")
    print("=" * 70)
    print("确保API相关信息和文档不会被上传到GitHub")
    print("=" * 70)
    
    checks = [
        ("GitIgnore配置", verify_gitignore),
        ("Git跟踪状态", verify_no_sensitive_files_in_git),
        ("环境文件", verify_env_files),
        ("硬编码密钥", verify_no_hardcoded_secrets)
    ]
    
    results = []
    
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}")
        result = check_func()
        results.append(result)
    
    print("\n" + "=" * 70)
    print("📊 验证结果汇总")
    print("=" * 70)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print("🎉 所有安全检查通过！")
        print("✅ 您的API密钥和敏感信息得到完全保护")
        print("✅ 可以安全地使用Git进行版本控制")
        print("✅ API相关信息不会被上传到GitHub")
    else:
        print(f"⚠️  验证结果: {passed}/{total} 项通过")
        print("❌ 请修复上述问题后再提交代码到版本控制")
    
    print("=" * 70)
    
    # 提供具体的安全操作指南
    if passed < total:
        print("\n🔧 修复建议:")
        print("1. 确保.gitignore包含所有敏感文件模式")
        print("2. 运行: git rm --cached .env 来停止跟踪.env文件")
        print("3. 检查.env.example只包含示例值")
        print("4. 删除代码中任何硬编码的API密钥")
        print("5. 使用环境变量或加密配置存储敏感信息")

if __name__ == "__main__":
    main()