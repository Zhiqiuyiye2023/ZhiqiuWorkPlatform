@echo off
REM 设置控制台编码为UTF-8
chcp 65001 >nul

cls
echo ========================================
echo 知秋YOLO工具 - 依赖自动安装脚本
echo ========================================
echo.

REM 检查Python是否安装
echo 1. 检查Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误：未检测到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 显示Python版本
for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo 检测到Python版本：%PYTHON_VERSION%
echo.

REM 选择是否创建虚拟环境
echo 是否在本地项目文件夹中创建虚拟环境？
echo 1. 是（推荐，隔离项目依赖）
echo 2. 否（安装到全局环境）
echo.
set /p VENV_CHOICE=请输入选项 [1-2]: 

set VENV_DIR=venv
set USE_VENV=false

if "%VENV_CHOICE%"=="1" (
    set USE_VENV=true
    echo 已选择：创建虚拟环境
    echo.
    
    REM 检查虚拟环境是否已存在
    if exist "%VENV_DIR%" (
        echo 检测到虚拟环境已存在，是否重新创建？
        echo 1. 是（删除现有虚拟环境并重新创建）
        echo 2. 否（使用现有虚拟环境）
        echo.
        set /p RESET_VENV=请输入选项 [1-2]: 
        
        if "%RESET_VENV%"=="1" (
            echo 删除现有虚拟环境...
            rmdir /s /q "%VENV_DIR%"
            if %errorlevel% neq 0 (
                echo 警告：删除虚拟环境失败
            )
        )
    )
    
    REM 创建虚拟环境
    if not exist "%VENV_DIR%" (
        echo 创建虚拟环境...
        python -m venv "%VENV_DIR%"
        if %errorlevel% neq 0 (
            echo 错误：创建虚拟环境失败
            pause
            exit /b 1
        )
        echo 虚拟环境创建成功
    )
    echo.
)

REM 激活虚拟环境或使用全局环境
set PIP_CMD=pip
set PYTHON_CMD=python

if "%USE_VENV%"=="true" (
    set PIP_CMD="%VENV_DIR%\Scripts\pip"
    set PYTHON_CMD="%VENV_DIR%\Scripts\python"
    echo 已激活虚拟环境
    echo.
)

REM 升级pip
echo 2. 升级pip...
%PYTHON_CMD% -m pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/
if %errorlevel% neq 0 (
    echo 警告：pip升级失败，将继续执行安装
)
echo.

echo 3. 跳过PyTorch相关依赖（已移除）...
echo.

REM 安装其他依赖
echo 4. 安装其他依赖...
%PIP_CMD% install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
if %errorlevel% neq 0 (
    echo 错误：其他依赖安装失败
    pause
    exit /b 1
)
echo.

REM 验证安装
echo 5. 验证安装...
echo 正在验证核心依赖...
%PYTHON_CMD% -c "import PyQt6; import cv2; import fitz; import img2pdf; from PIL import Image; import DrissionPage; print('PyQt6版本:', PyQt6.__version__ if hasattr(PyQt6, '__version__') else '已安装'); print('OpenCV版本:', cv2.__version__); print('PyMuPDF版本:', fitz.__version__); print('img2pdf已安装'); print('Pillow已安装'); print('DrissionPage已安装')"
if %errorlevel% neq 0 (
    echo 警告：部分依赖验证失败
)
echo.

REM 生成启动脚本
if "%USE_VENV%"=="true" (
    echo 6. 生成启动脚本...
    
    REM 创建启动脚本（批处理）
    echo @echo off > start_app.bat
    echo call "%VENV_DIR%\Scripts\activate" >> start_app.bat
    echo python demo.py >> start_app.bat
    echo pause >> start_app.bat
    
    REM 创建启动脚本（PowerShell）
    echo ^& "%VENV_DIR%\Scripts\Activate.ps1" > start_app.ps1
    echo python demo.py >> start_app.ps1
    
    echo 启动脚本已生成：
    echo 1. start_app.bat （命令提示符使用）
    echo 2. start_app.ps1 （PowerShell使用）
    echo.
)

REM 完成提示
echo ========================================
echo 依赖安装完成！
echo ========================================
echo 启动说明：
if "%USE_VENV%"=="true" (
    echo 1. 双击 start_app.bat 直接启动程序
    echo 2. 或手动激活虚拟环境后运行：
    echo    * 命令提示符：call %VENV_DIR%\Scripts\activate && python demo.py
    echo    * PowerShell：^& %VENV_DIR%\Scripts\Activate.ps1 && python demo.py
) else (
    echo 直接运行：python demo.py
)
echo.
echo 安装说明：
echo 1. 虚拟环境位置：%VENV_DIR%
if "%USE_VENV%"=="true" (
    echo 2. 所有依赖已安装到虚拟环境
) else (
    echo 2. 所有依赖已安装到全局环境
)
echo 3. 若需卸载，删除 %VENV_DIR% 文件夹即可（虚拟环境模式）
echo.
pause