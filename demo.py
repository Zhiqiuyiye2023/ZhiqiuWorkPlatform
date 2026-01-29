# coding:utf-8
import sys
import os
import json

# 从version.json文件中读取版本号
try:
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'version.json'), 'r', encoding='utf-8') as f:
        version_info = json.load(f)
    VERSION = version_info['version']
except Exception as e:
    # 如果读取失败，使用默认值
    VERSION = "1.0.3"
"""
python.exe -m pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
专业版：
pyinstaller -F -w --noconsole --icon="logo.ico" -n "知秋工作平台v1.0.2" demo.py
控制台版：
pyinstaller -F -c --icon="logo.ico" -n "知秋工作平台v1.0.2" demo.py
验证驱动是否正常
nvidia-smi
卸载当前的 CPU 版本
python -m pip uninstall torch torchvision torchaudio

安装 PyTorch
安装 PyTorch（CUDA 12.1）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

设备: GPU: NVIDIA GeForce RTX 5060 Laptop GPU (8.0GB)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

Python 中验证 GPU 支持
import torch
print("PyTorch version:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())        # 应输出 True
print("GPU name:", torch.cuda.get_device_name(0))          # 应输出 "Quadro RTX 4000"

"""
# 为了支持QtWebEngineWidgets，必须在创建QApplication之前导入
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings

from PyQt6.QtCore import Qt, QSize, QTimer, qInstallMessageHandler, QtMsgType
from PyQt6.QtGui import QIcon, QDesktopServices
from PyQt6.QtWidgets import QLabel, QHBoxLayout, QVBoxLayout, QApplication, QWidget, QDialog, QScrollArea, QPushButton
from PyQt6.QtCore import QUrl

# 自定义消息处理器，过滤掉特定的CSS属性警告
def custom_message_handler(mode, context, message):
    # 过滤掉CSS属性警告
    css_warnings = [
        'Unknown property -webkit-background-clip',
        'Unknown property -webkit-text-fill-color',
        'Unknown property transition',
        'Unknown property box-shadow',
        'Unknown property transform'
    ]
    
    message_str = message.strip()
    for warning in css_warnings:
        if warning in message_str:
            return  # 过滤掉该警告
    
    # 其他警告正常输出
    print(message_str)

# 安装自定义消息处理器
qInstallMessageHandler(custom_message_handler)

from qfluentwidgets import (FluentWindow, NavigationItemPosition, MessageBox,
                            SplashScreen, SystemThemeListener, SearchLineEdit,
                            TransparentToolButton, Action, AvatarWidget, Theme,
                            RoundMenu, MenuAnimationType, InfoBar, InfoBarPosition,
                            InfoBadge, InfoBadgePosition)
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets.window.fluent_window import FluentTitleBar

# 导入设置界面和配置
from interfaces.setting_interface import SettingInterface
from configs.config import cfg
from interfaces.app_card_interface import AppCardInterface
from interfaces.home_interface import HomeInterface
from interfaces.global_search import GlobalSearchDropdown

# 更新配置中的版本号
cfg.currentVersion.value = VERSION
# YOLO界面延迟导入，加快启动速度


class CustomTitleBar(FluentTitleBar):
    """ 带搜索框的标题栏 """

    def __init__(self, parent):
        super().__init__(parent)
        
        # 确保窗口控制按钮可见
        self.minBtn.show()
        self.minBtn.setVisible(True)
        self.maxBtn.show()
        self.maxBtn.setVisible(True)
        self.closeBtn.show()
        self.closeBtn.setVisible(True)
        
        # 从默认布局中移除控制按钮，以便我们可以自定义它们的位置
        self.hBoxLayout.removeWidget(self.minBtn)
        self.hBoxLayout.removeWidget(self.maxBtn)
        self.hBoxLayout.removeWidget(self.closeBtn)
        
        # 从 buttonLayout 中移除（FluentTitleBar会将按钮添加到这个布局）
        if hasattr(self, 'buttonLayout'):
            self.buttonLayout.removeWidget(self.minBtn)
            self.buttonLayout.removeWidget(self.maxBtn)
            self.buttonLayout.removeWidget(self.closeBtn)
        
        # 从 vBoxLayout 中移除 buttonLayout（我们将手动管理按钮）
        if hasattr(self, 'vBoxLayout') and hasattr(self, 'buttonLayout'):
            self.vBoxLayout.removeItem(self.buttonLayout)
        
        # 添加搜索框
        self.searchLineEdit = SearchLineEdit(self)
        self.searchLineEdit.setPlaceholderText('搜索应用、工具等')
        self.searchLineEdit.setFixedWidth(300)  # 调整宽度以适应右侧布局
        self.searchLineEdit.setClearButtonEnabled(True)
        
        # 创建全局搜索下拉框 (延迟初始化，避免在QApplication之前创建QWidget)
        self.searchDropdown = None
        
        # 连接搜索事件
        self.searchLineEdit.textChanged.connect(self._onSearchTextChanged)
        self.searchLineEdit.searchSignal.connect(self._onSearchEnter)  # 回车键搜索
        
        # 在右侧添加功能按钮
        # 添加一个弹性空间，将后续元素推到右侧
        self.hBoxLayout.addStretch(1)
        
        # 搜索框
        self.hBoxLayout.addWidget(self.searchLineEdit, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(12)  # 搜索框后添加间距
        
        self.notificationBtn = TransparentToolButton(FIF.CHAT, self)
        self.notificationBtn.setFixedSize(46, 32)
        self.notificationBtn.setToolTip('通知')
        
        # 未读消息计数器（使用InfoBadge）
        self.unreadBadge = None
        
        # 服务器状态圆形指示灯
        self.serverStatusIndicator = QLabel(self)
        self.serverStatusIndicator.setFixedSize(16, 16)  # 设置圆形指示灯大小
        self.serverStatusIndicator.setToolTip('服务器状态')
        # 初始状态为灰色（未连接）
        self.updateServerStatus(False)
        
        # 主题切换按钮
        self.themeBtn = TransparentToolButton(FIF.CONSTRACT, self)
        self.themeBtn.setFixedSize(46, 32)
        self.themeBtn.setToolTip('切换主题')
        
        # 用户头像
        self.avatar = AvatarWidget('resource/shoko.png', parent=self)
        self.avatar.setRadius(18)  # 设置圆角半径
        self.avatar.setFixedSize(36, 36)  # 设置头像大小为36x36
        
        # 将按钮添加到布局
        self.hBoxLayout.addWidget(self.notificationBtn, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(8)  # 通知按钮后添加间距
        self.hBoxLayout.addWidget(self.serverStatusIndicator, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.hBoxLayout.addSpacing(8)  # 服务器状态指示灯后添加间距
        self.hBoxLayout.addWidget(self.themeBtn, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(8)  # 主题按钮后添加间距
        self.hBoxLayout.addWidget(self.avatar, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(8)  # 头像后添加间距
        
        # 窗口控制按钮（最小化、最大化/还原、关闭）- 放置在头像右侧
        # 设置按钮样式以匹配整体UI
        self.minBtn.setFixedSize(40, 32)
        self.maxBtn.setFixedSize(40, 32)
        self.closeBtn.setFixedSize(40, 32)
        
        # 为按钮设置更美观的样式
        self.minBtn.setStyleSheet("border-radius: 4px;")
        self.maxBtn.setStyleSheet("border-radius: 4px;")
        self.closeBtn.setStyleSheet("border-radius: 4px;")
        
        # 创建按钮容器并添加窗口控制按钮
        from PyQt6.QtWidgets import QWidget, QHBoxLayout
        button_container = QWidget(self)
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(4)  # 按钮间间距
        
        # 将窗口控制按钮添加到按钮容器中
        button_layout.addWidget(self.minBtn)
        button_layout.addWidget(self.maxBtn)
        button_layout.addWidget(self.closeBtn)
        
        # 将按钮容器添加到主布局右侧（头像旁边）
        self.hBoxLayout.addWidget(button_container, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)  # 右侧边距
        
        # 连接信号
        self.notificationBtn.clicked.connect(self._onNotificationClicked)
        self.themeBtn.clicked.connect(self._onThemeClicked)
        self.avatar.clicked.connect(self._onAvatarClicked)
        
        # 应用初始主题
        self._updateTheme()
        
        # 美化标题文字
        self._updateTitleStyle()
        
        # 启动服务器状态检查
        self.startServerStatusCheck()
        
        # 上报客户端信息
        self.reportClientInfo()
        
        # 启动消息检查
        self.startMessageCheck()
        
        # 消息存储
        self.messages = []
        # 之前的未读消息数量，用于判断是否有新消息
        self.previous_unread_count = 0
        # 标记是否是首次启动
        self.is_first_start = True
    
    def _ensureSearchDropdown(self):
        """确保搜索下拉框已创建"""
        if self.searchDropdown is None:
            from interfaces.global_search import GlobalSearchDropdown
            self.searchDropdown = GlobalSearchDropdown(self)
            self.searchDropdown.hide()
            self.searchDropdown.appSelected.connect(self._onAppSelected)
    
    def _onSearchTextChanged(self, text: str):
        """ 搜索文本改变事件 - 全局搜索 """
        # 确保搜索下拉框已创建
        self._ensureSearchDropdown()
        
        if text and self.searchDropdown:
            # 更新搜索结果
            self.searchDropdown.updateResults(text)
            
            # 计算下拉框位置（在搜索框下方）
            search_pos = self.searchLineEdit.mapToGlobal(self.searchLineEdit.rect().bottomLeft())
            search_pos.setY(search_pos.y() + 5)  # 下移5px
            self.searchDropdown.showAtPosition(search_pos, self.searchLineEdit.width())
        elif self.searchDropdown:
            # 清空搜索时隐藏下拉框
            self.searchDropdown.hide()
        
        # 保留原有的应用页面过滤功能（兼容）
        from interfaces.app_card_interface import AppCardInterface  # 确保导入AppCardInterface
        window = self.window()
        if window and hasattr(window, 'appInterface') and isinstance(getattr(window, 'appInterface'), AppCardInterface):
            app_interface = getattr(window, 'appInterface')
            app_interface.filterCards(text)
    
    def _onSearchEnter(self):
        """ 回车键搜索事件 """
        # 如果有搜索结果，可以选择第一个结果
        pass
    
    def _onAppSelected(self, app_id: str, title: str):
        """ 应用被选中事件 """
        # 清空搜索框
        self.searchLineEdit.clear()
        
        # 打开应用
        from app_functions import AppFunctionManager
        try:
            AppFunctionManager.openApp(app_id, self.window())
            # 显示成功提示
            InfoBar.success(
                title='打开应用',
                content=f'正在启动「{title}」',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=1500,
                parent=self.window()
            )
        except Exception as e:
            InfoBar.error(
                title='错误',
                content=f'无法打开应用：{str(e)}',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000,
                parent=self.window()
            )
    
    def _onNotificationClicked(self):
        """ 通知按钮点击事件 """
        # 显示消息列表
        self.showMessageList()
    
    def startMessageCheck(self):
        """启动消息检查定时器"""
        from PyQt6.QtCore import QTimer
        self.message_timer = QTimer(self)
        self.message_timer.timeout.connect(self.startMessageCheckThread)
        self.message_timer.start(10000)  # 每10秒检查一次消息
        
        # 立即检查一次
        self.startMessageCheckThread()
    
    def startMessageCheckThread(self):
        """启动消息检查线程"""
        from PyQt6.QtCore import QThread, pyqtSignal
        
        # 创建消息检查线程
        class MessageCheckThread(QThread):
            """消息检查线程"""
            result_signal = pyqtSignal(list)  # 发送未读消息列表
            error_signal = pyqtSignal(str)    # 发送错误信息
            
            def __init__(self, client_id):
                super().__init__()
                self.client_id = client_id
            
            def run(self):
                """执行消息检查"""
                import requests
                import json
                
                try:
                    # 强制使用公网地址进行消息接收
                    server_url = "https://bream-guided-poodle.ngrok-free.app"
                    
                    if not server_url:
                        return
                    
                    # 请求未读消息
                    response = requests.get(
                        f'{server_url}/api/v1/messages/unread',
                        params={'client_id': self.client_id},
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        unread_messages = data.get('messages', [])
                        self.result_signal.emit(unread_messages)
                        
                except Exception as e:
                    error_msg = f"检查消息失败: {str(e)}"
                    self.error_signal.emit(error_msg)
        
        # 获取客户端标识
        client_id = self._get_mac_address()
        
        # 创建并启动线程
        self.message_thread = MessageCheckThread(client_id)
        self.message_thread.result_signal.connect(self.onMessageCheckFinished)
        self.message_thread.error_signal.connect(self.onMessageCheckError)
        self.message_thread.start()
    
    def onMessageCheckFinished(self, unread_messages):
        """消息检查完成回调"""
        current_count = len(unread_messages)
        
        # 更新未读消息徽章
        self.updateUnreadBadge(current_count)
        
        # 存储消息
        self.messages = unread_messages
        
        # 判断是否有新消息
        has_new_message = False
        if self.is_first_start:
            # 首次启动时，如果有未读消息，显示通知
            has_new_message = current_count > 0
            self.is_first_start = False
        else:
            # 非首次启动时，只有当消息数量增加时才显示通知
            has_new_message = current_count > self.previous_unread_count
        
        # 更新之前的未读消息数量
        self.previous_unread_count = current_count
        
        # 如果有新消息，显示通知
        if has_new_message and unread_messages:
            self.showNewMessageNotification(unread_messages)
    
    def onMessageCheckError(self, error_msg):
        """消息检查错误回调"""
        print(error_msg)
    
    def updateUnreadBadge(self, count):
        """更新未读消息徽章"""
        # 确保 notificationBtn 存在
        if not self.notificationBtn:
            return
        
        # 如果有未读消息，确保徽章存在并更新计数
        if count > 0:
            if not self.unreadBadge:
                from PyQt6.QtWidgets import QLabel
                from PyQt6.QtGui import QFont
                from PyQt6.QtCore import Qt
                
                # 创建一个圆形的红色徽章，使用更小的尺寸
                self.unreadBadge = QLabel(self)
                self.unreadBadge.setText(str(count))
                self.unreadBadge.setFixedSize(18, 18)  # 更小的尺寸
                self.unreadBadge.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # 设置字体
                font = QFont()
                font.setPointSize(10)
                font.setBold(True)
                self.unreadBadge.setFont(font)
                
                # 设置样式 - 红色圆形背景，白色文字
                self.unreadBadge.setStyleSheet("""
                    QLabel {
                        background-color: #ff3b30;
                        color: white;
                        border-radius: 9px;
                        font-size: 10px;
                        font-weight: bold;
                    }
                """)
                
                # 计算位置 - 根据通知按钮的位置
                btn_pos = self.notificationBtn.pos()
                badge_x = btn_pos.x() + self.notificationBtn.width() - 18
                badge_y = btn_pos.y() - 2  # 稍微向上偏移
                self.unreadBadge.move(badge_x, badge_y)
                
                # 强制显示徽章
                self.unreadBadge.show()
                # 确保徽章在最上层
                self.unreadBadge.raise_()
            else:
                # 更新现有徽章的计数
                self.unreadBadge.setText(str(count))
                # 确保徽章仍然显示
                self.unreadBadge.show()
                self.unreadBadge.raise_()
        else:
            # 没有未读消息，移除徽章
            if self.unreadBadge:
                self.unreadBadge.deleteLater()
                self.unreadBadge = None
    
    def showNewMessageNotification(self, messages):
        """显示新消息通知"""
        from qfluentwidgets import InfoBar, InfoBarPosition
        
        # 只显示最新的一条消息通知
        if messages:
            latest_message = messages[0]
            InfoBar.success(
                title='新消息',
                content=f'您收到了一条新消息: {latest_message.get("title", "")}',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000,
                parent=self.window()
            )
    
    def showMessageList(self):
        """显示消息列表"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QWidget
        from PyQt6.QtCore import Qt
        from qfluentwidgets import FluentIcon as FIF, PushButton, isDarkTheme, IconWidget
        
        # 创建消息列表对话框
        dialog = QDialog(self.window())
        dialog.setWindowTitle('消息中心')
        dialog.setMinimumSize(640, 480)
        dialog.setMaximumSize(800, 600)
        
        # 根据主题设置对话框样式
        is_dark = isDarkTheme()
        if is_dark:
            dialog.setStyleSheet('''
                QDialog {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    border-radius: 12px;
                }
            ''')
        else:
            dialog.setStyleSheet('''
                QDialog {
                    background-color: #f8f9fa;
                    color: #000000;
                    border-radius: 12px;
                }
            ''')
        
        # 创建布局
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # 创建消息统计
        stats_label = QLabel(f'共 {len(self.messages)} 条未读消息')
        if is_dark:
            stats_label.setStyleSheet('color: #888888; font-size: 14px;')
        else:
            stats_label.setStyleSheet('color: #666666; font-size: 14px;')
        layout.addWidget(stats_label)
        
        # 分页参数
        PAGE_SIZE = 1  # 每页显示1条消息
        current_page = 0
        total_pages = (len(self.messages) + PAGE_SIZE - 1) // PAGE_SIZE
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 设置滚动区域样式
        if is_dark:
            scroll_area.setStyleSheet('''
                QScrollArea {
                    background-color: transparent;
                }
                QScrollBar:vertical {
                    background-color: #2d2d2d;
                    width: 10px;
                    margin: 0px 4px 0px 4px;
                    border-radius: 5px;
                }
                QScrollBar::handle:vertical {
                    background-color: #4d4d4d;
                    border-radius: 5px;
                    min-height: 40px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: #5d5d5d;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 0px;
                }
            ''')
        else:
            scroll_area.setStyleSheet('''
                QScrollArea {
                    background-color: transparent;
                }
                QScrollBar:vertical {
                    background-color: #e9ecef;
                    width: 10px;
                    margin: 0px 4px 0px 4px;
                    border-radius: 5px;
                }
                QScrollBar::handle:vertical {
                    background-color: #ced4da;
                    border-radius: 5px;
                    min-height: 40px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: #adb5bd;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 0px;
                }
            ''')
        
        # 创建消息容器
        message_container = QWidget()
        message_layout = QVBoxLayout(message_container)
        message_layout.setSpacing(12)
        message_layout.setContentsMargins(0, 0, 0, 0)
        
        # 设置消息容器背景
        message_container.setStyleSheet('background-color: transparent;')
        
        # 显示消息的函数
        def displayMessages(page):
            # 清空现有消息
            for i in reversed(range(message_layout.count())):
                widget = message_layout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()
            
            # 计算当前页的消息范围
            start_idx = page * PAGE_SIZE
            end_idx = min(start_idx + PAGE_SIZE, len(self.messages))
            page_messages = self.messages[start_idx:end_idx]
            
            if page_messages:
                for msg in page_messages:
                    # 创建消息项
                    message_item = QWidget()
                    message_item.setMinimumHeight(180)
                    message_item.setMaximumHeight(300)
                    item_layout = QVBoxLayout(message_item)
                    item_layout.setContentsMargins(20, 16, 20, 16)
                    item_layout.setSpacing(8)
                    
                    # 根据主题设置消息项样式
                    if is_dark:
                        message_item.setStyleSheet('''
                            QWidget {
                                background-color: #2d2d2d;
                                border-radius: 10px;
                                border: 1px solid #3d3d3d;
                            }
                            QWidget:hover {
                                background-color: #333333;
                                border-color: #4d4d4d;
                            }
                        ''')
                    else:
                        message_item.setStyleSheet('''
                            QWidget {
                                background-color: #ffffff;
                                border-radius: 10px;
                                border: 1px solid #e9ecef;
                                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
                            }
                            QWidget:hover {
                                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                                border-color: #dee2e6;
                            }
                        ''')
                    
                    # 创建消息头部
                    header_layout = QHBoxLayout()
                    header_layout.setContentsMargins(0, 0, 0, 0)
                    header_layout.setSpacing(12)
                    
                    # 消息图标
                    icon_widget = IconWidget(FIF.MAIL)
                    icon_widget.setFixedSize(24, 24)
                    header_layout.addWidget(icon_widget, 0, Qt.AlignmentFlag.AlignVCenter)
                    
                    # 消息标题
                    title_label = QLabel(f'<b>{msg.get("title", "无标题")}</b>')
                    if is_dark:
                        title_label.setStyleSheet('color: #ffffff; font-size: 14px;')
                    else:
                        title_label.setStyleSheet('color: #212529; font-size: 14px;')
                    title_label.setFixedHeight(24)
                    title_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
                    header_layout.addWidget(title_label, 1)
                    
                    # 消息时间
                    time_label = QLabel(msg.get("time", "未知"))
                    if is_dark:
                        time_label.setStyleSheet('color: #888888; font-size: 12px;')
                    else:
                        time_label.setStyleSheet('color: #6c757d; font-size: 12px;')
                    time_label.setFixedHeight(24)
                    time_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
                    header_layout.addWidget(time_label)
                    
                    item_layout.addLayout(header_layout)
                    
                    # 消息内容
                    content_label = QLabel(msg.get("content", "无内容"))
                    content_label.setWordWrap(True)
                    content_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
                    if is_dark:
                        content_label.setStyleSheet('color: #cccccc; font-size: 14px; line-height: 1.4;')
                    else:
                        content_label.setStyleSheet('color: #495057; font-size: 14px; line-height: 1.4;')
                    item_layout.addWidget(content_label)
                    
                    # 添加到消息布局
                    message_layout.addWidget(message_item)
            else:
                # 空消息提示
                empty_widget = QWidget()
                empty_widget.setMinimumHeight(200)
                empty_layout = QVBoxLayout(empty_widget)
                empty_layout.setContentsMargins(0, 0, 0, 0)
                empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                empty_icon = IconWidget(FIF.MAIL)
                empty_icon.setFixedSize(48, 48)
                if is_dark:
                    empty_icon.setStyleSheet('color: #4d4d4d;')
                else:
                    empty_icon.setStyleSheet('color: #ced4da;')
                
                empty_label = QLabel('暂无未读消息')
                empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                if is_dark:
                    empty_label.setStyleSheet('color: #888888; font-size: 16px; margin-top: 12px;')
                else:
                    empty_label.setStyleSheet('color: #6c757d; font-size: 16px; margin-top: 12px;')
                
                empty_layout.addWidget(empty_icon)
                empty_layout.addWidget(empty_label)
                message_layout.addWidget(empty_widget)
            
            # 更新分页信息
            page_info_label.setText(f'第 {page + 1} / {total_pages} 页')
            # 更新按钮状态
            prev_btn.setEnabled(page > 0)
            next_btn.setEnabled(page < total_pages - 1)
        
        # 设置滚动区域内容
        scroll_area.setWidget(message_container)
        layout.addWidget(scroll_area)
        
        # 创建分页控件
        pagination_layout = QHBoxLayout()
        pagination_layout.setContentsMargins(0, 0, 0, 0)
        pagination_layout.setSpacing(12)
        
        # 上一页按钮
        prev_btn = PushButton('上一页')
        prev_btn.setFixedHeight(36)
        prev_btn.setEnabled(False)
        
        # 分页信息
        page_info_label = QLabel(f'第 {current_page + 1} / {total_pages} 页')
        if is_dark:
            page_info_label.setStyleSheet('color: #888888; font-size: 14px;')
        else:
            page_info_label.setStyleSheet('color: #666666; font-size: 14px;')
        page_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 下一页按钮
        next_btn = PushButton('下一页')
        next_btn.setFixedHeight(36)
        next_btn.setEnabled(total_pages > 1)
        
        # 已读并删除按钮
        delete_btn = PushButton('已读并删除')
        delete_btn.setFixedHeight(36)
        delete_btn.setEnabled(len(self.messages) > 0)
        
        # 按钮点击事件
        def onPrevPage():
            nonlocal current_page
            if current_page > 0:
                current_page -= 1
                displayMessages(current_page)
        
        def onNextPage():
            nonlocal current_page
            if current_page < total_pages - 1:
                current_page += 1
                displayMessages(current_page)
        
        def onDeleteCurrentMessage():
            nonlocal current_page, total_pages
            if self.messages:
                # 获取当前页的消息索引
                current_msg_idx = current_page * PAGE_SIZE
                if current_msg_idx < len(self.messages):
                    # 标记消息为已读
                    msg = self.messages[current_msg_idx]
                    message_id = msg.get('id')
                    if message_id:
                        try:
                            import requests
                            # 获取客户端标识
                            client_id = self._get_mac_address()
                            # 强制使用公网地址进行消息操作
                            server_url = "https://bream-guided-poodle.ngrok-free.app"
                            if server_url:
                                requests.post(
                                    f'{server_url}/api/v1/messages/read',
                                    json={'client_id': client_id, 'message_id': message_id},
                                    timeout=5
                                )
                        except Exception:
                            pass
                    
                    # 从消息列表中删除
                    self.messages.pop(current_msg_idx)
                    
                    # 更新未读消息徽章
                    self.updateUnreadBadge(len(self.messages))
                    
                    # 重新计算总页数
                    total_pages = (len(self.messages) + PAGE_SIZE - 1) // PAGE_SIZE
                    
                    # 调整当前页码
                    if current_page >= total_pages and current_page > 0:
                        current_page -= 1
                    
                    # 刷新消息统计
                    stats_label.setText(f'共 {len(self.messages)} 条未读消息')
                    
                    # 重新显示消息
                    displayMessages(current_page)
        
        prev_btn.clicked.connect(onPrevPage)
        next_btn.clicked.connect(onNextPage)
        delete_btn.clicked.connect(onDeleteCurrentMessage)
        
        pagination_layout.addWidget(prev_btn)
        pagination_layout.addWidget(page_info_label, 1)
        pagination_layout.addWidget(next_btn)
        pagination_layout.addWidget(delete_btn)
        
        layout.addLayout(pagination_layout)
        
        # 创建底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 标记所有已读按钮
        mark_read_btn = PushButton('标记所有已读')
        mark_read_btn.setFixedHeight(36)
        mark_read_btn.clicked.connect(lambda: self.markAllMessagesRead(dialog))
        button_layout.addWidget(mark_read_btn)
        button_layout.addSpacing(12)
        
        # 关闭按钮
        close_btn = PushButton('关闭')
        close_btn.setFixedHeight(36)
        close_btn.clicked.connect(dialog.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # 初始显示第一页
        displayMessages(current_page)
        
        # 显示对话框
        dialog.exec()
    
    def markAllMessagesRead(self, dialog):
        """标记所有消息已读"""
        import requests
        import json
        from configs.config import cfg
        
        try:
            # 获取客户端标识
            client_id = self._get_mac_address()
            
            # 强制使用公网地址进行消息操作
            server_url = "https://bream-guided-poodle.ngrok-free.app"
            
            if not server_url:
                return
            
            # 标记每条消息已读
            for msg in self.messages:
                message_id = msg.get('id')
                if message_id:
                    requests.post(
                        f'{server_url}/api/v1/messages/read',
                        json={'client_id': client_id, 'message_id': message_id},
                        timeout=5
                    )
            
            # 清空消息列表
            self.messages = []
            self.updateUnreadBadge(0)
            
            # 关闭对话框
            dialog.close()
            
            # 显示成功提示
            from qfluentwidgets import InfoBar, InfoBarPosition
            InfoBar.success(
                title='操作成功',
                content='所有消息已标记为已读',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self.window()
            )
            
        except Exception as e:
            print(f"标记消息已读失败: {str(e)}")
    
    def _onThemeClicked(self):
        """ 主题按钮点击事件 """
        # 在浅色和深色之间切换
        from configs.config import cfg
        from qfluentwidgets import Theme
        current_theme = cfg.get(cfg.themeMode)
        if current_theme == Theme.LIGHT:
            cfg.set(cfg.themeMode, Theme.DARK)
            theme_name = '深色'
        else:
            cfg.set(cfg.themeMode, Theme.LIGHT)
            theme_name = '浅色'
        
        InfoBar.success(
            title='主题已切换',
            content=f'当前主题：{theme_name}',
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=1500,
            parent=self.window()
        )
    
    def _onAvatarClicked(self):
        """ 头像点击事件 """
        # 显示用户菜单
        menu = RoundMenu(parent=self)
        menu.addAction(Action(FIF.PEOPLE, '个人信息'))
        menu.addAction(Action(FIF.SYNC, '切换账号'))
        menu.addSeparator()
        
        # 退出登录选项
        exitAction = Action(FIF.CLOSE, '退出登录')
        exitAction.triggered.connect(self._onExitTriggered)
        menu.addAction(exitAction)
        
        menu.exec(self.avatar.mapToGlobal(self.avatar.rect().bottomLeft()), aniType=MenuAnimationType.DROP_DOWN)
    
    def updateServerStatus(self, is_connected):
        """更新服务器状态圆形指示灯颜色
        
        Args:
            is_connected (bool): 服务器是否连接成功
        """
        # 始终显示公网服务器状态，忽略本地服务器配置
        server_type_text = "公网服务器"
        
        # 根据服务器状态设置不同的颜色
        if is_connected:
            # 服务器正常，设置为绿色圆形
            self.serverStatusIndicator.setStyleSheet(
                "QLabel { "
                "    background-color: #4CAF50; "
                "    border-radius: 8px; "  # 一半的宽度/高度，使其成为圆形
                "}"
            )
            self.serverStatusIndicator.setToolTip(f'{server_type_text}状态：正常')
        else:
            # 服务器未连接，设置为灰色圆形
            self.serverStatusIndicator.setStyleSheet(
                "QLabel { "
                "    background-color: #888888; "
                "    border-radius: 8px; "  # 一半的宽度/高度，使其成为圆形
                "}"
            )
            self.serverStatusIndicator.setToolTip(f'{server_type_text}状态：未连接')
    
    def startServerStatusCheck(self):
        """开始定期检查服务器状态"""
        from PyQt6.QtCore import QTimer
        from configs.config import cfg
        
        def check_server_status_async():
            """异步检查服务器状态"""
            from PyQt6.QtCore import QThread, pyqtSignal
            
            class ServerStatusCheckThread(QThread):
                """服务器状态检查线程"""
                status_signal = pyqtSignal(bool)  # 发送服务器状态
                
                def __init__(self, server_url):
                    super().__init__()
                    self.server_url = server_url
                
                def run(self):
                    """执行服务器状态检查"""
                    import requests
                    
                    try:
                        # 尝试连接服务器
                        response = requests.get(f'{self.server_url}/api/v1/healthcheck', timeout=2)
                        
                        # 验证响应内容
                        if response.status_code == 200:
                            try:
                                data = response.json()
                                if 'status' in data and data['status'] == 'ok':
                                    self.status_signal.emit(True)
                                    return
                            except ValueError:
                                pass
                        
                        # 连接失败或响应无效
                        self.status_signal.emit(False)
                    except requests.exceptions.RequestException:
                        # 连接超时或其他错误
                        self.status_signal.emit(False)
            
            # 获取服务器地址
            server_url = cfg.publicServerUrl.value.strip('`\'"')
            
            # 创建并启动线程
            self.server_status_thread = ServerStatusCheckThread(server_url)
            self.server_status_thread.status_signal.connect(self.updateServerStatus)
            self.server_status_thread.start()
        
        # 创建定时器，每10秒检查一次服务器状态
        self.server_status_timer = QTimer(self)
        self.server_status_timer.timeout.connect(check_server_status_async)
        self.server_status_timer.start(10000)  # 10秒检查一次
        
        # 立即执行一次检查
        check_server_status_async()
    
    def reportClientOffline(self):
        """上报客户端离线状态到服务器"""
        import requests
        import json
        import socket
        import platform
        from datetime import datetime
        
        try:
            # 获取客户端信息
            client_info = {
                'ip': self._get_local_ip(),
                'computer_name': socket.gethostname(),
                'mac_address': self._get_mac_address(),
                'device_info': self._get_device_info(),
                'connect_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'last_connect_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'offline'
                # 去掉connect_count字段，让服务器自己处理
            }
            
            # 从配置中获取服务器地址
            from configs.config import cfg
            # 使用公网服务器地址进行上报
            server_url = cfg.publicServerUrl.value.strip('`\'"')
            
            # 打印调试信息
            print(f'公网服务器地址: {server_url}')
            print(f'上报URL: {server_url}/api/v1/client/report')
            print(f'上报离线信息: {client_info}')
            
            if not server_url:
                print('公网服务器地址未配置，跳过客户端离线信息上报')
                return
            
            # 上报客户端离线信息
            response = requests.post(
                f'{server_url}/api/v1/client/report',
                json=client_info,
                timeout=5
            )
            
            if response.status_code == 200:
                print('客户端离线信息上报成功')
            else:
                print(f'客户端离线信息上报失败，状态码: {response.status_code}')
                
        except Exception as e:
            print(f'客户端离线信息上报出错: {str(e)}')

    def _onExitTriggered(self):
        """ 退出登录 """
        # 显示确认对话框
        w = MessageBox(
            '退出登录',
            '确定要退出登录吗？',
            self.window()
        )
        w.yesButton.setText('确定')
        w.cancelButton.setText('取消')
        
        if w.exec():
            # 用户确认退出，先上报离线状态
            self.reportClientOffline()
            # 延迟一秒后关闭应用，确保上报完成
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1000, QApplication.quit)
    
    def reportClientInfo(self):
        """上报客户端信息到服务器"""
        import requests
        import json
        import socket
        import platform
        from datetime import datetime
        
        try:
            # 获取客户端信息
            client_info = {
                'ip': self._get_local_ip(),
                'computer_name': socket.gethostname(),
                'mac_address': self._get_mac_address(),
                'device_info': self._get_device_info(),
                'connect_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'last_connect_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'online'
                # 去掉connect_count字段，让服务器自己处理
            }
            
            # 从配置中获取服务器地址
            from configs.config import cfg
            # 使用公网服务器地址进行上报
            server_url = cfg.publicServerUrl.value.strip('`\'"')
            
            # 打印调试信息
            print(f'公网服务器地址: {server_url}')
            print(f'上报URL: {server_url}/api/v1/client/report')
            print(f'上报信息: {client_info}')
            
            if not server_url:
                print('公网服务器地址未配置，跳过客户端信息上报')
                return
            
            # 上报客户端信息
            response = requests.post(
                f'{server_url}/api/v1/client/report',
                json=client_info,
                timeout=5
            )
            
            if response.status_code == 200:
                print('客户端信息上报成功')
            else:
                print(f'客户端信息上报失败，状态码: {response.status_code}')
                
        except Exception as e:
            print(f'客户端信息上报出错: {str(e)}')
    
    def _get_mac_address(self):
        """获取物理地址（MAC地址）"""
        try:
            import uuid
            import socket
            import platform
            
            # 尝试获取所有网络接口的MAC地址
            if platform.system() == 'Windows':
                # Windows系统
                import winreg
                
                # 打开注册表
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Control\Class\{4D36E972-E325-11CE-BFC1-08002BE10318}')
                
                mac_addresses = []
                
                # 遍历所有网络适配器
                for i in range(1000):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        subkey = winreg.OpenKey(key, subkey_name)
                        
                        # 尝试获取MAC地址
                        try:
                            mac = winreg.QueryValueEx(subkey, 'NetworkAddress')[0]
                            if mac:
                                mac_addresses.append(mac)
                        except Exception:
                            pass
                        
                        try:
                            mac = winreg.QueryValueEx(subkey, 'MACAddress')[0]
                            if mac:
                                mac_addresses.append(mac)
                        except Exception:
                            pass
                        
                        subkey.Close()
                    except Exception:
                        break
                
                key.Close()
                
                if mac_addresses:
                    # 返回第一个MAC地址
                    return mac_addresses[0].upper()
            
            # 跨平台方法：使用uuid.getnode()
            mac = uuid.getnode()
            mac_address = ':'.join(['{:02x}'.format((mac >> elements) & 0xff) for elements in range(0,28,8)][::-1])
            return mac_address
        except Exception:
            return '未知MAC地址'
    
    def _get_local_ip(self):
        """获取本地IP地址"""
        try:
            import socket
            
            # 方法1：尝试获取所有网络接口的IP地址
            ip_addresses = []
            
            # 获取主机名
            hostname = socket.gethostname()
            
            # 获取所有与主机名关联的IP地址
            addrinfo = socket.getaddrinfo(hostname, None, socket.AF_INET)
            for info in addrinfo:
                ip = info[4][0]
                if ip and not ip.startswith('127.'):
                    ip_addresses.append(ip)
            
            # 如果找到非本地回环地址，返回第一个
            if ip_addresses:
                return ip_addresses[0]
            
            # 方法2：使用传统方法作为后备
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0.5)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            print(f"获取IP地址失败: {e}")
            # 方法3：作为最后的后备，使用socket.gethostbyname
            try:
                hostname = socket.gethostname()
                ip = socket.gethostbyname(hostname)
                return ip
            except Exception:
                return '127.0.0.1'
    
    def _get_device_info(self):
        """获取设备信息"""
        try:
            system = platform.system()
            release = platform.release()
            version = platform.version()
            machine = platform.machine()
            return f'{system} {release} {version} ({machine})'
        except Exception:
            return '未知设备'
    
    def _updateTheme(self):
        """更新标题栏主题样式"""
        from qfluentwidgets import isDarkTheme
        
        if isDarkTheme():
            # 深色主题
            self.setStyleSheet("""
                FluentTitleBar {
                    background-color: #1e1e1e;
                }
            """)
        else:
            # 浅色主题
            self.setStyleSheet("""
                FluentTitleBar {
                    background-color: #f3f3f3;
                }
            """)
        self.update()
    
    def _updateTitleStyle(self):
        """更新标题文字样式"""
        from qfluentwidgets import isDarkTheme
        
        # 设置字体
        font = self.titleLabel.font()
        font.setFamily('Microsoft YaHei')
        font.setPointSize(14)
        font.setBold(True)
        self.titleLabel.setFont(font)
        
        # 根据主题设置颜色
        if isDarkTheme():
            # 深色主题下使用渐变色彩
            self.titleLabel.setStyleSheet("""
                QLabel#titleLabel {
                    color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ffffff, stop:1 #cccccc);
                    background: transparent;
                    font: bold 14px 'Microsoft YaHei';
                    padding: 0 4px;
                }
            """)
        else:
            # 浅色主题下使用渐变色彩
            self.titleLabel.setStyleSheet("""
                QLabel#titleLabel {
                    color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #333333, stop:1 #666666);
                    background: transparent;
                    font: bold 14px 'Microsoft YaHei';
                    padding: 0 4px;
                }
            """)
    
    def resizeEvent(self, a0):
        super().resizeEvent(a0)
        # 确保徽章在窗口大小变化时仍然保持正确的位置
        if self.unreadBadge and self.notificationBtn:
            btn_pos = self.notificationBtn.pos()
            badge_x = btn_pos.x() + self.notificationBtn.width() - 18
            badge_y = btn_pos.y() - 2  # 稍微向上偏移
            self.unreadBadge.move(badge_x, badge_y)
            # 确保徽章仍然显示
            self.unreadBadge.show()
            self.unreadBadge.raise_()


class CustomSplashScreen(SplashScreen):
    """ 自定义启动画面，隐藏窗口控制按钮 """

    def __init__(self, icon, parent=None, enableShadow=True):
        super().__init__(icon, parent, enableShadow)
        
        # 使用getattr安全地访问按钮属性并隐藏它们
        min_btn = getattr(self.titleBar, 'minBtn', None)
        if min_btn:
            min_btn.hide()
            
        max_btn = getattr(self.titleBar, 'maxBtn', None)
        if max_btn:
            max_btn.hide()
            
        close_btn = getattr(self.titleBar, 'closeBtn', None)
        if close_btn:
            close_btn.hide()
        
        # 从布局中移除按钮（如果存在hBoxLayout）
        h_box_layout = getattr(self.titleBar, 'hBoxLayout', None)
        if h_box_layout:
            if min_btn:
                h_box_layout.removeWidget(min_btn)
            if max_btn:
                h_box_layout.removeWidget(max_btn)
            if close_btn:
                h_box_layout.removeWidget(close_btn)


class Widget(QWidget):

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = QLabel(text, self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignmentFlag.AlignCenter)
        self.setObjectName(text.replace(' ', '-'))


class Window(FluentWindow):

    def __init__(self):
        super().__init__()
        
        # 设置自定义标题栏
        self.setTitleBar(CustomTitleBar(self))
        
        self.initWindow()

        # 不硬编码主题，使用配置文件或系统主题
        from qfluentwidgets import setTheme
        from configs.config import cfg
        setTheme(cfg.themeMode.value)

        # 创建系统主题监听器（用于跟随系统设置）
        self.themeListener = SystemThemeListener(self)

        # 创建所有界面
        self.homeInterface = HomeInterface(self)  # 使用炫酷的首页界面
        self.appInterface = AppCardInterface(self)  # 使用应用卡片界面
        self.settingInterface = SettingInterface(self)  # 设置界面
        
        # GIS工作流、自动化工具和新闻分析器界面现在在initNavigation中创建

        # 启用 acrylic 效果
        self.navigationInterface.setAcrylicEnabled(True)

        # add items to navigation interface
        self.initNavigation()
        
        # 完成启动画面
        self.splashScreen.finish()

        # 启动主题监听器
        self.themeListener.start()
        
        # 监听主题变化，更新窗口背景
        cfg.themeChanged.connect(self._onThemeChanged)
        
        # 监听主题变化，更新标题样式
        cfg.themeChanged.connect(self.titleBar._updateTitleStyle)
        
        # 应用初始主题
        self._onThemeChanged()

    def initNavigation(self):
        self.addSubInterface(self.homeInterface, FIF.HOME, '主页')
        self.addSubInterface(self.appInterface, FIF.APPLICATION, '应用')
        
        # 直接创建GIS工作流界面，不再使用占位符
        from interfaces.gis_workflow_interface import GisWorkflowInterface
        self.gisWorkflowInterface = GisWorkflowInterface(self)
        self.addSubInterface(self.gisWorkflowInterface, FIF.GLOBE, 'GIS工作流')
        
        # 直接创建自动化工具界面，不再使用占位符
        from interfaces.automation_tool_interface import AutomationToolInterface
        self.automationToolInterface = AutomationToolInterface(self)
        self.addSubInterface(self.automationToolInterface, FIF.FIT_PAGE, '自动化工具')
        
        # 直接创建新闻分析器界面，不再使用占位符
        from interfaces.news_analyzer_interface import NewsAnalyzerInterface
        self.newsAnalyzerInterface = NewsAnalyzerInterface(self)
        self.addSubInterface(self.newsAnalyzerInterface, FIF.MESSAGE, '新闻分析器')

        # 添加设置界面
        self.addSubInterface(self.settingInterface, FIF.SETTING, '设置', NavigationItemPosition.BOTTOM)
        
        self.navigationInterface.addItem(
            routeKey='Help',
            icon=FIF.HELP,
            text='帮助',
            onClick=self.showMessageBox,
            selectable=False,
            position=NavigationItemPosition.BOTTOM,
        )

    def initWindow(self):
        # 设置窗口最小大小和初始大小
        self.setMinimumSize(1200, 800)
        self.resize(1200, 800)
        
        # 使用本地图标，避免资源路径问题，加快启动速度
        self.setWindowIcon(QIcon('logo.ico'))
        self.setWindowTitle(f'知秋工作平台 v{VERSION}')
        
        # 创建自定义启动画面（隐藏控制按钮）
        self.splashScreen = CustomSplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(106, 106))
        self.splashScreen.raise_()

        desktop = QApplication.screens()[0].availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)

        # 默认以还原大小显示窗口（避免显示过程中看到窗口控制按钮）
        self.show()
        QApplication.processEvents()
        
        # 应用配置中的 Mica 效果设置 - 延迟应用
        from configs.config import cfg
        QTimer.singleShot(100, lambda: self.setMicaEffectEnabled(cfg.get(cfg.micaEnabled)))

        # 延迟收拢导航栏，确保布局完成后再收拢
        QTimer.singleShot(100, self._collapseNavigation)

    def _collapseNavigation(self):
        """ 延迟收拢导航栏 """
        self.navigationInterface.setExpandWidth(300)  # 设置展开宽度
        self.navigationInterface.panel.collapse()  # 收拢导航栏

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, 'splashScreen'):
            self.splashScreen.resize(self.size())
    
    def showNormal(self):
        """重写showNormal方法，确保还原时适配控件和面板到窗口宽高"""
        # 获取当前窗口状态
        current_state = self.windowState()
        
        # 检查是否从最大化状态还原
        if current_state & Qt.WindowState.WindowMaximized:
            # 先获取最大化前的尺寸，如果有记录的话
            # 调用父类方法执行实际还原操作
            super().showNormal()
            
            # 强制重新调整布局，确保控件适配还原后的窗口大小
            self.adjustLayoutOnWindowStateChanged(False)  # False表示从最大化状态还原
        else:
            # 普通还原操作
            super().showNormal()
            
            # 调整布局
            self.adjustLayoutOnWindowStateChanged(False)
    
    def adjustLayoutOnWindowStateChanged(self, is_maximized):
        """
        当窗口状态变化时调整布局
        
        Args:
            is_maximized: 窗口是否处于最大化状态
        """
        # 设置导航栏宽度
        if is_maximized:
            self.navigationInterface.setExpandWidth(220)  # 最大化时展开更多
        else:
            self.navigationInterface.setExpandWidth(180)  # 还原状态时稍微缩小
            
        # 调整活动界面布局
        current_interface = self.stackedWidget.currentWidget()
        if hasattr(current_interface, 'adjustLayout'):
            current_interface.adjustLayout(is_maximized)
    
    def resizeEvent(self, e):
        """重写resizeEvent，处理窗口大小变化时的布局调整"""
        super().resizeEvent(e)
        
        # 检查是否有启动画面需要调整大小
        if hasattr(self, 'splashScreen'):
            self.splashScreen.resize(self.size())
        
        # 检查当前窗口状态
        is_maximized = bool(self.windowState() & Qt.WindowState.WindowMaximized)
        
        # 调用布局调整方法
        self.adjustLayoutOnWindowStateChanged(is_maximized)
    
    def showMaximized(self):
        """重写showMaximized方法，添加最大化状态的布局适配"""
        super().showMaximized()
        # 通知布局调整
        self.adjustLayoutOnWindowStateChanged(True)  # True表示最大化状态

    def switchTo(self, interface):
        """重写switchTo方法，实现页面切换资源管理"""
        # 获取当前正在显示的界面
        current_widget = self.stackedWidget.currentWidget()
        
        # 触发hideEvent来清理资源
        if current_widget and hasattr(current_widget, 'hideEvent'):
            from PyQt6.QtGui import QHideEvent
            current_widget.hideEvent(QHideEvent())
        
        # 调用父类方法切换界面
        super().switchTo(interface)
    
    def _onThemeChanged(self):
        """主题变化时更新窗口背景和样式"""
        # FluentWindow会自动处理背景色，这里只需要触发重绘
        self.update()
        
        # 通知标题栏更新主题
        if hasattr(self, 'titleBar'):
            titleBar = self.titleBar
            update_theme_method = getattr(titleBar, '_updateTheme', None)
            if update_theme_method is not None:
                update_theme_method()
        
        # 通知GIS工作流界面更新主题
        if hasattr(self, 'gisWorkflowInterface'):
            gis_workflow = self.gisWorkflowInterface
            update_theme_method = getattr(gis_workflow, 'updateTheme', None)
            if update_theme_method is not None:
                update_theme_method()
        
        # 通知新闻分析器界面更新主题
        if hasattr(self, 'newsAnalyzerInterface'):
            news_analyzer = self.newsAnalyzerInterface
            update_theme_method = getattr(news_analyzer, 'updateTheme', None)
            if update_theme_method is not None:
                update_theme_method()
        

    
    def closeEvent(self, a0):
        # 停止主题监听器
        self.themeListener.terminate()
        self.themeListener.deleteLater()
        super().closeEvent(a0)

    def showMessageBox(self):
        w = MessageBox(
            '支持作者🥰',
            '个人开发不易，如果这个项目帮助到了您，可以考虑请作者喝一瓶快乐水🥤。您的支持就是作者开发和维护项目的动力🚀',
            self
        )
        w.yesButton.setText('来啦老弟')
        w.cancelButton.setText('下次一定')

        if w.exec():
            QDesktopServices.openUrl(QUrl("https://afdian.net/a/zhiyiYo"))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Window()
    # w.show()  # 已在 initWindow 中调用，无需重复
    app.exec()