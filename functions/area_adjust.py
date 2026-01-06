# coding:utf-8
"""
根据指定面积调整要素功能
"""

from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QFileDialog, QGroupBox, QMessageBox
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from qfluentwidgets import LineEdit, PrimaryPushButton, PushButton, ComboBox, ProgressBar, StateToolTip
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction
import geopandas as gpd


class AreaAdjustThread(QThread):
    """面积调整线程"""
    
    success = pyqtSignal(str)  # 成功信号，传递结果信息
    error = pyqtSignal(str)    # 错误信号，传递错误信息
    progress = pyqtSignal(int)  # 进度信号，传递进度值
    
    def __init__(self, file_path, field1, field2, area_value, output_path, output_type, parent=None):
        """
        Args:
            file_path: 矢量文件路径
            field1: 第一个字段名
            field2: 第二个字段名
            area_value: 指定的面积值
            output_path: 输出文件路径
            output_type: 输出类型
        """
        super().__init__(parent)
        self.file_path = file_path
        self.field1 = field1
        self.field2 = field2
        self.area_value = area_value
        self.output_path = output_path
        self.output_type = output_type
    
    def run(self):
        """线程运行方法"""
        try:
            # 从根目录导入数据处理方法
            import sys
            import os
            # 获取项目根目录
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if root_dir not in sys.path:
                sys.path.insert(0, root_dir)
            
            from .矢量操作 import 根据指定面积缓冲调整要素
            
            # 定义更新进度条的回调函数
            def update_progress(progress):
                self.progress.emit(int(progress))
            
            # 调用处理函数
            根据指定面积缓冲调整要素(
                self.file_path,
                self.field1,
                self.field2,
                self.area_value,
                update_progress,
                self.output_path,
                self.output_type
            )
            
            self.success.emit(f"面积调整完成！结果已保存到: {self.output_path}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error.emit(f"面积调整失败: {str(e)}\n\n{traceback.format_exc()}")


class AreaAdjustFunction(BaseFunction):
    """根据指定面积调整要素功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>"
            "根据指定面积缓冲调整要素<br>"
            "<span style='color: orange; font-weight: bold;'>提示：</span>调整面积只可能比原图斑小，不可能比原图斑大~~"
        )
        super().__init__("根据指定面积调整要素", description, parent)
        
        self._initUI()
        # 不使用默认执行按钮，使用自定义的缓冲调整按钮
        self.stateTooltip = None
        self._running = False
    
    def _initUI(self):
        """初始化界面"""
        # 输入矢量设置区域
        input_group = QGroupBox("输入矢量设置", self)
        input_layout = QVBoxLayout(input_group)
        
        # 矢量文件选择
        vector_layout = QHBoxLayout()
        vector_label = QLabel("矢量文件：")
        self.vector_path_edit = LineEdit(self)
        self.vector_path_edit.setPlaceholderText("选择矢量文件")
        self.vector_path_edit.setReadOnly(True)
        
        self.vector_shp_btn = PushButton("选择SHP", self, FIF.DOCUMENT)
        self.vector_shp_btn.clicked.connect(lambda: self._selectVectorFile("shp"))
        self.vector_gdb_btn = PushButton("选择GDB", self, FIF.FOLDER)
        self.vector_gdb_btn.clicked.connect(lambda: self._selectVectorFile("gdb"))
        
        vector_layout.addWidget(vector_label)
        vector_layout.addWidget(self.vector_path_edit, 1)
        vector_layout.addWidget(self.vector_shp_btn)
        vector_layout.addWidget(self.vector_gdb_btn)
        input_layout.addLayout(vector_layout)
        
        # 字段选择
        field_layout = QHBoxLayout()
        field_label = QLabel("唯一编号字段：")
        self.id_field_combo = ComboBox(self)
        self.id_field_combo.setPlaceholderText("选择唯一编号字段")
        self.area_field_combo = ComboBox(self)
        self.area_field_combo.setPlaceholderText("选择面积字段")
        
        field_layout.addWidget(field_label)
        field_layout.addWidget(self.id_field_combo, 1)
        field_layout.addStretch(1)
        field_layout.addWidget(self.area_field_combo, 1)
        input_layout.addLayout(field_layout)
        
        # 允许误差
        error_layout = QHBoxLayout()
        error_label = QLabel("允许误差（平方米）：")
        self.error_edit = LineEdit(self)
        self.error_edit.setText("1")
        
        error_layout.addWidget(error_label)
        error_layout.addWidget(self.error_edit, 1)
        error_layout.addStretch(1)
        input_layout.addLayout(error_layout)
        
        # 输出设置区域
        output_group = QGroupBox("输出设置", self)
        output_layout = QVBoxLayout(output_group)
        
        # 输出类型选择
        output_type_layout = QHBoxLayout()
        output_type_label = QLabel("输出类型：")
        self.output_type_combo = ComboBox(self)
        self.output_type_combo.addItems(["SHP文件", "GDB图层"])
        self.output_type_combo.currentTextChanged.connect(self._on_output_type_changed)
        
        output_type_layout.addWidget(output_type_label)
        output_type_layout.addWidget(self.output_type_combo, 1)
        output_layout.addLayout(output_type_layout)
        
        # SHP输出路径
        self.shp_output_layout = QHBoxLayout()
        shp_output_label = QLabel("SHP输出路径：")
        self.output_path_edit = LineEdit(self)
        self.output_path_edit.setPlaceholderText("选择输出SHP文件路径")
        self.output_path_edit.setReadOnly(True)
        
        self.output_shp_btn = PushButton("选择输出路径", self, FIF.SAVE)
        self.output_shp_btn.clicked.connect(self._selectOutputFile)
        
        self.shp_output_layout.addWidget(shp_output_label)
        self.shp_output_layout.addWidget(self.output_path_edit, 1)
        self.shp_output_layout.addWidget(self.output_shp_btn)
        output_layout.addLayout(self.shp_output_layout)
        
        # GDB输出设置
        self.gdb_output_layout = QHBoxLayout()
        gdb_output_label = QLabel("GDB输出路径：")
        self.output_gdb_path = LineEdit(self)
        self.output_gdb_path.setPlaceholderText("选择输出GDB文件路径")
        self.output_gdb_path.setReadOnly(True)
        
        self.output_gdb_btn = PushButton("选择GDB", self, FIF.FOLDER)
        self.output_gdb_btn.clicked.connect(self._select_output_gdb)
        
        self.gdb_output_layout.addWidget(gdb_output_label)
        self.gdb_output_layout.addWidget(self.output_gdb_path, 1)
        self.gdb_output_layout.addWidget(self.output_gdb_btn)
        output_layout.addLayout(self.gdb_output_layout)
        
        # GDB图层名称设置
        self.gdb_layer_layout = QHBoxLayout()
        gdb_layer_label = QLabel("GDB图层名称：")
        self.output_gdb_layer = LineEdit(self)
        self.output_gdb_layer.setPlaceholderText("输入输出图层名称")
        
        self.gdb_layer_layout.addWidget(gdb_layer_label)
        self.gdb_layer_layout.addWidget(self.output_gdb_layer, 1)
        output_layout.addLayout(self.gdb_layer_layout)
        
        # 初始显示SHP输出选项
        self._on_output_type_changed("SHP文件")
        
        # 将分组框添加到主布局
        self.contentLayout.addWidget(input_group)
        self.contentLayout.addWidget(output_group)
        
        # 添加执行按钮
        self.execute_btn = PrimaryPushButton("开始调整", self, FIF.PLAY)
        self.execute_btn.clicked.connect(self.execute)
        self.contentLayout.addWidget(self.execute_btn, 0, Qt.AlignmentFlag.AlignCenter)
    
    def _selectVectorFile(self, file_type="shp"):
        """选择矢量文件并获取字段列表"""
        if file_type == "shp":
            file_path, _ = QFileDialog.getOpenFileName(self, "选择SHP文件", "", "SHP文件 (*.shp)")
            if file_path:
                self.vector_path_edit.setText(file_path)
                self._loadFields(file_path, "shp")
        else:
            # 选择GDB文件
            file_path = QFileDialog.getExistingDirectory(self, "选择GDB文件", "")
            if file_path and file_path.endswith('.gdb'):
                self.vector_path_edit.setText(file_path)
                self._loadLayers(file_path)
    
    def _loadLayers(self, gdb_path):
        """加载GDB文件中的图层列表"""
        try:
            import fiona
            layers = fiona.listlayers(gdb_path)
            # 简单实现，只加载第一个图层
            if layers:
                layer_name = layers[0]
                self._loadFields(gdb_path, "gdb", layer_name)
        except Exception as e:
            QMessageBox.critical(self, '错误', f'读取GDB图层失败: {str(e)}')
    
    def _loadFields(self, file_path, file_type="shp", layer_name=None):
        """加载字段列表"""
        try:
            if file_type == "shp":
                gdf = gpd.read_file(file_path)
            else:  # gdb
                gdf = gpd.read_file(file_path, layer=layer_name)
            
            fields = gdf.columns.tolist()
            
            # 移除几何字段
            if 'geometry' in fields:
                fields.remove('geometry')
                
            # 更新两个下拉框
            self.id_field_combo.clear()
            self.id_field_combo.addItems(fields)
            self.id_field_combo.setCurrentIndex(-1)
            
            self.area_field_combo.clear()
            self.area_field_combo.addItems(fields)
            self.area_field_combo.setCurrentIndex(-1)
            
        except Exception as e:
            QMessageBox.critical(self, '错误', f'读取矢量文件字段失败: {str(e)}')
    
    def _selectOutputFile(self):
        """选择SHP输出文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存SHP文件", "", "SHP文件 (*.shp)"
        )
        if file_path:
            if not file_path.endswith('.shp'):
                file_path += '.shp'
            self.output_path_edit.setText(file_path)
    
    def _select_output_gdb(self):
        """选择GDB输出文件"""
        file_path = QFileDialog.getExistingDirectory(
            self, "选择输出GDB文件", ""
        )
        if file_path and file_path.endswith('.gdb'):
            self.output_gdb_path.setText(file_path)
    
    def _on_output_type_changed(self, output_type: str):
        """输出类型变化处理"""
        if output_type == "SHP文件":
            for i in range(self.shp_output_layout.count()):
                widget = self.shp_output_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(True)
            for i in range(self.gdb_output_layout.count()):
                widget = self.gdb_output_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(False)
            for i in range(self.gdb_layer_layout.count()):
                widget = self.gdb_layer_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(False)
        else:
            for i in range(self.shp_output_layout.count()):
                widget = self.shp_output_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(False)
            for i in range(self.gdb_output_layout.count()):
                widget = self.gdb_output_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(True)
            for i in range(self.gdb_layer_layout.count()):
                widget = self.gdb_layer_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(True)
    
    def validate(self) -> tuple[bool, str]:
        """验证输入"""
        # 验证输入矢量文件
        if not self.vector_path_edit.text():
            return False, "请选择矢量文件"
        
        # 验证字段选择
        if not self.id_field_combo.currentText():
            return False, "请选择唯一编号字段"
        if not self.area_field_combo.currentText():
            return False, "请选择面积字段"
        
        # 验证允许误差
        if not self.error_edit.text():
            return False, "请输入允许误差"
        try:
            float(self.error_edit.text())
        except ValueError:
            return False, "允许误差必须是数字"
        
        # 验证输出设置
        output_type = self.output_type_combo.currentText()
        if output_type == "SHP文件":
            if not self.output_path_edit.text():
                return self._set_default_output_path()
        else:  # GDB图层
            if not self.output_gdb_path.text():
                return self._set_default_output_gdb_path()
            if not self.output_gdb_layer.text():
                return False, "请输入GDB图层名称"
        
        return True, ""
    
    def _set_default_output_path(self):
        """设置默认SHP输出路径"""
        file_path = self.vector_path_edit.text()
        if file_path:
            base_path, ext = os.path.splitext(file_path)
            default_path = f"{base_path}_area{ext}"
            self.output_path_edit.setText(default_path)
            return True, ""
        return False, "请选择矢量文件"
    
    def _set_default_output_gdb_path(self):
        """设置默认GDB输出路径"""
        file_path = self.vector_path_edit.text()
        if file_path:
            base_path = os.path.splitext(file_path)[0]
            default_gdb = f"{base_path}.gdb"
            self.output_gdb_path.setText(default_gdb)
            return True, ""
        return False, "请选择矢量文件"
    
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
        
        # 获取输入参数
        file_path = self.vector_path_edit.text()
        field1 = self.id_field_combo.currentText()
        field2 = self.area_field_combo.currentText()
        area_value = self.error_edit.text()
        output_type = self.output_type_combo.currentText()
        
        if output_type == "SHP文件":
            output_path = self.output_path_edit.text()
            output_layer = None
        else:
            output_path = self.output_gdb_path.text()
            output_layer = self.output_gdb_layer.text()
        
        # 创建并启动面积调整线程
        self.area_thread = AreaAdjustThread(
            file_path=file_path,
            field1=field1,
            field2=field2,
            area_value=area_value,
            output_path=output_path,
            output_type=output_type,
            output_layer=output_layer,
            parent=self
        )
        
        # 连接信号
        self.area_thread.success.connect(self._onAreaAdjustSuccess)
        self.area_thread.error.connect(self._onAreaAdjustError)
        self.area_thread.progress.connect(self._onAreaAdjustProgress)
        self.area_thread.finished.connect(self._onAreaAdjustFinished)
        
        # 启动线程
        self.area_thread.start()
    
    def _onAreaAdjustProgress(self, progress: int):
        """面积调整进度更新处理"""
        self.progressBar.setValue(progress)
    
    def _onAreaAdjustSuccess(self, message: str):
        """面积调整成功处理"""
        if self.stateTooltip:
            self.stateTooltip.setContent('处理完成 ✅')
            self.stateTooltip.setState(True)
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1000, self.stateTooltip.close)
        
        self.showSuccess(message)
    
    def _onAreaAdjustError(self, message: str):
        """面积调整错误处理"""
        if self.stateTooltip:
            self.stateTooltip.setContent('处理失败 ❌')
            self.stateTooltip.setState(True)
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1000, self.stateTooltip.close)
        
        self.showError(message)
    
    def _onAreaAdjustFinished(self):
        """面积调整线程结束处理"""
        self._running = False
