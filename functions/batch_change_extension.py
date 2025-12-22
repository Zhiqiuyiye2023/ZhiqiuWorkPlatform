"""
批量修改后缀功能
作者: 知秋一叶
版本号: 0.0.5
"""

from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QPushButton, QLineEdit, QLabel, QTextEdit, QFileDialog, QComboBox, QCheckBox
from qfluentwidgets import LineEdit, PushButton, TextEdit, ComboBox, CheckBox
from qfluentwidgets import FluentIcon as FIF
from .file_processor_base import BaseFileProcessorFunction
import os


class BatchChangeExtensionFunction(BaseFileProcessorFunction):
    """批量修改后缀功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>" 
            "批量修改文件后缀<br>" 
            "支持从Excel文件加载规则或手动输入规则" 
        )
        super().__init__("批量修改后缀", description, parent)
        self._initUI()
    
    def _initUI(self):
        """初始化界面"""
        # 批量文件选择区域
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("选择文件:"))
        
        self.file_list_edit = LineEdit(self)
        self.file_list_edit.setPlaceholderText("已选择 0 个文件")
        self.file_list_edit.setReadOnly(True)
        
        self.browse_files_button = PushButton("选择文件", self, FIF.DOCUMENT)
        self.browse_files_button.clicked.connect(self.browse_files)
        
        self.clear_files_button = PushButton("清空", self, FIF.CLOSE)
        self.clear_files_button.clicked.connect(self.clear_files)
        
        file_layout.addWidget(self.file_list_edit)
        file_layout.addWidget(self.browse_files_button)
        file_layout.addWidget(self.clear_files_button)
        self.contentLayout.addLayout(file_layout)
        
        # 后缀修改规则区域
        rule_layout = QHBoxLayout()
        rule_layout.addWidget(QLabel("新后缀:"))
        
        self.new_extension_edit = LineEdit(self)
        self.new_extension_edit.setPlaceholderText("请输入新后缀，如：csv, png")
        
        rule_layout.addWidget(self.new_extension_edit)
        rule_layout.addStretch()
        self.contentLayout.addLayout(rule_layout)
        
        # 修改选项区域
        option_layout = QHBoxLayout()
        option_layout.addWidget(QLabel("修改选项:"))
        
        self.replace_all_checkbox = CheckBox("替换所有选择的文件")
        self.replace_all_checkbox.setChecked(True)
        
        self.ignore_extension_checkbox = CheckBox("忽略现有后缀")
        self.ignore_extension_checkbox.setChecked(False)
        
        option_layout.addWidget(self.replace_all_checkbox)
        option_layout.addWidget(self.ignore_extension_checkbox)
        option_layout.addStretch()
        self.contentLayout.addLayout(option_layout)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        self.change_button = PushButton("执行修改后缀", self, FIF.TAG)
        self.change_button.clicked.connect(self.execute_change_extension)
        
        button_layout.addStretch()
        button_layout.addWidget(self.change_button)
        self.contentLayout.addLayout(button_layout)
        
        # 初始化文件列表
        self.selected_files = []
    
    def browse_files(self):
        """选择多个文件"""
        from PyQt6.QtWidgets import QFileDialog
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择文件", "", "所有文件 (*.*)"
        )
        
        if files:
            # 添加到已选择的文件列表
            self.selected_files.extend(files)
            # 更新显示
            self.file_list_edit.setText(f"已选择 {len(self.selected_files)} 个文件")
    
    def clear_files(self):
        """清空已选择的文件"""
        self.selected_files.clear()
        self.file_list_edit.setText("已选择 0 个文件")
    
    def execute_change_extension(self):
        """执行修改后缀"""
        new_extension = self.new_extension_edit.text().strip()
        
        if not new_extension:
            self.show_warning("警告", "请输入新后缀")
            return
            
        if not self.selected_files:
            self.show_warning("警告", "请选择要修改的文件")
            return
            
        try:
            self.showProgress("正在执行修改后缀...")
            success_count = 0
            fail_count = 0
            
            for file_path in self.selected_files:
                try:
                    # 获取文件所在目录和文件名
                    dir_path = os.path.dirname(file_path)
                    file_name = os.path.basename(file_path)
                    
                    if self.ignore_extension_checkbox.isChecked():
                        # 忽略现有后缀，直接使用新后缀
                        new_file_name = f"{os.path.splitext(file_name)[0]}.{new_extension}"
                    else:
                        # 替换现有后缀
                        base_name = os.path.splitext(file_name)[0]
                        new_file_name = f"{base_name}.{new_extension}"
                    
                    # 构建新文件路径
                    new_file_path = os.path.join(dir_path, new_file_name)
                    
                    # 执行重命名
                    os.rename(file_path, new_file_path)
                    success_count += 1
                    
                except Exception as e:
                    fail_count += 1
                    print(f"修改后缀失败 {file_path} -> .{new_extension}: {str(e)}")
            
            # 清空已选择的文件列表
            self.clear_files()
            
            self.showSuccess(f"修改后缀完成\n成功: {success_count} 个\n失败: {fail_count} 个")
        except Exception as e:
            self.showError(f"修改后缀时出错: {str(e)}")
        finally:
            self.hideProgress()
