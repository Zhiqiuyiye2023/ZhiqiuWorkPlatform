# coding:utf-8
"""
修复尖锐角功能
"""

import os
import geopandas as gpd
import shapely
import fiona
from shapely.geometry import Polygon, MultiPolygon, LineString, Point
from shapely.validation import make_valid
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog, 
                            QListWidget, QListWidgetItem, QFrame, QMessageBox, QGroupBox, QSlider, QSizePolicy)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from qfluentwidgets import (PrimaryPushButton, PushButton, ToggleButton, SwitchButton, FluentIcon, InfoBar,
                            InfoBarPosition, LineEdit, ComboBox)
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction


class FixSharpAngleWorker(QThread):
    """修复尖锐角工作线程"""
    progress_updated = pyqtSignal(int)  # 进度条信号
    result_generated = pyqtSignal(dict)  # 结果生成信号
    error_occurred = pyqtSignal(str)  # 错误信号
    
    def __init__(self, main_vector_path, main_layer_name, angle_threshold=30, cut_length=1.0):
        super().__init__()
        self.main_vector_path = main_vector_path
        self.main_layer_name = main_layer_name
        self.angle_threshold = angle_threshold
        self.cut_length = cut_length
        
    def run(self):
        """执行修复尖锐角操作"""
        try:
            # 读取主矢量数据
            if self.main_layer_name:
                main_gdf = gpd.read_file(self.main_vector_path, layer=self.main_layer_name)
            else:
                main_gdf = gpd.read_file(self.main_vector_path)
            
            # 检测是否需要转换切割长度单位
            actual_cut_length = self.cut_length
            if main_gdf.crs and main_gdf.crs.is_geographic:
                # 如果是地理坐标系，将米转换为度数
                # 1度约等于111320米（赤道附近）
                actual_cut_length = self.cut_length / 111320
            
            # 创建结果GeoDataFrame列表，用于存储新生成的要素
            result_features = []
            
            # 存储修复的位置
            fixed_locations = []
            
            # 处理每个主矢量要素
            total_features = len(main_gdf)
            for idx, row in main_gdf.iterrows():
                # 更新进度
                progress = int((idx + 1) / total_features * 100)
                self.progress_updated.emit(progress)
                
                # 获取当前要素几何
                geometry = row.geometry
                
                # 确保几何有效且为多边形类型
                if not geometry.is_valid:
                    geometry = make_valid(geometry)
                    # 检查修复后的几何是否为多边形类型
                    if not hasattr(geometry, 'geom_type') or geometry.geom_type not in ['Polygon', 'MultiPolygon']:
                        continue
                    if not geometry.is_valid:
                        continue
                
                # 修复尖锐角，同时收集修复位置
                new_geometries, locations = self._fix_sharp_angle(geometry, actual_cut_length)
                if new_geometries:
                    # 为每个新生成的几何创建一个新要素
                    for geom in new_geometries:
                        # 复制原始要素的属性
                        new_row = row.copy()
                        new_row['geometry'] = geom
                        result_features.append(new_row)
                    # 添加修复位置
                    if locations:
                        fixed_locations.extend(locations) 
                else:
                    # 如果没有修复，保留原始要素
                    result_features.append(row.copy())
            
            # 创建结果GeoDataFrame
            result_gdf = gpd.GeoDataFrame(result_features, crs=main_gdf.crs)
            
            # 清理字段名，确保只包含ASCII字符且不超过10个字符
            def clean_field_names(gdf):
                import re
                cleaned_gdf = gdf.copy()
                new_columns = {}
                for col in cleaned_gdf.columns:
                    if col == 'geometry':
                        continue
                    # 移除中文字符，只保留ASCII字符
                    cleaned_col = re.sub(r'[^\x00-\x7F]+', '_', col)
                    # 替换特殊字符为下划线
                    cleaned_col = re.sub(r'[^a-zA-Z0-9_]', '_', cleaned_col)
                    # 限制长度为10个字符
                    cleaned_col = cleaned_col[:10]
                    new_columns[col] = cleaned_col
                return cleaned_gdf.rename(columns=new_columns)
            
            # 清理结果数据的字段名
            result_gdf = clean_field_names(result_gdf)
            
            # 创建输出目录
            output_dir = os.path.join(os.path.dirname(self.main_vector_path), "fixed_result")
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成输出文件名
            base_name = os.path.splitext(os.path.basename(self.main_vector_path))[0]
            output_path = os.path.join(output_dir, f"{base_name}_fixed.shp")
            
            # 保存结果，指定编码为UTF-8
            result_gdf.to_file(output_path, encoding='utf-8')
            
            # 保存修复位置矢量
            fixed_locations_path = None
            if fixed_locations:
                # 创建修复位置的GeoDataFrame
                from shapely.geometry import Point
                fixed_points = [Point(location) for location in fixed_locations]
                fixed_locations_gdf = gpd.GeoDataFrame(geometry=fixed_points, crs=main_gdf.crs)
                # 添加修复角度信息
                fixed_locations_gdf['fixed_angle_threshold'] = self.angle_threshold
                
                # 清理修复位置矢量的字段名
                fixed_locations_gdf = clean_field_names(fixed_locations_gdf)
                
                # 保存为SHP文件，指定编码为UTF-8
                fixed_locations_path = os.path.join(output_dir, f"{base_name}_fixed_locations.shp")
                fixed_locations_gdf.to_file(fixed_locations_path, encoding='utf-8')
            
            # 发送结果
            self.result_generated.emit({
                'output_path': output_path,
                'fixed_count': len(result_gdf),
                'fixed_locations_path': fixed_locations_path
            })
            
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def _fix_sharp_angle(self, geometry, cut_length):
        """修复尖锐角"""
        fixed_locations = []
        if isinstance(geometry, Polygon):
            new_geometries, locations = self._fix_polygon_sharp_angle(geometry, cut_length)
            if locations:
                fixed_locations.extend(locations)
            return new_geometries, fixed_locations
        elif isinstance(geometry, MultiPolygon):
            # 处理MultiPolygon中的每个Polygon
            all_new_geometries = []
            for poly in geometry.geoms:
                new_geometries, locations = self._fix_polygon_sharp_angle(poly, cut_length)
                if new_geometries:
                    all_new_geometries.extend(new_geometries)
                if locations:
                    fixed_locations.extend(locations)
            return all_new_geometries, fixed_locations
        # 只返回多边形类型的几何
        return [], fixed_locations
    
    def _fix_polygon_sharp_angle(self, polygon, cut_length):
        """修复多边形的尖锐角 - 切割等腰三角形，将一个要素变成两个要素"""
        import math
        
        # 获取多边形的外部边界坐标
        coords = list(polygon.exterior.coords)
        # 移除最后一个点，因为它与第一个点相同
        if len(coords) > 1 and coords[0] == coords[-1]:
            coords = coords[:-1]
        
        if len(coords) < 3:
            return [polygon], []
        
        new_geometries = []
        fixed_locations = []  # 存储修复位置
        
        # 检查每个顶点的内角
        for i in range(len(coords)):
            # 获取当前点及其前后点
            prev_point = coords[i-1] if i > 0 else coords[-1]
            curr_point = coords[i]
            next_point = coords[i+1] if i < len(coords)-1 else coords[0]
            
            # 计算向量
            vec1 = (prev_point[0] - curr_point[0], prev_point[1] - curr_point[1])
            vec2 = (next_point[0] - curr_point[0], next_point[1] - curr_point[1])
            
            # 计算向量的模长
            len1 = math.hypot(vec1[0], vec1[1])
            len2 = math.hypot(vec2[0], vec2[1])
            
            if len1 == 0 or len2 == 0:
                continue
            
            # 计算向量的点积
            dot_product = vec1[0] * vec2[0] + vec1[1] * vec2[1]
            
            # 计算夹角（弧度）
            cos_angle = dot_product / (len1 * len2)
            cos_angle = max(-1.0, min(1.0, cos_angle))
            angle = math.acos(cos_angle)
            
            # 检查是否为尖锐角（小于设定阈值）
            if angle < math.radians(self.angle_threshold):
                # 记录修复位置
                fixed_locations.append(curr_point)
                
                # 确保切割长度不超过边的长度
                actual_cut_length = min(cut_length, len1, len2)
                
                # 计算第一条边上的切割点（从curr_point向prev_point方向）
                # vec1是从curr_point指向prev_point，所以unit_vec1方向正确
                unit_vec1 = (vec1[0]/len1, vec1[1]/len1)
                cut_point1 = (
                    curr_point[0] + unit_vec1[0] * actual_cut_length,
                    curr_point[1] + unit_vec1[1] * actual_cut_length
                )
                
                # 计算第二条边上的切割点（从curr_point向next_point方向）
                # vec2是从curr_point指向next_point，所以unit_vec2方向正确
                unit_vec2 = (vec2[0]/len2, vec2[1]/len2)
                cut_point2 = (
                    curr_point[0] + unit_vec2[0] * actual_cut_length,
                    curr_point[1] + unit_vec2[1] * actual_cut_length
                )
                
                # 调试：输出实际切割长度和切割点
                # print(f"设定切割长度: {self.cut_length}, 实际切割长度: {actual_cut_length}")
                # print(f"切割点1: {cut_point1}, 切割点2: {cut_point2}")
                
                # 创建裁剪线（连接两个切割点）
                clip_line = LineString([cut_point1, cut_point2])
                
                # 创建原始多边形的边界线
                original_boundary = LineString(coords + [coords[0]])
                
                # 创建两个新多边形：
                # 1. 主多边形（移除尖锐角后的多边形）
                # 2. 裁剪出的三角形（尖锐角部分）
                
                # 构建主多边形坐标
                main_polygon_coords = []
                # 添加从起点到prev_point的所有坐标
                for j in range(i):
                    main_polygon_coords.append(coords[j])
                # 添加第一条边上的切割点
                main_polygon_coords.append(cut_point1)
                # 添加第二条边上的切割点
                main_polygon_coords.append(cut_point2)
                # 添加从next_point到终点的所有坐标
                for j in range(i+1, len(coords)):
                    main_polygon_coords.append(coords[j])
                # 闭合多边形
                main_polygon_coords.append(main_polygon_coords[0])
                
                # 构建三角形坐标
                triangle_coords = [cut_point1, curr_point, cut_point2, cut_point1]
                
                # 创建多边形对象
                main_polygon = Polygon(main_polygon_coords)
                triangle_polygon = Polygon(triangle_coords)
                
                # 确保多边形有效并只保留Polygon类型
                valid_geometries = []
                
                # 处理主多边形
                if main_polygon.is_valid:
                    valid_geometries.append(main_polygon)
                else:
                    fixed_main = make_valid(main_polygon)
                    if isinstance(fixed_main, Polygon):
                        valid_geometries.append(fixed_main)
                    elif hasattr(fixed_main, 'geom_type') and fixed_main.geom_type == 'Polygon':
                        valid_geometries.append(fixed_main)
                    elif hasattr(fixed_main, 'geoms'):  # 处理MultiPolygon或GeometryCollection情况
                        for g in fixed_main.geoms:
                            if hasattr(g, 'geom_type') and g.geom_type == 'Polygon':
                                valid_geometries.append(g)
                
                # 处理三角形多边形
                if triangle_polygon.is_valid:
                    valid_geometries.append(triangle_polygon)
                else:
                    fixed_triangle = make_valid(triangle_polygon)
                    if isinstance(fixed_triangle, Polygon):
                        valid_geometries.append(fixed_triangle)
                    elif hasattr(fixed_triangle, 'geom_type') and fixed_triangle.geom_type == 'Polygon':
                        valid_geometries.append(fixed_triangle)
                    elif hasattr(fixed_triangle, 'geoms'):  # 处理MultiPolygon或GeometryCollection情况
                        for g in fixed_triangle.geoms:
                            if hasattr(g, 'geom_type') and g.geom_type == 'Polygon':
                                valid_geometries.append(g)
                
                # 添加到结果列表
                new_geometries.extend(valid_geometries)
                
                # 只处理第一个尖锐角，避免复杂情况
                break
        
        if not new_geometries:
            # 如果没有修复，返回原始多边形
            return [polygon], fixed_locations
        
        return new_geometries, fixed_locations


class FixSharpAngleFunction(BaseFunction):
    """修复尖锐角功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>" 
            "修复矢量要素中的尖锐角<br>" 
            "- 主矢量：需要修复尖锐角的矢量数据<br>" 
            "- 角度阈值：小于该角度的角将被修复<br>" 
            "- 切割长度：从夹角起点的左右两条边切割的长度<br>" 
            "修复结果将生成新的矢量文件，一个尖锐角要素将被分割为两个要素"
        )
        super().__init__("修复尖锐角", description, parent)
        
        self.main_vector_path = ""
        self.main_layer_name = ""
        self.angle_threshold = 30  # 默认30度
        self.cut_length = 1.0  # 默认切割长度为1.0
        self.worker = None
        
        self._initUI()
    
    def _initUI(self):
        """初始化界面"""
        # 创建主矢量选择区域
        main_vector_group = QGroupBox("主矢量数据", self)
        main_vector_layout = QVBoxLayout(main_vector_group)
        
        # 主矢量文件选择
        main_file_layout = QHBoxLayout()
        main_file_label = QLabel("主矢量文件：")
        self.main_file_path = LineEdit(self)
        self.main_file_path.setPlaceholderText("选择需要修复尖锐角的矢量文件")
        self.main_file_path.setReadOnly(True)
        
        # 分别添加SHP和GDB文件选择按钮
        self.main_shp_btn = PushButton("选择SHP", self, FIF.FOLDER)
        self.main_shp_btn.clicked.connect(lambda: self._select_main_file(shp_only=True))
        self.main_shp_btn.setFixedWidth(120)
        
        self.main_gdb_btn = PushButton("选择GDB", self, FIF.FOLDER)
        self.main_gdb_btn.clicked.connect(lambda: self._select_main_file(gdb_only=True))
        self.main_gdb_btn.setFixedWidth(120)
        
        main_file_layout.addWidget(main_file_label)
        main_file_layout.addWidget(self.main_file_path, 1)
        main_file_layout.addWidget(self.main_shp_btn)
        main_file_layout.addWidget(self.main_gdb_btn)
        main_vector_layout.addLayout(main_file_layout)
        
        # 主矢量图层选择（仅GDB文件显示）
        main_layer_layout = QHBoxLayout()
        main_layer_label = QLabel("图层名称：")
        self.main_layer_combo = ComboBox(self)
        self.main_layer_combo.setPlaceholderText("请先选择文件")
        self.main_layer_combo.setEnabled(False)
        
        main_layer_layout.addWidget(main_layer_label)
        main_layer_layout.addWidget(self.main_layer_combo, 1)
        main_vector_layout.addLayout(main_layer_layout)
        
        # 修复参数设置
        params_group = QGroupBox("修复参数设置", self)
        params_layout = QVBoxLayout(params_group)
        
        # 角度阈值设置
        threshold_slider_layout = QHBoxLayout()
        threshold_label = QLabel("修复角度阈值：")
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        # 设置滑块范围（5-60度）
        self.threshold_slider.setMinimum(5)
        self.threshold_slider.setMaximum(60)
        self.threshold_slider.setValue(self.angle_threshold)
        # 设置滑块样式
        self.threshold_slider.setTickInterval(5)
        self.threshold_slider.setSingleStep(1)
        self.threshold_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        # 设置滑块大小策略
        self.threshold_slider.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        self.threshold_value = QLabel(f"{self.angle_threshold}°")
        # 设置标签样式
        self.threshold_value.setStyleSheet("QLabel { font-weight: bold; }")
        
        threshold_slider_layout.addWidget(threshold_label)
        threshold_slider_layout.addWidget(self.threshold_slider, 1)
        threshold_slider_layout.addWidget(self.threshold_value, 0, Qt.AlignmentFlag.AlignLeft)
        
        params_layout.addLayout(threshold_slider_layout)
        
        # 切割长度设置
        cut_length_layout = QHBoxLayout()
        cut_length_label = QLabel("切割长度：")
        self.cut_length_edit = LineEdit(self)
        self.cut_length_edit.setPlaceholderText("输入切割长度")
        self.cut_length_edit.setText(str(self.cut_length))
        # 设置输入验证，只允许输入数字
        from PyQt6.QtGui import QDoubleValidator
        validator = QDoubleValidator(0.1, 100.0, 2)
        self.cut_length_edit.setValidator(validator)
        
        cut_length_layout.addWidget(cut_length_label)
        cut_length_layout.addWidget(self.cut_length_edit, 1)
        
        params_layout.addLayout(cut_length_layout)
        
        # 连接信号
        self.threshold_slider.valueChanged.connect(self._on_threshold_changed)
        self.cut_length_edit.textChanged.connect(self._on_cut_length_changed)
        
        # 进度条容器
        self.progress_container = QWidget(self)
        self.progress_layout = QVBoxLayout(self.progress_container)
        self.progress_layout.setContentsMargins(0, 0, 0, 0)
        self.progress_layout.setSpacing(5)
        
        # 进度文本
        self.progress_text = QLabel("准备开始修复...", self)
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
        
        # 添加执行按钮
        self.execute_btn = PrimaryPushButton("开始修复", self, FIF.SEND)
        self.execute_btn.clicked.connect(self._execute_fix)
        self.execute_btn.setFixedHeight(36)
        self.execute_btn.setFixedWidth(150)
        
        # 将所有组件添加到内容布局
        self.contentLayout.addWidget(main_vector_group)
        self.contentLayout.addWidget(params_group)
        self.contentLayout.addSpacing(20)
        self.contentLayout.addWidget(self.progress_container)
        self.contentLayout.addSpacing(20)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self.execute_btn)
        self.contentLayout.addLayout(button_layout)
    
    def _select_main_file(self, shp_only=False, gdb_only=False):
        """选择主矢量文件"""
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
        else:
            # 选择所有矢量文件
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择主矢量文件", ".", "矢量文件 (*.shp *.geojson *.json *.gpkg);;所有文件 (*)"
            )
        
        if file_path:
            # 验证GDB文件
            if gdb_only and not file_path.endswith('.gdb'):
                InfoBar.warning(
                    title="警告",
                    content="请选择GDB文件",
                    parent=self,
                    position=InfoBarPosition.TOP_RIGHT
                )
                return
            
            self.main_vector_path = file_path
            self.main_file_path.setText(file_path)
            
            # 更新图层列表
            self._update_main_layer_list(file_path)
    
    def _update_main_layer_list(self, file_path):
        """更新主矢量图层列表"""
        self.main_layer_combo.clear()
        self.main_layer_combo.setEnabled(False)
        
        if file_path.lower().endswith('.gdb'):
            # 列出GDB中的所有图层
            try:
                with fiona.Env():
                    layers = fiona.listlayers(file_path)
                self.main_layer_combo.addItems(layers)
                self.main_layer_combo.setEnabled(True)
                self.main_layer_name = layers[0] if layers else ""
            except Exception as e:
                InfoBar.error(
                    title="错误",
                    content=f"无法读取GDB文件: {str(e)}",
                    parent=self,
                    position=InfoBarPosition.TOP_RIGHT
                )
        else:
            # SHP文件不需要图层选择
            self.main_layer_combo.setPlaceholderText("SHP文件无需选择图层")
            self.main_layer_name = ""
    

    
    def _execute_fix(self):
        """执行修复操作"""
        # 验证输入
        if not self.main_vector_path:
            InfoBar.warning(
                title="警告",
                content="请选择主矢量文件",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT
            )
            return
        
        # 更新图层名称
        if self.main_layer_combo.isEnabled():
            self.main_layer_name = self.main_layer_combo.currentText()
        
        # 禁用执行按钮
        self.execute_btn.setEnabled(False)
        
        # 显示进度容器
        self.progress_container.setVisible(True)
        self.progress_text.setText("准备开始修复...")
        
        # 创建并启动工作线程
        self.worker = FixSharpAngleWorker(
            self.main_vector_path,
            self.main_layer_name,
            self.angle_threshold,
            self.cut_length
        )
        
        self.worker.progress_updated.connect(self._update_progress)
        self.worker.result_generated.connect(self._on_result_generated)
        self.worker.error_occurred.connect(self._on_error)
        
        self.worker.start()
    
    def _update_progress(self, progress):
        """更新进度条和进度文本"""
        # 更新进度文本，显示百分比
        self.progress_text.setText(f"正在修复... {progress}%")
        
        # 使用字符串拼接方式，避免花括号冲突
        progress_ratio = progress / 100.0
        style = """
            QFrame {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #0078D4, stop:""" + str(progress_ratio) + """ #0078D4, 
                    stop:""" + str(progress_ratio) + """ #e0e0e0, stop:1 #e0e0e0);
                border-radius: 2px;
            }
        """
        self.progress_bar.setStyleSheet(style)
    
    def _on_result_generated(self, result):
        """处理结果生成"""
        # 重置进度容器
        self.progress_container.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QFrame {
                background-color: #e0e0e0;
                border-radius: 2px;
            }
        """)
        self.progress_text.setText("准备开始修复...")
        
        # 启用执行按钮
        self.execute_btn.setEnabled(True)
        
        # 显示成功信息
        content = f"尖锐角修复成功！结果已保存到：{result['output_path']}"
        if 'fixed_locations_path' in result and result['fixed_locations_path']:
            content += f"\n修复位置矢量已保存到：{result['fixed_locations_path']}"
        InfoBar.success(
            title="修复完成",
            content=content,
            parent=self,
            position=InfoBarPosition.TOP_RIGHT
        )
    
    def _on_error(self, error_msg):
        """处理错误"""
        # 重置进度容器
        self.progress_container.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QFrame {
                background-color: #e0e0e0;
                border-radius: 2px;
            }
        """)
        self.progress_text.setText("准备开始修复...")
        
        # 启用执行按钮
        self.execute_btn.setEnabled(True)
        
        # 显示错误信息
        InfoBar.error(
            title="修复失败",
            content=f"修复过程中发生错误：{error_msg}",
            parent=self,
            position=InfoBarPosition.TOP_RIGHT
        )
    
    def _on_threshold_changed(self, value):
        """角度阈值滑块值变化处理"""
        self.angle_threshold = value
        self.threshold_value.setText(f"{value}°")
    
    def _on_cut_length_changed(self, text):
        """切割长度输入变化处理"""
        try:
            self.cut_length = float(text)
        except ValueError:
            # 如果输入无效，使用默认值
            self.cut_length = 1.0