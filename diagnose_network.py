"""
网络诊断工具 - 检查AKShare和BaoStock的连接状态
"""

import sys
import time

def test_akshare_connection():
    """测试AKShare连接"""
    print("=" * 60)
    print("测试1: AKShare连接测试")
    print("=" * 60)
    
    try:
        import akshare as ak
        print("✅ akshare库已安装")
        
        # 测试简单接口
        print("\n🔄 测试 stock_info_a_code_name 接口...")
        start_time = time.time()
        
        df = ak.stock_info_a_code_name()
        elapsed = time.time() - start_time
        
        if df is not None and not df.empty:
            print(f"✅ AKShare连接正常 (耗时: {elapsed:.2f}秒)")
            print(f"   获取到 {len(df)} 只股票信息")
            return True
        else:
            print("❌ AKShare返回空数据")
            return False
            
    except ImportError:
        print("❌ akshare未安装,请运行: pip install akshare")
        return False
    except Exception as e:
        print(f"❌ AKShare连接失败: {e}")
        print("\n💡 可能原因:")
        print("   1. 网络连接问题")
        print("   2. 防火墙/代理阻止")
        print("   3. AKShare服务器暂时不可用")
        return False


def test_baostock_connection():
    """测试BaoStock连接"""
    print("\n" + "=" * 60)
    print("测试2: BaoStock连接测试")
    print("=" * 60)
    
    try:
        import baostock as bs
        print("✅ baostock库已安装")
        
        # 测试登录
        print("\n🔄 测试登录...")
        lg = bs.login()
        
        if lg.error_code != '0':
            print(f"❌ BaoStock登录失败: {lg.error_msg}")
            return False
        
        print("✅ BaoStock登录成功")
        
        # 测试查询
        print("\n🔄 测试查询股票 600580...")
        rs = bs.query_stock_basic(code="sh.600580")
        
        if rs.error_code != '0':
            print(f"❌ 查询失败: {rs.error_msg}")
            bs.logout()
            return False
        
        # 解析结果
        found = False
        while (rs.error_code == '0') and rs.next():
            row_data = rs.get_row_data()
            if len(row_data) > 1:
                print(f"✅ 查询成功: {row_data[1]} ({row_data[0]})")
                found = True
                break
        
        bs.logout()
        
        if found:
            print("✅ BaoStock连接正常")
            return True
        else:
            print("⚠️ BaoStock未返回数据")
            return False
            
    except ImportError:
        print("❌ baostock未安装,请运行: pip install baostock")
        return False
    except Exception as e:
        print(f"❌ BaoStock连接失败: {e}")
        print("\n💡 可能原因:")
        print("   1. 网络连接问题")
        print("   2. BaoStock服务器暂时不可用")
        return False


def test_valid_stock_codes():
    """测试有效股票代码"""
    print("\n" + "=" * 60)
    print("测试3: 验证常见股票代码")
    print("=" * 60)
    
    test_codes = [
        ("600580", "卧龙电驱"),
        ("000001", "平安银行"),
        ("300207", "欣旺达"),
    ]
    
    results = []
    
    for code, expected_name in test_codes:
        print(f"\n🔄 测试 {code} ({expected_name})...")
        
        # 尝试从BaoStock获取
        try:
            import baostock as bs
            lg = bs.login()
            
            if code.startswith(('6', '9')):
                full_code = f"sh.{code}"
            else:
                full_code = f"sz.{code}"
            
            rs = bs.query_stock_basic(code=full_code)
            bs.logout()
            
            if rs.error_code == '0':
                while rs.next():
                    row_data = rs.get_row_data()
                    if len(row_data) > 1:
                        actual_name = row_data[1]
                        if expected_name in actual_name or actual_name in expected_name:
                            print(f"✅ {code}: {actual_name} (匹配)")
                            results.append(True)
                        else:
                            print(f"⚠️ {code}: {actual_name} (名称不完全匹配)")
                            results.append(True)
                        break
            else:
                print(f"❌ {code}: 查询失败")
                results.append(False)
                
        except Exception as e:
            print(f"❌ {code}: {e}")
            results.append(False)
    
    success_count = sum(results)
    print(f"\n总计: {success_count}/{len(results)} 个代码验证通过")
    
    return success_count == len(results)


def check_network_settings():
    """检查网络设置"""
    print("\n" + "=" * 60)
    print("网络设置检查")
    print("=" * 60)
    
    import os
    
    # 检查代理设置
    proxies = {
        'HTTP_PROXY': os.environ.get('HTTP_PROXY'),
        'HTTPS_PROXY': os.environ.get('HTTPS_PROXY'),
        'http_proxy': os.environ.get('http_proxy'),
        'https_proxy': os.environ.get('https_proxy'),
    }
    
    active_proxies = {k: v for k, v in proxies.items() if v}
    
    if active_proxies:
        print("⚠️ 检测到代理设置:")
        for key, value in active_proxies.items():
            print(f"   {key} = {value}")
        print("\n💡 建议: 如果代理不可用,请临时禁用:")
        print("   Windows: set HTTP_PROXY=")
        print("   Windows: set HTTPS_PROXY=")
    else:
        print("✅ 未检测到代理设置")
    
    # 检查环境变量
    print("\n💡 其他建议:")
    print("   1. 检查防火墙是否阻止Python访问网络")
    print("   2. 尝试切换网络(如从WiFi切换到有线)")
    print("   3. 重启路由器")
    print("   4. 稍后再试(服务器可能临时维护)")


def main():
    """运行所有诊断"""
    print("\n🔍 开始网络诊断...\n")
    
    results = []
    
    # 运行测试
    results.append(("AKShare连接", test_akshare_connection()))
    results.append(("BaoStock连接", test_baostock_connection()))
    results.append(("股票代码验证", test_valid_stock_codes()))
    
    # 网络设置检查
    check_network_settings()
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("诊断结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 网络连接正常!")
        print("\n💡 建议:")
        print("   1. 使用有效的股票代码(如: 600580, 000001)")
        print("   2. 避免使用不存在的代码(如: 999999)")
    else:
        print(f"\n⚠️ {total - passed} 个测试失败")
        print("\n💡 解决步骤:")
        print("   1. 检查网络连接")
        print("   2. 禁用代理(如果有)")
        print("   3. 检查防火墙设置")
        print("   4. 稍后重试")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    exit(main())
