# coding:utf-8
import os
import sys
import psutil
import pyqtgraph as pg
from PyQt6.QtCore import QTimer, QThread, pyqtSignal, Qt, QProcess
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QSpinBox, QLineEdit, QCheckBox, QGroupBox, QTextEdit, QPushButton, QHeaderView, QTableWidgetItem
from qfluentwidgets import (NavigationItemPosition, setTheme, Theme, MSFluentWindow,
                            qrouter, SubtitleLabel, setFont, PushButton, SystemThemeListener,
                            isDarkTheme)
from qfluentwidgets import FluentIcon as FIF

# 资源路径获取函数
def resource_path(relative_path):
    """获取资源的绝对路径，兼容开发环境和打包后环境"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller打包后的临时目录
        base_path = sys._MEIPASS    
    else:
        # 脚本当前目录
        base_path = os.path.abspath(os.path.dirname(sys.argv[0]))
    return os.path.join(base_path, relative_path)

# 输出读取线程类
class OutputReader(QThread):
    output_signal = pyqtSignal(str)

    def __init__(self, process):
        super().__init__()
        self.process = process
        self._running = True

    def run(self):
        import os
        import select
        
        # 设置为非阻塞模式
        if hasattr(self.process.stdout, 'fileno'):
            try:
                # 将stdout设置为非阻塞
                fd = self.process.stdout.fileno()
                import fcntl
                flags = fcntl.fcntl(fd, fcntl.F_GETFL)
                fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
            except Exception:
                pass
        
        while self._running and self.process and self.process.poll() is None:
            try:
                # 非阻塞读取
                line = self.process.stdout.readline()
                if line:
                    try:
                        text = line.decode('utf-8', errors='replace')
                    except Exception:
                        text = str(line)
                    self.output_signal.emit(text)
                else:
                    # 无数据时短暂休眠，减少CPU占用
                    self.msleep(100)
            except (IOError, OSError):
                # 处理非阻塞IO可能产生的异常
                self.msleep(100)
        
        # 清理资源
        self._running = False

    def stop(self):
        self._running = False

class MonitorWidget(QWidget):
    """监控面板组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("MonitorWidget")  # 设置对象名称
        
        # 服务相关变量
        self.process = None
        self.output_thread = None
        self.public_ip_obtained = False  # 标记公网地址是否已获取
        
        self.initUI()
        self.initTimers()
        
    def initUI(self):
        layout = QVBoxLayout(self)
        
        # ========== 实时监控 ==========
        self.monitor_group = QGroupBox("实时监控")
        monitor_layout = QVBoxLayout()
        
        # 数值显示
        value_layout = QHBoxLayout()
        self.cpu_label = QLabel("CPU: 0.0%")
        self.mem_label = QLabel("内存: 0.0%")
        self.req_label = QLabel("请求数: 0")
        value_layout.addWidget(self.cpu_label)
        value_layout.addWidget(self.mem_label)
        value_layout.addWidget(self.req_label)
        value_layout.addStretch()
        monitor_layout.addLayout(value_layout)
        
        # 实时曲线图
        self.plot_widget = pg.PlotWidget(title="CPU/内存/请求数 实时监控")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.addLegend()
        self.plot_widget.setMinimumHeight(200)
        self.cpu_curve = self.plot_widget.plot(name="CPU(%)")
        self.mem_curve = self.plot_widget.plot(name="内存(%)")
        self.req_curve = self.plot_widget.plot(name="请求数")
        self.cpu_data, self.mem_data, self.req_data = [], [], []
        monitor_layout.addWidget(self.plot_widget)
        
        self.monitor_group.setLayout(monitor_layout)
        layout.addWidget(self.monitor_group)
        
        # ========== 服务参数设置-服务控制-IP地址 一行显示 ==========
        row_layout = QHBoxLayout()
        row_layout.setSpacing(15)
        
        # 服务参数设置
        self.param_group = QGroupBox("服务参数设置")
        param_layout = QVBoxLayout()
        
        # 创建表单布局
        form_layout = QVBoxLayout()
        form_layout.setSpacing(10)
        
        # 端口号设置
        port_layout = QHBoxLayout()
        self.port_label = QLabel("端口号：")
        port_layout.addWidget(self.port_label)
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(5000)
        self.port_input.setFixedWidth(120)
        port_layout.addWidget(self.port_input)
        port_layout.addStretch()
        form_layout.addLayout(port_layout)
        
        # 日志级别设置
        log_layout = QHBoxLayout()
        self.log_level_label = QLabel("日志级别：")
        log_layout.addWidget(self.log_level_label)
        self.log_level = QLineEdit("INFO")
        self.log_level.setFixedWidth(120)
        log_layout.addWidget(self.log_level)
        log_layout.addStretch()
        form_layout.addLayout(log_layout)
        
        # 自动重启设置
        self.auto_restart = QCheckBox("自动重启服务")
        form_layout.addWidget(self.auto_restart)
        
        # ngrok隧道设置
        self.enable_ngrok = QCheckBox("启用ngrok公网隧道")
        # 默认勾选，修复认证问题后可直接使用
        self.enable_ngrok.setChecked(True)
        form_layout.addWidget(self.enable_ngrok)
        
        param_layout.addLayout(form_layout)
        self.param_group.setLayout(param_layout)
        row_layout.addWidget(self.param_group, 1)  # 服务参数：25%
        
        # 服务控制
        self.status_group = QGroupBox("服务控制")
        status_layout = QVBoxLayout()
        
        # 服务状态
        self.status_label = QLabel("服务状态：启动中...")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 16px; padding: 8px; border-radius: 6px; background-color: #1976d2; color: white;")
        status_layout.addWidget(self.status_label)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        self.restart_btn = PushButton("重启服务")
        self.stop_btn = PushButton("停止服务")
        self.website_btn = PushButton("进入官网")
        self.stop_btn.setEnabled(False)
        # 设置按钮宽度，使其适配板块宽度
        self.restart_btn.setMinimumWidth(100)
        self.stop_btn.setMinimumWidth(100)
        self.website_btn.setMinimumWidth(100)
        # 设置按钮水平拉伸
        self.restart_btn.setSizePolicy(self.restart_btn.sizePolicy().horizontalPolicy(), self.restart_btn.sizePolicy().verticalPolicy())
        self.stop_btn.setSizePolicy(self.stop_btn.sizePolicy().horizontalPolicy(), self.stop_btn.sizePolicy().verticalPolicy())
        self.website_btn.setSizePolicy(self.website_btn.sizePolicy().horizontalPolicy(), self.website_btn.sizePolicy().verticalPolicy())
        self.restart_btn.clicked.connect(self.restart_service)
        self.stop_btn.clicked.connect(self.stop_service)
        self.website_btn.clicked.connect(self.open_website)
        btn_layout.addWidget(self.restart_btn, 1)
        btn_layout.addWidget(self.stop_btn, 1)
        btn_layout.addWidget(self.website_btn, 1)
        status_layout.addLayout(btn_layout)
        
        self.status_group.setLayout(status_layout)
        row_layout.addWidget(self.status_group, 1)  # 服务控制：25%
        
        # IP地址和公网地址
        self.ip_group = QGroupBox("IP地址")
        ip_layout = QVBoxLayout()
        self.ip_label = QLabel("IP: 获取中...")
        self.ip_label.setStyleSheet("font-size: 18px; padding: 8px;")
        ip_layout.addWidget(self.ip_label)
        
        # 公网地址标签
        self.public_ip_label = QLabel("公网地址: 启动中...")
        self.public_ip_label.setStyleSheet("font-size: 18px; padding: 8px; color: #2e7d32;")
        ip_layout.addWidget(self.public_ip_label)
        
        self.ip_group.setLayout(ip_layout)
        row_layout.addWidget(self.ip_group, 2)  # IP地址：50%
        
        layout.addLayout(row_layout)
        
        # ========== 调试日志 ==========
        self.log_group = QGroupBox("调试日志")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(200)
        log_layout.addWidget(self.log_text)
        self.log_group.setLayout(log_layout)
        layout.addWidget(self.log_group)
        
        # 设置布局间距
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 初始化主题样式
        self.updateThemeStyle()
        
        # 自动启动服务
        self.start_service()
    
    def initTimers(self):
        # 状态检查定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.check_status)
        self.status_timer.start(2000)
        
        # 绘图定时器
        self.plot_timer = QTimer()
        self.plot_timer.timeout.connect(self.update_plot)
        self.plot_timer.start(1000)
        
        # IP更新定时器
        self.ip_timer = QTimer()
        self.ip_timer.timeout.connect(self.update_ip)
        self.ip_timer.start(5000)
        
        # 公网地址更新定时器
        self.public_ip_timer = QTimer()
        self.public_ip_timer.timeout.connect(self.update_public_ip)
        self.public_ip_timer.start(2000)
        
        # 启动时先刷新一次IP
        self.update_ip()
    
    def set_status_color(self, status):
        # 根据状态设置不同背景色
        if "运行中" in status:
            color = "#2e7d32"  # 绿色
        elif "启动中" in status:
            color = "#1976d2"  # 蓝色
        elif "已停止" in status or "未启动" in status or "已退出" in status:
            color = "#b71c1c"  # 红色
        else:
            color = "#444"
        self.status_label.setStyleSheet(
            f"background-color: {color}; color: #fff; font-weight: bold; font-size: 18px; padding: 10px 0 10px 0; border-radius: 8px;"
        )
    
    def start_service(self):
        if self.process is None:
            try:
                # 清理旧的ngrok地址文件
                import os
                if os.path.exists('ngrok_url.txt'):
                    os.remove('ngrok_url.txt')
                
                # 启动主服务
                import subprocess
                port = str(self.port_input.value())
                log_level = self.log_level.text()
                
                # 使用python.exe但隐藏控制台窗口
                creationflags = 0
                if hasattr(subprocess, 'CREATE_NO_WINDOW'):
                    creationflags |= subprocess.CREATE_NO_WINDOW
                
                # 设置环境变量，根据用户选择启用或禁用ngrok隧道
                env = os.environ.copy()
                env['ENABLE_NGROK'] = 'true' if self.enable_ngrok.isChecked() else 'false'
                
                self.process = subprocess.Popen(
                    [sys.executable, "Server.py"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    creationflags=creationflags,
                    env=env
                )
                
                self.status_label.setText("服务状态：启动中...")
                self.set_status_color("启动中")
                if hasattr(self, 'restart_btn'):
                    self.restart_btn.setEnabled(False)
                self.stop_btn.setEnabled(True)
                self.log_text.append(">>> 服务启动...\n")
                
                # 更新公网地址显示
                self.public_ip_label.setText("公网地址: 启动中...")
                
                # 启动输出读取线程
                self.output_thread = OutputReader(self.process)
                self.output_thread.output_signal.connect(self.append_log)
                self.output_thread.start()
            except Exception as e:
                self.log_text.append(f">>> 启动服务失败：{e}\n")
                self.public_ip_label.setText("公网地址: 启动失败")
    
    def restart_service(self):
        """重启服务"""
        # 先停止服务
        if self.process is not None:
            self.stop_service()
        
        # 延迟启动服务
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(2000, self.start_service)
    
    def stop_service(self):
        # 停止主服务
        if self.process is not None:
            # 标记为正在停止，避免重复点击
            self.stop_btn.setEnabled(False)
            if hasattr(self, 'restart_btn'):
                self.restart_btn.setEnabled(False)
            self.status_label.setText("服务状态：停止中...")
            self.set_status_color("启动中")
            
            # 停止输出线程
            if self.output_thread:
                self.output_thread.stop()
                # 不使用wait()阻塞主线程，让线程自行结束
                self.output_thread = None
            
            # 终止进程，但不等待，避免阻塞UI
            try:
                self.process.terminate()
                # 使用QTimer延迟清理，让进程有时间终止
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(1000, self._cleanup_after_stop)
            except Exception as e:
                self.log_text.append(f">>> 停止服务失败：{e}\n")
                self._cleanup_after_stop()
    
    def _cleanup_after_stop(self):
        """停止服务后的清理工作"""
        # 清理进程资源
        if self.process:
            try:
                # 尝试获取返回码，不阻塞
                self.process.poll()
            except Exception:
                pass
            self.process = None
        
        # 清理ngrok地址文件
        import os
        if os.path.exists('ngrok_url.txt'):
            try:
                os.remove('ngrok_url.txt')
            except Exception as e:
                self.log_text.append(f">>> 清理ngrok地址文件失败：{e}\n")
        
        # 更新UI状态
        self.status_label.setText("服务状态：已停止")
        self.set_status_color("已停止")
        if hasattr(self, 'restart_btn'):
            self.restart_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.log_text.append(">>> 服务已停止\n")
        
        # 更新公网地址显示
        self.public_ip_label.setText("公网地址: 已停止")
    
    def check_status(self):
        if self.process is not None:
            if self.process.poll() is None:
                # 只有当公网地址已获取时，才显示服务状态为运行中
                if hasattr(self, 'public_ip_obtained') and self.public_ip_obtained:
                    self.status_label.setText("服务状态：运行中")
                    self.set_status_color("运行中")
                    if hasattr(self, 'restart_btn'):
                        self.restart_btn.setEnabled(False)
                    self.stop_btn.setEnabled(True)
                else:
                    # 公网地址未获取到，保持启动中状态
                    self.status_label.setText("服务状态：启动中...")
                    self.set_status_color("启动中")
                    if hasattr(self, 'restart_btn'):
                        self.restart_btn.setEnabled(False)
                    self.stop_btn.setEnabled(False)
            else:
                self.status_label.setText("服务状态：已退出")
                self.set_status_color("已退出")
                self.process = None
                if hasattr(self, 'restart_btn'):
                    self.restart_btn.setEnabled(True)
                self.stop_btn.setEnabled(False)
                self.log_text.append(">>> 服务已退出\n")
                
                if self.output_thread:
                    self.output_thread.stop()
                    self.output_thread.wait()
                    self.output_thread = None
        else:
            self.status_label.setText("服务状态：未启动")
            self.set_status_color("未启动")
            if hasattr(self, 'restart_btn'):
                self.restart_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
    
    def append_log(self, text):
        # 处理终端控制字符，如颜色码
        import re
        # 移除ANSI颜色代码
        text = re.sub(r'\x1b\[[0-9;]*m', '', text)
        # 替换中文乱码（如果有）
        text = text.encode('utf-8', 'ignore').decode('utf-8', 'ignore')
        # 确保文本末尾有换行符
        if not text.endswith('\n'):
            text += '\n'
        self.log_text.append(text)
    
    def update_plot(self):
        # 采集系统CPU/内存/请求数
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        req = 0  # 假设请求数为0（可扩展为定时请求 /get_online_users）
        
        # 更新数据
        self.cpu_data.append(cpu)
        self.mem_data.append(mem)
        self.req_data.append(req)
        
        # 只保留最近60个点
        if len(self.cpu_data) > 60:
            self.cpu_data = self.cpu_data[-60:]
            self.mem_data = self.mem_data[-60:]
            self.req_data = self.req_data[-60:]
        
        # 更新曲线
        x = list(range(len(self.cpu_data)))
        self.cpu_curve.setData(x, self.cpu_data)
        self.mem_curve.setData(x, self.mem_data)
        self.req_curve.setData(x, self.req_data)
        
        # 实时更新数值显示
        self.cpu_label.setText(f"CPU: {cpu:.1f}%")
        self.mem_label.setText(f"内存: {mem:.1f}%")
        self.req_label.setText(f"请求数: {req}")
    
    def updateThemeStyle(self):
        """根据当前主题更新样式"""
        is_dark = isDarkTheme()
        
        # 设置标签文字颜色
        label_style = "color: #d8dee9;" if is_dark else "color: black;"
        group_box_style = "QGroupBox { color: #d8dee9; font-weight: bold; }" if is_dark else "QGroupBox { color: black; font-weight: bold; }"
        
        # 设置数值标签样式
        if is_dark:
            self.cpu_label.setStyleSheet("font-weight: bold; font-size: 15px; color: #81a1c1;")
            self.mem_label.setStyleSheet("font-weight: bold; font-size: 15px; color: #b48ead;")
            self.req_label.setStyleSheet("font-weight: bold; font-size: 15px; color: #ebcb8b;")
        else:
            self.cpu_label.setStyleSheet("font-weight: bold; font-size: 15px; color: #5e81ac;")
            self.mem_label.setStyleSheet("font-weight: bold; font-size: 15px; color: #a3be8c;")
            self.req_label.setStyleSheet("font-weight: bold; font-size: 15px; color: #d08770;")
        
        # 设置板块标签样式
        self.port_label.setStyleSheet(label_style)
        self.log_level_label.setStyleSheet(label_style)
        self.auto_restart.setStyleSheet(label_style)
        self.enable_ngrok.setStyleSheet(label_style)
        
        # 设置输入控件样式
        if is_dark:
            # 深色主题样式
            self.port_input.setStyleSheet("""
                QSpinBox {
                    background-color: #3b4252;
                    color: #d8dee9;
                    border: 1px solid #4c566a;
                    border-radius: 4px;
                    padding: 2px 8px;
                }
                QSpinBox:hover {
                    border-color: #5e81ac;
                }
                QSpinBox::up-button, QSpinBox::down-button {
                    background-color: #4c566a;
                    color: #d8dee9;
                    border: none;
                }
                QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                    background-color: #5e81ac;
                }
            """)
            
            self.log_level.setStyleSheet("""
                QLineEdit {
                    background-color: #3b4252;
                    color: #d8dee9;
                    border: 1px solid #4c566a;
                    border-radius: 4px;
                    padding: 2px 8px;
                }
                QLineEdit:hover {
                    border-color: #5e81ac;
                }
                QLineEdit:focus {
                    border-color: #81a1c1;
                    outline: none;
                }
            """)
        else:
            # 浅色主题样式
            self.port_input.setStyleSheet("""
                QSpinBox {
                    background-color: white;
                    color: black;
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                    padding: 2px 8px;
                }
                QSpinBox:hover {
                    border-color: #5e81ac;
                }
                QSpinBox::up-button, QSpinBox::down-button {
                    background-color: #f0f0f0;
                    color: black;
                    border: none;
                }
                QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                    background-color: #e0e0e0;
                }
            """)
            
            self.log_level.setStyleSheet("""
                QLineEdit {
                    background-color: white;
                    color: black;
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                    padding: 2px 8px;
                }
                QLineEdit:hover {
                    border-color: #5e81ac;
                }
                QLineEdit:focus {
                    border-color: #5e81ac;
                    outline: none;
                }
            """)
        
        # 设置分组框样式
        self.monitor_group.setStyleSheet(group_box_style)
        self.param_group.setStyleSheet(group_box_style)
        self.status_group.setStyleSheet(group_box_style)
        self.ip_group.setStyleSheet(group_box_style)
        self.log_group.setStyleSheet(group_box_style)
        
        # 设置图表样式
        if is_dark:
            self.plot_widget.setBackground('#2e3440')
            self.cpu_curve.setPen(pg.mkPen('#81a1c1', width=2))
            self.mem_curve.setPen(pg.mkPen('#b48ead', width=2))
            self.req_curve.setPen(pg.mkPen('#ebcb8b', width=2, style=Qt.PenStyle.DashLine))
        else:
            self.plot_widget.setBackground('#f0f0f0')
            self.cpu_curve.setPen(pg.mkPen('#5e81ac', width=2))
            self.mem_curve.setPen(pg.mkPen('#a3be8c', width=2))
            self.req_curve.setPen(pg.mkPen('#d08770', width=2, style=Qt.PenStyle.DashLine))
        
        # 设置调试日志样式
        if is_dark:
            self.log_text.setStyleSheet("background-color: #2e3440; color: #d8dee9; border: 1px solid #4c566a;")
        else:
            self.log_text.setStyleSheet("background-color: white; color: black; border: 1px solid #e0e0e0;")
        
        # 设置IP和公网地址标签样式
        self.ip_label.setStyleSheet(f"font-size: 18px; padding: 8px; {label_style}")
        self.public_ip_label.setStyleSheet(f"font-size: 18px; padding: 8px; color: #2e7d32; {label_style}")
    
    def update_ip(self):
        """获取并显示本机IP地址"""
        import socket
        ip = "未知"
        try:
            # 获取本机局域网IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0)
            try:
                # 连接到外部地址但不发送数据
                s.connect(('8.8.8.8', 80))
                ip = s.getsockname()[0]
            except Exception:
                ip = socket.gethostbyname(socket.gethostname())
            finally:
                s.close()
        except Exception:
            pass
        self.ip_label.setText(f"IP: {ip}")
    
    def update_public_ip(self):
        """从文件中读取并显示公网地址"""
        import os
        if os.path.exists('ngrok_url.txt'):
            try:
                with open('ngrok_url.txt', 'r') as f:
                    public_url = f.read().strip()
                self.public_ip_label.setText(f"公网地址: {public_url}")
                # 标记公网地址已获取
                self.public_ip_obtained = True
                # 当获取到公网地址后，更新服务状态为运行中
                if self.process is not None and self.process.poll() is None:
                    self.status_label.setText("服务状态：运行中")
                    self.set_status_color("运行中")
                    if hasattr(self, 'restart_btn'):
                        self.restart_btn.setEnabled(False)
                    self.stop_btn.setEnabled(True)
            except Exception as e:
                self.public_ip_label.setText(f"公网地址: 读取失败")
                self.public_ip_obtained = False
        else:
            if self.process is not None and self.process.poll() is None:
                # 如果服务正在运行但没有公网地址文件，可能是ngrok启动失败
                self.public_ip_label.setText("公网地址: 未获取到")
                self.public_ip_obtained = False
            else:
                # 服务未运行
                self.public_ip_label.setText("公网地址: 未启用")
                self.public_ip_obtained = False
    
    def open_website(self):
        """打开浏览器进入官网（公网地址）"""
        import webbrowser
        import re
        try:
            # 从公网地址标签中提取URL
            public_url_text = self.public_ip_label.text()
            if "公网地址: " in public_url_text:
                # 提取URL，处理可能包含的反引号
                public_url = public_url_text.replace("公网地址: ", "").strip()
                
                # 移除可能的反引号
                public_url = public_url.replace('`', '')
                
                # 检查是否是有效的URL
                if public_url.startswith(('http://', 'https://')):
                    webbrowser.open(public_url)
                    self.log_text.append(f">>> 正在打开官网：{public_url}\n")
                else:
                    self.log_text.append(">>> 公网地址无效，请先启动服务获取有效的公网地址\n")
            else:
                self.log_text.append(">>> 未获取到公网地址，请先启动服务\n")
        except Exception as e:
            self.log_text.append(f">>> 打开官网失败：{e}\n")

class ManagementToolWidget(QWidget):
    """管理工具界面"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ManagementToolWidget")  # 设置对象名称
        self.initUI()
        
    def initUI(self):
        # 创建主布局
        layout = QVBoxLayout(self)
        
        # 创建日志输出区域
        self.log_group = QGroupBox("操作日志")
        log_layout = QVBoxLayout(self.log_group)
        
        # 创建日志文本框
        self.log_text = QTextEdit(self.log_group)
        self.log_text.setReadOnly(True)
        self.log_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.log_text.setFont(QFont("Consolas", 10))
        
        # 清空日志按钮
        self.clear_log_btn = PushButton("清空日志", self.log_group)
        self.clear_log_btn.setIcon(FIF.DELETE)
        self.clear_log_btn.clicked.connect(self.clear_log)
        
        # 添加到日志布局
        log_layout.addWidget(self.log_text)
        log_layout.addWidget(self.clear_log_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        # 创建功能按钮组
        self.buttons_group = QGroupBox("功能选项")
        buttons_layout = QVBoxLayout(self.buttons_group)
        buttons_layout.setSpacing(10)
        
        # 创建第一行按钮布局（依赖安装）
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(10)
        
        # 安装依赖按钮
        self.install_deps_btn = PushButton("安装完整依赖", self.buttons_group)
        self.install_deps_btn.setIcon(FIF.DOWNLOAD)
        self.install_deps_btn.clicked.connect(self.install_dependencies)
        row1_layout.addWidget(self.install_deps_btn)
        row1_layout.addStretch()
        buttons_layout.addLayout(row1_layout)
        
        # 创建第二行按钮布局（打包EXE应用）
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(10)
        
        # 打包exe应用（无控制台）
        self.build_exe_btn = PushButton("打包EXE应用（无控制台）", self.buttons_group)
        self.build_exe_btn.setIcon(FIF.APPLICATION)
        self.build_exe_btn.clicked.connect(self.build_exe)
        row2_layout.addWidget(self.build_exe_btn)
        
        # 打包exe应用（含控制台）
        self.build_exe_console_btn = PushButton("打包EXE应用（含控制台）", self.buttons_group)
        self.build_exe_console_btn.setIcon(FIF.COMMAND_PROMPT)
        self.build_exe_console_btn.clicked.connect(self.build_exe_console)
        row2_layout.addWidget(self.build_exe_console_btn)
        row2_layout.addStretch()
        buttons_layout.addLayout(row2_layout)
        
        # 创建第三行按钮布局（目录模式打包）
        row3_layout = QHBoxLayout()
        row3_layout.setSpacing(10)
        
        # 使用目录模式打包应用
        self.build_dir_btn = PushButton("使用目录模式打包应用", self.buttons_group)
        self.build_dir_btn.setIcon(FIF.FOLDER_ADD)
        self.build_dir_btn.clicked.connect(self.build_dir)
        row3_layout.addWidget(self.build_dir_btn)
        row3_layout.addStretch()
        buttons_layout.addLayout(row3_layout)
        
        # 创建第四行按钮布局（生成安装包）
        row4_layout = QHBoxLayout()
        row4_layout.setSpacing(10)
        
        # 生成安装包
        self.build_installer_btn = PushButton("生成安装包", self.buttons_group)
        self.build_installer_btn.setIcon(FIF.ZIP_FOLDER)
        self.build_installer_btn.clicked.connect(self.build_installer)
        row4_layout.addWidget(self.build_installer_btn)
        row4_layout.addStretch()
        buttons_layout.addLayout(row4_layout)
        
        # 创建第五行按钮布局（目录模式打包并生成安装包）
        row5_layout = QHBoxLayout()
        row5_layout.setSpacing(10)
        
        # 目录模式打包并生成安装包
        self.build_dir_and_installer_btn = PushButton("目录模式打包并生成安装包", self.buttons_group)
        self.build_dir_and_installer_btn.setIcon(FIF.ZIP_FOLDER)
        self.build_dir_and_installer_btn.clicked.connect(self.build_dir_and_installer)
        row5_layout.addWidget(self.build_dir_and_installer_btn)
        
        # 目录模式打包（含控制台）并生成安装包
        self.build_dir_console_and_installer_btn = PushButton("目录模式打包（含控制台）并生成安装包", self.buttons_group)
        self.build_dir_console_and_installer_btn.setIcon(FIF.ZIP_FOLDER)
        self.build_dir_console_and_installer_btn.clicked.connect(self.build_dir_console_and_installer)
        row5_layout.addWidget(self.build_dir_console_and_installer_btn)
        row5_layout.addStretch()
        buttons_layout.addLayout(row5_layout)
        
        # 创建第六行按钮布局（版本号修改）
        row6_layout = QHBoxLayout()
        row6_layout.setSpacing(10)
        
        # 版本号输入框
        self.version_input_label = QLabel("版本号:")
        row6_layout.addWidget(self.version_input_label)
        from qfluentwidgets import LineEdit
        self.version_input = LineEdit(self.buttons_group)
        self.version_input.setPlaceholderText("例如: 1.0.5.0128")
        self.version_input.setText(self.get_version())
        self.version_input.setFixedWidth(200)
        row6_layout.addWidget(self.version_input)
        
        # 修改版本号按钮
        self.update_version_btn = PushButton("修改版本号", self.buttons_group)
        self.update_version_btn.setIcon(FIF.EDIT)
        self.update_version_btn.clicked.connect(self.update_version)
        row6_layout.addWidget(self.update_version_btn)
        row6_layout.addStretch()
        buttons_layout.addLayout(row6_layout)
        
        # 添加组件到主布局
        layout.addWidget(self.buttons_group)
        layout.addWidget(self.log_group)
        
        # 设置布局间距
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 初始化主题样式
        self.updateThemeStyle()
    
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
            import subprocess
            import sys
            import os
            
            # 修复路径包含空格的问题：在Windows上，对包含空格的路径使用引号包裹
            if isinstance(command, str):
                # 特殊处理PyInstaller命令，确保带空格的Python路径被正确处理
                # 在Windows上，直接在命令字符串中给Python路径添加引号
                python_path = sys.executable
                if ' ' in python_path and not python_path.startswith('"'):
                    python_path = f'"{python_path}"'
                
                # 替换命令中的sys.executable为带引号的版本
                command = command.replace(sys.executable, python_path)
                
                # 使用shell=True执行命令，让Windows命令行处理路径和参数
                process = subprocess.Popen(
                    command, 
                    shell=True, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT,
                    cwd=os.getcwd()
                )
            else:
                # 如果已经是列表形式，直接执行
                process = subprocess.Popen(
                    command, 
                    shell=False, 
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
            else:
                self.log(f"=== {description} 失败 (返回码: {return_code}) ===")
                
        except Exception as e:
            self.log(f"=== {description} 出错: {str(e)} ===")
    
    def install_dependencies(self):
        """安装完整依赖"""
        import sys
        command = f"{sys.executable} -m pip install -r requirements.txt"
        self.run_command(command, "安装完整依赖")
        
    def get_version(self):
        """从version.json文件中获取版本号"""
        import json
        import os
        try:
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'version.json'), 'r', encoding='utf-8') as f:
                version_info = json.load(f)
            return version_info['version']
        except Exception as e:
            self.log(f"读取版本号失败: {str(e)}")
            return "1.0.0"
    
    def build_exe(self):
        """打包exe应用（无控制台）"""
        import sys
        version = self.get_version()
        command = f"{sys.executable} -m PyInstaller demo.py -F -w --icon=logo.ico -n \"知秋工作平台v{version}\" --add-data=qfluentwidgets;qfluentwidgets --add-data=configs;configs --add-data=interfaces;interfaces --add-data=functions;functions --add-data=automation_tool;automation_tool --add-data=gis_workflow;gis_workflow --add-data=version.json;. --clean"
        self.run_command(command, "打包EXE应用（无控制台）")
        
    def build_exe_console(self):
        """打包exe应用（含控制台）"""
        import sys
        version = self.get_version()
        command = f"{sys.executable} -m PyInstaller demo.py -F -c --icon=logo.ico -n \"知秋工作平台v{version}（控制台）\" --add-data=qfluentwidgets;qfluentwidgets --add-data=configs;configs --add-data=interfaces;interfaces --add-data=functions;functions --add-data=automation_tool;automation_tool --add-data=gis_workflow;gis_workflow --add-data=version.json;. --clean"
        self.run_command(command, "打包EXE应用（含控制台）")
        
    def build_dir(self):
        """使用目录模式打包应用"""
        import sys
        version = self.get_version()
        command = f"{sys.executable} -m PyInstaller demo.py -D -w --icon=logo.ico -n \"知秋工作平台v{version}\" --add-data=qfluentwidgets;qfluentwidgets --add-data=configs;configs --add-data=interfaces;interfaces --add-data=functions;functions --add-data=automation_tool;automation_tool --add-data=gis_workflow;gis_workflow --add-data=version.json;. --clean --noupx"
        self.run_command(command, "使用目录模式打包应用")
        
    def update_installer_script(self):
        """更新安装脚本中的版本号和目录名称"""
        import os
        import re
        version = self.get_version()
        installer_path = "installer.iss"
        
        self.log(f"\n=== 更新安装脚本 ===")
        self.log(f"当前版本号: {version}")
        
        try:
            # 读取安装脚本内容
            with open(installer_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 更新AppVersion
            content = re.sub(r'AppVersion=.*', f'AppVersion={version}', content)
            
            # 更新OutputBaseFilename，添加版本号
            content = re.sub(r'OutputBaseFilename=.*', f'OutputBaseFilename=知秋工作安装包v{version}', content)
            
            # 更新源文件路径
            # 先删除旧的源文件路径行
            content = re.sub(r'Source: "dist\\知秋工作平台v.*?\*";.*?\n', '', content)
            # 添加新的源文件路径行
            files_section = "[Files]"
            if files_section in content:
                # 找到[Files]部分的位置
                files_pos = content.find(files_section) + len(files_section) + 1
                # 在[Files]部分的开头添加新的源文件路径行
                new_source_line = f'Source: "dist\\知秋工作平台v{version}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs\n'
                content = content[:files_pos] + new_source_line + content[files_pos:]
            
            # 直接替换固定的旧版本号为当前版本号
            content = content.replace('知秋工作平台v1.1.0.exe', f'知秋工作平台v{version}.exe')
            content = content.replace('知秋工作平台v1.0.4.exe', f'知秋工作平台v{version}.exe')
            
            # 写入更新后的内容
            with open(installer_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.log(f"=== 更新安装脚本 成功 ===")
            return True
        except Exception as e:
            self.log(f"=== 更新安装脚本 出错: {str(e)} ===")
            return False
        
    def build_installer(self):
        """生成安装包"""
        import os
        import subprocess
        
        # 更新安装脚本
        if not self.update_installer_script():
            return
        
        # 生成安装包
        self.log(f"\n=== 生成安装包 ===")
        inno_setup_path = "C:\\Program Files (x86)\\Inno Setup 6\\iscc.exe"
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
            else:
                self.log(f"=== 生成安装包 失败 (返回码: {return_code}) ===")
        except Exception as e:
            self.log(f"=== 生成安装包 出错: {str(e)} ===")

    def build_dir_and_installer(self):
        """目录模式打包并生成安装包"""
        # 先执行目录模式打包
        self.build_dir()
        
        # 然后生成安装包
        self.build_installer()
    
    def build_dir_console_and_installer(self):
        """目录模式打包（含控制台）并生成安装包"""
        # 先执行目录模式打包（含控制台）
        import sys
        version = self.get_version()
        command = f"{sys.executable} -m PyInstaller demo.py -D -c --icon=logo.ico -n \"知秋工作平台v{version}\" --add-data=qfluentwidgets;qfluentwidgets --add-data=configs;configs --add-data=interfaces;interfaces --add-data=functions;functions --add-data=automation_tool;automation_tool --add-data=gis_workflow;gis_workflow --add-data=version.json;. --clean --noupx"
        self.run_command(command, "使用目录模式打包应用（含控制台）")
        
        # 然后生成安装包
        self.build_installer()
    
    def update_version(self):
        """修改版本号"""
        new_version = self.version_input.text().strip()
        if not new_version:
            self.log("=== 版本号不能为空 ===")
            return
        
        self.log(f"\n=== 修改版本号为: {new_version} ===")
        
        # 更新version.json文件
        try:
            import json
            import os
            import datetime
            
            version_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'version.json')
            with open(version_file, 'r', encoding='utf-8') as f:
                version_info = json.load(f)
            
            version_info['version'] = new_version
            version_info['update_time'] = datetime.datetime.now().isoformat()
            version_info['build_time'] = datetime.datetime.now().isoformat()
            
            with open(version_file, 'w', encoding='utf-8') as f:
                json.dump(version_info, f, indent=4, ensure_ascii=False)
            
            self.log("=== 更新version.json 成功 ===")
        except Exception as e:
            self.log(f"=== 更新version.json 出错: {str(e)} ===")
            return
        
        # 更新installer.iss文件
        try:
            import os
            import re
            
            installer_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'installer.iss')
            with open(installer_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 更新AppVersion
            content = re.sub(r'AppVersion=.*', f'AppVersion={new_version}', content)
            
            # 更新OutputBaseFilename
            content = re.sub(r'OutputBaseFilename=.*', f'OutputBaseFilename=知秋工作安装包v{new_version}', content)
            
            # 更新源文件路径
            content = re.sub(r'Source: "dist\\知秋工作平台v.*?\\*";.*?\\n', '', content)
            files_section = "[Files]"
            if files_section in content:
                files_pos = content.find(files_section) + len(files_section) + 1
                new_source_line = f'Source: "dist\\知秋工作平台v{new_version}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs\n'
                content = content[:files_pos] + new_source_line + content[files_pos:]
            
            # 更新快捷方式和运行命令中的版本号
            content = re.sub(r'知秋工作平台v.*?\.exe', f'知秋工作平台v{new_version}.exe', content)
            
            with open(installer_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.log("=== 更新installer.iss 成功 ===")
            self.log("=== 版本号修改完成 ===")
        except Exception as e:
            self.log(f"=== 更新installer.iss 出错: {str(e)} ===")
            return
    
    def updateThemeStyle(self):
        """根据当前主题更新样式"""
        is_dark = isDarkTheme()
        
        # 设置标签文字颜色
        label_style = "color: #d8dee9;" if is_dark else "color: black;"
        group_box_style = "QGroupBox { color: #d8dee9; font-weight: bold; }" if is_dark else "QGroupBox { color: black; font-weight: bold; }"
        
        # 设置面板标签样式
        self.buttons_group.setStyleSheet(group_box_style)
        self.log_group.setStyleSheet(group_box_style)
        
        # 设置版本号输入框标签样式
        if hasattr(self, 'version_input_label'):
            self.version_input_label.setStyleSheet(label_style)
        
        # 设置日志文本框样式
        if is_dark:
            self.log_text.setStyleSheet("background-color: #2e3440; color: #d8dee9; border: 1px solid #4c566a;")
        else:
            self.log_text.setStyleSheet("background-color: white; color: black; border: 1px solid #e0e0e0;")

class ClientMonitorWidget(QWidget):
    """客户端监控界面"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ClientMonitorWidget")
        self.initUI()
        self.initTimers()
        
        # 客户端记录存储
        self.client_records = []
        
        # 初始化时刷新客户端列表
        self.refresh_clients()
        
    def initUI(self):
        layout = QVBoxLayout(self)
        
        # ========== 客户端监控 ==========
        self.monitor_group = QGroupBox("客户端监控")
        monitor_layout = QVBoxLayout()
        
        # 统计信息
        stat_layout = QHBoxLayout()
        self.total_label = QLabel("总客户端: 0")
        self.online_label = QLabel("在线: 0")
        self.offline_label = QLabel("离线: 0")
        stat_layout.addWidget(self.total_label)
        stat_layout.addWidget(self.online_label)
        stat_layout.addWidget(self.offline_label)
        stat_layout.addStretch()
        monitor_layout.addLayout(stat_layout)
        
        # 客户端列表
        from qfluentwidgets import TableWidget
        self.client_table = TableWidget()
        self.client_table.setBorderVisible(True)
        self.client_table.setColumnCount(9)
        self.client_table.setHorizontalHeaderLabels(["ID", "客户端IP", "计算机名", "在线状态", "物理地址", "初次连接时间", "最近连接时间", "连接次数", "消息读取状态"])
        # 隐藏垂直表头（解决状态列前面的空白列问题）
        self.client_table.verticalHeader().setVisible(False)
        # 设置表格宽度适配窗口
        self.client_table.setSizePolicy(self.client_table.sizePolicy().horizontalPolicy(), self.client_table.sizePolicy().verticalPolicy())
        
        # 设置列的宽度
        # ID列（索引0）- 固定宽度
        self.client_table.setColumnWidth(0, 60)
        self.client_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        
        # 客户端IP列（索引1）- 拉伸
        self.client_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        # 计算机名列（索引2）- 拉伸
        self.client_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        
        # 在线状态列（索引3）- 固定宽度
        self.client_table.setColumnWidth(3, 80)
        self.client_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        
        # 物理地址列（索引4）- 拉伸
        self.client_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        
        # 初次连接时间列（索引5）- 拉伸
        self.client_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        
        # 最近连接时间列（索引6）- 拉伸
        self.client_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        
        # 连接次数列（索引7）- 固定宽度
        self.client_table.setColumnWidth(7, 80)
        self.client_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        
        # 消息读取状态列（索引8）- 拉伸
        self.client_table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.Stretch)
        
        self.client_table.setAlternatingRowColors(True)
        self.client_table.setMinimumHeight(400)
        monitor_layout.addWidget(self.client_table)
        
        # 操作按钮
        action_layout = QHBoxLayout()
        self.refresh_btn = PushButton("刷新列表")
        self.delete_btn = PushButton("删除选中")
        self.clear_btn = PushButton("清空记录")
        self.select_all_btn = PushButton("全选")
        self.send_message_btn = PushButton("发送消息")
        self.send_message_btn.setIcon(FIF.SEND)
        action_layout.addWidget(self.select_all_btn)
        action_layout.addWidget(self.refresh_btn)
        action_layout.addWidget(self.delete_btn)
        action_layout.addWidget(self.clear_btn)
        action_layout.addWidget(self.send_message_btn)
        action_layout.addStretch()
        monitor_layout.addLayout(action_layout)
        
        self.monitor_group.setLayout(monitor_layout)
        layout.addWidget(self.monitor_group)
        
        # 设置布局间距
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 初始化主题样式
        self.updateThemeStyle()
        
        # 连接信号
        self.refresh_btn.clicked.connect(self.refresh_clients)
        self.delete_btn.clicked.connect(self.delete_selected)
        self.clear_btn.clicked.connect(self.clear_all)
        self.select_all_btn.clicked.connect(self.select_all_clients)
        self.send_message_btn.clicked.connect(self.openMessageDialog)
        
        # 消息内容缓存
        self.message_title_cache = ""
        self.message_content_cache = ""
    
    def initTimers(self):
        # 刷新定时器
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_clients)
        self.refresh_timer.start(5000)  # 每5秒刷新一次
    
    def load_client_records(self):
        """从文件加载客户端记录"""
        import json
        import os
        records_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'client_records.json')
        
        try:
            if os.path.exists(records_file):
                with open(records_file, 'r', encoding='utf-8') as f:
                    self.client_records = json.load(f)
            else:
                self.client_records = []
        except Exception as e:
            print(f"加载客户端记录失败: {e}")
            self.client_records = []
    
    def save_client_records(self):
        """保存客户端记录到文件"""
        import json
        import os
        records_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'client_records.json')
        
        try:
            with open(records_file, 'w', encoding='utf-8') as f:
                json.dump(self.client_records, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存客户端记录失败: {e}")
    
    def refresh_clients(self):
        """刷新客户端列表"""
        # 保存当前选中的客户端MAC地址（作为唯一标识）
        selected_macs = []
        selection_model = self.client_table.selectionModel()
        if selection_model:
            for index in selection_model.selectedRows():
                row = index.row()
                if 0 <= row < len(self.client_records):
                    record = self.client_records[row]
                    mac = record.get('mac_address')
                    if mac:
                        selected_macs.append(mac)
        
        # 加载客户端记录
        self.load_client_records()
        
        # 加载消息文件
        import json
        import os
        messages_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'messages.json')
        messages_data = {}
        if os.path.exists(messages_file):
            try:
                with open(messages_file, 'r', encoding='utf-8') as f:
                    messages_data = json.load(f)
            except Exception as e:
                print(f"加载消息文件失败: {str(e)}")
        
        # 清空表格
        self.client_table.setRowCount(0)
        
        # 更新表格数据
        online_count = 0
        offline_count = 0
        mac_to_row = {}
        
        for idx, record in enumerate(self.client_records, 1):
            row_position = self.client_table.rowCount()
            self.client_table.insertRow(row_position)
            
            # 保存MAC地址到行索引的映射
            mac = record.get('mac_address')
            if mac:
                mac_to_row[mac] = row_position
            
            # ID列
            id_item = QTableWidgetItem(str(idx))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.client_table.setItem(row_position, 0, id_item)
            
            # 客户端IP列
            ip_item = QTableWidgetItem(record.get('ip', '未知'))
            self.client_table.setItem(row_position, 1, ip_item)
            
            # 计算机名列
            computer_name_item = QTableWidgetItem(record.get('computer_name', '未知'))
            self.client_table.setItem(row_position, 2, computer_name_item)
            
            # 在线状态列
            status_item = QTableWidgetItem()
            status = record.get('status', 'offline')
            status_item.setText('在线' if status == 'online' else '离线')
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            # 设置状态颜色
            if status == 'online':
                status_item.setForeground(Qt.GlobalColor.green)
            else:
                status_item.setForeground(Qt.GlobalColor.gray)
            self.client_table.setItem(row_position, 3, status_item)
            
            # 物理地址列
            mac_address_item = QTableWidgetItem(record.get('mac_address', '未知'))
            self.client_table.setItem(row_position, 4, mac_address_item)
            
            # 初次连接时间列
            first_connect_item = QTableWidgetItem(record.get('connect_time', '未知'))
            self.client_table.setItem(row_position, 5, first_connect_item)
            
            # 最近连接时间列
            last_connect_item = QTableWidgetItem(record.get('last_connect_time', record.get('connect_time', '未知')))
            self.client_table.setItem(row_position, 6, last_connect_item)
            
            # 连接次数列
            connect_count_item = QTableWidgetItem(str(record.get('connect_count', 0)))
            connect_count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.client_table.setItem(row_position, 7, connect_count_item)
            
            # 消息读取状态列
            message_status_item = QTableWidgetItem()
            message_status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # 获取客户端标识
            client_id = record.get('mac_address', f'client_{idx}')
            
            # 检查消息读取状态
            client_messages = messages_data.get(client_id, {}).get('messages', [])
            if client_messages:
                # 检查是否有未读消息
                unread_count = sum(1 for msg in client_messages if not msg.get('read', False))
                if unread_count > 0:
                    message_status_item.setText(f'未读({unread_count})')
                    message_status_item.setForeground(Qt.GlobalColor.red)
                else:
                    message_status_item.setText('全部已读')
                    message_status_item.setForeground(Qt.GlobalColor.green)
            else:
                message_status_item.setText('无消息')
                message_status_item.setForeground(Qt.GlobalColor.gray)
            
            self.client_table.setItem(row_position, 8, message_status_item)
            
            # 更新计数
            if status == 'online':
                online_count += 1
            else:
                offline_count += 1
        
        # 更新统计信息
        total_count = len(self.client_records)
        self.total_label.setText(f"总客户端: {total_count}")
        self.online_label.setText(f"在线: {online_count}")
        self.offline_label.setText(f"离线: {offline_count}")
        
        # 恢复选中状态
        if selected_macs:
            # 先清除所有选中状态
            self.client_table.clearSelection()
            # 设置为多选模式
            self.client_table.setSelectionMode(self.client_table.SelectionMode.MultiSelection)
            # 逐个选中符合条件的行
            for mac in selected_macs:
                if mac in mac_to_row:
                    row = mac_to_row[mac]
                    # 使用selectRange而不是selectRow，这样可以保持之前的选中状态
                    self.client_table.selectRow(row)
    
    def delete_selected(self):
        """删除选中的客户端记录"""
        selected_rows = sorted([index.row() for index in self.client_table.selectionModel().selectedRows()], reverse=True)
        
        if not selected_rows:
            return
        
        # 删除选中的记录
        for row in selected_rows:
            if 0 <= row < len(self.client_records):
                del self.client_records[row]
        
        # 保存并刷新
        self.save_client_records()
        self.refresh_clients()
    
    def clear_all(self):
        """清空所有客户端记录"""
        from qfluentwidgets import MessageBox
        msg_box = MessageBox('确认清空', '确定要清空所有客户端记录吗？此操作不可恢复。', self)
        msg_box.yesButton.setText('确定')
        msg_box.cancelButton.setText('取消')
        
        if msg_box.exec():
            self.client_records = []
            self.save_client_records()
            self.refresh_clients()
    
    def select_all_clients(self):
        """全选客户端"""
        self.client_table.selectAll()
    
    def openMessageDialog(self):
        """打开消息发送对话框"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton
        from qfluentwidgets import PushButton, FluentIcon as FIF, isDarkTheme
        
        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle('消息推送')
        dialog.setMinimumSize(600, 400)
        
        # 根据主题设置对话框样式
        is_dark = isDarkTheme()
        if is_dark:
            dialog.setStyleSheet('''
                QDialog {
                    background-color: #1e1e1e;
                    color: #ffffff;
                }
                QLabel {
                    color: #ffffff;
                }
                QLineEdit, QTextEdit {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    border: 1px solid #3d3d3d;
                    border-radius: 4px;
                    padding: 8px;
                }
            ''')
        else:
            dialog.setStyleSheet('''
                QDialog {
                    background-color: #f3f3f3;
                    color: #000000;
                }
                QLabel {
                    color: #000000;
                }
                QLineEdit, QTextEdit {
                    background-color: #ffffff;
                    color: #000000;
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                    padding: 8px;
                }
            ''')
        
        # 创建布局
        layout = QVBoxLayout(dialog)
        
        # 消息标题输入
        title_layout = QHBoxLayout()
        title_label = QLabel('消息标题：')
        title_input = QLineEdit()
        title_input.setPlaceholderText('请输入消息标题')
        title_input.setText(self.message_title_cache)  # 使用缓存的内容
        title_layout.addWidget(title_label)
        title_layout.addWidget(title_input)
        layout.addLayout(title_layout)
        
        # 消息内容输入
        content_layout = QHBoxLayout()
        content_label = QLabel('消息内容：')
        content_input = QTextEdit()
        content_input.setPlaceholderText('请输入消息内容')
        content_input.setMinimumHeight(200)
        content_input.setText(self.message_content_cache)  # 使用缓存的内容
        content_layout.addWidget(content_label)
        content_layout.addWidget(content_input)
        layout.addLayout(content_layout)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 取消按钮
        cancel_btn = PushButton('取消')
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        # 发送按钮
        send_btn = PushButton('发送消息')
        send_btn.setIcon(FIF.SEND)
        
        def on_send():
            """发送消息"""
            title = title_input.text().strip()
            content = content_input.toPlainText().strip()
            
            if not title or not content:
                from qfluentwidgets import InfoBar, InfoBarPosition
                InfoBar.warning(
                    title='消息内容不完整',
                    content='请输入消息标题和内容',
                    position=InfoBarPosition.TOP_RIGHT,
                    parent=dialog
                )
                return
            
            # 保存到缓存
            self.message_title_cache = title
            self.message_content_cache = content
            
            # 发送消息
            self.send_message(title, content)
            
            # 关闭对话框
            dialog.accept()
        
        send_btn.clicked.connect(on_send)
        button_layout.addWidget(send_btn)
        
        layout.addLayout(button_layout)
        
        # 显示对话框
        dialog.exec()
    
    def send_message(self, title, content):
        """发送消息到选中的客户端"""
        # 获取选中的客户端
        selected_rows = [index.row() for index in self.client_table.selectionModel().selectedRows()]
        
        if not selected_rows:
            from qfluentwidgets import InfoBar, InfoBarPosition
            InfoBar.warning(
                title='未选择客户端',
                content='请至少选择一个客户端后再发送消息',
                position=InfoBarPosition.TOP_RIGHT,
                parent=self
            )
            return
        
        # 发送消息
        try:
            import json
            import os
            import uuid
            from datetime import datetime
            
            # 加载现有消息
            messages_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'messages.json')
            if os.path.exists(messages_file):
                with open(messages_file, 'r', encoding='utf-8') as f:
                    messages = json.load(f)
            else:
                messages = {}
            
            # 为每个选中的客户端创建消息
            sent_count = 0
            for row in selected_rows:
                if 0 <= row < len(self.client_records):
                    client = self.client_records[row]
                    client_id = client.get('mac_address', f'client_{row}')
                    
                    # 确保客户端消息列表存在
                    if client_id not in messages:
                        messages[client_id] = {'messages': []}
                    
                    # 创建消息
                    message = {
                        'id': str(uuid.uuid4()),
                        'title': title,
                        'content': content,
                        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'read': False
                    }
                    
                    # 添加消息
                    messages[client_id]['messages'].append(message)
                    sent_count += 1
            
            # 保存消息
            with open(messages_file, 'w', encoding='utf-8') as f:
                json.dump(messages, f, ensure_ascii=False, indent=2)
            
            # 显示发送成功信息
            from qfluentwidgets import InfoBar, InfoBarPosition
            InfoBar.success(
                title='消息发送成功',
                content=f'已成功发送消息到 {sent_count} 个客户端',
                position=InfoBarPosition.TOP_RIGHT,
                parent=self
            )
            
        except Exception as e:
            from qfluentwidgets import InfoBar, InfoBarPosition
            InfoBar.error(
                title='消息发送失败',
                content=f'发送消息时出错：{str(e)}',
                position=InfoBarPosition.TOP_RIGHT,
                parent=self
            )

    def updateThemeStyle(self):
        """根据当前主题更新样式"""
        is_dark = isDarkTheme()
        
        # 设置标签文字颜色
        label_style = "color: #d8dee9;" if is_dark else "color: black;"
        group_box_style = "QGroupBox { color: #d8dee9; font-weight: bold; }" if is_dark else "QGroupBox { color: black; font-weight: bold; }"
        
        # 设置分组框样式
        self.monitor_group.setStyleSheet(group_box_style)
        
        # 设置统计标签样式
        self.total_label.setStyleSheet(label_style)
        self.online_label.setStyleSheet(label_style)
        self.offline_label.setStyleSheet(label_style)
        
        # 设置表格样式
        if is_dark:
            table_style = """
                QTableWidget {
                    background-color: #2d2d2d;
                    alternate-background-color: #323232;
                    border: 1px solid #3d3d3d;
                    border-radius: 4px;
                }
                QTableWidget::item {
                    padding: 5px;
                    color: #ffffff;
                }
                QTableWidget::item:selected {
                    background-color: #0078d7;
                }
                QHeaderView::section {
                    background-color: #3d3d3d;
                    color: #ffffff;
                    padding: 5px;
                    border: 1px solid #4d4d4d;
                    font-weight: bold;
                }
                QHeaderView::section:horizontal {
                    border-left: none;
                    height: 33px;
                }
                QHeaderView::section:horizontal:last {
                    border-right: none;
                }
                QHeaderView::section:vertical {
                    border-top: none;
                }
                QTableCornerButton::section {
                    background-color: #3d3d3d;
                    border: 1px solid #4d4d4d;
                }
            """
        else:
            table_style = """
                QTableWidget {
                    background-color: #ffffff;
                    alternate-background-color: #f9f9f9;
                    border: 1px solid #d0d0d0;
                    border-radius: 4px;
                }
                QTableWidget::item {
                    padding: 5px;
                    color: #000000;
                }
                QTableWidget::item:selected {
                    background-color: #0078d7;
                    color: #ffffff;
                }
                QHeaderView::section {
                    background-color: #f5f5f5;
                    color: #000000;
                    padding: 5px;
                    border: 1px solid #e0e0e0;
                    font-weight: bold;
                }
                QHeaderView::section:horizontal {
                    border-left: none;
                    height: 33px;
                }
                QHeaderView::section:horizontal:last {
                    border-right: none;
                }
            """
        self.client_table.setStyleSheet(table_style)

# 客户端信息上报处理函数
def handle_client_report(client_info):
    """处理客户端信息上报"""
    import json
    import os
    records_file = 'client_records.json'
    
    try:
        # 加载现有记录
        if os.path.exists(records_file):
            with open(records_file, 'r', encoding='utf-8') as f:
                records = json.load(f)
        else:
            records = []
        
        # 检查是否已存在相同IP的记录
        existing_record = None
        for record in records:
            if record.get('ip') == client_info.get('ip'):
                existing_record = record
                break
        
        if existing_record:
            # 更新现有记录
            existing_record.update(client_info)
        else:
            # 添加新记录
            records.append(client_info)
        
        # 保存记录
        with open(records_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f"处理客户端上报失败: {e}")
        return False

class Widget(QWidget):
    """基础界面组件"""
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = QLabel(text, self)
        self.hBoxLayout = QHBoxLayout(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignmentFlag.AlignCenter)
        self.setObjectName(text.replace(' ', '-'))

class MainWindow(MSFluentWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()
        
        # 设置主题为自动适应系统主题
        setTheme(Theme.AUTO)
        
        # create sub interface
        self.monitorInterface = MonitorWidget(self)  # 监控面板
        self.managementToolInterface = ManagementToolWidget(self)  # 管理工具
        self.clientMonitorInterface = ClientMonitorWidget(self)  # 客户端监控
        self.libraryInterface = Widget('library Interface', self)
        
        self.initNavigation()
        self.initWindow()
        
        # 添加系统主题监听器
        self.themeListener = SystemThemeListener(self)
        self.themeListener.systemThemeChanged.connect(self.updateTheme)
        self.themeListener.start()
        
        # 初始化标题颜色
        self.updateTitleColor()
    
    def initNavigation(self):
        # 添加导航项
        self.addSubInterface(self.monitorInterface, FIF.HOME, '监控面板', FIF.HOME_FILL)
        self.addSubInterface(self.managementToolInterface, FIF.SETTING, '管理工具')
        self.addSubInterface(self.clientMonitorInterface, FIF.VIDEO, '客户端监控')
        
        # 添加底部导航项
        self.addSubInterface(self.libraryInterface, FIF.BOOK_SHELF, '库', FIF.LIBRARY_FILL, NavigationItemPosition.BOTTOM)
    
    def initWindow(self):
        self.resize(1200, 800)
        
        # 设置窗口图标
        icon_path = resource_path("resource\\Server.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.setWindowTitle('知秋工作平台 - 服务管理面板')
        
        # 居中显示
        desktop = self.screen().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)
    
    def updateTheme(self):
        """更新主题"""
        setTheme(Theme.AUTO)
        # 更新监控面板的主题样式
        self.monitorInterface.updateThemeStyle()
        # 更新管理工具的主题样式
        self.managementToolInterface.updateThemeStyle()
        # 更新客户端监控的主题样式
        self.clientMonitorInterface.updateThemeStyle()
        # 更新标题颜色
        self.updateTitleColor()
    
    def updateTitleColor(self):
        """更新标题文字颜色"""
        is_dark = isDarkTheme()
        # 设置标题文字颜色
        if hasattr(self, 'titleBar') and hasattr(self.titleBar, 'titleLabel'):
            if is_dark:
                self.titleBar.titleLabel.setStyleSheet('color: gold; font-weight: bold;')
            else:
                self.titleBar.titleLabel.setStyleSheet('color: black; font-weight: bold;')
    
    def closeEvent(self, event):
        """处理窗口关闭事件，确保所有线程都被正确停止"""
        # 停止系统主题监听器线程
        if hasattr(self, 'themeListener') and self.themeListener.isRunning():
            self.themeListener.terminate()
            self.themeListener.wait()
        # 继续执行默认的关闭事件处理
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec()
