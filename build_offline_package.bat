@echo off
chcp 65001 >nul
echo ========================================
echo Kronos离线部署包构建工具
echo ========================================
echo.

REM 检查虚拟环境
echo [步骤1/3] 检查虚拟环境...
if not exist .venv\Scripts\python.exe (
    echo ❌ 错误: 虚拟环境不存在
    echo 请先创建虚拟环境: python -m venv .venv
    echo 然后安装依赖: .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)
echo ✅ 虚拟环境存在
echo.

REM 检查或下载模型文件
echo [步骤2/3] 检查模型文件...
if exist models\NeoQuasar\Kronos-Tokenizer-base\config.json (
    if exist models\NeoQuasar\Kronos-base\config.json (
        echo ✅ 模型文件已存在，跳过下载
        echo    Tokenizer: models\NeoQuasar\Kronos-Tokenizer-base
        echo    Model: models\NeoQuasar\Kronos-base
    ) else (
        echo ⚠️ 模型文件不完整，开始下载...
        call :download_models
    )
) else (
    echo ⚠️ 未找到模型文件，开始下载...
    echo 注意: 模型文件较大(约1-2GB)，下载可能需要较长时间
    echo 提示: 如果网络不稳定，可以手动从HF缓存复制
    echo.
    call :download_models
)
echo.

REM 执行打包
echo [步骤3/3] 开始打包...
echo 这可能需要几分钟时间，请耐心等待...
echo.
.venv\Scripts\python.exe build_package.py
if errorlevel 1 (
    echo.
    echo ❌ 打包失败，请检查上面的错误信息
    pause
    exit /b 1
)
echo.

REM 验证打包结果
echo ========================================
echo ✅ 离线部署包构建完成!
echo ========================================
echo.
echo 📦 部署包位置: dist\KronosStockPredictor\
echo.

pause
exit /b 0

:download_models
    .venv\Scripts\python.exe download_models.py
    if errorlevel 1 (
        echo.
        echo ❌ 模型下载失败
        echo.
        echo 💡 备选方案: 从HF缓存复制模型
        echo    1. 检查缓存: %%USERPROFILE%%\.cache\huggingface\hub
        echo    2. 复制到: models\NeoQuasar\
        echo.
        pause
        exit /b 1
    )
    exit /b 0
