"""
文件统计功能
作者: 知秋一叶
版本号: 0.0.5
"""

from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QPushButton, QLineEdit, QLabel, QTableWidgetItem, QHeaderView, QApplication
from qfluentwidgets import LineEdit, PushButton, TextEdit, TableWidget
from qfluentwidgets import FluentIcon as FIF
from .file_processor_base import BaseFileProcessorFunction
import os


class FileStatFunction(BaseFileProcessorFunction):
    """文件统计功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>"
            "统计指定目录下的文件和文件夹信息<br>"
            "支持多种统计方式，包括文件名、文件夹名、空文件夹等"
        )
        super().__init__("文件统计", description, parent)
        self._initUI()
    
    def _initUI(self):
        """初始化界面"""
        # 路径选择区域
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("目录路径:"))
        
        self.path_edit = LineEdit(self)
        self.path_edit.setPlaceholderText("请选择要统计的目录")
        
        self.browse_button = PushButton("浏览", self, FIF.FOLDER)
        self.browse_button.clicked.connect(lambda: self.browse_directory(self.path_edit))
        
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.browse_button)
        self.contentLayout.addLayout(path_layout)
        
        # 功能按钮区域
        button_layout = QHBoxLayout()
        self.stat_files_button = PushButton("统计文件名", self, FIF.DOCUMENT)
        self.stat_folders_button = PushButton("统计文件夹名", self, FIF.FOLDER)
        self.stat_empty_button = PushButton("统计空文件夹", self, FIF.ZIP_FOLDER)
        
        self.stat_files_button.clicked.connect(self.stat_files)
        self.stat_folders_button.clicked.connect(self.stat_folders)
        self.stat_empty_button.clicked.connect(self.stat_empty_folders)
        
        button_layout.addWidget(self.stat_files_button)
        button_layout.addWidget(self.stat_folders_button)
        button_layout.addWidget(self.stat_empty_button)
        self.contentLayout.addLayout(button_layout)
        
        # 统计结果标签
        self.stat_label = QLabel("共计 0 行")
        self.contentLayout.addWidget(self.stat_label)
        
        # 结果显示表格
        self.result_table = TableWidget(self)
        self.result_table.setBorderVisible(True)
        self.result_table.setColumnCount(1)
        self.result_table.setHorizontalHeaderLabels(["名称"])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setFixedHeight(200)
        self.contentLayout.addWidget(self.result_table)
        
        # 操作按钮区域
        action_layout = QHBoxLayout()
        self.copy_button = PushButton("拷贝统计内容", self, FIF.COPY)
        self.clear_button = PushButton("清空结果", self, FIF.DELETE)
        
        self.copy_button.clicked.connect(self.copy_results)
        self.clear_button.clicked.connect(self.clear_results)
        
        action_layout.addWidget(self.copy_button)
        action_layout.addWidget(self.clear_button)
        action_layout.addStretch()
        self.contentLayout.addLayout(action_layout)
    
    def validate(self) -> tuple[bool, str]:
        """验证输入"""
        if not self.path_edit.text():
            return False, "请选择目录路径"
        if not os.path.exists(self.path_edit.text()):
            return False, "目录路径不存在"
        return True, ""
    
    def stat_files(self):
        """统计文件名"""
        valid, message = self.validate()
        if not valid:
            self.show_error("错误", message)
            return
            
        try:
            self.showProgress("正在统计文件...")
            directory = self.path_edit.text()
            files = []
            
            for root, dirs, filenames in os.walk(directory):
                for filename in filenames:
                    files.append(os.path.join(root, filename))
            
            self.display_results(files)
            self.showSuccess("统计完成")
        except Exception as e:
            self.showError(f"统计失败: {str(e)}")
        finally:
            self.hideProgress()
    
    def stat_folders(self):
        """统计文件夹名"""
        valid, message = self.validate()
        if not valid:
            self.show_error("错误", message)
            return
            
        try:
            self.showProgress("正在统计文件夹...")
            directory = self.path_edit.text()
            folders = []
            
            for root, dirnames, filenames in os.walk(directory):
                for dirname in dirnames:
                    folders.append(os.path.join(root, dirname))
            
            self.display_results(folders)
            self.showSuccess("统计完成")
        except Exception as e:
            self.showError(f"统计失败: {str(e)}")
        finally:
            self.hideProgress()
    
    def stat_empty_folders(self):
        """统计空文件夹"""
        valid, message = self.validate()
        if not valid:
            self.show_error("错误", message)
            return
            
        try:
            self.showProgress("正在统计空文件夹...")
            directory = self.path_edit.text()
            empty_folders = []
            
            for root, dirnames, filenames in os.walk(directory):
                for dirname in dirnames:
                    folder_path = os.path.join(root, dirname)
                    if not os.listdir(folder_path):
                        empty_folders.append(folder_path)
            
            self.display_results(empty_folders)
            self.showSuccess("统计完成")
        except Exception as e:
            self.showError(f"统计失败: {str(e)}")
        finally:
            self.hideProgress()
    
    def display_results(self, results):
        """显示结果"""
        self.result_table.setRowCount(len(results))
        for i, result in enumerate(results):
            self.result_table.setItem(i, 0, QTableWidgetItem(result))
        # 更新统计标签
        self.stat_label.setText(f"共计 {len(results)} 行")
    
    def copy_results(self):
        """拷贝统计内容"""
        results = []
        for i in range(self.result_table.rowCount()):
            item = self.result_table.item(i, 0)
            if item:
                results.append(item.text())
        
        if results:
            clipboard = QApplication.clipboard()
            clipboard.setText('\n'.join(results))
            self.show_success("成功", "统计内容已拷贝到剪贴板")
        else:
            self.show_warning("警告", "没有可拷贝的内容")
    
    def clear_results(self):
        """清空结果"""
        self.result_table.setRowCount(0)
        self.stat_label.setText("共计 0 行")
        self.show_success("成功", "结果已清空")