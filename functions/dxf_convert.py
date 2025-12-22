# coding:utf-8
"""
DXF转SHP功能
"""

from PyQt6.QtWidgets import QHBoxLayout, QLabel
from PyQt6.QtCore import QThread, pyqtSignal
from qfluentwidgets import LineEdit, PrimaryPushButton, StateToolTip
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction


class DxfConvertThread(QThread):
    """DXF转SHP线程"""
    
    success = pyqtSignal(str)  # 成功信号，传递结果信息
    error = pyqtSignal(str)    # 错误信号，传递错误信息
    
    def __init__(self, dxf_path, layer_name, parent=None):
        """
        Args:
            dxf_path: DXF文件路径
            layer_name: 要提取的图层名称
        """
        super().__init__(parent)
        self.dxf_path = dxf_path
        self.layer_name = layer_name
    
    def run(self):
        """线程运行方法"""
        try:
            # 从根目录导入数据处理方法
            import sys
            import os
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if root_dir not in sys.path:
                sys.path.insert(0, root_dir)
            
            from .格式转换 import DXF转SHP
            DXF转SHP(self.dxf_path, self.layer_name)
            self.success.emit("转换完成！")
        except Exception as e:
            import traceback
            self.error.emit(f"转换失败: {str(e)}\n\n{traceback.format_exc()}")


class DxfConvertFunction(BaseFunction):
    """DXF提取指定图层面要素转SHP功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>"
            "提取DXF指定图层面要素转换为SHP格式"
        )
        super().__init__("DXF提取指定图层面要素转SHP", description, parent)
        
        self._initUI()
        # 不使用默认执行按钮
        self.stateTooltip = None
        self._running = False
    
    def _initUI(self):
        """初始化界面"""
        # 单行布局：按钮 + DXF目录标签 + DXF目录输入框 + 提取图层标签 + 提取图层输入框
        hBoxLayout = QHBoxLayout()
        
        # 开始执行按钮
        self.buttonExecute = PrimaryPushButton(self.tr('开始执行'), self, FIF.SEND)
        self.buttonExecute.clicked.connect(self.execute)
        
        # DXF目录
        self.label8 = QLabel("DXF目录：")
        self.lineEdit12 = LineEdit(self)
        self.lineEdit12.setPlaceholderText("请输入DXF文件所在目录路径")
        
        # 提取图层
        self.label9 = QLabel("提取图层：")
        self.lineEdit13 = LineEdit(self)
        self.lineEdit13.setText("JZD")  # 默认值
        self.lineEdit13.setPlaceholderText("请输入要提取的图层名称")
        
        # 添加到布局
        hBoxLayout.addWidget(self.buttonExecute)
        hBoxLayout.addWidget(self.label8)
        hBoxLayout.addWidget(self.lineEdit12)
        hBoxLayout.addWidget(self.label9)
        hBoxLayout.addWidget(self.lineEdit13)
        
        self.contentLayout.addLayout(hBoxLayout)
    
    def validate(self) -> tuple[bool, str]:
        """验证输入"""
        if not self.lineEdit12.text():
            return False, "请输入DXF目录路径"
        if not self.lineEdit13.text():
            return False, "请输入要提取的图层名称"
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
        
        # 创建并启动DXF转换线程
        self.dxf_thread = DxfConvertThread(
            dxf_path=self.lineEdit12.text(),
            layer_name=self.lineEdit13.text(),
            parent=self
        )
        
        # 连接信号
        self.dxf_thread.success.connect(self._onDxfConvertSuccess)
        self.dxf_thread.error.connect(self._onDxfConvertError)
        self.dxf_thread.finished.connect(self._onDxfConvertFinished)
        
        # 启动线程
        self.dxf_thread.start()
    
    def _onDxfConvertSuccess(self, message: str):
        """DXF转换成功处理"""
        if self.stateTooltip:
            self.stateTooltip.setContent('处理完成 ✅')
            self.stateTooltip.setState(True)
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1000, self.stateTooltip.close)
        
        self.showSuccess(message)
    
    def _onDxfConvertError(self, message: str):
        """DXF转换错误处理"""
        if self.stateTooltip:
            self.stateTooltip.setContent('处理失败 ❌')
            self.stateTooltip.setState(True)
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1000, self.stateTooltip.close)
        
        self.showError(message)
    
    def _onDxfConvertFinished(self):
        """DXF转换线程结束处理"""
        self._running = False
