"""
文件处理功能对话框基类
作者: 知秋一叶
版本号: 0.0.5
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QWidget, QLabel, QFrame)
from PyQt6.QtGui import QPalette
from qfluentwidgets import (BodyLabel, PrimaryPushButton, PushButton, 
                           ScrollArea, isDarkTheme, LineEdit, TextEdit)
from configs.config import cfg


class BaseFileProcessDialog(QDialog):
    """文件处理功能对话框基类"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(800, 600)
        self.setModal(True)
        
        # 创建主布局
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(20, 20, 20, 20)
        self.mainLayout.setSpacing(15)
        
        # 标题
        self.titleLabel = BodyLabel(title)
        self.titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.titleLabel.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        self.mainLayout.addWidget(self.titleLabel)
        
        # 内容区域
        self.contentArea = QFrame()
        self.contentLayout = QVBoxLayout(self.contentArea)
        self.contentLayout.setContentsMargins(15, 15, 15, 15)
        self.contentLayout.setSpacing(10)
        self.mainLayout.addWidget(self.contentArea)
        
        # 连接主题变化信号
        cfg.themeChanged.connect(self._onThemeChanged)
        
        # 应用初始主题
        self._onThemeChanged()
    
    def _onThemeChanged(self):
        """主题变化时更新样式"""
        if isDarkTheme():
            self.setStyleSheet("""
                QDialog {
                    background-color: #2d2d2d;
                }
                QFrame {
                    background-color: #323232;
                    border-radius: 8px;
                    border: 1px solid #3d3d3d;
                }
                QLineEdit, QTextEdit, QComboBox {
                    background-color: #3d3d3d;
                    color: #ffffff;
                    border: 1px solid #555555;
                    border-radius: 4px;
                    padding: 8px;
                }
                QLineEdit:disabled, QTextEdit:disabled, QComboBox:disabled {
                    background-color: #2d2d2d;
                    color: #888888;
                }
            """)
            self.titleLabel.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px; color: white;")
        else:
            self.setStyleSheet("""
                QDialog {
                    background-color: #f3f3f3;
                }
                QFrame {
                    background-color: white;
                    border-radius: 8px;
                    border: 1px solid #e0e0e0;
                }
                QLineEdit, QTextEdit, QComboBox {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    padding: 8px;
                }
                QLineEdit:disabled, QTextEdit:disabled, QComboBox:disabled {
                    background-color: #f0f0f0;
                    color: #999999;
                }
            """)
            self.titleLabel.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px; color: black;")
    
    def addContentWidget(self, widget):
        """添加内容控件"""
        self.contentLayout.addWidget(widget)
    
    def addContentLayout(self, layout):
        """添加内容布局"""
        self.contentLayout.addLayout(layout)
    
    def addStretch(self):
        """添加弹性空间"""
        self.contentLayout.addStretch()