# Kronos 工具脚本集合

本目录包含Kronos股票预测系统的各种工具脚本,分为以下几类:

## 目录结构

```
scripts/
├── build/              # 打包相关脚本
│   ├── build_package.py           - PyInstaller打包脚本
│   ├── build_with_nuitka.py       - Nuitka打包脚本
│   └── download_models.py         - 模型下载脚本
├── batch/              # 批处理文件(Windows)
│   ├── build_nuitka.bat           - Nuitka打包批处理
│   ├── build_offline_package.bat  - 离线包构建批处理
│   └── export_cache.bat           - 缓存导出批处理
├── test/               # 测试和诊断工具
│   ├── test_data_sources.py       - 数据源模块测试
│   ├── diagnose_network.py        - 网络诊断工具
│   └── verify_package.py          - 打包结果验证
└── config/             # 配置文件
    └── offline_config.py          - 离线模式配置
```

## 使用方法

### 打包脚本

#### PyInstaller打包
```bash
cd scripts/build
python build_package.py
```

或使用批处理文件(推荐):
```bash
cd scripts/batch
build_offline_package.bat
```

#### Nuitka打包
```bash
cd scripts/build
python build_with_nuitka.py
```

或使用批处理文件(推荐):
```bash
cd scripts/batch
build_nuitka.bat
```

#### 下载模型
```bash
cd scripts/build
python download_models.py
```

### 测试和诊断工具

#### 数据源测试
```bash
cd scripts/test
python test_data_sources.py
```

#### 网络诊断
```bash
cd scripts/test
python diagnose_network.py
```

#### 验证打包结果
```bash
cd scripts/test
python verify_package.py
```

### 缓存管理

#### 导出缓存数据
```bash
cd scripts/batch
export_cache.bat
```

这将把 `cache/` 目录中的所有CSV文件导出到带时间戳的文件夹中,方便备份和迁移。

### 离线配置

如需在代码中使用离线模式配置:
```python
import sys
sys.path.insert(0, 'scripts/config')
import offline_config
```

## 注意事项

1. **相对路径**: 所有脚本都使用相对于项目根目录的路径 (`../../`),请确保从正确的目录运行脚本。

2. **批处理文件**: Windows批处理文件会自动切换到项目根目录,可以从任何位置运行。

3. **Python脚本**: 直接运行Python脚本时,建议先切换到对应的子目录。

4. **虚拟环境**: 所有打包脚本都需要 `.venv` 虚拟环境存在并已安装依赖。

5. **Hook文件**: PyInstaller的hook文件 (`hook-*.py`) 和 `main.spec` 保留在项目根目录,这是PyInstaller的要求。

## 迁移说明

这些脚本原本位于项目根目录,现已迁移到 `scripts/` 目录以保持项目结构清晰。所有内部路径引用已更新,功能保持不变。

如果使用版本控制系统,请注意:
- 根目录的旧文件已被删除
- 新文件位于 `scripts/` 子目录
- 可能需要更新CI/CD配置中的脚本路径
