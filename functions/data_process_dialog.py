"""
数据处理功能对话框
作者: 知秋一叶
版本号: 0.0.5
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, 
                            QTextEdit, QFileDialog, QLabel, QComboBox)
from qfluentwidgets import (BodyLabel, PushButton, ComboBox, MessageBox, 
                           InfoBar, InfoBarPosition)
from .base_dialog import BaseFileProcessDialog
from functions.processor import FileBatchProcessor


class DataProcessDialog(BaseFileProcessDialog):
    """数据处理功能对话框"""
    
    def __init__(self, parent=None):
        super().__init__("单数据对应多信息处理", parent)
        self.processor = FileBatchProcessor()
        self.setup_ui()
    
    def setup_ui(self):
        """设置界面"""
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
        
        # 列选择区域
        column_layout = QHBoxLayout()
        self.id_label = BodyLabel("序号列:")
        self.id_combo = ComboBox()
        self.id_combo.setPlaceholderText("请选择序号列")
        self.id_combo.setFixedHeight(35)
        
        self.content_label = BodyLabel("关联内容列:")
        self.content_combo = ComboBox()
        self.content_combo.setPlaceholderText("请选择关联内容列")
        self.content_combo.setFixedHeight(35)
        
        self.load_button = PushButton("加载到文本框")
        self.load_button.setFixedHeight(35)
        self.load_button.clicked.connect(self.load_data)
        
        column_layout.addWidget(self.id_label)
        column_layout.addWidget(self.id_combo)
        column_layout.addWidget(self.content_label)
        column_layout.addWidget(self.content_combo)
        column_layout.addWidget(self.load_button)
        self.addContentLayout(column_layout)
        
        # 文本输入区域
        self.text_edit = QTextEdit()
        self.text_edit.setFixedHeight(200)
        # 设置默认示例内容
        sample_content = (
            "A\t1\t===>\tA\t1,2  \n"
            "A\t2\t===>\tB\t3,4  \n"
            "B\t3\t===>\tC\t5,6,7  \n"
            "B\t4\t       \n"
            "C\t5\t       \n"
            "C\t6\t       \n"
            "C\t7\t       \n"
        )
        self.text_edit.setPlainText(sample_content)
        self.addContentWidget(self.text_edit)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        self.sample_button = PushButton("添加示例")
        self.sample_button.setFixedHeight(35)
        self.sample_button.clicked.connect(self.add_sample)
        
        self.process_button = PushButton("执行")
        self.process_button.setFixedHeight(35)
        self.process_button.clicked.connect(self.process_data)
        
        button_layout.addWidget(self.sample_button)
        button_layout.addWidget(self.process_button)
        self.addContentLayout(button_layout)
    
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
            columns = self.processor.load_data_excel_columns(excel_path)
            self.id_combo.clear()
            self.content_combo.clear()
            self.id_combo.addItems(columns)
            self.content_combo.addItems(columns)
        except Exception as e:
            InfoBar.error(
                title='错误',
                content=f'加载Excel文件时出错: {str(e)}',
                parent=self,
                duration=3000
            )
    
    def load_data(self):
        """从Excel加载数据到文本框"""
        excel_path = self.excel_edit.text()
        id_col = self.id_combo.currentText()
        content_col = self.content_combo.currentText()
        
        if not excel_path:
            InfoBar.warning(
                title='警告',
                content='请选择Excel文件',
                parent=self,
                duration=2000
            )
            return
            
        if not id_col or not content_col:
            InfoBar.warning(
                title='警告',
                content='请选择序号列和关联内容列',
                parent=self,
                duration=2000
            )
            return
            
        try:
            text_content = self.processor.load_data_from_excel(excel_path, id_col, content_col)
            self.text_edit.setPlainText(text_content)
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
    
    def add_sample(self):
        """添加示例数据"""
        sample_content = (
            "A\t1\n"
            "A\t2\n"
            "B\t3\n"
            "B\t4\n"
            "C\t5\n"
            "C\t6\n"
            "C\t7\n"
        )
        self.text_edit.setPlainText(sample_content)
    
    def process_data(self):
        """处理数据"""
        text_content = self.text_edit.toPlainText()
        if not text_content.strip():
            InfoBar.warning(
                title='警告',
                content='请输入数据内容',
                parent=self,
                duration=2000
            )
            return
            
        try:
            result_text = self.processor.process_data(text_content)
            self.text_edit.setPlainText(result_text)
            InfoBar.success(
                title='成功',
                content='数据处理完成',
                parent=self,
                duration=2000
            )
        except Exception as e:
            InfoBar.error(
                title='错误',
                content=f'处理数据时出错: {str(e)}',
                parent=self,
                duration=3000
            )