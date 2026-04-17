# -*- coding: utf-8 -*-
"""
Kronos股票预测系统 - PyInstaller打包脚本
使用.venv虚拟环境进行打包
"""

import os
import sys
import subprocess
from pathlib import Path

def check_venv():
    """检查虚拟环境是否存在"""
    venv_python = Path(".venv/Scripts/python.exe")
    if not venv_python.exists():
        print("❌ 错误: 虚拟环境不存在")
        print("请先创建虚拟环境: python -m venv .venv")
        print("然后激活并安装依赖: .venv\\Scripts\\activate && pip install -r requirements.txt")
        return False
    
    print(f"✅ 找到虚拟环境: {venv_python}")
    return True

def check_dependencies():
    """检查必要的依赖是否已安装"""
    print("\n📦 检查依赖...")
    
    required_packages = [
        'pyinstaller',
        'akshare',
        'baostock',
        'pandas',
        'numpy',
        'matplotlib',
        'torch',
        'transformers',
        'safetensors',
        'einops',
        'huggingface_hub',
        'tqdm'
    ]
    
    missing = []
    for package in required_packages:
        try:
            # 对于pyinstaller，直接检查可执行文件
            if package == 'pyinstaller':
                pyinstaller_exe = Path(".venv/Scripts/pyinstaller.exe")
                if pyinstaller_exe.exists():
                    print(f"  ✅ {package} 已安装")
                    continue
                else:
                    missing.append(package)
                    print(f"  ❌ {package} 未安装")
                    continue
            
            result = subprocess.run(
                [".venv/Scripts/python.exe", "-c", f"import {package}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                missing.append(package)
                print(f"  ❌ {package} 未安装")
            else:
                print(f"  ✅ {package} 已安装")
        except Exception as e:
            missing.append(package)
            print(f"  ❌ {package} 检查失败: {e}")
    
    if missing:
        print(f"\n⚠️ 缺少以下依赖: {', '.join(missing)}")
        print("请运行: .venv\\Scripts\\pip install " + " ".join(missing))
        return False
    
    return True

def collect_data_files():
    """收集需要打包的数据文件"""
    print("\n📁 收集数据文件...")
    
    datas = []
    
    # 1. akshare的数据文件（通过hook自动收集，这里只确认路径）
    try:
        result = subprocess.run(
            [".venv/Scripts/python.exe", "-c", 
             "import akshare, os; print(os.path.dirname(akshare.__file__))"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            akshare_path = result.stdout.strip()
            calendar_file = os.path.join(akshare_path, 'file_fold', 'calendar.json')
            if os.path.exists(calendar_file):
                # 注意：akshare的数据文件会通过hook-akshare.py自动收集
                # 这里只是验证文件存在
                print(f"  ✅ akshare calendar.json 存在: {calendar_file}")
            else:
                print(f"  ⚠️ akshare calendar.json 不存在: {calendar_file}")
        else:
            print(f"  ⚠️ 无法获取akshare路径")
    except Exception as e:
        print(f"  ⚠️ 检查akshare时出错: {e}")
    
    # 2. model目录
    if os.path.exists('model'):
        datas.append(('model', 'model'))
        print(f"  ✅ model目录")
    else:
        print(f"  ❌ model目录不存在")
    
    # 3. data_sources目录
    if os.path.exists('data_sources'):
        datas.append(('data_sources', 'data_sources'))
        print(f"  ✅ data_sources目录")
    else:
        print(f"  ❌ data_sources目录不存在")
    
    return datas

def create_spec_file(datas):
    """创建spec文件"""
    print("\n📝 创建spec文件...")
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas={datas},
    hiddenimports=[
        # GUI相关
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.dates',
        
        # 数据处理
        'pandas',
        'numpy',
        
        # 日志
        'logging.handlers',
        
        # 股票数据源
        'akshare',
        'baostock',
        
        # AI模型
        'torch',
        'transformers',
        'huggingface_hub',
        'safetensors',
        'einops',
        'tqdm',
        
        # 项目模块
        'model',
        'model.kronos',
        'model.module',
        'data_sources',
        'data_sources.base',
        'data_sources.akshare_source',
        'data_sources.baostock_source',
        'data_sources.fallback_source',
        'data_sources.manager',
    ],
    hookspath=['.'],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        'tkinter.test',
        'test',
        'tests',
        'pytest',
        'IPython',
        'jupyter',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='KronosStockPredictor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='KronosStockPredictor',
)
'''
    
    with open('main.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("  ✅ spec文件已创建: main.spec")

def build():
    """执行打包"""
    print("\n🔨 开始打包...")
    print("=" * 60)
    
    try:
        # 清理旧的build和dist目录
        import shutil
        import time
        
        if os.path.exists('build'):
            print("🗑️  清理build目录...")
            try:
                shutil.rmtree('build')
            except Exception as e:
                print(f"  ⚠️ 无法删除build目录: {e}")
                print("  💡 请手动删除build目录后重试")
                return False
        
        if os.path.exists('dist'):
            print("🗑️  清理dist目录...")
            try:
                shutil.rmtree('dist')
            except Exception as e:
                print(f"  ⚠️ 无法删除dist目录: {e}")
                print("  💡 可能程序正在运行，请关闭后重试")
                print("  💡 或者手动删除dist目录")
                return False
        
        # 执行pyinstaller
        cmd = [".venv/Scripts/pyinstaller.exe", "main.spec", "--clean"]
        print(f"📋 执行命令: {' '.join(cmd)}")
        print()
        
        result = subprocess.run(cmd)
        
        if result.returncode == 0:
            print("\n" + "=" * 60)
            print("✅ 打包成功!")
            exe_path = os.path.join('dist', 'KronosStockPredictor', 'main.exe')
            if os.path.exists(exe_path):
                print(f"📦 可执行文件位置: {exe_path}")
                file_size = os.path.getsize(exe_path) / (1024 * 1024)
                print(f"📊 文件大小: {file_size:.1f} MB")
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
    print("=" * 60)
    print("Kronos股票预测系统 - PyInstaller打包工具")
    print("=" * 60)
    
    # 1. 检查虚拟环境
    if not check_venv():
        sys.exit(1)
    
    # 2. 检查依赖
    if not check_dependencies():
        print("\n⚠️ 依赖不完整，建议先安装所有依赖后再打包")
        response = input("是否继续打包? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # 3. 收集数据文件
    datas = collect_data_files()
    
    # 4. 创建spec文件
    create_spec_file(datas)
    
    # 5. 执行打包
    success = build()
    
    if success:
        print("\n💡 提示:")
        print("  1. 首次运行可能需要下载模型文件（需要网络连接）")
        print("  2. 确保网络连接正常以获取股票数据")
        print("  3. 日志文件保存在 logs 目录")
        print("  4. 缓存文件保存在 cache 目录")
        print("  5. 预测结果保存在 outputs 目录")
        print("\n📦 打包完成！可执行文件位置:")
        exe_path = os.path.join('dist', 'KronosStockPredictor', 'KronosStockPredictor.exe')
        if os.path.exists(exe_path):
            print(f"   {os.path.abspath(exe_path)}")
            file_size = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"   文件大小: {file_size:.1f} MB")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
