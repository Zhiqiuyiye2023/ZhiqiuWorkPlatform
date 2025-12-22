# coding:utf-8
"""
SHP转KMZ奥维格式功能
"""

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QFileDialog, QMessageBox
from PyQt6.QtGui import QColor
from qfluentwidgets import (LineEdit, PushButton, ComboBox, CheckBox, SpinBox,
                           ColorPickerButton, StateToolTip)
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction
import geopandas as gpd
import os


class ConversionThread(QThread):
    """转换线程类，用于在后台执行SHP转KMZ任务"""
    success = pyqtSignal(str)  # 成功信号
    error = pyqtSignal(str)     # 错误信号
    
    def __init__(self, 文件路径, 分离字段, 标注字段, 颜色值, 线宽值, 是否分离):
        super().__init__()
        self.文件路径 = 文件路径
        self.分离字段 = 分离字段
        self.标注字段 = 标注字段
        self.颜色值 = 颜色值
        self.线宽值 = 线宽值
        self.是否分离 = 是否分离
    
    def run(self):
        """执行转换任务"""
        try:
            # 导入格式转换模块
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            from .格式转换 import SHP转KMZ奥维格式
            
            # 直接调用格式转换模块中的函数
            SHP转KMZ奥维格式(
                矢量路径=self.文件路径,
                分离字段=self.分离字段,
                标注字段=self.标注字段,
                颜色值=self.颜色值,
                线宽值=self.线宽值,
                是否分离=self.是否分离
            )
            
            # 发送成功信号
            self.success.emit(os.path.dirname(self.文件路径))
            
        except Exception as e:
            import traceback
            error_msg = f'转换失败: {str(e)}\n\n{traceback.format_exc()}'
            # 发送错误信号
            self.error.emit(error_msg)


class CustomColorPickerButton(ColorPickerButton):
    """自定义颜色选择器"""
    def __init__(self, parent=None):
        # 初始化为红色
        super().__init__(QColor('#ff0000'), "选择颜色", parent)


class ShpToKmzFunction(BaseFunction):
    """SHP转KMZ奥维格式功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>"
            "1. <b>文件选择</b><br>"
            "   - 选择SHP文件进行转换<br>"
            "2. <b>样式设置</b><br>"
            "   - 线条颜色：点击选择器设置颜色（ABGR格式）<br>"
            "   - 线条宽度：1-10之间的整数<br>"
            "3. <b>字段分离</b><br>"
            "   - 勾选后可按指定字段分离要素<br>"
            "   - 分离后每个字段值生成独立KMZ文件<br>"
            "4. <b>标注字段</b><br>"
            "   - 选择用于显示标注的字段<br>"
        )
        super().__init__("SHP转KMZ奥维格式", description, parent)
        
        self._initUI()
        self.addExecuteButton("开始转换", self.execute)
    
    def _initUI(self):
        """初始化界面"""
        # 文件选择行
        fileRow = QHBoxLayout()
        fileRow.setSpacing(10)
        
        label_shp = QLabel("SHP文件：")
        label_shp.setFixedWidth(60)
        
        self.addVectorBtn = PushButton("选择文件", self, FIF.DOCUMENT)
        self.addVectorBtn.clicked.connect(self._selectFile)
        self.addVectorBtn.setFixedWidth(100)
        
        self.filePathLabel = QLabel("")
        self.filePathLabel.setFixedWidth(300)
        
        fileRow.addWidget(label_shp)
        fileRow.addWidget(self.addVectorBtn)
        fileRow.addWidget(self.filePathLabel)
        fileRow.addStretch(1)
        
        self.contentLayout.addLayout(fileRow)
        
        # 字段选择行
        fieldRow = QHBoxLayout()
        fieldRow.setSpacing(10)
        
        # 分离选项
        self.checkBox分离 = CheckBox("按字段分离", self)
        self.checkBox分离.setChecked(False)
        self.checkBox分离.stateChanged.connect(self._onCheckBoxChanged)
        
        label_split = QLabel("分离字段：")
        self.fieldCombo = ComboBox(self)
        self.fieldCombo.setPlaceholderText("选择分离字段")
        self.fieldCombo.setFixedWidth(150)
        self.fieldCombo.setEnabled(False)
        
        label_name = QLabel("标注字段：")
        self.nameCombo = ComboBox(self)
        self.nameCombo.setPlaceholderText("选择标注字段")
        self.nameCombo.setFixedWidth(150)
        self.nameCombo.setEnabled(False)
        
        fieldRow.addWidget(self.checkBox分离)
        fieldRow.addWidget(label_split)
        fieldRow.addWidget(self.fieldCombo)
        fieldRow.addWidget(label_name)
        fieldRow.addWidget(self.nameCombo)
        fieldRow.addStretch(1)
        
        self.contentLayout.addLayout(fieldRow)
        
        # 样式设置行
        styleRow = QHBoxLayout()
        styleRow.setSpacing(10)
        
        label_color = QLabel("线条颜色：")
        self.colorPicker = CustomColorPickerButton(self)
        self.colorPicker.setToolTip('设置线条颜色，默认为红色')
        
        label_width = QLabel("线条宽度：")
        self.spinBox线宽 = SpinBox(self)
        self.spinBox线宽.setFixedWidth(150)
        self.spinBox线宽.setRange(1, 10)
        self.spinBox线宽.setValue(1)
        self.spinBox线宽.setSingleStep(1)
        self.spinBox线宽.setSuffix(' 像素')
        self.spinBox线宽.setToolTip('设置线条宽度，范围1-10像素')
        self.spinBox线宽.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        styleRow.addWidget(label_color)
        styleRow.addWidget(self.colorPicker)
        styleRow.addWidget(label_width)
        styleRow.addWidget(self.spinBox线宽)
        styleRow.addStretch(1)
        
        self.contentLayout.addLayout(styleRow)
    
    def _selectFile(self):
        """选择SHP文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择矢量文件", "", "矢量文件 (*.shp)"
        )
        if file_path:
            self.filePathLabel.setText(file_path)
            try:
                # 读取字段列表
                gdf = gpd.read_file(file_path)
                fields = gdf.columns.tolist()
                if 'geometry' in fields:
                    fields.remove('geometry')
                
                # 更新下拉框
                self.fieldCombo.clear()
                self.fieldCombo.addItems(fields)
                self.fieldCombo.setCurrentIndex(-1)
                
                self.nameCombo.clear()
                self.nameCombo.addItems(fields)
                self.nameCombo.setCurrentIndex(-1)
                self.nameCombo.setEnabled(True)
                
            except Exception as e:
                QMessageBox.critical(self, '错误', f'读取矢量文件字段失败: {str(e)}')
    
    def _onCheckBoxChanged(self, state):
        """复选框状态改变事件"""
        self.fieldCombo.setEnabled(state)
    
    def validate(self) -> tuple[bool, str]:
        """验证输入"""
        if not self.filePathLabel.text():
            return False, "请选择SHP文件"
        
        if not os.path.exists(self.filePathLabel.text()):
            return False, "文件不存在"
        
        if self.checkBox分离.isChecked() and not self.fieldCombo.currentText():
            return False, "已选择按字段分离，但未选择分离字段"
        
        线宽值 = self.spinBox线宽.value()
        if 线宽值 < 1 or 线宽值 > 10:
            return False, "请设置有效的线宽值（1-10之间）"
        
        return True, ""
    
    def execute(self):
        """执行转换"""
        valid, message = self.validate()
        if not valid:
            self.showError(message)
            return
        
        # 获取参数
        文件路径 = self.filePathLabel.text()
        分离字段 = self.fieldCombo.currentText() if self.checkBox分离.isChecked() else ""
        标注字段 = self.nameCombo.currentText()
        是否分离 = self.checkBox分离.isChecked()
        
        # 获取颜色值（转换为ABGR格式）
        color = self.colorPicker.color
        r = color.red()
        g = color.green()
        b = color.blue()
        颜色值 = f"ff{b:02x}{g:02x}{r:02x}"
        
        线宽值 = self.spinBox线宽.value()
        
        # 显示进度提示
        self.stateTooltip = StateToolTip('正在转换', '请稍候...', self)
        self.stateTooltip.move(self.width()//2 - 100, 30)
        self.stateTooltip.show()
        
        # 创建转换线程
        self.conversion_thread = ConversionThread(
            文件路径=文件路径,
            分离字段=分离字段,
            标注字段=标注字段,
            颜色值=颜色值,
            线宽值=线宽值,
            是否分离=是否分离
        )
        
        # 连接信号槽
        self.conversion_thread.success.connect(self._on_conversion_success)
        self.conversion_thread.error.connect(self._on_conversion_error)
        
        # 启动线程
        self.conversion_thread.start()
    
    def _on_conversion_success(self, output_dir):
        """转换成功处理"""
        self.showSuccess(f'转换成功！\n输出目录：{output_dir}')
        if hasattr(self, 'stateTooltip') and self.stateTooltip:
            try:
                self.stateTooltip.close()
            except:
                pass
    
    def _on_conversion_error(self, error_msg):
        """转换错误处理"""
        self.showError(error_msg)
        if hasattr(self, 'stateTooltip') and self.stateTooltip:
            try:
                self.stateTooltip.close()
            except:
                pass
