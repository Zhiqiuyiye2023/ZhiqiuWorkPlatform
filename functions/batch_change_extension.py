"""
批量修改后缀功能
作者: 知秋一叶
版本号: 0.0.5
"""

from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QPushButton, QLineEdit, QLabel, QTextEdit, QFileDialog, QComboBox, QCheckBox, QHeaderView, QTableWidgetItem, QGroupBox
from qfluentwidgets import LineEdit, PushButton, TextEdit, ComboBox, CheckBox, TableWidget
from qfluentwidgets import FluentIcon as FIF
from .file_processor_base import BaseFileProcessorFunction
import os


class BatchChangeExtensionFunction(BaseFileProcessorFunction):
    """批量修改后缀功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>" +
            "批量修改后缀<br>" +
            "支持从Excel文件加载规则或手动输入规则<br>" +
            "<font color='red'>💡 支持拖拽文件到列表中</font>"
        )
        super().__init__("批量修改后缀", description, parent)
        self._initUI()
        # 启用拖拽支持
        self.setAcceptDrops(True)
    
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
        
        # 文件列表展示区域
        file_list_group = QGroupBox("已选择文件", self)
        file_list_layout = QVBoxLayout(file_list_group)
        
        # 表格显示区域（参考矢量统计面板样式）
        self.table_widget = TableWidget(self)
        self.table_widget.setColumnCount(1)
        self.table_widget.setHorizontalHeaderLabels(["文件名"])
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setFixedHeight(200)  # 设置固定高度
        self.table_widget.setBorderVisible(True)
        file_list_layout.addWidget(self.table_widget)
        
        self.contentLayout.addWidget(file_list_group)
        
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
            # 更新表格显示
            self.update_file_table()
    
    def clear_files(self):
        """清空已选择的文件"""
        self.selected_files.clear()
        self.file_list_edit.setText("已选择 0 个文件")
        # 清空表格
        self.table_widget.setRowCount(0)
    
    def update_file_table(self):
        """更新文件列表表格"""
        # 清空现有表格内容
        self.table_widget.setRowCount(0)
        
        # 添加文件到表格
        for i, file_path in enumerate(self.selected_files):
            # 添加新行
            row = self.table_widget.rowCount()
            self.table_widget.insertRow(row)
            
            # 设置文件名
            file_name = os.path.basename(file_path)
            self.table_widget.setItem(row, 0, QTableWidgetItem(file_name))
    
    def dragEnterEvent(self, event):
        """拖拽进入事件处理"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        """拖拽释放事件处理"""
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):  # 只处理文件，不处理文件夹
                files.append(file_path)
        
        if files:
            # 添加到已选择的文件列表
            self.selected_files.extend(files)
            # 更新显示
            self.file_list_edit.setText(f"已选择 {len(self.selected_files)} 个文件")
            # 更新表格显示
            self.update_file_table()
    
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
