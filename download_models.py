# -*- coding: utf-8 -*-
"""
Kronos模型预下载脚本
用于在打包前下载所有必需的模型文件到本地目录
"""

import os
import sys
from pathlib import Path

def download_models():
    """下载Kronos模型到本地目录"""
    
    print("=" * 60)
    print("Kronos模型预下载工具")
    print("=" * 60)
    
    # 检查依赖
    try:
        from model import KronosTokenizer, Kronos
        print("✅ Kronos模块导入成功")
    except ImportError as e:
        print(f"❌ 无法导入Kronos模块: {e}")
        print("请确保已安装所有依赖: pip install -r requirements.txt")
        return False
    
    # 设置下载目录
    base_dir = Path(__file__).parent
    models_dir = base_dir / "models" / "NeoQuasar"
    
    tokenizer_path = models_dir / "Kronos-Tokenizer-base"
    model_path = models_dir / "Kronos-base"
    
    print(f"\n📁 模型存储目录: {models_dir}")
    
    # 创建目录
    os.makedirs(tokenizer_path, exist_ok=True)
    os.makedirs(model_path, exist_ok=True)
    
    # 下载Tokenizer
    print("\n" + "=" * 60)
    print("步骤1: 下载 Kronos-Tokenizer-base")
    print("=" * 60)
    
    if _check_model_exists(tokenizer_path):
        print(f"⚠️ Tokenizer已存在: {tokenizer_path}")
        response = input("是否重新下载? (y/n): ")
        if response.lower() != 'y':
            print("跳过Tokenizer下载")
        else:
            _download_tokenizer(tokenizer_path)
    else:
        _download_tokenizer(tokenizer_path)
    
    # 下载Model
    print("\n" + "=" * 60)
    print("步骤2: 下载 Kronos-base")
    print("=" * 60)
    
    if _check_model_exists(model_path):
        print(f"⚠️ Model已存在: {model_path}")
        response = input("是否重新下载? (y/n): ")
        if response.lower() != 'y':
            print("跳过Model下载")
        else:
            _download_model(model_path)
    else:
        _download_model(model_path)
    
    # 验证下载结果
    print("\n" + "=" * 60)
    print("验证下载结果")
    print("=" * 60)
    
    tokenizer_ok = _check_model_exists(tokenizer_path)
    model_ok = _check_model_exists(model_path)
    
    if tokenizer_ok and model_ok:
        print("\n✅ 所有模型下载成功!")
        print(f"   Tokenizer: {tokenizer_path}")
        print(f"   Model: {model_path}")
        
        # 计算总大小
        total_size = _get_directory_size(tokenizer_path) + _get_directory_size(model_path)
        print(f"   总大小: {total_size / (1024**3):.2f} GB")
        
        print("\n💡 提示:")
        print("   现在可以运行 build_package.py 进行打包")
        print("   打包后的exe将包含这些模型,无需网络连接即可运行")
        
        return True
    else:
        print("\n❌ 模型下载不完整!")
        if not tokenizer_ok:
            print(f"   缺少: {tokenizer_path}")
        if not model_ok:
            print(f"   缺少: {model_path}")
        return False


def _download_tokenizer(path):
    """下载Tokenizer模型"""
    from model import KronosTokenizer
    
    print(f"📥 正在下载 Tokenizer 到: {path}")
    print("   这可能需要几分钟时间,请耐心等待...")
    
    try:
        tokenizer = KronosTokenizer.from_pretrained(
            "NeoQuasar/Kronos-Tokenizer-base",
            cache_dir=str(path.parent),
            local_files_only=False
        )
        
        # 保存到指定路径
        tokenizer.save_pretrained(str(path))
        
        print(f"✅ Tokenizer下载并保存成功: {path}")
        size = _get_directory_size(path)
        print(f"   大小: {size / (1024**2):.2f} MB")
        
    except Exception as e:
        print(f"❌ Tokenizer下载失败: {e}")
        import traceback
        traceback.print_exc()
        raise


def _download_model(path):
    """下载Kronos模型"""
    from model import Kronos
    
    print(f"📥 正在下载 Kronos-base 到: {path}")
    print("   这可能需要较长时间(模型约1-2GB),请耐心等待...")
    print("   如果网络不稳定,可能会重试多次")
    
    try:
        model = Kronos.from_pretrained(
            "NeoQuasar/Kronos-base",
            cache_dir=str(path.parent),
            local_files_only=False
        )
        
        # 保存到指定路径
        model.save_pretrained(str(path))
        
        print(f"✅ Model下载并保存成功: {path}")
        size = _get_directory_size(path)
        print(f"   大小: {size / (1024**3):.2f} GB")
        
    except Exception as e:
        print(f"❌ Model下载失败: {e}")
        import traceback
        traceback.print_exc()
        raise


def _check_model_exists(path):
    """检查模型是否已存在且完整"""
    path = Path(path)
    
    if not path.exists():
        return False
    
    # 检查关键文件
    required_files = ['config.json', 'pytorch_model.bin']
    for file in required_files:
        if not (path / file).exists():
            return False
    
    # 检查文件大小(至少100MB才认为是完整的)
    total_size = _get_directory_size(path)
    if total_size < 100 * 1024 * 1024:  # 100MB
        return False
    
    return True


def _get_directory_size(path):
    """计算目录总大小(字节)"""
    total_size = 0
    path = Path(path)
    
    if not path.exists():
        return 0
    
    for item in path.rglob('*'):
        if item.is_file():
            total_size += item.stat().st_size
    
    return total_size


if __name__ == "__main__":
    try:
        success = download_models()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断下载")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
