# coding:utf-8
"""
文件与文件夹内容修改功能
包括删除内容和插入内容功能
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFileDialog
from PyQt6.QtCore import Qt
from qfluentwidgets import PrimaryPushButton, TransparentPushButton, BodyLabel, ComboBox, LineEdit
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction
import os


class FileFolderContentModifierFunction(BaseFunction):
    """文件与文件夹内容修改功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>" 
            "修改文件与文件夹名称，支持删除指定内容和插入指定内容<br>" 
            "1. 删除内容：删除名称中包含的指定文本<br>" 
            "2. 插入内容：在名称的前缀或后缀插入指定文本"
        )
        super().__init__("文件与文件夹内容修改", description, parent)
        # 调整主布局间距，使界面更紧凑
        self.contentLayout.setSpacing(10)  # 减小控件之间的垂直间距
        self._initUI()
    
    def _initUI(self):
        """初始化界面"""
        # 目录选择区域
        dir_layout = QHBoxLayout()
        dir_layout.setSpacing(8)  # 减小间距，使布局更紧凑
        
        dir_label = BodyLabel("目录路径：")
        dir_layout.addWidget(dir_label)
        
        self.dir_edit = LineEdit(self)  # 使用 LineEdit 替代 QLineEdit
        self.dir_edit.setPlaceholderText("请选择要修改名称的目录")
        self.dir_edit.setMinimumWidth(350)  # 增加输入框宽度，使其更实用
        self.dir_edit.setFixedHeight(36)  # 固定高度，与按钮高度一致
        dir_layout.addWidget(self.dir_edit)
        
        browse_button = TransparentPushButton("浏览", self, FIF.FOLDER)
        browse_button.setFixedHeight(36)  # 固定按钮高度
        browse_button.clicked.connect(self._browse_directory)
        dir_layout.addWidget(browse_button)
        
        self.contentLayout.addLayout(dir_layout)
        
        # 操作类型选择
        operation_layout = QHBoxLayout()
        operation_layout.setSpacing(8)  # 减小间距
        
        operation_label = BodyLabel("操作类型：")
        operation_layout.addWidget(operation_label)
        
        self.operation_combo = ComboBox(self)
        self.operation_combo.addItems(["删除内容", "插入内容"])
        self.operation_combo.currentTextChanged.connect(self._on_operation_changed)
        self.operation_combo.setFixedHeight(36)  # 固定高度
        operation_layout.addWidget(self.operation_combo)
        operation_layout.addStretch(1)  # 添加弹性空间，使控件靠左对齐
        
        self.contentLayout.addLayout(operation_layout)
        
        # 删除内容区域 - 使用QWidget包裹布局
        self.delete_widget = QWidget(self)
        self.delete_layout = QHBoxLayout(self.delete_widget)
        self.delete_layout.setSpacing(8)  # 减小间距
        self.delete_layout.setContentsMargins(0, 0, 0, 0)
        
        delete_label = BodyLabel("删除内容：")
        self.delete_layout.addWidget(delete_label)
        
        self.delete_edit = LineEdit(self)  # 使用 LineEdit 替代 QLineEdit
        self.delete_edit.setPlaceholderText("请输入要删除的文本")
        self.delete_edit.setMinimumWidth(350)  # 增加输入框宽度
        self.delete_edit.setFixedHeight(36)  # 固定高度
        self.delete_layout.addWidget(self.delete_edit)
        self.delete_layout.addStretch(1)  # 添加弹性空间
        
        self.contentLayout.addWidget(self.delete_widget)
        
        # 插入内容区域 - 使用QWidget包裹布局
        self.insert_widget = QWidget(self)
        self.insert_layout = QHBoxLayout(self.insert_widget)
        self.insert_layout.setSpacing(8)  # 减小间距
        self.insert_layout.setContentsMargins(0, 0, 0, 0)
        
        insert_label = BodyLabel("插入内容：")
        self.insert_layout.addWidget(insert_label)
        
        self.insert_edit = LineEdit(self)  # 使用 LineEdit 替代 QLineEdit
        self.insert_edit.setPlaceholderText("请输入要插入的文本")
        self.insert_edit.setMinimumWidth(200)  # 调整输入框宽度
        self.insert_edit.setFixedHeight(36)  # 固定高度
        self.insert_layout.addWidget(self.insert_edit)
        
        position_label = BodyLabel("插入位置：")
        self.insert_layout.addWidget(position_label)
        
        self.position_combo = ComboBox(self)
        self.position_combo.addItems(["前缀", "后缀"])
        self.position_combo.setFixedHeight(36)  # 固定高度
        self.position_combo.setFixedWidth(100)  # 固定宽度
        self.insert_layout.addWidget(self.position_combo)
        self.insert_layout.addStretch(1)  # 添加弹性空间
        
        self.contentLayout.addWidget(self.insert_widget)
        self.insert_widget.hide()  # 默认隐藏插入内容区域
        
        # 执行按钮区域
        button_layout = QHBoxLayout()
        execute_button = PrimaryPushButton("执行修改", self, FIF.SEND)
        execute_button.setFixedHeight(36)  # 固定按钮高度
        execute_button.setFixedWidth(120)  # 固定按钮宽度
        execute_button.clicked.connect(self.execute)
        button_layout.addStretch(1)  # 添加弹性空间，使按钮居中
        button_layout.addWidget(execute_button)
        button_layout.addStretch(1)  # 添加弹性空间，使按钮居中
        self.contentLayout.addLayout(button_layout)
    
    def _browse_directory(self):
        """浏览目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择目录")
        if directory:
            self.dir_edit.setText(directory)
    
    def _on_operation_changed(self, text):
        """操作类型改变时的处理"""
        if text == "删除内容":
            self.delete_widget.show()
            self.insert_widget.hide()
        else:
            self.delete_widget.hide()
            self.insert_widget.show()
    
    def execute(self):
        """执行文件与文件夹内容修改"""
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
        """删除文件与文件夹名称中的指定内容"""
        self.showProgress("正在删除文件与文件夹名称中的指定内容...")
        
        success_count = 0
        fail_count = 0
        
        try:
            items = os.listdir(dir_path)
            total = len(items)
            
            for index, item in enumerate(items):
                item_path = os.path.join(dir_path, item)
                try:
                    new_name = item.replace(content, '')
                    new_path = os.path.join(dir_path, new_name)
                    # 检查新名称是否已存在
                    if not os.path.exists(new_path):
                        os.rename(item_path, new_path)
                        success_count += 1
                    else:
                        fail_count += 1
                except Exception as e:
                    fail_count += 1
                    print(f"修改 {item} 失败: {e}")
                
                # 更新进度
                progress = int((index + 1) / total * 100)
                self.updateProgress(progress, f"正在处理: {item}")
        except Exception as e:
            self.showError(f"修改名称时出错: {str(e)}")
            return
        
        self.showSuccess(f"名称修改完成\n成功: {success_count} 个\n失败: {fail_count} 个")
    
    def _insert_content(self, dir_path, content, position):
        """在文件与文件夹名称中插入指定内容"""
        self.showProgress("正在文件与文件夹名称中插入指定内容...")
        
        success_count = 0
        fail_count = 0
        
        try:
            items = os.listdir(dir_path)
            total = len(items)
            
            for index, item in enumerate(items):
                item_path = os.path.join(dir_path, item)
                try:
                    if os.path.isfile(item_path):
                        name, ext = os.path.splitext(item)
                        if position == "前缀":
                            new_name = content + name + ext
                        else:
                            new_name = name + content + ext
                    else:
                        if position == "前缀":
                            new_name = content + item
                        else:
                            new_name = item + content
                    
                    new_path = os.path.join(dir_path, new_name)
                    os.rename(item_path, new_path)
                    success_count += 1
                except Exception as e:
                    fail_count += 1
                    print(f"修改 {item} 失败: {e}")
                
                # 更新进度
                progress = int((index + 1) / total * 100)
                self.updateProgress(progress, f"正在处理: {item}")
        except Exception as e:
            self.showError(f"修改名称时出错: {str(e)}")
            return
        
        self.showSuccess(f"名称修改完成\n成功: {success_count} 个\n失败: {fail_count} 个")