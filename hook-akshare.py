# -*- coding: utf-8 -*-
"""
PyInstaller hook for akshare
确保 akshare 的数据文件被正确打包
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 收集 akshare 的所有数据文件
datas = collect_data_files('akshare')

# 收集 akshare 的所有子模块
hiddenimports = collect_submodules('akshare')
