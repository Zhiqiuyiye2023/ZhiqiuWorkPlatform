# coding:utf-8
"""
坐标转SHP功能
"""

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QFileDialog, QMessageBox, QTextEdit
from qfluentwidgets import (LineEdit, PushButton, PrimaryPushButton, 
                           StateToolTip, TextEdit, SpinBox, ComboBox)
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction
import os


class CoordsToShpThread(QThread):
    """坐标转SHP转换线程类"""
    success = pyqtSignal(str)  # 成功信号，传递输出文件路径
    error = pyqtSignal(str)     # 错误信号
    
    def __init__(self, coord_string, zone_number, output_path):
        super().__init__()
        self.coord_string = coord_string
        self.zone_number = zone_number
        self.output_path = output_path
    
    def run(self):
        """执行坐标转SHP转换"""
        try:
            # 导入坐标处理模块
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            from .坐标处理 import 坐标转SHP格式
            
            # 直接调用坐标处理模块中的函数
            output_path = 坐标转SHP格式(
                self.coord_string, self.zone_number, self.output_path
            )
            
            # 发送成功信号
            self.success.emit(output_path)
            
        except Exception as e:
            import traceback
            error_msg = f'转换失败: {str(e)}\n\n{traceback.format_exc()}'
            # 发送错误信号
            self.error.emit(error_msg)


class CoordsToShpFunction(BaseFunction):
    """坐标转SHP功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>" 
            "将坐标串转换为SHP矢量文件"
        )
        super().__init__("坐标转SHP", description, parent)
        
        self._initUI()
        self._running = False
        self.stateTooltip = None
    
    def _initUI(self):
        """初始化界面"""
        # 功能说明标签
        infoLabel = QLabel(
            "📢 <span style='color: orange; font-weight: bold;'>功能说明：</span>"
            "<br>1. 输入坐标串，支持多行格式，每行一个坐标点 (X,Y或X,Y,Z)"
            "<br>2. 支持多部件坐标串，使用|分隔不同部件"
            "<br>3. 设置投影带号，3度分带(≤39)或6度分带(>39)"
            "<br>4. 坐标点必须首尾闭合，形成完整多边形"
            "<br>5. 支持多种分隔符：逗号、冒号等"
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
        
        # 坐标输入区域
        inputRow = QVBoxLayout()
        inputLabel = QLabel("坐标串：")
        inputRow.addWidget(inputLabel)
        
        self.coordTextEdit = QTextEdit(self)
        self.coordTextEdit.setPlaceholderText("请输入坐标串，例如：\n100.0,20.0\n101.0,20.0\n101.0,21.0\n100.0,21.0\n100.0,20.0")
        self.coordTextEdit.setFixedHeight(150)
        inputRow.addWidget(self.coordTextEdit)
        
        # 操作按钮
        buttonsRow = QHBoxLayout()
        buttonsRow.setSpacing(10)
        
        self.loadExampleBtn = PushButton("加载示例", self, FIF.INFO)
        self.loadExampleBtn.clicked.connect(self._loadExampleCoords)
        buttonsRow.addWidget(self.loadExampleBtn)
        
        self.clearBtn = PushButton("清空", self, FIF.DELETE)
        self.clearBtn.clicked.connect(self._clearCoords)
        buttonsRow.addWidget(self.clearBtn)
        
        buttonsRow.addStretch(1)
        inputRow.addLayout(buttonsRow)
        
        self.contentLayout.addLayout(inputRow)
        
        # 参数设置区域
        paramsRow = QHBoxLayout()
        paramsRow.setSpacing(15)
        
        # 投影带号
        zoneLabel = QLabel("投影带号：")
        paramsRow.addWidget(zoneLabel)
        
        self.zoneSpin = SpinBox(self)
        self.zoneSpin.setRange(1, 60)
        self.zoneSpin.setValue(35)  # 默认35度带
        self.zoneSpin.setSuffix(" 度带")
        paramsRow.addWidget(self.zoneSpin)
        
        paramsRow.addStretch(1)
        self.contentLayout.addLayout(paramsRow)
        
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
        coord_text = self.coordTextEdit.toPlainText().strip()
        if not coord_text:
            return False, "请输入坐标串"
        
        output_path = self.outputPathEdit.text().strip()
        if not output_path:
            return False, "请选择输出文件路径"
        
        if not output_path.lower().endswith('.shp'):
            return False, "输出文件必须是SHP格式"
        
        return True, ""
    
    def execute(self):
        """执行坐标转SHP转换"""
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
        coord_text = self.coordTextEdit.toPlainText().strip()
        zone_number = self.zoneSpin.value()
        output_path = self.outputPathEdit.text().strip()
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # 创建转换线程
        self.coords_thread = CoordsToShpThread(coord_text, zone_number, output_path)
        
        # 连接信号槽
        self.coords_thread.success.connect(self._on_conversion_success)
        self.coords_thread.error.connect(self._on_conversion_error)
        
        # 启动线程
        self.coords_thread.start()
    
    def _on_conversion_success(self, output_path):
        """转换成功处理"""
        self.showSuccess(f"坐标转SHP成功！\n输出文件: {output_path}")
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
    
    def _loadExampleCoords(self):
        """加载示例坐标"""
        example_coords = """100.0,20.0
101.0,20.0
101.0,21.0
100.0,21.0
100.0,20.0"""
        self.coordTextEdit.setText(example_coords)
    
    def _clearCoords(self):
        """清空坐标输入"""
        self.coordTextEdit.clear()
        self.coordTextEdit.setPlaceholderText("请输入坐标串，例如：\n100.0,20.0\n101.0,20.0\n101.0,21.0\n100.0,21.0\n100.0,20.0")
