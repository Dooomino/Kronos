# -*- coding: utf-8 -*-
"""
使用Nuitka打包Kronos股票预测系统
"""

import os
import sys
import subprocess
from pathlib import Path

def check_environment():
    """检查环境"""
    print("=" * 60)
    print("Kronos Nuitka打包工具")
    print("=" * 60)
    
    # 检查虚拟环境
    venv_python = Path(".venv/Scripts/python.exe")
    if not venv_python.exists():
        print("❌ 错误: 虚拟环境不存在")
        return False
    
    print(f"✅ 虚拟环境: {venv_python}")
    
    # 检查Nuitka
    try:
        result = subprocess.run(
            [str(venv_python), "-m", "nuitka", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✅ Nuitka已安装: {result.stdout.strip().split(chr(10))[0]}")
        else:
            print("❌ Nuitka未安装，请运行: pip install nuitka zstandard")
            return False
    except Exception as e:
        print(f"❌ 检查Nuitka失败: {e}")
        return False
    
    # 检查模型文件
    if not Path("models/NeoQuasar/Kronos-Tokenizer-base/config.json").exists():
        print("⚠️ 警告: 模型文件不存在，打包后将无法离线运行")
        print("   建议先运行: python download_models.py")
    else:
        print("✅ 模型文件已存在")
    
    return True

def build():
    """执行打包"""
    print("\n🔨 开始打包...")
    print("=" * 60)
    
    # 清理旧的dist目录
    import shutil
    if os.path.exists('dist_nuitka'):
        print("🗑️  清理旧的dist_nuitka目录...")
        shutil.rmtree('dist_nuitka')
    
    # 构建Nuitka命令
    cmd = [
        ".venv/Scripts/python.exe",
        "-m", "nuitka",
        "--standalone",                    # 独立模式
        "--onefile",                       # 单文件exe
        "--windows-console-mode=force",    # 显示控制台窗口
        "--include-package=model",         # 包含model包
        "--include-package=data_sources",  # 包含data_sources包
        "--include-package=safetensors",   # 包含safetensors
        "--include-package=huggingface_hub",
        "--include-package=torch",
        "--include-package=pandas",
        "--include-package=numpy",
        "--include-package=matplotlib",
        "--include-package=akshare",
        "--include-package=baostock",
        "--include-data-dir=models=models",           # 包含模型目录
        "--include-data-dir=model=model",             # 包含model目录
        "--include-data-dir=data_sources=data_sources", # 包含data_sources目录
        "--include-data-dir=cache=cache",             # 包含cache目录（如果有）
        "--nofollow-import-to=tkinter.test",          # 排除测试模块
        "--nofollow-import-to=IPython",
        "--nofollow-import-to=jupyter",
        "--output-dir=dist_nuitka",       # 输出目录
        "--remove-output",                # 清理临时文件
        "--enable-plugin=tk-inter",       # 启用tkinter支持
        "--python-flag=no_site",          # 不加载site模块，加快速度
        "--noinclude-pytest-mode=nofollow",  # 不包含pytest
        "main.py"                         # 入口文件
    ]
    
    print(f"📋 执行命令:")
    print("   python -m nuitka \\")
    for i, arg in enumerate(cmd[2:], 2):
        if i < len(cmd) - 1:
            print(f"   {arg} \\")
        else:
            print(f"   {arg}")
    print()
    
    try:
        result = subprocess.run(cmd, cwd=os.getcwd())
        
        if result.returncode == 0:
            print("\n" + "=" * 60)
            print("✅ 打包成功!")
            
            # 查找生成的exe
            exe_path = Path("dist_nuitka/main.exe")
            if exe_path.exists():
                file_size = exe_path.stat().st_size / (1024 * 1024)
                print(f"📦 可执行文件: {exe_path.absolute()}")
                print(f"📊 文件大小: {file_size:.1f} MB")
                
                print("\n💡 提示:")
                print("  1. 首次运行可能需要解压，请耐心等待")
                print("  2. 确保目标机器有足够内存(建议8GB+)")
                print("  3. 日志和输出文件会在exe同目录生成")
            else:
                print("⚠️ 打包完成但未找到exe文件")
                print(f"   请检查 dist_nuitka 目录")
            
            print("=" * 60)
            return True
        else:
            print("\n❌ 打包失败，请检查上面的错误信息")
            return False
            
    except Exception as e:
        print(f"\n❌ 打包过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    if not check_environment():
        sys.exit(1)
    
    success = build()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
