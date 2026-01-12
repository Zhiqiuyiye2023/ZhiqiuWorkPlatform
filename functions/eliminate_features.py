# coding:utf-8
"""
面消除功能：通过将面与具有最大面积或最长公用边界的邻近面合并来消除面
"""

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QGroupBox, QWidget, QFrame
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from qfluentwidgets import LineEdit, PrimaryPushButton, StateToolTip, ComboBox, SpinBox, FluentIcon as FIF
from .base_function import BaseFunction
import os
import sys
import geopandas as gpd
import pandas as pd
from datetime import datetime
from shapely.geometry import Polygon, LineString, MultiPolygon
from shapely.ops import unary_union


class EliminateThread(QThread):
    """消除功能线程"""
    
    success = pyqtSignal(str)  # 成功信号，传递结果信息
    error = pyqtSignal(str)    # 错误信号，传递错误信息
    
    def __init__(self, input_path, output_path, method='max_area', area_threshold=0, exclude_layer_path=None, input_layer="", exclude_layer="", parent=None):
        """
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            method: 合并方法，'max_area' 或 'longest_boundary'
            area_threshold: 面积阈值，小于该值的面将被消除
            exclude_layer_path: 排除图层路径，该图层的面将被转换为线，与这些线相交的面将被排除
            input_layer: 输入图层名称，仅当输入文件为GDB时使用
            exclude_layer: 排除图层名称，仅当排除图层为GDB时使用
        """
        super().__init__(parent)
        self.input_path = input_path
        self.output_path = output_path
        self.method = method
        self.area_threshold = area_threshold
        self.exclude_layer_path = exclude_layer_path
        self.input_layer = input_layer
        self.exclude_layer = exclude_layer
    
    def run(self):
        """线程运行方法"""
        try:
            # 执行消除操作
            result = self._eliminate_features()
            if result:
                self.success.emit(f"处理完成！结果保存到: {result}")
            else:
                self.error.emit("消除操作执行失败，没有生成结果文件。")
        except Exception as e:
            self.error.emit(f"发生错误: {str(e)}")
    
    def _eliminate_features(self):
        """
        执行面消除操作
        通过将面与具有最大面积或最长公用边界的邻近面合并来消除面
        """
        # 读取输入文件，支持GDB图层
        if self.input_path.endswith('.gdb') and self.input_layer:
            gdf = gpd.read_file(self.input_path, layer=self.input_layer)
        else:
            gdf = gpd.read_file(self.input_path)
        
        # 确保是面要素
        if gdf.geometry.geom_type.iloc[0] not in ['Polygon', 'MultiPolygon']:
            raise Exception("输入文件必须包含面要素")
        
        # 计算每个面的面积
        gdf['area'] = gdf.geometry.area
        
        # 处理排除图层
        exclude_lines = []
        if self.exclude_layer_path:
            # 读取排除图层，支持GDB图层
            if self.exclude_layer_path.endswith('.gdb') and self.exclude_layer:
                exclude_gdf = gpd.read_file(self.exclude_layer_path, layer=self.exclude_layer)
            else:
                exclude_gdf = gpd.read_file(self.exclude_layer_path)
            
            # 确保只处理面要素
            if exclude_gdf.geometry.geom_type.iloc[0] not in ['Polygon', 'MultiPolygon']:
                print(f"警告：排除图层包含非面要素（{exclude_gdf.geometry.geom_type.iloc[0]}），将跳过处理")
            else:
                # 将排除图层的面转换为线
                for idx, row in exclude_gdf.iterrows():
                    # 获取面的边界
                    boundary = row.geometry.boundary
                    
                    # 根据边界类型添加到排除线列表
                    if boundary.geom_type == 'LineString':
                        exclude_lines.append(boundary)
                        print(f"  排除面 {idx} 转换为线（长度: {boundary.length:.2f}）")
                    elif boundary.geom_type == 'MultiLineString':
                        # 分解为多个线要素
                        for i, line in enumerate(boundary.geoms):
                            exclude_lines.append(line)
                            print(f"  排除面 {idx} 的子面 {i} 转换为线（长度: {line.length:.2f}）")
                    else:
                        # 跳过无法转换为线的情况
                        print(f"  排除面 {idx} 无法转换为线（边界类型: {boundary.geom_type}），将跳过")
        
        # 标识需要消除的面：仅根据面积阈值，不考虑排除区域
        # 排除线只影响边界合并，不影响面的标记
        gdf['to_eliminate'] = gdf['area'] <= self.area_threshold
        
        # 创建一个副本用于输出，初始包含所有面
        output_gdf = gdf.copy()
        
        # 保存原始几何形状用于邻近面查找
        original_geoms = gdf.geometry.copy()
        
        # 已合并的面索引集合
        merged = set()
        
        # 遍历所有需要消除的面
        to_eliminate_list = list(gdf[gdf['to_eliminate']].index)
        
        for i in to_eliminate_list:
            if i in merged:
                continue
            
            # 获取当前面的几何形状
            current_geom = original_geoms.loc[i]
            
            print(f"\n处理需要消除的面 {i} (面积: {gdf['area'].loc[i]:.6f})")
            
            # 查找所有可能的邻近面（排除已合并的面和需要消除的面）
            neighbors = []
            for j in gdf.index:
                if j == i or j in merged or gdf['to_eliminate'].loc[j]:
                    continue
                
                # 获取邻近面的信息
                neighbor_geom = original_geoms.loc[j]
                neighbor_area = gdf['area'].loc[j]
                
                # 检查是否相交
                if current_geom.intersects(neighbor_geom):
                    # 计算公用边界
                    shared_boundary = current_geom.intersection(neighbor_geom)
                    
                    # 检查公用边界是否有效
                    if shared_boundary.is_empty:
                        continue
                    
                    # 计算公用边界长度
                    boundary_length = shared_boundary.length
                    
                    # 检查当前面是否完全在邻近面内部
                    is_inside = current_geom.within(neighbor_geom)
                    
                    # 只有当公用边界长度大于1e-6或者当前面完全在邻近面内部时，才认为是有效的相邻面
                    if boundary_length < 1e-6 and not is_inside:
                        print(f"  面 {j} 与面 {i} 仅有点相交或边界长度过小（{boundary_length:.6f}），不视为有效相邻面")
                        continue
                    
                    # 检查公用边界是否与排除线相交 - 这是关键的排除线检查
                    can_merge = True
                    if exclude_lines:
                        # 如果当前面完全在邻近面内部，检查当前面的边界是否与排除线相交
                        if is_inside:
                            # 检查当前面的边界是否与排除线相交
                            for idx, exclude_line in enumerate(exclude_lines):
                                # 先检查两个边界框是否相交，快速判断
                                if not (current_geom.bounds[0] <= exclude_line.bounds[2] and \
                                        current_geom.bounds[2] >= exclude_line.bounds[0] and \
                                        current_geom.bounds[1] <= exclude_line.bounds[3] and \
                                        current_geom.bounds[3] >= exclude_line.bounds[1]):
                                    # 边界框不相交，直接跳过
                                    continue
                                
                                # 边界框相交，详细检查
                                if current_geom.boundary.intersects(exclude_line):
                                    # 计算交集长度
                                    intersection = current_geom.boundary.intersection(exclude_line)
                                    intersection_length = intersection.length
                                    
                                    # 只有当交集长度大于1e-6时，才认为真的相交，此时不能合并
                                    if intersection_length > 1e-6:
                                        print(f"  面 {j} 包含面 {i}，面 {i} 的边界与排除线 {idx} 相交（交集长度: {intersection_length:.6f}），不允许合并")
                                        can_merge = False
                                        break
                                    else:
                                        # 交集长度非常小，可能是数值精度问题，允许合并
                                        print(f"  面 {j} 包含面 {i}，面 {i} 的边界与排除线 {idx} 有数值精度相交（交集长度: {intersection_length:.6f}），允许合并")
                        else:
                            # 正常的相邻面情况，检查公用边界是否与排除线相交
                            for idx, exclude_line in enumerate(exclude_lines):
                                # 先检查两个边界框是否相交，快速判断
                                if not (shared_boundary.bounds[0] <= exclude_line.bounds[2] and \
                                        shared_boundary.bounds[2] >= exclude_line.bounds[0] and \
                                        shared_boundary.bounds[1] <= exclude_line.bounds[3] and \
                                        shared_boundary.bounds[3] >= exclude_line.bounds[1]):
                                    # 边界框不相交，直接跳过
                                    continue
                                
                                # 边界框相交，详细检查
                                if shared_boundary.intersects(exclude_line):
                                    # 计算交集长度
                                    intersection = shared_boundary.intersection(exclude_line)
                                    intersection_length = intersection.length
                                    
                                    # 只有当交集长度大于1e-6时，才认为真的相交，此时不能合并
                                    if intersection_length > 1e-6:
                                        print(f"  面 {j} 与面 {i} 的公用边界与排除线 {idx} 相交（交集长度: {intersection_length:.6f}），不允许合并")
                                        can_merge = False
                                        break
                                    else:
                                        # 交集长度非常小，可能是数值精度问题，允许合并
                                        print(f"  面 {j} 与面 {i} 的公用边界与排除线 {idx} 有数值精度相交（交集长度: {intersection_length:.6f}），允许合并")
                    
                    # 如果通过排除线检查，则添加到邻近列表
                    if can_merge:
                        neighbors.append((j, neighbor_area, boundary_length))
                        if is_inside:
                            print(f"  找到符合条件的邻近面 {j} (面积: {neighbor_area:.6f}，包含面 {i})")
                        else:
                            print(f"  找到符合条件的邻近面 {j} (面积: {neighbor_area:.6f}, 公用边界长度: {boundary_length:.6f})")
            
            if not neighbors:
                # 没有合适的邻近面，跳过（保留当前面）
                continue
            
            # 选择最佳邻近面
            best_neighbor = None
            if self.method == 'max_area':
                # 选择面积最大的邻近面
                best_neighbor = max(neighbors, key=lambda x: x[1])[0]
            else:  # longest_boundary
                # 选择具有最长公用边界的邻近面
                best_neighbor = max(neighbors, key=lambda x: x[2])[0]
            
            if best_neighbor is not None:
                try:
                    # 获取最佳邻近面的当前几何形状
                    best_neighbor_geom = output_gdf.geometry.loc[best_neighbor]
                    
                    # 先确保两个几何形状都是有效的
                    if not current_geom.is_valid:
                        current_geom = current_geom.buffer(0)
                    if not best_neighbor_geom.is_valid:
                        best_neighbor_geom = best_neighbor_geom.buffer(0)
                    
                    # 尝试多种合并方法，确保两个面真正融合
                    merged_geom = None
                    
                    # 方法1：使用unary_union
                    try:
                        merged_geom = unary_union([current_geom, best_neighbor_geom])
                    except Exception as e:
                        print(f"面 {i} 与面 {best_neighbor} 使用unary_union合并失败: {e}")
                    
                    # 方法2：如果方法1失败或结果是MultiPolygon，尝试buffer(0)修复
                    if merged_geom is None or isinstance(merged_geom, MultiPolygon):
                        try:
                            # 先合并，然后使用buffer(0)修复拓扑
                            combined = current_geom.union(best_neighbor_geom)
                            merged_geom = combined.buffer(0)
                        except Exception as e:
                            print(f"面 {i} 与面 {best_neighbor} 使用union+buffer(0)合并失败: {e}")
                    
                    # 方法3：如果仍然失败，尝试膨胀后再收缩
                    if merged_geom is None or isinstance(merged_geom, MultiPolygon):
                        try:
                            # 先膨胀一点，再收缩，强制融合
                            expanded1 = current_geom.buffer(0.001)
                            expanded2 = best_neighbor_geom.buffer(0.001)
                            combined = expanded1.union(expanded2)
                            merged_geom = combined.buffer(-0.001)
                        except Exception as e:
                            print(f"面 {i} 与面 {best_neighbor} 使用膨胀收缩合并失败: {e}")
                    
                    # 验证合并结果
                    if merged_geom is None:
                        print(f"面 {i} 与面 {best_neighbor} 所有合并方法都失败，跳过该合并")
                        continue
                    
                    # 确保合并结果有效
                    if not merged_geom.is_valid:
                        merged_geom = merged_geom.buffer(0)
                    
                    # 最终验证
                    if not merged_geom.is_valid:
                        print(f"面 {i} 与面 {best_neighbor} 合并后无法生成有效几何，跳过该合并")
                        continue
                    
                    # 确保合并结果是Polygon类型
                    if isinstance(merged_geom, MultiPolygon):
                        # 如果仍然是MultiPolygon，计算每个部件与原面的关系
                        best_part = None
                        max_intersection_area = 0
                        
                        for part in merged_geom.geoms:
                            # 计算该部件与原最佳邻近面的交集面积
                            intersection_area = part.intersection(best_neighbor_geom).area
                            if intersection_area > max_intersection_area:
                                max_intersection_area = intersection_area
                                best_part = part
                        
                        # 确保选择的部件包含原最佳邻近面的大部分
                        if best_part and best_part.area > best_neighbor_geom.area * 0.9:
                            merged_geom = best_part
                        else:
                            # 如果无法确定最佳部件，使用原始最佳邻近面
                            merged_geom = best_neighbor_geom
                            print(f"面 {i} 与面 {best_neighbor} 合并后无法确定有效部件，保留原始面")
                            continue
                    
                    # 更新最佳邻近面的几何形状和面积
                    output_gdf.loc[best_neighbor, 'geometry'] = merged_geom
                    output_gdf.loc[best_neighbor, 'area'] = merged_geom.area
                    
                    # 标记当前面为已合并
                    merged.add(i)
                    print(f"面 {i} 已成功合并到面 {best_neighbor}")
                except Exception as e:
                    print(f"面 {i} 与面 {best_neighbor} 合并时出错: {e}，跳过该合并")
                    continue
        
        # 创建最终输出：只移除成功合并的面
        if merged:
            final_output_gdf = output_gdf.drop(merged)
            print(f"成功合并了 {len(merged)} 个面")
        else:
            # 如果没有面被合并，直接返回原始输出
            final_output_gdf = output_gdf
            print("没有面被合并")
        
        # 重置索引
        final_output_gdf = final_output_gdf.reset_index(drop=True)
        
        # 清理字段名称
        from .矢量操作 import _clean_field_names
        final_output_gdf = _clean_field_names(final_output_gdf)
        
        # 保存结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 检查输出路径类型
        if self.output_path.endswith('.gdb'):
            # 输出到GDB文件
            # 从执行方法中获取输出图层名称
            from inspect import currentframe, getframeinfo
            frame = currentframe().f_back
            frame_info = getframeinfo(frame)
            
            # 尝试获取output_layer变量
            output_layer = frame.f_locals.get('output_layer', f'eliminated_{timestamp}')
            
            # 保存到GDB文件的指定图层
            final_output_gdf.to_file(
                self.output_path, 
                layer=output_layer, 
                driver='OpenFileGDB',
                encoding='utf-8'
            )
            output_file = f"{self.output_path}\{output_layer}"
        else:
            # 输出到SHP文件
            # 生成输出文件名
            base_name = os.path.basename(self.input_path)
            name, ext = os.path.splitext(base_name)
            output_file = os.path.join(self.output_path, f"{name}_eliminated.shp")
            
            # 保存文件
            final_output_gdf.to_file(output_file, encoding='utf-8')
        
        return output_file


class EliminateFeaturesFunction(BaseFunction):
    """面消除功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>"
            "通过将面与具有最大面积或最长公用边界的邻近面合并来消除面<br>"
            "支持选择合并方法，可选择排除特定图层"
        )
        super().__init__("面消除功能", description, parent)
        
        self._initUI()
        # 不使用默认执行按钮
        self.stateTooltip = None
        self._running = False
    
    def _initUI(self):
        """初始化界面"""
        # 创建输入矢量选择区域
        input_vector_group = QGroupBox("输入矢量数据", self)
        input_vector_layout = QVBoxLayout(input_vector_group)
        
        # 主矢量文件选择
        main_vector_layout = QHBoxLayout()
        main_vector_label = QLabel("主矢量文件：")
        self.main_vector_path = LineEdit(self)
        self.main_vector_path.setPlaceholderText("选择需要进行面消除的矢量文件")
        self.main_vector_path.setReadOnly(True)
        
        # 分别添加SHP和GDB文件选择按钮
        self.main_shp_btn = PrimaryPushButton("选择SHP", self, FIF.FOLDER)
        self.main_shp_btn.clicked.connect(lambda: self._select_vector_file(shp_only=True))
        self.main_shp_btn.setFixedWidth(120)
        
        self.main_gdb_btn = PrimaryPushButton("选择GDB", self, FIF.FOLDER)
        self.main_gdb_btn.clicked.connect(lambda: self._select_vector_file(gdb_only=True))
        self.main_gdb_btn.setFixedWidth(120)
        
        main_vector_layout.addWidget(main_vector_label)
        main_vector_layout.addWidget(self.main_vector_path, 1)
        main_vector_layout.addWidget(self.main_shp_btn)
        main_vector_layout.addWidget(self.main_gdb_btn)
        input_vector_layout.addLayout(main_vector_layout)
        
        # 主矢量图层选择（仅GDB文件显示）
        self.main_layer_layout = QHBoxLayout()
        main_layer_label = QLabel("主矢量图层：")
        self.main_layer_combo = ComboBox(self)
        self.main_layer_combo.setPlaceholderText("请先选择文件")
        self.main_layer_combo.setEnabled(False)
        
        self.main_layer_layout.addWidget(main_layer_label)
        self.main_layer_layout.addWidget(self.main_layer_combo, 1)
        # 默认隐藏主矢量图层选择
        for i in range(self.main_layer_layout.count()):
            widget = self.main_layer_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(False)
        input_vector_layout.addLayout(self.main_layer_layout)
        
        # 排除图层选择
        exclude_layer_layout = QHBoxLayout()
        exclude_layer_label = QLabel("排除图层：")
        self.exclude_vector_path = LineEdit(self)
        self.exclude_vector_path.setPlaceholderText("选择排除的面矢量图层（可选）")
        self.exclude_vector_path.setReadOnly(True)
        
        # 分别添加SHP和GDB文件选择按钮
        self.exclude_shp_btn = PrimaryPushButton("选择SHP", self, FIF.FOLDER)
        self.exclude_shp_btn.clicked.connect(lambda: self._select_exclude_file(shp_only=True))
        self.exclude_shp_btn.setFixedWidth(120)
        
        self.exclude_gdb_btn = PrimaryPushButton("选择GDB", self, FIF.FOLDER)
        self.exclude_gdb_btn.clicked.connect(lambda: self._select_exclude_file(gdb_only=True))
        self.exclude_gdb_btn.setFixedWidth(120)
        
        exclude_layer_layout.addWidget(exclude_layer_label)
        exclude_layer_layout.addWidget(self.exclude_vector_path, 1)
        exclude_layer_layout.addWidget(self.exclude_shp_btn)
        exclude_layer_layout.addWidget(self.exclude_gdb_btn)
        input_vector_layout.addLayout(exclude_layer_layout)
        
        # 排除矢量图层选择（仅GDB文件显示）
        self.exclude_layer_layout = QHBoxLayout()
        exclude_layer_label = QLabel("排除图层：")
        self.exclude_layer_combo = ComboBox(self)
        self.exclude_layer_combo.setPlaceholderText("请先选择文件")
        self.exclude_layer_combo.setEnabled(False)
        
        self.exclude_layer_layout.addWidget(exclude_layer_label)
        self.exclude_layer_layout.addWidget(self.exclude_layer_combo, 1)
        # 默认隐藏排除图层选择
        for i in range(self.exclude_layer_layout.count()):
            widget = self.exclude_layer_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(False)
        input_vector_layout.addLayout(self.exclude_layer_layout)
        
        # 消除参数设置区域
        param_group = QGroupBox("消除参数设置", self)
        param_layout = QVBoxLayout(param_group)
        
        # 面积阈值设置
        threshold_layout = QHBoxLayout()
        threshold_label = QLabel("面积阈值：")
        self.doubleSpinBoxThreshold = SpinBox(self)
        self.doubleSpinBoxThreshold.setFixedWidth(150)
        self.doubleSpinBoxThreshold.setRange(0, 1000000)
        self.doubleSpinBoxThreshold.setValue(1)
        self.doubleSpinBoxThreshold.setSingleStep(1)
        self.doubleSpinBoxThreshold.setSuffix(' 平方米')
        self.doubleSpinBoxThreshold.setToolTip('设置面积阈值，小于该值的面将被消除')
        self.doubleSpinBoxThreshold.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        threshold_layout.addWidget(threshold_label)
        threshold_layout.addWidget(self.doubleSpinBoxThreshold)
        threshold_layout.addStretch(1)
        param_layout.addLayout(threshold_layout)
        
        # 合并方法选择
        method_layout = QHBoxLayout()
        method_label = QLabel("合并方法：")
        self.comboMethod = ComboBox(self)
        self.comboMethod.addItems(["最大面积", "最长边界"])
        method_layout.addWidget(method_label)
        method_layout.addWidget(self.comboMethod)
        method_layout.addStretch(1)
        param_layout.addLayout(method_layout)
        
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
        
        self.outputFileBtn = PrimaryPushButton("选择输出路径", self, FIF.SAVE)
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
        
        self.output_gdb_btn = PrimaryPushButton("选择GDB", self, FIF.FOLDER)
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
        self.progress_text = QLabel("准备开始面消除...", self)
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
        
        # 添加执行按钮
        self.buttonExecute = PrimaryPushButton(self.tr('开始执行'), self, FIF.SEND)
        self.buttonExecute.clicked.connect(self.execute)
        self.contentLayout.addWidget(self.buttonExecute)
        self.contentLayout.addSpacing(20)
    
    def _select_vector_file(self, shp_only=False, gdb_only=False):
        """选择主矢量文件"""
        from PyQt6.QtWidgets import QFileDialog
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
                from qfluentwidgets import InfoBar, InfoBarPosition
                InfoBar.warning(
                    title="警告",
                    content="请选择GDB文件",
                    parent=self,
                    position=InfoBarPosition.TOP_RIGHT
                )
                return
            
            self.main_vector_path.setText(file_path)
            
            # 自动生成输出文件名
            self._auto_generate_output_path(file_path)
            
            # 更新图层列表
            self._update_layer_list(file_path, is_exclude=False)
    
    def _select_exclude_file(self, shp_only=False, gdb_only=False):
        """选择排除图层文件"""
        from PyQt6.QtWidgets import QFileDialog
        file_path = ""
        
        if shp_only:
            # 选择SHP文件
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择排除图层SHP文件", ".", "Shapefiles (*.shp)"
            )
        elif gdb_only:
            # 选择GDB文件（GDB是目录，所以使用getExistingDirectory）
            file_path = QFileDialog.getExistingDirectory(
                self, "选择排除图层GDB文件", "."
            )
        else:
            # 选择所有矢量文件
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择排除图层文件", ".", "矢量文件 (*.shp *.geojson *.json *.gpkg);;所有文件 (*)"
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
            
            self.exclude_vector_path.setText(file_path)
            
            # 更新图层列表
            self._update_layer_list(file_path, is_exclude=True)
    
    def _update_layer_list(self, file_path, is_exclude=False):
        """更新图层列表"""
        if is_exclude:
            combo = self.exclude_layer_combo
            layout = self.exclude_layer_layout
        else:
            combo = self.main_layer_combo
            layout = self.main_layer_layout
        
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
                import fiona
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
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "选择输出SHP文件", 
            "", 
            "SHP文件 (*.shp);;所有文件 (*.*)"
        )
        if file_path:
            # 确保文件扩展名是.shp
            if not file_path.lower().endswith('.shp'):
                file_path += '.shp'
            self.outputFilePath.setText(file_path)
    
    def _select_output_gdb(self):
        """选择输出GDB文件"""
        from PyQt6.QtWidgets import QFileDialog
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
    
    def _auto_generate_output_path(self, input_path):
        """自动生成输出文件名"""
        dir_name = os.path.dirname(input_path)
        base_name = os.path.basename(input_path)
        name, ext = os.path.splitext(base_name)
        output_path = os.path.join(dir_name, f"{name}_eliminated.shp")
        self.outputFilePath.setText(output_path)
    
    def validate(self) -> tuple[bool, str]:
        """验证输入"""
        # 检查输入文件
        if not self.main_vector_path.text():
            return False, "请选择主矢量文件"
        
        main_path = self.main_vector_path.text()
        # 验证主矢量文件
        if not (main_path.endswith('.shp') or main_path.endswith('.gdb')):
            return False, "请选择有效的SHP文件或GDB文件"
        
        # 验证GDB输入的图层选择
        if main_path.endswith('.gdb'):
            if not self.main_layer_combo.currentText():
                return False, "请选择主矢量的GDB图层"
        
        # 检查排除图层（如果提供）
        exclude_path = self.exclude_vector_path.text()
        if exclude_path:
            if not (exclude_path.endswith('.shp') or exclude_path.endswith('.gdb')):
                return False, "请选择有效的排除图层SHP文件或GDB文件"
            
            # 验证排除图层的GDB输入
            if exclude_path.endswith('.gdb'):
                if not self.exclude_layer_combo.currentText():
                    return False, "请选择排除图层的GDB图层"
        
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
            
            if not self.output_gdb_path.text().endswith('.gdb'):
                return False, "请选择有效的GDB文件"
            
            if not self.output_gdb_layer.text():
                return False, "请输入GDB输出图层名称"
        
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
        
        # 显示进度条
        self.progress_container.setVisible(True)
        
        # 获取输入参数
        main_vector_path = self.main_vector_path.text()
        main_layer = self.main_layer_combo.currentText() if main_vector_path.endswith('.gdb') else ""
        
        # 获取排除图层路径
        exclude_layer_path = self.exclude_vector_path.text() if self.exclude_vector_path.text() else None
        exclude_layer = self.exclude_layer_combo.currentText() if exclude_layer_path and exclude_layer_path.endswith('.gdb') else ""
        
        # 获取面积阈值
        area_threshold = self.doubleSpinBoxThreshold.value()
        
        # 获取合并方法
        method = 'max_area' if self.comboMethod.currentText() == "最大面积" else 'longest_boundary'
        
        # 获取输出设置
        output_type = self.output_type_combo.currentText()
        if output_type == "SHP文件":
            output_path = self.outputFilePath.text()
            # 对于SHP输出，output_dir是输出文件的目录
            output_dir = os.path.dirname(output_path)
        else:
            output_path = self.output_gdb_path.text()
            output_dir = output_path
            output_layer = self.output_gdb_layer.text()
        
        # 创建并启动消除线程
        self.eliminate_thread = EliminateThread(
            input_path=main_vector_path,
            output_path=output_dir,
            method=method,
            area_threshold=area_threshold,
            exclude_layer_path=exclude_layer_path,
            parent=self
        )
        
        # 连接信号
        self.eliminate_thread.success.connect(self._onEliminateSuccess)
        self.eliminate_thread.error.connect(self._onEliminateError)
        self.eliminate_thread.finished.connect(self._onEliminateFinished)
        
        # 启动线程
        self.eliminate_thread.start()
    
    def _onEliminateSuccess(self, message: str):
        """消除操作成功处理"""
        if hasattr(self, 'stateTooltip') and self.stateTooltip is not None:
            self.stateTooltip.setContent('处理完成 ✅')
            self.stateTooltip.setState(True)
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1000, self.stateTooltip.close)
        
        self.showSuccess(message)
    
    def _onEliminateError(self, message: str):
        """消除操作错误处理"""
        if hasattr(self, 'stateTooltip') and self.stateTooltip is not None:
            self.stateTooltip.setContent('处理失败 ❌')
            self.stateTooltip.setState(True)
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1000, self.stateTooltip.close)
        
        self.showError(message)
    
    def _onEliminateFinished(self):
        """消除线程结束处理"""
        self._running = False
