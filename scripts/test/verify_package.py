# -*- coding: utf-8 -*-
"""
验证打包结果的完整性
"""
import os
from pathlib import Path

def verify_package():
    """验证打包结果"""
    print("=" * 60)
    print("Kronos 打包结果验证")
    print("=" * 60)
    
    base_dir = Path("../../dist/KronosStockPredictor")
    
    if not base_dir.exists():
        print("❌ 打包目录不存在")
        return False
    
    print(f"\n✅ 打包目录存在: {base_dir}")
    
    # 检查主程序
    exe_path = base_dir / "KronosStockPredictor.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"✅ 主程序存在: {exe_path.name} ({size_mb:.1f} MB)")
    else:
        print(f"❌ 主程序不存在: {exe_path}")
        return False
    
    # 检查 _internal 目录
    internal_dir = base_dir / "_internal"
    if not internal_dir.exists():
        print(f"❌ _internal 目录不存在")
        return False
    print(f"✅ _internal 目录存在")
    
    # 检查关键模块
    critical_dirs = [
        ("model", ["kronos.py", "module.py", "__init__.py"]),
        ("data_sources", ["manager.py", "akshare_source.py", "baostock_source.py"]),
        ("akshare", ["file_fold"]),
    ]
    
    all_ok = True
    for dir_name, files in critical_dirs:
        dir_path = internal_dir / dir_name
        if dir_path.exists():
            print(f"✅ {dir_name}/ 目录存在")
            
            # 检查关键文件
            for file in files:
                file_path = dir_path / file
                if file_path.exists() or (dir_path / file).is_dir():
                    print(f"   ✅ {file}")
                else:
                    print(f"   ⚠️ {file} 不存在")
        else:
            print(f"❌ {dir_name}/ 目录不存在")
            all_ok = False
    
    # 检查 akshare 数据文件
    calendar_path = internal_dir / "akshare" / "file_fold" / "calendar.json"
    if calendar_path.exists():
        print(f"✅ akshare 交易日历文件存在")
    else:
        print(f"⚠️ akshare 交易日历文件不存在")
    
    # 统计信息
    total_files = sum(1 for _ in internal_dir.rglob("*") if _.is_file())
    total_size = sum(f.stat().st_size for f in internal_dir.rglob("*") if f.is_file())
    total_size_mb = total_size / (1024 * 1024)
    
    print(f"\n📊 打包统计:")
    print(f"   文件总数: {total_files}")
    print(f"   总大小: {total_size_mb:.1f} MB")
    print(f"   主程序: {size_mb:.1f} MB")
    print(f"   依赖库: {total_size_mb:.1f} MB")
    
    if all_ok:
        print("\n" + "=" * 60)
        print("✅ 验证通过!打包完整且正确")
        print("=" * 60)
        return True
    else:
        print("\n" + "=" * 60)
        print("⚠️ 验证发现问题,请检查上述警告")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = verify_package()
    exit(0 if success else 1)
