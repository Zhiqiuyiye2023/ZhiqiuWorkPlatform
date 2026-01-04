# coding:utf-8
"""
面消除功能：通过将面与具有最大面积或最长公用边界的邻近面合并来消除面
"""

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QComboBox, QDoubleSpinBox
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from qfluentwidgets import LineEdit, PrimaryPushButton, StateToolTip, FluentIcon as FIF
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
    
    def __init__(self, input_path, output_path, method='max_area', area_threshold=0, exclude_layer_path=None, parent=None):
        """
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            method: 合并方法，'max_area' 或 'longest_boundary'
            area_threshold: 面积阈值，小于该值的面将被消除
            exclude_layer_path: 排除图层路径，该图层的面将被转换为线，与这些线相交的面将被排除
        """
        super().__init__(parent)
        self.input_path = input_path
        self.output_path = output_path
        self.method = method
        self.area_threshold = area_threshold
        self.exclude_layer_path = exclude_layer_path
    
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
        # 读取输入文件
        gdf = gpd.read_file(self.input_path)
        
        # 确保是面要素
        if gdf.geometry.geom_type.iloc[0] not in ['Polygon', 'MultiPolygon']:
            raise Exception("输入文件必须包含面要素")
        
        # 计算每个面的面积
        gdf['area'] = gdf.geometry.area
        
        # 处理排除图层
        exclude_lines = []
        if self.exclude_layer_path:
            # 读取排除图层
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
        output_file = os.path.join(self.output_path, f'eliminated_{timestamp}.shp')
        
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
        # 第一行：输入文件选择
        hBoxLayout1 = QHBoxLayout()
        self.labelInput = QLabel("输入文件：")
        self.lineEditInput = LineEdit(self)
        self.lineEditInput.setPlaceholderText("请输入要处理的SHP文件路径")
        self.buttonBrowseInput = PrimaryPushButton(self.tr('浏览'), self, FIF.FOLDER)
        self.buttonBrowseInput.clicked.connect(self._browseInput)
        hBoxLayout1.addWidget(self.labelInput)
        hBoxLayout1.addWidget(self.lineEditInput)
        hBoxLayout1.addWidget(self.buttonBrowseInput)
        self.contentLayout.addLayout(hBoxLayout1)
        
        # 第二行：面积阈值输入
        hBoxLayout3 = QHBoxLayout()
        self.labelThreshold = QLabel("面积阈值：")
        self.doubleSpinBoxThreshold = QDoubleSpinBox(self)
        self.doubleSpinBoxThreshold.setMinimum(0.0)
        self.doubleSpinBoxThreshold.setMaximum(1000000.0)
        self.doubleSpinBoxThreshold.setSingleStep(0.1)
        self.doubleSpinBoxThreshold.setValue(1.0)
        self.doubleSpinBoxThreshold.setDecimals(6)
        hBoxLayout3.addWidget(self.labelThreshold)
        hBoxLayout3.addWidget(self.doubleSpinBoxThreshold)
        hBoxLayout3.addStretch(1)
        self.contentLayout.addLayout(hBoxLayout3)
        
        # 第三行：排除图层选择
        hBoxLayout4 = QHBoxLayout()
        self.labelExclude = QLabel("排除图层：")
        self.lineEditExclude = LineEdit(self)
        self.lineEditExclude.setPlaceholderText("请选择排除的面矢量图层（可选）")
        self.buttonBrowseExclude = PrimaryPushButton(self.tr('浏览'), self, FIF.FOLDER)
        self.buttonBrowseExclude.clicked.connect(self._browseExclude)
        hBoxLayout4.addWidget(self.labelExclude)
        hBoxLayout4.addWidget(self.lineEditExclude)
        hBoxLayout4.addWidget(self.buttonBrowseExclude)
        self.contentLayout.addLayout(hBoxLayout4)
        
        # 第四行：合并方法选择
        hBoxLayout5 = QHBoxLayout()
        self.labelMethod = QLabel("合并方法：")
        self.comboMethod = QComboBox(self)
        self.comboMethod.addItems(["最大面积", "最长边界"])
        hBoxLayout5.addWidget(self.labelMethod)
        hBoxLayout5.addWidget(self.comboMethod)
        hBoxLayout5.addStretch(1)
        self.contentLayout.addLayout(hBoxLayout5)
        
        # 第五行：开始执行按钮
        hBoxLayout6 = QHBoxLayout()
        self.buttonExecute = PrimaryPushButton(self.tr('开始执行'), self, FIF.SEND)
        self.buttonExecute.clicked.connect(self.execute)
        hBoxLayout6.addWidget(self.buttonExecute)
        hBoxLayout6.addStretch(1)
        self.contentLayout.addLayout(hBoxLayout6)
    
    def _browseInput(self):
        """浏览输入文件"""
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择要处理的SHP文件", 
            "", 
            "SHP文件 (*.shp);;所有文件 (*.*)"
        )
        if file_path:
            self.lineEditInput.setText(file_path)
    
    def _browseOutput(self):
        """浏览输出路径"""
        from PyQt6.QtWidgets import QFileDialog
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if dir_path:
            self.lineEditOutput.setText(dir_path)
    
    def _browseExclude(self):
        """浏览排除图层文件"""
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择排除的面矢量图层", 
            "", 
            "SHP文件 (*.shp);;所有文件 (*.*)"
        )
        if file_path:
            self.lineEditExclude.setText(file_path)
    
    def validate(self) -> tuple[bool, str]:
        """验证输入"""
        # 检查输入文件
        if not self.lineEditInput.text() or not self.lineEditInput.text().endswith('.shp'):
            return False, "请选择有效的SHP文件"
        
        # 检查排除图层（如果提供）
        exclude_path = self.lineEditExclude.text()
        if exclude_path and not exclude_path.endswith('.shp'):
            return False, "请选择有效的排除图层SHP文件"
        
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
        
        # 获取输入参数
        input_path = self.lineEditInput.text()
        
        # 将输出路径设置为输入文件的当前路径
        output_path = os.path.dirname(input_path)
        
        # 获取面积阈值
        area_threshold = self.doubleSpinBoxThreshold.value()
        
        # 获取排除图层路径
        exclude_layer_path = self.lineEditExclude.text() if self.lineEditExclude.text() else None
        
        # 获取合并方法
        method = 'max_area' if self.comboMethod.currentText() == "最大面积" else 'longest_boundary'
        
        # 创建并启动消除线程
        self.eliminate_thread = EliminateThread(
            input_path=input_path,
            output_path=output_path,
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
