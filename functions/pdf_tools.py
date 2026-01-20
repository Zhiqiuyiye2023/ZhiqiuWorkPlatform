# coding:utf-8
"""
PDF文件处理功能
"""

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QHeaderView, QTableWidgetItem, QGroupBox
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from qfluentwidgets import TextEdit, PrimaryPushButton, ProgressBar, StateToolTip, TableWidget
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction
import threading
import os


class PDFProcessThread(QThread):
    """PDF处理线程"""
    
    success = pyqtSignal(str)      # 成功信号，传递结果信息
    error = pyqtSignal(str)        # 错误信号，传递错误信息
    progress_update = pyqtSignal(int) # 进度更新信号
    
    def __init__(self, function_type, params, parent=None):
        """
        Args:
            function_type: PDF处理类型（'PDF合并', 'PDF分离', 'PDF转图片', '图片转PDF'）
            params: 处理参数
            parent: 父对象
        """
        super().__init__(parent)
        self.function_type = function_type
        self.params = params
    
    def run(self):
        """线程运行方法"""
        try:
            # 从根目录导入PDF处理方法
            import sys
            import os
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if root_dir not in sys.path:
                sys.path.insert(0, root_dir)
            
            from .PDF处理 import PDF合并, PDF分离, PDF转图片, 图片转PDF
            
            # 定义进度回调函数
            def update_progress(progress):
                self.progress_update.emit(int(progress))
            
            # 根据功能类型调用不同的处理函数
            if self.function_type == 'PDF合并':
                file_text, = self.params
                PDF合并(file_text, update_progress)
                self.success.emit("PDF合并完成！")
            elif self.function_type == 'PDF分离':
                file_text, = self.params
                PDF分离(file_text, update_progress)
                self.success.emit("PDF分离完成！")
            elif self.function_type == 'PDF转图片':
                file_text, = self.params
                PDF转图片(file_text, update_progress)
                self.success.emit("PDF转图片完成！")
            elif self.function_type == '图片转PDF':
                file_text, = self.params
                图片转PDF(file_text, update_progress)
                self.success.emit("图片转PDF完成！")
            else:
                raise ValueError(f"未知的PDF处理类型: {self.function_type}")
        except Exception as e:
            import traceback
            self.error.emit(f"处理失败: {str(e)}\n\n{traceback.format_exc()}")


class PdfToolsFunction(BaseFunction):
    """PDF文件处理功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>"+
            "1. 支持文件拖拽到列表<br>"+
            "2. PDF合并：将多个PDF合并为一个文件<br>"+
            "3. PDF转图片：将PDF转换为高清图片<br>"+
            "4. PDF分离：将PDF拆分为单页文件<br>"+
            "5. 图片转PDF：将多张图片合并为一个PDF"
        )
        super().__init__("PDF文件处理功能", description, parent)
        
        self._initUI()
        # 不使用默认执行按钮，使用自定义4个功能按钮
        self.stateTooltip = None
        self._running = False
        # 启用拖拽支持
        self.setAcceptDrops(True)
    
    def _initUI(self):
        """初始化界面"""
        
        # 文件列表展示区域
        file_list_group = QGroupBox("已选择文件", self)
        file_list_layout = QVBoxLayout(file_list_group)
        file_list_group.setFixedWidth(800)
        
        # 表格显示区域（参考矢量统计面板样式）
        self.table_widget = TableWidget(self)
        self.table_widget.setColumnCount(2)
        self.table_widget.setHorizontalHeaderLabels(["文件名", "文件大小"])
        self.table_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # 文件名自适应宽度
        self.table_widget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # 文件大小固定宽度
        self.table_widget.setColumnWidth(1, 100)  # 文件大小列固定宽度100px
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setFixedHeight(200)
        self.table_widget.setBorderVisible(True)
        file_list_layout.addWidget(self.table_widget)
        
        self.contentLayout.addWidget(file_list_group)
        
        # 添加文件按钮区域
        add_button_layout = QHBoxLayout()
        self.add_files_button = PrimaryPushButton(self.tr('添加文件'), self, FIF.ADD)
        self.add_files_button.clicked.connect(self._add_files)
        
        self.clear_files_button = PrimaryPushButton(self.tr('清空列表'), self, FIF.DELETE)
        self.clear_files_button.clicked.connect(self._clear_files)
        
        add_button_layout.addWidget(self.add_files_button)
        add_button_layout.addWidget(self.clear_files_button)
        add_button_layout.addStretch()
        self.contentLayout.addLayout(add_button_layout)
        
        # 按钮布局
        buttonLayout = QHBoxLayout()
        
        # 创建功能按钮
        self.buttonMerge = PrimaryPushButton(self.tr('合并PDF'), self, FIF.ADD)
        self.buttonMerge.clicked.connect(lambda: self._executeFunction('PDF合并'))
        
        self.buttonToImage = PrimaryPushButton(self.tr('PDF转图片'), self, FIF.PHOTO)
        self.buttonToImage.clicked.connect(lambda: self._executeFunction('pdf转图片'))
        
        self.buttonSplit = PrimaryPushButton(self.tr('PDF分离'), self, FIF.TILES)
        self.buttonSplit.clicked.connect(lambda: self._executeFunction('PDF分离'))
        
        self.buttonImageToPdf = PrimaryPushButton(self.tr('图片转PDF'), self, FIF.DOCUMENT)
        self.buttonImageToPdf.clicked.connect(lambda: self._executeFunction('图片转PDF'))
        
        # 添加按钮到布局
        buttonLayout.addWidget(self.buttonMerge)
        buttonLayout.addWidget(self.buttonToImage)
        buttonLayout.addWidget(self.buttonSplit)
        buttonLayout.addWidget(self.buttonImageToPdf)
        
        self.contentLayout.addLayout(buttonLayout)
        
        # 进度条
        self.progressBarPDF = ProgressBar(self)
        self.progressBarPDF.setFixedWidth(800)
        self.progressBarPDF.hide()  # 默认隐藏进度条
        self.contentLayout.addWidget(self.progressBarPDF)
    
    def _format_file_size(self, size_bytes):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    def _add_files(self):
        """通过文件选择对话框添加文件"""
        from PyQt6.QtWidgets import QFileDialog
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择文件", "", "PDF文件 (*.pdf);;图片文件 (*.png *.jpg *.jpeg *.bmp *.gif);;所有文件 (*.*)"
        )
        
        if files:
            self._add_files_to_table(files)
    
    def _add_files_to_table(self, files):
        """将文件添加到表格"""
        for file_path in files:
            # 添加新行
            row = self.table_widget.rowCount()
            self.table_widget.insertRow(row)
            
            # 设置文件名
            file_name = os.path.basename(file_path)
            self.table_widget.setItem(row, 0, QTableWidgetItem(file_path))
            
            # 设置文件大小
            file_size = os.path.getsize(file_path)
            size_str = self._format_file_size(file_size)
            self.table_widget.setItem(row, 1, QTableWidgetItem(size_str))
    
    def _clear_files(self):
        """清空文件列表"""
        self.table_widget.setRowCount(0)
    
    def _get_files_from_table(self):
        """从表格获取文件列表"""
        files = []
        for row in range(self.table_widget.rowCount()):
            file_item = self.table_widget.item(row, 0)
            if file_item:
                file_path = file_item.text()
                if file_path:
                    files.append(file_path)
        return files
    
    def validate(self) -> tuple[bool, str]:
        """验证输入"""
        files = self._get_files_from_table()
        if not files:
            return False, "请添加文件到列表"
        return True, ""
    
    def dragEnterEvent(self, event):
        """拖拽进入事件处理"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        """拖拽释放事件处理"""
        new_files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):  # 只处理文件
                new_files.append(file_path)
        
        if new_files:
            self._add_files_to_table(new_files)
    
    def _executeFunction(self, function_type: str):
        """执行功能
        
        Args:
            function_type: 'PDF合并', 'pdf转图片', 'PDF分离', '图片转PDF'
        """
        valid, message = self.validate()
        if not valid:
            self.showError(message)
            return
        
        if self._running:
            return
        
        self._running = True
        self.stateTooltip = StateToolTip('正在运行程序', '客官请耐心等待哦~~', self)
        self.stateTooltip.move(510, 30)
        self.stateTooltip.show()
        
        # 显示进度条
        self.progressBarPDF.setValue(0)
        self.progressBarPDF.show()
        
        # 标准化功能类型字符串，确保与线程中的判断匹配
        if function_type == 'pdf转图片':
            function_type = 'PDF转图片'
        
        # 获取文件路径列表
        files = self._get_files_from_table()
        file_text = '\n'.join(files)
        
        # 创建并配置线程
        thread = PDFProcessThread(function_type, (file_text,), self)
        
        # 连接信号和槽
        def on_success(message):
            self.progressBarPDF.setValue(100)
            
            if self.stateTooltip:
                self.stateTooltip.setContent('处理完成 ✅')
                self.stateTooltip.setState(True)
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(1000, self.stateTooltip.close)
            
            self.showSuccess(message)
            
            # 延迟隐藏进度条
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(2000, self.progressBarPDF.hide)
        
        def on_error(message):
            if self.stateTooltip:
                self.stateTooltip.setContent('处理失败 ❌')
                self.stateTooltip.setState(True)
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(1000, self.stateTooltip.close)
            
            self.showError(message)
            self.progressBarPDF.hide()
        
        def on_progress_update(progress):
            self.progressBarPDF.setValue(progress)
        
        def on_thread_finished():
            self._running = False
        
        thread.success.connect(on_success)
        thread.error.connect(on_error)
        thread.progress_update.connect(on_progress_update)
        thread.finished.connect(on_thread_finished)
        
        # 启动线程
        thread.start()
    
    def execute(self):
        """执行功能（基类接口，默认执行合并PDF）"""
        self._executeFunction('PDF合并')
