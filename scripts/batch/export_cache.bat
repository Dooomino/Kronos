@echo off
chcp 65001 >nul

REM 切换到项目根目录
cd /d %~dp0\..\..

echo ========================================
echo Kronos 缓存数据导出工具
echo ========================================
echo.

REM 检查cache目录
if not exist cache (
    echo ❌ 错误: cache目录不存在
    echo 请先运行程序生成缓存数据
    pause
    exit /b 1
)

REM 统计缓存文件
set FILE_COUNT=0
for %%F in (cache\*.csv) do set /a FILE_COUNT+=1

if %FILE_COUNT% EQU 0 (
    echo ⚠️  cache目录中没有CSV缓存文件
    echo 请先运行程序获取股票数据
    pause
    exit /b 1
)

echo 📊 发现 %FILE_COUNT% 个缓存文件
echo.

REM 创建导出目录
set EXPORT_DIR=cache_export_%DATE:~0,4%%DATE:~5,2%%DATE:~8,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%
set EXPORT_DIR=%EXPORT_DIR: =0%

if exist %EXPORT_DIR% (
    rmdir /s /q %EXPORT_DIR%
)
mkdir %EXPORT_DIR%

echo 📁 导出目录: %EXPORT_DIR%
echo.

REM 复制缓存文件
echo 正在复制缓存文件...
xcopy cache\*.csv %EXPORT_DIR%\ /Y >nul

if errorlevel 1 (
    echo ❌ 导出失败
    pause
    exit /b 1
)

echo ✅ 导出成功!
echo.
echo 📦 导出位置: %CD%\%EXPORT_DIR%
echo.
echo 💡 使用方法:
echo    1. 将整个 %EXPORT_DIR% 文件夹复制到U盘或移动硬盘
echo    2. 在离线机器上,将文件夹内容复制到 KronosStockPredictor\cache\ 目录
echo    3. 运行程序时将自动使用这些缓存数据
echo.

pause
