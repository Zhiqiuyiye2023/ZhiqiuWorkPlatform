"""
移动复制功能对话框
作者: 知秋一叶
版本号: 0.0.5
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, 
                            QTextEdit, QFileDialog, QLabel)
from qfluentwidgets import (BodyLabel, PushButton, MessageBox, 
                           InfoBar, InfoBarPosition)
from .base_dialog import BaseFileProcessDialog
from functions.processor import FileBatchProcessor


class MoveCopyDialog(BaseFileProcessDialog):
    """移动复制功能对话框"""
    
    def __init__(self, parent=None):
        super().__init__("移动复制文件和文件夹", parent)
        self.processor = FileBatchProcessor()
        self.setup_ui()
    
    def setup_ui(self):
        """设置界面"""
        # 路径选择区域
        source_layout = QHBoxLayout()
        self.source_label = BodyLabel("原始路径:")
        self.source_edit = QLineEdit()
        self.source_edit.setPlaceholderText("请选择源目录")
        self.source_edit.setFixedHeight(35)  # 增加高度
        self.source_browse_button = PushButton("浏览")
        self.source_browse_button.setFixedHeight(35)
        
        source_layout.addWidget(self.source_label)
        source_layout.addWidget(self.source_edit)
        source_layout.addWidget(self.source_browse_button)
        self.addContentLayout(source_layout)
        
        target_layout = QHBoxLayout()
        self.target_label = BodyLabel("目标路径:")
        self.target_edit = QLineEdit()
        self.target_edit.setPlaceholderText("请选择目标目录")
        self.target_edit.setFixedHeight(35)  # 增加高度
        self.target_browse_button = PushButton("浏览")
        self.target_browse_button.setFixedHeight(35)
        
        target_layout.addWidget(self.target_label)
        target_layout.addWidget(self.target_edit)
        target_layout.addWidget(self.target_browse_button)
        self.addContentLayout(target_layout)
        
        # 提示标签
        self.tip_label = BodyLabel("📢 请填写需要移动的文件或文件夹名用于过滤~~")
        self.tip_label.setStyleSheet("color: orange; font-weight: bold;")
        self.addContentWidget(self.tip_label)
        
        # 文本输入区域
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("请输入需要移动或复制的文件/文件夹名称，每行一个")
        self.text_edit.setFixedHeight(150)
        self.addContentWidget(self.text_edit)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        self.copy_folder_button = PushButton("复制文件夹")
        self.copy_folder_button.setFixedHeight(35)
        self.move_folder_button = PushButton("移动文件夹")
        self.move_folder_button.setFixedHeight(35)
        self.copy_file_button = PushButton("复制文件")
        self.copy_file_button.setFixedHeight(35)
        self.move_file_button = PushButton("移动文件")
        self.move_file_button.setFixedHeight(35)
        self.create_folder_button = PushButton("批量创建文件夹")
        self.create_folder_button.setFixedHeight(35)
        
        self.copy_folder_button.clicked.connect(self.copy_folder)
        self.move_folder_button.clicked.connect(self.move_folder)
        self.copy_file_button.clicked.connect(self.copy_file)
        self.move_file_button.clicked.connect(self.move_file)
        self.create_folder_button.clicked.connect(self.create_folders)
        
        button_layout.addWidget(self.copy_folder_button)
        button_layout.addWidget(self.move_folder_button)
        button_layout.addWidget(self.copy_file_button)
        button_layout.addWidget(self.move_file_button)
        button_layout.addWidget(self.create_folder_button)
        self.addContentLayout(button_layout)
    
    def browse_directory(self, line_edit):
        """浏览目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择目录")
        if directory:
            line_edit.setText(directory)
    
    def copy_folder(self):
        """复制文件夹"""
        try:
            source_path = self.source_edit.text()
            target_path = self.target_edit.text()
            folder_names = self.text_edit.toPlainText()
            
            if not source_path or not target_path:
                InfoBar.warning(
                    title='警告',
                    content='请输入源路径和目标路径',
                    parent=self,
                    duration=2000
                )
                return
            
            if not folder_names.strip():
                InfoBar.warning(
                    title='警告',
                    content='请输入要复制的文件夹名称',
                    parent=self,
                    duration=2000
                )
                return
            
            copied_folders = self.processor.copy_folder_method(source_path, target_path, folder_names)
            InfoBar.success(
                title='成功',
                content=f'文件夹复制完成，共复制 {len(copied_folders)} 个文件夹',
                parent=self,
                duration=2000
            )
        except Exception as e:
            InfoBar.error(
                title='错误',
                content=f'复制文件夹时出错: {str(e)}',
                parent=self,
                duration=3000
            )
    
    def move_folder(self):
        """移动文件夹"""
        try:
            source_path = self.source_edit.text()
            target_path = self.target_edit.text()
            folder_names = self.text_edit.toPlainText()
            
            if not source_path or not target_path:
                InfoBar.warning(
                    title='警告',
                    content='请输入源路径和目标路径',
                    parent=self,
                    duration=2000
                )
                return
            
            if not folder_names.strip():
                InfoBar.warning(
                    title='警告',
                    content='请输入要移动的文件夹名称',
                    parent=self,
                    duration=2000
                )
                return
            
            moved_folders = self.processor.move_folder_method(source_path, target_path, folder_names)
            InfoBar.success(
                title='成功',
                content=f'文件夹移动完成，共移动 {len(moved_folders)} 个文件夹',
                parent=self,
                duration=2000
            )
        except Exception as e:
            InfoBar.error(
                title='错误',
                content=f'移动文件夹时出错: {str(e)}',
                parent=self,
                duration=3000
            )
    
    def copy_file(self):
        """复制文件"""
        try:
            source_path = self.source_edit.text()
            target_path = self.target_edit.text()
            file_names = self.text_edit.toPlainText()
            
            if not source_path or not target_path:
                InfoBar.warning(
                    title='警告',
                    content='请输入源路径和目标路径',
                    parent=self,
                    duration=2000
                )
                return
            
            if not file_names.strip():
                InfoBar.warning(
                    title='警告',
                    content='请输入要复制的文件名称',
                    parent=self,
                    duration=2000
                )
                return
            
            copied_files = self.processor.copy_file_method(source_path, target_path, file_names)
            InfoBar.success(
                title='成功',
                content=f'文件复制完成，共复制 {len(copied_files)} 个文件',
                parent=self,
                duration=2000
            )
        except Exception as e:
            InfoBar.error(
                title='错误',
                content=f'复制文件时出错: {str(e)}',
                parent=self,
                duration=3000
            )
    
    def move_file(self):
        """移动文件"""
        try:
            source_path = self.source_edit.text()
            target_path = self.target_edit.text()
            file_names = self.text_edit.toPlainText()
            
            if not source_path or not target_path:
                InfoBar.warning(
                    title='警告',
                    content='请输入源路径和目标路径',
                    parent=self,
                    duration=2000
                )
                return
            
            if not file_names.strip():
                InfoBar.warning(
                    title='警告',
                    content='请输入要移动的文件名称',
                    parent=self,
                    duration=2000
                )
                return
            
            moved_files = self.processor.move_file_method(source_path, target_path, file_names)
            InfoBar.success(
                title='成功',
                content=f'文件移动完成，共移动 {len(moved_files)} 个文件',
                parent=self,
                duration=2000
            )
        except Exception as e:
            InfoBar.error(
                title='错误',
                content=f'移动文件时出错: {str(e)}',
                parent=self,
                duration=3000
            )
    
    def create_folders(self):
        """批量创建文件夹"""
        try:
            target_path = self.target_edit.text()
            folder_names = self.text_edit.toPlainText()
            
            if not target_path:
                InfoBar.warning(
                    title='警告',
                    content='请输入目标路径',
                    parent=self,
                    duration=2000
                )
                return
            
            if not folder_names.strip():
                InfoBar.warning(
                    title='警告',
                    content='请输入文件夹名称',
                    parent=self,
                    duration=2000
                )
                return
            
            created_folders = self.processor.batch_create_folders_old(target_path, folder_names)
            InfoBar.success(
                title='成功',
                content=f'文件夹创建完成，共创建 {len(created_folders)} 个文件夹',
                parent=self,
                duration=2000
            )
        except Exception as e:
            InfoBar.error(
                title='错误',
                content=f'创建文件夹时出错: {str(e)}',
                parent=self,
                duration=3000
            )