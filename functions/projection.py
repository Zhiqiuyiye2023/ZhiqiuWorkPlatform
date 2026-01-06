# coding:utf-8
"""
修改与定义数据投影功能
"""

from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QFileDialog, QGroupBox, QMessageBox
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from qfluentwidgets import LineEdit, PrimaryPushButton, PushButton, ComboBox, StateToolTip
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction
import geopandas as gpd
import sys
import os


class ProjectionThread(QThread):
    """投影转换线程"""
    
    success = pyqtSignal(str)  # 成功信号，传递结果信息
    error = pyqtSignal(str)    # 错误信号，传递错误信息
    
    def __init__(self, file_path, proj_index, operation_type, output_path, output_type, output_layer, parent=None):
        """
        Args:
            file_path: 矢量文件路径
            proj_index: 投影索引
            operation_type: '修改数据投影' 或 '定义数据投影'
            output_path: 输出文件路径
            output_type: 输出类型（SHP文件或GDB图层）
            output_layer: 输出图层名称（仅GDB需要）
        """
        super().__init__(parent)
        self.file_path = file_path
        self.proj_index = proj_index
        self.operation_type = operation_type
        self.output_path = output_path
        self.output_type = output_type
        self.output_layer = output_layer
    
    def run(self):
        """线程运行方法"""
        try:
            # 导入投影转换函数
            from gis_workflow.投影转换 import 修改数据投影, 定义数据投影
            
            # 根据操作类型调用相应的函数
            if self.operation_type == '修改数据投影':
                result = 修改数据投影(self.file_path, self.proj_index, self.output_path, self.output_type, self.output_layer)
            elif self.operation_type == '定义数据投影':
                result = 定义数据投影(self.file_path, self.proj_index, self.output_path, self.output_type, self.output_layer)
            else:
                raise ValueError(f"未知的操作类型: {self.operation_type}")
            
            if result:
                self.success.emit(f"投影操作成功完成！\n输出文件: {result}")
            else:
                self.error.emit("投影操作执行失败！")
                
        except Exception as e:
            self.error.emit(f"发生错误: {str(e)}")


class ProjectionFunction(BaseFunction):
    """修改与定义数据投影功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>"
            "1. <b>修改数据投影</b>功能用于将矢量数据从当前投影转换为指定投影<br>"
            "2. <b>定义数据投影</b>功能用于为无投影信息的矢量数据指定投影坐标系"
        )
        super().__init__("修改与定义数据投影", description, parent)
        
        self._initUI()
        # 不使用默认执行按钮，使用自定义的修改投影和定义投影按钮
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
        
        # 坐标系信息显示
        self.crsInfoLabel = QLabel()
        # 使用qfluentwidgets的内置样式，不再硬编码颜色
        self.crsInfoLabel.setStyleSheet("""
            QLabel {
                font-size: 13px;
                padding: 10px;
                background-color: rgba(0, 0, 0, 5);
                border: 1px solid rgba(0, 0, 0, 20);
                border-radius: 6px;
                min-height: 60px;
            }
        """)
        self.crsInfoLabel.setWordWrap(True)
        self.crsInfoLabel.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.crsInfoLabel.hide()
        input_layout.addWidget(self.crsInfoLabel)
        
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
        
        # 投影参数选择
        proj_layout = QHBoxLayout()
        proj_label = QLabel("目标投影：")
        self.proj_combo = ComboBox(self)
        self.proj_combo.setPlaceholderText("选择投影参数")
        items = [
            'CGCS2000_3_Degree_GK_Zone_25', 'CGCS2000_3_Degree_GK_Zone_26', 'CGCS2000_3_Degree_GK_Zone_27',
            'CGCS2000_3_Degree_GK_Zone_28', 'CGCS2000_3_Degree_GK_Zone_29', 'CGCS2000_3_Degree_GK_Zone_30',
            'CGCS2000_3_Degree_GK_Zone_31', 'CGCS2000_3_Degree_GK_Zone_32', 'CGCS2000_3_Degree_GK_Zone_33',
            'CGCS2000_3_Degree_GK_Zone_34', 'CGCS2000_3_Degree_GK_Zone_35', 'CGCS2000_3_Degree_GK_Zone_36',
            'CGCS2000_3_Degree_GK_Zone_37',
            'CGCS2000_3_Degree_GK_Zone_38', 'CGCS2000_3_Degree_GK_Zone_39', 'CGCS2000_3_Degree_GK_Zone_40',
            'CGCS2000_3_Degree_GK_Zone_41', 'CGCS2000_3_Degree_GK_Zone_42', 'CGCS2000_3_Degree_GK_Zone_43',
            'CGCS2000_3_Degree_GK_Zone_44', 'CGCS2000_3_Degree_GK_Zone_45', 'GCS_China_Geodetic_Coordinate_System_2000'
        ]
        self.proj_combo.addItems(items)
        self.proj_combo.setCurrentIndex(-1)
        
        proj_layout.addWidget(proj_label)
        proj_layout.addWidget(self.proj_combo, 1)
        output_layout.addLayout(proj_layout)
        
        # 操作类型选择
        operation_layout = QHBoxLayout()
        operation_label = QLabel("操作类型：")
        self.operation_combo = ComboBox(self)
        self.operation_combo.addItems(["修改数据投影", "定义数据投影"])
        
        operation_layout.addWidget(operation_label)
        operation_layout.addWidget(self.operation_combo, 1)
        output_layout.addLayout(operation_layout)
        
        # 初始显示SHP输出选项
        self._on_output_type_changed("SHP文件")
        
        # 将分组框添加到主布局
        self.contentLayout.addWidget(input_group)
        self.contentLayout.addWidget(output_group)
        
        # 添加执行按钮
        self.execute_btn = PrimaryPushButton("开始执行", self, FIF.PLAY)
        self.execute_btn.clicked.connect(self.execute)
        self.contentLayout.addWidget(self.execute_btn, 0, Qt.AlignmentFlag.AlignCenter)
    
    def _selectVectorFile(self, file_type="shp"):
        """选择矢量文件并显示坐标系信息"""
        if file_type == "shp":
            file_path, _ = QFileDialog.getOpenFileName(self, "选择SHP文件", "", "SHP文件 (*.shp)")
            if file_path:
                self.vector_path_edit.setText(file_path)
                self._loadCRSInfo(file_path, "shp")
        else:
            # 选择GDB文件
            file_path = QFileDialog.getExistingDirectory(self, "选择GDB文件", "")
            if file_path and file_path.endswith('.gdb'):
                self.vector_path_edit.setText(file_path)
                self._loadGDBLayers(file_path)
    
    def _loadGDBLayers(self, gdb_path):
        """加载GDB文件中的图层列表"""
        try:
            import fiona
            layers = fiona.listlayers(gdb_path)
            if layers:
                layer_name = layers[0]
                self._loadCRSInfo(gdb_path, "gdb", layer_name)
        except Exception as e:
            QMessageBox.critical(self, '错误', f'读取GDB图层失败: {str(e)}')
    
    def _loadCRSInfo(self, file_path, file_type="shp", layer_name=None):
        """加载并显示坐标系信息"""
        try:
            if file_type == "shp":
                gdf = gpd.read_file(file_path)
            else:  # gdb
                gdf = gpd.read_file(file_path, layer=layer_name)
            
            # 获取并显示坐标系统信息
            if gdf.crs is None:
                crs_info = "无坐标系统"
            else:
                epsg_code = gdf.crs.to_epsg()
                if epsg_code == 4490:
                    crs_info = "EPSG:4490 (GCS_China_Geodetic_Coordinate_System_2000)"
                else:
                    crs_info = f"EPSG:{epsg_code} ({gdf.crs.name})"
            
            bounds = gdf.total_bounds
            bounds_info = f"范围: X({bounds[0]:.2f}~{bounds[2]:.2f}), Y({bounds[1]:.2f}~{bounds[3]:.2f})"
            
            info_text = f"📊 矢量文件信息\n\n" \
                        f"📍 坐标系统：\n{crs_info}\n\n" \
                        f"📐 数据范围：\n{bounds_info}"
            self.crsInfoLabel.setText(info_text)
            self.crsInfoLabel.show()
            
        except Exception as e:
            QMessageBox.critical(self, '错误', f'读取矢量文件信息失败: {str(e)}')
    
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
        if not self.vector_path_edit.text():
            return False, "请选择矢量文件"
        if self.proj_combo.currentIndex() == -1:
            return False, "请选择目标投影参数"
        if self.operation_combo.currentIndex() == -1:
            return False, "请选择操作类型"
        
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
            default_path = f"{base_path}_prj{ext}"
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
        """执行投影操作"""
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
        
        # 获取参数
        file_path = self.vector_path_edit.text()
        proj_index = self.proj_combo.currentIndex()
        operation_type = self.operation_combo.currentText()
        output_type = self.output_type_combo.currentText()
        
        if output_type == "SHP文件":
            output_path = self.output_path_edit.text()
            output_layer = None
        else:
            output_path = self.output_gdb_path.text()
            output_layer = self.output_gdb_layer.text()
        
        # 创建并启动投影转换线程
        self.projection_thread = ProjectionThread(
            file_path=file_path,
            proj_index=proj_index,
            operation_type=operation_type,
            output_path=output_path,
            output_type=output_type,
            output_layer=output_layer,
            parent=self
        )
        
        # 连接信号
        self.projection_thread.success.connect(self._onProjectionSuccess)
        self.projection_thread.error.connect(self._onProjectionError)
        self.projection_thread.finished.connect(self._onProjectionFinished)
        
        # 启动线程
        self.projection_thread.start()
    
    def _onProjectionSuccess(self, message: str):
        """投影操作成功处理"""
        if self.stateTooltip:
            self.stateTooltip.setContent('处理完成 ✅')
            self.stateTooltip.setState(True)
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1000, self.stateTooltip.close)
        
        self.showSuccess(message)
    
    def _onProjectionError(self, message: str):
        """投影操作错误处理"""
        if self.stateTooltip:
            self.stateTooltip.setContent('处理失败 ❌')
            self.stateTooltip.setState(True)
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1000, self.stateTooltip.close)
        
        self.showError(message)
    
    def _onProjectionFinished(self):
        """投影线程结束处理"""
        self._running = False
