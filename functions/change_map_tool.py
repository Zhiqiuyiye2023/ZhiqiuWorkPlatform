# coding:utf-8
"""
变更上图工具功能模块
执行变更上图的迭代处理模式，包括要素转换与裁剪、延长线要素、分割要素B
"""

from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QFileDialog, QWidget, QFrame, QGroupBox
from PyQt6.QtCore import Qt
from qfluentwidgets import LineEdit, PushButton, ComboBox, SpinBox
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction
import threading
import os
import pandas as pd
import geopandas as gpd
from shapely.ops import unary_union, split, polygonize
from shapely.geometry import LineString, MultiLineString, Point, Polygon, box
import concurrent.futures


class ChangeMapToolFunction(BaseFunction):
    """变更上图工具功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>"
            "执行变更上图的迭代处理模式，包括要素转换与裁剪、延长线要素、分割数据库底图、要素去重叠以及空间挂接字段等步骤。"
        )
        super().__init__("变更上图工具", description, parent)
        
        # 定义默认文件路径
        self.feature_a_path = ""
        self.feature_b_path = ""
        self.buffer_distance = "0.1"
        self.extend_distance = "0.5"
        
        # 添加时间跟踪变量
        self.start_time = None
        self.operation_start_time = None
        
        # 添加界面更新控制变量
        self.last_update_time = 0
        self.update_interval = 0.1  # 100毫秒更新一次界面
        
        # 线程管理相关配置
        self.cpu_count = os.cpu_count()
        self.max_threads = min(10, self.cpu_count + 4)  # 最大线程数
        self.batch_size = 100  # 每个批次处理的要素数量
        
        # 使用普通变量进行进度更新，线程池使用普通锁即可
        self.processed_count = 0  # 已处理的要素数量
        self.total_count = 0  # 总要素数量
        self.progress_lock = threading.Lock()  # 用于保护进度更新的锁
        
        # 初始化UI
        self._initUI()
        
        # 添加执行按钮布局
        execute_layout = QHBoxLayout()
        
        # 添加帮助按钮
        self.help_btn = PushButton("帮助", self, FIF.HELP)
        self.help_btn.setFixedWidth(100)
        self.help_btn.clicked.connect(self.show_detailed_help)
        execute_layout.addWidget(self.help_btn)
        
        execute_layout.addStretch(1)
        
        # 开始上图按钮（原迭代处理模式）
        self.iterative_btn = PushButton("开始上图", self, FIF.UPDATE)
        self.iterative_btn.clicked.connect(self.execute_iterative_mode)
        self.iterative_btn.setFixedWidth(150)
        execute_layout.addWidget(self.iterative_btn)
        
        self.contentLayout.addLayout(execute_layout)
        
        # 添加时长显示相关变量
        self.start_time = None
        self.end_time = None
    
    def _initUI(self):
        """初始化界面控件"""
        
        # 创建输入矢量选择区域
        input_vector_group = QGroupBox("输入矢量数据", self)
        input_vector_layout = QVBoxLayout(input_vector_group)
        
        # 上图图斑文件选择
        feature_a_layout = QHBoxLayout()
        feature_a_label = QLabel("上图图斑：")
        self.feature_a_lineedit = LineEdit(self)
        self.feature_a_lineedit.setPlaceholderText("选择上图图斑文件")
        self.feature_a_lineedit.setReadOnly(True)
        
        # 分别添加SHP和GDB文件选择按钮
        self.feature_a_shp_btn = PushButton("选择SHP", self, FIF.FOLDER)
        self.feature_a_shp_btn.clicked.connect(lambda: self._select_feature_a(shp_only=True))
        self.feature_a_shp_btn.setFixedWidth(120)
        
        self.feature_a_gdb_btn = PushButton("选择GDB", self, FIF.FOLDER)
        self.feature_a_gdb_btn.clicked.connect(lambda: self._select_feature_a(gdb_only=True))
        self.feature_a_gdb_btn.setFixedWidth(120)
        
        feature_a_layout.addWidget(feature_a_label)
        feature_a_layout.addWidget(self.feature_a_lineedit, 1)
        feature_a_layout.addWidget(self.feature_a_shp_btn)
        feature_a_layout.addWidget(self.feature_a_gdb_btn)
        input_vector_layout.addLayout(feature_a_layout)
        
        # 上图图斑图层选择（仅GDB文件显示）
        self.feature_a_layer_layout = QHBoxLayout()
        feature_a_layer_label = QLabel("上图图斑图层：")
        self.feature_a_layer_combo = ComboBox(self)
        self.feature_a_layer_combo.setPlaceholderText("请先选择文件")
        self.feature_a_layer_combo.setEnabled(False)
        
        self.feature_a_layer_layout.addWidget(feature_a_layer_label)
        self.feature_a_layer_layout.addWidget(self.feature_a_layer_combo, 1)
        # 创建一个容器widget来包装图层选择布局，用于控制显示/隐藏
        self.feature_a_layer_widget = QWidget(self)
        self.feature_a_layer_widget.setLayout(self.feature_a_layer_layout)
        self.feature_a_layer_widget.setVisible(False)  # 默认隐藏
        input_vector_layout.addWidget(self.feature_a_layer_widget)
        
        # 数据库底图文件选择
        feature_b_layout = QHBoxLayout()
        feature_b_label = QLabel("数据库底图：")
        self.feature_b_lineedit = LineEdit(self)
        self.feature_b_lineedit.setPlaceholderText("选择数据库底图文件")
        self.feature_b_lineedit.setReadOnly(True)
        
        # 分别添加SHP和GDB文件选择按钮
        self.feature_b_shp_btn = PushButton("选择SHP", self, FIF.FOLDER)
        self.feature_b_shp_btn.clicked.connect(lambda: self._select_feature_b(shp_only=True))
        self.feature_b_shp_btn.setFixedWidth(120)
        
        self.feature_b_gdb_btn = PushButton("选择GDB", self, FIF.FOLDER)
        self.feature_b_gdb_btn.clicked.connect(lambda: self._select_feature_b(gdb_only=True))
        self.feature_b_gdb_btn.setFixedWidth(120)
        
        feature_b_layout.addWidget(feature_b_label)
        feature_b_layout.addWidget(self.feature_b_lineedit, 1)
        feature_b_layout.addWidget(self.feature_b_shp_btn)
        feature_b_layout.addWidget(self.feature_b_gdb_btn)
        input_vector_layout.addLayout(feature_b_layout)
        
        # 数据库底图图层选择（仅GDB文件显示）
        self.feature_b_layer_layout = QHBoxLayout()
        feature_b_layer_label = QLabel("数据库底图图层：")
        self.feature_b_layer_combo = ComboBox(self)
        self.feature_b_layer_combo.setPlaceholderText("请先选择文件")
        self.feature_b_layer_combo.setEnabled(False)
        
        self.feature_b_layer_layout.addWidget(feature_b_layer_label)
        self.feature_b_layer_layout.addWidget(self.feature_b_layer_combo, 1)
        # 创建一个容器widget来包装图层选择布局，用于控制显示/隐藏
        self.feature_b_layer_widget = QWidget(self)
        self.feature_b_layer_widget.setLayout(self.feature_b_layer_layout)
        self.feature_b_layer_widget.setVisible(False)  # 默认隐藏
        input_vector_layout.addWidget(self.feature_b_layer_widget)
        
        # 参数设置区域
        param_group = QGroupBox("参数设置", self)
        param_layout = QVBoxLayout(param_group)
        
        # 外扩阈值
        buffer_layout = QHBoxLayout()
        buffer_label = QLabel("外扩阈值：")
        self.buffer_distance_lineedit = LineEdit(self)
        self.buffer_distance_lineedit.setText(self.buffer_distance)
        buffer_unit_label = QLabel("单位：根据数据坐标系调整")
        
        buffer_layout.addWidget(buffer_label)
        buffer_layout.addWidget(self.buffer_distance_lineedit)
        buffer_layout.addWidget(buffer_unit_label)
        buffer_layout.addStretch(1)
        param_layout.addLayout(buffer_layout)
        
        # 延长距离
        extend_layout = QHBoxLayout()
        extend_label = QLabel("延长距离：")
        self.extend_distance_lineedit = LineEdit(self)
        self.extend_distance_lineedit.setText(self.extend_distance)
        extend_unit_label = QLabel("单位：米")
        
        extend_layout.addWidget(extend_label)
        extend_layout.addWidget(self.extend_distance_lineedit)
        extend_layout.addWidget(extend_unit_label)
        extend_layout.addStretch(1)
        param_layout.addLayout(extend_layout)
        
        # 重叠面积阈值（用于空间挂接）
        threshold_layout = QHBoxLayout()
        threshold_label = QLabel("重叠面积阈值：")
        self.threshold_spinbox = SpinBox(self)
        self.threshold_spinbox.setValue(10)
        self.threshold_spinbox.setMinimum(0)
        self.threshold_spinbox.setMaximum(1000000)
        threshold_unit_label = QLabel("单位：平方米，用于空间挂接字段")
        
        threshold_layout.addWidget(threshold_label)
        threshold_layout.addWidget(self.threshold_spinbox)
        threshold_layout.addWidget(threshold_unit_label)
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
        
        # 中间数据生成选项
        from PyQt6.QtWidgets import QCheckBox
        self.generate_intermediate_checkbox = QCheckBox("生成中间数据", self)
        self.generate_intermediate_checkbox.setChecked(False)  # 默认不生成中间数据
        output_layout.addWidget(self.generate_intermediate_checkbox)
        

        
        # SHP输出路径
        self.shp_output_layout = QHBoxLayout()
        shp_output_label = QLabel("SHP输出目录：")
        self.output_shp_dir = LineEdit(self)
        self.output_shp_dir.setPlaceholderText("选择输出SHP文件的目录")
        self.output_shp_dir.setReadOnly(True)
        
        self.output_shp_btn = PushButton("选择目录", self, FIF.FOLDER)
        self.output_shp_btn.clicked.connect(self._select_output_shp_dir)
        
        self.shp_output_layout.addWidget(shp_output_label)
        self.shp_output_layout.addWidget(self.output_shp_dir, 1)
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
        gdb_layer_label = QLabel("GDB图层名称前缀：")
        self.output_gdb_layer_prefix = LineEdit(self)
        self.output_gdb_layer_prefix.setPlaceholderText("输入输出图层名称前缀")
        
        self.gdb_layer_layout.addWidget(gdb_layer_label)
        self.gdb_layer_layout.addWidget(self.output_gdb_layer_prefix, 1)
        output_layout.addLayout(self.gdb_layer_layout)
        
        # 进度条容器
        self.progress_container = QWidget(self)
        self.progress_layout = QVBoxLayout(self.progress_container)
        self.progress_layout.setContentsMargins(0, 0, 0, 0)
        self.progress_layout.setSpacing(5)
        
        # 进度文本
        self.progress_text = QLabel("准备开始执行...", self)
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
        
        # 初始显示SHP输出选项，隐藏GDB输出选项
        self._on_output_type_changed("SHP文件")
        
        # 将所有组件添加到内容布局
        self.contentLayout.addWidget(input_vector_group)
        self.contentLayout.addWidget(param_group)
        self.contentLayout.addWidget(output_group)
        self.contentLayout.addSpacing(20)
        self.contentLayout.addWidget(self.progress_container)
        self.contentLayout.addSpacing(20)
    
    def _select_feature_a(self, shp_only=False, gdb_only=False):
        """选择上图图斑文件"""
        file_path = ""
        
        if shp_only:
            # 选择SHP文件
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择上图图斑SHP文件", ".", "Shapefiles (*.shp)"
            )
        elif gdb_only:
            # 选择GDB文件（GDB是目录，所以使用getExistingDirectory）
            file_path = QFileDialog.getExistingDirectory(
                self, "选择上图图斑GDB文件", "."
            )
        else:
            # 选择所有矢量文件
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择上图图斑文件", ".", "矢量文件 (*.shp *.geojson *.json *.gpkg);;所有文件 (*)"
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
            
            self.feature_a_lineedit.setText(file_path)
            # 更新图层列表
            self._update_feature_layer_list("A", file_path)
            
            # 如果选择的是GDB文件，自动设置输出类型为GDB图层，并将输出GDB路径设为当前GDB
            if file_path.endswith('.gdb'):
                self.output_type_combo.setCurrentText("GDB图层")
                self.output_gdb_path.setText(file_path)
    
    def _select_feature_b(self, shp_only=False, gdb_only=False):
        """选择数据库底图文件"""
        file_path = ""
        
        if shp_only:
            # 选择SHP文件
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择数据库底图SHP文件", ".", "Shapefiles (*.shp)"
            )
        elif gdb_only:
            # 选择GDB文件（GDB是目录，所以使用getExistingDirectory）
            file_path = QFileDialog.getExistingDirectory(
                self, "选择数据库底图GDB文件", "."
            )
        else:
            # 选择所有矢量文件
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择数据库底图文件", ".", "矢量文件 (*.shp *.geojson *.json *.gpkg);;所有文件 (*)"
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
            
            self.feature_b_lineedit.setText(file_path)
            # 更新图层列表
            self._update_feature_layer_list("B", file_path)
    
    def _update_feature_layer_list(self, feature_type, file_path):
        """更新要素图层列表"""
        if feature_type == "A":
            combo = self.feature_a_layer_combo
            widget = self.feature_a_layer_widget
        else:
            combo = self.feature_b_layer_combo
            widget = self.feature_b_layer_widget
        
        combo.clear()
        combo.setEnabled(False)
        widget.setVisible(False)  # 默认隐藏
        
        if file_path.lower().endswith('.gdb'):
            # 列出GDB中的所有图层
            try:
                import fiona
                with fiona.Env():
                    layers = fiona.listlayers(file_path)
                combo.addItems(layers)
                combo.setEnabled(True)
                widget.setVisible(True)  # 选择GDB后显示图层选择器
            except Exception as e:
                from qfluentwidgets import InfoBar, InfoBarPosition
                InfoBar.error(
                    title="错误",
                    content=f"无法读取GDB文件: {str(e)}",
                    parent=self,
                    position=InfoBarPosition.TOP_RIGHT
                )
        else:
            # SHP文件不需要图层选择
            combo.setPlaceholderText("SHP文件无需选择图层")
            widget.setVisible(False)  # 非GDB文件时隐藏图层选择器
    
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
    
    def _select_output_shp_dir(self):
        """选择SHP输出目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择SHP输出目录", "."
        )
        if dir_path:
            self.output_shp_dir.setText(dir_path)
    
    def _select_output_gdb(self):
        """选择输出GDB文件"""
        file_path = QFileDialog.getExistingDirectory(
            self, "选择输出GDB文件", "."
        )
        
        if file_path:
            if not file_path.lower().endswith('.gdb'):
                from qfluentwidgets import InfoBar, InfoBarPosition
                InfoBar.warning(
                    title="警告",
                    content="请选择GDB文件",
                    parent=self,
                    position=InfoBarPosition.TOP_RIGHT
                )
                return
            
            self.output_gdb_path.setText(file_path)


    def reset_progress(self):
        """重置进度条"""
        self.progress_container.setVisible(False)
        self.progress_text.setText("准备开始执行...")
        self.progress_bar.setStyleSheet("""
            QFrame {
                background-color: #e0e0e0;
                border-radius: 2px;
            }
        """)
    
    def convert_to_lines(self, gdf):
        """将面要素转换为线要素"""
        if len(gdf) == 0:
            return gpd.GeoDataFrame(geometry=[], crs=gdf.crs)
        
        geom_types = gdf.geom_type
        first_geom_type = geom_types.iloc[0] if hasattr(geom_types, 'iloc') else geom_types[0]
        
        if first_geom_type == 'Polygon' or first_geom_type == 'MultiPolygon':
            self.update_progress_signal.emit(30, f"正在转换 {len(gdf)} 个面要素为线要素...")
            lines_gdf = gpd.GeoDataFrame(
                geometry=gdf.boundary, 
                crs=gdf.crs
            )
            lines_gdf = lines_gdf[~lines_gdf.is_empty]
            return lines_gdf
        elif first_geom_type == 'LineString' or first_geom_type == 'MultiLineString':
            return gdf
        else:
            raise ValueError(f"不支持的几何类型: {first_geom_type}")
    
    def split_gdf_into_batches(self, gdf, batch_size=None):
        """将GeoDataFrame分割为多个子GeoDataFrame批次"""
        if batch_size is None:
            batch_size = self.batch_size
        
        total = len(gdf)
        num_batches = (total + batch_size - 1) // batch_size
        
        batches = []
        for i in range(num_batches):
            start_idx = i * batch_size
            end_idx = min((i + 1) * batch_size, total)
            batch = gdf.iloc[start_idx:end_idx]
            batches.append(batch)
        
        return batches
    
    def process_batch(self, batch, process_func, *args, **kwargs):
        """处理单个批次的辅助方法"""
        geometries = batch.geometry.array
        return [process_func(geom, *args, **kwargs) for geom in geometries]
    
    def process_step1(self, feature_a=None, feature_b=None, return_gdf=False, progress_offset=0):
        """执行步骤1：要素转换与裁剪
        
        Args:
            feature_a: 上图图斑GeoDataFrame（可选，批量执行时使用）
            feature_b: 数据库底图GeoDataFrame（可选，批量执行时使用）
            return_gdf: 是否返回GeoDataFrame而不是保存文件
            progress_offset: 进度偏移量（可选，批量执行时使用，用于累积进度）
            
        Returns:
            如果return_gdf=True，返回(clipped_gdf, output_dir)；否则返回结果字符串
        """
        try:
            # 获取参数
            buffer_distance = float(self.buffer_distance_lineedit.text())
            
            if feature_a is None or feature_b is None:
                # 单步执行：从文件读取数据
                feature_a_path = self.feature_a_lineedit.text()
                feature_b_path = self.feature_b_lineedit.text()
                
                # 获取图层名称
                feature_a_layer = self.feature_a_layer_combo.currentText() if feature_a_path.lower().endswith('.gdb') else ""
                feature_b_layer = self.feature_b_layer_combo.currentText() if feature_b_path.lower().endswith('.gdb') else ""
                
                # 基于上图图斑文件路径构建输出路径
                output_dir = os.path.dirname(feature_a_path)
                output_path = os.path.join(output_dir, "clipped_features.shp")
                
                self.update_progress_signal.emit(5, f"读取上图图斑: {feature_a_path}")
                if feature_a_path.lower().endswith('.gdb') and feature_a_layer:
                    feature_a = gpd.read_file(feature_a_path, layer=feature_a_layer)
                else:
                    feature_a = gpd.read_file(feature_a_path, driver='ESRI Shapefile')
                self.update_progress_signal.emit(10, f"上图图斑包含 {len(feature_a)} 个要素")
                
                self.update_progress_signal.emit(15, f"读取数据库底图: {feature_b_path}")
                if feature_b_path.lower().endswith('.gdb') and feature_b_layer:
                    feature_b = gpd.read_file(feature_b_path, layer=feature_b_layer)
                else:
                    feature_b = gpd.read_file(feature_b_path, driver='ESRI Shapefile')
                self.update_progress_signal.emit(20, f"数据库底图包含 {len(feature_b)} 个要素")
            else:
                # 批量执行：使用传入的GeoDataFrame
                feature_a_path = self.feature_a_lineedit.text()
                output_dir = os.path.dirname(feature_a_path)
            
            # 优化筛选流程：先使用边界框快速筛选，再使用精确缓冲区筛选
            self.update_progress_signal.emit(25, "筛选与上图图斑相关的数据库底图要素...")
            
            # 步骤1: 快速筛选 - 使用上图图斑的边界框进行初步筛选
            feature_a_bounds = feature_a.total_bounds
            minx, miny, maxx, maxy = feature_a_bounds
            expand_buffer = buffer_distance * 2
            minx -= expand_buffer
            miny -= expand_buffer
            maxx += expand_buffer
            maxy += expand_buffer
            
            # 快速筛选：只保留边界框内的要素
            feature_b_quick = feature_b.cx[minx:maxx, miny:maxy]
            
            # 步骤2: 精确筛选 - 仅对快速筛选后的结果使用精确的缓冲区相交检查
            feature_b_filtered = feature_b_quick
            if len(feature_b_quick) > 0:
                # 创建上图图斑的包围盒多边形
                feature_a_box = box(*feature_a_bounds)
                feature_a_buffer = feature_a_box.buffer(expand_buffer)
                feature_b_filtered = feature_b_quick[feature_b_quick.intersects(feature_a_buffer)]
            
            # 如果筛选后没有要素，使用原始数据
            if len(feature_b_filtered) == 0:
                feature_b_filtered = feature_b
            else:
                feature_b = feature_b_filtered
            
            self.update_progress_signal.emit(35, "将上图图斑转换为线要素...")
            lines_a = self.convert_to_lines(feature_a)
            
            # 将数据库底图转换为线要素
            self.update_progress_signal.emit(45, "将数据库底图转换为线要素...")
            lines_b = self.convert_to_lines(feature_b)
            
            # 合并数据库底图的线要素
            self.update_progress_signal.emit(55, "合并数据库底图的线要素...")
            merged_b = unary_union(lines_b.geometry)
            
            self.update_progress_signal.emit(65, f"对数据库底图线要素外扩 {buffer_distance} 单位...")
            buffered_b = merged_b.buffer(buffer_distance)
            
            # 裁剪上图图斑的线要素
            self.update_progress_signal.emit(70, "开始裁剪上图图斑的线要素...")
            total_geoms = len(lines_a)
            self.total_count = total_geoms
            self.processed_count = 0
            
            # 定义裁剪函数
            def clip_geom(geom):
                clipped_geom = geom.difference(buffered_b)
                with self.progress_lock:
                    self.processed_count += 1
                return clipped_geom
            
            # 将GeoDataFrame分割为批次
            batches = self.split_gdf_into_batches(lines_a)
            clipped_geoms = []
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_threads) as executor:
                futures = []
                for batch in batches:
                    future = executor.submit(self.process_batch, batch, clip_geom)
                    futures.append(future)
                
                for i, future in enumerate(concurrent.futures.as_completed(futures)):
                    batch_results = future.result()
                    for result in batch_results:
                        if not result.is_empty:
                            clipped_geoms.append(result)
                    
                    progress = 70 + (self.processed_count / total_geoms) * 20  # 70%到90%之间
                    self.update_progress_signal.emit(progress, f"正在裁剪第 {self.processed_count}/{total_geoms} 个要素")
            
            # 合并裁剪后的线要素
            self.update_progress_signal.emit(90, "合并连续的线要素...")
            
            # 高级合并逻辑：合并端点连续的线条
            def merge_contiguous_lines(lines):
                """合并端点连续的线条"""
                if not lines:
                    return []
                    
                # 将所有线条转换为LineString对象
                line_list = []
                for line in lines:
                    if isinstance(line, LineString):
                        line_list.append(line)
                    elif isinstance(line, MultiLineString):
                        line_list.extend(line.geoms)
                
                if not line_list:
                    return []
                
                # 创建一个线条字典，用于存储线条及其端点
                from shapely.geometry import Point
                line_dict = {}
                endpoints = {}
                
                # 为每条线分配一个唯一ID，并记录其端点
                for i, line in enumerate(line_list):
                    coords = list(line.coords)
                    start = Point(coords[0])
                    end = Point(coords[-1])
                    
                    line_dict[i] = {
                        'line': line,
                        'start': start,
                        'end': end,
                        'coords': coords
                    }
                    
                    # 记录端点连接的线条
                    start_key = tuple(round(coord, 6) for coord in coords[0])
                    end_key = tuple(round(coord, 6) for coord in coords[-1])
                    
                    if start_key not in endpoints:
                        endpoints[start_key] = []
                    endpoints[start_key].append((i, 'start'))
                    
                    if end_key not in endpoints:
                        endpoints[end_key] = []
                    endpoints[end_key].append((i, 'end'))
                
                # 合并连续的线条
                merged_lines = []
                used = set()
                
                for i in line_dict:
                    if i in used:
                        continue
                    
                    current_line = line_dict[i]
                    current_coords = current_line['coords'].copy()
                    used.add(i)
                    
                    # 向前扩展（从终点开始寻找连接的线条）
                    extended = True
                    while extended:
                        extended = False
                        # 获取当前终点
                        current_end = tuple(round(coord, 6) for coord in current_coords[-1])
                        
                        # 查找连接到当前终点的线条
                        if current_end in endpoints:
                            for line_id, end_type in endpoints[current_end]:
                                if line_id in used:
                                    continue
                                
                                next_line = line_dict[line_id]
                                next_coords = next_line['coords'].copy()
                                
                                # 检查连接方式
                                if end_type == 'start':
                                    # 直接连接
                                    current_coords.pop()  # 移除重复的端点
                                    current_coords.extend(next_coords)
                                elif end_type == 'end':
                                    # 需要反转线条方向
                                    next_coords.reverse()
                                    current_coords.pop()  # 移除重复的端点
                                    current_coords.extend(next_coords)
                                
                                used.add(line_id)
                                extended = True
                                break
                    
                    # 向后扩展（从起点开始寻找连接的线条）
                    extended = True
                    while extended:
                        extended = False
                        # 获取当前起点
                        current_start = tuple(round(coord, 6) for coord in current_coords[0])
                        
                        # 查找连接到当前起点的线条
                        if current_start in endpoints:
                            for line_id, end_type in endpoints[current_start]:
                                if line_id in used:
                                    continue
                                
                                prev_line = line_dict[line_id]
                                prev_coords = prev_line['coords'].copy()
                                
                                # 检查连接方式
                                if end_type == 'end':
                                    # 直接连接
                                    prev_coords.pop()  # 移除重复的端点
                                    current_coords = prev_coords + current_coords
                                elif end_type == 'start':
                                    # 需要反转线条方向
                                    prev_coords.reverse()
                                    prev_coords.pop()  # 移除重复的端点
                                    current_coords = prev_coords + current_coords
                                
                                used.add(line_id)
                                extended = True
                                break
                    
                    # 添加合并后的线条
                    merged_lines.append(LineString(current_coords))
                
                # 如果没有合并任何线条，返回原始线条
                if not merged_lines:
                    return line_list
                
                return merged_lines
            
            # 首先使用unary_union合并重叠的线条
            initial_merge = unary_union(clipped_geoms)
            
            # 提取线条列表
            initial_lines = []
            if isinstance(initial_merge, LineString):
                initial_lines = [initial_merge]
            elif isinstance(initial_merge, MultiLineString):
                initial_lines = list(initial_merge.geoms)
            
            # 使用高级合并逻辑合并端点连续的线条
            final_geoms = merge_contiguous_lines(initial_lines)
            
            # 最后再次使用unary_union确保完全合并
            if final_geoms:
                final_merge = unary_union(final_geoms)
                if isinstance(final_merge, LineString):
                    final_geoms = [final_merge]
                elif isinstance(final_merge, MultiLineString):
                    final_geoms = list(final_merge.geoms)
            
            clipped_inverse = gpd.GeoDataFrame(geometry=final_geoms, crs=lines_a.crs)
            
            if return_gdf:
                # 批量执行：返回GeoDataFrame
                return clipped_inverse, output_dir
            else:
                # 单步执行：保存到文件
                output_type = self.output_type_combo.currentText()
                output_dir = self.output_shp_dir.text() if output_type == "SHP文件" else self.output_gdb_path.text()
                
                if output_type == "SHP文件":
                    output_path = os.path.join(output_dir, "clipped_features.shp")
                    self.update_progress_signal.emit(95, f"保存结果到: {output_path}")
                    # 确保crs信息被正确写入PRJ文件
                    if clipped_inverse.crs is None:
                        # 如果crs为空，尝试从原始数据获取
                        if hasattr(lines_a, 'crs') and lines_a.crs is not None:
                            clipped_inverse.crs = lines_a.crs
                    # 不再向to_file方法传递crs参数，pyogrio引擎会自动使用GeoDataFrame的crs属性
                    clipped_inverse.to_file(output_path, driver='ESRI Shapefile', index=False)
                    return f"步骤1执行完成！\n生成文件: {output_path}"
                else:
                    # 保存到GDB
                    layer_prefix = self.output_gdb_layer_prefix.text()
                    # 替换图层名称中的空格为下划线，确保GDB图层名称有效
                    layer_prefix = layer_prefix.replace(" ", "_")
                    layer_name = f"{layer_prefix}_clipped_features"
                    self.update_progress_signal.emit(95, f"保存结果到GDB图层: {layer_name}")
                    
                    # 处理数据：移除OBJECTID字段（GDB自动生成）
                    gdf_to_save = clipped_inverse.copy()
                    if 'OBJECTID' in gdf_to_save.columns:
                        gdf_to_save = gdf_to_save.drop(columns=['OBJECTID'])
                    
                    # 使用fiona引擎保存
                    gdf_to_save.to_file(output_dir, layer=layer_name, driver='OpenFileGDB', index=False, engine='fiona')
                    return f"步骤1执行完成！\n生成GDB图层: {layer_name}"
        except Exception as e:
            import traceback
            return f"步骤1执行出错: {str(e)}\n\n详细错误信息: {traceback.format_exc()}"
    
    def extend_line(self, line, extend_dist, boundary=None):
        """延长线的两端超出边界指定距离"""
        if line.geom_type == 'MultiLineString':
            extended_lines = []
            for single_line in line.geoms:
                extended = self.extend_line(single_line, extend_dist, boundary)
                extended_lines.append(extended)
            return MultiLineString(extended_lines)
        
        coords = list(line.coords)
        if len(coords) < 2:
            return line
        
        # 检查线条是否闭合
        def is_closed(line_coords, tolerance=1e-6):
            """检查线条是否闭合"""
            if len(line_coords) < 3:
                return False
            # 比较起点和终点坐标，考虑浮点数精度
            start_x, start_y = line_coords[0]
            end_x, end_y = line_coords[-1]
            return abs(start_x - end_x) < tolerance and abs(start_y - end_y) < tolerance
        
        # 计算起点方向向量
        start = Point(coords[0])
        second = Point(coords[1])
        dx_start = start.x - second.x
        dy_start = start.y - second.y
        length_start = ((dx_start ** 2) + (dy_start ** 2)) ** 0.5
        if length_start == 0:
            ux_start = 1
            uy_start = 0
        else:
            ux_start = dx_start / length_start
            uy_start = dy_start / length_start
        
        # 计算终点方向向量
        penultimate = Point(coords[-2])
        end = Point(coords[-1])
        dx_end = end.x - penultimate.x
        dy_end = end.y - penultimate.y
        length_end = ((dx_end ** 2) + (dy_end ** 2)) ** 0.5
        if length_end == 0:
            ux_end = 1
            uy_end = 0
        else:
            ux_end = dx_end / length_end
            uy_end = dy_end / length_end
        
        # 检查线条是否闭合
        closed = is_closed(coords)
        
        # 如果提供了边界，先延长到边界，再延长指定距离
        if boundary is not None and not closed:
            # 处理起点延长
            # 创建足够长的延长线，确保能与边界相交
            # 使用一个非常大的距离来确保延长线与边界相交
            long_extend_dist = 1000000  # 足够大的距离，确保能与边界相交
            
            # 起点方向：创建足够长的延长线
            start_extend_line = LineString([
                start,
                Point(start.x + ux_start * long_extend_dist,
                      start.y + uy_start * long_extend_dist)
            ])
            
            # 终点方向：创建足够长的延长线
            end_extend_line = LineString([
                end,
                Point(end.x + ux_end * long_extend_dist,
                      end.y + uy_end * long_extend_dist)
            ])
            
            # 找到延长线与边界的交点
            start_intersection = start_extend_line.intersection(boundary)
            end_intersection = end_extend_line.intersection(boundary)
            
            # 计算最终的延长点
            # 处理起点延长
            if start_intersection.is_empty:
                # 没有交点，直接延长指定距离
                final_start_extend = extend_dist
            else:
                # 有交点，计算交点到起点的距离
                if hasattr(start_intersection, 'geoms'):
                    # MultiPoint情况，取最近的交点
                    min_dist = float('inf')
                    closest_point = None
                    for p in start_intersection.geoms:
                        dist = start.distance(p)
                        if dist < min_dist:
                            min_dist = dist
                            closest_point = p
                    intersection_dist = min_dist
                else:
                    # Point情况
                    intersection_dist = start.distance(start_intersection)
                # 最终延长距离 = 交点到端点的距离 + 指定延长阈值
                final_start_extend = intersection_dist + extend_dist
            
            # 处理终点延长
            if end_intersection.is_empty:
                # 没有交点，直接延长指定距离
                final_end_extend = extend_dist
            else:
                # 有交点，计算交点到终点的距离
                if hasattr(end_intersection, 'geoms'):
                    # MultiPoint情况，取最近的交点
                    min_dist = float('inf')
                    closest_point = None
                    for p in end_intersection.geoms:
                        dist = end.distance(p)
                        if dist < min_dist:
                            min_dist = dist
                            closest_point = p
                    intersection_dist = min_dist
                else:
                    # Point情况
                    intersection_dist = end.distance(end_intersection)
                # 最终延长距离 = 交点到端点的距离 + 指定延长阈值
                final_end_extend = intersection_dist + extend_dist
        else:
            # 闭合线条或没有边界，直接延长指定距离
            final_start_extend = extend_dist
            final_end_extend = extend_dist
        
        # 计算最终的延长点
        extended_start = Point(
            start.x + ux_start * final_start_extend,
            start.y + uy_start * final_start_extend
        )
        
        extended_end = Point(
            end.x + ux_end * final_end_extend,
            end.y + uy_end * final_end_extend
        )
        
        # 构建新的线
        new_coords = [extended_start.coords[0]] + coords + [extended_end.coords[0]]
        return LineString(new_coords)
    
    def process_step2(self, clipped_gdf=None, feature_b=None, output_dir=None, return_gdf=False, progress_offset=0):
        """执行步骤2：延长线要素
        
        Args:
            clipped_gdf: 裁剪后的线要素GeoDataFrame（可选，批量执行时使用）
            feature_b: 数据库底图GeoDataFrame（可选，批量执行时使用）
            output_dir: 输出目录（可选，批量执行时使用）
            return_gdf: 是否返回GeoDataFrame而不是保存文件
            progress_offset: 进度偏移量（可选，批量执行时使用，用于累积进度）
            
        Returns:
            如果return_gdf=True，返回(extended_gdf, output_dir)；否则返回结果字符串
        """
        try:
            # 获取参数
            extend_distance = float(self.extend_distance_lineedit.text())
            
            if clipped_gdf is None or feature_b is None or output_dir is None:
                # 单步执行：从文件读取数据
                feature_a_path = self.feature_a_lineedit.text()
                output_dir = os.path.dirname(feature_a_path)
                clipped_features_path = os.path.join(output_dir, "clipped_features.shp")
                feature_b_path = self.feature_b_lineedit.text()
                
                # 获取图层名称
                feature_b_layer = self.feature_b_layer_combo.currentText() if feature_b_path.lower().endswith('.gdb') else ""
                
                output_path = os.path.join(output_dir, "extended_features.shp")
                
                self.update_progress_signal.emit(progress_offset + 10, f"读取裁剪后的线要素: {clipped_features_path}")
                clipped_gdf = gpd.read_file(clipped_features_path, driver='ESRI Shapefile')
                
                self.update_progress_signal.emit(progress_offset + 20, f"读取数据库底图: {feature_b_path}")
                if feature_b_path.lower().endswith('.gdb') and feature_b_layer:
                    feature_b = gpd.read_file(feature_b_path, layer=feature_b_layer)
                else:
                    feature_b = gpd.read_file(feature_b_path, driver='ESRI Shapefile')
            else:
                # 批量执行：使用传入的GeoDataFrame
                self.update_progress_signal.emit(progress_offset + 5, "使用内存中的裁剪后线要素数据...")
                self.update_progress_signal.emit(progress_offset + 10, "使用内存中的数据库底图数据...")
            
            # 计算裁剪后线要素的缓冲区，用于筛选相关的数据库底图要素
            self.update_progress_signal.emit(progress_offset + 15, "计算裁剪后线要素的缓冲区...")
            clipped_bounds = clipped_gdf.total_bounds
            clipped_box = box(*clipped_bounds)
            expand_buffer = extend_distance * 2
            clipped_buffer = clipped_box.buffer(expand_buffer)
            
            # 筛选与裁剪后线要素缓冲区相交的数据库底图要素
            feature_b_filtered = feature_b[feature_b.intersects(clipped_buffer)]
            if len(feature_b_filtered) == 0:
                feature_b_filtered = feature_b
            else:
                feature_b = feature_b_filtered
            
            # 将数据库底图转换为线要素
            self.update_progress_signal.emit(progress_offset + 25, "将数据库底图转换为线要素...")
            lines_b = self.convert_to_lines(feature_b)
            
            # 合并数据库底图的线要素
            self.update_progress_signal.emit(progress_offset + 35, "合并数据库底图的线要素...")
            merged_b = unary_union(lines_b.geometry)
            
            self.update_progress_signal.emit(progress_offset + 45, "创建数据库底图的边界缓冲区...")
            boundary = merged_b.buffer(0.001)
            
            # 延长线要素
            self.update_progress_signal.emit(progress_offset + 50, f"开始延长线要素两端超出边界 {extend_distance} 米...")
            total_geoms = len(clipped_gdf)
            self.total_count = total_geoms
            self.processed_count = 0
            
            # 定义延长线函数
            def extend_single_line(geom):
                extended_geom = self.extend_line(geom, extend_distance, boundary)
                with self.progress_lock:
                    self.processed_count += 1
                return extended_geom
            
            # 将GeoDataFrame分割为批次
            batches = self.split_gdf_into_batches(clipped_gdf)
            extended_geoms = []
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_threads) as executor:
                futures = []
                for batch in batches:
                    future = executor.submit(self.process_batch, batch, extend_single_line)
                    futures.append(future)
                
                for i, future in enumerate(concurrent.futures.as_completed(futures)):
                    batch_results = future.result()
                    extended_geoms.extend(batch_results)
                    
                    progress = progress_offset + 50 + (self.processed_count / total_geoms) * 25  # 50%到75%之间
                    self.update_progress_signal.emit(progress, f"正在延长第 {self.processed_count}/{total_geoms} 个要素")
            
            extended_gdf = gpd.GeoDataFrame(geometry=extended_geoms, crs=clipped_gdf.crs)
            
            if return_gdf:
                # 批量执行：返回GeoDataFrame
                return extended_gdf, output_dir
            else:
                # 单步执行：保存到文件
                output_type = self.output_type_combo.currentText()
                output_dir = self.output_shp_dir.text() if output_type == "SHP文件" else self.output_gdb_path.text()
                
                if output_type == "SHP文件":
                    output_path = os.path.join(output_dir, "extended_features.shp")
                    self.update_progress_signal.emit(progress_offset + 80, f"保存结果到: {output_path}")
                    # 确保crs信息被正确写入PRJ文件
                    if extended_gdf.crs is None:
                        # 如果crs为空，尝试从原始数据获取
                        if hasattr(clipped_gdf, 'crs') and clipped_gdf.crs is not None:
                            extended_gdf.crs = clipped_gdf.crs
                    # 不再向to_file方法传递crs参数，pyogrio引擎会自动使用GeoDataFrame的crs属性
                    extended_gdf.to_file(output_path, driver='ESRI Shapefile', index=False)
                    return f"步骤2执行完成！\n生成文件: {output_path}"
                else:
                    # 保存到GDB
                    layer_prefix = self.output_gdb_layer_prefix.text()
                    # 替换图层名称中的空格为下划线，确保GDB图层名称有效
                    layer_prefix = layer_prefix.replace(" ", "_")
                    layer_name = f"{layer_prefix}_extended_features"
                    self.update_progress_signal.emit(progress_offset + 80, f"保存结果到GDB图层: {layer_name}")
                    
                    # 处理数据：移除OBJECTID字段（GDB自动生成）
                    gdf_to_save = extended_gdf.copy()
                    if 'OBJECTID' in gdf_to_save.columns:
                        gdf_to_save = gdf_to_save.drop(columns=['OBJECTID'])
                    
                    # 使用fiona引擎保存
                    gdf_to_save.to_file(output_dir, layer=layer_name, driver='OpenFileGDB', index=False, engine='fiona')
                    return f"步骤2执行完成！\n生成GDB图层: {layer_name}"
        except Exception as e:
            import traceback
            return f"步骤2执行出错: {str(e)}\n\n详细错误信息: {traceback.format_exc()}"
    
    def show_detailed_help(self):
        """显示详细功能说明"""
        from qfluentwidgets import MessageBox
        
        detailed_help = (
            "<b>功能说明：</b><br>"
            "执行变更上图的迭代处理模式，包括以下步骤：<br>"
            "1. 要素转换与裁剪：将上图图斑转换为线要素，裁剪数据库底图的线要素<br>"
            "2. 延长线要素：延长线要素两端超出数据库底图边界<br>"
            "3. 分割数据库底图：使用延长后的线要素分割数据库底图<br>"
            "4. 要素去重叠：对分割结果执行去重叠处理，移除重叠区域并保留边界<br>"
            "5. 空间挂接字段：<br>"
            "   - 第一次挂接：去重叠结果挂接上图图斑<br>"
            "   - 第二次挂接：第一次挂接结果挂接数据库底图<br>"

            "<br>"
            "<b>参数说明：</b><br>"
            "- 外扩阈值：用于裁剪要素的缓冲区大小<br>"
            "- 延长距离：线要素延长的距离<br>"
            "- 重叠面积阈值：用于空间挂接的最小重叠面积，默认为10<br>"

            "<br>"
            "<b>输出设置：</b><br>"
            "- 支持SHP文件和GDB图层输出<br>"
        )
        
        msg_box = MessageBox("变更上图工具 - 详细说明", detailed_help, self)
        msg_box.exec()
    
    def is_closed_line(self, line):
        """检查线是否闭合"""
        if isinstance(line, LineString):
            coords = list(line.coords)
            if len(coords) >= 2:
                start = Point(coords[0])
                end = Point(coords[-1])
                return start.distance(end) < 0.0001
        return False

    def split_polygon_with_lines(self, polygon, lines):
        """使用线要素分割单个多边形要素"""
        from shapely.ops import polygonize
        from shapely.geometry import MultiPolygon
        
        result_polygons = []
        
        # 处理MultiPolygon类型
        if isinstance(polygon, MultiPolygon):
            # 遍历MultiPolygon中的每个Polygon
            for poly in polygon.geoms:
                # 递归调用split_polygon_with_lines函数处理每个Polygon
                poly_result = self.split_polygon_with_lines(poly, lines)
                result_polygons.extend(poly_result)
            return result_polygons
        
        # 处理单个Polygon类型
        try:
            # 1. 获取多边形边界（外边界+内洞）
            boundary_lines = [polygon.exterior] + list(polygon.interiors)
            
            # 2. 合并边界线条与分割线条
            merged_lines = boundary_lines + lines
            
            # 3. 构建线条网络并生成多边形
            line_network = unary_union(merged_lines)
            if isinstance(line_network, LineString) or isinstance(line_network, MultiLineString):
                polygons = list(polygonize([line_network]))
                
                # 4. 筛选原始多边形内部的结果
                for p in polygons:
                    if polygon.contains(p) or polygon.intersection(p).area > 0:
                        if p.is_valid and not p.is_empty:
                            result_polygons.append(p)
                
                if not result_polygons:
                    return [polygon]
                return result_polygons
            else:
                return [polygon]
        except Exception as e:
            return [polygon]
    
    def split_polygons_by_lines(self, polygon_gdf, line_gdf):
        """使用线要素分割多边形要素"""
        all_lines = []  # 普通线要素
        closed_polygons = []  # 由闭合线条转换的多边形
        
        for geom in line_gdf.geometry:
            if isinstance(geom, LineString):
                if self.is_closed_line(geom):
                    try:
                        closed_poly = Polygon(geom)
                        if closed_poly.is_valid:
                            closed_polygons.append(closed_poly)
                    except Exception as e:
                        all_lines.append(geom)
                else:
                    all_lines.append(geom)
            elif isinstance(geom, MultiLineString):
                for line in geom.geoms:
                    if self.is_closed_line(line):
                        try:
                            closed_poly = Polygon(line)
                            if closed_poly.is_valid:
                                closed_polygons.append(closed_poly)
                        except Exception as e:
                            all_lines.append(line)
                    else:
                        all_lines.append(line)
        
        # 优化：只处理与线要素相交的多边形
        line_bounds = line_gdf.total_bounds
        line_box = box(*line_bounds)
        polygon_gdf = polygon_gdf[polygon_gdf.intersects(line_box)]
        total_polygons = len(polygon_gdf)
        
        if total_polygons == 0:
            return polygon_gdf
        
        # 优化：提前合并所有普通线
        merged_lines = None
        if all_lines:
            merged_lines = unary_union(all_lines)
        
        result_polygons = []
        for polygon in polygon_gdf.geometry:
            current_polygons = [polygon]
            
            # 1. 先使用闭合多边形进行分割
            if closed_polygons:
                for closed_poly in closed_polygons:
                    if not polygon.intersects(closed_poly):
                        continue
                    
                    new_polygons = []
                    for current_poly in current_polygons:
                        if current_poly.intersects(closed_poly):
                            try:
                                difference = current_poly.difference(closed_poly)
                                if not difference.is_empty:
                                    if isinstance(difference, Polygon):
                                        new_polygons.append(difference)
                                    elif isinstance(difference, MultiPolygon):
                                        new_polygons.extend(list(difference.geoms))
                            except Exception:
                                new_polygons.append(current_poly)
                        else:
                            new_polygons.append(current_poly)
                    current_polygons = new_polygons
            
            # 2. 再使用普通线进行分割
            if merged_lines:
                new_polygons = []
                for current_poly in current_polygons:
                    if current_poly.intersects(merged_lines):
                        split_result = self.split_polygon_with_lines(current_poly, [merged_lines])
                        new_polygons.extend(split_result)
                    else:
                        new_polygons.append(current_poly)
                current_polygons = new_polygons
            
            result_polygons.extend(current_polygons)
        
        return gpd.GeoDataFrame(geometry=result_polygons, crs=polygon_gdf.crs)
    
    def process_step3(self, feature_b=None, extended_gdf=None, output_dir=None, return_gdf=False, progress_offset=0):
        """执行步骤3：分割要素B
        
        Args:
            feature_b: 数据库底图GeoDataFrame（可选，批量执行时使用）
            extended_gdf: 延长后的线要素GeoDataFrame（可选，批量执行时使用）
            output_dir: 输出目录（可选，批量执行时使用）
            return_gdf: 是否返回GeoDataFrame而不是保存文件
            progress_offset: 进度偏移量（可选，批量执行时使用，用于累积进度）
            
        Returns:
            结果字符串
        """
        try:
            if feature_b is None or extended_gdf is None or output_dir is None:
                # 单步执行：从文件读取数据
                feature_b_path = self.feature_b_lineedit.text()
                feature_a_path = self.feature_a_lineedit.text()
                
                # 获取图层名称
                feature_b_layer = self.feature_b_layer_combo.currentText() if feature_b_path.lower().endswith('.gdb') else ""
                
                output_dir = os.path.dirname(feature_a_path)
                extended_features_path = os.path.join(output_dir, "extended_features.shp")
                output_path = os.path.join(output_dir, "split_features_b.shp")
                
                self.update_progress_signal.emit(progress_offset + 20, f"读取数据库底图: {feature_b_path}")
                if feature_b_path.lower().endswith('.gdb') and feature_b_layer:
                    feature_b = gpd.read_file(feature_b_path, layer=feature_b_layer)
                else:
                    feature_b = gpd.read_file(feature_b_path, driver='ESRI Shapefile')
                
                self.update_progress_signal.emit(progress_offset + 40, f"读取延长后的线要素: {extended_features_path}")
                extended_gdf = gpd.read_file(extended_features_path, driver='ESRI Shapefile')
            else:
                # 批量执行：使用传入的GeoDataFrame
                output_path = os.path.join(output_dir, "split_features_b.shp")
                self.update_progress_signal.emit(progress_offset + 5, "使用内存中的数据库底图数据...")
                self.update_progress_signal.emit(progress_offset + 10, "使用内存中的延长后线要素数据...")
            
            self.update_progress_signal.emit(progress_offset + 20, "开始分割多边形...")
            split_result = self.split_polygons_by_lines(feature_b, extended_gdf)
            
            # 检查并处理几何类型
            if len(split_result) > 0:
                # 过滤掉无效的几何
                split_result = split_result[split_result.is_valid]
                
                # 确保只包含多边形类型
                valid_types = ['Polygon', 'MultiPolygon']
                split_result = split_result[split_result.geom_type.isin(valid_types)]
                
                # 如果结果为空，返回提示
                if len(split_result) == 0:
                    return f"步骤3执行完成！\n没有生成有效的分割结果。"
                
                # 尝试将所有几何转换为Polygon类型
                # 对于MultiPolygon，尝试分解为单个Polygon
                def convert_to_polygon(geom):
                    from shapely.geometry import Polygon, MultiPolygon
                    if isinstance(geom, MultiPolygon):
                        # 返回第一个有效多边形
                        for poly in geom.geoms:
                            if poly.is_valid:
                                return poly
                    return geom
                
                try:
                    split_result['geometry'] = split_result['geometry'].apply(convert_to_polygon)
                    # 再次过滤，确保都是Polygon类型
                    split_result = split_result[split_result.geom_type == 'Polygon']
                    
                    # 如果转换后结果为空，返回提示
                    if len(split_result) == 0:
                        return f"步骤3执行完成！\n几何类型转换失败，没有生成有效的结果。"
                except Exception as e:
                    print(f"几何类型转换警告: {str(e)}")
                    # 转换失败时，继续使用原始结果
                    pass
            
            output_type = self.output_type_combo.currentText()
            if output_type == "SHP文件":
                output_dir = self.output_shp_dir.text()
                output_path = os.path.join(output_dir, "split_features_b.shp")
                self.update_progress_signal.emit(progress_offset + 80, f"保存结果到: {output_path}")
                # 确保crs信息被正确写入PRJ文件
                if split_result.crs is None:
                    # 如果crs为空，尝试从原始数据获取
                    if hasattr(feature_b, 'crs') and feature_b.crs is not None:
                        split_result.crs = feature_b.crs
                # 不再向to_file方法传递crs参数，pyogrio引擎会自动使用GeoDataFrame的crs属性
                split_result.to_file(output_path, driver='ESRI Shapefile', index=False)
                return f"步骤3执行完成！\n生成文件: {output_path}"
            else:
                # 保存到GDB
                output_dir = self.output_gdb_path.text()
                layer_prefix = self.output_gdb_layer_prefix.text()
                # 替换图层名称中的空格为下划线，确保GDB图层名称有效
                layer_prefix = layer_prefix.replace(" ", "_")
                layer_name = f"{layer_prefix}_split_features_b"
                self.update_progress_signal.emit(progress_offset + 80, f"保存结果到GDB图层: {layer_name}")
                try:
                    # 显式定义schema，避免geometry type错误
                    import fiona
                    # 获取所有字段
                    columns = list(split_result.columns)
                    if 'geometry' in columns:
                        columns.remove('geometry')
                    
                    # 构建schema
                    schema = {
                        'geometry': 'Polygon',
                        'properties': {}
                    }
                    
                    # 添加所有非几何字段
                    for col in columns:
                        dtype = str(split_result[col].dtype)
                        if dtype in ['int64', 'int32', 'int16', 'int8']:
                            schema['properties'][col] = 'int'
                        elif dtype in ['float64', 'float32', 'float16']:
                            schema['properties'][col] = 'float'
                        elif dtype == 'bool':
                            schema['properties'][col] = 'bool'
                        else:
                            schema['properties'][col] = 'str'
                    
                    # 使用fiona显式schema保存
                    split_result.to_file(
                        output_dir, 
                        layer=layer_name, 
                        driver='OpenFileGDB', 
                        index=False,
                        schema=schema
                    )
                    return f"步骤3执行完成！\n生成GDB图层: {layer_name}"
                except Exception as e:
                    # 如果保存到GDB失败，尝试使用pyogrio直接写入
                    try:
                        import pyogrio
                        pyogrio.write_dataframe(
                            split_result, 
                            output_dir, 
                            layer=layer_name, 
                            driver='OpenFileGDB',
                            geometry_type='Polygon'
                        )
                        return f"处理完成!结果保存到:{output_dir}#{layer_name}"
                    except Exception as e2:
                        # 如果仍然失败，返回错误信息
                        return f"处理完成!结果保存失败: {str(e2)}"
        except Exception as e:
            import traceback
            return f"步骤3执行出错: {str(e)}\n\n详细错误信息: {traceback.format_exc()}"

    def execute_iterative_mode(self):
        """执行迭代处理模式：依次将上图图斑的要素转换成线条，然后延长距离并对数据库底图进行裁剪，生成单个最终结果"""
        # 1. 验证输入
        valid, message = self.validate()
        if not valid:
            self.showError(message)
            return
        
        # 2. 显示进度条
        self.progress_container.setVisible(True)
        self.updateProgress(0)
        
        # 3. 显示进度
        self.showProgress("正在执行迭代处理模式...")
        
        # 4. 在线程中执行处理
        def run_iterative_process():
            import time
            try:
                # 记录开始时间
                self.start_time = time.time()
                
                # 获取输入文件路径和图层
                feature_a_path = self.feature_a_lineedit.text()
                feature_b_path = self.feature_b_lineedit.text()
                
                # 获取图层名称
                feature_a_layer = self.feature_a_layer_combo.currentText() if feature_a_path.lower().endswith('.gdb') else ""
                feature_b_layer = self.feature_b_layer_combo.currentText() if feature_b_path.lower().endswith('.gdb') else ""
                
                # 获取输出设置
                output_type = self.output_type_combo.currentText()
                output_dir = self.output_shp_dir.text() if output_type == "SHP文件" else self.output_gdb_path.text()
                
                # 读取数据库底图（只需要读取一次）
                self.update_progress_signal.emit(10, f"读取数据库底图: {feature_b_path}")
                if feature_b_path.lower().endswith('.gdb') and feature_b_layer:
                    feature_b = gpd.read_file(feature_b_path, layer=feature_b_layer)
                else:
                    feature_b = gpd.read_file(feature_b_path, driver='ESRI Shapefile')
                
                # 读取上图图斑
                self.update_progress_signal.emit(20, f"读取上图图斑: {feature_a_path}")
                if feature_a_path.lower().endswith('.gdb') and feature_a_layer:
                    feature_a = gpd.read_file(feature_a_path, layer=feature_a_layer)
                else:
                    feature_a = gpd.read_file(feature_a_path, driver='ESRI Shapefile')
                
                total_features = len(feature_a)
                self.update_progress_signal.emit(30, f"开始处理 {total_features} 个图斑要素...")
                
                # 初始化空的GeoDataFrame，用于存储所有处理后的线要素
                all_extended_lines = None
                all_clipped_lines = None  # 存储所有延长前的线要素
                
                # 遍历每个上图图斑要素
                for i in range(total_features):
                    # 更新进度
                    progress = 30 + (i / total_features) * 50  # 30%到80%之间
                    self.update_progress_signal.emit(progress, f"正在处理第 {i+1}/{total_features} 个图斑要素")
                    
                    # 获取单个图斑要素
                    single_feature = feature_a.iloc[[i]]
                    
                    # 执行步骤1：要素转换与裁剪（返回GeoDataFrame）
                    try:
                        step1_result, _ = self.process_step1(single_feature, feature_b, return_gdf=True)
                    except Exception as e:
                        self.update_progress_signal.emit(progress, f"处理第 {i+1} 个图斑时步骤1出错: {str(e)}")
                        continue
                    
                    # 执行步骤2：延长线要素（返回GeoDataFrame）
                    try:
                        step2_result, _ = self.process_step2(step1_result, feature_b, output_dir, return_gdf=True)
                    except Exception as e:
                        self.update_progress_signal.emit(progress, f"处理第 {i+1} 个图斑时步骤2出错: {str(e)}")
                        continue
                    
                    # 合并所有延长前的线要素
                    if all_clipped_lines is None:
                        all_clipped_lines = step1_result
                    else:
                        import pandas as pd
                        all_clipped_lines = pd.concat([all_clipped_lines, step1_result], ignore_index=True)
                    
                    # 合并所有延长后的线要素
                    if all_extended_lines is None:
                        all_extended_lines = step2_result
                    else:
                        all_extended_lines = pd.concat([all_extended_lines, step2_result], ignore_index=True)
                
                # 使用所有延长后的线要素对数据库底图进行一次性分割
                if all_extended_lines is not None and len(all_extended_lines) > 0:
                    self.update_progress_signal.emit(85, "正在使用所有延长线对数据库底图进行分割...")
                    
                    # 如果勾选了生成中间数据，保存中间结果
                    if self.generate_intermediate_checkbox.isChecked():
                        # 保存延长前的线要素
                        if all_clipped_lines is not None and len(all_clipped_lines) > 0:
                            if output_type == "SHP文件":
                                clipped_all_output_path = os.path.join(output_dir, "clipped_all_lines.shp")
                                all_clipped_lines.to_file(clipped_all_output_path, driver='ESRI Shapefile', index=False)
                            else:
                                layer_prefix = self.output_gdb_layer_prefix.text() if self.output_gdb_layer_prefix.text() else "processed"
                                # 替换图层名称中的空格为下划线，确保GDB图层名称有效
                                layer_prefix = layer_prefix.replace(" ", "_")
                                layer_name = f"{layer_prefix}_clipped_all_lines"
                                
                                # 处理数据：移除OBJECTID字段（GDB自动生成）
                                gdf_to_save = all_clipped_lines.copy()
                                if 'OBJECTID' in gdf_to_save.columns:
                                    gdf_to_save = gdf_to_save.drop(columns=['OBJECTID'])
                                
                                # 使用fiona引擎保存
                                gdf_to_save.to_file(output_dir, layer=layer_name, driver='OpenFileGDB', index=False, engine='fiona')
                        
                        # 保存所有延长后的线要素
                        if output_type == "SHP文件":
                            extended_all_output_path = os.path.join(output_dir, "extended_all_lines.shp")
                            all_extended_lines.to_file(extended_all_output_path, driver='ESRI Shapefile', index=False)
                        else:
                            layer_prefix = self.output_gdb_layer_prefix.text() if self.output_gdb_layer_prefix.text() else "processed"
                            # 替换图层名称中的空格为下划线，确保GDB图层名称有效
                            layer_prefix = layer_prefix.replace(" ", "_")
                            layer_name = f"{layer_prefix}_extended_all_lines"
                            
                            # 处理数据：移除OBJECTID字段（GDB自动生成）
                            gdf_to_save = all_extended_lines.copy()
                            if 'OBJECTID' in gdf_to_save.columns:
                                gdf_to_save = gdf_to_save.drop(columns=['OBJECTID'])
                            
                            # 使用fiona引擎保存
                            gdf_to_save.to_file(output_dir, layer=layer_name, driver='OpenFileGDB', index=False, engine='fiona')
                    
                    # 使用分割函数处理
                    split_result = self.split_polygons_by_lines(feature_b, all_extended_lines)
                    
                    if len(split_result) > 0:
                        # 过滤掉无效的几何
                        split_result = split_result[split_result.is_valid]
                        
                        # 确保只包含多边形类型
                        valid_types = ['Polygon', 'MultiPolygon']
                        split_result = split_result[split_result.geom_type.isin(valid_types)]
                        
                        # 如果结果不为空，保存到文件
                    if len(split_result) > 0:
                        # 直接使用分割结果作为最终结果，不执行要素去重叠处理
                        final_result = split_result.copy()
                        
                        # 直接使用最终结果，不执行空间挂接操作
                        joined_result = final_result.copy()
                        
                        # 用上图图斑选择数据库底图，用最终输出的结果擦除选择的底图，然后合并这两部分进行输出
                        self.update_progress_signal.emit(88, "正在执行边界一致图斑处理...")
                        
                        # 1. 获取与上图图斑相交的数据库底图要素
                        self.update_progress_signal.emit(89, "正在选择与上图图斑相交的数据库底图要素...")
                        # 确保坐标系一致
                        if feature_a.crs != feature_b.crs:
                            feature_a_for_select = feature_a.to_crs(feature_b.crs)
                        else:
                            feature_a_for_select = feature_a.copy()
                        
                        # 选择与上图图斑相交的数据库底图要素
                        selected_basemap = feature_b[feature_b.intersects(feature_a_for_select.unary_union)]
                        
                        # 2. 用最终输出结果擦除选择的底图
                        self.update_progress_signal.emit(90, "正在用最终输出结果擦除选择的底图...")
                        # 确保坐标系一致
                        if joined_result.crs != feature_b.crs:
                            joined_result_projected = joined_result.to_crs(feature_b.crs)
                            selected_basemap_projected = selected_basemap
                        else:
                            joined_result_projected = joined_result
                            selected_basemap_projected = selected_basemap
                        
                        # 计算擦除后的底图：selected_basemap - joined_result
                        def erase_geom(geom):
                            try:
                                # 计算当前底图要素与所有最终结果的差集
                                difference = geom
                                for result_geom in joined_result_projected.geometry:
                                    if difference.intersects(result_geom):
                                        difference = difference.difference(result_geom)
                                        if difference.is_empty:
                                            break
                                return difference
                            except Exception:
                                return geom
                        
                        # 应用擦除操作
                        erased_basemap = selected_basemap_projected.copy()
                        erased_basemap['geometry'] = erased_basemap['geometry'].apply(erase_geom)
                        
                        # 过滤掉无效的几何
                        erased_basemap = erased_basemap[~erased_basemap['geometry'].is_empty]
                        erased_basemap = erased_basemap[erased_basemap['geometry'].is_valid]
                        
                        # 3. 合并擦除后的底图和最终输出结果
                        self.update_progress_signal.emit(91, "正在合并处理结果...")
                        # 确保坐标系一致
                        if erased_basemap.crs != joined_result.crs:
                            erased_basemap = erased_basemap.to_crs(joined_result.crs)
                        
                        # 合并两个结果
                        final_merged_result = gpd.GeoDataFrame(
                            pd.concat([joined_result, erased_basemap], ignore_index=True),
                            crs=joined_result.crs
                        )
                        
                        # 清理无效几何和非多边形几何
                        final_merged_result = final_merged_result[final_merged_result['geometry'].is_valid]
                        final_merged_result = final_merged_result[~final_merged_result['geometry'].is_empty]
                        # 确保只包含Polygon和MultiPolygon类型
                        valid_types = ['Polygon', 'MultiPolygon']
                        final_merged_result = final_merged_result[final_merged_result['geometry'].geom_type.isin(valid_types)]
                        # 对于MultiPolygon，转换为单个Polygon
                        def convert_to_polygon(geom):
                            from shapely.geometry import Polygon, MultiPolygon
                            if isinstance(geom, MultiPolygon):
                                # 返回第一个有效多边形
                                for poly in geom.geoms:
                                    if poly.is_valid and poly.area > 1e-8:
                                        return poly
                                return None
                            return geom
                        
                        # 应用转换
                        final_merged_result['geometry'] = final_merged_result['geometry'].apply(convert_to_polygon)
                        # 过滤掉转换后为None的几何
                        final_merged_result = final_merged_result[final_merged_result['geometry'].notnull()]
                        # 再次过滤，确保都是Polygon类型
                        final_merged_result = final_merged_result[final_merged_result['geometry'].geom_type == 'Polygon']
                        
                        # 1. 执行要素去重叠处理
                        self.update_progress_signal.emit(85, "正在执行要素去重叠处理...")
                        # 计算所有要素的并集
                        all_polygons = unary_union(final_merged_result.geometry)
                        # 提取所有要素的边界
                        all_boundaries = unary_union([geom.boundary for geom in final_merged_result.geometry])
                        # 使用边界线分割所有多边形
                        split_polygons = list(polygonize(all_boundaries))
                        # 移除可能产生的无效多边形（面积为0或非常小的）
                        split_polygons = [poly for poly in split_polygons if poly.area > 1e-8]
                        # 将分割后的多边形转换为GeoDataFrame
                        no_overlap_result = gpd.GeoDataFrame(
                            {'id': range(len(split_polygons))}, 
                            geometry=split_polygons, 
                            crs=final_merged_result.crs
                        )
                        
                        # 2. 执行第一次空间挂接：去重叠结果挂接上图图斑
                        self.update_progress_signal.emit(86, "正在执行第一次空间挂接：去重叠结果挂接上图图斑...")
                        # 获取重叠面积阈值
                        threshold = self.threshold_spinbox.value()
                        
                        # 确保坐标系一致
                        if feature_a.crs != no_overlap_result.crs:
                            feature_a_projected = feature_a.to_crs(no_overlap_result.crs)
                        else:
                            feature_a_projected = feature_a.copy()
                        
                        # 步骤1: 先执行相交连接，获取所有可能的匹配对（以去重叠结果为主体）
                        joined_gdf = gpd.sjoin(no_overlap_result, feature_a_projected, how="left", predicate="intersects")
                        
                        # 步骤2: 计算每对匹配要素的重叠面积
                        overlap_areas = []
                        for idx, row in joined_gdf.iterrows():
                            # 获取去重叠结果的几何体
                            a_geom = row['geometry']
                            # 获取对应的上图图斑的几何体（如果存在）
                            if not pd.isna(row['index_right']):
                                b_idx = int(row['index_right'])
                                b_geom = feature_a_projected.iloc[b_idx]['geometry']
                                # 计算重叠面积
                                overlap_area = a_geom.intersection(b_geom).area
                            else:
                                overlap_area = 0
                            overlap_areas.append(overlap_area)
                        
                        # 添加重叠面积列
                        joined_gdf = joined_gdf.copy()
                        joined_gdf.loc[:, 'overlap_area'] = overlap_areas
                        
                        # 步骤3: 根据重叠面积阈值筛选匹配对
                        filtered_gdf = joined_gdf[joined_gdf['overlap_area'] >= threshold]
                        
                        # 步骤4: 处理原始去重叠结果，确保所有要素都被保留
                        # 获取匹配成功的去重叠结果的索引
                        matched_indices = set(filtered_gdf.index)
                        # 分离匹配成功和未匹配成功的要素
                        matched_result = filtered_gdf.copy()
                        unmatched_result = no_overlap_result[~no_overlap_result.index.isin(matched_indices)].copy()
                        # 将未匹配成功的要素转换为与matched_result相同的列结构
                        for col in matched_result.columns:
                            if col not in unmatched_result.columns and col != 'geometry':
                                unmatched_result.loc[:, col] = None
                        # 重新排列列顺序，确保一致
                        unmatched_result = unmatched_result[matched_result.columns].copy()
                        # 合并匹配和未匹配的要素（确保所有去重叠结果都被保留）
                        first_joined_result = gpd.GeoDataFrame(pd.concat([matched_result, unmatched_result], ignore_index=True), crs=no_overlap_result.crs)
                        # 移除overlap_area和index_right列，因为不需要保存到最终结果
                        first_joined_result = first_joined_result.drop(columns=['overlap_area', 'index_right'], errors='ignore')
                        
                        # 3. 执行第二次空间挂接：第一次挂接结果挂接数据库底图
                        self.update_progress_signal.emit(89, "正在执行第二次空间挂接：挂接数据库底图...")
                        
                        # 确保坐标系一致
                        if feature_b.crs != first_joined_result.crs:
                            feature_b_projected = feature_b.to_crs(first_joined_result.crs)
                        else:
                            feature_b_projected = feature_b.copy()
                        
                        # 步骤1: 先执行相交连接，获取所有可能的匹配对（以第一次挂接结果为主体）
                        second_joined_gdf = gpd.sjoin(first_joined_result, feature_b_projected, how="left", predicate="intersects")
                        
                        # 步骤2: 计算每对匹配要素的重叠面积
                        second_overlap_areas = []
                        for idx, row in second_joined_gdf.iterrows():
                            # 获取第一次挂接结果的几何体
                            a_geom = row['geometry']
                            # 获取对应的数据库底图的几何体（如果存在）
                            if not pd.isna(row['index_right']):
                                b_idx = int(row['index_right'])
                                b_geom = feature_b_projected.iloc[b_idx]['geometry']
                                # 计算重叠面积
                                overlap_area = a_geom.intersection(b_geom).area
                            else:
                                overlap_area = 0
                            second_overlap_areas.append(overlap_area)
                        
                        # 添加重叠面积列
                        second_joined_gdf = second_joined_gdf.copy()
                        second_joined_gdf.loc[:, 'overlap_area'] = second_overlap_areas
                        
                        # 步骤3: 根据重叠面积阈值筛选匹配对
                        second_filtered_gdf = second_joined_gdf[second_joined_gdf['overlap_area'] >= threshold]
                        
                        # 步骤4: 处理原始第一次挂接结果，确保所有要素都被保留
                        # 获取匹配成功的第一次挂接结果的索引
                        second_matched_indices = set(second_filtered_gdf.index)
                        # 分离匹配成功和未匹配成功的要素
                        second_matched_result = second_filtered_gdf.copy()
                        second_unmatched_result = first_joined_result[~first_joined_result.index.isin(second_matched_indices)].copy()
                        # 将未匹配成功的要素转换为与second_matched_result相同的列结构
                        for col in second_matched_result.columns:
                            if col not in second_unmatched_result.columns and col != 'geometry':
                                second_unmatched_result.loc[:, col] = None
                        # 重新排列列顺序，确保一致
                        second_unmatched_result = second_unmatched_result[second_matched_result.columns].copy()
                        # 合并匹配和未匹配的要素（确保所有第一次挂接结果都被保留）
                        spatial_joined_result = gpd.GeoDataFrame(pd.concat([second_matched_result, second_unmatched_result], ignore_index=True), crs=first_joined_result.crs)
                        # 移除overlap_area和index_right列，因为不需要保存到最终结果
                        spatial_joined_result = spatial_joined_result.drop(columns=['overlap_area', 'index_right'], errors='ignore')
                        
                        # 使用空间挂接后的结果作为最终结果
                        final_merged_result = spatial_joined_result
                        
                        self.update_progress_signal.emit(92, "正在保存最终处理结果...")
                        
                        if output_type == "SHP文件":
                            # 保存为单个SHP文件
                            output_path = os.path.join(output_dir, "processed_basemap.shp")
                            # 确保crs信息被正确写入PRJ文件
                            if final_merged_result.crs is None:
                                # 如果crs为空，尝试从原始数据获取
                                if hasattr(feature_b, 'crs') and feature_b.crs is not None:
                                    final_merged_result.crs = feature_b.crs
                            # 不再向to_file方法传递crs参数，pyogrio引擎会自动使用GeoDataFrame的crs属性
                            final_merged_result.to_file(output_path, driver='ESRI Shapefile', index=False)
                            result_msg = f"处理结果已保存到: {output_path}"
                        else:
                            # 保存为单个GDB图层
                            layer_prefix = self.output_gdb_layer_prefix.text() if self.output_gdb_layer_prefix.text() else "processed"
                            # 替换图层名称中的空格为下划线，确保GDB图层名称有效
                            layer_prefix = layer_prefix.replace(" ", "_")
                            layer_name = f"{layer_prefix}_basemap"
                            
                            save_success = False
                            save_error = ""
                            
                            try:
                                # 处理数据：移除OBJECTID字段（GDB自动生成）
                                gdf_to_save = final_merged_result.copy()
                                if 'OBJECTID' in gdf_to_save.columns:
                                    gdf_to_save = gdf_to_save.drop(columns=['OBJECTID'])
                                
                                # 1. 尝试使用fiona引擎保存，明确指定engine='fiona'
                                gdf_to_save.to_file(
                                    output_dir, 
                                    layer=layer_name, 
                                    driver='OpenFileGDB', 
                                    index=False,
                                    engine='fiona'
                                )
                                save_success = True
                            except Exception as e:
                                save_error = f"Fiona保存失败: {str(e)}"
                                
                                # 2. 尝试使用pyogrio引擎保存，不使用schema参数
                                try:
                                    import pyogrio
                                    # 处理数据：移除OBJECTID字段（GDB自动生成）
                                    gdf_to_save = final_merged_result.copy()
                                    if 'OBJECTID' in gdf_to_save.columns:
                                        gdf_to_save = gdf_to_save.drop(columns=['OBJECTID'])
                                    
                                    pyogrio.write_dataframe(
                                        gdf_to_save, 
                                        output_dir, 
                                        layer=layer_name, 
                                        driver='OpenFileGDB',
                                        geometry_type='Polygon'
                                    )
                                    save_success = True
                                except Exception as e2:
                                    save_error += f"; Pyogrio保存失败: {str(e2)}"
                            
                            if save_success:
                                # 按照用户期望的格式显示结果，使用#分隔GDB路径和图层名称
                                result_msg = f"处理结果已保存到GDB: {output_dir}#{layer_name}"
                            else:
                                result_msg = f"保存结果失败: {save_error}"
                    else:
                        result_msg = "没有生成有效的分割结果"
                else:
                    result_msg = "没有成功处理任何图斑要素"
                
                self.update_progress_signal.emit(100, "迭代处理模式执行完成！")
                
                # 记录结束时间
                self.end_time = time.time()
                execution_time = self.end_time - self.start_time
                
                # 格式化时长
                if execution_time < 60:
                    time_str = f"{execution_time:.2f}秒"
                elif execution_time < 3600:
                    minutes = int(execution_time // 60)
                    seconds = execution_time % 60
                    time_str = f"{minutes}分{seconds:.2f}秒"
                else:
                    hours = int(execution_time // 3600)
                    minutes = int((execution_time % 3600) // 60)
                    seconds = execution_time % 60
                    time_str = f"{hours}时{minutes}分{seconds:.2f}秒"
                
                # 发送成功信号，在主线程中显示成功消息
                self.show_success_signal.emit(f"迭代处理模式执行完成！\n{result_msg}\n共处理 {total_features} 个图斑要素\n\n执行时长: {time_str}")
                
                # 重置进度条
                self.reset_progress()
                
            except Exception as e:
                # 记录结束时间（如果有错误）
                self.end_time = time.time()
                
                # 捕获并发送错误信号，在主线程中显示错误消息
                import traceback
                error_msg = f"迭代处理模式执行失败: {str(e)}\n\n{traceback.format_exc()}"
                self.show_error_signal.emit(error_msg)
                
                # 重置进度条
                self.reset_progress()
        
        # 启动线程
        threading.Thread(target=run_iterative_process, daemon=True).start()
    
    def validate(self) -> tuple[bool, str]:
        """验证输入参数"""
        # 验证输入文件
        if not self.feature_a_lineedit.text():
            return False, "请选择上图图斑文件"
        
        if not self.feature_b_lineedit.text():
            return False, "请选择数据库底图文件"
        
        if not os.path.exists(self.feature_a_lineedit.text()):
            return False, "上图图斑文件不存在"
        
        if not os.path.exists(self.feature_b_lineedit.text()):
            return False, "数据库底图文件不存在"
        
        # 验证GDB输入的图层选择
        if self.feature_a_lineedit.text().lower().endswith('.gdb'):
            if not self.feature_a_layer_combo.currentText():
                return False, "请选择上图图斑的GDB图层"
        
        if self.feature_b_lineedit.text().lower().endswith('.gdb'):
            if not self.feature_b_layer_combo.currentText():
                return False, "请选择数据库底图的GDB图层"
        
        # 验证输出设置
        # 自动检测输入是否为GDB文件，如果是，默认输出到同一GDB
        feature_a_path = self.feature_a_lineedit.text()
        # 获取上图图斑输入名作为默认前缀
        default_prefix = os.path.splitext(os.path.basename(feature_a_path))[0]
        if feature_a_path.lower().endswith('.gdb'):
            # 如果输入是GDB文件，默认输出类型设为GDB图层
            self.output_type_combo.setCurrentText("GDB图层")
            # 默认输出到同一GDB
            self.output_gdb_path.setText(feature_a_path)
            # 默认图层前缀设为上图图斑输入名
            if not self.output_gdb_layer_prefix.text():
                self.output_gdb_layer_prefix.setText(default_prefix)
        
        output_type = self.output_type_combo.currentText()
        if output_type == "SHP文件":
            # 验证SHP输出目录
            if not self.output_shp_dir.text():
                # 如果未选择输出目录，使用默认目录
                default_dir = os.path.dirname(feature_a_path)
                self.output_shp_dir.setText(default_dir)
        else:
            # 验证GDB输出
            if not self.output_gdb_path.text():
                # 如果未选择GDB输出路径，使用默认GDB路径
                if feature_a_path.lower().endswith('.gdb'):
                    self.output_gdb_path.setText(feature_a_path)
                else:
                    return False, "请选择GDB输出路径"
            
            if not os.path.exists(self.output_gdb_path.text()):
                return False, "GDB输出文件不存在"
            
            if not self.output_gdb_path.text().lower().endswith('.gdb'):
                return False, "请选择有效的GDB文件"
            
            if not self.output_gdb_layer_prefix.text():
                self.output_gdb_layer_prefix.setText(default_prefix)
        
        # 验证参数
        try:
            float(self.buffer_distance_lineedit.text())
        except ValueError:
            return False, "外扩阈值必须是数字"
        
        try:
            float(self.extend_distance_lineedit.text())
        except ValueError:
            return False, "延长距离必须是数字"
        
        return True, ""