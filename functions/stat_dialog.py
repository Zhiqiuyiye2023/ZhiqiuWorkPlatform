"""
文件统计功能对话框
作者: 知秋一叶
版本号: 0.0.5
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, 
                            QTableWidgetItem, QHeaderView, QLabel, QFileDialog, QApplication)
from qfluentwidgets import (BodyLabel, PushButton, ComboBox, MessageBox, 
                           InfoBar, InfoBarPosition, TableWidget)
from .base_dialog import BaseFileProcessDialog
from functions.processor import FileBatchProcessor
from qfluentwidgets import isDarkTheme


class FileStatDialog(BaseFileProcessDialog):
    """文件统计功能对话框"""
    
    def __init__(self, parent=None):
        super().__init__("文件与文件夹统计", parent)
        self.processor = FileBatchProcessor()
        self.setup_ui()
        # 初始化时更新一次样式
        self._updateLineEditStyle()
        self._updateTableStyle()
    
    def setup_ui(self):
        """设置界面"""
        # 路径选择区域
        path_layout = QHBoxLayout()
        self.path_label = BodyLabel("目录路径:")
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("请选择要统计的目录")
        self.browse_button = PushButton("浏览")
        self.browse_button.clicked.connect(self.browse_directory)
        
        path_layout.addWidget(self.path_label)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.browse_button)
        self.addContentLayout(path_layout)
        
        # 功能按钮区域
        button_layout = QHBoxLayout()
        self.stat_files_button = PushButton("统计文件名")
        self.stat_folders_button = PushButton("统计文件夹名")
        self.stat_empty_button = PushButton("统计空文件夹")
        self.stat_contents_button = PushButton("统计文件夹内容数量")
        self.organize_button = PushButton("将文件放入同名文件夹")
        
        self.stat_files_button.clicked.connect(self.stat_files)
        self.stat_folders_button.clicked.connect(self.stat_folders)
        self.stat_empty_button.clicked.connect(self.stat_empty_folders)
        self.stat_contents_button.clicked.connect(self.stat_folder_contents)
        self.organize_button.clicked.connect(self.organize_files)
        
        button_layout.addWidget(self.stat_files_button)
        button_layout.addWidget(self.stat_folders_button)
        button_layout.addWidget(self.stat_empty_button)
        button_layout.addWidget(self.stat_contents_button)
        button_layout.addWidget(self.organize_button)
        self.addContentLayout(button_layout)
        
        # 统计结果标签
        self.stat_label = BodyLabel("共计 0 行")
        self.addContentWidget(self.stat_label)
        
        # 结果显示表格
        self.result_table = TableWidget()
        self.result_table.setBorderVisible(True)
        self.result_table.setColumnCount(1)
        self.result_table.setHorizontalHeaderLabels(["名称"])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.result_table.setAlternatingRowColors(True)
        self.addContentWidget(self.result_table)
        
        # 操作按钮区域
        action_layout = QHBoxLayout()
        self.copy_button = PushButton("拷贝统计内容")
        self.clear_button = PushButton("清空结果")
        
        self.copy_button.clicked.connect(self.copy_results)
        self.clear_button.clicked.connect(self.clear_results)
        
        action_layout.addWidget(self.copy_button)
        action_layout.addWidget(self.clear_button)
        action_layout.addStretch()
        self.addContentLayout(action_layout)
        
        # 设置样式
        self._updateLineEditStyle()
        
        # 监听主题变化以更新样式
        from qfluentwidgets import qconfig
        qconfig.themeChangedFinished.connect(self._onThemeChanged)
    
    def _updateLineEditStyle(self):
        """更新输入框样式以匹配主题和按钮高度"""
        # 确保输入框控件存在
        if not hasattr(self, 'path_edit'):
            return
            
        if isDarkTheme():
            # 深色主题下的输入框样式
            line_edit_style = """
                QLineEdit {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    border: 1px solid #3d3d3d;
                    border-radius: 4px;
                    padding: 5px;
                    font-size: 13px;
                    min-height: 30px;
                }
                QLineEdit:focus {
                    border: 1px solid #0078d7;
                }
                QLineEdit:disabled {
                    background-color: #252525;
                    color: #666666;
                }
            """
        else:
            # 浅色主题下的输入框样式
            line_edit_style = """
                QLineEdit {
                    background-color: #ffffff;
                    color: #000000;
                    border: 1px solid #d0d0d0;
                    border-radius: 4px;
                    padding: 5px;
                    font-size: 13px;
                    min-height: 30px;
                }
                QLineEdit:focus {
                    border: 1px solid #0078d7;
                }
                QLineEdit:disabled {
                    background-color: #f0f0f0;
                    color: #999999;
                }
            """
        self.path_edit.setStyleSheet(line_edit_style)
    
    def _updateTableStyle(self):
        """更新表格样式以提高可读性"""
        # 确保表格控件存在
        if not hasattr(self, 'result_table'):
            return
            
        if isDarkTheme():
            # 深色主题下的表格样式
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
            # 浅色主题下的表格样式
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
                QHeaderView::section:vertical {
                    border-top: none;
                }
                QTableCornerButton::section {
                    background-color: #f5f5f5;
                    border: 1px solid #e0e0e0;
                }
            """
        self.result_table.setStyleSheet(table_style)
    
    def _onThemeChanged(self):
        """主题变化时更新样式"""
        self._updateLineEditStyle()
    
    def browse_directory(self):
        """浏览目录"""
        # 确保输入框控件存在
        if not hasattr(self, 'path_edit'):
            return
            
        directory = QFileDialog.getExistingDirectory(self, "选择目录")
        if directory:
            self.path_edit.setText(directory)
    
    def stat_files(self):
        """统计文件名"""
        try:
            # 确保输入框控件存在
            if not hasattr(self, 'path_edit'):
                InfoBar.warning(
                    title='警告',
                    content='输入框控件未初始化',
                    parent=self,
                    duration=2000
                )
                return
                
            folder_path = self.path_edit.text()
            if not folder_path:
                InfoBar.warning(
                    title='警告',
                    content='请输入目录路径',
                    parent=self,
                    duration=2000
                )
                return
            
            files = self.processor.stat_files(folder_path)
            self.display_results(files)
            InfoBar.success(
                title='成功',
                content=f'统计完成，共找到 {len(files)} 个文件',
                parent=self,
                duration=2000
            )
        except Exception as e:
            InfoBar.error(
                title='错误',
                content=f'统计文件时出错: {str(e)}',
                parent=self,
                duration=3000
            )
    
    def stat_folders(self):
        """统计文件夹名"""
        try:
            # 确保输入框控件存在
            if not hasattr(self, 'path_edit'):
                InfoBar.warning(
                    title='警告',
                    content='输入框控件未初始化',
                    parent=self,
                    duration=2000
                )
                return
                
            folder_path = self.path_edit.text()
            if not folder_path:
                InfoBar.warning(
                    title='警告',
                    content='请输入目录路径',
                    parent=self,
                    duration=2000
                )
                return
            
            folders = self.processor.stat_folders(folder_path)
            self.display_results(folders)
            InfoBar.success(
                title='成功',
                content=f'统计完成，共找到 {len(folders)} 个文件夹',
                parent=self,
                duration=2000
            )
        except Exception as e:
            InfoBar.error(
                title='错误',
                content=f'统计文件夹时出错: {str(e)}',
                parent=self,
                duration=3000
            )
    
    def stat_empty_folders(self):
        """统计空文件夹"""
        try:
            # 确保输入框控件存在
            if not hasattr(self, 'path_edit'):
                InfoBar.warning(
                    title='警告',
                    content='输入框控件未初始化',
                    parent=self,
                    duration=2000
                )
                return
                
            folder_path = self.path_edit.text()
            if not folder_path:
                InfoBar.warning(
                    title='警告',
                    content='请输入目录路径',
                    parent=self,
                    duration=2000
                )
                return
            
            empty_folders = self.processor.stat_empty_folders(folder_path)
            self.display_results(empty_folders)
            InfoBar.success(
                title='成功',
                content=f'统计完成，共找到 {len(empty_folders)} 个空文件夹',
                parent=self,
                duration=2000
            )
        except Exception as e:
            InfoBar.error(
                title='错误',
                content=f'统计空文件夹时出错: {str(e)}',
                parent=self,
                duration=3000
            )
    
    def stat_folder_contents(self):
        """统计文件夹内容数量"""
        try:
            # 确保输入框控件存在
            if not hasattr(self, 'path_edit'):
                InfoBar.warning(
                    title='警告',
                    content='输入框控件未初始化',
                    parent=self,
                    duration=2000
                )
                return
                
            folder_path = self.path_edit.text()
            if not folder_path:
                InfoBar.warning(
                    title='警告',
                    content='请输入目录路径',
                    parent=self,
                    duration=2000
                )
                return
            
            folder_contents = self.processor.stat_folder_contents(folder_path)
            self.display_results(folder_contents)
            InfoBar.success(
                title='成功',
                content=f'统计完成',
                parent=self,
                duration=2000
            )
        except Exception as e:
            InfoBar.error(
                title='错误',
                content=f'统计文件夹内容数量时出错: {str(e)}',
                parent=self,
                duration=3000
            )
    
    def organize_files(self):
        """将文件放入同名文件夹"""
        try:
            # 确保输入框控件存在
            if not hasattr(self, 'path_edit'):
                InfoBar.warning(
                    title='警告',
                    content='输入框控件未初始化',
                    parent=self,
                    duration=2000
                )
                return
                
            folder_path = self.path_edit.text()
            if not folder_path:
                InfoBar.warning(
                    title='警告',
                    content='请输入目录路径',
                    parent=self,
                    duration=2000
                )
                return
            
            self.processor.organize_files_by_name(folder_path)
            InfoBar.success(
                title='成功',
                content='文件整理完成',
                parent=self,
                duration=2000
            )
        except Exception as e:
            InfoBar.error(
                title='错误',
                content=f'整理文件时出错: {str(e)}',
                parent=self,
                duration=3000
            )
    
    def display_results(self, items):
        """显示结果"""
        # 确保表格控件存在
        if not hasattr(self, 'result_table'):
            return
            
        self.result_table.setRowCount(len(items))
        for i, item in enumerate(items):
            # 名称列
            name_item = QTableWidgetItem(str(item))
            self.result_table.setItem(i, 0, name_item)
        
        # 更新统计标签
        if hasattr(self, 'stat_label'):
            self.stat_label.setText(f"共计 {len(items)} 行")
    
    def copy_results(self):
        """拷贝统计内容"""
        try:
            # 确保表格控件存在
            if not hasattr(self, 'result_table'):
                InfoBar.warning(
                    title='警告',
                    content='表格控件未初始化',
                    parent=self,
                    duration=2000
                )
                return
                
            items = []
            for i in range(self.result_table.rowCount()):
                item = self.result_table.item(i, 1)
                if item:
                    items.append(item.text())
            
            if items:
                clipboard = QApplication.clipboard()
                if clipboard:
                    clipboard.setText('\n'.join(items))
                    InfoBar.success(
                        title='成功',
                        content='统计内容已复制到剪贴板',
                        parent=self,
                        duration=2000
                    )
                else:
                    InfoBar.warning(
                        title='警告',
                        content='无法访问剪贴板',
                        parent=self,
                        duration=2000
                    )
            else:
                InfoBar.warning(
                    title='警告',
                    content='没有可复制的内容',
                    parent=self,
                    duration=2000
                )
        except Exception as e:
            InfoBar.error(
                title='错误',
                content=f'拷贝内容时出错: {str(e)}',
                parent=self,
                duration=3000
            )
    
    def clear_results(self):
        """清空结果"""
        # 确保表格控件存在
        if not hasattr(self, 'result_table'):
            return
        self.result_table.setRowCount(0)
        
        # 重置统计标签
        if hasattr(self, 'stat_label'):
            self.stat_label.setText("共计 0 行")