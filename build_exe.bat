@echo off
REM 设置控制台编码为UTF-8
chcp 65001 >nul

cls
echo ========================================
echo 知秋YOLO工具 - EXE打包脚本
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误：未检测到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 检查pyinstaller是否安装
echo 1. 检查pyinstaller...
python -c "import sys; sys.path = list(set(sys.path)); import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在安装pyinstaller...
    python -m pip install --upgrade pyinstaller -i https://mirrors.aliyun.com/pypi/simple/
    if %errorlevel% neq 0 (
        echo 警告：安装pyinstaller失败，但可能已安装在其他位置，尝试继续...
    ) else (
        echo pyinstaller安装成功
    )
) else (
    echo pyinstaller已安装
)

REM 获取版本号
echo.
echo 2. 请输入版本号：
echo 例如：1.0.0
echo.
set /p VERSION=版本号：

REM 验证版本号格式
if "%VERSION%"=="" (
    echo 错误：版本号不能为空
    pause
    exit /b 1
)

REM 清理旧的打包文件
echo.
echo 3. 清理旧的打包文件...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "*.spec" del /q "*.spec"
echo 清理完成

REM 开始打包
echo.
echo 4. 开始打包版本 %VERSION%...
echo 这可能需要几分钟，请耐心等待...
echo.

python -m PyInstaller --name="知秋YOLO工具_v%VERSION%" ^
--onefile ^
--windowed ^
--icon=logo.ico ^
--add-data="configs;configs" ^
--add-data="automation_tool;automation_tool" ^
--add-data="interfaces;interfaces" ^
--add-data="functions;functions" ^
--add-data="gis_workflow;gis_workflow" ^
--add-data="resource;resource" ^
--hidden-import="PyQt6.sip" ^
--hidden-import="PyQt6.QtPrintSupport" ^
--hidden-import="PyQt6.QtSvg" ^
--hidden-import="PyQt6.QtXml" ^
--hidden-import="PyQt6.QtNetwork" ^
--hidden-import="DrissionPage" ^
--hidden-import="fitz" ^
--hidden-import="img2pdf" ^
--exclude-module="numpy" ^
--exclude-module="pandas" ^
--exclude-module="matplotlib" ^
--exclude-module="scipy" ^
--exclude-module="torch" ^
--exclude-module="ultralytics" ^
--clean ^
demo.py

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo 打包成功！
    echo ========================================
    echo 版本号：%VERSION%
    echo 输出目录：dist\
    echo 可执行文件：dist\知秋YOLO工具_v%VERSION%.exe
    echo.
    echo 提示：
    echo 1. 请检查dist目录下的exe文件
    echo 2. 首次运行可能会有防火墙提示，请允许访问
    echo 3. 如果运行出错，请检查是否缺少依赖文件
    echo.
) else (
    echo.
    echo ========================================
    echo 打包失败！
    echo ========================================
    echo 请检查错误信息并重试
    echo.
)

pause
