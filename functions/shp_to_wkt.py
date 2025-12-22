# coding:utf-8
"""
SHP转WKT文本格式功能
"""

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QFileDialog
from qfluentwidgets import PrimaryPushButton, TransparentPushButton, StateToolTip
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction


class WktConversionThread(QThread):
    """转换线程类，用于在后台执行SHP转WKT任务"""
    success = pyqtSignal(str, str)  # 成功信号，传递SHP输出路径和WKT输出路径
    error = pyqtSignal(str)          # 错误信号
    
    def __init__(self, shp_path):
        super().__init__()
        self.shp_path = shp_path
    
    def run(self):
        """执行转换任务"""
        try:
            # 导入格式转换模块
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from .格式转换 import SHP转WKT文本格式
            
            # 直接调用格式转换模块中的函数
            shp_output_path, txt_output_path = SHP转WKT文本格式(self.shp_path)
            
            # 发送成功信号
            self.success.emit(shp_output_path, txt_output_path)
            
        except Exception as e:
            import traceback
            error_msg = f'转换失败: {str(e)}\n\n{traceback.format_exc()}'
            # 发送错误信号
            self.error.emit(error_msg)


class ShpToWktFunction(BaseFunction):
    """SHP转WKT格式（含ZIP）功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <span style='color: orange; font-weight: bold;'>WKT格式说明：</span><br>"
            "1. 普通面格式：POLYGON((x1 y1, x2 y2, x3 y3, x1 y1))<br>"
            "2. 多面格式：MULTIPOLYGON(((x1 y1, x2 y2, x3 y3, x1 y1)), ((x4 y4, x5 y5, x6 y6, x4 y4)))<br>"
            "注意：坐标点需要首尾相连，形成闭合多边形<br>"
            "3. 转换时将同时生成ZIP格式文件"
        )
        super().__init__("SHP转WKT格式（含ZIP）", description, parent)
        
        self._initUI()
        # 不使用默认执行按钮
        self.stateTooltip = None
        self._running = False
    
    def _initUI(self):
        """初始化界面"""
        # 功能说明标签
        vBoxLayout_info = QVBoxLayout()
        infoLabel = QLabel(
            "📢 <span style='color: orange; font-weight: bold;'>WKT格式说明：</span>"
            "<br>1. 普通面格式：POLYGON((x1 y1, x2 y2, x3 y3, x1 y1))"
            "<br>2. 多面格式：MULTIPOLYGON(((x1 y1, x2 y2, x3 y3, x1 y1)), ((x4 y4, x5 y5, x6 y6, x4 y4)))"
            "<br>注意：坐标点需要首尾相连，形成闭合多边形"
            "<br>3. 转换时将同时生成ZIP格式文件"
        )
        infoLabel.setWordWrap(True)
        vBoxLayout_info.addWidget(infoLabel)
        
        # 按钮布局
        buttonLayout = QHBoxLayout()
        
        # 转WKT按钮
        self.buttonConvert = PrimaryPushButton(self.tr('转WKT'), self, FIF.SEND)
        self.buttonConvert.clicked.connect(self.execute)
        
        # 添加矢量路径按钮
        self.buttonAddVector = TransparentPushButton(self.tr('添加矢量路径'), self, FIF.DOCUMENT)
        self.buttonAddVector.clicked.connect(self._selectVectorFile)
        
        # 文件路径标签
        self.label18 = QLabel()
        self.label18.setWordWrap(True)
        
        # 添加到布局
        buttonLayout.addWidget(self.buttonConvert)
        buttonLayout.addWidget(self.buttonAddVector)
        buttonLayout.addWidget(self.label18)
        
        # 添加到主布局
        self.contentLayout.addLayout(buttonLayout)
        self.contentLayout.addLayout(vBoxLayout_info)
    
    def _selectVectorFile(self):
        """选择矢量文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open File", "", "矢量文件 (*.shp)"
        )
        if file_path:
            self.label18.setText(file_path)
    
    def validate(self) -> tuple[bool, str]:
        """验证输入"""
        if not self.label18.text():
            return False, "请选择矢量文件"
        return True, ""
    
    def execute(self):
        """执行功能"""
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
        
        # 获取SHP文件路径
        shp_path = self.label18.text()
        
        # 创建转换线程
        self.wkt_thread = WktConversionThread(shp_path)
        
        # 连接信号槽
        self.wkt_thread.success.connect(self._on_wkt_success)
        self.wkt_thread.error.connect(self._on_wkt_error)
        
        # 启动线程
        self.wkt_thread.start()
    
    def _on_wkt_success(self, shp_output_path, txt_output_path):
        """WKT转换成功处理"""
        try:
            if hasattr(self, 'stateTooltip') and self.stateTooltip is not None:
                self.stateTooltip.setContent('处理完成 ✅')
                self.stateTooltip.setState(True)
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(1000, self.stateTooltip.close)
        except RuntimeError:
            # 捕获QLabel已被删除的错误
            pass
        
        self.showSuccess(f"处理完成！\nSHP输出文件: {shp_output_path}\nWKT文本文件: {txt_output_path}")
        self._running = False
    
    def _on_wkt_error(self, error_msg):
        """WKT转换错误处理"""
        try:
            if hasattr(self, 'stateTooltip') and self.stateTooltip is not None:
                self.stateTooltip.setContent('处理失败 ❌')
                self.stateTooltip.setState(True)
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(1000, self.stateTooltip.close)
        except RuntimeError:
            # 捕获QLabel已被删除的错误
            pass
        
        self.showError(f'发生错误: {error_msg}')
        self._running = False
