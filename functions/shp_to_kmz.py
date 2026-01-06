# coding:utf-8
"""
SHP转KMZ奥维格式功能
"""

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QFileDialog, QMessageBox, QGroupBox
from PyQt6.QtGui import QColor
from qfluentwidgets import (LineEdit, PushButton, ComboBox, CheckBox, SpinBox,
                           ColorPickerButton, StateToolTip)
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction
import geopandas as gpd
import os


class ConversionThread(QThread):
    """转换线程类，用于在后台执行SHP转KMZ任务"""
    success = pyqtSignal(str)  # 成功信号，传递输出路径
    error = pyqtSignal(str)     # 错误信号
    
    def __init__(self, 文件路径, 图层名称, 分离字段, 标注字段, 颜色值, 线宽值, 是否分离, 输出路径):
        super().__init__()
        self.文件路径 = 文件路径
        self.图层名称 = 图层名称
        self.分离字段 = 分离字段
        self.标注字段 = 标注字段
        self.颜色值 = 颜色值
        self.线宽值 = 线宽值
        self.是否分离 = 是否分离
        self.输出路径 = 输出路径
    
    def run(self):
        """执行转换任务"""
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            import geopandas as gpd
            
            # 读取矢量数据
            if self.文件路径.lower().endswith('.gdb') and self.图层名称:
                gdf = gpd.read_file(self.文件路径, layer=self.图层名称)
            else:
                gdf = gpd.read_file(self.文件路径)
            
            # 导入格式转换模块
            from .格式转换 import SHP转KMZ奥维格式
            
            # 直接调用格式转换模块中的函数
            # 注意：SHP转KMZ奥维格式函数不支持output_path和layer_name参数，会使用默认输出路径
            SHP转KMZ奥维格式(
                矢量路径=self.文件路径,
                分离字段=self.分离字段,
                标注字段=self.标注字段,
                颜色值=self.颜色值,
                线宽值=self.线宽值,
                是否分离=self.是否分离
            )
            
            # 发送成功信号
            self.success.emit(self.输出路径)
            
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
            "- 支持SHP/GDB矢量文件转换为KMZ奥维格式<br>"
            "- 可自定义线条颜色、宽度等样式参数<br>"
            "- 支持按字段分离要素，生成独立KMZ文件<br>"
            "- 可选择字段作为地物标注显示<br>"
        )
        super().__init__("SHP转KMZ奥维格式", description, parent)
        
        self._initUI()
        self.addExecuteButton("开始转换", self.execute)
    
    def _initUI(self):
        """初始化界面"""
        # 输入设置区域
        input_group = QGroupBox("输入矢量数据", self)
        input_layout = QVBoxLayout(input_group)
        
        # 输入文件选择
        input_layout.addLayout(self._createInputFileLayout())
        
        # GDB图层选择
        self.gdb_layer_layout = QHBoxLayout()
        gdb_layer_label = QLabel("GDB图层：")
        self.gdb_layer_combo = ComboBox(self)
        self.gdb_layer_combo.setPlaceholderText("请先选择GDB文件")
        self.gdb_layer_combo.setEnabled(False)
        
        self.gdb_layer_layout.addWidget(gdb_layer_label)
        self.gdb_layer_layout.addWidget(self.gdb_layer_combo, 1)
        # 默认隐藏GDB图层选择
        for i in range(self.gdb_layer_layout.count()):
            widget = self.gdb_layer_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(False)
        input_layout.addLayout(self.gdb_layer_layout)
        
        # 字段设置
        field_row = QHBoxLayout()
        
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
        
        field_row.addWidget(self.checkBox分离)
        field_row.addWidget(label_split)
        field_row.addWidget(self.fieldCombo)
        field_row.addWidget(label_name)
        field_row.addWidget(self.nameCombo)
        field_row.addStretch(1)
        input_layout.addLayout(field_row)
        
        # 样式设置
        style_row = QHBoxLayout()
        
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
        
        style_row.addWidget(label_color)
        style_row.addWidget(self.colorPicker)
        style_row.addWidget(label_width)
        style_row.addWidget(self.spinBox线宽)
        style_row.addStretch(1)
        input_layout.addLayout(style_row)
        
        # 输出设置区域
        output_group = QGroupBox("输出设置", self)
        output_layout = QVBoxLayout(output_group)
        
        # KMZ输出路径
        kmz_output_layout = QHBoxLayout()
        kmz_output_label = QLabel("KMZ输出路径：")
        self.output_path_edit = LineEdit(self)
        self.output_path_edit.setPlaceholderText("选择输出KMZ文件路径")
        self.output_path_edit.setReadOnly(True)
        
        self.output_kmz_btn = PushButton("选择输出路径", self, FIF.SAVE)
        self.output_kmz_btn.clicked.connect(self._selectOutputFile)
        
        kmz_output_layout.addWidget(kmz_output_label)
        kmz_output_layout.addWidget(self.output_path_edit, 1)
        kmz_output_layout.addWidget(self.output_kmz_btn)
        output_layout.addLayout(kmz_output_layout)
        
        # 将分组框添加到主布局
        self.contentLayout.addWidget(input_group)
        self.contentLayout.addWidget(output_group)
    
    def _createInputFileLayout(self):
        """创建输入文件选择布局"""
        layout = QHBoxLayout()
        label = QLabel("输入文件：")
        self.filePathLabel = LineEdit(self)
        self.filePathLabel.setPlaceholderText("选择要转换的矢量文件")
        self.filePathLabel.setReadOnly(True)
        
        # 分别添加SHP和GDB文件选择按钮
        self.shp_btn = PushButton("选择SHP", self, FIF.FOLDER)
        self.shp_btn.clicked.connect(lambda: self._selectFeatureFile(shp_only=True))
        self.shp_btn.setFixedWidth(120)
        
        self.gdb_btn = PushButton("选择GDB", self, FIF.FOLDER)
        self.gdb_btn.clicked.connect(lambda: self._selectFeatureFile(gdb_only=True))
        self.gdb_btn.setFixedWidth(120)
        
        layout.addWidget(label)
        layout.addWidget(self.filePathLabel, 1)
        layout.addWidget(self.shp_btn)
        layout.addWidget(self.gdb_btn)
        return layout
    
    def _selectFeatureFile(self, shp_only=False, gdb_only=False):
        """选择矢量文件"""
        file_path = ""
        
        if shp_only:
            # 选择SHP文件
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择SHP文件", ".", "Shapefiles (*.shp)"
            )
        elif gdb_only:
            # 选择GDB文件（GDB是目录，所以使用getExistingDirectory）
            file_path = QFileDialog.getExistingDirectory(
                self, "选择GDB文件", "."
            )
        
        if file_path:
            # 验证GDB文件
            if gdb_only and not file_path.endswith('.gdb'):
                from qfluentwidgets import InfoBar, InfoBarPosition
                InfoBar.warning(
                    title="警告",
                    content="请选择GDB文件",
                    parent=self,
                    position=InfoBarPosition.TOP_RIGHT
                )
                return
            
            self.filePathLabel.setText(file_path)
            # 设置默认输出路径
            base_path, ext = os.path.splitext(file_path)
            default_path = f"{base_path}.kmz"
            self.output_path_edit.setText(default_path)
            
            if file_path.lower().endswith('.gdb'):
                # 显示图层选择控件
                for i in range(self.gdb_layer_layout.count()):
                    widget = self.gdb_layer_layout.itemAt(i).widget()
                    if widget:
                        widget.setVisible(True)
                # 列出GDB中的所有图层
                self._update_gdb_layers(file_path)
            else:
                # 隐藏图层选择控件
                for i in range(self.gdb_layer_layout.count()):
                    widget = self.gdb_layer_layout.itemAt(i).widget()
                    if widget:
                        widget.setVisible(False)
                # 读取SHP字段列表
                self._load_fields(file_path)
    
    def _update_gdb_layers(self, gdb_path):
        """更新GDB图层列表"""
        try:
            import fiona
            with fiona.Env():
                layers = fiona.listlayers(gdb_path)
            self.gdb_layer_combo.clear()
            self.gdb_layer_combo.addItems(layers)
            self.gdb_layer_combo.setEnabled(True)
            self.gdb_layer_combo.currentTextChanged.connect(self._on_gdb_layer_changed)
        except Exception as e:
            from qfluentwidgets import InfoBar, InfoBarPosition
            InfoBar.error(
                title="错误",
                content=f"无法读取GDB文件: {str(e)}",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT
            )
    
    def _on_gdb_layer_changed(self, layer_name):
        """GDB图层变化事件"""
        if layer_name and self.filePathLabel.text().lower().endswith('.gdb'):
            gdb_path = self.filePathLabel.text()
            self._load_fields(gdb_path, layer_name)
    
    def _load_fields(self, file_path, layer_name=None):
        """加载矢量文件字段"""
        try:
            # 读取字段列表
            if file_path.lower().endswith('.gdb') and layer_name:
                gdf = gpd.read_file(file_path, layer=layer_name)
            else:
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
    
    def _selectOutputFile(self):
        """选择KMZ输出文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存KMZ文件", "", "KMZ文件 (*.kmz)"
        )
        if file_path:
            if not file_path.endswith('.kmz'):
                file_path += '.kmz'
            self.output_path_edit.setText(file_path)
    
    def _onCheckBoxChanged(self, state):
        """复选框状态改变事件"""
        self.fieldCombo.setEnabled(state)
    
    def validate(self) -> tuple[bool, str]:
        """验证输入"""
        if not self.filePathLabel.text():
            return False, "请选择矢量文件"
        
        if not os.path.exists(self.filePathLabel.text()):
            return False, "文件不存在"
        
        if not self.output_path_edit.text():
            return False, "请选择输出路径"
        
        # 验证GDB输入的图层选择
        if self.filePathLabel.text().lower().endswith('.gdb'):
            if not self.gdb_layer_combo.currentText():
                return False, "请选择GDB图层"
        
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
        # 获取GDB图层名称（如果是GDB文件）
        图层名称 = self.gdb_layer_combo.currentText() if 文件路径.lower().endswith('.gdb') else ""
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
        
        # 获取输出路径
        输出路径 = self.output_path_edit.text()
        
        # 创建转换线程
        self.conversion_thread = ConversionThread(
            文件路径=文件路径,
            图层名称=图层名称,
            分离字段=分离字段,
            标注字段=标注字段,
            颜色值=颜色值,
            线宽值=线宽值,
            是否分离=是否分离,
            输出路径=输出路径
        )
        
        # 连接信号槽
        self.conversion_thread.success.connect(self._on_conversion_success)
        self.conversion_thread.error.connect(self._on_conversion_error)
        
        # 启动线程
        self.conversion_thread.start()
    
    def _on_conversion_success(self, output_path):
        """转换成功处理"""
        self.showSuccess(f'SHP转KMZ成功！\n输出文件：{output_path}')
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
