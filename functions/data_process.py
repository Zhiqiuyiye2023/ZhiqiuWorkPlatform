"""
数据处理功能
作者: 知秋一叶
版本号: 0.0.5
"""

import os
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QPushButton, QLineEdit, QLabel, QTextEdit, QFileDialog, QComboBox
from qfluentwidgets import LineEdit, PushButton, TextEdit, ComboBox
from qfluentwidgets import FluentIcon as FIF
from .file_processor_base import BaseFileProcessorFunction
import pandas as pd


class DataProcessFunction(BaseFileProcessorFunction):
    """文本重复整合功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>"+
            "文本重复整合<br>"+
            "将相同ID的重复文本内容整合到一起"
        )
        super().__init__("文本重复整合", description, parent)
        self._initUI()
    
    def _initUI(self):
        """初始化界面"""
        # Excel文件选择区域
        excel_layout = QHBoxLayout()
        excel_layout.addWidget(QLabel("Excel文件:"))
        
        self.excel_edit = LineEdit(self)
        self.excel_edit.setPlaceholderText("请选择Excel文件")
        # 添加文本变化信号，自动加载列名
        self.excel_edit.textChanged.connect(self._auto_load_columns)
        
        self.excel_browse_button = PushButton("选择Excel", self, FIF.DOCUMENT)
        self.excel_browse_button.clicked.connect(lambda: self.browse_file(self.excel_edit, "Excel Files (*.xlsx *.xls)"))
        
        excel_layout.addWidget(self.excel_edit)
        excel_layout.addWidget(self.excel_browse_button)
        self.contentLayout.addLayout(excel_layout)
        
        # 列选择区域
        column_layout = QHBoxLayout()
        
        # 序号列
        id_layout = QHBoxLayout()
        id_label = QLabel("序号列:")
        id_label.setStyleSheet("margin-right: 5px;")
        self.id_col_combo = ComboBox(self)
        id_layout.addWidget(id_label)
        id_layout.addWidget(self.id_col_combo, 1)  # 添加拉伸因子，让下拉框根据页面宽度适配
        
        # 关联内容列
        content_layout = QHBoxLayout()
        content_label = QLabel("关联内容列:")
        content_label.setStyleSheet("margin-right: 5px;")
        self.content_col_combo = ComboBox(self)
        content_layout.addWidget(content_label)
        content_layout.addWidget(self.content_col_combo, 1)  # 添加拉伸因子，让下拉框根据页面宽度适配
        
        # 添加从Excel加载数据到处理结果显示区域的按钮
        self.load_to_text_button = PushButton("加载到处理结果", self, FIF.SYNC)
        self.load_to_text_button.clicked.connect(self.load_excel_to_text)
        
        column_layout.addLayout(id_layout, 1)  # 添加拉伸因子，让两个布局均匀分配空间
        column_layout.addSpacing(20)  # 添加间距
        column_layout.addLayout(content_layout, 1)  # 添加拉伸因子，让两个布局均匀分配空间
        column_layout.addWidget(self.load_to_text_button)
        self.contentLayout.addLayout(column_layout)
        
        # 数据显示区域
        self.text_edit = TextEdit(self)
        self.text_edit.setPlaceholderText("处理结果将显示在这里...")
        self.text_edit.setFixedHeight(200)
        self.contentLayout.addWidget(self.text_edit)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        self.sample_button = PushButton("添加示例", self, FIF.EDIT)
        self.clear_button = PushButton("清除", self, FIF.DELETE)
        self.process_button = PushButton("处理数据", self, FIF.ALIGNMENT)
        
        self.sample_button.clicked.connect(self.add_sample)
        self.clear_button.clicked.connect(self.clear_text)
        self.process_button.clicked.connect(self.process_data)
        
        button_layout.addWidget(self.sample_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.process_button)
        self.contentLayout.addLayout(button_layout)
    
    def _auto_load_columns(self, text):
        """自动加载Excel列名"""
        if text and os.path.exists(text) and (text.endswith('.xlsx') or text.endswith('.xls')):
            try:
                import pandas as pd
                df = pd.read_excel(text)
                columns = df.columns.tolist()
                
                self.id_col_combo.clear()
                self.content_col_combo.clear()
                
                self.id_col_combo.addItems(columns)
                self.content_col_combo.addItems(columns)
            except Exception as e:
                # 自动加载失败不显示错误，仅在手动加载时显示
                pass
    
    def load_excel_to_text(self):
        """从Excel加载数据到处理结果显示区域"""
        excel_path = self.excel_edit.text()
        id_col = self.id_col_combo.currentText()
        content_col = self.content_col_combo.currentText()
        
        if not excel_path:
            self.show_warning("警告", "请选择Excel文件")
            return
        
        if not id_col or not content_col:
            self.show_warning("警告", "请选择序号列和关联内容列")
            return
        
        try:
            self.showProgress("正在从Excel加载数据...")
            
            # 读取Excel数据
            df = pd.read_excel(excel_path)
            
            # 确保选择的列存在
            if id_col not in df.columns or content_col not in df.columns:
                self.show_error("错误", "选择的列不存在于Excel文件中")
                return
            
            # 构建文本内容
            text_content = ""
            for _, row in df.iterrows():
                id_value = str(row[id_col])
                content_value = str(row[content_col])
                text_content += f"{id_value}\t{content_value}\n"
            
            # 将数据显示到处理结果区域
            self.text_edit.setPlainText(text_content)
            self.showSuccess("数据加载完成")
        except Exception as e:
            self.show_error("错误", f"从Excel加载数据时出错: {str(e)}")
        finally:
            self.hideProgress()
    
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
    
    def clear_text(self):
        """清除处理结果显示区域的内容"""
        self.text_edit.clear()
        self.showSuccess("已清除处理结果")
    
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