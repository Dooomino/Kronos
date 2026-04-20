@echo off
chcp 65001 >nul

REM 切换到项目根目录
cd /d %~dp0\..\..

echo ========================================
echo Kronos Nuitka打包工具
echo ========================================
echo.

REM 检查虚拟环境
if not exist .venv\Scripts\python.exe (
    echo ❌ 错误: 虚拟环境不存在
    pause
    exit /b 1
)

REM 检查Nuitka
.venv\Scripts\python.exe -m nuitka --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Nuitka未安装,正在安装...
    .venv\Scripts\pip install nuitka zstandard
    if errorlevel 1 (
        echo ❌ Nuitka安装失败
        pause
        exit /b 1
    )
)

echo ✅ 环境检查通过
echo.

REM 执行打包
.venv\Scripts\python.exe scripts\build\build_with_nuitka.py
if errorlevel 1 (
    echo.
    echo ❌ 打包失败
    pause
    exit /b 1
)

echo.
pause
