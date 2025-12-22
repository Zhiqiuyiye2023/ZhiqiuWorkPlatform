# coding:utf-8
"""
功能模块基类
所有功能模块都继承自此基类
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette
from qfluentwidgets import PrimaryPushButton, TransparentPushButton, BodyLabel, StateToolTip
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import isDarkTheme, Theme, setTheme
from configs.config import cfg


class BaseFunction(QWidget):
    """功能模块基类"""
    
    # 状态信号
    started = pyqtSignal()  # 开始执行
    finished = pyqtSignal(bool, str)  # 执行完成(成功/失败, 消息)
    progress = pyqtSignal(int, str)  # 进度更新(百分比, 状态文本)
    
    def __init__(self, title: str, description: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.description = description
        self.stateTooltip = None
        self._running = False
        self._status_indicator = None  # 状态指示灯
        self._blink_timer = None  # 闪烁定时器
        
        # 创建主布局
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(30, 20, 30, 30)
        self.mainLayout.setSpacing(20)
        
        # 添加标题和说明
        self._addHeader()
        
        # 添加功能说明（子类可重写）
        self._addDescription()
        
        # 功能区域容器（子类在这里添加控件）
        self.contentWidget = QWidget(self)
        self.contentLayout = QVBoxLayout(self.contentWidget)
        self.contentLayout.setContentsMargins(0, 0, 0, 0)
        self.contentLayout.setSpacing(15)
        self.mainLayout.addWidget(self.contentWidget)
        
        # 按钮区域
        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setSpacing(10)
        self.mainLayout.addLayout(self.buttonLayout)
        
        # 添加弹性空间
        self.mainLayout.addStretch(1)
        
        # 监听主题变化
        cfg.themeChanged.connect(self._onThemeChanged)
        
        # 应用初始主题
        self._onThemeChanged()
        
    def _onThemeChanged(self):
        """主题变化时更新背景色"""
        if isDarkTheme():
            # 深色主题
            self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
            self.contentWidget.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        else:
            # 浅色主题
            self.setStyleSheet("background-color: #f3f3f3; color: #000000;")
            self.contentWidget.setStyleSheet("background-color: #f3f3f3; color: #000000;")
        
        # 更新标题和说明文本颜色
        for child in self.findChildren(QLabel):
            if isDarkTheme():
                child.setStyleSheet(child.styleSheet().replace("color: #000000;", "color: #ffffff;").replace("color: #0078D4;", "color: #00B4FF;"))
            else:
                child.setStyleSheet(child.styleSheet().replace("color: #ffffff;", "color: #000000;").replace("color: #00B4FF;", "color: #0078D4;"))
        
    def _addHeader(self):
        """添加标题区域，包含状态指示灯"""
        # 创建水平布局包含标题和状态灯
        headerLayout = QHBoxLayout()
        headerLayout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        headerLayout.setSpacing(15)
        
        # 添加标题
        headerLabel = QLabel(f"📋 {self.title}", self)
        headerLabel.setFont(QFont('Microsoft YaHei', 18, QFont.Weight.Bold))
        headerLabel.setStyleSheet("color: #0078D4; padding: 10px 0;")
        headerLayout.addWidget(headerLabel)
        
        # 添加状态指示灯
        self._status_indicator = QFrame(self)
        self._status_indicator.setFixedSize(20, 20)
        self._status_indicator.setStyleSheet("border-radius: 10px; background-color: #CCCCCC;")
        self._status_indicator.setToolTip("模块状态：未运行")
        headerLayout.addWidget(self._status_indicator)
        
        # 添加弹性空间
        headerLayout.addStretch(1)
        
        # 将水平布局添加到主布局
        self.mainLayout.addLayout(headerLayout)
    
    def _addDescription(self):
        """添加功能说明（子类可重写）"""
        if self.description:
            descLabel = QLabel(self.description, self)
            descLabel.setWordWrap(True)
            descLabel.setStyleSheet("""
                QLabel {
                    padding: 12px;
                    font-size: 13px;
                    background-color: rgba(0, 120, 212, 0.1);
                    border-left: 3px solid #0078D4;
                    border-radius: 4px;
                }
            """)
            self.mainLayout.addWidget(descLabel)
    
    def addExecuteButton(self, text: str = "开始执行", callback=None):
        """添加执行按钮"""
        button = PrimaryPushButton(text, self, FIF.SEND)
        button.setFixedHeight(36)
        if callback:
            button.clicked.connect(callback)
        else:
            button.clicked.connect(self.execute)
        self.buttonLayout.addWidget(button)
        self.buttonLayout.addStretch(1)
        return button
    
    def addCustomButton(self, text: str, icon=FIF.ADD, callback=None):
        """添加自定义按钮"""
        button = TransparentPushButton(text, self, icon)
        button.setFixedHeight(36)
        if callback:
            button.clicked.connect(callback)
        self.buttonLayout.addWidget(button)
        return button
    
    def showProgress(self, message: str = "正在处理..."):
        """显示进度提示"""
        if not self.stateTooltip:
            self.stateTooltip = StateToolTip('执行中', message, self)
            self.stateTooltip.move(self.width() // 2 - 100, 30)
            self.stateTooltip.show()
        self._running = True
        # 更新状态指示灯为运行中（绿色闪烁）
        self._update_status_indicator("running", message)
        self.started.emit()
    
    def hideProgress(self):
        """隐藏进度提示"""
        if self.stateTooltip:
            self.stateTooltip.setContent("处理完成!")
            self.stateTooltip.setState(True)
            self.stateTooltip = None
        self._running = False
        # 停止闪烁并恢复初始状态
        self._stop_blinking()
        self._update_status_indicator("idle", "未运行")
    
    def showSuccess(self, message: str):
        """显示成功消息"""
        self.hideProgress()
        # 更新状态指示灯为成功状态（绿色）
        self._update_status_indicator("success", "执行成功")
        # 3秒后恢复初始状态
        QTimer.singleShot(3000, lambda: self._update_status_indicator("idle", "未运行"))
        self.finished.emit(True, message)
        
        # 显示成功对话框
        from qfluentwidgets import MessageBox
        msg_box = MessageBox(self.title, message, self)
        msg_box.exec()
    
    def showError(self, message: str):
        """显示错误消息"""
        if self.stateTooltip:
            self.stateTooltip.setContent("处理失败!")
            self.stateTooltip.setState(False)
            self.stateTooltip = None
        self._running = False
        # 更新状态指示灯为错误状态（红色）
        self._update_status_indicator("error", "执行失败")
        # 5秒后恢复初始状态
        QTimer.singleShot(5000, lambda: self._update_status_indicator("idle", "未运行"))
        self.finished.emit(False, message)
        
        # 显示错误对话框
        from qfluentwidgets import MessageBox
        msg_box = MessageBox(self.title, message, self)
        msg_box.exec()
    
    def updateProgress(self, percent: int, status: str = ""):
        """更新进度"""
        try:
            self.progress.emit(percent, status)
            # 如果有状态消息，更新状态指示灯的工具提示
            if status and hasattr(self, '_status_indicator') and self._status_indicator is not None:
                if self._status_indicator.toolTip() != f"执行中: {status}":
                    self._status_indicator.setToolTip(f"执行中: {status}")
        except RuntimeError:
            # 捕获UI元素已被删除的错误
            pass
    
    def _update_status_indicator(self, state: str, tooltip: str):
        """
        更新状态指示灯的状态
        
        参数:
            state: 状态 - "idle"(灰色), "running"(绿色闪烁), "success"(绿色), "error"(红色)
            tooltip: 鼠标悬停提示文本
        """
        try:
            if not hasattr(self, '_status_indicator') or self._status_indicator is None:
                return
            
            self._stop_blinking()
            
            if state == "idle":
                self._status_indicator.setStyleSheet("border-radius: 10px; background-color: #CCCCCC;")
            elif state == "running":
                # 开始绿色闪烁效果
                self._status_indicator.setStyleSheet("border-radius: 10px; background-color: #00B42A;")
                self._blink_timer = QTimer(self)
                self._blink_timer.timeout.connect(self._blink)
                self._blink_timer.start(500)  # 500ms闪烁一次
            elif state == "success":
                self._status_indicator.setStyleSheet("border-radius: 10px; background-color: #00B42A;")
            elif state == "error":
                self._status_indicator.setStyleSheet("border-radius: 10px; background-color: #F53F3F;")
            
            self._status_indicator.setToolTip(f"模块状态：{tooltip}")
        except RuntimeError:
            # 捕获UI元素已被删除的错误
            pass
    
    def _blink(self):
        """闪烁效果实现"""
        try:
            if not hasattr(self, '_status_indicator') or self._status_indicator is None or not self._running:
                self._stop_blinking()
                return
            
            current_style = self._status_indicator.styleSheet()
            if "#00B42A" in current_style:
                # 切换为较浅的绿色
                self._status_indicator.setStyleSheet("border-radius: 10px; background-color: #4CD964;")
            else:
                # 切换回正常绿色
                self._status_indicator.setStyleSheet("border-radius: 10px; background-color: #00B42A;")
        except RuntimeError:
            # 捕获UI元素已被删除的错误
            self._stop_blinking()
    
    def _stop_blinking(self):
        """停止闪烁效果"""
        if self._blink_timer and self._blink_timer.isActive():
            self._blink_timer.stop()
            self._blink_timer.deleteLater()
            self._blink_timer = None
    
    def execute(self):
        """执行功能（子类必须重写）"""
        raise NotImplementedError("子类必须实现 execute 方法")
    
    def validate(self) -> tuple[bool, str]:
        """验证输入参数（子类可重写）"""
        return True, ""
    
    def isRunning(self) -> bool:
        """检查是否正在运行"""
        return self._running
