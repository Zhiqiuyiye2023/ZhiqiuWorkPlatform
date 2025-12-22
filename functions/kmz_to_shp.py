# coding:utf-8
"""
KMZ转SHP格式功能
"""

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QFileDialog, QMessageBox
from qfluentwidgets import (PrimaryPushButton, TransparentPushButton, 
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
    
    def __init__(self, kmz_path):
        super().__init__()
        self.kmz_path = kmz_path
    
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
                
                # 生成输出路径
                output_dir = os.path.dirname(self.kmz_path)
                base_name = os.path.splitext(os.path.basename(self.kmz_path))[0]
                shp_path = os.path.join(output_dir, f"{base_name}.shp")
                
                # 保存为SHP文件
                self.log_signal.emit(f"正在保存SHP文件: {os.path.basename(shp_path)}")
                gdf.to_file(shp_path, encoding='utf-8')
                
                self.log_signal.emit(f"转换完成！")
                self.log_signal.emit(f"输出文件: {shp_path}")
                
                # 发送成功信号
                self.success.emit(shp_path)
                
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
        # 功能说明标签
        infoLabel = QLabel(
            "📢 <span style='color: orange; font-weight: bold;'>功能说明：</span>"
            "<br>1. 选择KMZ文件进行转换"
            "<br>2. 转换后的SHP文件将保存到原KMZ文件目录"
            "<br>3. 支持点、线、面等几何类型"
            "<br>4. 自动处理坐标系转换"
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
        
        # 按钮和控件布局
        buttonLayout = QHBoxLayout()
        
        # 执行按钮
        self.executeBtn = PrimaryPushButton(self.tr('开始转换'), self, FIF.SEND)
        self.executeBtn.clicked.connect(self.execute)
        buttonLayout.addWidget(self.executeBtn)
        
        # 添加KMZ文件按钮
        self.addKmzBtn = TransparentPushButton(self.tr('添加KMZ文件'), self, FIF.DOCUMENT)
        self.addKmzBtn.clicked.connect(self._selectKmzFile)
        buttonLayout.addWidget(self.addKmzBtn)
        
        # 文件路径标签
        self.filePathLabel = QLabel("")
        buttonLayout.addWidget(self.filePathLabel)
        
        self.contentLayout.addLayout(buttonLayout)
        
        # 日志显示区域
        self.logText = TextEdit(self)
        self.logText.setReadOnly(True)
        self.logText.setPlaceholderText("转换日志将显示在这里...")
        self.logText.setFixedHeight(200)
        self.logText.setFixedWidth(1070)
        self.contentLayout.addWidget(self.logText)
    
    def _selectKmzFile(self):
        """选择KMZ文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择KMZ文件", "", "KMZ文件 (*.kmz)"
        )
        if file_path:
            self.filePathLabel.setText(file_path)
    
    def validate(self) -> tuple[bool, str]:
        """验证输入"""
        if not self.filePathLabel.text():
            return False, "请选择KMZ文件"
        
        if not os.path.exists(self.filePathLabel.text()):
            return False, "文件不存在"
        
        if not self.filePathLabel.text().lower().endswith('.kmz'):
            return False, "请选择有效的KMZ文件"
        
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
        
        # 获取KMZ文件路径
        kmz_path = self.filePathLabel.text()
        
        # 创建转换线程
        self.kmz_thread = KmzToShpThread(kmz_path)
        
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
        # 显示成功信息
        self.showSuccess(f"KMZ转SHP成功！\n输出文件: {shp_path}")
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
