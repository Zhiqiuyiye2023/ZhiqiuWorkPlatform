# coding:utf-8
"""
DXF转SHP功能
"""

from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QFileDialog, QGroupBox, QMessageBox
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from qfluentwidgets import LineEdit, PrimaryPushButton, PushButton, ComboBox, StateToolTip
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction


class DxfConvertThread(QThread):
    """DXF转SHP线程"""
    
    success = pyqtSignal(str)  # 成功信号，传递结果信息
    error = pyqtSignal(str)    # 错误信号，传递错误信息
    
    def __init__(self, dxf_path, layer_name, output_path, output_gdb, output_layer, output_type, parent=None):
        """
        Args:
            dxf_path: DXF文件路径
            layer_name: 要提取的图层名称
            output_path: SHP输出路径
            output_gdb: GDB输出路径
            output_layer: GDB输出图层名称
            output_type: 输出类型（SHP文件或GDB图层）
        """
        super().__init__(parent)
        self.dxf_path = dxf_path
        self.layer_name = layer_name
        self.output_path = output_path
        self.output_gdb = output_gdb
        self.output_layer = output_layer
        self.output_type = output_type
    
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
            
            if self.output_type == "SHP文件":
                DXF转SHP(self.dxf_path, self.layer_name, self.output_path)
                self.success.emit(f"DXF转SHP成功！结果已保存到: {self.output_path}")
            else:
                # GDB图层输出暂不支持，需要更新底层函数
                # 先转换为SHP，再转换为GDB
                base_path, ext = os.path.splitext(self.dxf_path)
                temp_shp = f"{base_path}_temp.shp"
                DXF转SHP(self.dxf_path, self.layer_name, temp_shp)
                
                # 转换SHP到GDB
                import geopandas as gpd
                gdf = gpd.read_file(temp_shp)
                gdf.to_file(self.output_gdb, layer=self.output_layer, driver='OpenFileGDB')
                
                # 删除临时文件
                for ext in ['.shp', '.dbf', '.shx', '.prj', '.cpg', '.qpj']:
                    temp_file = f"{base_path}_temp{ext}"
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                
                self.success.emit(f"DXF转GDB成功！结果已保存到: {self.output_gdb} 图层: {self.output_layer}")
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
        # 输入设置区域
        input_group = QGroupBox("输入设置", self)
        input_layout = QVBoxLayout(input_group)
        
        # DXF文件选择
        dxf_layout = QHBoxLayout()
        dxf_label = QLabel("DXF文件：")
        self.dxf_path_edit = LineEdit(self)
        self.dxf_path_edit.setPlaceholderText("选择DXF文件")
        self.dxf_path_edit.setReadOnly(True)
        
        self.dxf_browse_btn = PushButton("选择DXF", self, FIF.DOCUMENT)
        self.dxf_browse_btn.clicked.connect(self._selectDxfFile)
        
        dxf_layout.addWidget(dxf_label)
        dxf_layout.addWidget(self.dxf_path_edit, 1)
        dxf_layout.addWidget(self.dxf_browse_btn)
        input_layout.addLayout(dxf_layout)
        
        # 图层设置
        layer_layout = QHBoxLayout()
        layer_label = QLabel("提取图层：")
        self.layer_edit = LineEdit(self)
        self.layer_edit.setText("JZD")  # 默认值
        self.layer_edit.setPlaceholderText("请输入要提取的图层名称")
        
        layer_layout.addWidget(layer_label)
        layer_layout.addWidget(self.layer_edit, 1)
        input_layout.addLayout(layer_layout)
        
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
        self.buttonExecute = PrimaryPushButton("开始转换", self, FIF.PLAY)
        self.buttonExecute.clicked.connect(self.execute)
        self.contentLayout.addWidget(self.buttonExecute, 0, Qt.AlignmentFlag.AlignCenter)
    
    def _selectDxfFile(self):
        """选择DXF文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择DXF文件", "", "DXF文件 (*.dxf)"
        )
        if file_path:
            self.dxf_path_edit.setText(file_path)
            # 设置默认输出路径
            base_path, ext = os.path.splitext(file_path)
            default_path = f"{base_path}.shp"
            self.output_path_edit.setText(default_path)
            self.output_gdb_layer.setText(os.path.basename(base_path))
    
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
        if not self.dxf_path_edit.text():
            return False, "请选择DXF文件"
        if not self.layer_edit.text():
            return False, "请输入要提取的图层名称"
        
        output_type = self.output_type_combo.currentText()
        if output_type == "SHP文件":
            if not self.output_path_edit.text():
                return False, "请选择SHP输出路径"
        else:  # GDB图层
            if not self.output_gdb_path.text():
                return False, "请选择GDB输出路径"
            if not self.output_gdb_layer.text():
                return False, "请输入GDB图层名称"
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
        
        # 获取参数
        dxf_path = self.dxf_path_edit.text()
        layer_name = self.layer_edit.text()
        output_type = self.output_type_combo.currentText()
        
        if output_type == "SHP文件":
            output_path = self.output_path_edit.text()
            output_gdb = None
            output_layer = None
        else:
            output_path = None
            output_gdb = self.output_gdb_path.text()
            output_layer = self.output_gdb_layer.text()
        
        # 创建并启动DXF转换线程
        self.dxf_thread = DxfConvertThread(
            dxf_path=dxf_path,
            layer_name=layer_name,
            output_path=output_path,
            output_gdb=output_gdb,
            output_layer=output_layer,
            output_type=output_type,
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
