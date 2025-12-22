"""
批量复制/移动功能
作者: 知秋一叶
版本号: 0.0.5
"""

from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QPushButton, QLineEdit, QLabel, QTextEdit, QFileDialog, QComboBox, QHeaderView, QTableWidgetItem
from qfluentwidgets import LineEdit, PushButton, TextEdit, ComboBox, TableWidget
from qfluentwidgets import FluentIcon as FIF
from .file_processor_base import BaseFileProcessorFunction
import os
import shutil


class BatchCopyMoveFunction(BaseFileProcessorFunction):
    """批量复制/移动功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>"
            "批量复制/替换/移动/删除/重命名文件/文件夹<br>"
            "支持从Excel或文本输入批量操作规则"
        )
        super().__init__("批量操作", description, parent)
        self._initUI()
    
    def _initUI(self):
        """初始化界面"""
        # Excel文件选择区域
        excel_layout = QHBoxLayout()
        excel_layout.addWidget(QLabel("Excel文件:"))
        
        self.excel_edit = LineEdit(self)
        self.excel_edit.setPlaceholderText("请选择Excel文件")
        self.excel_edit.setMinimumWidth(200)
        # 添加文本变化信号，自动加载列名
        self.excel_edit.textChanged.connect(self._auto_load_columns)
        
        self.excel_browse_button = PushButton("选择Excel", self, FIF.DOCUMENT)
        self.excel_browse_button.clicked.connect(lambda: self.browse_file(self.excel_edit, "Excel Files (*.xlsx *.xls)"))
        
        self.load_excel_button = PushButton("加载数据", self, FIF.SYNC)
        self.load_excel_button.clicked.connect(self.load_copy_to_table)
        
        excel_layout.addWidget(self.excel_edit)
        excel_layout.addWidget(self.excel_browse_button)
        excel_layout.addWidget(self.load_excel_button)
        self.contentLayout.addLayout(excel_layout)
        
        # 列选择区域 - 一行展示，标签与下拉控件对应
        column_layout = QHBoxLayout()
        
        # 源路径列
        source_layout = QHBoxLayout()
        source_label = QLabel("源路径列:")
        source_label.setStyleSheet("margin-right: 5px;")
        self.source_col_combo = ComboBox(self)
        self.source_col_combo.setFixedWidth(150)
        source_layout.addWidget(source_label)
        source_layout.addWidget(self.source_col_combo)
        
        # 目标路径列
        target_layout = QHBoxLayout()
        target_label = QLabel("目标路径列:")
        target_label.setStyleSheet("margin-right: 5px;")
        self.target_col_combo = ComboBox(self)
        self.target_col_combo.setFixedWidth(150)
        target_layout.addWidget(target_label)
        target_layout.addWidget(self.target_col_combo)
        
        column_layout.addLayout(source_layout)
        column_layout.addSpacing(20)
        column_layout.addLayout(target_layout)
        
        self.contentLayout.addLayout(column_layout)
        
        # 输入区域
        input_layout = QHBoxLayout()
        
        # 左侧：源路径列表
        left_layout = QVBoxLayout()
        self.source_list_label = QLabel("源路径列表:")
        self.source_text = TextEdit(self)
        self.source_text.setPlaceholderText("请输入源路径，每行一个\n例如：\nC:/source/file1.txt\nC:/source/file2.txt")
        self.source_text.setFixedHeight(100)
        
        left_layout.addWidget(self.source_list_label)
        left_layout.addWidget(self.source_text)
        
        # 右侧：目标路径列表
        right_layout = QVBoxLayout()
        self.target_list_label = QLabel("目标路径列表:")
        self.target_text = TextEdit(self)
        self.target_text.setPlaceholderText("请输入目标路径，每行一个\n例如：\nD:/target/file1.txt\nD:/target/file2.txt")
        self.target_text.setFixedHeight(100)
        
        right_layout.addWidget(self.target_list_label)
        right_layout.addWidget(self.target_text)
        
        input_layout.addLayout(left_layout)
        input_layout.addLayout(right_layout)
        self.contentLayout.addLayout(input_layout)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        self.load_to_table_button2 = PushButton("加载到表格", self, FIF.SYNC)
        self.execute_copy_button = PushButton("执行复制", self, FIF.COPY)
        self.execute_replace_button = PushButton("执行替换", self, FIF.UPDATE)
        self.execute_move_button = PushButton("执行移动", self, FIF.MOVE)
        self.execute_delete_button = PushButton("执行删除", self, FIF.DELETE)
        self.execute_rename_button = PushButton("执行重命名", self, FIF.EDIT)
        
        self.load_to_table_button2.clicked.connect(self.load_text_to_table)
        self.execute_copy_button.clicked.connect(self.execute_copy)
        self.execute_replace_button.clicked.connect(self.execute_replace)
        self.execute_move_button.clicked.connect(self.execute_move)
        self.execute_delete_button.clicked.connect(self.execute_delete)
        self.execute_rename_button.clicked.connect(self.execute_rename)
        
        button_layout.addWidget(self.load_to_table_button2)
        button_layout.addWidget(self.execute_copy_button)
        button_layout.addWidget(self.execute_replace_button)
        button_layout.addWidget(self.execute_move_button)
        button_layout.addWidget(self.execute_delete_button)
        button_layout.addWidget(self.execute_rename_button)
        self.contentLayout.addLayout(button_layout)
        
        # 统计结果标签
        self.stat_label = QLabel("共计 0 行")
        self.contentLayout.addWidget(self.stat_label)
        
        # 复制/移动表格
        self.copy_table = TableWidget(self)
        self.copy_table.setColumnCount(3)
        self.copy_table.setHorizontalHeaderLabels(["源路径", "目标路径", "结果"])
        self.copy_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.copy_table.setAlternatingRowColors(True)
        self.copy_table.setFixedHeight(200)
        self.copy_table.setBorderVisible(True)
        self.contentLayout.addWidget(self.copy_table)

    def _auto_load_columns(self, text):
        """自动加载Excel列名"""
        if text and os.path.exists(text) and (text.endswith('.xlsx') or text.endswith('.xls')):
            try:
                import pandas as pd
                df = pd.read_excel(text)
                columns = df.columns.tolist()
                
                self.source_col_combo.clear()
                self.target_col_combo.clear()
                
                self.source_col_combo.addItems(columns)
                self.target_col_combo.addItems(columns)
            except Exception as e:
                # 自动加载失败不显示错误，仅在手动加载时显示
                pass
    
    def load_copy_to_table(self):
        """从Excel加载复制/移动数据到表格"""
        excel_path = self.excel_edit.text()
        source_col = self.source_col_combo.currentText()
        target_col = self.target_col_combo.currentText()
        
        if not excel_path:
            self.show_warning("警告", "请选择Excel文件")
            return
            
        # 允许只选择目标名称列，但不允许只选择源名称列
        if not source_col and not target_col:
            self.show_warning("警告", "请选择至少一个列")
            return
        elif source_col and not target_col:
            self.show_warning("警告", "只选择源名称列无法创建文件夹，请同时选择目标名称列")
            return
            
        try:
            import pandas as pd
            df = pd.read_excel(excel_path)
            copy_data = []
            
            if not source_col and target_col:
                # 只选择了目标列，则源路径使用Excel文件所在目录
                source_base = os.path.dirname(excel_path)
                for _, row in df.iterrows():
                    target_path = str(row[target_col])
                    copy_data.append((source_base, target_path))
            else:
                # 同时选择了源和目标列
                for _, row in df.iterrows():
                    source_path = str(row[source_col])
                    target_path = str(row[target_col])
                    copy_data.append((source_path, target_path))
            
            self.display_copy_data(copy_data)
            self.show_success("成功", "数据加载完成")
        except Exception as e:
            self.show_error("错误", f"加载Excel数据时出错: {str(e)}")
    
    def load_text_to_table(self):
        """从文本加载复制/移动数据到表格"""
        source_text = self.source_text.toPlainText()
        target_text = self.target_text.toPlainText()
        
        try:
            source_lines = source_text.strip().split('\n')
            target_lines = target_text.strip().split('\n')
            
            # 清理空行
            source_lines = [line.strip() for line in source_lines if line.strip()]
            target_lines = [line.strip() for line in target_lines if line.strip()]
            
            copy_data = []
            for source_path, target_path in zip(source_lines, target_lines):
                copy_data.append((source_path, target_path))
                
            self.display_copy_data(copy_data)
            self.show_success("成功", "数据加载完成")
        except Exception as e:
            self.show_error("错误", f"加载文本数据时出错: {str(e)}")
    
    def display_copy_data(self, copy_data):
        """显示复制/移动数据"""
        self.copy_table.setRowCount(len(copy_data))
        for i, (source_path, target_path) in enumerate(copy_data):
            self.copy_table.setItem(i, 0, QTableWidgetItem(str(source_path)))
            self.copy_table.setItem(i, 1, QTableWidgetItem(str(target_path)))
            # 清空结果列
            self.copy_table.setItem(i, 2, QTableWidgetItem(""))
        # 更新统计标签
        self.stat_label.setText(f"共计 {len(copy_data)} 行")
    
    def execute_copy(self):
        """执行批量复制"""
        self._execute_operation(is_copy=True, is_replace=False)
    
    def execute_replace(self):
        """执行批量替换"""
        self._execute_operation(is_copy=True, is_replace=True)
    
    def execute_move(self):
        """执行批量移动"""
        self._execute_operation(is_copy=False, is_replace=False)
    
    def execute_delete(self):
        """执行批量删除"""
        if not self.copy_table.rowCount():
            self.show_warning("警告", "没有要处理的数据")
            return
        
        try:
            self.showProgress("正在执行删除操作...")
            
            # 收集操作数据
            delete_data = []
            for i in range(self.copy_table.rowCount()):
                source_item = self.copy_table.item(i, 0)
                if source_item:
                    source_path = source_item.text()
                    if source_path:
                        delete_data.append(source_path)
            
            if not delete_data:
                self.show_warning("警告", "没有有效的删除路径")
                return
            
            success_count = 0
            fail_count = 0
            failed_operations = []
            
            for path in delete_data:
                try:
                    if os.path.isfile(path):
                        # 删除文件
                        os.remove(path)
                    elif os.path.isdir(path):
                        # 删除目录及其内容
                        shutil.rmtree(path)
                    else:
                        raise FileNotFoundError(f"路径不存在: {path}")
                    
                    success_count += 1
                except Exception as e:
                    fail_count += 1
                    failed_operations.append((path, str(e)))
                    print(f"删除失败 {path}: {str(e)}")
            
            # 清空表格，只显示失败的操作
            self.copy_table.setRowCount(0)
            
            # 显示失败的操作，使用红色文本
            from PyQt6.QtGui import QColor, QBrush
            for path, result_msg in failed_operations:
                # 添加新行
                row = self.copy_table.rowCount()
                self.copy_table.insertRow(row)
                
                # 设置源路径列
                source_item = QTableWidgetItem(path)
                self.copy_table.setItem(row, 0, source_item)
                
                # 设置目标路径列为空
                target_item = QTableWidgetItem("")
                self.copy_table.setItem(row, 1, target_item)
                
                # 设置结果列，使用红色文本
                result_text = f"删除失败: {result_msg}"
                result_item = QTableWidgetItem(result_text)
                # 设置红色文本
                result_item.setForeground(QBrush(QColor(255, 0, 0)))
                self.copy_table.setItem(row, 2, result_item)
            
            # 更新统计标签
            self.stat_label.setText(f"共计 {self.copy_table.rowCount()} 行")
            
            self.showSuccess(f"删除操作完成\n成功: {success_count} 个\n失败: {fail_count} 个\n失败的操作已显示在表格中")
        except Exception as e:
            self.showError(f"删除操作出错: {str(e)}")
        finally:
            self.hideProgress()
    
    def execute_rename(self):
        """执行批量重命名"""
        if not self.copy_table.rowCount():
            self.show_warning("警告", "没有要处理的数据")
            return
        
        try:
            self.showProgress("正在执行重命名操作...")
            
            # 收集操作数据
            rename_data = []
            for i in range(self.copy_table.rowCount()):
                source_item = self.copy_table.item(i, 0)
                target_item = self.copy_table.item(i, 1)
                if source_item and target_item:
                    source_path = source_item.text()
                    target_path = target_item.text()
                    if source_path and target_path:
                        rename_data.append((source_path, target_path))
            
            if not rename_data:
                self.show_warning("警告", "没有有效的重命名数据")
                return
            
            success_count = 0
            fail_count = 0
            failed_operations = []
            
            for source_path, target_path in rename_data:
                try:
                    # 检查源路径是否存在
                    if not os.path.exists(source_path):
                        raise FileNotFoundError(f"源路径不存在: {source_path}")
                    
                    # 检查目标路径的父目录是否存在，不存在则创建
                    target_dir = os.path.dirname(target_path)
                    if target_dir and not os.path.exists(target_dir):
                        os.makedirs(target_dir, exist_ok=True)
                    
                    # 执行重命名
                    os.rename(source_path, target_path)
                    success_count += 1
                except Exception as e:
                    fail_count += 1
                    failed_operations.append((source_path, target_path, str(e)))
                    print(f"重命名失败 {source_path} -> {target_path}: {str(e)}")
            
            # 清空表格，只显示失败的操作
            self.copy_table.setRowCount(0)
            
            # 显示失败的操作，使用红色文本
            from PyQt6.QtGui import QColor, QBrush
            for source_path, target_path, result_msg in failed_operations:
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
                result_text = f"重命名失败: {result_msg}"
                result_item = QTableWidgetItem(result_text)
                # 设置红色文本
                result_item.setForeground(QBrush(QColor(255, 0, 0)))
                self.copy_table.setItem(row, 2, result_item)
            
            # 更新统计标签
            self.stat_label.setText(f"共计 {self.copy_table.rowCount()} 行")
            
            self.showSuccess(f"重命名操作完成\n成功: {success_count} 个\n失败: {fail_count} 个\n失败的操作已显示在表格中")
        except Exception as e:
            self.showError(f"重命名操作出错: {str(e)}")
        finally:
            self.hideProgress()
    
    def _execute_operation(self, is_copy=True, is_replace=False):
        """执行批量操作
        
        参数:
            is_copy: 是否为复制操作，False表示移动操作
            is_replace: 是否替换已存在的文件/目录
        """
        if not self.copy_table.rowCount():
            self.show_warning("警告", "没有要处理的数据")
            return
            
        try:
            self.showProgress("正在执行操作...")
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
                self.show_warning("警告", "没有有效的操作数据")
                return
            
            success_count = 0
            fail_count = 0
            failed_operations = []
            
            for source_path, target_path in copy_data:
                try:
                    # 判断源路径是否以斜杠结尾
                    ends_with_slash = source_path.endswith('\\') or source_path.endswith('/')
                    
                    if ends_with_slash:
                        # 以斜杠结尾，表示复制/移动整个目录
                        source_path = source_path.rstrip('\\/')  # 去除末尾斜杠
                        
                        if is_copy:
                            # 复制整个目录
                            if os.path.exists(target_path):
                                if is_replace:
                                    # 替换模式，删除已存在的目录
                                    shutil.rmtree(target_path)
                                else:
                                    # 复制模式，跳过已存在的目录
                                    fail_count += 1
                                    failed_operations.append((source_path, target_path, f"目录已存在，跳过: {target_path}"))
                                    print(f"目录已存在，跳过: {target_path}")
                                    continue
                            shutil.copytree(source_path, target_path)
                        else:
                            # 移动整个目录
                            shutil.move(source_path, target_path)
                    else:
                        # 不以斜杠结尾
                        if os.path.isfile(source_path):
                            # 源路径是文件，执行文件操作
                            # 确保目标目录存在
                            target_dir = os.path.dirname(target_path)
                            if target_dir and not os.path.exists(target_dir):
                                os.makedirs(target_dir)
                            
                            if is_copy:
                                if os.path.exists(target_path):
                                    if is_replace:
                                        # 替换模式，直接覆盖
                                        shutil.copy2(source_path, target_path)
                                    else:
                                        # 复制模式，跳过已存在的文件
                                        fail_count += 1
                                        failed_operations.append((source_path, target_path, f"文件已存在，跳过: {target_path}"))
                                        print(f"文件已存在，跳过: {target_path}")
                                        continue
                                else:
                                    # 文件不存在，直接复制
                                    shutil.copy2(source_path, target_path)
                            else:
                                # 移动文件
                                shutil.move(source_path, target_path)
                        elif os.path.isdir(source_path):
                            # 源路径是目录，表示复制/移动该目录下的所有文件
                            # 确保目标目录存在
                            if not os.path.exists(target_path):
                                os.makedirs(target_path)
                            
                            # 遍历源目录下的所有文件
                            for item in os.listdir(source_path):
                                item_path = os.path.join(source_path, item)
                                if os.path.isfile(item_path):
                                    # 构建目标文件路径
                                    target_file = os.path.join(target_path, item)
                                    if is_copy:
                                        if os.path.exists(target_file):
                                            if is_replace:
                                                # 替换模式，直接覆盖
                                                shutil.copy2(item_path, target_file)
                                            else:
                                                # 复制模式，跳过已存在的文件
                                                print(f"文件已存在，跳过: {target_file}")
                                                continue
                                        else:
                                            # 文件不存在，直接复制
                                            shutil.copy2(item_path, target_file)
                                    else:
                                        # 移动文件
                                        shutil.move(item_path, target_file)
                        else:
                            raise FileNotFoundError(f"源路径不存在: {source_path}")
                    
                    success_count += 1
                except Exception as e:
                    fail_count += 1
                    error_msg = f"操作失败 {source_path} -> {target_path}: {str(e)}"
                    failed_operations.append((source_path, target_path, str(e)))
                    print(error_msg)
            
            operation_name = "复制" if is_copy else "移动"
            if is_copy and is_replace:
                operation_name = "替换"
            
            # 清空表格，只显示失败的操作
            self.copy_table.setRowCount(0)
            
            # 显示失败的操作，使用红色文本
            from PyQt6.QtGui import QColor, QBrush
            for source_path, target_path, result_msg in failed_operations:
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
                result_text = f"失败: {result_msg}"
                result_item = QTableWidgetItem(result_text)
                # 设置红色文本
                result_item.setForeground(QBrush(QColor(255, 0, 0)))
                self.copy_table.setItem(row, 2, result_item)
            
            # 更新统计标签
            self.stat_label.setText(f"共计 {self.copy_table.rowCount()} 行")
            
            self.showSuccess(f"{operation_name}操作完成\n成功: {success_count} 个\n失败: {fail_count} 个\n失败的操作已显示在表格中")
        except Exception as e:
            self.showError(f"操作时出错: {str(e)}")
        finally:
            self.hideProgress()