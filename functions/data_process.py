"""
数据处理功能
作者: 知秋一叶
版本号: 0.0.5
"""

from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QPushButton, QLineEdit, QLabel, QTextEdit, QFileDialog, QComboBox
from qfluentwidgets import LineEdit, PushButton, TextEdit, ComboBox
from qfluentwidgets import FluentIcon as FIF
from .file_processor_base import BaseFileProcessorFunction
import pandas as pd


class DataProcessFunction(BaseFileProcessorFunction):
    """数据处理功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>"
            "单数据对应多信息处理<br>"
            "从Excel文件中提取数据并进行处理"
        )
        super().__init__("数据处理", description, parent)
        self._initUI()
    
    def _initUI(self):
        """初始化界面"""
        # Excel文件选择区域
        excel_layout = QHBoxLayout()
        excel_layout.addWidget(QLabel("Excel文件:"))
        
        self.excel_edit = LineEdit(self)
        self.excel_edit.setPlaceholderText("请选择Excel文件")
        
        self.excel_browse_button = PushButton("选择Excel", self, FIF.DOCUMENT)
        self.excel_browse_button.clicked.connect(lambda: self.browse_file(self.excel_edit, "Excel Files (*.xlsx *.xls)"))
        
        excel_layout.addWidget(self.excel_edit)
        excel_layout.addWidget(self.excel_browse_button)
        self.contentLayout.addLayout(excel_layout)
        
        # 列选择区域
        column_layout = QHBoxLayout()
        column_layout.addWidget(QLabel("序号列:"))
        
        self.id_col_combo = ComboBox(self)
        self.id_col_combo.setFixedWidth(150)
        
        column_layout.addWidget(QLabel("关联内容列:"))
        self.content_col_combo = ComboBox(self)
        self.content_col_combo.setFixedWidth(150)
        
        self.load_columns_button = PushButton("加载列名", self, FIF.SYNC)
        self.load_columns_button.clicked.connect(self.load_excel_columns)
        
        column_layout.addWidget(self.id_col_combo)
        column_layout.addWidget(self.content_col_combo)
        column_layout.addWidget(self.load_columns_button)
        self.contentLayout.addLayout(column_layout)
        
        # 数据显示区域
        self.text_edit = TextEdit(self)
        self.text_edit.setPlaceholderText("处理结果将显示在这里...")
        self.text_edit.setFixedHeight(200)
        self.contentLayout.addWidget(self.text_edit)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        self.sample_button = PushButton("添加示例", self, FIF.EDIT)
        self.process_button = PushButton("处理数据", self, FIF.ALIGNMENT)
        
        self.sample_button.clicked.connect(self.add_sample)
        self.process_button.clicked.connect(self.process_data)
        
        button_layout.addWidget(self.sample_button)
        button_layout.addWidget(self.process_button)
        self.contentLayout.addLayout(button_layout)
    
    def load_excel_columns(self):
        """加载Excel列名"""
        excel_path = self.excel_edit.text()
        if not excel_path:
            self.show_warning("警告", "请选择Excel文件")
            return
            
        try:
            df = pd.read_excel(excel_path)
            columns = df.columns.tolist()
            
            self.id_col_combo.clear()
            self.content_col_combo.clear()
            
            self.id_col_combo.addItems(columns)
            self.content_col_combo.addItems(columns)
            
            self.show_success("成功", "列名加载完成")
        except Exception as e:
            self.show_error("错误", f"加载Excel列名时出错: {str(e)}")
    
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
            self.show_warning("警告", "请输入数据内容")
            return
            
        try:
            self.showProgress("正在处理数据...")
            lines = text_content.strip().split('\n')
            data_dict = {}
            
            # 按序号分组
            for line in lines:
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    id_value = parts[0]
                    content_value = parts[1]
                    if id_value in data_dict:
                        data_dict[id_value].append(content_value)
                    else:
                        data_dict[id_value] = [content_value]
            
            # 生成结果
            result_lines = []
            for id_value, content_list in data_dict.items():
                merged_content = ','.join(content_list)
                result_lines.append(f"{id_value}\t{merged_content}")
                
            result_text = '\n'.join(result_lines)
            self.text_edit.setPlainText(result_text)
            self.showSuccess("处理完成")
        except Exception as e:
            self.showError(f"处理数据时出错: {str(e)}")
        finally:
            self.hideProgress()