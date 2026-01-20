# coding:utf-8
"""
文件名称修改功能
包括删除内容和插入内容功能
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFileDialog, QGroupBox, QHeaderView, QTableWidgetItem, QStackedWidget
from PyQt6.QtCore import Qt
from qfluentwidgets import PrimaryPushButton, TransparentPushButton, BodyLabel, ComboBox, LineEdit, PushButton, TableWidget
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction
import os


class FileFolderContentModifierFunction(BaseFunction):
    """文件名称修改功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>" 
            "修改文件名称，支持删除指定内容和插入指定内容<br>" 
            "1. 删除内容：删除名称中包含的指定文本<br>" 
            "2. 插入内容：在名称的前缀或后缀插入指定文本<br>"
            "3. 选择文件夹后自动识别文件并展示到列表中<br>"
            "4. 支持输入路径后执行展示<br>"
            "5. 支持拖拽文件到列表中"
        )
        super().__init__("文件名称修改", description, parent)
        # 调整主布局间距，使界面更紧凑
        self.contentLayout.setSpacing(10)  # 减小控件之间的垂直间距
        self._initUI()
        # 启用拖拽支持
        self.setAcceptDrops(True)
    
    def _initUI(self):
        """初始化界面"""
        # 目录选择区域
        dir_layout = QHBoxLayout()
        dir_layout.setSpacing(8)  # 减小间距
        
        dir_label = QLabel("目录路径：")
        dir_layout.addWidget(dir_label)
        
        self.dir_edit = LineEdit(self)
        self.dir_edit.setPlaceholderText("请输入或选择要修改名称的目录")
        self.dir_edit.setMinimumWidth(350)  # 增加输入框宽度
        dir_layout.addWidget(self.dir_edit)
        
        self.browse_dir_button = PushButton("选择目录", self, FIF.FOLDER)
        self.browse_dir_button.clicked.connect(self._browse_directory)
        dir_layout.addWidget(self.browse_dir_button)
        
        self.show_files_button = PushButton("执行展示", self, FIF.SEARCH)
        self.show_files_button.clicked.connect(self._show_files)
        dir_layout.addWidget(self.show_files_button)
        
        self.clear_files_button = PushButton("清空", self, FIF.CLOSE)
        self.clear_files_button.clicked.connect(self.clear_files)
        dir_layout.addWidget(self.clear_files_button)
        
        self.contentLayout.addLayout(dir_layout)
        
        # 文件列表展示区域
        file_list_group = QGroupBox("已识别文件", self)
        file_list_layout = QVBoxLayout(file_list_group)
        
        # 表格显示区域（参考批量修改后缀面板样式）
        self.table_widget = TableWidget(self)
        self.table_widget.setColumnCount(2)
        self.table_widget.setHorizontalHeaderLabels(["文件名", "文件路径"])
        self.table_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table_widget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setFixedHeight(200)  # 设置固定高度
        self.table_widget.setBorderVisible(True)
        file_list_layout.addWidget(self.table_widget)
        
        self.contentLayout.addWidget(file_list_group)
        
        # 初始化文件列表
        self.selected_files = []
        
        # 综合操作区域 - 所有控件呈一行显示
        main_layout = QHBoxLayout()
        main_layout.setSpacing(8)  # 减小间距
        
        # 操作类型
        operation_label = QLabel("操作类型：")
        main_layout.addWidget(operation_label)
        
        self.operation_combo = ComboBox(self)
        self.operation_combo.addItems(["删除内容", "插入内容"])
        self.operation_combo.currentTextChanged.connect(self._on_operation_changed)
        self.operation_combo.setFixedHeight(36)  # 固定高度
        main_layout.addWidget(self.operation_combo)
        
        # 统一的内容输入框
        self.content_label = QLabel("删除内容：")
        main_layout.addWidget(self.content_label)
        
        self.content_edit = LineEdit(self)
        self.content_edit.setPlaceholderText("请输入要删除的文本")
        self.content_edit.setMinimumWidth(200)  # 调整输入框宽度
        self.content_edit.setFixedHeight(36)  # 固定高度
        main_layout.addWidget(self.content_edit)
        
        # 插入位置选择（仅在插入内容时显示）
        self.position_label = QLabel("插入位置：")
        main_layout.addWidget(self.position_label)
        
        self.position_combo = ComboBox(self)
        self.position_combo.addItems(["前缀", "后缀"])
        self.position_combo.setFixedHeight(36)  # 固定高度
        self.position_combo.setFixedWidth(100)  # 固定宽度
        main_layout.addWidget(self.position_combo)
        
        # 执行按钮
        main_layout.addStretch(1)  # 添加弹性空间，使按钮靠右
        
        execute_button = PrimaryPushButton("执行修改", self, FIF.SEND)
        execute_button.setFixedHeight(36)  # 固定按钮高度
        execute_button.setFixedWidth(120)  # 固定按钮宽度
        execute_button.clicked.connect(self.execute)
        main_layout.addWidget(execute_button)
        
        self.contentLayout.addLayout(main_layout)
        
        # 默认显示删除内容相关控件
        self._on_operation_changed("删除内容")
    
    def _browse_directory(self):
        """浏览目录"""
        from PyQt6.QtWidgets import QFileDialog
        directory = QFileDialog.getExistingDirectory(self, "选择目录")
        if directory:
            self.dir_edit.setText(directory)
            # 选择目录后自动执行展示
            self._show_files()
    
    def _show_files(self):
        """执行展示目录下的文件"""
        dir_path = self.dir_edit.text().strip()
        if not dir_path:
            self.showError("请输入或选择目录路径")
            return
        
        if not os.path.exists(dir_path):
            self.showError("目录路径不存在")
            return
        
        # 获取目录下的所有文件
        try:
            self.selected_files = []
            for item in os.listdir(dir_path):
                item_path = os.path.join(dir_path, item)
                if os.path.isfile(item_path):
                    self.selected_files.append(item_path)
            
            # 更新表格显示
            self.update_file_table()
        except Exception as e:
            self.showError(f"获取文件列表时出错: {str(e)}")
    
    def clear_files(self):
        """清空已选择的文件"""
        self.selected_files.clear()
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
            
            # 设置文件路径
            self.table_widget.setItem(row, 1, QTableWidgetItem(file_path))
    
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
            # 更新表格显示
            self.update_file_table()
            # 更新目录路径为第一个文件的目录
            if self.dir_edit.text().strip() == "":
                first_file_dir = os.path.dirname(files[0])
                self.dir_edit.setText(first_file_dir)
    
    def _update_table_after_modification(self):
        """更新表格显示修改后的结果"""
        dir_path = self.dir_edit.text().strip()
        if not dir_path or not os.path.exists(dir_path):
            return
        
        # 重新获取目录下的所有文件
        try:
            self.selected_files = []
            for item in os.listdir(dir_path):
                item_path = os.path.join(dir_path, item)
                if os.path.isfile(item_path):
                    self.selected_files.append(item_path)
            
            # 更新表格显示
            self.update_file_table()
        except Exception as e:
            print(f"更新表格时出错: {str(e)}")
    
    def _on_operation_changed(self, text):
        """操作类型改变时的处理"""
        if text == "删除内容":
            # 修改为删除内容模式
            self.content_label.setText("删除内容：")
            self.content_edit.setPlaceholderText("请输入要删除的文本")
            self.position_label.hide()  # 隐藏插入位置标签
            self.position_combo.hide()  # 隐藏插入位置选择
        else:
            # 修改为插入内容模式
            self.content_label.setText("插入内容：")
            self.content_edit.setPlaceholderText("请输入要插入的文本")
            self.position_label.show()  # 显示插入位置标签
            self.position_combo.show()  # 显示插入位置选择
    
    def execute(self):
        """执行文件名称修改"""
        # 验证输入
        if not self.selected_files:
            self.showError("请选择要修改的文件")
            return
        
        operation = self.operation_combo.currentText()
        content = self.content_edit.text().strip()
        
        if not content:
            if operation == "删除内容":
                self.showError("请输入要删除的内容")
            else:
                self.showError("请输入要插入的内容")
            return
        
        if operation == "删除内容":
            self._delete_content(content)
        else:
            position = self.position_combo.currentText()
            self._insert_content(content, position)
    
    def _delete_content(self, content):
        """删除文件名称中的指定内容"""
        self.showProgress("正在删除文件名称中的指定内容...")
        
        success_count = 0
        fail_count = 0
        total = len(self.selected_files)
        
        try:
            for index, file_path in enumerate(self.selected_files):
                try:
                    # 获取文件所在目录和文件名
                    dir_path = os.path.dirname(file_path)
                    file_name = os.path.basename(file_path)
                    
                    new_name = file_name.replace(content, '')
                    new_path = os.path.join(dir_path, new_name)
                    
                    # 检查新名称是否已存在
                    if not os.path.exists(new_path):
                        os.rename(file_path, new_path)
                        success_count += 1
                    else:
                        fail_count += 1
                except Exception as e:
                    fail_count += 1
                    print(f"修改 {file_path} 失败: {e}")
                
                # 更新进度
                progress = int((index + 1) / total * 100)
                self.updateProgress(progress, f"正在处理: {file_name}")
        except Exception as e:
            self.showError(f"修改名称时出错: {str(e)}")
            return
        
        # 更新表格显示修改后的结果
        self._update_table_after_modification()
        
        self.showSuccess(f"名称修改完成\n成功: {success_count} 个\n失败: {fail_count} 个")
    
    def _insert_content(self, content, position):
        """在文件名称中插入指定内容"""
        self.showProgress("正在文件名称中插入指定内容...")
        
        success_count = 0
        fail_count = 0
        total = len(self.selected_files)
        
        try:
            for index, file_path in enumerate(self.selected_files):
                try:
                    # 获取文件所在目录和文件名
                    dir_path = os.path.dirname(file_path)
                    file_name = os.path.basename(file_path)
                    
                    name, ext = os.path.splitext(file_name)
                    if position == "前缀":
                        new_name = content + name + ext
                    else:
                        new_name = name + content + ext
                    
                    new_path = os.path.join(dir_path, new_name)
                    os.rename(file_path, new_path)
                    success_count += 1
                except Exception as e:
                    fail_count += 1
                    print(f"修改 {file_path} 失败: {e}")
                
                # 更新进度
                progress = int((index + 1) / total * 100)
                self.updateProgress(progress, f"正在处理: {file_name}")
        except Exception as e:
            self.showError(f"修改名称时出错: {str(e)}")
            return
        
        # 更新表格显示修改后的结果
        self._update_table_after_modification()
        
        self.showSuccess(f"名称修改完成\n成功: {success_count} 个\n失败: {fail_count} 个")