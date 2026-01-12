# coding:utf-8
import sys
import os

# 版本号定义
VERSION = "1.0.2"
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
from PyQt6.QtWidgets import QLabel, QHBoxLayout, QVBoxLayout, QApplication, QWidget
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
                            RoundMenu, MenuAnimationType, InfoBar, InfoBarPosition)
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
        # 可以显示通知列表或其他功能
        InfoBar.info(
            title='通知',
            content='您有 0 条未读通知',
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self.window()
        )
    
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
            # 用户确认退出，关闭应用
            QApplication.quit()
    
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

        # create sub interface
        self.homeInterface = HomeInterface(self)  # 使用炫酷的首页界面
        self.appInterface = AppCardInterface(self)  # 使用应用卡片界面
        

        self.settingInterface = SettingInterface(self)
        
        # 加载GIS工作流界面
        from interfaces.gis_workflow_interface import GisWorkflowInterface
        self.gisWorkflowInterface = GisWorkflowInterface(self)
        
        # 加载自动化工具界面
        from interfaces.automation_tool_interface import AutomationToolInterface
        self.automationToolInterface = AutomationToolInterface(self)
        
        # 加载新闻分析器界面
        from interfaces.news_analyzer_interface import NewsAnalyzerInterface
        self.newsAnalyzerInterface = NewsAnalyzerInterface(self)

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
        
        # 添加GIS工作流界面
        self.addSubInterface(self.gisWorkflowInterface, FIF.GLOBE, 'GIS工作流')
        
        # 添加自动化工具界面
        self.addSubInterface(self.automationToolInterface, FIF.FIT_PAGE, '自动化工具')
        
        # 添加新闻分析器界面
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
        self.setWindowIcon(QIcon(':/qfluentwidgets/images/logo.png'))
        self.setWindowTitle(f'知秋工作平台 v{VERSION}')
        
        # 应用配置中的 Mica 效果设置
        self.setMicaEffectEnabled(cfg.get(cfg.micaEnabled))

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
            
        # 调用父类方法
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