"""
批量重命名功能对话框
作者: 知秋一叶
版本号: 0.0.5
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, 
                            QTextEdit, QFileDialog, QLabel, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView)
from qfluentwidgets import (BodyLabel, PushButton, ComboBox, MessageBox, 
                           InfoBar, InfoBarPosition)
from .base_dialog import BaseFileProcessDialog
from functions.processor import FileBatchProcessor


class RenameDialog(BaseFileProcessDialog):
    """批量重命名功能对话框"""
    
    def __init__(self, parent=None):
        super().__init__("批量重命名文件/文件夹", parent)
        self.processor = FileBatchProcessor()
        self.setup_ui()
    
    def setup_ui(self):
        """设置界面"""
        # 路径输入区域
        path_layout = QHBoxLayout()
        self.path_label = BodyLabel("目标路径:")
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("请选择目标目录")
        self.path_edit.setFixedHeight(35)  # 增加高度
        self.path_browse_button = PushButton("浏览")
        self.path_browse_button.setFixedHeight(35)
        self.path_browse_button.clicked.connect(lambda: self.browse_directory(self.path_edit))
        
        path_layout.addWidget(self.path_label)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.path_browse_button)
        self.addContentLayout(path_layout)
        
        # Excel文件选择区域
        excel_layout = QHBoxLayout()
        self.excel_label = BodyLabel("Excel文件:")
        self.excel_edit = QLineEdit()
        self.excel_edit.setPlaceholderText("请选择Excel文件")
        self.excel_edit.setFixedHeight(35)  # 增加高度
        self.excel_browse_button = PushButton("选择Excel")
        self.excel_browse_button.setFixedHeight(35)
        self.excel_browse_button.clicked.connect(self.select_excel)
        
        excel_layout.addWidget(self.excel_label)
        excel_layout.addWidget(self.excel_edit)
        excel_layout.addWidget(self.excel_browse_button)
        self.addContentLayout(excel_layout)
        
        # 列选择
        column_layout = QHBoxLayout()
        self.old_name_label = BodyLabel("原名称列:")
        self.old_name_combo = ComboBox()
        self.old_name_combo.setPlaceholderText("请选择原名称列")
        self.old_name_combo.setFixedHeight(35)
        
        self.new_name_label = BodyLabel("新名称列:")
        self.new_name_combo = ComboBox()
        self.new_name_combo.setPlaceholderText("请选择新名称列")
        self.new_name_combo.setFixedHeight(35)
        
        self.load_to_table_button = PushButton("加载到表格")
        self.load_to_table_button.setFixedHeight(35)
        self.load_to_table_button.clicked.connect(self.load_rename_to_table)
        
        column_layout.addWidget(self.old_name_label)
        column_layout.addWidget(self.old_name_combo)
        column_layout.addWidget(self.new_name_label)
        column_layout.addWidget(self.new_name_combo)
        column_layout.addWidget(self.load_to_table_button)
        self.addContentLayout(column_layout)
        
        # 文本输入区域
        self.text_edit = QTextEdit()
        self.text_edit.setFixedHeight(100)
        self.text_edit.setPlaceholderText("请输入原名称和新名称，每行一对，用制表符或空格分隔\n例如：\n原文件.txt\t新文件.txt\n旧文件夹\t新文件夹")
        sample_content = "请输入原名称和新名称，每行一对，用制表符或空格分隔\n例如：\n原文件.txt\t新文件.txt\n旧文件夹\t新文件夹"
        self.text_edit.setPlainText(sample_content)
        self.addContentWidget(self.text_edit)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        self.load_to_table_button2 = PushButton("加载到表格")
        self.load_to_table_button2.setFixedHeight(35)
        self.load_to_table_button2.clicked.connect(self.load_text_to_table)
        
        self.execute_button = PushButton("执行重命名")
        self.execute_button.setFixedHeight(35)
        self.execute_button.clicked.connect(self.execute_rename)
        
        button_layout.addWidget(self.load_to_table_button2)
        button_layout.addWidget(self.execute_button)
        self.addContentLayout(button_layout)
        
        # 重命名表格
        self.rename_table = QTableWidget()
        self.rename_table.setColumnCount(2)
        self.rename_table.setHorizontalHeaderLabels(["原名称", "新名称"])
        self.rename_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.rename_table.setAlternatingRowColors(True)
        self.rename_table.setFixedHeight(200)
        self.addContentWidget(self.rename_table)
    
    def browse_directory(self, line_edit):
        """浏览目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择目录")
        if directory:
            line_edit.setText(directory)
    
    def select_excel(self):
        """选择Excel文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择Excel文件", "", "Excel Files (*.xlsx *.xls)"
        )
        if file_path:
            self.excel_edit.setText(file_path)
            self.load_excel_columns()
    
    def load_excel_columns(self):
        """加载Excel列名到下拉框"""
        excel_path = self.excel_edit.text()
        if not excel_path:
            return
            
        try:
            columns = self.processor.load_rename_excel_columns(excel_path)
            self.old_name_combo.clear()
            self.new_name_combo.clear()
            self.old_name_combo.addItems(columns)
            self.new_name_combo.addItems(columns)
        except Exception as e:
            InfoBar.error(
                title='错误',
                content=f'加载Excel文件时出错: {str(e)}',
                parent=self,
                duration=3000
            )
    
    def load_rename_to_table(self):
        """从Excel加载重命名数据到表格"""
        excel_path = self.excel_edit.text()
        old_col = self.old_name_combo.currentText()
        new_col = self.new_name_combo.currentText()
        
        if not excel_path:
            InfoBar.warning(
                title='警告',
                content='请选择Excel文件',
                parent=self,
                duration=2000
            )
            return
            
        if not old_col or not new_col:
            InfoBar.warning(
                title='警告',
                content='请选择原名称列和新名称列',
                parent=self,
                duration=2000
            )
            return
            
        try:
            rename_data = self.processor.load_rename_from_excel(excel_path, old_col, new_col)
            self.display_rename_data(rename_data)
            InfoBar.success(
                title='成功',
                content='数据加载完成',
                parent=self,
                duration=2000
            )
        except Exception as e:
            InfoBar.error(
                title='错误',
                content=f'加载Excel数据时出错: {str(e)}',
                parent=self,
                duration=3000
            )
    
    def load_text_to_table(self):
        """从文本加载重命名数据到表格"""
        text = self.text_edit.toPlainText()
        try:
            rename_data = self.processor.load_rename_from_text(text)
            self.display_rename_data(rename_data)
            InfoBar.success(
                title='成功',
                content='数据加载完成',
                parent=self,
                duration=2000
            )
        except Exception as e:
            InfoBar.error(
                title='错误',
                content=f'加载文本数据时出错: {str(e)}',
                parent=self,
                duration=3000
            )
    
    def display_rename_data(self, rename_data):
        """显示重命名数据"""
        self.rename_table.setRowCount(len(rename_data))
        for i, (old_name, new_name) in enumerate(rename_data):
            self.rename_table.setItem(i, 0, QTableWidgetItem(str(old_name)))
            self.rename_table.setItem(i, 1, QTableWidgetItem(str(new_name)))
    
    def execute_rename(self):
        """执行重命名"""
        folder_path = self.path_edit.text()
        if not folder_path:
            InfoBar.warning(
                title='警告',
                content='请输入目标路径',
                parent=self,
                duration=2000
            )
            return
            
        if not self.rename_table.rowCount():
            InfoBar.warning(
                title='警告',
                content='没有要重命名的数据',
                parent=self,
                duration=2000
            )
            return
            
        try:
            # 收集重命名数据
            rename_data = []
            for i in range(self.rename_table.rowCount()):
                old_item = self.rename_table.item(i, 0)
                new_item = self.rename_table.item(i, 1)
                if old_item and new_item:
                    old_name = old_item.text()
                    new_name = new_item.text()
                    if old_name and new_name:
                        rename_data.append((old_name, new_name))
            
            if not rename_data:
                InfoBar.warning(
                    title='警告',
                    content='没有有效的重命名数据',
                    parent=self,
                    duration=2000
                )
                return
            
            success_count, fail_count = self.processor.execute_rename(folder_path, rename_data)
            InfoBar.success(
                title='完成',
                content=f'重命名完成\n成功: {success_count} 个\n失败: {fail_count} 个',
                parent=self,
                duration=3000
            )
        except Exception as e:
            InfoBar.error(
                title='错误',
                content=f'重命名时出错: {str(e)}',
                parent=self,
                duration=3000
            )