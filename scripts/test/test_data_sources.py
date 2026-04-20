"""
测试数据源模块 - 验证所有组件是否正常
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

def test_imports():
    """测试导入"""
    print("=" * 60)
    print("测试1: 导入数据源模块")
    print("=" * 60)
    
    try:
        from data_sources import (
            DataSource,
            AKShareSource,
            BaoStockSource,
            FallbackSource,
            DataSourceManager
        )
        print("✅ 所有模块导入成功")
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_manager_creation():
    """测试管理器创建"""
    print("\n" + "=" * 60)
    print("测试2: 创建数据源管理器")
    print("=" * 60)
    
    try:
        from data_sources import DataSourceManager
        
        # 测试默认配置
        manager = DataSourceManager()
        sources = manager.get_available_sources()
        print(f"✅ 管理器创建成功")
        print(f"   可用数据源: {sources}")
        
        # 测试指定数据源
        manager2 = DataSourceManager(enabled_sources=['akshare', 'baostock'])
        sources2 = manager2.get_available_sources()
        print(f"✅ 自定义管理器创建成功")
        print(f"   可用数据源: {sources2}")
        
        return True
    except Exception as e:
        print(f"❌ 管理器创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_source_properties():
    """测试数据源属性"""
    print("\n" + "=" * 60)
    print("测试3: 检查数据源属性")
    print("=" * 60)
    
    try:
        from data_sources import AKShareSource, BaoStockSource, FallbackSource
        
        sources = [
            AKShareSource(),
            BaoStockSource(),
            FallbackSource()
        ]
        
        for source in sources:
            print(f"✅ {source.get_name()}")
            print(f"   优先级: {source.priority}")
            print(f"   可用性: {source.is_available()}")
        
        return True
    except Exception as e:
        print(f"❌ 属性检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_main_integration():
    """测试main.py集成"""
    print("\n" + "=" * 60)
    print("测试4: 检查main.py集成")
    print("=" * 60)
    
    try:
        # 尝试从main.py导入
        import main
        
        # 检查DataSourceManager是否已导入
        if hasattr(main, 'DataSourceManager'):
            print("✅ main.py已成功导入DataSourceManager")
        else:
            print("⚠️ main.py中未找到DataSourceManager")
        
        # 检查fetch_stock_data函数是否存在
        if hasattr(main, 'fetch_stock_data'):
            print("✅ fetch_stock_data函数存在")
        else:
            print("❌ fetch_stock_data函数不存在")
            return False
        
        return True
    except Exception as e:
        print(f"❌ main.py集成检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n🧪 开始测试数据源模块\n")
    
    results = []
    
    # 运行测试
    results.append(("导入测试", test_imports()))
    results.append(("管理器创建", test_manager_creation()))
    results.append(("属性检查", test_source_properties()))
    results.append(("main.py集成", test_main_integration()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过!数据源模块已就绪")
        return 0
    else:
        print(f"\n⚠️ {total - passed} 个测试失败,请检查错误信息")
        return 1


if __name__ == "__main__":
    exit(main())
