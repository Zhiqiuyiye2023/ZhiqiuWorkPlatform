# coding:utf-8
"""
KMZ转SHP格式功能
"""

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QFileDialog, QMessageBox, QGroupBox
from qfluentwidgets import (PrimaryPushButton, PushButton, LineEdit, ComboBox,
                           StateToolTip, TextEdit)
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction
import os
import tempfile
import zipfile
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon, MultiPolygon
from shapely.wkt import loads


class KmzToShpThread(QThread):
    """KMZ转SHP转换线程类"""
    log_signal = pyqtSignal(str)       # 日志信号
    success = pyqtSignal(str)          # 成功信号，传递输出文件路径
    error = pyqtSignal(str)            # 错误信号
    
    def __init__(self, kmz_path, output_path, output_type="SHP文件", output_layer=""):
        super().__init__()
        self.kmz_path = kmz_path
        self.output_path = output_path
        self.output_type = output_type
        self.output_layer = output_layer
    
    def run(self):
        """执行KMZ转SHP转换"""
        try:
            import sys
            import os
            import xml.etree.ElementTree as ET
            
            # 发送日志信号
            self.log_signal.emit(f"正在处理KMZ文件: {os.path.basename(self.kmz_path)}")
            
            # 解压KMZ文件
            with tempfile.TemporaryDirectory() as temp_dir:
                self.log_signal.emit(f"正在解压KMZ文件到临时目录: {temp_dir}")
                
                with zipfile.ZipFile(self.kmz_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # 查找KML文件
                kml_files = []
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if file.lower().endswith('.kml'):
                            kml_files.append(os.path.join(root, file))
                
                if not kml_files:
                    raise Exception("在KMZ文件中未找到KML文件")
                
                self.log_signal.emit(f"找到 {len(kml_files)} 个KML文件")
                
                # 处理第一个KML文件
                kml_path = kml_files[0]
                self.log_signal.emit(f"正在处理KML文件: {os.path.basename(kml_path)}")
                
                # 解析KML文件
                tree = ET.parse(kml_path)
                root = tree.getroot()
                
                # 定义命名空间
                namespaces = {
                    'kml': 'http://www.opengis.net/kml/2.2'
                }
                
                # 查找所有Placemark元素
                placemarks = root.findall('.//kml:Placemark', namespaces)
                self.log_signal.emit(f"找到 {len(placemarks)} 个地物")
                
                # 准备转换数据
                features = []
                
                for i, placemark in enumerate(placemarks):
                    try:
                        # 获取名称
                        name_elem = placemark.find('kml:name', namespaces)
                        name = name_elem.text if name_elem is not None else f'地物_{i+1}'
                        
                        # 查找几何元素
                        point = placemark.find('kml:Point', namespaces)
                        line = placemark.find('kml:LineString', namespaces)
                        polygon = placemark.find('kml:Polygon', namespaces)
                        multi_geometry = placemark.find('kml:MultiGeometry', namespaces)
                        
                        geometry = None
                        
                        if point is not None:
                            # 处理点
                            coords_elem = point.find('kml:coordinates', namespaces)
                            if coords_elem is not None:
                                coords = coords_elem.text.strip().split(',')[:2]
                                lon, lat = float(coords[0]), float(coords[1])
                                geometry = Point(lon, lat)
                        
                        elif line is not None:
                            # 处理线
                            coords_elem = line.find('kml:coordinates', namespaces)
                            if coords_elem is not None:
                                coords_text = coords_elem.text.strip()
                                coords_list = []
                                for coord in coords_text.split(): 
                                    if coord.strip():  # 跳过空行
                                        coords = coord.split(',')[:2]
                                        lon, lat = float(coords[0]), float(coords[1])
                                        coords_list.append((lon, lat))
                                geometry = LineString(coords_list)
                        
                        elif polygon is not None:
                            # 处理面
                            outer_boundary = polygon.find('kml:outerBoundaryIs', namespaces)
                            if outer_boundary is not None:
                                linear_ring = outer_boundary.find('kml:LinearRing', namespaces)
                                if linear_ring is not None:
                                    coords_elem = linear_ring.find('kml:coordinates', namespaces)
                                    if coords_elem is not None:
                                        coords_text = coords_elem.text.strip()
                                        coords_list = []
                                        for coord in coords_text.split(): 
                                            if coord.strip():  # 跳过空行
                                                coords = coord.split(',')[:2]
                                                lon, lat = float(coords[0]), float(coords[1])
                                                coords_list.append((lon, lat))
                                        geometry = Polygon(coords_list)
                        
                        elif multi_geometry is not None:
                            # 处理多几何
                            polygons = []
                            multi_polygons = multi_geometry.findall('kml:Polygon', namespaces)
                            for poly in multi_polygons:
                                outer_boundary = poly.find('kml:outerBoundaryIs', namespaces)
                                if outer_boundary is not None:
                                    linear_ring = outer_boundary.find('kml:LinearRing', namespaces)
                                    if linear_ring is not None:
                                        coords_elem = linear_ring.find('kml:coordinates', namespaces)
                                        if coords_elem is not None:
                                            coords_text = coords_elem.text.strip()
                                            coords_list = []
                                            for coord in coords_text.split(): 
                                                if coord.strip():  # 跳过空行
                                                    coords = coord.split(',')[:2]
                                                    lon, lat = float(coords[0]), float(coords[1])
                                                    coords_list.append((lon, lat))
                                            polygons.append(Polygon(coords_list))
                            if polygons:
                                geometry = MultiPolygon(polygons)
                        
                        if geometry is not None:
                            features.append({
                                'geometry': geometry,
                                '名称': name
                            })
                            self.log_signal.emit(f"  处理成功: {name} ({geometry.geom_type})")
                        else:
                            self.log_signal.emit(f"  警告: 地物 {name} 没有可识别的几何类型")
                    except Exception as e:
                        self.log_signal.emit(f"  错误: 处理地物 {i+1} 时出错: {str(e)}")
                
                if not features:
                    raise Exception("没有找到可转换的几何要素")
                
                self.log_signal.emit(f"成功解析 {len(features)} 个要素")
                
                # 创建GeoDataFrame
                gdf = gpd.GeoDataFrame(features, crs='EPSG:4326')
                
                # 根据输出类型保存文件
                if self.output_type == "SHP文件":
                    self.log_signal.emit(f"正在保存SHP文件: {os.path.basename(self.output_path)}")
                    gdf.to_file(self.output_path, encoding='utf-8')
                else:
                    self.log_signal.emit(f"正在保存GDB图层: {self.output_layer}")
                    gdf.to_file(self.output_path, layer=self.output_layer, driver='OpenFileGDB')
                
                self.log_signal.emit(f"转换完成！")
                self.log_signal.emit(f"输出文件: {self.output_path}")
                
                # 发送成功信号
                self.success.emit(self.output_path)
                
        except Exception as e:
            import traceback
            error_msg = f'转换失败: {str(e)}\n\n{traceback.format_exc()}'
            # 发送错误信号
            self.error.emit(error_msg)


class KmzToShpFunction(BaseFunction):
    """KMZ转SHP格式功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>" 
            "将KMZ奥维格式转换为SHP矢量文件"
        )
        super().__init__("KMZ转SHP格式", description, parent)
        
        self._initUI()
        self._running = False
        self.stateTooltip = None
    
    def _initUI(self):
        """初始化界面"""
        # 输入设置区域
        input_group = QGroupBox("输入设置", self)
        input_layout = QVBoxLayout(input_group)
        
        # KMZ文件选择
        kmz_layout = QHBoxLayout()
        kmz_label = QLabel("KMZ文件：")
        self.filePathLabel = LineEdit(self)
        self.filePathLabel.setPlaceholderText("选择要转换的KMZ文件")
        self.filePathLabel.setReadOnly(True)
        
        self.addKmzBtn = PushButton("选择文件", self, FIF.DOCUMENT)
        self.addKmzBtn.clicked.connect(self._selectKmzFile)
        
        kmz_layout.addWidget(kmz_label)
        kmz_layout.addWidget(self.filePathLabel, 1)
        kmz_layout.addWidget(self.addKmzBtn)
        input_layout.addLayout(kmz_layout)
        
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
        
        # 日志显示区域
        self.logText = TextEdit(self)
        self.logText.setReadOnly(True)
        self.logText.setPlaceholderText("转换日志将显示在这里...")
        self.logText.setFixedHeight(200)
        self.contentLayout.addWidget(self.logText)
        
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
    
    def _selectKmzFile(self):
        """选择KMZ文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择KMZ文件", "", "KMZ文件 (*.kmz)"
        )
        if file_path:
            self.filePathLabel.setText(file_path)
            # 设置默认输出路径
            base_path, ext = os.path.splitext(file_path)
            default_path = f"{base_path}.shp"
            self.output_path_edit.setText(default_path)
    
    def _selectOutputFile(self):
        """选择SHP输出文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存SHP文件", "", "SHP文件 (*.shp)"
        )
        if file_path:
            if not file_path.endswith('.shp'):
                file_path += '.shp'
            self.output_path_edit.setText(file_path)
    
    def validate(self) -> tuple[bool, str]:
        """验证输入"""
        if not self.filePathLabel.text():
            return False, "请选择KMZ文件"
        
        if not os.path.exists(self.filePathLabel.text()):
            return False, "文件不存在"
        
        if not self.filePathLabel.text().lower().endswith('.kmz'):
            return False, "请选择有效的KMZ文件"
        
        output_type = self.output_type_combo.currentText()
        if output_type == "SHP文件":
            if not self.output_path_edit.text():
                return False, "请选择SHP输出路径"
        else:
            if not self.output_gdb_path.text():
                return False, "请选择GDB输出路径"
            if not self.output_gdb_path.text().lower().endswith('.gdb'):
                return False, "请选择有效的GDB文件"
            if not self.output_gdb_layer.text():
                return False, "请输入GDB图层名称"
        
        return True, ""
    
    def execute(self):
        """执行KMZ转SHP转换"""
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
        
        # 清除之前的日志
        self.logText.clear()
        
        # 获取参数
        kmz_path = self.filePathLabel.text()
        output_type = self.output_type_combo.currentText()
        
        if output_type == "SHP文件":
            output_path = self.output_path_edit.text()
            output_layer = ""
        else:
            output_path = self.output_gdb_path.text()
            output_layer = self.output_gdb_layer.text()
        
        # 创建转换线程
        self.kmz_thread = KmzToShpThread(kmz_path, output_path, output_type, output_layer)
        
        # 连接信号槽
        self.kmz_thread.log_signal.connect(self._on_kmz_log)
        self.kmz_thread.success.connect(self._on_kmz_success)
        self.kmz_thread.error.connect(self._on_kmz_error)
        
        # 启动线程
        self.kmz_thread.start()
    
    def _on_kmz_log(self, msg):
        """处理日志信号"""
        self.logText.append(msg)
        # 滚动到底部
        scrollbar = self.logText.verticalScrollBar()
        if scrollbar:
            scrollbar.setValue(scrollbar.maximum())
    
    def _on_kmz_success(self, shp_path):
        """KMZ转SHP成功处理"""
        output_type = self.output_type_combo.currentText()
        if output_type == "SHP文件":
            self.showSuccess(f"KMZ转SHP成功！\n输出文件: {shp_path}")
        else:
            self.showSuccess(f"KMZ转GDB成功！\n输出GDB: {shp_path}\n输出图层: {self.output_gdb_layer.text()}")
        self._running = False
        if hasattr(self, 'stateTooltip') and self.stateTooltip:
            try:
                self.stateTooltip.close()
            except:
                pass
    
    def _on_kmz_error(self, error_msg):
        """KMZ转SHP错误处理"""
        self.showError(error_msg)
        self._running = False
        if hasattr(self, 'stateTooltip') and self.stateTooltip:
            try:
                self.stateTooltip.close()
            except:
                pass
