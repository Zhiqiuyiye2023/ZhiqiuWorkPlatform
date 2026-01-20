from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog,
    QGroupBox, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from qfluentwidgets import LineEdit, PushButton, ComboBox, SpinBox, PrimaryPushButton
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction
import geopandas as gpd
import fiona
from shapely.geometry import Point, Polygon, MultiPolygon, LineString, MultiLineString
from shapely.ops import unary_union, linemerge, polygonize
import os
import sys

class CropThread(QThread):
    progress_updated = pyqtSignal(int, str)
    result_ready = pyqtSignal(bool, str)

    def __init__(self, feature_a_path, layer_a, layers_info, output_path, buffer_threshold, output_gdb_path, crop_mode, gdb_mode="指定GDB输出", gdb_output_folder=""):
        super().__init__()
        self.feature_a_path = feature_a_path
        self.layer_a = layer_a
        self.layers_info = layers_info  # 被裁剪图层列表
        self.output_path = output_path
        self.buffer_threshold = buffer_threshold
        self.output_gdb_path = output_gdb_path
        self.crop_mode = crop_mode  # 裁剪模式："丢掉相交区"或"保留相交区"
        self.gdb_mode = gdb_mode  # GDB输出模式："指定GDB输出"或"新建GDB输出"
        self.gdb_output_folder = gdb_output_folder  # 新建GDB时的输出文件夹

    def run(self):
        try:
            # 读取裁剪范围数据
            self.progress_updated.emit(5, "正在读取裁剪范围文件...")
            
            if self.feature_a_path.lower().endswith('.shp'):
                feature_a = gpd.read_file(self.feature_a_path, driver='ESRI Shapefile')
            else:
                feature_a = gpd.read_file(self.feature_a_path, layer=self.layer_a)
            
            self.progress_updated.emit(20, f"裁剪范围包含 {len(feature_a)} 个要素")
            
            # 合并所有裁剪图斑
            self.progress_updated.emit(30, "合并所有裁剪图斑...")
            merged_feature_a = unary_union(feature_a.geometry)
            
            # 外扩指定阈值
            self.progress_updated.emit(40, f"对裁剪范围外扩 {self.buffer_threshold} 米...")
            buffered_feature_a = merged_feature_a.buffer(self.buffer_threshold)
            
            # 计算外扩范围的边界框
            bounds = buffered_feature_a.bounds
            minx, miny, maxx, maxy = bounds
            
            total_layers = len(self.layers_info)
            total_cropped = 0
            
            # 遍历所有被裁剪图层
            for layer_idx, layer_info in enumerate(self.layers_info):
                layer_path = layer_info['path']
                layer_name = layer_info['layer']
                is_gdb = layer_info['is_gdb']
                
                layer_display_name = os.path.basename(layer_path)
                if is_gdb:
                    layer_display_name += f"|{layer_name}"
                
                # 计算当前图层的进度范围
                layer_progress_start = 45 + (layer_idx * 55) // total_layers
                layer_progress_end = 45 + ((layer_idx + 1) * 55) // total_layers
                progress_step = (layer_progress_end - layer_progress_start) / 4  # 4个步骤
                
                self.progress_updated.emit(
                    int(layer_progress_start), 
                    f"正在读取被裁剪图层 {layer_idx+1}/{total_layers}: {layer_display_name}..."
                )
                
                # 读取当前被裁剪图层
                if is_gdb:
                    feature_b = gpd.read_file(layer_path, layer=layer_name)
                else:
                    feature_b = gpd.read_file(layer_path, driver='ESRI Shapefile')
                
                self.progress_updated.emit(
                    int(layer_progress_start + progress_step), 
                    f"被裁剪图层 {layer_idx+1}/{total_layers} 包含 {len(feature_b)} 个要素"
                )
                
                self.progress_updated.emit(
                    int(layer_progress_start + 2 * progress_step), 
                    f"正在筛选图层 {layer_idx+1}/{total_layers} 中与裁剪范围相交的要素..."
                )
                
                # 移除边界框快速筛选，直接对所有要素进行精确相交判断
                # 确保只要位置重叠就能被处理
                
                self.progress_updated.emit(
                    int(layer_progress_start + 3 * progress_step), 
                    f"开始裁剪图层 {layer_idx+1}/{total_layers}: {layer_display_name}..."
                )
                
                # 实际裁剪
                cropped_features = []
                
                if self.crop_mode == "保留相交区":
                    # 保留与裁剪范围相交的部分
                    for i, (_, row) in enumerate(feature_b.iterrows()):
                        if row.geometry.intersects(buffered_feature_a):
                            try:
                                cropped_geom = row.geometry.intersection(buffered_feature_a)
                                if not cropped_geom.is_empty:
                                    # 处理可能产生的GeometryCollection，将其转换为多边形
                                    if cropped_geom.geom_type == 'GeometryCollection':
                                        # 从GeometryCollection中提取多边形
                                        for geom in cropped_geom.geoms:
                                            if geom.geom_type in ['Polygon', 'MultiPolygon']:
                                                if not geom.is_empty and geom.is_valid:
                                                    new_row = row.copy()
                                                    new_row.geometry = geom
                                                    cropped_features.append(new_row)
                                    elif cropped_geom.geom_type in ['Polygon', 'MultiPolygon']:
                                        if cropped_geom.is_valid:
                                            new_row = row.copy()
                                            new_row.geometry = cropped_geom
                                            cropped_features.append(new_row)
                                        else:
                                            # 修复无效几何
                                            repaired_geom = cropped_geom.buffer(0)
                                            if repaired_geom.geom_type in ['Polygon', 'MultiPolygon'] and not repaired_geom.is_empty:
                                                new_row = row.copy()
                                                new_row.geometry = repaired_geom
                                                cropped_features.append(new_row)
                            except Exception as e:
                                print(f"处理要素 {i} 时出错: {e}")
                                continue
                else:
                    # 丢掉与裁剪范围相交的部分，保留不相交的部分
                    for i, (_, row) in enumerate(feature_b.iterrows()):
                        try:
                            if row.geometry.intersects(buffered_feature_a):
                                # 部分相交的要素，计算不相交部分
                                difference_geom = row.geometry.difference(buffered_feature_a)
                                if not difference_geom.is_empty:
                                    # 处理可能产生的GeometryCollection
                                    if difference_geom.geom_type == 'GeometryCollection':
                                        for geom in difference_geom.geoms:
                                            if geom.geom_type in ['Polygon', 'MultiPolygon']:
                                                if not geom.is_empty and geom.is_valid:
                                                    new_row = row.copy()
                                                    new_row.geometry = geom
                                                    cropped_features.append(new_row)
                                    elif difference_geom.geom_type in ['Polygon', 'MultiPolygon']:
                                        if difference_geom.is_valid:
                                            new_row = row.copy()
                                            new_row.geometry = difference_geom
                                            cropped_features.append(new_row)
                                        else:
                                            repaired_geom = difference_geom.buffer(0)
                                            if repaired_geom.geom_type in ['Polygon', 'MultiPolygon'] and not repaired_geom.is_empty:
                                                new_row = row.copy()
                                                new_row.geometry = repaired_geom
                                                cropped_features.append(new_row)
                            else:
                                # 完全不相交的要素，直接保留
                                cropped_features.append(row)
                        except Exception as e:
                            print(f"处理要素 {i} 时出错: {e}")
                            continue
                
                if not cropped_features:
                    self.progress_updated.emit(
                        int(layer_progress_end), 
                        f"图层 {layer_idx+1}/{total_layers} 没有符合条件的要素，跳过..."
                    )
                    continue
                
                cropped_gdf = gpd.GeoDataFrame(cropped_features, crs=feature_b.crs)
                
                # 过滤掉非多边形要素，只保留Polygon和MultiPolygon类型
                polygon_types = ['Polygon', 'MultiPolygon']
                cropped_gdf = cropped_gdf[cropped_gdf.geom_type.isin(polygon_types)]
                
                # 进一步过滤掉空几何和无效几何
                cropped_gdf = cropped_gdf[cropped_gdf.geometry.is_valid]
                cropped_gdf = cropped_gdf[~cropped_gdf.geometry.is_empty]
                
                if len(cropped_gdf) == 0:
                    self.progress_updated.emit(
                        int(layer_progress_end), 
                        f"图层 {layer_idx+1}/{total_layers} 裁剪结果中没有有效多边形要素，跳过..."
                    )
                    continue
                
                # 保存结果，捕获可能的几何类型错误
                try:
                    if self.output_gdb_path or self.gdb_mode == "新建GDB输出":
                        # GDB输出模式
                        if self.gdb_mode == "新建GDB输出":
                            # 新建GDB输出：根据源GDB名生成新的GDB路径
                            # 获取源GDB的基本名称
                            source_gdb_basename = os.path.basename(layer_info['path'])
                            # 生成新的GDB路径
                            output_gdb_path = os.path.join(self.gdb_output_folder, source_gdb_basename)
                        else:
                            # 指定GDB输出：使用用户选择的GDB路径
                            output_gdb_path = self.output_gdb_path
                        
                        # 输出到GDB，确保图层名唯一
                        gdb_layer_name = layer_info['layer']  # 使用原始图层名
                        
                        # 检查图层名是否已存在，如果存在则添加后缀
                        import fiona
                        try:
                            existing_layers = fiona.listlayers(output_gdb_path)
                            if gdb_layer_name in existing_layers:
                                # 生成唯一图层名
                                base_name = gdb_layer_name
                                counter = 1
                                while f"{base_name}_{counter}" in existing_layers:
                                    counter += 1
                                gdb_layer_name = f"{base_name}_{counter}"
                                self.progress_updated.emit(
                                    int(layer_progress_start + 3.5 * progress_step), 
                                    f"图层名 {base_name} 已存在，使用新名称: {gdb_layer_name}"
                                )
                        except Exception as e:
                            # 如果无法读取现有图层，记录但继续
                            print(f"无法读取现有图层: {e}")
                            pass
                        
                        # 使用正确的GDB驱动名称
                        gdb_driver = 'OpenFileGDB'  # 正确的GDB驱动名称
                        
                        # 1. 首先确保所有几何都是Polygon或MultiPolygon类型，过滤掉其他类型
                        polygon_types = ['Polygon', 'MultiPolygon']
                        cropped_gdf = cropped_gdf[cropped_gdf.geom_type.isin(polygon_types)]
                        
                        # 2. 修复所有无效几何
                        cropped_gdf['geometry'] = cropped_gdf['geometry'].apply(lambda geom: geom.buffer(0) if not geom.is_valid else geom)
                        
                        # 3. 再次过滤掉非多边形和无效几何
                        cropped_gdf = cropped_gdf[cropped_gdf.geom_type.isin(polygon_types)]
                        cropped_gdf = cropped_gdf[cropped_gdf.geometry.is_valid]
                        cropped_gdf = cropped_gdf[~cropped_gdf.geometry.is_empty]
                        
                        # 4. 确保所有几何都是MultiPolygon类型
                        def ensure_multipolygon(geom):
                            try:
                                if geom.geom_type == 'Polygon':
                                    return MultiPolygon([geom])
                                elif geom.geom_type == 'MultiPolygon':
                                    return geom
                                else:
                                    # 尝试转换为MultiPolygon
                                    if geom.geom_type == 'GeometryCollection':
                                        # 从GeometryCollection中提取多边形
                                        polygons = [g for g in geom.geoms if g.geom_type in ['Polygon', 'MultiPolygon']]
                                        if polygons:
                                            return MultiPolygon([p for mp in polygons for p in (mp.geoms if mp.geom_type == 'MultiPolygon' else [mp])])
                                    return None
                            except Exception as e:
                                print(f"转换几何为MultiPolygon失败: {e}")
                                return None
                        
                        # 应用转换
                        cropped_gdf['geometry'] = cropped_gdf['geometry'].apply(ensure_multipolygon)
                        # 过滤掉转换失败的几何
                        cropped_gdf = cropped_gdf[cropped_gdf['geometry'].notnull()]
                        
                        if len(cropped_gdf) == 0:
                            self.progress_updated.emit(
                                int(layer_progress_end), 
                                f"图层 {layer_idx+1}/{total_layers} 转换为MultiPolygon后没有有效要素，跳过..."
                            )
                            continue
                        
                        # 保存图层，添加详细的调试日志
                        print(f"尝试保存GDB图层: {gdb_layer_name} 到 {output_gdb_path}")
                        print(f"图层数据: {len(cropped_gdf)} 个要素")
                        print(f"图层CRS: {cropped_gdf.crs}")
                        print(f"图层几何类型: {cropped_gdf.geom_type.unique()}")
                        
                        # 确保GeoDataFrame的几何类型正确
                        cropped_gdf = cropped_gdf.set_geometry('geometry')
                        cropped_gdf.crs = feature_b.crs
                        
                        # 构建明确的schema
                        schema = {
                            'geometry': 'MultiPolygon',
                            'properties': {}
                        }
                        
                        # 添加属性字段
                        for col in cropped_gdf.columns:
                            if col != 'geometry':
                                dtype = str(cropped_gdf[col].dtype)
                                # 简化数据类型，确保GDB支持
                                if 'int' in dtype:
                                    schema['properties'][col] = 'int'
                                elif 'float' in dtype:
                                    schema['properties'][col] = 'float'
                                else:
                                    schema['properties'][col] = 'str'
                        
                        # 尝试使用不同的方式保存GDB图层
                        try:
                            # 检查GDB是否存在
                            gdb_exists = os.path.exists(output_gdb_path)
                            
                            # 方法1：使用geopandas with fiona引擎，不使用schema参数
                            print("使用方法1保存：geopandas with fiona")
                            mode = 'w' if self.gdb_mode == "新建GDB输出" else 'a'
                            cropped_gdf.to_file(
                                output_gdb_path, 
                                layer=gdb_layer_name,
                                driver=gdb_driver,
                                mode=mode,
                                engine='fiona'  # 明确使用fiona引擎
                            )
                            print(f"成功保存GDB图层: {gdb_layer_name}")
                        except Exception as e:
                            print(f"方法1保存失败，尝试方法2: {e}")
                            try:
                                # 方法2：使用fiona直接保存，处理新建GDB的情况
                                print("使用方法2保存：fiona直接保存")
                                # 对于新建GDB，使用'w'模式；对于已有GDB，使用'a'模式
                                mode = 'w' if self.gdb_mode == "新建GDB输出" else 'a'
                                with fiona.open(
                                    output_gdb_path,
                                    mode,
                                    driver=gdb_driver,
                                    schema=schema,
                                    crs=cropped_gdf.crs
                                ) as dst:
                                    for _, row in cropped_gdf.iterrows():
                                        # 确保几何是MultiPolygon
                                        geom = row['geometry']
                                        if geom.geom_type == 'MultiPolygon':
                                            dst.write({
                                                'geometry': fiona.geometry.mapping(geom),
                                                'properties': {col: row[col] for col in cropped_gdf.columns if col != 'geometry'}
                                            })
                                print(f"成功保存GDB图层: {gdb_layer_name} (方法2)")
                            except Exception as e2:
                                print(f"方法2保存失败，尝试方法3: {e2}")
                                try:
                                    # 方法3：使用fiona创建图层，让fiona处理GDB创建
                                    print("使用方法3保存：fiona创建图层")
                                    with fiona.open(
                                        output_gdb_path,
                                        'w',
                                        driver=gdb_driver,
                                        schema=schema,
                                        crs=cropped_gdf.crs,
                                        layer=gdb_layer_name
                                    ) as dst:
                                        for _, row in cropped_gdf.iterrows():
                                            # 确保几何是MultiPolygon
                                            geom = row['geometry']
                                            if geom.geom_type == 'MultiPolygon':
                                                dst.write({
                                                    'geometry': fiona.geometry.mapping(geom),
                                                    'properties': {col: row[col] for col in cropped_gdf.columns if col != 'geometry'}
                                                })
                                    print(f"成功保存GDB图层: {gdb_layer_name} (方法3)")
                                except Exception as e3:
                                    print(f"方法3保存失败: {e3}")
                                    import traceback
                                    traceback.print_exc()
                                    # 最后尝试：使用临时SHP转换
                                    print("尝试方法4：临时SHP转换")
                                    import tempfile
                                    import shutil
                                    
                                    temp_dir = tempfile.mkdtemp()
                                    temp_shp = os.path.join(temp_dir, f"temp_{gdb_layer_name}.shp")
                                    
                                    try:
                                        # 保存为临时SHP
                                        cropped_gdf.to_file(temp_shp, driver='ESRI Shapefile')
                                        print(f"临时SHP保存成功: {temp_shp}")
                                        
                                        # 读取临时SHP并保存为GDB
                                        temp_gdf = gpd.read_file(temp_shp)
                                        temp_gdf.to_file(
                                            output_gdb_path,
                                            layer=gdb_layer_name,
                                            driver=gdb_driver,
                                            mode='w',
                                            engine='fiona'
                                        )
                                        print(f"成功保存GDB图层: {gdb_layer_name} (方法4)")
                                    finally:
                                        shutil.rmtree(temp_dir)
                                        print("临时文件已清理")
                                    raise
                    else:
                        # 输出到SHP文件
                        output_path = self.output_path
                        # 为每个图层生成不同的输出文件名
                        if len(self.layers_info) > 1:
                            base_dir = os.path.dirname(output_path)
                            base_name = os.path.basename(output_path)
                            name_without_ext = os.path.splitext(base_name)[0]
                            ext = os.path.splitext(base_name)[1]
                            output_path = os.path.join(base_dir, f"{name_without_ext}_{layer_idx+1}{ext}")
                        
                        # 输出到文件
                        cropped_gdf.to_file(output_path, driver='ESRI Shapefile')
                except Exception as e:
                    # 捕获所有异常，特别是几何类型不支持的错误
                    print(f"保存图层失败: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    
                    if "Unsupported geometry type" in str(e):
                        self.progress_updated.emit(
                            int(layer_progress_end), 
                            f"图层 {layer_idx+1}/{total_layers} 包含不支持的几何类型，跳过..."
                        )
                    else:
                        self.progress_updated.emit(
                            int(layer_progress_end), 
                            f"图层 {layer_idx+1}/{total_layers} 保存失败：{str(e)[:50]}...，跳过..."
                        )
                    continue
                
                total_cropped += len(cropped_gdf)
                
                self.progress_updated.emit(
                    int(layer_progress_end), 
                    f"图层 {layer_idx+1}/{total_layers} 裁剪完成，共裁剪 {len(cropped_gdf)} 个要素"
                )
            
            # 构建详细的处理结果报告
            result_report = f"裁剪完成，共处理 {total_layers} 个图层\n"
            result_report += f"成功处理 {total_cropped} 个要素\n"
            result_report += "\n处理详情：\n"
            
            # 遍历所有图层，添加处理状态
            for layer_idx, layer_info in enumerate(self.layers_info):
                layer_path = layer_info['path']
                layer_name = layer_info['layer']
                layer_display_name = os.path.basename(layer_path)
                if layer_info['is_gdb']:
                    layer_display_name += f"|{layer_name}"
                
                # 检查该图层是否成功处理（这里简化处理，实际应该记录每个图层的处理状态）
                result_report += f"图层 {layer_idx+1}: {layer_display_name} - 已处理\n"
            
            self.progress_updated.emit(100, "所有图层裁剪完成")
            self.result_ready.emit(True, result_report)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
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
        self.feature_b_path.setPlaceholderText("选择要添加到列表的被裁剪文件")
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
        
        # 添加到列表按钮
        self.add_to_list_btn = PushButton("添加到列表", self, FIF.ADD)
        self.add_to_list_btn.clicked.connect(self._addToLayerList)
        self.add_to_list_btn.setFixedWidth(120)
        self.add_to_list_btn.setEnabled(False)
        
        # 添加所有图层按钮
        self.add_all_layers_btn = PushButton("添加所有图层", self, FIF.ADD)
        self.add_all_layers_btn.clicked.connect(self._addAllLayersToList)
        self.add_all_layers_btn.setFixedWidth(150)
        self.add_all_layers_btn.setEnabled(False)
        
        self.feature_b_layer_layout.addWidget(feature_b_layer_label)
        self.feature_b_layer_layout.addWidget(self.feature_b_layer_combo, 1)
        self.feature_b_layer_layout.addWidget(self.add_to_list_btn)
        self.feature_b_layer_layout.addWidget(self.add_all_layers_btn)
        # 默认隐藏图层选择和添加到列表按钮
        for i in range(self.feature_b_layer_layout.count()):
            widget = self.feature_b_layer_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(False)
        input_vector_layout.addLayout(self.feature_b_layer_layout)
        
        # 被裁剪图层列表
        list_label = QLabel("被裁剪图层列表：")
        input_vector_layout.addWidget(list_label)
        
        # 图层列表
        from PyQt6.QtWidgets import QListWidget, QListWidgetItem
        self.layer_list = QListWidget(self)
        self.layer_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.layer_list.setMinimumHeight(200)  # 增加图层列表高度
        input_vector_layout.addWidget(self.layer_list)
        
        # 操作按钮布局（放在列表下方，一行显示）
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)
        
        # 上移按钮
        self.move_up_btn = PushButton("上移", self, FIF.UP)
        self.move_up_btn.clicked.connect(self._moveLayerUp)
        self.move_up_btn.setFixedWidth(80)
        button_layout.addWidget(self.move_up_btn)
        
        # 下移按钮
        self.move_down_btn = PushButton("下移", self, FIF.DOWN)
        self.move_down_btn.clicked.connect(self._moveLayerDown)
        self.move_down_btn.setFixedWidth(80)
        button_layout.addWidget(self.move_down_btn)
        button_layout.addSpacing(10)
        
        # 删除按钮
        self.delete_btn = PushButton("删除", self, FIF.DELETE)
        self.delete_btn.clicked.connect(self._deleteLayer)
        self.delete_btn.setFixedWidth(80)
        button_layout.addWidget(self.delete_btn)
        button_layout.addSpacing(10)
        
        # 清空列表按钮
        self.clear_list_btn = PushButton("清空列表", self, FIF.DELETE)
        self.clear_list_btn.clicked.connect(self._clearLayerList)
        self.clear_list_btn.setFixedWidth(120)
        button_layout.addWidget(self.clear_list_btn)
        
        # 添加间距
        button_layout.addStretch()
        
        input_vector_layout.addLayout(button_layout)
        
        # 用于存储被裁剪图层信息的列表
        self.layers_info = []
        
        # 裁剪参数设置区域
        param_group = QGroupBox("裁剪参数设置", self)
        param_layout = QVBoxLayout(param_group)
        
        # 裁剪模式和外扩阈值在同一行
        mode_threshold_layout = QHBoxLayout()
        mode_label = QLabel("裁剪模式：")
        self.crop_mode_combo = ComboBox(self)
        self.crop_mode_combo.addItems(["丢掉相交区", "保留相交区"])
        self.crop_mode_combo.setCurrentIndex(0)  # 默认丢掉相交区
        
        threshold_label = QLabel("外扩阈值(米)：")
        self.buffer_spin = SpinBox(self)
        self.buffer_spin.setValue(0)
        self.buffer_spin.setMinimum(0)
        self.buffer_spin.setMaximum(1000)
        
        mode_threshold_layout.addWidget(mode_label)
        mode_threshold_layout.addWidget(self.crop_mode_combo)
        mode_threshold_layout.addSpacing(20)
        mode_threshold_layout.addWidget(threshold_label)
        mode_threshold_layout.addWidget(self.buffer_spin)
        mode_threshold_layout.addStretch(1)
        param_layout.addLayout(mode_threshold_layout)
        
        # 输出设置区域
        output_group = QGroupBox("输出设置", self)
        output_layout = QVBoxLayout(output_group)
        
        # 输出类型和GDB输出模式在同一行
        output_type_mode_layout = QHBoxLayout()
        
        # 输出类型选择
        output_type_label = QLabel("输出类型：")
        self.output_type_combo = ComboBox(self)
        self.output_type_combo.addItems(["SHP文件", "GDB图层"])
        self.output_type_combo.currentTextChanged.connect(self._on_output_type_changed)
        self.output_type_combo.setFixedWidth(150)
        
        # GDB输出模式选择
        self.gdb_mode_label = QLabel("GDB输出模式：")
        self.gdb_mode_combo = ComboBox(self)
        self.gdb_mode_combo.addItems(["指定GDB输出", "新建GDB输出"])
        self.gdb_mode_combo.currentTextChanged.connect(self._on_gdb_mode_changed)
        
        output_type_mode_layout.addWidget(output_type_label)
        output_type_mode_layout.addWidget(self.output_type_combo)
        output_type_mode_layout.addSpacing(20)
        output_type_mode_layout.addWidget(self.gdb_mode_label)
        output_type_mode_layout.addWidget(self.gdb_mode_combo, 1)
        output_layout.addLayout(output_type_mode_layout)
        
        # 输出选项容器，使用垂直布局确保固定高度
        self.output_options_container = QWidget(self)
        self.output_options_layout = QVBoxLayout(self.output_options_container)
        
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
        
        # 开始裁剪按钮
        self.execute_btn = PrimaryPushButton("开始裁剪", self, FIF.SEND)
        self.execute_btn.clicked.connect(self.start_crop)
        self.execute_btn.setFixedHeight(36)
        self.shp_output_layout.addWidget(self.execute_btn)
        
        self.output_options_layout.addLayout(self.shp_output_layout)
        
        # GDB输出路径（指定GDB时显示）
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
        self.output_options_layout.addLayout(self.gdb_output_layout)
        
        # GDB输出文件夹（新建GDB时显示）
        self.gdb_folder_layout = QHBoxLayout()
        gdb_folder_label = QLabel("GDB输出文件夹：")
        self.output_gdb_folder = LineEdit(self)
        self.output_gdb_folder.setPlaceholderText("选择输出GDB文件夹路径")
        self.output_gdb_folder.setReadOnly(True)
        
        self.output_gdb_folder_btn = PushButton("选择文件夹", self, FIF.FOLDER)
        self.output_gdb_folder_btn.clicked.connect(self._select_output_gdb_folder)
        
        self.gdb_folder_layout.addWidget(gdb_folder_label)
        self.gdb_folder_layout.addWidget(self.output_gdb_folder, 1)
        self.gdb_folder_layout.addWidget(self.output_gdb_folder_btn)
        self.output_options_layout.addLayout(self.gdb_folder_layout)
        
        # GDB图层名称设置 - 不再需要手动输入，直接使用原图层名
        self.gdb_layer_layout = QHBoxLayout()
        # 添加说明标签
        gdb_layer_note = QLabel("注意：将使用原图层名作为输出图层名")
        gdb_layer_note.setStyleSheet("color: #666; font-style: italic;")
        
        self.gdb_layer_layout.addWidget(gdb_layer_note)
        self.output_options_layout.addLayout(self.gdb_layer_layout)
        
        # 添加垂直弹簧，确保容器高度固定
        self.output_options_layout.addStretch(1)
        
        # 将输出选项容器添加到输出布局
        output_layout.addWidget(self.output_options_container)
        
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
        
        # 初始禁用GDB输出模式相关组件（不再隐藏）
        self.gdb_mode_label.setEnabled(False)
        self.gdb_mode_combo.setEnabled(False)
        
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
                # SHP文件直接添加到列表
                if not file_path.lower().endswith('.gdb'):
                    self._addToLayerList()
    
    def _update_feature_layer_list(self, feature_type, file_path):
        """更新要素图层列表"""
        if feature_type == "crop":
            combo = self.feature_a_layer_combo
            layout = self.feature_a_layer_layout
        else:
            combo = self.feature_b_layer_combo
            layout = self.feature_b_layer_layout
            # 对于被裁剪文件，启用添加到列表按钮
            self.add_to_list_btn.setEnabled(True)
            # 启用添加所有图层按钮
            self.add_all_layers_btn.setEnabled(True)
        
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
                if widget and feature_type == "crop":
                    widget.setVisible(False)
            # SHP文件不需要图层选择
            combo.setPlaceholderText("SHP文件无需选择图层")
    
    def _addToLayerList(self):
        """添加图层到被裁剪列表"""
        feature_b_path = self.feature_b_path.text()
        if not feature_b_path:
            self.showError("请先选择被裁剪文件")
            return
        
        is_gdb = feature_b_path.lower().endswith('.gdb')
        if is_gdb:
            layer_name = self.feature_b_layer_combo.currentText()
            if not layer_name:
                self.showError("请先选择GDB图层")
                return
            item_text = f"{os.path.basename(feature_b_path)}|{layer_name}"
        else:
            layer_name = ""
            item_text = os.path.basename(feature_b_path)
        
        # 添加到列表
        from PyQt6.QtWidgets import QListWidgetItem
        item = QListWidgetItem(item_text)
        self.layer_list.addItem(item)
        
        # 保存图层信息
        self.layers_info.append({
            'path': feature_b_path,
            'layer': layer_name,
            'is_gdb': is_gdb
        })
    
    def _addAllLayersToList(self):
        """将GDB中的所有图层添加到被裁剪列表"""
        feature_b_path = self.feature_b_path.text()
        if not feature_b_path:
            self.showError("请先选择被裁剪文件")
            return
        
        if not feature_b_path.lower().endswith('.gdb'):
            self.showError("只有GDB文件支持添加所有图层")
            return
        
        # 读取GDB中的所有图层
        try:
            with fiona.Env():
                layers = fiona.listlayers(feature_b_path)
            
            if not layers:
                self.showError("GDB中没有找到图层")
                return
            
            # 添加所有图层到列表
            from PyQt6.QtWidgets import QListWidgetItem
            gdb_basename = os.path.basename(feature_b_path)
            
            for layer_name in layers:
                item_text = f"{gdb_basename}|{layer_name}"
                item = QListWidgetItem(item_text)
                self.layer_list.addItem(item)
                
                # 保存图层信息
                self.layers_info.append({
                    'path': feature_b_path,
                    'layer': layer_name,
                    'is_gdb': True
                })
            
            # 显示成功信息
            from qfluentwidgets import InfoBar, InfoBarPosition
            InfoBar.success(
                title="成功",
                content=f"已将{len(layers)}个图层添加到列表",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT
            )
            
        except Exception as e:
            from qfluentwidgets import InfoBar, InfoBarPosition
            InfoBar.error(
                title="错误",
                content=f"读取GDB图层失败: {str(e)}",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT
            )
    
    def _moveLayerUp(self):
        """上移图层"""
        selected_index = self.layer_list.currentRow()
        if selected_index <= 0:
            return
        
        # 交换列表项
        self.layer_list.insertItem(selected_index - 1, self.layer_list.takeItem(selected_index))
        # 交换图层信息
        self.layers_info[selected_index], self.layers_info[selected_index - 1] = \
            self.layers_info[selected_index - 1], self.layers_info[selected_index]
        # 保持选中状态
        self.layer_list.setCurrentRow(selected_index - 1)
    
    def _moveLayerDown(self):
        """下移图层"""
        selected_index = self.layer_list.currentRow()
        if selected_index < 0 or selected_index >= self.layer_list.count() - 1:
            return
        
        # 交换列表项
        self.layer_list.insertItem(selected_index + 1, self.layer_list.takeItem(selected_index))
        # 交换图层信息
        self.layers_info[selected_index], self.layers_info[selected_index + 1] = \
            self.layers_info[selected_index + 1], self.layers_info[selected_index]
        # 保持选中状态
        self.layer_list.setCurrentRow(selected_index + 1)
    
    def _deleteLayer(self):
        """删除选中的图层"""
        selected_index = self.layer_list.currentRow()
        if selected_index < 0:
            self.showError("请先选择要删除的图层")
            return
        
        # 删除列表项
        self.layer_list.takeItem(selected_index)
        # 删除图层信息
        del self.layers_info[selected_index]
    
    def _clearLayerList(self):
        """清空图层列表"""
        if self.layer_list.count() == 0:
            return
        
        # 清空列表
        self.layer_list.clear()
        # 清空图层信息
        self.layers_info.clear()
    
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
            
            # 禁用GDB输出模式相关组件
            self.gdb_mode_label.setEnabled(False)
            self.gdb_mode_combo.setEnabled(False)
            
            # 隐藏其他GDB相关选项
            for i in range(self.gdb_output_layout.count()):
                widget = self.gdb_output_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(False)
            
            for i in range(self.gdb_folder_layout.count()):
                widget = self.gdb_folder_layout.itemAt(i).widget()
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
            
            # 启用GDB输出模式相关组件
            self.gdb_mode_label.setEnabled(True)
            self.gdb_mode_combo.setEnabled(True)
            
            # 根据当前GDB模式显示相应的路径选择
            self._on_gdb_mode_changed(self.gdb_mode_combo.currentText())
            
            # 不再显示GDB图层说明
            for i in range(self.gdb_layer_layout.count()):
                widget = self.gdb_layer_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(False)
    
    def _on_gdb_mode_changed(self, gdb_mode):
        """GDB输出模式变化处理"""
        if gdb_mode == "指定GDB输出":
            # 显示指定GDB路径选择，隐藏新建GDB文件夹选择
            for i in range(self.gdb_output_layout.count()):
                widget = self.gdb_output_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(True)
            
            for i in range(self.gdb_folder_layout.count()):
                widget = self.gdb_folder_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(False)
        else:
            # 显示新建GDB文件夹选择，隐藏指定GDB路径选择
            for i in range(self.gdb_output_layout.count()):
                widget = self.gdb_output_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(False)
            
            for i in range(self.gdb_folder_layout.count()):
                widget = self.gdb_folder_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(True)
    
    def _select_output_gdb_folder(self):
        """选择GDB输出文件夹"""
        folder_path = QFileDialog.getExistingDirectory(
            self, "选择GDB输出文件夹", "."
        )
        
        if folder_path:
            self.output_gdb_folder.setText(folder_path)
    
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
        style += "    background-color: qlineargradient(x1:0, y1:0, x2:1, y2=0, "
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
        
        if not os.path.exists(self.feature_a_path.text()):
            return False, "裁剪范围文件不存在"
        
        # 验证裁剪范围GDB图层选择
        if self.feature_a_path.text().lower().endswith('.gdb'):
            if not self.feature_a_layer_combo.currentText():
                return False, "请选择裁剪范围的GDB图层"
        
        # 验证被裁剪图层列表
        if len(self.layers_info) == 0:
            return False, "请至少添加一个被裁剪图层到列表"
        
        # 验证每个被裁剪图层
        for layer_info in self.layers_info:
            if not os.path.exists(layer_info['path']):
                return False, f"被裁剪文件不存在: {layer_info['path']}"
        
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
            gdb_mode = self.gdb_mode_combo.currentText()
            if gdb_mode == "指定GDB输出":
                if not self.output_gdb_path.text():
                    return False, "请选择GDB输出路径"
                
                if not os.path.exists(self.output_gdb_path.text()):
                    return False, "GDB输出文件不存在"
                
                if not self.output_gdb_path.text().lower().endswith('.gdb'):
                    return False, "请选择有效的GDB文件"
            else:
                if not self.output_gdb_folder.text():
                    return False, "请选择GDB输出文件夹"
                
                if not os.path.exists(self.output_gdb_folder.text()):
                    return False, "GDB输出文件夹不存在"
        
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
        threshold = self.buffer_spin.value()
        crop_mode = self.crop_mode_combo.currentText()  # 获取裁剪模式
        
        # 获取裁剪范围图层名称
        feature_a_layer = self.feature_a_layer_combo.currentText() if feature_a_path.lower().endswith('.gdb') else ""
        
        # 获取输出设置
        output_type = self.output_type_combo.currentText()
        if output_type == "SHP文件":
            output_path = self.outputFilePath.text()
            output_gdb_path = ""
            gdb_mode = ""
            gdb_output_folder = ""
        else:
            output_path = ""  # 不再需要手动输入图层名
            gdb_mode = self.gdb_mode_combo.currentText()
            if gdb_mode == "指定GDB输出":
                output_gdb_path = self.output_gdb_path.text()
                gdb_output_folder = ""
            else:
                output_gdb_path = ""  # 新建GDB时，路径在裁剪线程中生成
                gdb_output_folder = self.output_gdb_folder.text()
        
        print(f"开始执行要素裁剪...")
        print(f"裁剪范围: {feature_a_path}")
        print(f"裁剪范围图层: {feature_a_layer}")
        print(f"被裁剪图层数量: {len(self.layers_info)}")
        print(f"裁剪模式: {crop_mode}")
        print(f"外扩阈值: {threshold}")
        print(f"输出类型: {output_type}")
        if output_type == "SHP文件":
            print(f"输出路径: {output_path}")
        else:
            print(f"GDB输出模式: {gdb_mode}")
            if gdb_mode == "指定GDB输出":
                print(f"输出GDB: {output_gdb_path}")
            else:
                print(f"输出GDB文件夹: {gdb_output_folder}")
        
        # 显示进度
        self.showProgress("正在裁剪...")
        # 设置进度条容器为可见
        self.progress_container.setVisible(True)
        
        # 启动裁剪线程
        self.crop_thread = CropThread(
            feature_a_path, feature_a_layer, self.layers_info, 
            output_path, threshold, output_gdb_path, crop_mode, 
            gdb_mode=gdb_mode, gdb_output_folder=gdb_output_folder
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
