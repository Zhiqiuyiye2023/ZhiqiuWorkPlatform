"""
批量复制/移动功能对话框
作者: 知秋一叶
版本号: 0.0.5
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, 
                            QTextEdit, QFileDialog, QLabel, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar)
from qfluentwidgets import (BodyLabel, PushButton, ComboBox, MessageBox, 
                           InfoBar, InfoBarPosition)
from .base_dialog import BaseFileProcessDialog
from functions.processor import FileBatchProcessor


class BatchCopyMoveDialog(BaseFileProcessDialog):
    """批量复制/移动功能对话框"""
    
    def __init__(self, parent=None):
        super().__init__("批量复制/移动/删除文件/文件夹", parent)
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
        
        # 列选择
        column_layout = QHBoxLayout()
        self.source_col_label = BodyLabel("源路径列:")
        self.source_col_combo = ComboBox()
        self.source_col_combo.setPlaceholderText("请选择源路径列")
        self.source_col_combo.setFixedHeight(35)
        
        self.target_col_label = BodyLabel("目标路径列:")
        self.target_col_combo = ComboBox()
        self.target_col_combo.setPlaceholderText("请选择目标路径列")
        self.target_col_combo.setFixedHeight(35)
        
        self.load_to_table_button = PushButton("加载到表格")
        self.load_to_table_button.setFixedHeight(35)
        self.load_to_table_button.clicked.connect(self.load_copy_to_table)
        
        column_layout.addWidget(self.source_col_label)
        column_layout.addWidget(self.source_col_combo)
        column_layout.addWidget(self.target_col_label)
        column_layout.addWidget(self.target_col_combo)
        column_layout.addWidget(self.load_to_table_button)
        self.addContentLayout(column_layout)
        
        # 文本输入区域 - 横向排列
        input_layout = QHBoxLayout()
        
        # 左侧：源路径列表
        left_layout = QVBoxLayout()
        self.source_list_label = BodyLabel("源路径列表:")
        self.source_text = QTextEdit()
        self.source_text.setFixedHeight(100)
        self.source_text.setPlaceholderText("请输入源文件/文件夹完整路径，每行一个")
        sample_source = "请输入源文件/文件夹完整路径，每行一个\n例如：\nc:\\source\\file.txt\nc:\\source\\folder"
        self.source_text.setPlainText(sample_source)
        
        left_layout.addWidget(self.source_list_label)
        left_layout.addWidget(self.source_text)
        
        # 右侧：目标路径列表
        right_layout = QVBoxLayout()
        self.target_list_label = BodyLabel("目标路径列表:")
        self.target_text = QTextEdit()
        self.target_text.setFixedHeight(100)
        self.target_text.setPlaceholderText("请输入目标文件/文件夹完整路径，每行一个")
        sample_target = "请输入目标文件/文件夹完整路径，每行一个\n例如：\nc:\\target\\file.txt\nc:\\target\\folder"
        self.target_text.setPlainText(sample_target)
        
        right_layout.addWidget(self.target_list_label)
        right_layout.addWidget(self.target_text)
        
        input_layout.addLayout(left_layout)
        input_layout.addLayout(right_layout)
        self.addContentLayout(input_layout)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        self.load_to_table_button2 = PushButton("加载到表格")
        self.load_to_table_button2.setFixedHeight(35)
        self.load_to_table_button2.clicked.connect(self.load_text_to_table)
        
        self.execute_copy_button = PushButton("执行复制")
        self.execute_copy_button.setFixedHeight(35)
        self.execute_copy_button.clicked.connect(self.execute_copy)
        
        self.execute_move_button = PushButton("执行移动")
        self.execute_move_button.setFixedHeight(35)
        self.execute_move_button.clicked.connect(self.execute_move)
        
        self.execute_delete_button = PushButton("执行删除")
        self.execute_delete_button.setFixedHeight(35)
        self.execute_delete_button.clicked.connect(self.execute_delete)
        
        self.create_folder_button = PushButton("创建文件夹")
        self.create_folder_button.setFixedHeight(35)
        self.create_folder_button.clicked.connect(self.batch_create_folders)
        
        button_layout.addWidget(self.load_to_table_button2)
        button_layout.addWidget(self.execute_copy_button)
        button_layout.addWidget(self.execute_move_button)
        button_layout.addWidget(self.execute_delete_button)
        button_layout.addWidget(self.create_folder_button)
        self.addContentLayout(button_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(25)
        self.addContentWidget(self.progress_bar)
        
        # 统计结果标签
        self.stat_label = BodyLabel("共计 0 行")
        self.addContentWidget(self.stat_label)
        
        # 复制/移动表格
        self.copy_table = QTableWidget()
        self.copy_table.setColumnCount(3)
        self.copy_table.setHorizontalHeaderLabels(["源路径", "目标路径", "结果"])
        self.copy_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.copy_table.setAlternatingRowColors(True)
        self.copy_table.setFixedHeight(200)
        self.addContentWidget(self.copy_table)
    
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
            columns = self.processor.load_copy_excel_columns(excel_path)
            self.source_col_combo.clear()
            self.target_col_combo.clear()
            self.source_col_combo.addItems(columns)
            self.target_col_combo.addItems(columns)
        except Exception as e:
            InfoBar.error(
                title='错误',
                content=f'加载Excel文件时出错: {str(e)}',
                parent=self,
                duration=3000
            )
    
    def load_copy_to_table(self):
        """从Excel加载复制/移动数据到表格"""
        excel_path = self.excel_edit.text()
        source_col = self.source_col_combo.currentText()
        target_col = self.target_col_combo.currentText()
        
        if not excel_path:
            InfoBar.warning(
                title='警告',
                content='请选择Excel文件',
                parent=self,
                duration=2000
            )
            return
            
        # 允许只选择目标名称列，但不允许只选择源名称列
        if not source_col and not target_col:
            InfoBar.warning(
                title='警告',
                content='请选择至少一个列',
                parent=self,
                duration=2000
            )
            return
        elif source_col and not target_col:
            InfoBar.warning(
                title='警告',
                content='只选择源名称列无法创建文件夹，请同时选择目标名称列',
                parent=self,
                duration=2000
            )
            return
            
        try:
            copy_data = self.processor.load_copy_from_excel(excel_path, source_col, target_col)
            self.display_copy_data(copy_data)
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
        """从文本加载复制/移动数据到表格"""
        source_text = self.source_text.toPlainText()
        target_text = self.target_text.toPlainText()
        
        try:
            copy_data = self.processor.load_copy_from_text(source_text, target_text)
            self.display_copy_data(copy_data)
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
    
    def display_copy_data(self, copy_data):
        """显示复制/移动数据"""
        self.copy_table.setRowCount(len(copy_data))
        for i, item in enumerate(copy_data):
            if len(item) >= 2:
                source_path, target_path = item[0], item[1]
                self.copy_table.setItem(i, 0, QTableWidgetItem(str(source_path)))
                self.copy_table.setItem(i, 1, QTableWidgetItem(str(target_path)))
                # 清空结果列
                self.copy_table.setItem(i, 2, QTableWidgetItem(""))
            else:
                # 对于批量创建文件夹的情况
                folder_path = item[0]
                self.copy_table.setItem(i, 0, QTableWidgetItem(""))
                self.copy_table.setItem(i, 1, QTableWidgetItem(str(folder_path)))
                self.copy_table.setItem(i, 2, QTableWidgetItem(""))
        
        # 更新统计标签
        self.stat_label.setText(f"共计 {len(copy_data)} 行")
    
    def execute_copy(self):
        """执行批量复制"""
        self._execute_operation(is_copy=True)
    
    def execute_move(self):
        """执行批量移动"""
        self._execute_operation(is_copy=False)
    
    def execute_delete(self):
        """执行批量删除"""
        if not self.copy_table.rowCount():
            InfoBar.warning(
                title='警告',
                content='没有要处理的数据',
                parent=self,
                duration=2000
            )
            return
            
        try:
            # 收集操作数据
            delete_data = []
            for i in range(self.copy_table.rowCount()):
                source_item = self.copy_table.item(i, 0)
                if source_item:
                    source_path = source_item.text()
                    if source_path:
                        delete_data.append(source_path)
            
            if not delete_data:
                InfoBar.warning(
                    title='警告',
                    content='没有有效的删除路径',
                    parent=self,
                    duration=2000
                )
                return
            
            # 显示进度条
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, len(delete_data))
            self.progress_bar.setValue(0)
            
            success_count, fail_count, processed_items = self.processor.execute_delete(delete_data)
            operation_name = "删除"
            
            # 清空表格，只显示失败的操作
            self.copy_table.setRowCount(0)
            
            # 更新表格显示操作结果，只显示失败的
            for source_path, target_path, status, result_msg in processed_items:
                if status == '失败':
                    # 添加新行
                    row = self.copy_table.rowCount()
                    self.copy_table.insertRow(row)
                    
                    # 设置源路径列
                    source_item = QTableWidgetItem(source_path)
                    self.copy_table.setItem(row, 0, source_item)
                    
                    # 设置目标路径列为空
                    target_item = QTableWidgetItem("")
                    self.copy_table.setItem(row, 1, target_item)
                    
                    # 设置结果列，使用红色文本
                    result_text = f"{status}: {result_msg}"
                    result_item = QTableWidgetItem(result_text)
                    # 设置红色文本
                    from PyQt6.QtGui import QColor, QBrush, QFont
                    result_item.setForeground(QBrush(QColor(255, 0, 0)))
                    self.copy_table.setItem(row, 2, result_item)
            
            # 更新统计标签
            self.stat_label.setText(f"共计 {self.copy_table.rowCount()} 行")
            
            # 隐藏进度条
            self.progress_bar.setVisible(False)
            
            InfoBar.success(
                title='完成',
                content=f'{operation_name}操作完成\n成功: {success_count} 个\n失败: {fail_count} 个\n失败的操作已显示在表格中',
                parent=self,
                duration=3000
            )
        except Exception as e:
            self.progress_bar.setVisible(False)
            InfoBar.error(
                title='错误',
                content=f'操作时出错: {str(e)}',
                parent=self,
                duration=3000
            )
    
    def _execute_operation(self, is_copy=True):
        """执行批量操作"""
        if not self.copy_table.rowCount():
            InfoBar.warning(
                title='警告',
                content='没有要处理的数据',
                parent=self,
                duration=2000
            )
            return
            
        try:
            # 收集操作数据
            copy_data = []
            for i in range(self.copy_table.rowCount()):
                source_item = self.copy_table.item(i, 0)
                target_item = self.copy_table.item(i, 1)
                if source_item and target_item:
                    source_path = source_item.text()
                    target_path = target_item.text()
                    if source_path and target_path:
                        copy_data.append((source_path, target_path))
            
            if not copy_data:
                InfoBar.warning(
                    title='警告',
                    content='没有有效的操作数据',
                    parent=self,
                    duration=2000
                )
                return
            
            # 显示进度条
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, len(copy_data))
            self.progress_bar.setValue(0)
            
            if is_copy:
                success_count, fail_count, processed_items = self.processor.execute_copy(copy_data)
                operation_name = "复制"
            else:
                success_count, fail_count, processed_items = self.processor.execute_move(copy_data)
                operation_name = "移动"
            
            # 清空表格，只显示失败的操作
            self.copy_table.setRowCount(0)
            
            # 更新表格显示操作结果，只显示失败的
            for source_path, target_path, status, result_msg in processed_items:
                if status == '失败':
                    # 添加新行
                    row = self.copy_table.rowCount()
                    self.copy_table.insertRow(row)
                    
                    # 设置源路径列
                    source_item = QTableWidgetItem(source_path)
                    self.copy_table.setItem(row, 0, source_item)
                    
                    # 设置目标路径列
                    target_item = QTableWidgetItem(target_path)
                    self.copy_table.setItem(row, 1, target_item)
                    
                    # 设置结果列，使用红色文本
                    result_text = f"{status}: {result_msg}"
                    result_item = QTableWidgetItem(result_text)
                    # 设置红色文本
                    from PyQt6.QtGui import QColor, QBrush, QFont
                    result_item.setForeground(QBrush(QColor(255, 0, 0)))
                    self.copy_table.setItem(row, 2, result_item)
            
            # 更新统计标签
            self.stat_label.setText(f"共计 {self.copy_table.rowCount()} 行")
            
            # 隐藏进度条
            self.progress_bar.setVisible(False)
            
            InfoBar.success(
                title='完成',
                content=f'{operation_name}操作完成\n成功: {success_count} 个\n失败: {fail_count} 个\n失败的操作已显示在表格中',
                parent=self,
                duration=3000
            )
        except Exception as e:
            self.progress_bar.setVisible(False)
            InfoBar.error(
                title='错误',
                content=f'操作时出错: {str(e)}',
                parent=self,
                duration=3000
            )
    
    def batch_create_folders(self):
        """批量创建文件夹"""
        # 从目标路径列表和表格中读取要创建的文件夹路径
        folder_paths = []
        
        # 1. 从目标路径列表输入框读取
        target_text = self.target_text.toPlainText()
        target_lines = target_text.strip().split('\n')
        
        # 清理列表，移除空行和示例行
        def clean_lines(lines):
            cleaned = []
            for line in lines:
                stripped = line.strip()
                if stripped and "例如：" not in stripped and "请输入" not in stripped:
                    cleaned.append(stripped)
            return cleaned
        
        input_folder_paths = clean_lines(target_lines)
        folder_paths.extend(input_folder_paths)
        
        # 2. 从表格中读取目标路径
        for i in range(self.copy_table.rowCount()):
            target_item = self.copy_table.item(i, 1)
            if target_item:
                target_path = target_item.text()
                if target_path and target_path not in folder_paths:  # 避免重复
                    folder_paths.append(target_path)
        
        if not folder_paths:
            InfoBar.warning(
                title='警告',
                content='请输入要创建的文件夹路径或在表格中添加目标路径',
                parent=self,
                duration=2000
            )
            return
        
        try:
            # 显示进度条
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, len(folder_paths))
            self.progress_bar.setValue(0)
            
            success_count, fail_count, created_folders = self.processor.batch_create_folders(folder_paths)
            
            # 清空表格，只显示失败的操作
            self.copy_table.setRowCount(0)
            
            # 更新表格显示操作结果，只显示失败的
            for folder_path, status, result_msg in created_folders:
                if status == '失败':
                    # 添加新行
                    row = self.copy_table.rowCount()
                    self.copy_table.insertRow(row)
                    
                    # 设置源路径列为空（文件夹创建没有源路径）
                    source_item = QTableWidgetItem("")
                    self.copy_table.setItem(row, 0, source_item)
                    
                    # 设置目标路径列
                    target_item = QTableWidgetItem(folder_path)
                    self.copy_table.setItem(row, 1, target_item)
                    
                    # 设置结果列，使用红色文本
                    result_text = f"{status}: {result_msg}"
                    result_item = QTableWidgetItem(result_text)
                    # 设置红色文本
                    from PyQt6.QtGui import QColor, QBrush, QFont
                    result_item.setForeground(QBrush(QColor(255, 0, 0)))
                    self.copy_table.setItem(row, 2, result_item)
            
            # 更新统计标签
            self.stat_label.setText(f"共计 {self.copy_table.rowCount()} 行")
            
            # 隐藏进度条
            self.progress_bar.setVisible(False)
            
            InfoBar.success(
                title='完成',
                content=f'文件夹创建完成\n成功: {success_count} 个\n失败: {fail_count} 个\n失败的操作已显示在表格中',
                parent=self,
                duration=3000
            )
        except Exception as e:
            self.progress_bar.setVisible(False)
            InfoBar.error(
                title='错误',
                content=f'创建文件夹时出错: {str(e)}',
                parent=self,
                duration=3000
            )