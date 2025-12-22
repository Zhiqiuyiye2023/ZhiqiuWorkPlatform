# coding:utf-8
"""
PDF文件处理功能
"""

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout
from PyQt6.QtCore import QThread, pyqtSignal
from qfluentwidgets import TextEdit, PrimaryPushButton, ProgressBar, StateToolTip
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction
import threading


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
            "📢 <b>功能说明：</b><br>"
            "PDF合并、分离、转图片、图片转PDF"
        )
        super().__init__("PDF文件处理功能", description, parent)
        
        self._initUI()
        # 不使用默认执行按钮，使用自定义4个功能按钮
        self.stateTooltip = None
        self._running = False
    
    def _initUI(self):
        """初始化界面"""
        # 功能说明标签
        infoLabel = QLabel(
            "📢 <span style='color: orange; font-weight: bold;'>提示：</span>"
            "<br>1. 支持文件拖拽到文本框"
            "<br>2. PDF合并：将多个PDF合并为一个文件"
            "<br>3. PDF转图片：将PDF转换为高清图片"
            "<br>4. PDF分离：将PDF拆分为单页文件"
            "<br>5. 图片转PDF：将多张图片合并为一个PDF"
        )
        infoLabel.setWordWrap(True)
        self.contentLayout.addWidget(infoLabel)
        
        # 文本编辑框用于显示文件路径
        self.textEditR = TextEdit(self)
        self.textEditR.setPlaceholderText(
            "请将文件拖拽到此处，每个文件一行\n支持的格式：\nPDF合并/分离：*.pdf\nPDF转图片：*.pdf\n图片转PDF：*.png, *.jpg, *.jpeg, *.bmp, *.gif")
        self.textEditR.setFixedHeight(150)
        self.textEditR.setFixedWidth(1070)
        self.contentLayout.addWidget(self.textEditR)
        
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
        self.progressBarPDF.setFixedWidth(1070)
        self.progressBarPDF.hide()  # 默认隐藏进度条
        self.contentLayout.addWidget(self.progressBarPDF)
    
    def validate(self) -> tuple[bool, str]:
        """验证输入"""
        if not self.textEditR.toPlainText().strip():
            return False, "请输入或拖拽文件路径"
        return True, ""
    
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
        
        # 获取文件路径文本
        file_text = self.textEditR.toPlainText()
        
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
