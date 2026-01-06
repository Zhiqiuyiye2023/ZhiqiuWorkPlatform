# coding:utf-8
"""
WKT坐标串转SHP功能
"""

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QFileDialog, QMessageBox, QTextEdit, QGroupBox
from qfluentwidgets import (LineEdit, PushButton, PrimaryPushButton, 
                           StateToolTip, TextEdit, ComboBox)
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction
import os


class WktToShpThread(QThread):
    """WKT转SHP转换线程类"""
    success = pyqtSignal(str)  # 成功信号，传递输出文件路径
    error = pyqtSignal(str)     # 错误信号
    
    def __init__(self, wkt_string, output_path, output_type="SHP文件", output_layer=""):
        super().__init__()
        self.wkt_string = wkt_string
        self.output_path = output_path
        self.output_type = output_type
        self.output_layer = output_layer
    
    def run(self):
        """执行WKT转SHP转换"""
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            from shapely.wkt import loads
            import geopandas as gpd
            
            geom = loads(self.wkt_string)
            gdf = gpd.GeoDataFrame(geometry=[geom], crs="EPSG:4326")
            
            if self.output_type == "SHP文件":
                gdf.to_file(self.output_path, driver='ESRI Shapefile', encoding='utf-8')
            else:
                gdf.to_file(self.output_path, layer=self.output_layer, driver='OpenFileGDB')
            
            self.success.emit(self.output_path)
            
        except Exception as e:
            import traceback
            error_msg = f'转换失败: {str(e)}\n\n{traceback.format_exc()}'
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
        # 输入设置区域
        input_group = QGroupBox("输入设置", self)
        input_layout = QVBoxLayout(input_group)
        
        # WKT输入
        wkt_label = QLabel("WKT坐标串：")
        input_layout.addWidget(wkt_label)
        
        self.wktTextEdit = QTextEdit(self)
        self.wktTextEdit.setPlaceholderText("请输入WKT格式的坐标串...")
        self.wktTextEdit.setFixedHeight(150)
        input_layout.addWidget(self.wktTextEdit)
        
        # 操作按钮
        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(10)
        
        self.loadExampleBtn = PushButton("加载示例", self, FIF.INFO)
        self.loadExampleBtn.clicked.connect(self._loadExampleWkt)
        buttons_row.addWidget(self.loadExampleBtn)
        
        self.clearBtn = PushButton("清空", self, FIF.DELETE)
        self.clearBtn.clicked.connect(self._clearWkt)
        buttons_row.addWidget(self.clearBtn)
        
        buttons_row.addStretch(1)
        input_layout.addLayout(buttons_row)
        
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
        self.outputPathEdit = LineEdit(self)
        self.outputPathEdit.setPlaceholderText("选择输出SHP文件路径")
        self.outputPathEdit.setReadOnly(True)
        
        self.browseBtn = PushButton("选择输出路径", self, FIF.SAVE)
        self.browseBtn.clicked.connect(self._selectOutputFile)
        
        self.shp_output_layout.addWidget(shp_output_label)
        self.shp_output_layout.addWidget(self.outputPathEdit, 1)
        self.shp_output_layout.addWidget(self.browseBtn)
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
        self.executeBtn = PrimaryPushButton("开始转换", self, FIF.PLAY)
        self.executeBtn.clicked.connect(self.execute)
        self.contentLayout.addWidget(self.executeBtn, 0, Qt.AlignmentFlag.AlignCenter)
    
    def _on_output_type_changed(self, output_type):
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
    
    def _select_output_gdb(self):
        """选择输出GDB文件"""
        from qfluentwidgets import InfoBar, InfoBarPosition
        file_path = QFileDialog.getExistingDirectory(
            self, "选择输出GDB文件", "."
        )
        
        if file_path:
            if not file_path.lower().endswith('.gdb'):
                InfoBar.warning(
                    title="警告",
                    content="请选择GDB文件",
                    parent=self,
                    position=InfoBarPosition.TOP_RIGHT
                )
                return
            
            self.output_gdb_path.setText(file_path)
    
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
        
        output_type = self.output_type_combo.currentText()
        if output_type == "SHP文件":
            output_path = self.outputPathEdit.text().strip()
            if not output_path:
                return False, "请选择SHP输出文件路径"
            
            if not output_path.lower().endswith('.shp'):
                return False, "输出文件必须是SHP格式"
        else:
            output_path = self.output_gdb_path.text().strip()
            if not output_path:
                return False, "请选择GDB输出路径"
            
            if not output_path.lower().endswith('.gdb'):
                return False, "请选择有效的GDB文件"
            
            if not self.output_gdb_layer.text().strip():
                return False, "请输入GDB图层名称"
        
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
        output_type = self.output_type_combo.currentText()
        
        if output_type == "SHP文件":
            output_path = self.outputPathEdit.text().strip()
            output_layer = ""
        else:
            output_path = self.output_gdb_path.text().strip()
            output_layer = self.output_gdb_layer.text().strip()
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # 创建转换线程
        self.wkt_thread = WktToShpThread(wkt_text, output_path, output_type, output_layer)
        
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
