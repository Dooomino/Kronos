# -*- coding: utf-8 -*-
"""
离线模式配置
设置所有必要的环境变量以支持完全离线运行
"""

import os
import sys

def setup_offline_mode():
    """配置离线运行环境"""
    
    # HuggingFace离线模式 - 禁止所有网络请求
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
    os.environ['HF_UPDATE_CHECK'] = '0'
    os.environ['HF_HUB_DISABLE_IMPLICIT_TOKEN'] = '1'
    
    # Torch配置
    if getattr(sys, 'frozen', False):
        # PyInstaller打包环境
        base_path = sys._MEIPASS
    else:
        # 开发环境 - 指向项目根目录
        base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
    
    # 设置Torch缓存目录到本地
    torch_cache = os.path.join(base_path, 'cache', 'torch')
    os.environ['TORCH_HOME'] = torch_cache
    os.makedirs(torch_cache, exist_ok=True)
    
    # 禁用Python警告(可选)
    # os.environ['PYTHONWARNINGS'] = 'ignore'
    
    print("✅ 离线模式已配置")
    print(f"   HF_HUB_OFFLINE: {os.environ.get('HF_HUB_OFFLINE')}")
    print(f"   TRANSFORMERS_OFFLINE: {os.environ.get('TRANSFORMERS_OFFLINE')}")
    print(f"   TORCH_HOME: {os.environ.get('TORCH_HOME')}")


# 模块导入时自动执行配置
setup_offline_mode()
