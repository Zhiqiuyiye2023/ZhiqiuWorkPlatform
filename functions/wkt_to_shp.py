# coding:utf-8
"""
WKT坐标串转SHP功能
"""

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QFileDialog, QMessageBox, QTextEdit
from qfluentwidgets import (LineEdit, PushButton, PrimaryPushButton, 
                           StateToolTip, TextEdit, ComboBox)
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction
import os


class WktToShpThread(QThread):
    """WKT转SHP转换线程类"""
    success = pyqtSignal(str)  # 成功信号，传递输出文件路径
    error = pyqtSignal(str)     # 错误信号
    
    def __init__(self, wkt_string, output_path):
        super().__init__()
        self.wkt_string = wkt_string
        self.output_path = output_path
    
    def run(self):
        """执行WKT转SHP转换"""
        try:
            # 导入格式转换模块
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            from .格式转换 import WKT转SHP格式
            
            # 直接调用格式转换模块中的函数
            output_path = WKT转SHP格式(self.wkt_string, self.output_path)
            
            # 发送成功信号
            self.success.emit(output_path)
            
        except Exception as e:
            import traceback
            error_msg = f'转换失败: {str(e)}\n\n{traceback.format_exc()}'
            # 发送错误信号
            self.error.emit(error_msg)


class WktToShpFunction(BaseFunction):
    """WKT坐标串转SHP功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>" 
            "将WKT坐标串转换为SHP矢量文件"
        )
        super().__init__("WKT坐标串转SHP", description, parent)
        
        self._initUI()
        self._running = False
        self.stateTooltip = None
    
    def _initUI(self):
        """初始化界面"""
        # 功能说明标签
        infoLabel = QLabel(
            "📢 <span style='color: orange; font-weight: bold;'>功能说明：</span>"
            "<br>1. 输入WKT格式的坐标串"
            "<br>2. 支持点、线、面、多面等几何类型"
            "<br>3. 输出为SHP矢量文件"
            "<br>4. WKT示例：POLYGON((100.0 20.0, 101.0 20.0, 101.0 21.0, 100.0 21.0, 100.0 20.0))"
        )
        infoLabel.setWordWrap(True)
        infoLabel.setStyleSheet('''
            QLabel {
                padding: 10px 0 18px 0;
                font-size: 13px;
                line-height: 1.5;
            }
        ''')
        self.contentLayout.addWidget(infoLabel)
        
        # WKT输入区域
        inputRow = QVBoxLayout()
        inputLabel = QLabel("WKT坐标串：")
        inputRow.addWidget(inputLabel)
        
        self.wktTextEdit = QTextEdit(self)
        self.wktTextEdit.setPlaceholderText("请输入WKT格式的坐标串...")
        self.wktTextEdit.setFixedHeight(150)
        inputRow.addWidget(self.wktTextEdit)
        
        # 操作按钮
        buttonsRow = QHBoxLayout()
        buttonsRow.setSpacing(10)
        
        self.loadExampleBtn = PushButton("加载示例", self, FIF.INFO)
        self.loadExampleBtn.clicked.connect(self._loadExampleWkt)
        buttonsRow.addWidget(self.loadExampleBtn)
        
        self.clearBtn = PushButton("清空", self, FIF.DELETE)
        self.clearBtn.clicked.connect(self._clearWkt)
        buttonsRow.addWidget(self.clearBtn)
        
        buttonsRow.addStretch(1)
        inputRow.addLayout(buttonsRow)
        
        self.contentLayout.addLayout(inputRow)
        
        # 输出文件选择
        outputRow = QHBoxLayout()
        outputLabel = QLabel("输出文件：")
        outputRow.addWidget(outputLabel)
        
        self.outputPathEdit = LineEdit(self)
        self.outputPathEdit.setPlaceholderText("请选择输出SHP文件路径")
        outputRow.addWidget(self.outputPathEdit, 1)
        
        self.browseBtn = PushButton("浏览", self, FIF.FOLDER)
        self.browseBtn.clicked.connect(self._selectOutputFile)
        outputRow.addWidget(self.browseBtn)
        
        self.contentLayout.addLayout(outputRow)
        
        # 执行按钮
        buttonRow = QHBoxLayout()
        buttonRow.addStretch(1)
        
        self.executeBtn = PrimaryPushButton("开始转换", self, FIF.SEND)
        self.executeBtn.clicked.connect(self.execute)
        buttonRow.addWidget(self.executeBtn)
        
        buttonRow.addStretch(1)
        self.contentLayout.addLayout(buttonRow)
    
    def _selectOutputFile(self):
        """选择输出文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存SHP文件", "", "SHP文件 (*.shp)"
        )
        if file_path:
            if not file_path.lower().endswith('.shp'):
                file_path += '.shp'
            self.outputPathEdit.setText(file_path)
    
    def validate(self) -> tuple[bool, str]:
        """验证输入"""
        wkt_text = self.wktTextEdit.toPlainText().strip()
        if not wkt_text:
            return False, "请输入WKT坐标串"
        
        output_path = self.outputPathEdit.text().strip()
        if not output_path:
            return False, "请选择输出文件路径"
        
        if not output_path.lower().endswith('.shp'):
            return False, "输出文件必须是SHP格式"
        
        # 验证WKT格式是否有效
        if not (wkt_text.startswith('POLYGON') or wkt_text.startswith('MULTIPOLYGON') or 
                wkt_text.startswith('LINESTRING') or wkt_text.startswith('POINT')):
            return False, "请输入有效的WKT坐标串"
        
        return True, ""
    
    def execute(self):
        """执行WKT转SHP转换"""
        valid, message = self.validate()
        if not valid:
            self.showError(message)
            return
        
        if self._running:
            return
        
        self._running = True
        
        # 显示进度提示
        self.stateTooltip = StateToolTip('正在转换', '请稍候...', self)
        self.stateTooltip.move(self.width()//2 - 100, 30)
        self.stateTooltip.show()
        
        # 获取参数
        wkt_text = self.wktTextEdit.toPlainText().strip()
        output_path = self.outputPathEdit.text().strip()
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # 创建转换线程
        self.wkt_thread = WktToShpThread(wkt_text, output_path)
        
        # 连接信号槽
        self.wkt_thread.success.connect(self._on_conversion_success)
        self.wkt_thread.error.connect(self._on_conversion_error)
        
        # 启动线程
        self.wkt_thread.start()
    
    def _on_conversion_success(self, output_path):
        """转换成功处理"""
        self.showSuccess(f"WKT转SHP成功！\n输出文件: {output_path}")
        if hasattr(self, 'stateTooltip') and self.stateTooltip:
            try:
                self.stateTooltip.close()
            except:
                pass
        self._running = False
    
    def _on_conversion_error(self, error_msg):
        """转换错误处理"""
        self.showError(error_msg)
        if hasattr(self, 'stateTooltip') and self.stateTooltip:
            try:
                self.stateTooltip.close()
            except:
                pass
        self._running = False
    
    def _loadExampleWkt(self):
        """加载示例WKT"""
        example_wkt = "POLYGON((100.0 20.0, 101.0 20.0, 101.0 21.0, 100.0 21.0, 100.0 20.0))"
        self.wktTextEdit.setText(example_wkt)
    
    def _clearWkt(self):
        """清空WKT输入"""
        self.wktTextEdit.clear()
        self.wktTextEdit.setPlaceholderText("请输入WKT格式的坐标串...")
