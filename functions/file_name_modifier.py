# coding:utf-8
"""
文件名修改功能
包括删除内容和插入内容功能
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QRadioButton, QFileDialog
from PyQt6.QtCore import Qt
from qfluentwidgets import PrimaryPushButton, TransparentPushButton, BodyLabel, ComboBox
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction
import os


class FileNameModifierFunction(BaseFunction):
    """文件名修改功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>" 
            "修改文件名，支持删除指定内容和插入指定内容<br>" 
            "1. 删除内容：删除文件名中包含的指定文本<br>" 
            "2. 插入内容：在文件名的前缀或后缀插入指定文本"
        )
        super().__init__("文件名修改", description, parent)
        self._initUI()
    
    def _initUI(self):
        """初始化界面"""
        # 目录选择区域
        dir_layout = QHBoxLayout()
        dir_layout.setSpacing(12)
        
        dir_label = BodyLabel("目录路径：")
        dir_layout.addWidget(dir_label)
        
        self.dir_edit = QLineEdit(self)
        self.dir_edit.setPlaceholderText("请选择要修改文件名的目录")
        self.dir_edit.setMinimumWidth(300)
        dir_layout.addWidget(self.dir_edit)
        
        browse_button = TransparentPushButton("浏览", self, FIF.FOLDER)
        browse_button.clicked.connect(self._browse_directory)
        dir_layout.addWidget(browse_button)
        
        self.contentLayout.addLayout(dir_layout)
        
        # 操作类型选择
        operation_layout = QHBoxLayout()
        operation_layout.setSpacing(12)
        
        operation_label = BodyLabel("操作类型：")
        operation_layout.addWidget(operation_label)
        
        self.operation_combo = ComboBox(self)
        self.operation_combo.addItems(["删除内容", "插入内容"])
        self.operation_combo.currentTextChanged.connect(self._on_operation_changed)
        operation_layout.addWidget(self.operation_combo)
        
        self.contentLayout.addLayout(operation_layout)
        
        # 删除内容区域
        self.delete_layout = QHBoxLayout()
        self.delete_layout.setSpacing(12)
        
        delete_label = BodyLabel("删除内容：")
        self.delete_layout.addWidget(delete_label)
        
        self.delete_edit = QLineEdit(self)
        self.delete_edit.setPlaceholderText("请输入要删除的文本")
        self.delete_layout.addWidget(self.delete_edit)
        
        self.contentLayout.addLayout(self.delete_layout)
        
        # 插入内容区域
        self.insert_layout = QHBoxLayout()
        self.insert_layout.setSpacing(12)
        
        insert_label = BodyLabel("插入内容：")
        self.insert_layout.addWidget(insert_label)
        
        self.insert_edit = QLineEdit(self)
        self.insert_edit.setPlaceholderText("请输入要插入的文本")
        self.insert_layout.addWidget(self.insert_edit)
        
        position_label = BodyLabel("插入位置：")
        self.insert_layout.addWidget(position_label)
        
        self.position_combo = ComboBox(self)
        self.position_combo.addItems(["前缀", "后缀"])
        self.insert_layout.addWidget(self.position_combo)
        
        self.contentLayout.addLayout(self.insert_layout)
        self.insert_layout.hide()  # 默认隐藏插入内容区域
        
        # 执行按钮
        execute_button = PrimaryPushButton("执行修改", self, FIF.SEND)
        execute_button.clicked.connect(self.execute)
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(execute_button)
        button_layout.addStretch(1)
        self.contentLayout.addLayout(button_layout)
    
    def _browse_directory(self):
        """浏览目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择目录")
        if directory:
            self.dir_edit.setText(directory)
    
    def _on_operation_changed(self, text):
        """操作类型改变时的处理"""
        if text == "删除内容":
            self.delete_layout.show()
            self.insert_layout.hide()
        else:
            self.delete_layout.hide()
            self.insert_layout.show()
    
    def execute(self):
        """执行文件名修改"""
        # 验证输入
        dir_path = self.dir_edit.text().strip()
        if not dir_path:
            self.showError("请选择目录路径")
            return
        
        if not os.path.exists(dir_path):
            self.showError("目录路径不存在")
            return
        
        operation = self.operation_combo.currentText()
        
        if operation == "删除内容":
            content = self.delete_edit.text().strip()
            if not content:
                self.showError("请输入要删除的内容")
                return
            
            self._delete_content(dir_path, content)
        else:
            content = self.insert_edit.text().strip()
            if not content:
                self.showError("请输入要插入的内容")
                return
            
            position = self.position_combo.currentText()
            self._insert_content(dir_path, content, position)
    
    def _delete_content(self, dir_path, content):
        """删除文件名中的指定内容"""
        self.showProgress("正在删除文件名中的指定内容...")
        
        success_count = 0
        fail_count = 0
        
        try:
            for filename in os.listdir(dir_path):
                file_path = os.path.join(dir_path, filename)
                if os.path.isfile(file_path):
                    try:
                        name, ext = os.path.splitext(filename)
                        new_name = name.replace(content, '') + ext
                        new_path = os.path.join(dir_path, new_name)
                        os.rename(file_path, new_path)
                        success_count += 1
                    except Exception as e:
                        fail_count += 1
                        print(f"修改文件 {filename} 失败: {e}")
        except Exception as e:
            self.showError(f"修改文件名时出错: {str(e)}")
            return
        
        self.showSuccess(f"文件名修改完成\n成功: {success_count} 个\n失败: {fail_count} 个")
    
    def _insert_content(self, dir_path, content, position):
        """在文件名中插入指定内容"""
        self.showProgress("正在文件名中插入指定内容...")
        
        success_count = 0
        fail_count = 0
        
        try:
            for filename in os.listdir(dir_path):
                file_path = os.path.join(dir_path, filename)
                if os.path.isfile(file_path):
                    try:
                        name, ext = os.path.splitext(filename)
                        if position == "前缀":
                            new_name = content + name + ext
                        else:
                            new_name = name + content + ext
                        new_path = os.path.join(dir_path, new_name)
                        os.rename(file_path, new_path)
                        success_count += 1
                    except Exception as e:
                        fail_count += 1
                        print(f"修改文件 {filename} 失败: {e}")
        except Exception as e:
            self.showError(f"修改文件名时出错: {str(e)}")
            return
        
        self.showSuccess(f"文件名修改完成\n成功: {success_count} 个\n失败: {fail_count} 个")