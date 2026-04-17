# -*- coding: utf-8 -*-
"""
PyInstaller hook for transformers
确保 transformers 库的所有必要组件被正确打包
"""

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# 收集 transformers 的所有子模块
hiddenimports = collect_submodules('transformers')

# 收集 transformers 的数据文件(配置文件等)
datas = collect_data_files('transformers')

# 额外添加一些可能遗漏的重要模块
hiddenimports.extend([
    'transformers.models.auto',
    'transformers.models.auto.modeling_auto',
    'transformers.models.auto.tokenization_auto',
    'transformers.models.auto.configuration_auto',
])
