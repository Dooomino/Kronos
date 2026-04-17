# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('model', 'model'), ('data_sources', 'data_sources')],
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
    hooksconfig={},
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
