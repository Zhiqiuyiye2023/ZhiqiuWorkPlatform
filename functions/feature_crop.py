from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog,
    QGroupBox, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from qfluentwidgets import LineEdit, PushButton, ComboBox, SpinBox
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction
import geopandas as gpd
import fiona
from shapely.geometry import Point, Polygon, MultiPolygon, LineString, MultiLineString
from shapely.ops import unary_union
import os
import sys

class CropThread(QThread):
    progress_updated = pyqtSignal(int, str)
    result_ready = pyqtSignal(bool, str)

    def __init__(self, feature_a_path, layer_a, feature_b_path, layer_b, output_path, buffer_threshold, output_gdb_path):
        super().__init__()
        self.feature_a_path = feature_a_path
        self.layer_a = layer_a
        self.feature_b_path = feature_b_path
        self.layer_b = layer_b
        self.output_path = output_path
        self.buffer_threshold = buffer_threshold
        self.output_gdb_path = output_gdb_path

    def run(self):
        try:
            # 读取数据
            self.progress_updated.emit(5, "正在读取裁剪范围文件...")
            
            if self.feature_a_path.lower().endswith('.shp'):
                feature_a = gpd.read_file(self.feature_a_path, driver='ESRI Shapefile')
            else:
                feature_a = gpd.read_file(self.feature_a_path, layer=self.layer_a)
            
            self.progress_updated.emit(20, f"裁剪范围包含 {len(feature_a)} 个要素")
            
            self.progress_updated.emit(25, "正在读取被裁剪文件...")
            
            if self.feature_b_path.lower().endswith('.shp'):
                feature_b = gpd.read_file(self.feature_b_path, driver='ESRI Shapefile')
            else:
                feature_b = gpd.read_file(self.feature_b_path, layer=self.layer_b)
            
            self.progress_updated.emit(40, f"被裁剪文件包含 {len(feature_b)} 个要素")
            
            # 合并所有裁剪图斑
            self.progress_updated.emit(50, "合并所有裁剪图斑...")
            merged_feature_a = unary_union(feature_a.geometry)
            
            # 外扩指定阈值
            self.progress_updated.emit(55, f"对裁剪范围外扩 {self.buffer_threshold} 米...")
            buffered_feature_a = merged_feature_a.buffer(self.buffer_threshold)
            
            # 计算外扩范围的边界框
            bounds = buffered_feature_a.bounds
            minx, miny, maxx, maxy = bounds
            
            # 边界框快速筛选
            self.progress_updated.emit(60, "使用边界框快速筛选要素...")
            feature_b_quick = feature_b.cx[minx:maxx, miny:maxy]
            
            self.progress_updated.emit(65, f"边界框筛选后剩余 {len(feature_b_quick)} 个要素")
            
            # 筛选与外扩范围相交的要素
            self.progress_updated.emit(70, "精确筛选与外扩范围相交的要素...")
            feature_b_intersect = feature_b_quick[feature_b_quick.intersects(buffered_feature_a)]
            
            self.progress_updated.emit(75, f"精确筛选后剩余 {len(feature_b_intersect)} 个要素")
            
            # 实际裁剪
            self.progress_updated.emit(80, "开始实际裁剪...")
            cropped_features = []
            total = len(feature_b_intersect)
            for i, (_, row) in enumerate(feature_b_intersect.iterrows()):
                if row.geometry.intersects(buffered_feature_a):
                    cropped_geom = row.geometry.intersection(buffered_feature_a)
                    if not cropped_geom.is_empty:
                        new_row = row.copy()
                        new_row.geometry = cropped_geom
                        cropped_features.append(new_row)
                # 更新进度
                if (i + 1) % 100 == 0 or (i + 1) == total:
                    progress = 80 + int((i + 1) / total * 15)
                    self.progress_updated.emit(progress, f"正在裁剪第 {i+1}/{total} 个要素")
            
            self.progress_updated.emit(95, "合并裁剪结果...")
            
            if not cropped_features:
                self.result_ready.emit(False, "没有找到相交的要素")
                return
            
            cropped_gdf = gpd.GeoDataFrame(cropped_features, crs=feature_b.crs)
            
            # 过滤掉非多边形要素，只保留Polygon和MultiPolygon类型
            self.progress_updated.emit(93, "过滤非多边形要素...")
            polygon_types = ['Polygon', 'MultiPolygon']
            cropped_gdf = cropped_gdf[cropped_gdf.geom_type.isin(polygon_types)]
            
            if len(cropped_gdf) == 0:
                self.result_ready.emit(False, "裁剪结果中没有多边形要素")
                return
            
            # 保存结果
            self.progress_updated.emit(97, "正在保存结果...")
            if self.output_gdb_path:
                # 输出到GDB
                layer_name = os.path.splitext(os.path.basename(self.output_path))[0]
                cropped_gdf.to_file(
                    self.output_gdb_path, 
                    layer=layer_name,
                    driver='OpenFileGDB',
                    mode='a'
                )
            else:
                # 输出到文件
                cropped_gdf.to_file(self.output_path, driver='ESRI Shapefile')
            
            self.progress_updated.emit(100, "裁剪完成")
            self.result_ready.emit(True, f"裁剪完成，共裁剪 {len(cropped_gdf)} 个要素")
            
        except Exception as e:
            import traceback
            self.result_ready.emit(False, f"裁剪失败：{str(e)}\n\n详细错误信息：{traceback.format_exc()}")

class FeatureCropFunction(BaseFunction):
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>"
            "执行要素裁剪操作，使用裁剪范围裁剪要素，支持输出到文件或GDB"
        )
        super().__init__("要素裁剪", description, parent)
        
        # 初始化UI
        self._initUI()
        
        # 添加执行按钮
        self.execute_btn = self.addExecuteButton("开始裁剪", self.start_crop)
    
    def _initUI(self):
        """初始化界面控件"""
        # 创建输入矢量选择区域
        input_vector_group = QGroupBox("输入矢量数据", self)
        input_vector_layout = QVBoxLayout(input_vector_group)
        
        # 裁剪范围文件选择
        feature_a_layout = QHBoxLayout()
        feature_a_label = QLabel("裁剪范围文件：")
        self.feature_a_path = LineEdit(self)
        self.feature_a_path.setPlaceholderText("选择裁剪范围文件")
        self.feature_a_path.setReadOnly(True)
        
        # 分别添加SHP和GDB文件选择按钮
        self.feature_a_shp_btn = PushButton("选择SHP", self, FIF.FOLDER)
        self.feature_a_shp_btn.clicked.connect(lambda: self._selectFeatureFile("crop", shp_only=True))
        self.feature_a_shp_btn.setFixedWidth(120)
        
        self.feature_a_gdb_btn = PushButton("选择GDB", self, FIF.FOLDER)
        self.feature_a_gdb_btn.clicked.connect(lambda: self._selectFeatureFile("crop", gdb_only=True))
        self.feature_a_gdb_btn.setFixedWidth(120)
        
        feature_a_layout.addWidget(feature_a_label)
        feature_a_layout.addWidget(self.feature_a_path, 1)
        feature_a_layout.addWidget(self.feature_a_shp_btn)
        feature_a_layout.addWidget(self.feature_a_gdb_btn)
        input_vector_layout.addLayout(feature_a_layout)
        
        # 裁剪范围图层选择（仅GDB文件显示）
        self.feature_a_layer_layout = QHBoxLayout()
        feature_a_layer_label = QLabel("裁剪范围图层：")
        self.feature_a_layer_combo = ComboBox(self)
        self.feature_a_layer_combo.setPlaceholderText("请先选择文件")
        self.feature_a_layer_combo.setEnabled(False)
        
        self.feature_a_layer_layout.addWidget(feature_a_layer_label)
        self.feature_a_layer_layout.addWidget(self.feature_a_layer_combo, 1)
        # 默认隐藏图层选择
        for i in range(self.feature_a_layer_layout.count()):
            widget = self.feature_a_layer_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(False)
        input_vector_layout.addLayout(self.feature_a_layer_layout)
        
        # 被裁剪文件选择
        feature_b_layout = QHBoxLayout()
        feature_b_label = QLabel("被裁剪文件：")
        self.feature_b_path = LineEdit(self)
        self.feature_b_path.setPlaceholderText("选择被裁剪文件")
        self.feature_b_path.setReadOnly(True)
        
        # 分别添加SHP和GDB文件选择按钮
        self.feature_b_shp_btn = PushButton("选择SHP", self, FIF.FOLDER)
        self.feature_b_shp_btn.clicked.connect(lambda: self._selectFeatureFile("clip", shp_only=True))
        self.feature_b_shp_btn.setFixedWidth(120)
        
        self.feature_b_gdb_btn = PushButton("选择GDB", self, FIF.FOLDER)
        self.feature_b_gdb_btn.clicked.connect(lambda: self._selectFeatureFile("clip", gdb_only=True))
        self.feature_b_gdb_btn.setFixedWidth(120)
        
        feature_b_layout.addWidget(feature_b_label)
        feature_b_layout.addWidget(self.feature_b_path, 1)
        feature_b_layout.addWidget(self.feature_b_shp_btn)
        feature_b_layout.addWidget(self.feature_b_gdb_btn)
        input_vector_layout.addLayout(feature_b_layout)
        
        # 被裁剪图层选择（仅GDB文件显示）
        self.feature_b_layer_layout = QHBoxLayout()
        feature_b_layer_label = QLabel("被裁剪图层：")
        self.feature_b_layer_combo = ComboBox(self)
        self.feature_b_layer_combo.setPlaceholderText("请先选择文件")
        self.feature_b_layer_combo.setEnabled(False)
        
        self.feature_b_layer_layout.addWidget(feature_b_layer_label)
        self.feature_b_layer_layout.addWidget(self.feature_b_layer_combo, 1)
        # 默认隐藏图层选择
        for i in range(self.feature_b_layer_layout.count()):
            widget = self.feature_b_layer_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(False)
        input_vector_layout.addLayout(self.feature_b_layer_layout)
        
        # 裁剪参数设置区域
        param_group = QGroupBox("裁剪参数设置", self)
        param_layout = QVBoxLayout(param_group)
        
        # 重叠面积阈值
        threshold_layout = QHBoxLayout()
        threshold_label = QLabel("外扩阈值(米)：")
        self.buffer_spin = SpinBox(self)
        self.buffer_spin.setValue(0)
        self.buffer_spin.setMinimum(0)
        self.buffer_spin.setMaximum(1000)
        
        threshold_layout.addWidget(threshold_label)
        threshold_layout.addWidget(self.buffer_spin)
        threshold_layout.addStretch(1)
        param_layout.addLayout(threshold_layout)
        
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
        
        # 输出文件/图层设置
        # SHP输出路径
        self.shp_output_layout = QHBoxLayout()
        shp_output_label = QLabel("SHP输出路径：")
        self.outputFilePath = LineEdit(self)
        self.outputFilePath.setPlaceholderText("选择输出SHP文件路径")
        self.outputFilePath.setReadOnly(True)
        
        self.outputFileBtn = PushButton("选择输出路径", self, FIF.SAVE)
        self.outputFileBtn.clicked.connect(self._selectOutputFile)
        
        self.shp_output_layout.addWidget(shp_output_label)
        self.shp_output_layout.addWidget(self.outputFilePath, 1)
        self.shp_output_layout.addWidget(self.outputFileBtn)
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
        self.output_gdb_layer.setPlaceholderText("输入或选择输出图层名称")
        
        self.gdb_layer_layout.addWidget(gdb_layer_label)
        self.gdb_layer_layout.addWidget(self.output_gdb_layer, 1)
        output_layout.addLayout(self.gdb_layer_layout)
        
        # 进度条容器
        self.progress_container = QWidget(self)
        self.progress_layout = QVBoxLayout(self.progress_container)
        self.progress_layout.setContentsMargins(0, 0, 0, 0)
        self.progress_layout.setSpacing(5)
        
        # 进度文本
        self.progress_text = QLabel("准备开始裁剪...", self)
        self.progress_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_text.setStyleSheet("QLabel { font-weight: bold; }")
        
        # 进度条
        self.progress_bar = QFrame(self)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setStyleSheet("""
            QFrame {
                background-color: #e0e0e0;
                border-radius: 2px;
            }
        """)
        
        # 将进度文本和进度条添加到容器
        self.progress_layout.addWidget(self.progress_text)
        self.progress_layout.addWidget(self.progress_bar)
        
        # 设置容器初始不可见
        self.progress_container.setVisible(False)
        
        # 初始显示SHP输出选项
        self._on_output_type_changed("SHP文件")
        
        # 将所有组件添加到内容布局
        self.contentLayout.addWidget(input_vector_group)
        self.contentLayout.addWidget(param_group)
        self.contentLayout.addWidget(output_group)
        self.contentLayout.addSpacing(20)
        self.contentLayout.addWidget(self.progress_container)
        self.contentLayout.addSpacing(20)
    
    def _selectFeatureFile(self, feature_type, shp_only=False, gdb_only=False):
        """选择要素文件"""
        file_path = ""
        
        if shp_only:
            # 选择SHP文件
            file_path, _ = QFileDialog.getOpenFileName(
                self, f"选择{feature_type}SHP文件", ".", "Shapefiles (*.shp)"
            )
        elif gdb_only:
            # 选择GDB文件（GDB是目录，所以使用getExistingDirectory）
            file_path = QFileDialog.getExistingDirectory(
                self, f"选择{feature_type}GDB文件", "."
            )
        else:
            # 选择所有矢量文件
            file_path, _ = QFileDialog.getOpenFileName(
                self, f"选择{feature_type}文件", ".", "矢量文件 (*.shp *.geojson *.json *.gpkg);;所有文件 (*)"
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
            
            if feature_type == "crop":
                self.feature_a_path.setText(file_path)
                # 自动生成输出文件名
                self._autoGenerateOutputPath(file_path)
                # 更新图层列表
                self._update_feature_layer_list("crop", file_path)
            else:
                self.feature_b_path.setText(file_path)
                # 更新图层列表
                self._update_feature_layer_list("clip", file_path)
    
    def _update_feature_layer_list(self, feature_type, file_path):
        """更新要素图层列表"""
        if feature_type == "crop":
            combo = self.feature_a_layer_combo
            layout = self.feature_a_layer_layout
        else:
            combo = self.feature_b_layer_combo
            layout = self.feature_b_layer_layout
        
        combo.clear()
        combo.setEnabled(False)
        
        if file_path.lower().endswith('.gdb'):
            # 显示图层选择控件
            for i in range(layout.count()):
                widget = layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(True)
            # 列出GDB中的所有图层
            try:
                with fiona.Env():
                    layers = fiona.listlayers(file_path)
                combo.addItems(layers)
                combo.setEnabled(True)
            except Exception as e:
                from qfluentwidgets import InfoBar, InfoBarPosition
                InfoBar.error(
                    title="错误",
                    content=f"无法读取GDB文件: {str(e)}",
                    parent=self,
                    position=InfoBarPosition.TOP_RIGHT
                )
        else:
            # 隐藏图层选择控件
            for i in range(layout.count()):
                widget = layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(False)
            # SHP文件不需要图层选择
            combo.setPlaceholderText("SHP文件无需选择图层")
    
    def _autoGenerateOutputPath(self, input_path):
        """自动生成输出文件名"""
        dir_name = os.path.dirname(input_path)
        base_name = os.path.basename(input_path)
        name, ext = os.path.splitext(base_name)
        output_path = os.path.join(dir_name, f"{name}_cropped.shp")
        self.outputFilePath.setText(output_path)
    
    def _on_output_type_changed(self, output_type):
        """输出类型变化处理"""
        if output_type == "SHP文件":
            # 显示SHP输出选项，隐藏GDB输出选项
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
            # 显示GDB输出选项，隐藏SHP输出选项
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
    
    def _selectOutputFile(self):
        """选择输出文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "选择输出文件", "", "Shapefiles (*.shp)"
        )
        if file_path:
            self.outputFilePath.setText(file_path)
    
    def _select_output_gdb(self):
        """选择输出GDB文件"""
        file_path = QFileDialog.getExistingDirectory(
            self, "选择输出GDB文件", "."
        )
        
        if file_path:
            if not file_path.endswith('.gdb'):
                from qfluentwidgets import InfoBar, InfoBarPosition
                InfoBar.warning(
                    title="警告",
                    content="请选择GDB文件",
                    parent=self,
                    position=InfoBarPosition.TOP_RIGHT
                )
                return
            
            self.output_gdb_path.setText(file_path)
    
    def updateProgress(self, percent: int, status: str = ""):
        """更新进度条和进度文本"""
        # 更新进度文本
        if status:
            self.progress_text.setText(f"{status} {percent}%")
        else:
            self.progress_text.setText(f"正在裁剪... {percent}%")
        
        # 更新进度条样式
        progress_ratio = percent / 100.0
        style = ""
        style += "QFrame {"
        style += "    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
        style += f"        stop:0 #0078D4, stop:{progress_ratio} #0078D4, "
        style += f"        stop:{progress_ratio} #e0e0e0, stop:1 #e0e0e0);"
        style += "    border-radius: 2px;"
        style += "}"
        self.progress_bar.setStyleSheet(style)
    
    def reset_progress(self):
        """重置进度条"""
        self.progress_container.setVisible(False)
        self.progress_text.setText("准备开始裁剪...")
        self.progress_bar.setStyleSheet("""
            QFrame {
                background-color: #e0e0e0;
                border-radius: 2px;
            }
        """)
    
    def validate(self) -> tuple[bool, str]:
        """验证输入参数"""
        # 验证输入文件
        if not self.feature_a_path.text():
            return False, "请选择裁剪范围文件"
        
        if not self.feature_b_path.text():
            return False, "请选择被裁剪文件"
        
        if not os.path.exists(self.feature_a_path.text()):
            return False, "裁剪范围文件不存在"
        
        if not os.path.exists(self.feature_b_path.text()):
            return False, "被裁剪文件不存在"
        
        # 验证GDB输入的图层选择
        if self.feature_a_path.text().lower().endswith('.gdb'):
            if not self.feature_a_layer_combo.currentText():
                return False, "请选择裁剪范围的GDB图层"
        
        if self.feature_b_path.text().lower().endswith('.gdb'):
            if not self.feature_b_layer_combo.currentText():
                return False, "请选择被裁剪的GDB图层"
        
        # 验证输出设置
        output_type = self.output_type_combo.currentText()
        if output_type == "SHP文件":
            # 验证SHP输出
            if not self.outputFilePath.text():
                return False, "请选择SHP输出路径"
            
            # 检查输出目录是否存在
            output_dir = os.path.dirname(self.outputFilePath.text())
            if not os.path.exists(output_dir):
                return False, "SHP输出目录不存在"
        else:
            # 验证GDB输出
            if not self.output_gdb_path.text():
                return False, "请选择GDB输出路径"
            
            if not os.path.exists(self.output_gdb_path.text()):
                return False, "GDB输出文件不存在"
            
            if not self.output_gdb_path.text().lower().endswith('.gdb'):
                return False, "请选择有效的GDB文件"
            
            if not self.output_gdb_layer.text():
                return False, "请输入GDB输出图层名称"
        
        return True, ""
    
    def start_crop(self):
        """执行功能"""
        # 1. 验证输入
        valid, message = self.validate()
        if not valid:
            self.showError(message)
            print(f"验证失败: {message}")
            return
        
        # 2. 获取参数
        feature_a_path = self.feature_a_path.text()
        feature_b_path = self.feature_b_path.text()
        threshold = self.buffer_spin.value()
        
        # 获取图层名称
        feature_a_layer = self.feature_a_layer_combo.currentText() if feature_a_path.lower().endswith('.gdb') else ""
        feature_b_layer = self.feature_b_layer_combo.currentText() if feature_b_path.lower().endswith('.gdb') else ""
        
        # 获取输出设置
        output_type = self.output_type_combo.currentText()
        if output_type == "SHP文件":
            output_path = self.outputFilePath.text()
            output_gdb_path = ""
        else:
            output_path = self.output_gdb_layer.text()
            output_gdb_path = self.output_gdb_path.text()
        
        print(f"开始执行要素裁剪...")
        print(f"裁剪范围: {feature_a_path}")
        print(f"裁剪范围图层: {feature_a_layer}")
        print(f"被裁剪文件: {feature_b_path}")
        print(f"被裁剪图层: {feature_b_layer}")
        print(f"外扩阈值: {threshold}")
        print(f"输出类型: {output_type}")
        print(f"输出路径: {output_path}")
        if output_gdb_path:
            print(f"输出GDB: {output_gdb_path}")
        
        # 显示进度
        self.showProgress("正在裁剪...")
        # 设置进度条容器为可见
        self.progress_container.setVisible(True)
        
        # 启动裁剪线程
        self.crop_thread = CropThread(
            feature_a_path, feature_a_layer, feature_b_path, feature_b_layer, 
            output_path, threshold, output_gdb_path
        )
        self.crop_thread.progress_updated.connect(self.updateProgress)
        self.crop_thread.result_ready.connect(self._crop_finished)
        self.crop_thread.start()
    
    def _crop_finished(self, success, message):
        """裁剪完成处理"""
        if success:
            self.showSuccess(message)
        else:
            self.showError(message)
        # 无论成功还是失败，重置进度条
        self.reset_progress()