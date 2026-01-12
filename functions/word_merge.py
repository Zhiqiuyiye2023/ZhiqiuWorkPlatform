# coding:utf-8
"""
Word文档合并功能
用于合并多个Word文档，支持拖入文件和添加目录
"""

import os
from PyQt6.QtWidgets import (QHBoxLayout, QVBoxLayout, QLabel, QFileDialog, 
                             QListWidget, QListWidgetItem, QPushButton, 
                             QSplitter, QMessageBox, QGroupBox, QTableWidgetItem)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from qfluentwidgets import (PushButton, ComboBox, LineEdit, TextEdit, 
                           InfoBar, InfoBarPosition, PrimaryPushButton, 
                           FluentIcon, ListWidget)
from .file_processor_base import BaseFileProcessorFunction
# Word文档合并核心功能
import os
from docx import Document

def merge_word_documents(source_dir, output_path):
    """
    合并目录下所有Word文档到一个文件中，保持源格式
    
    Args:
        source_dir (str): 源目录路径
        output_path (str): 输出文件路径
    """
    # 获取目录下所有.docx文件
    docx_files = []
    for filename in os.listdir(source_dir):
        if filename.lower().endswith('.docx'):
            docx_files.append(os.path.join(source_dir, filename))
    
    if not docx_files:
        print(f"在目录 {source_dir} 中未找到任何.docx文件")
        return False
    
    # 按文件名排序，确保合并顺序一致
    docx_files.sort()
    
    print(f"找到 {len(docx_files)} 个Word文档:")
    for file in docx_files:
        print(f"  - {os.path.basename(file)}")
    
    # 读取第一个文档作为基础文档
    if docx_files:
        merged_doc = Document(docx_files[0])
        print(f"正在处理: {os.path.basename(docx_files[0])} (1/{len(docx_files)})")
        
        # 处理剩余的文档
        for idx, file_path in enumerate(docx_files[1:], start=2):
            print(f"正在处理: {os.path.basename(file_path)} ({idx}/{len(docx_files)})")
            
            # 临时加载源文档
            source_doc = Document(file_path)
            
            # 复制源文档的所有元素到合并文档
            for element in source_doc.element.body:
                if not element.tag.endswith('sectPr'):  # 跳过文档设置部分
                    merged_doc.element.body.append(element)
            
            # 添加分页符（除了最后一个文档）
            if idx < len(docx_files):
                merged_doc.add_page_break()
    
    # 保存合并后的文档
    merged_doc.save(output_path)
    print(f"合并完成！输出文件: {output_path}")
    return True


class WordMergeFunction(BaseFileProcessorFunction):
    """Word文档合并功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>" 
            "合并多个Word文档，支持拖入文件和添加目录<br>" 
            "可以调整合并顺序，设置默认路径"
        )
        super().__init__("Word文档合并", description, parent)
        self.init_ui()
    
    def init_ui(self):
        """初始化UI界面"""
        # 直接使用父类的contentLayout
        self.contentLayout.setContentsMargins(0, 0, 0, 0)
        self.contentLayout.setSpacing(15)
        
        # 创建文件列表区域
        self.create_file_list_section()
        
        # 创建输出设置区域
        self.create_output_settings_section()
        
    def create_file_list_section(self):
        """创建文件列表区域"""
        # 创建文件列表组
        self.file_list_group = QGroupBox("文件列表")
        self.file_list_layout = QVBoxLayout(self.file_list_group)
        self.file_list_layout.setSpacing(10)
        
        # 创建列表描述
        self.list_desc_label = QLabel("可以将Word文件拖入列表，或通过按钮添加文件/目录")
        self.list_desc_label.setStyleSheet("font-size: 12px; color: #666;")
        self.file_list_layout.addWidget(self.list_desc_label)
        
        # 创建文件列表表格
        from qfluentwidgets import TableWidget
        from PyQt6.QtWidgets import QHeaderView
        self.file_list_widget = TableWidget()
        self.file_list_widget.setColumnCount(1)
        self.file_list_widget.setHorizontalHeaderLabels(["文件路径"])
        self.file_list_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.file_list_widget.setAlternatingRowColors(True)
        self.file_list_widget.setFixedHeight(200)
        self.file_list_widget.setAcceptDrops(True)
        self.file_list_widget.dragEnterEvent = self.on_drag_enter
        self.file_list_widget.dropEvent = self.on_drop
        self.file_list_layout.addWidget(self.file_list_widget)
        
        # 创建列表操作按钮区域
        self.list_buttons_layout = QHBoxLayout()
        self.list_buttons_layout.setSpacing(10)
        
        # 添加文件按钮
        self.add_file_btn = PushButton("添加文件", icon=FluentIcon.ADD_TO)
        self.add_file_btn.clicked.connect(self.add_file)
        
        # 添加目录按钮
        self.add_dir_btn = PushButton("添加目录", icon=FluentIcon.FOLDER)
        self.add_dir_btn.clicked.connect(self.add_directory)
        
        # 移除选中按钮
        self.remove_selected_btn = PushButton("移除选中", icon=FluentIcon.DELETE)
        self.remove_selected_btn.clicked.connect(self.remove_selected)
        
        # 上移按钮
        self.move_up_btn = PushButton("上移", icon=FluentIcon.UP)
        self.move_up_btn.clicked.connect(self.move_up)
        
        # 下移按钮
        self.move_down_btn = PushButton("下移", icon=FluentIcon.DOWN)
        self.move_down_btn.clicked.connect(self.move_down)
        
        # 清空列表按钮
        self.clear_list_btn = PushButton("清空列表", icon=FluentIcon.DELETE)
        self.clear_list_btn.clicked.connect(self.clear_list)
        
        # 添加按钮到布局
        self.list_buttons_layout.addWidget(self.add_file_btn)
        self.list_buttons_layout.addWidget(self.add_dir_btn)
        self.list_buttons_layout.addWidget(self.remove_selected_btn)
        self.list_buttons_layout.addWidget(self.move_up_btn)
        self.list_buttons_layout.addWidget(self.move_down_btn)
        self.list_buttons_layout.addWidget(self.clear_list_btn)
        self.file_list_layout.addLayout(self.list_buttons_layout)
        
        # 添加到contentLayout
        self.contentLayout.addWidget(self.file_list_group)
    
    def create_output_settings_section(self):
        """创建输出设置区域"""
        # 创建输出设置组
        self.output_group = QGroupBox("输出设置")
        self.output_layout = QVBoxLayout(self.output_group)
        self.output_layout.setSpacing(10)
        
        # 输出路径设置
        self.output_path_layout = QHBoxLayout()
        self.output_path_label = QLabel("输出路径：")
        self.output_path_edit = LineEdit()
        self.output_path_edit.setPlaceholderText("选择输出文件路径")
        # 列表中未添加文件时不显示内容
        self.output_path_edit.setText("")
        
        self.browse_output_btn = PushButton("浏览", icon=FluentIcon.FOLDER)
        self.browse_output_btn.clicked.connect(self.browse_output_path)
        
        self.output_path_layout.addWidget(self.output_path_label)
        self.output_path_layout.addWidget(self.output_path_edit, 1)
        self.output_path_layout.addWidget(self.browse_output_btn)
        self.output_layout.addLayout(self.output_path_layout)
        
        # 输出文件名设置
        self.output_filename_layout = QHBoxLayout()
        self.output_filename_label = QLabel("输出文件名：")
        self.output_filename_edit = LineEdit()
        # 列表中未添加文件时不显示内容
        self.output_filename_edit.setText("")
        
        self.output_filename_layout.addWidget(self.output_filename_label)
        self.output_filename_layout.addWidget(self.output_filename_edit, 1)
        self.output_layout.addLayout(self.output_filename_layout)
        
        # 添加执行按钮
        self.execute_btn = PrimaryPushButton("开始合并", icon=FluentIcon.SEND)
        self.execute_btn.clicked.connect(self.execute_merge)
        self.output_layout.addWidget(self.execute_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 添加到contentLayout
        self.contentLayout.addWidget(self.output_group)
    
    def on_drag_enter(self, event):
        """处理拖入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def on_drop(self, event):
        """处理拖放事件"""
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path) and file_path.lower().endswith('.docx'):
                self.add_file_to_list(file_path)
    
    def add_file(self):
        """添加文件到列表"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择Word文件", self.get_default_path(), "Word Files (*.docx)"
        )
        for file in files:
            self.add_file_to_list(file)
    
    def add_directory(self):
        """添加目录中的Word文件到列表"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择目录", self.get_default_path()
        )
        if dir_path:
            for file in os.listdir(dir_path):
                file_path = os.path.join(dir_path, file)
                if os.path.isfile(file_path) and file_path.lower().endswith('.docx'):
                    self.add_file_to_list(file_path)
    
    def add_file_to_list(self, file_path):
        """将文件添加到列表"""
        # 检查文件是否已在列表中
        for row in range(self.file_list_widget.rowCount()):
            if self.file_list_widget.item(row, 0).text() == file_path:
                return
        
        # 添加到表格
        row = self.file_list_widget.rowCount()
        self.file_list_widget.insertRow(row)
        self.file_list_widget.setItem(row, 0, QTableWidgetItem(file_path))
        
        # 更新输出路径和输出文件名
        if row == 0:  # 只有当添加第一个文件时更新
            # 设置输出路径为默认路径
            self.output_path_edit.setText(self.get_default_path())
            # 设置默认输出文件名
            self.output_filename_edit.setText("merged_document.docx")
    
    def remove_selected(self):
        """移除选中的项目"""
        selected_rows = []
        for item in self.file_list_widget.selectedItems():
            selected_rows.append(item.row())
        
        # 按降序删除，避免索引问题
        for row in sorted(selected_rows, reverse=True):
            self.file_list_widget.removeRow(row)
        
        # 检查列表是否为空
        if self.file_list_widget.rowCount() == 0:
            # 清空输出路径和输出文件名
            self.output_path_edit.setText("")
            self.output_filename_edit.setText("")
    
    def move_up(self):
        """将选中的项目上移"""
        current_item = self.file_list_widget.currentItem()
        if not current_item:
            return
        current_row = current_item.row()
        if current_row > 0:
            # 获取当前行数据
            file_path = self.file_list_widget.item(current_row, 0).text()
            
            # 移除当前行
            self.file_list_widget.removeRow(current_row)
            
            # 插入到上一行
            self.file_list_widget.insertRow(current_row - 1)
            self.file_list_widget.setItem(current_row - 1, 0, QTableWidgetItem(file_path))
            
            # 设置当前行
            self.file_list_widget.setCurrentItem(self.file_list_widget.item(current_row - 1, 0))
    
    def move_down(self):
        """将选中的项目下移"""
        current_item = self.file_list_widget.currentItem()
        if not current_item:
            return
        current_row = current_item.row()
        if current_row < self.file_list_widget.rowCount() - 1:
            # 获取当前行数据
            file_path = self.file_list_widget.item(current_row, 0).text()
            
            # 移除当前行
            self.file_list_widget.removeRow(current_row)
            
            # 插入到下一行
            self.file_list_widget.insertRow(current_row + 1)
            self.file_list_widget.setItem(current_row + 1, 0, QTableWidgetItem(file_path))
            
            # 设置当前行
            self.file_list_widget.setCurrentItem(self.file_list_widget.item(current_row + 1, 0))
    
    def clear_list(self):
        """清空列表"""
        self.file_list_widget.setRowCount(0)
        # 清空输出路径和输出文件名
        self.output_path_edit.setText("")
        self.output_filename_edit.setText("")
    
    def get_default_path(self):
        """获取默认路径"""
        if self.file_list_widget.rowCount() > 0:
            first_file = self.file_list_widget.item(0, 0).text()
            return os.path.dirname(first_file)
        return os.getcwd()
    
    def browse_output_path(self):
        """浏览输出路径"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存合并后的文档", self.get_default_path(), "Word Files (*.docx)"
        )
        if file_path:
            self.output_path_edit.setText(file_path)
            # 自动提取文件名
            self.output_filename_edit.setText(os.path.basename(file_path))
    
    def execute_merge(self):
        """执行文档合并"""
        # 获取文件列表
        file_list = []
        for i in range(self.file_list_widget.rowCount()):
            file_list.append(self.file_list_widget.item(i, 0).text())
        
        if not file_list:
            QMessageBox.warning(self, "警告", "请先添加要合并的Word文档！")
            return
        
        # 获取输出路径
        output_path = self.output_path_edit.text().strip()
        output_filename = self.output_filename_edit.text().strip()
        
        # 验证输出路径
        if not output_path or not output_filename:
            # 使用默认输出路径和文件名
            default_dir = self.get_default_path()
            output_path = os.path.join(default_dir, output_filename if output_filename else "merged_document.docx")
        elif os.path.isdir(output_path):
            # 如果输出路径是目录，自动添加文件名
            output_path = os.path.join(output_path, output_filename if output_filename else "merged_document.docx")
        
        try:
            self.showProgress("正在合并文档...")
            
            # 检查输出路径权限
            output_dir = os.path.dirname(output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            # 创建临时目录存储文件列表
            temp_dir = os.path.join(os.getcwd(), "temp_word_merge")
            os.makedirs(temp_dir, exist_ok=True)
            
            # 将文件列表复制到临时目录（按顺序）
            for i, file_path in enumerate(file_list):
                # 检查文件是否存在且可读
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"文件不存在：{file_path}")
                if not os.access(file_path, os.R_OK):
                    raise PermissionError(f"没有读取文件的权限：{file_path}")
                
                temp_file = os.path.join(temp_dir, f"{i:03d}_{os.path.basename(file_path)}")
                import shutil
                shutil.copy2(file_path, temp_file)
            
            # 执行合并
            success = merge_word_documents(temp_dir, output_path)
            
            if success:
                self.showSuccess(f"文档合并完成！\n输出文件：{output_path}")
            else:
                self.showError("文档合并失败！")
        except Exception as e:
            error_msg = f"合并过程中发生错误：{str(e)}"
            # 改进错误提示
            if "Permission denied" in str(e):
                if "E:/WORD" in str(e):
                    error_msg = "合并过程中发生权限错误！\n请确保您有访问E:/WORD目录的权限，或者选择其他输出路径。"
                else:
                    error_msg = f"合并过程中发生权限错误！\n请确保您有访问相关目录的权限：{str(e)}"
            self.showError(error_msg)
        finally:
            # 清理临时目录
            import shutil
            temp_dir = os.path.join(os.getcwd(), "temp_word_merge")
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def execute(self):
        """执行功能（BaseFunction要求实现的方法）"""
        self.execute_merge()