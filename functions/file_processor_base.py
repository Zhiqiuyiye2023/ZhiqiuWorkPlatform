"""
文件处理功能基类
作者: 知秋一叶
版本号: 0.0.5
"""

from PyQt6.QtWidgets import (QHBoxLayout, QVBoxLayout, QPushButton, QLineEdit, 
                            QTextEdit, QFileDialog, QLabel, QComboBox, QTableWidget, 
                            QTableWidgetItem, QHeaderView, QProgressBar, QWidget)
from PyQt6.QtCore import Qt
from qfluentwidgets import (BodyLabel, PushButton, ComboBox, MessageBox, 
                           InfoBar, InfoBarPosition, LineEdit, TextEdit, PrimaryPushButton)
from .base_function import BaseFunction
from .processor import FileBatchProcessor


class BaseFileProcessorFunction(BaseFunction):
    """文件处理功能基类"""
    
    def __init__(self, title: str, description: str, parent=None):
        super().__init__(title, description, parent)
        self.processor = FileBatchProcessor()
        
    def browse_directory(self, line_edit):
        """浏览目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择目录")
        if directory:
            line_edit.setText(directory)
            
    def browse_file(self, line_edit, file_filter="所有文件 (*.*)", allow_dir=False):
        """浏览文件，支持选择目录
        allow_dir: 是否允许选择目录
        """
        if allow_dir:
            file_path = QFileDialog.getExistingDirectory(self, "选择文件或目录")
        else:
            file_path, _ = QFileDialog.getOpenFileName(self, "选择文件", "", file_filter)
        
        if file_path:
            line_edit.setText(file_path)
            
    def browse_file_or_dir(self, line_edit, file_filter="所有文件 (*.*)"):
        """浏览文件或目录"""
        options = QFileDialog.Option.DontResolveSymlinks | QFileDialog.Option.ShowDirsOnly
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文件或目录", "", file_filter, options=options
        )
        if file_path:
            line_edit.setText(file_path)
            
    def show_info(self, title, content):
        """显示信息提示"""
        InfoBar.info(
            title=title,
            content=content,
            parent=self,
            duration=2000
        )
        
    def show_success(self, title, content):
        """显示成功提示"""
        InfoBar.success(
            title=title,
            content=content,
            parent=self,
            duration=2000
        )
        
    def show_warning(self, title, content):
        """显示警告提示"""
        InfoBar.warning(
            title=title,
            content=content,
            parent=self,
            duration=2000
        )
        
    def show_error(self, title, content):
        """显示错误提示"""
        InfoBar.error(
            title=title,
            content=content,
            parent=self,
            duration=3000
        )