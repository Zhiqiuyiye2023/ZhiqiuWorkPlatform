# coding:utf-8
"""
用于管理项目的依赖安装、打包和安装包生成功能
"""

import sys
import os
import subprocess
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QGroupBox
from PyQt6.QtCore import Qt, QProcess, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from qfluentwidgets import (PushButton, TitleLabel, SubtitleLabel, InfoBar, InfoBarPosition,
                          FluentWindow, NavigationItemPosition, MessageBox, PrimaryPushButton)
from qfluentwidgets import FluentIcon as FIF

# 主应用窗口
class IntegrationTool(FluentWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("知秋工作平台打包工具")
        self.resize(800, 600)
        self.setMinimumSize(600, 400)
        
        # 创建主界面
        self.main_widget = QWidget()
        self.main_widget.setObjectName("ManagementTool")  # 设置对象名称
        self.main_layout = QVBoxLayout(self.main_widget)
        
        # 添加标题
        self.title_label = TitleLabel("知秋工作平台 - 集成管理工具", self.main_widget)
        self.subtitle_label = SubtitleLabel("用于管理项目的依赖安装、打包和安装包生成功能", self.main_widget)
        
        # 创建功能按钮组
        self.create_buttons()
        
        # 创建日志输出区域
        self.create_log_area()
        
        # 设置布局
        self.main_layout.addWidget(self.title_label)
        self.main_layout.addWidget(self.subtitle_label)
        self.main_layout.addSpacing(20)
        self.main_layout.addWidget(self.buttons_group)
        self.main_layout.addSpacing(20)
        self.main_layout.addWidget(self.log_group)
        
        # 添加主界面作为子界面
        self.addSubInterface(self.main_widget, FIF.SETTING, "管理工具")
        
        # 初始化QProcess
        self.process = None
        
    def create_buttons(self):
        """创建功能按钮"""
        self.buttons_group = QGroupBox("功能选项", self.main_widget)
        self.buttons_layout = QVBoxLayout(self.buttons_group)
        
        # 安装依赖按钮
        self.install_deps_btn = PrimaryPushButton("安装完整依赖", self.buttons_group)
        self.install_deps_btn.setIcon(FIF.DOWNLOAD)
        self.install_deps_btn.clicked.connect(self.install_dependencies)
        
        # 打包exe应用（无控制台）
        self.build_exe_btn = PushButton("打包EXE应用（无控制台）", self.buttons_group)
        self.build_exe_btn.setIcon(FIF.APPLICATION)
        self.build_exe_btn.clicked.connect(self.build_exe)
        
        # 打包exe应用（含控制台）
        self.build_exe_console_btn = PushButton("打包EXE应用（含控制台）", self.buttons_group)
        self.build_exe_console_btn.setIcon(FIF.COMMAND_PROMPT)
        self.build_exe_console_btn.clicked.connect(self.build_exe_console)
        
        # 使用目录模式打包应用
        self.build_dir_btn = PushButton("使用目录模式打包应用", self.buttons_group)
        self.build_dir_btn.setIcon(FIF.FOLDER_ADD)
        self.build_dir_btn.clicked.connect(self.build_dir)
        
        # 生成安装包
        self.build_installer_btn = PrimaryPushButton("生成安装包", self.buttons_group)
        self.build_installer_btn.setIcon(FIF.ZIP_FOLDER)
        self.build_installer_btn.clicked.connect(self.build_installer)
        
        # 添加按钮到布局
        self.buttons_layout.addWidget(self.install_deps_btn)
        self.buttons_layout.addWidget(self.build_exe_btn)
        self.buttons_layout.addWidget(self.build_exe_console_btn)
        self.buttons_layout.addWidget(self.build_dir_btn)
        self.buttons_layout.addWidget(self.build_installer_btn)
        
    def create_log_area(self):
        """创建日志输出区域"""
        self.log_group = QGroupBox("操作日志", self.main_widget)
        self.log_layout = QVBoxLayout(self.log_group)
        
        # 创建日志文本框
        self.log_text = QTextEdit(self.log_group)
        self.log_text.setReadOnly(True)
        self.log_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.log_text.setFont(QFont("Consolas", 10))
        
        # 清空日志按钮
        self.clear_log_btn = PushButton("清空日志", self.log_group)
        self.clear_log_btn.setIcon(FIF.DELETE)
        self.clear_log_btn.clicked.connect(self.clear_log)
        
        # 添加到布局
        self.log_layout.addWidget(self.log_text)
        self.log_layout.addWidget(self.clear_log_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
    def log(self, message):
        """记录日志"""
        self.log_text.append(message)
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())
        QApplication.processEvents()
        
    def clear_log(self):
        """清空日志"""
        self.log_text.clear()
        
    def run_command(self, command, description="执行命令"):
        """运行命令并显示输出"""
        self.log(f"\n=== {description} ===")
        self.log(f"执行命令: {command}")
        
        try:
            # 创建子进程执行命令
            process = subprocess.Popen(
                command, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                cwd=os.getcwd()
            )
            
            # 实时读取输出，处理编码问题
            while True:
                output = process.stdout.readline()
                if output == b'' and process.poll() is not None:
                    break
                if output:
                    try:
                        # 尝试使用UTF-8解码
                        output_str = output.decode('utf-8').strip()
                    except UnicodeDecodeError:
                        try:
                            # 尝试使用GBK解码
                            output_str = output.decode('gbk').strip()
                        except UnicodeDecodeError:
                            # 最后尝试使用latin-1解码
                            output_str = output.decode('latin-1').strip()
                    self.log(output_str)
                    QApplication.processEvents()
            
            # 获取返回码
            return_code = process.poll()
            if return_code == 0:
                self.log(f"=== {description} 成功 ===")
                InfoBar.success(
                    title="操作成功",
                    content=f"{description} 已成功完成",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=2000,
                    parent=self
                )
            else:
                self.log(f"=== {description} 失败 (返回码: {return_code}) ===")
                InfoBar.error(
                    title="操作失败",
                    content=f"{description} 执行失败，请查看日志",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3000,
                    parent=self
                )
                
        except Exception as e:
            self.log(f"=== {description} 出错: {str(e)} ===")
            InfoBar.error(
                title="操作出错",
                content=f"{description} 执行出错: {str(e)}",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000,
                parent=self
            )
    
    def install_dependencies(self):
        """安装完整依赖"""
        command = f"{sys.executable} -m pip install -r requirements.txt"
        self.run_command(command, "安装完整依赖")
        
    def build_exe(self):
        """打包exe应用（无控制台）"""
        command = f"{sys.executable} -m PyInstaller demo.py -F -w --icon=logo.ico -n \"知秋工作平台\" --add-data=qfluentwidgets;qfluentwidgets --add-data=configs;configs --add-data=interfaces;interfaces --add-data=functions;functions --add-data=automation_tool;automation_tool --add-data=gis_workflow;gis_workflow --add-data=news_sources.json;. --clean"
        self.run_command(command, "打包EXE应用（无控制台）")
        
    def build_exe_console(self):
        """打包exe应用（含控制台）"""
        command = f"{sys.executable} -m PyInstaller demo.py -F -c --icon=logo.ico -n \"知秋工作平台（控制台）\" --add-data=qfluentwidgets;qfluentwidgets --add-data=configs;configs --add-data=interfaces;interfaces --add-data=functions;functions --add-data=automation_tool;automation_tool --add-data=gis_workflow;gis_workflow --add-data=news_sources.json;. --clean"
        self.run_command(command, "打包EXE应用（含控制台）")
        
    def build_dir(self):
        """使用目录模式打包应用"""
        command = f"{sys.executable} -m PyInstaller demo.py -D -w --icon=logo.ico -n \"知秋工作平台\" --add-data=qfluentwidgets;qfluentwidgets --add-data=configs;configs --add-data=interfaces;interfaces --add-data=functions;functions --add-data=automation_tool;automation_tool --add-data=gis_workflow;gis_workflow --add-data=news_sources.json;. --clean --noupx"
        self.run_command(command, "使用目录模式打包应用")
        
    def build_installer(self):
        """生成安装包"""
        import requests
        
        # 先检查是否已安装Inno Setup
        inno_setup_path = "C:\\Program Files (x86)\\Inno Setup 6\\iscc.exe"
        if not os.path.exists(inno_setup_path):
            InfoBar.warning(
                title="Inno Setup 未安装",
                content="正在下载并安装 Inno Setup...",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000,
                parent=self
            )
            
            # 下载Inno Setup - 使用Python的requests库
            self.log(f"\n=== 下载Inno Setup ===")
            self.log("正在下载 Inno Setup...")
            try:
                url = "https://files.jrsoftware.org/is/6/innosetup-6.3.2.exe"
                response = requests.get(url, stream=True)
                with open("innosetup.exe", "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                self.log("=== 下载Inno Setup 成功 ===")
            except Exception as e:
                self.log(f"=== 下载Inno Setup 出错: {str(e)} ===")
                InfoBar.error(
                    title="下载失败",
                    content=f"无法下载Inno Setup: {str(e)}",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3000,
                    parent=self
                )
                return
            
            # 安装Inno Setup
            self.log(f"\n=== 安装Inno Setup ===")
            self.log("正在安装 Inno Setup...")
            try:
                # 使用subprocess直接执行安装程序
                process = subprocess.Popen(
                    [".\\innosetup.exe", "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"],
                    cwd=os.getcwd()
                )
                process.wait()
                if process.returncode == 0:
                    self.log("=== 安装Inno Setup 成功 ===")
                else:
                    self.log(f"=== 安装Inno Setup 失败 (返回码: {process.returncode}) ===")
            except Exception as e:
                self.log(f"=== 安装Inno Setup 出错: {str(e)} ===")
                InfoBar.error(
                    title="安装失败",
                    content=f"无法安装Inno Setup: {str(e)}",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3000,
                    parent=self
                )
                return
        
        # 生成安装包
        self.log(f"\n=== 生成安装包 ===")
        self.log(f"执行命令: \"{inno_setup_path}\" installer.iss")
        try:
            # 使用subprocess直接执行编译命令
            process = subprocess.Popen(
                [inno_setup_path, "installer.iss"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=os.getcwd()
            )
            
            # 实时读取输出
            while True:
                output = process.stdout.readline()
                if output == b'' and process.poll() is not None:
                    break
                if output:
                    try:
                        output_str = output.decode('utf-8').strip()
                    except UnicodeDecodeError:
                        try:
                            output_str = output.decode('gbk').strip()
                        except UnicodeDecodeError:
                            output_str = output.decode('latin-1').strip()
                    self.log(output_str)
                    QApplication.processEvents()
            
            # 获取返回码
            return_code = process.poll()
            if return_code == 0:
                self.log("=== 生成安装包 成功 ===")
                InfoBar.success(
                    title="操作成功",
                    content="生成安装包已成功完成",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=2000,
                    parent=self
                )
            else:
                self.log(f"=== 生成安装包 失败 (返回码: {return_code}) ===")
                InfoBar.error(
                    title="操作失败",
                    content="生成安装包执行失败，请查看日志",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3000,
                    parent=self
                )
        except Exception as e:
            self.log(f"=== 生成安装包 出错: {str(e)} ===")
            InfoBar.error(
                title="操作出错",
                content=f"生成安装包执行出错: {str(e)}",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000,
                parent=self
            )

# 主函数
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = IntegrationTool()
    window.show()
    sys.exit(app.exec())