# -*- coding: utf-8 -*-
"""
PyInstaller hook for safetensors
确保 safetensors 库及其子模块被正确打包
"""

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# 收集 safetensors 的所有子模块
hiddenimports = collect_submodules('safetensors')

# 特别确保 torch 集成模块被包含
hiddenimports.extend([
    'safetensors.torch',
])

# 收集数据文件（如果有）
datas = collect_data_files('safetensors')
