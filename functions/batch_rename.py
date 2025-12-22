"""
批量重命名功能
作者: 知秋一叶
版本号: 0.0.5
"""

from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QPushButton, QLineEdit, QLabel, QTextEdit, QFileDialog, QComboBox
from qfluentwidgets import LineEdit, PushButton, TextEdit, ComboBox
from qfluentwidgets import FluentIcon as FIF
from .file_processor_base import BaseFileProcessorFunction
import os


class BatchRenameFunction(BaseFileProcessorFunction):
    """批量重命名功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>"
            "批量重命名文件/文件夹<br>"
            "支持从Excel或文本输入重命名规则"
        )
        super().__init__("批量重命名", description, parent)
        self._initUI()
    
    def _initUI(self):
        """初始化界面"""
        # 路径输入区域
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("目标路径:"))
        
        self.path_edit = LineEdit(self)
        self.path_edit.setPlaceholderText("请选择目标目录")
        
        self.path_browse_button = PushButton("浏览", self, FIF.FOLDER)
        self.path_browse_button.clicked.connect(lambda: self.browse_directory(self.path_edit))
        
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.path_browse_button)
        self.contentLayout.addLayout(path_layout)
        
        # Excel文件选择区域
        excel_layout = QHBoxLayout()
        excel_layout.addWidget(QLabel("Excel文件:"))
        
        self.excel_edit = LineEdit(self)
        self.excel_edit.setPlaceholderText("请选择Excel文件（可选）")
        
        self.excel_browse_button = PushButton("选择Excel", self, FIF.DOCUMENT)
        self.excel_browse_button.clicked.connect(lambda: self.browse_file(self.excel_edit, "Excel Files (*.xlsx *.xls)"))
        
        self.load_excel_button = PushButton("加载数据", self, FIF.SYNC)
        self.load_excel_button.clicked.connect(self.load_rename_to_table)
        
        excel_layout.addWidget(self.excel_edit)
        excel_layout.addWidget(self.excel_browse_button)
        excel_layout.addWidget(self.load_excel_button)
        self.contentLayout.addLayout(excel_layout)
        
        # 列选择区域
        column_layout = QHBoxLayout()
        column_layout.addWidget(QLabel("原名称列:"))
        
        self.old_name_combo = ComboBox(self)
        self.old_name_combo.setFixedWidth(150)
        
        column_layout.addWidget(QLabel("新名称列:"))
        self.new_name_combo = ComboBox(self)
        self.new_name_combo.setFixedWidth(150)
        
        self.load_columns_button = PushButton("加载列名", self, FIF.SYNC)
        self.load_columns_button.clicked.connect(self.load_excel_columns)
        
        column_layout.addWidget(self.old_name_combo)
        column_layout.addWidget(self.new_name_combo)
        column_layout.addWidget(self.load_columns_button)
        self.contentLayout.addLayout(column_layout)
        
        # 文本输入区域
        self.text_edit = TextEdit(self)
        self.text_edit.setPlaceholderText("请输入重命名规则，格式：原名称<TAB>新名称\n例如：\nold_name1\tnew_name1\nold_name2\tnew_name2")
        self.text_edit.setFixedHeight(150)
        self.contentLayout.addWidget(self.text_edit)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        self.sample_button = PushButton("添加示例", self, FIF.EDIT)
        self.load_text_button = PushButton("加载文本", self, FIF.SYNC)
        self.rename_button = PushButton("执行重命名", self, FIF.TAG)
        
        self.sample_button.clicked.connect(self.add_sample)
        self.load_text_button.clicked.connect(self.load_text_to_table)
        self.rename_button.clicked.connect(self.execute_rename)
        
        button_layout.addWidget(self.sample_button)
        button_layout.addWidget(self.load_text_button)
        button_layout.addWidget(self.rename_button)
        self.contentLayout.addLayout(button_layout)
    
    def load_excel_columns(self):
        """加载Excel列名"""
        excel_path = self.excel_edit.text()
        if not excel_path:
            self.show_warning("警告", "请选择Excel文件")
            return
            
        try:
            import pandas as pd
            df = pd.read_excel(excel_path)
            columns = df.columns.tolist()
            
            self.old_name_combo.clear()
            self.new_name_combo.clear()
            
            self.old_name_combo.addItems(columns)
            self.new_name_combo.addItems(columns)
            
            self.show_success("成功", "列名加载完成")
        except Exception as e:
            self.show_error("错误", f"加载Excel列名时出错: {str(e)}")
    
    def load_rename_to_table(self):
        """从Excel加载重命名数据到表格"""
        excel_path = self.excel_edit.text()
        old_col = self.old_name_combo.currentText()
        new_col = self.new_name_combo.currentText()
        
        if not excel_path:
            self.show_warning("警告", "请选择Excel文件")
            return
            
        if not old_col or not new_col:
            self.show_warning("警告", "请选择原名称列和新名称列")
            return
            
        try:
            import pandas as pd
            df = pd.read_excel(excel_path)
            rename_data = []
            
            for _, row in df.iterrows():
                old_name = str(row[old_col])
                new_name = str(row[new_col])
                rename_data.append(f"{old_name}\t{new_name}")
                
            self.text_edit.setPlainText('\n'.join(rename_data))
            self.show_success("成功", "数据加载完成")
        except Exception as e:
            self.show_error("错误", f"加载Excel数据时出错: {str(e)}")
    
    def load_text_to_table(self):
        """从文本加载重命名数据到表格"""
        text = self.text_edit.toPlainText()
        if not text.strip():
            self.show_warning("警告", "请输入重命名规则")
            return
            
        try:
            self.show_success("成功", "数据加载完成")
        except Exception as e:
            self.show_error("错误", f"加载文本数据时出错: {str(e)}")
    
    def add_sample(self):
        """添加示例数据"""
        sample_content = (
            "old_name1\tnew_name1\n"
            "old_name2\tnew_name2\n"
            "old_name3\tnew_name3\n"
        )
        self.text_edit.setPlainText(sample_content)
    
    def execute_rename(self):
        """执行重命名"""
        text_content = self.text_edit.toPlainText()
        target_path = self.path_edit.text()
        
        if not target_path:
            self.show_warning("警告", "请输入目标路径")
            return
            
        if not os.path.exists(target_path):
            self.show_warning("警告", "目标路径不存在")
            return
            
        if not text_content.strip():
            self.show_warning("警告", "请输入重命名规则")
            return
            
        try:
            self.showProgress("正在执行重命名...")
            lines = text_content.strip().split('\n')
            success_count = 0
            fail_count = 0
            
            for line in lines:
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    old_name = parts[0]
                    new_name = parts[1]
                    
                    old_path = os.path.join(target_path, old_name)
                    new_path = os.path.join(target_path, new_name)
                    
                    if os.path.exists(old_path):
                        try:
                            os.rename(old_path, new_path)
                            success_count += 1
                        except Exception as e:
                            fail_count += 1
                            print(f"重命名失败 {old_name} -> {new_name}: {str(e)}")
                    else:
                        fail_count += 1
                        print(f"文件不存在: {old_path}")
            
            self.showSuccess(f"重命名完成\n成功: {success_count} 个\n失败: {fail_count} 个")
        except Exception as e:
            self.showError(f"重命名时出错: {str(e)}")
        finally:
            self.hideProgress()