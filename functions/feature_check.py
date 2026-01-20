# feature_check.py - 要素检查功能模块
# 用于检查GDB中图层要素或SHP要素的常规检查
import os
import geopandas as gpd
import shapely
from shapely.geometry import Polygon, MultiPolygon, LineString
from shapely.validation import make_valid
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QCheckBox, QFileDialog, QListWidget, QListWidgetItem, QProgressBar,
                            QGroupBox, QGridLayout, QFrame, QMessageBox, QSlider, QSizePolicy)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from qfluentwidgets import (PrimaryPushButton, PushButton, ToggleButton, SwitchButton, FluentIcon, InfoBar,
                            InfoBarPosition, LineEdit, ComboBox, SpinBox)
from .base_function import BaseFunction

class FeatureCheckWorker(QThread):
    """要素检查工作线程"""
    progress_updated = pyqtSignal(int)  # 主进度条信号
    overlap_progress_updated = pyqtSignal(int)  # 面面相叠检查进度条信号
    result_progress_updated = pyqtSignal(int)  # 结果生成进度条信号
    check_completed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, input_path, check_items, layer_name=None, check_params=None):
        super().__init__()
        self.input_path = input_path
        self.check_items = check_items
        self.layer_name = layer_name
        self.check_params = check_params or {}
        
    def run(self):
        """执行检查"""
        try:
            # 读取要素
            if self.layer_name:
                # GDB图层
                try:
                    gdf = gpd.read_file(self.input_path, layer=self.layer_name)
                except Exception as e:
                    self.error_occurred.emit(f"读取GDB图层 '{self.layer_name}' 失败: {str(e)}")
                    return
            else:
                # SHP文件
                try:
                    gdf = gpd.read_file(self.input_path)
                except Exception as e:
                    self.error_occurred.emit(f"读取SHP文件失败: {str(e)}")
                    return
            
            # 验证读取结果
            if gdf is None:
                self.error_occurred.emit("文件读取失败，未返回有效的GeoDataFrame")
                return
            
            total_features = len(gdf)
            if total_features == 0:
                if self.layer_name:
                    self.error_occurred.emit(f"图层 '{self.layer_name}' 中没有找到要素")
                else:
                    self.error_occurred.emit("文件中没有找到要素")
                return
            
            # 初始化结果字典
            results = {
                'narrow': [],
                'overlap': [],
                'roundabout': [],
                'sharp_angle': [],
                'tadpole': []
            }
            
            # 检查每个要素
            geometries = []
            sharp_angle_lines = []  # 存储尖锐角的夹角线
            for idx, row in gdf.iterrows():
                geometry = row.geometry
                geometries.append(geometry)
                
                # 进度更新
                progress = int((idx + 1) / total_features * 100)
                self.progress_updated.emit(progress)
                
                # 确保几何有效（用于其他检查）
                if not geometry.is_valid:
                    geometry = make_valid(geometry)
                    if not geometry.is_valid:
                        continue
                
                # 狭长检查
                if 'narrow' in self.check_items:
                    is_narrow, aspect_ratio = self._check_narrow(geometry)
                    if is_narrow:
                        results['narrow'].append((idx, aspect_ratio))
                
                # 环岛图斑检查
                if 'roundabout' in self.check_items:
                    if self._check_roundabout(geometry):
                        results['roundabout'].append(idx)
                
                # 尖锐角检查
                if 'sharp_angle' in self.check_items:
                    angles = self._check_sharp_angle(geometry)
                    if angles:
                        results['sharp_angle'].append(idx)
                        sharp_angle_lines.extend(angles)
                
                # 蝌蚪形图斑检查
                if 'tadpole' in self.check_items:
                    tadpole_lines = self._check_tadpole(geometry)
                    if tadpole_lines:
                        results['tadpole'].append(idx)
                        # 存储蝌蚪形图斑的线段
                        if not hasattr(self, 'tadpole_lines'):
                            self.tadpole_lines = []
                        self.tadpole_lines.extend(tadpole_lines)
            
            # 面面相叠检查（只保留重叠部分）
            overlap_geometries = []
            if 'overlap' in self.check_items:
                # 为所有几何创建有效的2D多边形副本和边界框
                valid_geometries = []
                bounds_list = []
                for geometry in geometries:
                    # 确保几何有效
                    if not geometry.is_valid:
                        geometry = make_valid(geometry)
                    # 转换为2D几何
                    if geometry.has_z:
                        geometry = geometry.buffer(0)
                    valid_geometries.append(geometry)
                    bounds_list.append(geometry.bounds)
                
                # 记录已经检查过的要素对，避免重复检查
                checked_pairs = set()
                total_pairs = len(valid_geometries) * (len(valid_geometries) - 1) // 2
                checked_count = 0
                
                # 使用边界框预检查优化性能（不依赖外部库）
                for i in range(len(valid_geometries)):
                    if not isinstance(valid_geometries[i], (Polygon, MultiPolygon)):
                        continue
                    
                    bbox1 = bounds_list[i]
                    
                    for j in range(i + 1, len(valid_geometries)):
                        if not isinstance(valid_geometries[j], (Polygon, MultiPolygon)):
                            continue
                        
                        # 跳过已经检查过的对
                        pair = tuple(sorted((i, j)))
                        if pair in checked_pairs:
                            continue
                        checked_pairs.add(pair)
                        checked_count += 1
                        
                        try:
                            bbox2 = bounds_list[j]
                            
                            # 边界框快速预检查
                            if (bbox1[2] < bbox2[0] or bbox1[0] > bbox2[2] or 
                                bbox1[3] < bbox2[1] or bbox1[1] > bbox2[3]):
                                continue  # 边界框不相交，跳过
                            
                            geom1 = valid_geometries[i]
                            geom2 = valid_geometries[j]
                            
                            # 计算重叠区域
                            intersection = geom1.intersection(geom2)
                            
                            # 只保留有实际面积的重叠区域
                            if hasattr(intersection, 'area') and intersection.area > 1e-8:
                                # 确保重叠区域是有效的多边形
                                if isinstance(intersection, (Polygon, MultiPolygon)):
                                    overlap_geometries.append(intersection)
                                elif hasattr(intersection, 'geoms'):  # 处理GeometryCollection
                                    for part in intersection.geoms:
                                        if isinstance(part, (Polygon, MultiPolygon)) and part.area > 1e-8:
                                            overlap_geometries.append(part)
                        except Exception as e:
                            continue
                        
                        # 发送面面相叠检查进度更新
                        progress = int(checked_count / total_pairs * 100)
                        self.overlap_progress_updated.emit(progress)
            
            # 生成结果GeoDataFrame
            result_gdfs = {}
            
            # 计算总结果类型数
            total_result_types = 0
            if 'narrow' in self.check_items:
                total_result_types += 1
            if 'overlap' in self.check_items:
                total_result_types += 1
            if 'roundabout' in self.check_items:
                total_result_types += 1
            if 'sharp_angle' in self.check_items:
                total_result_types += 1
            if 'tadpole' in self.check_items:
                total_result_types += 1
            
            processed_types = 0
            
            # 发送结果生成开始信号
            self.result_progress_updated.emit(0)
            
            # 处理狭长和环岛图斑结果（保留原始要素）
            for check_type, indices in results.items():
                if check_type == 'sharp_angle':
                    # 尖锐角结果单独处理，生成夹角线
                    continue
                elif check_type != 'overlap' and indices:
                    if check_type == 'narrow':
                        # 处理狭长结果，添加宽长比字段
                        narrow_indices = [idx for idx, _ in indices]
                        narrow_gdf = gdf.iloc[narrow_indices].copy()
                        narrow_gdf['threshold'] = [aspect_ratio for _, aspect_ratio in indices]
                        result_gdfs[check_type] = narrow_gdf
                    else:
                        # 其他结果直接复制
                        result_gdfs[check_type] = gdf.iloc[indices].copy()
                    processed_types += 1
                    # 更新结果生成进度
                    progress = int(processed_types / total_result_types * 100)
                    self.result_progress_updated.emit(progress)
            
            # 处理面面相叠结果（只保留重叠区域）
            if overlap_geometries and 'overlap' in self.check_items:
                # 创建只包含重叠区域的GeoDataFrame
                overlap_gdf = gpd.GeoDataFrame(geometry=overlap_geometries, crs=gdf.crs)
                result_gdfs['overlap'] = overlap_gdf
                processed_types += 1
            
            # 处理尖锐角结果（生成夹角线）
            if sharp_angle_lines and 'sharp_angle' in self.check_items:
                # 创建包含夹角线和角度值的GeoDataFrame
                angles = [angle for angle, _ in sharp_angle_lines]
                lines = [line for _, line in sharp_angle_lines]
                sharp_angle_gdf = gpd.GeoDataFrame({'threshold': angles, 'geometry': lines}, crs=gdf.crs)
                result_gdfs['sharp_angle'] = sharp_angle_gdf
                processed_types += 1
            
            # 处理蝌蚪形图斑结果（生成问题线段）
            if hasattr(self, 'tadpole_lines') and self.tadpole_lines and 'tadpole' in self.check_items:
                # 创建包含问题线段和距离值的GeoDataFrame
                distances = [distance for distance, _ in self.tadpole_lines]
                lines = [line for _, line in self.tadpole_lines]
                tadpole_gdf = gpd.GeoDataFrame({'distance': distances, 'geometry': lines}, crs=gdf.crs)
                result_gdfs['tadpole'] = tadpole_gdf
                processed_types += 1
            
            # 发送结果生成完成信号
            self.result_progress_updated.emit(100)
            
            self.check_completed.emit(result_gdfs)
            
        except Exception as e:
            self.error_occurred.emit(str(e))
    

    
    def _check_narrow(self, geometry):
        """检查狭长面（通过宽长比判断）并返回宽长比"""
        # 获取阈值，默认0.2
        threshold = self.check_params.get('narrow_threshold', 0.2)
        
        if isinstance(geometry, Polygon):
            min_rect = geometry.minimum_rotated_rectangle
            if min_rect.area == 0:
                return False, 0
            # 计算宽长比
            coords = list(min_rect.exterior.coords)
            if len(coords) >= 5:
                # 计算边长
                # 使用 math.hypot 计算两点之间的距离
                edge1 = ((coords[1][0] - coords[0][0]) ** 2 + (coords[1][1] - coords[0][1]) ** 2) ** 0.5
                edge2 = ((coords[2][0] - coords[1][0]) ** 2 + (coords[2][1] - coords[1][1]) ** 2) ** 0.5
                width = min(edge1, edge2)
                length = max(edge1, edge2)
                if length > 0:
                    aspect_ratio = width / length
                    # 宽长比小于阈值视为狭长
                    return aspect_ratio < threshold, aspect_ratio
        elif isinstance(geometry, MultiPolygon):
            # 对每个多边形进行检查
            for poly in geometry.geoms:
                is_narrow, aspect_ratio = self._check_narrow(poly)
                if is_narrow:
                    return True, aspect_ratio
        return False, 0
    
    def _check_roundabout(self, geometry):
        """检查环岛图斑（具有多个内部环的多边形）"""
        if isinstance(geometry, Polygon):
            # 检查多边形是否有内部环（孔洞）
            if len(geometry.interiors) > 0:
                return True
        elif isinstance(geometry, MultiPolygon):
            # 对每个多边形进行检查
            for poly in geometry.geoms:
                if self._check_roundabout(poly):
                    return True
        return False
    
    def _check_sharp_angle(self, geometry):
        """检查尖锐角（小于阈值的内角）并返回包含角度值和两根线组成的角度要素"""
        # 获取阈值，默认30度
        threshold = self.check_params.get('sharp_angle_threshold', 30.0)
        
        # 将角度转换为弧度
        import math
        from shapely.geometry import LineString
        threshold_rad = math.radians(threshold)
        
        sharp_angles = []
        
        if isinstance(geometry, Polygon):
            coords = list(geometry.exterior.coords)
            # 移除最后一个点，因为它与第一个点相同
            if len(coords) > 1 and coords[0] == coords[-1]:
                coords = coords[:-1]
            
            if len(coords) < 3:
                return sharp_angles
            
            # 计算每个顶点的内角
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
                # 确保cos_angle在[-1, 1]范围内，避免数值误差导致的问题
                cos_angle = max(-1.0, min(1.0, cos_angle))
                angle = math.acos(cos_angle)
                
                # 检查夹角是否小于阈值
                if angle < threshold_rad:
                    # 将弧度转换为角度
                    angle_deg = math.degrees(angle)
                    
                    # 计算向量的单位向量
                    unit_vec1 = (vec1[0]/len1, vec1[1]/len1)
                    unit_vec2 = (vec2[0]/len2, vec2[1]/len2)
                    
                    # 延伸距离（根据原边长的10%）
                    extend_dist = min(len1, len2) * 0.1
                    
                    # 确保curr_point是2D坐标
                    curr_point_2d = (curr_point[0], curr_point[1])
                    
                    # 生成两根线，形成完整的角度
                    # 第一根线：从顶点向第一个方向延伸
                    line1_end = (curr_point_2d[0] + unit_vec1[0] * extend_dist, curr_point_2d[1] + unit_vec1[1] * extend_dist)
                    line1 = LineString([curr_point_2d, line1_end])
                    
                    # 第二根线：从顶点向第二个方向延伸
                    line2_end = (curr_point_2d[0] + unit_vec2[0] * extend_dist, curr_point_2d[1] + unit_vec2[1] * extend_dist)
                    line2 = LineString([curr_point_2d, line2_end])
                    
                    # 添加这两根线和角度值到结果列表
                    sharp_angles.append((angle_deg, line1))
                    sharp_angles.append((angle_deg, line2))
            
            # 检查内部环（孔洞）
            for interior in geometry.interiors:
                coords = list(interior.coords)
                # 移除最后一个点
                if len(coords) > 1 and coords[0] == coords[-1]:
                    coords = coords[:-1]
                
                if len(coords) < 3:
                    continue
                
                # 计算每个顶点的内角
                for i in range(len(coords)):
                    prev_point = coords[i-1] if i > 0 else coords[-1]
                    curr_point = coords[i]
                    next_point = coords[i+1] if i < len(coords)-1 else coords[0]
                    
                    vec1 = (prev_point[0] - curr_point[0], prev_point[1] - curr_point[1])
                    vec2 = (next_point[0] - curr_point[0], next_point[1] - curr_point[1])
                    
                    len1 = math.hypot(vec1[0], vec1[1])
                    len2 = math.hypot(vec2[0], vec2[1])
                    
                    if len1 == 0 or len2 == 0:
                        continue
                    
                    dot_product = vec1[0] * vec2[0] + vec1[1] * vec2[1]
                    cos_angle = dot_product / (len1 * len2)
                    cos_angle = max(-1.0, min(1.0, cos_angle))
                    angle = math.acos(cos_angle)
                    
                    if angle < threshold_rad:
                        # 将弧度转换为角度
                        angle_deg = math.degrees(angle)
                        
                        # 计算向量的单位向量
                        unit_vec1 = (vec1[0]/len1, vec1[1]/len1)
                        unit_vec2 = (vec2[0]/len2, vec2[1]/len2)
                        
                        # 延伸距离（根据原边长的10%）
                        extend_dist = min(len1, len2) * 0.1
                        
                        # 确保curr_point是2D坐标
                        curr_point_2d = (curr_point[0], curr_point[1])
                        
                        # 生成两根线，形成完整的角度
                        # 第一根线：从顶点向第一个方向延伸
                        line1_end = (curr_point_2d[0] + unit_vec1[0] * extend_dist, curr_point_2d[1] + unit_vec1[1] * extend_dist)
                        line1 = LineString([curr_point_2d, line1_end])
                        
                        # 第二根线：从顶点向第二个方向延伸
                        line2_end = (curr_point_2d[0] + unit_vec2[0] * extend_dist, curr_point_2d[1] + unit_vec2[1] * extend_dist)
                        line2 = LineString([curr_point_2d, line2_end])
                        
                        # 添加这两根线和角度值到结果列表
                        sharp_angles.append((angle_deg, line1))
                        sharp_angles.append((angle_deg, line2))
        elif isinstance(geometry, MultiPolygon):
            # 对每个多边形进行检查
            for poly in geometry.geoms:
                sharp_angles.extend(self._check_sharp_angle(poly))
        return sharp_angles
    
    def _check_tadpole(self, geometry):
        """检查蝌蚪形图斑：一个图斑转换为线段后，出现一条线段与不相接的另一条线段边界距离小于阈值且有一定长度相邻的情况"""
        # 获取阈值，默认距离阈值1米，长度阈值1米
        distance_threshold = self.check_params.get('tadpole_distance_threshold', 1.0)
        length_threshold = self.check_params.get('tadpole_length_threshold', 1.0)
        
        import math
        
        # 辅助函数：计算线段的方向向量
        def get_direction_vector(line):
            coords = list(line.coords)
            x1, y1 = coords[0]
            x2, y2 = coords[-1]
            dx = x2 - x1
            dy = y2 - y1
            length = math.hypot(dx, dy)
            if length == 0:
                return (0, 0)
            # 单位向量
            return (dx / length, dy / length)
        
        # 辅助函数：计算两条线段的平行程度（返回角度的余弦值，1表示平行，0表示垂直）
        def get_parallel_degree(vec1, vec2):
            # 计算点积
            dot_product = vec1[0] * vec2[0] + vec1[1] * vec2[1]
            # 取绝对值，因为平行包括相同方向和相反方向
            return abs(dot_product)
        
        # 辅助函数：计算两条线段的平行重叠长度
        def get_parallel_overlap_length(line1, line2, distance_threshold, parallel_threshold=0.8):
            # 计算两条线段的方向向量
            vec1 = get_direction_vector(line1)
            vec2 = get_direction_vector(line2)
            
            # 计算平行程度，如果小于阈值则认为不平行
            parallel_degree = get_parallel_degree(vec1, vec2)
            if parallel_degree < parallel_threshold:
                return 0.0
            
            # 采样间隔，用于检测平行重叠部分
            sample_interval = 0.5  # 0.5米采样
            
            # 对线段1进行采样，检查每个采样点到线段2的距离
            line1_length = line1.length
            num_samples = max(2, int(line1_length / sample_interval) + 1)
            
            # 记录符合条件的采样点位置
            valid_samples = []
            
            for sample_idx in range(num_samples):
                # 均匀采样
                sample_dist = (sample_idx / (num_samples - 1)) * line1_length if num_samples > 1 else 0
                sample_point = line1.interpolate(sample_dist)
                
                # 检查采样点到另一条线段的距离
                if sample_point.distance(line2) < distance_threshold:
                    valid_samples.append(sample_dist)
            
            # 如果没有足够的采样点，返回0
            if len(valid_samples) < 2:
                return 0.0
            
            # 计算连续采样点之间的最大距离
            # 首先排序采样点位置
            valid_samples.sort()
            
            max_overlap_length = 0.0
            current_start = valid_samples[0]
            
            for i in range(1, len(valid_samples)):
                # 如果两个采样点之间的距离超过采样间隔的2倍，认为是不连续的
                if valid_samples[i] - valid_samples[i-1] > sample_interval * 2:
                    # 计算当前连续段的长度
                    current_length = valid_samples[i-1] - current_start
                    if current_length > max_overlap_length:
                        max_overlap_length = current_length
                    # 开始新的连续段
                    current_start = valid_samples[i]
            
            # 计算最后一个连续段的长度
            final_length = valid_samples[-1] - current_start
            if final_length > max_overlap_length:
                max_overlap_length = final_length
            
            return max_overlap_length
        
        tadpole_lines = []
        
        # 确保几何类型正确
        if isinstance(geometry, Polygon):
            # 将多边形转换为线段（仅外部边界）
            exterior_coords = list(geometry.exterior.coords)
            if len(exterior_coords) < 2:
                return tadpole_lines
            
            # 生成所有线段及其边界框
            lines = []
            line_bboxes = []
            for i in range(len(exterior_coords) - 1):
                line = LineString([exterior_coords[i], exterior_coords[i+1]])
                lines.append(line)
                # 计算扩展后的边界框，用于快速预检查
                bbox = line.bounds
                expanded_bbox = (
                    bbox[0] - distance_threshold,
                    bbox[1] - distance_threshold,
                    bbox[2] + distance_threshold,
                    bbox[3] + distance_threshold
                )
                line_bboxes.append(expanded_bbox)
            
            # 检查每对线段
            num_lines = len(lines)
            for i in range(num_lines):
                # 获取当前线段和其扩展边界框
                line1 = lines[i]
                bbox1 = line_bboxes[i]
                
                # 获取线段1的端点
                coords1 = list(line1.coords)
                p1_start, p1_end = coords1[0], coords1[-1]
                
                for j in range(i + 1, num_lines):
                    # 获取另一线段和其边界框
                    line2 = lines[j]
                    bbox2 = line_bboxes[j]
                    
                    # 边界框快速预检查：如果扩展边界框不相交，则跳过
                    if (bbox1[2] < bbox2[0] or bbox1[0] > bbox2[2] or 
                        bbox1[3] < bbox2[1] or bbox1[1] > bbox2[3]):
                        continue
                    
                    # 获取线段2的端点
                    coords2 = list(line2.coords)
                    p2_start, p2_end = coords2[0], coords2[-1]
                    
                    # 快速检查线段是否相邻（有公共点）
                    is_adjacent = False
                    if (p1_start == p2_start or p1_start == p2_end or 
                        p1_end == p2_start or p1_end == p2_end):
                        is_adjacent = True
                    if is_adjacent:
                        continue
                    
                    # 计算两条线段之间的距离
                    distance = line1.distance(line2)
                    
                    # 如果距离大于等于阈值，跳过
                    if distance >= distance_threshold:
                        continue
                    
                    # 计算两条线段的平行重叠长度
                    overlap_length1 = get_parallel_overlap_length(line1, line2, distance_threshold)
                    overlap_length2 = get_parallel_overlap_length(line2, line1, distance_threshold)
                    
                    # 取两条线段中较大的重叠长度
                    max_overlap_length = max(overlap_length1, overlap_length2)
                    
                    # 如果平行重叠长度超过阈值，记录这对线段
                    if max_overlap_length >= length_threshold:
                        tadpole_lines.append((distance, line1))
                        tadpole_lines.append((distance, line2))
                        # 找到一对符合条件的线段后，可以考虑提前终止当前图斑的检查
                        break
        elif isinstance(geometry, MultiPolygon):
            # 对每个多边形进行检查
            for poly in geometry.geoms:
                tadpole_lines.extend(self._check_tadpole(poly))
        
        return tadpole_lines
    


class FeatureCheckFunction(BaseFunction):
    """要素检查功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>" 
            "对GDB中图层要素或SHP要素的常规检查，检查包括：<br>" 
            "- 是否存在狭长<br>" 
            "- 是否存在环岛图斑<br>" 
            "- 是否存在尖锐角<br>" 
            "检查结果生成要素矢量文件"
        )
        super().__init__("要素常规检查", description, parent)
        
        self.input_path = ""
        self.layer_name = ""
        self.check_items = []
        self.worker = None
        
        self._initUI()
    
    def _initUI(self):
        """初始化UI"""
        # 输入选择区域
        input_group = QGroupBox("输入选择")
        input_layout = QVBoxLayout(input_group)
        
        # 批量检测选项
        batch_layout = QHBoxLayout()
        self.batch_check = SwitchButton(self)
        batch_layout.addWidget(QLabel("批量检测："))
        batch_layout.addWidget(self.batch_check)
        batch_layout.addStretch(1)
        
        input_layout.addLayout(batch_layout)
        
        # 文件/文件夹路径选择
        file_layout = QHBoxLayout()
        file_label = QLabel("路径：")
        self.file_edit = LineEdit()
        self.file_edit.setPlaceholderText("请输入文件/文件夹路径或点击浏览选择")
        self.shp_browse_btn = PushButton("浏览SHP", self, FluentIcon.DOCUMENT)
        self.shp_browse_btn.clicked.connect(self._browse_shp)
        self.gdb_browse_btn = PushButton("浏览GDB", self, FluentIcon.FOLDER)
        self.gdb_browse_btn.clicked.connect(self._browse_gdb)
        self.folder_browse_btn = PushButton("浏览文件夹", self, FluentIcon.FOLDER)
        self.folder_browse_btn.clicked.connect(self._browse_folder)
        
        file_layout.addWidget(file_label)
        file_layout.addWidget(self.file_edit)
        file_layout.addWidget(self.shp_browse_btn)
        file_layout.addWidget(self.gdb_browse_btn)
        file_layout.addWidget(self.folder_browse_btn)
        
        # 图层选择（仅GDB文件需要）
        layer_layout = QHBoxLayout()
        self.layer_label = QLabel("图层名称：")
        self.layer_combo = ComboBox()
        self.layer_combo.setPlaceholderText("选择图层")
        self.layer_combo.setEnabled(False)
        # 初始隐藏图层选择控件
        self.layer_label.setVisible(False)
        self.layer_combo.setVisible(False)
        
        layer_layout.addWidget(self.layer_label)
        layer_layout.addWidget(self.layer_combo)
        layer_layout.addStretch(1)
        
        input_layout.addLayout(file_layout)
        input_layout.addLayout(layer_layout)
        
        # 检查项选择区域
        check_group = QGroupBox("检查项选择")
        check_layout = QGridLayout(check_group)
        
        # 设置网格间距和对齐
        check_layout.setHorizontalSpacing(15)  # 水平间距
        check_layout.setVerticalSpacing(20)  # 垂直间距
        
        # 一行显示所有检查项
        # 狭长检查
        narrow_label = QLabel("狭长检查：")
        check_layout.addWidget(narrow_label, 0, 0, Qt.AlignmentFlag.AlignRight)
        
        self.narrow_check = SwitchButton(self)  # 只显示开关，不包含文本
        check_layout.addWidget(self.narrow_check, 0, 1, Qt.AlignmentFlag.AlignLeft)
        
        # 面面相叠检查
        overlap_label = QLabel("面面相叠检查：")
        check_layout.addWidget(overlap_label, 0, 2, Qt.AlignmentFlag.AlignRight)
        
        self.overlap_check = SwitchButton(self)  # 只显示开关，不包含文本
        check_layout.addWidget(self.overlap_check, 0, 3, Qt.AlignmentFlag.AlignLeft)
        
        # 环岛图斑检查
        roundabout_label = QLabel("环岛图斑检查：")
        check_layout.addWidget(roundabout_label, 0, 4, Qt.AlignmentFlag.AlignRight)
        
        self.roundabout_check = SwitchButton(self)  # 只显示开关，不包含文本
        check_layout.addWidget(self.roundabout_check, 0, 5, Qt.AlignmentFlag.AlignLeft)
        
        # 尖锐角检查
        sharp_angle_label = QLabel("尖锐角检查：")
        check_layout.addWidget(sharp_angle_label, 0, 6, Qt.AlignmentFlag.AlignRight)
        
        self.sharp_angle_check = SwitchButton(self)  # 只显示开关，不包含文本
        check_layout.addWidget(self.sharp_angle_check, 0, 7, Qt.AlignmentFlag.AlignLeft)
        
        # 蝌蚪形图斑检查
        tadpole_label = QLabel("蝌蚪形图斑检查：")
        check_layout.addWidget(tadpole_label, 0, 8, Qt.AlignmentFlag.AlignRight)
        
        self.tadpole_check = SwitchButton(self)  # 只显示开关，不包含文本
        check_layout.addWidget(self.tadpole_check, 0, 9, Qt.AlignmentFlag.AlignLeft)
        
        # 创建一个容器来容纳所有阈值控件，初始隐藏
        self.all_thresholds_container = QWidget()
        all_thresholds_layout = QHBoxLayout(self.all_thresholds_container)
        all_thresholds_layout.setSpacing(20)  # 设置适当间距
        all_thresholds_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # 狭长阈值控件
        self.threshold_container = QWidget()
        threshold_layout = QHBoxLayout(self.threshold_container)
        threshold_layout.setSpacing(15)  # 增加间距
        threshold_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.narrow_threshold_label = QLabel("狭长阈值：")
        threshold_layout.addWidget(self.narrow_threshold_label, 0, Qt.AlignmentFlag.AlignRight)
        
        self.narrow_threshold_slider = QSlider(Qt.Orientation.Horizontal)
        # 设置滑块范围（0-100对应0.0-1.0）
        self.narrow_threshold_slider.setMinimum(0)
        self.narrow_threshold_slider.setMaximum(100)
        self.narrow_threshold_slider.setValue(20)  # 默认0.2
        self.narrow_threshold_slider.setTickInterval(5)
        self.narrow_threshold_slider.setSingleStep(1)
        # 设置滑块宽度和样式
        self.narrow_threshold_slider.setMinimumWidth(300)  # 加宽滑块
        self.narrow_threshold_slider.setTickPosition(QSlider.TickPosition.TicksBelow)  # 添加刻度
        self.narrow_threshold_slider.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        threshold_layout.addWidget(self.narrow_threshold_slider, 1, Qt.AlignmentFlag.AlignCenter)
        
        self.narrow_threshold_value = QLabel("0.2")
        self.narrow_threshold_value.setStyleSheet("QLabel { font-weight: bold; }")  # 加粗显示数值
        threshold_layout.addWidget(self.narrow_threshold_value, 0, Qt.AlignmentFlag.AlignLeft)
        
        self.threshold_container.setVisible(False)
        all_thresholds_layout.addWidget(self.threshold_container)
        
        # 尖锐角阈值控件
        self.sharp_angle_threshold_container = QWidget()
        sharp_angle_threshold_layout = QHBoxLayout(self.sharp_angle_threshold_container)
        sharp_angle_threshold_layout.setSpacing(15)  # 增加间距
        sharp_angle_threshold_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.sharp_angle_threshold_label = QLabel("尖锐角阈值（度）：")
        sharp_angle_threshold_layout.addWidget(self.sharp_angle_threshold_label, 0, Qt.AlignmentFlag.AlignRight)
        
        self.sharp_angle_threshold_slider = QSlider(Qt.Orientation.Horizontal)
        # 设置滑块范围（0-90度）
        self.sharp_angle_threshold_slider.setMinimum(0)
        self.sharp_angle_threshold_slider.setMaximum(90)
        self.sharp_angle_threshold_slider.setValue(30)  # 默认30度
        self.sharp_angle_threshold_slider.setTickInterval(5)
        self.sharp_angle_threshold_slider.setSingleStep(1)
        # 设置滑块宽度和样式，与修复角度阈值滑块保持一致
        self.sharp_angle_threshold_slider.setMinimumWidth(300)  # 加宽滑块
        self.sharp_angle_threshold_slider.setTickPosition(QSlider.TickPosition.TicksBelow)  # 添加刻度
        self.sharp_angle_threshold_slider.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sharp_angle_threshold_layout.addWidget(self.sharp_angle_threshold_slider, 1, Qt.AlignmentFlag.AlignCenter)
        
        self.sharp_angle_threshold_value = QLabel("30")
        self.sharp_angle_threshold_value.setStyleSheet("QLabel { font-weight: bold; }")  # 加粗显示数值
        sharp_angle_threshold_layout.addWidget(self.sharp_angle_threshold_value, 0, Qt.AlignmentFlag.AlignLeft)
        
        self.sharp_angle_threshold_container.setVisible(False)
        all_thresholds_layout.addWidget(self.sharp_angle_threshold_container)
        
        # 蝌蚪形图斑距离阈值控件
        self.tadpole_distance_threshold_container = QWidget()
        tadpole_distance_threshold_layout = QHBoxLayout(self.tadpole_distance_threshold_container)
        tadpole_distance_threshold_layout.setSpacing(15)  # 增加间距
        tadpole_distance_threshold_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.tadpole_distance_threshold_label = QLabel("距离阈值：")
        tadpole_distance_threshold_layout.addWidget(self.tadpole_distance_threshold_label, 0, Qt.AlignmentFlag.AlignRight)
        
        # 使用 SpinBox 替代 Slider，与面消除功能面积阈值样式保持一致
        self.tadpole_distance_threshold_spinbox = SpinBox(self)
        self.tadpole_distance_threshold_spinbox.setFixedWidth(150)
        self.tadpole_distance_threshold_spinbox.setRange(0, 1000)
        self.tadpole_distance_threshold_spinbox.setValue(1)
        self.tadpole_distance_threshold_spinbox.setSingleStep(0.1)
        self.tadpole_distance_threshold_spinbox.setSuffix(' 米')
        self.tadpole_distance_threshold_spinbox.setToolTip('设置距离阈值，小于该值的图斑将被检测为蝌蚪形')
        self.tadpole_distance_threshold_spinbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tadpole_distance_threshold_layout.addWidget(self.tadpole_distance_threshold_spinbox, 1, Qt.AlignmentFlag.AlignCenter)
        
        self.tadpole_distance_threshold_container.setVisible(False)
        all_thresholds_layout.addWidget(self.tadpole_distance_threshold_container)
        
        # 蝌蚪形图斑长度阈值控件
        self.tadpole_length_threshold_container = QWidget()
        tadpole_length_threshold_layout = QHBoxLayout(self.tadpole_length_threshold_container)
        tadpole_length_threshold_layout.setSpacing(15)  # 增加间距
        tadpole_length_threshold_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.tadpole_length_threshold_label = QLabel("长度阈值：")
        tadpole_length_threshold_layout.addWidget(self.tadpole_length_threshold_label, 0, Qt.AlignmentFlag.AlignRight)
        
        # 使用 SpinBox 替代 Slider，与面消除功能面积阈值样式保持一致
        self.tadpole_length_threshold_spinbox = SpinBox(self)
        self.tadpole_length_threshold_spinbox.setFixedWidth(150)
        self.tadpole_length_threshold_spinbox.setRange(0, 1000)
        self.tadpole_length_threshold_spinbox.setValue(1)
        self.tadpole_length_threshold_spinbox.setSingleStep(0.1)
        self.tadpole_length_threshold_spinbox.setSuffix(' 米')
        self.tadpole_length_threshold_spinbox.setToolTip('设置长度阈值，大于该值的图斑将被检测为蝌蚪形')
        self.tadpole_length_threshold_spinbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tadpole_length_threshold_layout.addWidget(self.tadpole_length_threshold_spinbox, 1, Qt.AlignmentFlag.AlignCenter)
        
        self.tadpole_length_threshold_container.setVisible(False)
        all_thresholds_layout.addWidget(self.tadpole_length_threshold_container)
        
        # 跨所有列居中显示，使用最大宽度
        check_layout.addWidget(self.all_thresholds_container, 1, 0, 1, 10, Qt.AlignmentFlag.AlignCenter)
        
        # 连接信号
        # SwitchButton使用checkedChanged信号而不是toggled
        self.narrow_check.checkedChanged.connect(self._on_narrow_check_changed)
        self.narrow_threshold_slider.valueChanged.connect(self._on_threshold_slider_changed)
        
        # 尖锐角检查信号连接
        self.sharp_angle_check.checkedChanged.connect(self._on_sharp_angle_check_changed)
        self.sharp_angle_threshold_slider.valueChanged.connect(self._on_sharp_angle_threshold_slider_changed)
        
        # 蝌蚪形图斑检查信号连接
        self.tadpole_check.checkedChanged.connect(self._on_tadpole_check_changed)
        
        # 设置列拉伸，确保均匀分布
        for i in range(10):
            check_layout.setColumnStretch(i, 1)
        
        # 执行区域
        execute_layout = QHBoxLayout()
        self.execute_btn = PushButton("执行检查", self)
        self.execute_btn.clicked.connect(self._execute_check)
        self.cancel_btn = PushButton("取消", self)
        self.cancel_btn.clicked.connect(self._cancel_check)
        self.cancel_btn.setEnabled(False)
        
        execute_layout.addStretch(1)
        execute_layout.addWidget(self.execute_btn)
        execute_layout.addWidget(self.cancel_btn)
        
        # 进度条区域
        progress_group = QGroupBox("检查进度")
        progress_layout = QVBoxLayout(progress_group)
        
        # 单一进度条，动态显示不同类型的进度
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setFormat("%p%")  # 默认格式，会动态更新
        progress_layout.addWidget(self.progress_bar)
        
        # 结果显示区域
        result_group = QGroupBox("检查结果")
        result_layout = QVBoxLayout(result_group)
        
        self.result_list = QListWidget()
        result_layout.addWidget(self.result_list)
        
        # 保存结果按钮
        save_layout = QHBoxLayout()
        self.save_btn = PushButton("保存结果", self)
        self.save_btn.clicked.connect(self._save_results)
        self.save_btn.setEnabled(False)
        
        save_layout.addStretch(1)
        save_layout.addWidget(self.save_btn)
        
        # 添加到主布局
        self.contentLayout.addWidget(input_group)
        self.contentLayout.addWidget(check_group)
        self.contentLayout.addWidget(progress_group)  # 添加进度条区域
        self.contentLayout.addLayout(execute_layout)
        self.contentLayout.addWidget(result_group)
        self.contentLayout.addLayout(save_layout)
        
        # 初始隐藏进度组
        progress_group.setVisible(False)
        
        # 连接信号
        self.file_edit.textChanged.connect(self._on_file_path_changed)
        
        # 结果数据
        self.result_gdfs = {}
    
    def _browse_shp(self):
        """浏览SHP文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择SHP文件", ".", "Shapefiles (*.shp)"
        )
        if file_path:
            self.file_edit.setText(file_path)
            # 清除图层选择
            self.layer_combo.clear()
            self.layer_combo.setEnabled(False)
            # 隐藏图层选择控件
            self.layer_label.setVisible(False)
            self.layer_combo.setVisible(False)
    
    def _browse_gdb(self):
        """浏览GDB文件"""
        file_path = QFileDialog.getExistingDirectory(
            self, "选择GDB文件", "."
        )
        if file_path and file_path.endswith('.gdb'):
            self.file_edit.setText(file_path)
            # 显示图层选择控件
            self.layer_label.setVisible(True)
            self.layer_combo.setVisible(True)
    
    def _browse_folder(self):
        """浏览文件夹"""
        folder_path = QFileDialog.getExistingDirectory(
            self, "选择文件夹", "."
        )
        if folder_path:
            self.file_edit.setText(folder_path)
            # 批量检测模式下，隐藏图层选择控件
            self.layer_label.setVisible(False)
            self.layer_combo.setVisible(False)
    
    def _on_file_path_changed(self, file_path):
        """文件路径改变时更新图层列表"""
        self.layer_combo.clear()
        self.layer_combo.setEnabled(False)
        
        if file_path.endswith('.gdb'):
            # 显示图层选择控件
            self.layer_label.setVisible(True)
            self.layer_combo.setVisible(True)
            try:
                # 列出GDB中的所有图层
                import fiona
                with fiona.Env():
                    layer_names = fiona.listlayers(file_path)
                
                if not layer_names:
                    InfoBar.warning(
                        title="警告",
                        content=f"GDB文件 '{file_path}' 中没有找到任何图层",
                        parent=self,
                        position=InfoBarPosition.TOP_RIGHT
                    )
                    return
                
                for layer_name in layer_names:
                    self.layer_combo.addItem(layer_name, layer_name)
                self.layer_combo.setEnabled(True)
                # 默认选择第一个图层
                self.layer_combo.setCurrentIndex(0)
            except Exception as e:
                InfoBar.error(
                    title="错误",
                    content=f"无法读取GDB文件: {str(e)}",
                    parent=self,
                    position=InfoBarPosition.TOP_RIGHT
                )
        else:
            # 隐藏图层选择控件
            self.layer_label.setVisible(False)
            self.layer_combo.setVisible(False)
    
    def _on_narrow_check_changed(self, checked):
        """狭长检查开关状态变化时的处理"""
        # 显示/隐藏阈值容器
        self.threshold_container.setVisible(checked)
        # 启用/禁用滑块
        self.narrow_threshold_slider.setEnabled(checked)
    
    def _on_threshold_slider_changed(self, value):
        """阈值滑块值变化时的处理"""
        # 将滑块值转换为实际阈值（0-100 → 0.0-1.0）
        threshold = value / 100.0
        self.narrow_threshold_value.setText(f"{threshold:.2f}")
    
    def _on_sharp_angle_check_changed(self, checked):
        """尖锐角检查复选框状态变化时的处理"""
        # 启用或禁用阈值滑块
        self.sharp_angle_threshold_container.setVisible(checked)
    
    def _on_sharp_angle_threshold_slider_changed(self, value):
        """尖锐角阈值滑块值变化时的处理"""
        # 直接显示角度值
        self.sharp_angle_threshold_value.setText(f"{value}")
    
    def _on_tadpole_check_changed(self, checked):
        """蝌蚪形图斑检查开关状态变化时的处理"""
        # 显示/隐藏阈值容器
        self.tadpole_distance_threshold_container.setVisible(checked)
        self.tadpole_length_threshold_container.setVisible(checked)
    

    
    def _execute_check(self):
        """执行检查"""
        # 验证输入
        input_path = self.file_edit.text()
        
        # 检查是否选择了输入路径
        if not input_path:
            InfoBar.warning(
                title="警告",
                content="请选择文件/文件夹路径",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT
            )
            return
        
        # 检查项选择
        self.check_items = []
        check_params = {}
        if self.narrow_check.isChecked():
            self.check_items.append('narrow')
            # 从滑块获取狭长阈值（0-100 → 0.0-1.0）
            threshold = self.narrow_threshold_slider.value() / 100.0
            check_params['narrow_threshold'] = threshold
        if self.overlap_check.isChecked():
            self.check_items.append('overlap')
        if hasattr(self, 'roundabout_check') and self.roundabout_check.isChecked():
            self.check_items.append('roundabout')
        if hasattr(self, 'sharp_angle_check') and self.sharp_angle_check.isChecked():
            self.check_items.append('sharp_angle')
            # 从滑块获取尖锐角阈值
            sharp_angle_threshold = self.sharp_angle_threshold_slider.value()
            check_params['sharp_angle_threshold'] = sharp_angle_threshold
        if hasattr(self, 'tadpole_check') and self.tadpole_check.isChecked():
            self.check_items.append('tadpole')
            # 从SpinBox获取距离阈值
            distance_threshold = self.tadpole_distance_threshold_spinbox.value()
            check_params['tadpole_distance_threshold'] = distance_threshold
            # 从SpinBox获取长度阈值
            length_threshold = self.tadpole_length_threshold_spinbox.value()
            check_params['tadpole_length_threshold'] = length_threshold
        
        if not self.check_items:
            InfoBar.warning(
                title="警告",
                content="请至少选择一个检查项",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT
            )
            return
        
        # 初始化UI
        self.execute_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        
        # 显示进度组
        for i in range(self.contentLayout.count()):
            widget = self.contentLayout.itemAt(i).widget()
            if widget and widget.title() == "检查进度":
                widget.setVisible(True)
                break
        
        # 重置并显示进度条
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.progress_bar.setFormat("开始检查...")
        
        self.result_list.clear()
        self.result_gdfs.clear()
        self.save_btn.setEnabled(False)
        
        # 判断是否为批量检测
        if self.batch_check.isChecked():
            # 批量检测模式
            self._execute_batch_check(input_path, check_params)
        else:
            # 单文件检测模式
            # 确定图层名称
            layer_name = None
            is_gdb = input_path.endswith('.gdb')
            
            # 如果是GDB文件，检查是否选择了图层
            if is_gdb:
                if self.layer_combo.currentIndex() == -1:
                    InfoBar.warning(
                        title="警告",
                        content="请选择图层",
                        parent=self,
                        position=InfoBarPosition.TOP_RIGHT
                    )
                    self._reset_ui()
                    return
                # 使用currentText()获取当前选择的图层名称，更可靠
                layer_name = self.layer_combo.currentText()
            
            # 启动检查线程
            self.worker = FeatureCheckWorker(input_path, self.check_items, layer_name, check_params)
            self.worker.progress_updated.connect(lambda value: self._update_progress(value, "主检查进度"))
            self.worker.overlap_progress_updated.connect(lambda value: self._update_progress(value, "面面相叠检查进度"))
            self.worker.result_progress_updated.connect(lambda value: self._update_progress(value, "结果生成进度"))
            self.worker.check_completed.connect(self._on_check_completed)
            self.worker.error_occurred.connect(self._on_error)
            self.worker.start()
    
    def _execute_batch_check(self, folder_path, check_params):
        """执行批量检测"""
        # 遍历文件夹下所有shp和gdb文件
        file_list = []
        
        for root, dirs, files in os.walk(folder_path):
            # 处理gdb文件
            for dir_name in dirs:
                if dir_name.endswith('.gdb'):
                    gdb_path = os.path.join(root, dir_name)
                    # 获取gdb中的所有图层
                    try:
                        import fiona
                        with fiona.Env():
                            layer_names = fiona.listlayers(gdb_path)
                        
                        if not layer_names:
                            InfoBar.warning(
                                title="警告",
                                content=f"GDB文件 {gdb_path} 中没有找到任何图层",
                                parent=self,
                                position=InfoBarPosition.TOP_RIGHT
                            )
                            continue
                        
                        for layer_name in layer_names:
                            file_list.append((gdb_path, layer_name))
                    except Exception as e:
                        InfoBar.warning(
                            title="警告",
                            content=f"无法读取GDB文件 {gdb_path}: {str(e)}",
                            parent=self,
                            position=InfoBarPosition.TOP_RIGHT
                        )
            
            # 处理shp文件
            for file_name in files:
                if file_name.endswith('.shp'):
                    shp_path = os.path.join(root, file_name)
                    file_list.append((shp_path, None))
        
        if not file_list:
            InfoBar.warning(
                title="警告",
                content="文件夹中未找到SHP或GDB文件",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT
            )
            self._reset_ui()
            return
        
        # 初始化批量结果
        self.batch_results = []
        self.total_files = len(file_list)
        self.processed_files = 0
        
        # 显示文件处理进度
        self.progress_bar.setFormat(f"准备处理 {self.total_files} 个文件...")
        
        # 处理第一个文件
        self.current_file_index = 0
        self._process_next_file(file_list, check_params)
    
    def _cancel_check(self):
        """取消检查"""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        self._reset_ui()
    
    def _process_next_file(self, file_list, check_params):
        """处理下一个文件"""
        if self.current_file_index >= self.total_files:
            # 所有文件处理完成
            self._on_batch_check_completed()
            return
        
        # 获取当前要处理的文件
        input_path, layer_name = file_list[self.current_file_index]
        self.current_file_index += 1
        
        # 更新进度
        file_progress = int(self.current_file_index / self.total_files * 100)
        self.progress_bar.setValue(file_progress)
        
        # 显示当前处理的文件信息
        if layer_name:
            # GDB图层
            file_info = f"处理 {os.path.basename(input_path)} - {layer_name}"
        else:
            # SHP文件
            file_info = f"处理 {os.path.basename(input_path)}"
        
        self.progress_bar.setFormat(f"{file_info} ({self.current_file_index}/{self.total_files})")
        
        # 启动检查线程
        self.worker = FeatureCheckWorker(input_path, self.check_items, layer_name, check_params)
        self.worker.progress_updated.connect(lambda value: self._update_progress(value, f"{file_info} - 主检查进度"))
        self.worker.overlap_progress_updated.connect(lambda value: self._update_progress(value, f"{file_info} - 面面相叠检查进度"))
        self.worker.result_progress_updated.connect(lambda value: self._update_progress(value, f"{file_info} - 结果生成进度"))
        self.worker.check_completed.connect(lambda result_gdfs: self._on_file_check_completed(result_gdfs, input_path, layer_name, file_list, check_params))
        self.worker.error_occurred.connect(lambda error_msg: self._on_file_error(error_msg, input_path, layer_name, file_list, check_params))
        self.worker.start()
    
    def _on_file_check_completed(self, result_gdfs, input_path, layer_name, file_list, check_params):
        """单个文件检查完成"""
        # 保存当前文件的结果
        if layer_name:
            # GDB图层
            file_key = f"{os.path.basename(input_path)}_{layer_name}"
        else:
            # SHP文件
            file_key = os.path.basename(input_path)
        
        self.batch_results.append((file_key, result_gdfs))
        
        # 处理下一个文件
        self._process_next_file(file_list, check_params)
    
    def _on_file_error(self, error_msg, input_path, layer_name, file_list, check_params):
        """单个文件检查错误"""
        # 记录错误信息
        if layer_name:
            # GDB图层
            file_info = f"{os.path.basename(input_path)} - {layer_name}"
        else:
            # SHP文件
            file_info = os.path.basename(input_path)
        
        InfoBar.error(
            title="错误",
            content=f"处理 {file_info} 失败: {error_msg}",
            parent=self,
            position=InfoBarPosition.TOP_RIGHT
        )
        
        # 继续处理下一个文件
        self._process_next_file(file_list, check_params)
    
    def _on_batch_check_completed(self):
        """批量检查完成"""
        # 更新结果列表
        self.result_list.clear()
        
        total_errors = 0
        for file_key, result_gdfs in self.batch_results:
            if result_gdfs:
                item = QListWidgetItem(f"{file_key}:")
                item.setForeground(Qt.GlobalColor.blue)
                self.result_list.addItem(item)
                
                for check_type, gdf in result_gdfs.items():
                    count = len(gdf)
                    if count > 0:
                        total_errors += count
                        sub_item = QListWidgetItem(f"  - {check_type}: {count} 个要素")
                        self.result_list.addItem(sub_item)
            else:
                item = QListWidgetItem(f"{file_key}: 无异常要素")
                item.setForeground(Qt.GlobalColor.green)
                self.result_list.addItem(item)
        
        InfoBar.success(
            title="成功",
            content=f"批量检查完成，共处理 {self.total_files} 个文件，发现 {total_errors} 个异常要素",
            parent=self,
            position=InfoBarPosition.TOP_RIGHT
        )
        
        if total_errors > 0:
            self.save_btn.setEnabled(True)
        
        self._reset_ui()
    
    def _on_check_completed(self, result_gdfs):
        """单个文件检查完成"""
        self.result_gdfs = result_gdfs
        
        # 更新结果列表
        self.result_list.clear()
        for check_type, gdf in result_gdfs.items():
            count = len(gdf)
            item = QListWidgetItem(f"{check_type}: {count} 个要素")
            self.result_list.addItem(item)
        
        if not result_gdfs:
            InfoBar.success(
                title="成功",
                content="未发现异常要素",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT
            )
        else:
            InfoBar.success(
                title="成功",
                content="检查完成",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT
            )
            self.save_btn.setEnabled(True)
        
        self._reset_ui()
    
    def _on_error(self, error_msg):
        """单个文件错误处理"""
        InfoBar.error(
            title="错误",
            content=f"检查失败: {error_msg}",
            parent=self,
            position=InfoBarPosition.TOP_RIGHT
        )
        self._reset_ui()
    
    def _update_progress(self, value, progress_type):
        """动态更新进度条"""
        self.progress_bar.setValue(value)
        self.progress_bar.setFormat(f"{progress_type}: %p%")
    
    def _reset_ui(self):
        """重置UI"""
        self.execute_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        # 隐藏单一进度条
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p%")
        # 隐藏进度组
        for i in range(self.contentLayout.count()):
            widget = self.contentLayout.itemAt(i).widget()
            if widget and widget.title() == "检查进度":
                widget.setVisible(False)
                break
    
    def _save_results(self):
        """保存结果"""
        if self.batch_check.isChecked():
            # 批量检测结果保存
            if not self.batch_results:
                return
        else:
            # 单文件检测结果保存
            if not self.result_gdfs:
                return
        
        # 选择保存目录
        save_dir = QFileDialog.getExistingDirectory(self, "选择保存目录", ".")
        if not save_dir:
            return
        
        try:
            import datetime
            # 获取当前日期时间，格式：YYYYMMDD_HHMMSS
            current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if self.batch_check.isChecked():
                # 批量检测结果保存
                for file_key, result_gdfs in self.batch_results:
                    if result_gdfs:
                        # 为每个文件创建一个子目录
                        file_dir = os.path.join(save_dir, f"{file_key}_{current_time}")
                        os.makedirs(file_dir, exist_ok=True)
                        
                        for check_type, gdf in result_gdfs.items():
                            # 生成文件名，包含日期时间
                            output_name = f"{file_key}_{check_type}.shp"
                            output_path = os.path.join(file_dir, output_name)
                            
                            # 保留所有属性字段，包括阈值字段
                            gdf_copy = gdf.copy()
                            
                            # 删除可能存在的旧文件（解决文件被占用问题）
                            import glob
                            for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg']:
                                old_file = output_path.replace('.shp', ext)
                                if os.path.exists(old_file):
                                    try:
                                        os.remove(old_file)
                                    except:
                                        pass
                            
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
                            
                            # 清理字段名
                            gdf_cleaned = clean_field_names(gdf_copy)
                            # 保存为SHP文件，使用GBK编码处理中文文件名
                            gdf_cleaned.to_file(output_path, driver='ESRI Shapefile', encoding='gbk')
            else:
                # 单文件检测结果保存
                base_name = os.path.splitext(os.path.basename(self.file_edit.text()))[0]
                
                for check_type, gdf in self.result_gdfs.items():
                    # 生成文件名，包含日期时间
                    output_name = f"{base_name}_{check_type}_{current_time}.shp"
                    output_path = os.path.join(save_dir, output_name)
                    
                    # 保留所有属性字段，包括阈值字段
                    gdf_copy = gdf.copy()
                    
                    # 删除可能存在的旧文件（解决文件被占用问题）
                    import glob
                    for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg']:
                        old_file = output_path.replace('.shp', ext)
                        if os.path.exists(old_file):
                            try:
                                os.remove(old_file)
                            except:
                                pass
                    
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
                    
                    # 清理字段名
                    gdf_cleaned = clean_field_names(gdf_copy)
                    # 保存为SHP文件，使用GBK编码处理中文文件名
                    gdf_cleaned.to_file(output_path, driver='ESRI Shapefile', encoding='gbk')
            
            InfoBar.success(
                title="成功",
                content="结果已保存",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT
            )
            
        except Exception as e:
            InfoBar.error(
                title="错误",
                content=f"保存失败: {str(e)}",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT
            )
