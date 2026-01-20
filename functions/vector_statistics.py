# coding:utf-8
"""
矢量统计功能模块
作者：知秋一叶
版本：0.0.1
"""

import sys
import os
from PyQt6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QLineEdit, QTableWidgetItem, 
    QFileDialog, QProgressBar, QLabel, QComboBox, QGroupBox, QFrame, QHeaderView
)
from qfluentwidgets import CheckBox
from PyQt6.QtCore import Qt
from qfluentwidgets import LineEdit, PushButton, BodyLabel, ComboBox, TableWidget
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction
import shapefile
import geopandas as gpd
import pandas as pd
import fnmatch


class VectorStatisticsFunction(BaseFunction):
    """
    矢量统计功能组件
    """
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>"+
            "矢量统计功能，支持统计矢量字段、总面积、字段信息、勾选面积、坐标系和编码类型"
        )
        super().__init__("矢量统计", description, parent)
        
        self._initUI()
        
    def _initUI(self):
        """初始化界面"""
        # 创建输入文件选择区域
        input_group = QGroupBox("输入矢量数据", self)
        input_layout = QVBoxLayout(input_group)
        
        # 文件选择布局
        file_layout = QHBoxLayout()
        file_label = QLabel("选择矢量文件：")
        self.file_path_input = LineEdit(self)
        self.file_path_input.setPlaceholderText("选择要统计的矢量文件")
        
        self.select_shp_btn = PushButton("选择SHP", self, FIF.FOLDER)
        self.select_shp_btn.setFixedWidth(140)
        self.select_gdb_btn = PushButton("选择GDB", self, FIF.FOLDER)
        self.select_gdb_btn.setFixedWidth(140)
        self.select_folder_btn = PushButton("选择文件夹", self, FIF.FOLDER)
        self.select_folder_btn.setFixedWidth(140)
        
        file_layout.addWidget(file_label)
        file_layout.addWidget(self.file_path_input, 1)
        file_layout.addWidget(self.select_shp_btn)
        file_layout.addWidget(self.select_gdb_btn)
        file_layout.addWidget(self.select_folder_btn)
        input_layout.addLayout(file_layout)
        
        # 图层选择布局（仅GDB文件显示）
        self.layer_layout = QHBoxLayout()
        layer_label = QLabel("图层选择：")
        self.layer_combo = ComboBox(self)
        self.layer_combo.setPlaceholderText("请先选择GDB文件")
        self.layer_combo.setEnabled(False)
        
        # 添加到表格按钮
        self.add_to_table_btn = PushButton("添加到表格", self, FIF.ADD)
        self.add_to_table_btn.setFixedWidth(120)
        self.add_to_table_btn.setEnabled(False)
        
        # 添加所有图层到表格按钮
        self.add_all_layers_btn = PushButton("添加所有图层到表格", self, FIF.ADD)
        self.add_all_layers_btn.setFixedWidth(200)
        self.add_all_layers_btn.setEnabled(False)
        
        self.layer_layout.addWidget(layer_label)
        self.layer_layout.addWidget(self.layer_combo, 1)
        self.layer_layout.addWidget(self.add_to_table_btn)
        self.layer_layout.addWidget(self.add_all_layers_btn)
        
        # 默认隐藏图层选择
        for i in range(self.layer_layout.count()):
            widget = self.layer_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(False)
        input_layout.addLayout(self.layer_layout)
        
        # 添加到内容布局
        self.contentLayout.addWidget(input_group)
        
        # 创建功能按钮区域
        function_group = QGroupBox("统计功能", self)
        function_layout = QVBoxLayout(function_group)
        
        # 功能按钮网格布局
        btn_grid_layout = QHBoxLayout()
        btn_grid_layout.setSpacing(10)
        
        self.stats_vector_btn = PushButton("统计矢量字段", self, FIF.CHECKBOX)
        self.stats_folder_btn = PushButton("统计属性", self, FIF.FOLDER)
        self.clear_table_btn = PushButton("清除列表", self, FIF.DELETE)
        self.delete_selected_btn = PushButton("选中删除", self, FIF.DELETE)
        
        # 设置按钮固定宽度
        self.stats_vector_btn.setFixedWidth(180)
        self.stats_folder_btn.setFixedWidth(180)
        self.clear_table_btn.setFixedWidth(180)
        self.delete_selected_btn.setFixedWidth(180)
        
        # 添加按钮到网格布局
        btn_grid_layout.addWidget(self.stats_vector_btn)
        btn_grid_layout.addWidget(self.stats_folder_btn)
        btn_grid_layout.addWidget(self.clear_table_btn)
        btn_grid_layout.addWidget(self.delete_selected_btn)
        btn_grid_layout.addStretch(1)
        
        function_layout.addLayout(btn_grid_layout)
        self.contentLayout.addWidget(function_group)
        
        # 创建结果显示区域
        result_group = QGroupBox("统计结果", self)
        result_layout = QVBoxLayout(result_group)
        
        # 表格显示区域
        self.table_widget = TableWidget(self)
        self.table_widget.setColumnCount(5)
        self.table_widget.setHorizontalHeaderLabels(["文件名/字段名", "数量/类型", "面积", "其他1", "其他2"])
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setFixedHeight(250)
        self.table_widget.setBorderVisible(True)
        result_layout.addWidget(self.table_widget)
        
        # 进度条
        self.progress_container = QFrame(self)
        self.progress_container.setFixedHeight(40)
        self.progress_layout = QVBoxLayout(self.progress_container)
        self.progress_layout.setContentsMargins(0, 0, 0, 0)
        self.progress_layout.setSpacing(5)
        
        # 进度文本
        self.progress_text = QLabel("", self)
        self.progress_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
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
        result_layout.addWidget(self.progress_container)
        
        self.contentLayout.addWidget(result_group)
        
        # 连接信号槽
        self.select_shp_btn.clicked.connect(lambda: self.select_vector_file(shp_only=True))
        self.select_gdb_btn.clicked.connect(lambda: self.select_vector_file(gdb_only=True))
        self.select_folder_btn.clicked.connect(self.select_vector_folder)
        self.stats_vector_btn.clicked.connect(self.stats_current_vector_fields)
        self.stats_folder_btn.clicked.connect(self.stats_folder_statistics)
        self.clear_table_btn.clicked.connect(self.clear_table)
        self.delete_selected_btn.clicked.connect(self.delete_selected_rows)
        self.add_to_table_btn.clicked.connect(self.add_to_table)
        self.add_all_layers_btn.clicked.connect(self.add_all_layers_to_table)
        
    def select_vector_file(self, shp_only=False, gdb_only=False):
        """选择矢量文件"""
        file_path = ""
        
        if shp_only:
            # 选择SHP文件
            file_path, _ = QFileDialog.getOpenFileName(
                self, 
                caption="选择矢量文件", 
                directory="D:/", 
                filter='Shapefile (*.shp)'
            )
        elif gdb_only:
            # 选择GDB文件（GDB是目录，所以使用getExistingDirectory）
            file_path = QFileDialog.getExistingDirectory(
                self, 
                caption="选择GDB文件", 
                directory="D:/"
            )
        else:
            # 选择所有矢量文件
            file_path, _ = QFileDialog.getOpenFileName(
                self, 
                caption="选择矢量文件", 
                directory="D:/", 
                filter='Shapefile (*.shp)'
            )
        
        if file_path:
            self.file_path_input.setText(file_path)
            # 如果是文件夹，直接添加其中的SHP文件到列表
            if os.path.isdir(file_path) and not file_path.lower().endswith('.gdb'):
                # 遍历文件夹中的所有SHP文件并添加到列表中
                self._add_folder_shps_to_list(file_path)
            else:
                # 更新图层列表
                self._update_layer_list(file_path)
            
    def select_vector_folder(self):
        """选择矢量文件夹"""
        folder_path = QFileDialog.getExistingDirectory(
            self, 
            caption="选择矢量文件夹", 
            directory="D:/"
        )
        if folder_path:
            self.file_path_input.setText(folder_path)
            # 隐藏图层选择（文件夹不需要图层选择）
            for i in range(self.layer_layout.count()):
                widget = self.layer_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(False)
            self.layer_combo.setPlaceholderText("文件夹无需选择图层")
            
            # 遍历文件夹中的所有SHP文件并添加到列表中
            self._add_folder_shps_to_list(folder_path)
            
    def _add_folder_shps_to_list(self, folder_path):
        """将文件夹中的所有SHP文件添加到列表中"""
        self.progress_container.setVisible(True)
        self.updateProgress(0, f"正在遍历文件夹 {os.path.basename(folder_path)}...")
        
        try:
            # 查找文件夹中的所有SHP文件
            shp_files = []
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.lower().endswith('.shp'):
                        shp_files.append(os.path.join(root, file))
            
            if not shp_files:
                self.showError("文件夹中未找到SHP文件")
                self.progress_container.setVisible(False)
                return
            
            # 清空现有表格并设置表头
            self.table_widget.clear()
            self.table_widget.setRowCount(len(shp_files))
            self.table_widget.setColumnCount(1)
            self.table_widget.setHorizontalHeaderLabels(["图层名"])
            self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            self.table_widget.setAlternatingRowColors(True)
            self.table_widget.setFixedHeight(250)
            self.table_widget.setBorderVisible(True)
            
            # 添加SHP文件到表格
            for i, shp_path in enumerate(shp_files):
                # 设置表格数据
                vector_name = os.path.basename(shp_path)
                self.table_widget.setItem(i, 0, QTableWidgetItem(vector_name))
                
                # 更新进度
                progress = int((i + 1) / len(shp_files) * 100)
                self.updateProgress(progress, f"正在添加SHP文件 {i+1}/{len(shp_files)}...")
            
            self.updateProgress(100, f"已添加 {len(shp_files)} 个SHP文件到列表")
            # 添加完成后隐藏进度容器
            self.progress_container.setVisible(False)
            
        except Exception as e:
            error_msg = f"遍历文件夹时出错: {e}"
            print(error_msg)
            self.showError(error_msg)
            # 出错时也要隐藏进度容器
            self.progress_container.setVisible(False)
    
    def _update_layer_list(self, file_path):
        """更新图层列表"""
        self.layer_combo.clear()
        self.layer_combo.setEnabled(False)
        self.add_to_table_btn.setEnabled(False)
        self.add_all_layers_btn.setEnabled(False)
        
        if file_path.lower().endswith('.gdb'):
            # 显示图层选择控件
            for i in range(self.layer_layout.count()):
                widget = self.layer_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(True)
            # 列出GDB中的所有图层
            try:
                import fiona
                with fiona.Env():
                    layers = fiona.listlayers(file_path)
                self.layer_combo.addItems(layers)
                self.layer_combo.setEnabled(True)
                self.add_to_table_btn.setEnabled(True)
                self.add_all_layers_btn.setEnabled(True)
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
            for i in range(self.layer_layout.count()):
                widget = self.layer_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(False)
            # SHP文件不需要图层选择
            self.layer_combo.setPlaceholderText("SHP文件无需选择图层")
            # 直接将SHP文件添加到列表中
            self._add_shp_to_list(file_path)
            
    def _add_shp_to_list(self, shp_path):
        """将SHP文件添加到列表中"""
        self.progress_container.setVisible(True)
        self.updateProgress(0, f"正在添加SHP文件 {os.path.basename(shp_path)} 到列表...")
        
        try:
            # 获取当前表格行数，用于插入新行
            current_row = self.table_widget.rowCount()
            
            # 如果表格为空，设置表头
            if current_row == 0:
                self.table_widget.setRowCount(1)
                self.table_widget.setColumnCount(1)
                self.table_widget.setHorizontalHeaderLabels(["图层名"])
                self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
                self.table_widget.setAlternatingRowColors(True)
                self.table_widget.setFixedHeight(250)
                self.table_widget.setBorderVisible(True)
            else:
                # 插入新行
                self.table_widget.insertRow(current_row)
            
            # 设置表格数据
            vector_name = os.path.basename(shp_path)
            self.table_widget.setItem(current_row, 0, QTableWidgetItem(vector_name))
            
            self.updateProgress(100, f"SHP文件 {vector_name} 添加完成")
            # 添加完成后隐藏进度容器
            self.progress_container.setVisible(False)
            
        except Exception as e:
            error_msg = f"添加SHP文件到列表时出错: {e}"
            print(error_msg)
            self.showError(error_msg)
            # 出错时也要隐藏进度容器
            self.progress_container.setVisible(False)
            
    def stats_current_vector_fields(self):
        """统计当前矢量字段：自动统计数字类字段的面积与个数"""
        self.table_widget.clear()
        vector_file = self.file_path_input.text()
        
        if not vector_file or not os.path.exists(vector_file):
            self.showError("请选择有效的矢量文件或文件夹")
            return
            
        try:
            self.progress_container.setVisible(True)
            self.updateProgress(0, "正在准备统计矢量字段...")
            
            # 初始化数据变量
            data = None
            
            # 如果是文件夹，获取第一个shp文件
            if os.path.isdir(vector_file):
                if vector_file.lower().endswith('.gdb'):
                    # 是GDB文件，需要图层名称
                    layer_name = self.layer_combo.currentText()
                    if not layer_name:
                        self.showError("请选择GDB文件中的图层")
                        return
                    # 读取GDB图层
                    data = gpd.read_file(vector_file, layer=layer_name)
                else:
                    # 普通文件夹，查找SHP文件
                    shp_files = []
                    for root, dirs, files in os.walk(vector_file):
                        for file in files:
                            if fnmatch.fnmatch(file, '*.shp'):
                                shp_files.append(os.path.join(root, file))
                    
                    if not shp_files:
                        self.showError("文件夹中未找到shapefile文件")
                        return
                        
                    # 使用第一个找到的shp文件
                    data = gpd.read_file(shp_files[0])
            else:
                # 是单个文件
                data = gpd.read_file(vector_file)
            
            # 获取所有字段
            fields = data.columns.tolist()
            
            # 过滤出数字类型字段
            numeric_fields = []
            for field in fields:
                try:
                    # 尝试转换为数值类型
                    pd.to_numeric(data[field])
                    numeric_fields.append(field)
                except:
                    continue
            
            # 设置表格
            self.table_widget.setRowCount(len(numeric_fields))
            self.table_widget.setColumnCount(5)
            self.table_widget.setHorizontalHeaderLabels(["字段名", "字段类型", "总数量", "面积总和", "大于0计数"])
            self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            self.table_widget.setAlternatingRowColors(True)
            self.table_widget.setFixedHeight(250)
            self.table_widget.setBorderVisible(True)
            
            self.updateProgress(50, "正在统计数字字段...")
            
            for i, field in enumerate(numeric_fields):
                # 字段名
                field_name_item = QTableWidgetItem(field)
                self.table_widget.setItem(i, 0, field_name_item)
                
                # 字段类型
                field_type = str(data[field].dtype)
                field_type_item = QTableWidgetItem(field_type)
                self.table_widget.setItem(i, 1, field_type_item)
                
                # 总数量
                total_count = len(data)
                total_count_item = QTableWidgetItem(str(total_count))
                self.table_widget.setItem(i, 2, total_count_item)
                
                # 面积总和
                try:
                    data[field] = pd.to_numeric(data[field])
                    area_sum = data[field].sum()
                    area_sum_item = QTableWidgetItem("%.2f" % area_sum)
                    self.table_widget.setItem(i, 3, area_sum_item)
                except:
                    area_sum_item = QTableWidgetItem("-")
                    self.table_widget.setItem(i, 3, area_sum_item)
                
                # 大于0计数
                try:
                    gt_zero_count = len(data[data[field] > 0])
                    gt_zero_item = QTableWidgetItem(str(gt_zero_count))
                    self.table_widget.setItem(i, 4, gt_zero_item)
                except:
                    gt_zero_item = QTableWidgetItem("-")
                    self.table_widget.setItem(i, 4, gt_zero_item)
                
            self.updateProgress(100, "矢量字段统计完成")
            # 统计完成后隐藏进度容器
            self.progress_container.setVisible(False)
            
        except Exception as e:
            error_msg = f"统计矢量字段时出错: {e}"
            print(error_msg)
            self.showError(error_msg)
            # 出错时也要隐藏进度容器
            self.progress_container.setVisible(False)
            
    def stats_folder_statistics(self):
        """统计属性：合并总面积、坐标系和编码类型统计"""
        folder_path = self.file_path_input.text()
        
        if not os.path.isdir(folder_path):
            self.showError("请选择有效的文件夹")
            return
            
        try:
            vector_files = []
            count = 0
            
            # 检查是否为GDB文件
            if folder_path.lower().endswith('.gdb'):
                # 是GDB文件，列出所有图层
                import fiona
                with fiona.Env():
                    layers = fiona.listlayers(folder_path)
                for layer in layers:
                    count += 1
                    vector_files.append((folder_path, f"{os.path.basename(folder_path)}/{layer}", layer))
            else:
                # 普通文件夹，查找SHP文件
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        if fnmatch.fnmatch(file, '*.shp'):
                            count += 1
                            vector_files.append((os.path.join(root, file), file, ""))
                        # 查找GDB文件
                        if file.lower().endswith('.gdb'):
                            gdb_path = os.path.join(root, file)
                            try:
                                import fiona
                                with fiona.Env():
                                    layers = fiona.listlayers(gdb_path)
                                for layer in layers:
                                    count += 1
                                    vector_files.append((gdb_path, f"{file}/{layer}", layer))
                            except Exception as e:
                                print(f"无法读取GDB文件 {gdb_path}: {e}")
                                continue
                        
            if count == 0:
                self.showError("文件夹中未找到shapefile文件或GDB文件")
                return
                
            self.table_widget.clear()
            self.table_widget.setRowCount(count)
            self.table_widget.setColumnCount(5)
            self.table_widget.setHorizontalHeaderLabels(["文件名", "总面积", "坐标系", "完整坐标系", "编码类型"])
            # 设置列宽模式为Interactive，防止自动拉伸
            self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            # 设置固定列宽，确保表格不会因内容过多而调整加宽
            self.table_widget.setColumnWidth(0, 150)  # 文件名列
            self.table_widget.setColumnWidth(1, 100)  # 总面积列
            self.table_widget.setColumnWidth(2, 100)  # 坐标系列
            self.table_widget.setColumnWidth(3, 200)  # 完整坐标系列
            self.table_widget.setColumnWidth(4, 80)   # 编码类型列
            self.table_widget.setAlternatingRowColors(True)
            self.table_widget.setFixedHeight(250)
            self.table_widget.setBorderVisible(True)
            
            self.progress_container.setVisible(True)
            self.updateProgress(0, "正在进行统计属性...")
            
            for i, (vector_path, vector_name, layer_name) in enumerate(vector_files):
                # 读取矢量文件
                try:
                    if vector_path.lower().endswith('.gdb') and layer_name:
                        gdf = gpd.read_file(vector_path, layer=layer_name)
                    else:
                        gdf = gpd.read_file(vector_path)
                        file = shapefile.Reader(vector_path)
                    
                    # 计算总面积
                    if gdf.crs and gdf.crs.is_geographic:
                        gdf = gdf.to_crs(gdf.estimate_utm_crs())
                    gdf['area'] = gdf.geometry.area
                    total_area = gdf['area'].sum()
                
                    # 获取坐标系
                    crs = gdf.crs
                    crs_str = str(crs)  # 完整坐标系
                    
                    def is_projcs_start(s):
                        return s.startswith("PROJCS[")
                    
                    if is_projcs_start(crs_str):
                        start_index = crs_str.find('PROJCS["') + len('PROJCS["')
                        end_index = crs_str.find('"', start_index)
                        crs_name = crs_str[start_index:end_index]
                    else:
                        crs_name = str(crs)  # 简单坐标系名称
                    
                    # 检测编码类型
                    def read_shapefile_with_encoding(file_path, encoding='utf-8'):
                        try:
                            gpd.read_file(file_path, encoding=encoding)
                            return encoding
                        except UnicodeDecodeError:
                            if encoding == 'utf-8':
                                return read_shapefile_with_encoding(file_path, encoding='gbk')
                            else:
                                raise
                    
                    if vector_path.lower().endswith('.gdb') and layer_name:
                        encoding_type = "utf-8"  # GDB文件默认使用utf-8编码
                    else:
                        encoding_type = read_shapefile_with_encoding(vector_path)
                    
                    # 设置表格数据
                    self.table_widget.setItem(i, 0, QTableWidgetItem(str(vector_name)))
                    self.table_widget.setItem(i, 1, QTableWidgetItem(str("%.2f" % total_area)))
                    self.table_widget.setItem(i, 2, QTableWidgetItem(crs_name))
                    self.table_widget.setItem(i, 3, QTableWidgetItem(crs_str))  # 完整坐标系
                    self.table_widget.setItem(i, 4, QTableWidgetItem(encoding_type))  # 编码类型
                    
                    # 更新进度条
                    progress = int((i + 1) / count * 100)
                    self.updateProgress(progress, f"正在统计文件 {i+1}/{count}...")
                except Exception as e:
                    print(f"处理文件 {vector_name} 时出错: {e}")
                    # 设置错误信息到表格
                    self.table_widget.setItem(i, 0, QTableWidgetItem(str(vector_name)))
                    self.table_widget.setItem(i, 1, QTableWidgetItem("错误"))
                    self.table_widget.setItem(i, 2, QTableWidgetItem("错误"))
                    self.table_widget.setItem(i, 3, QTableWidgetItem("错误"))
                    self.table_widget.setItem(i, 4, QTableWidgetItem("错误"))
                    
                    # 更新进度条
                    progress = int((i + 1) / count * 100)
                    self.updateProgress(progress, f"正在统计文件 {i+1}/{count}...")
                
            self.updateProgress(100, "统计属性完成")
            # 统计完成后隐藏进度容器
            self.progress_container.setVisible(False)
            
        except Exception as e:
                error_msg = f"统计属性时出错: {e}"
                print(error_msg)
                self.showError(error_msg)
                # 出错时也要隐藏进度容器
                self.progress_container.setVisible(False)
    
    def add_to_table(self):
        """将当前选中的GDB图层添加到表格"""
        gdb_path = self.file_path_input.text()
        layer_name = self.layer_combo.currentText()
        
        if not gdb_path or not layer_name:
            self.showError("请选择GDB文件和图层")
            return
        
        try:
            self.progress_container.setVisible(True)
            self.updateProgress(0, f"正在添加图层 {layer_name} 到表格...")
            
            # 获取当前表格行数，用于插入新行
            current_row = self.table_widget.rowCount()
            
            # 如果表格为空，设置表头
            if current_row == 0:
                self.table_widget.setRowCount(1)
                self.table_widget.setColumnCount(1)
                self.table_widget.setHorizontalHeaderLabels(["图层名"])
                self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
                self.table_widget.setAlternatingRowColors(True)
                self.table_widget.setFixedHeight(250)
                self.table_widget.setBorderVisible(True)
            else:
                # 插入新行
                self.table_widget.insertRow(current_row)
            
            # 设置表格数据
            vector_name = f"{os.path.basename(gdb_path)}/{layer_name}"
            self.table_widget.setItem(current_row, 0, QTableWidgetItem(vector_name))
            
            self.updateProgress(100, f"图层 {layer_name} 添加完成")
            # 添加完成后隐藏进度容器
            self.progress_container.setVisible(False)
            
        except Exception as e:
            error_msg = f"添加图层到表格时出错: {e}"
            print(error_msg)
            self.showError(error_msg)
            # 出错时也要隐藏进度容器
            self.progress_container.setVisible(False)
    
    def add_all_layers_to_table(self):
        """将GDB文件中的所有图层添加到表格"""
        gdb_path = self.file_path_input.text()
        
        if not gdb_path.lower().endswith('.gdb'):
            self.showError("请选择有效的GDB文件")
            return
        
        try:
            # 列出所有图层
            import fiona
            with fiona.Env():
                layers = fiona.listlayers(gdb_path)
            
            if not layers:
                self.showError("GDB文件中没有图层")
                return
            
            self.progress_container.setVisible(True)
            self.updateProgress(0, "正在添加所有图层到表格...")
            
            # 清空表格并设置表头
            self.table_widget.clear()
            self.table_widget.setRowCount(len(layers))
            self.table_widget.setColumnCount(1)
            self.table_widget.setHorizontalHeaderLabels(["图层名"])
            self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            self.table_widget.setAlternatingRowColors(True)
            self.table_widget.setFixedHeight(250)
            self.table_widget.setBorderVisible(True)
            
            for i, layer_name in enumerate(layers):
                # 设置表格数据
                vector_name = f"{os.path.basename(gdb_path)}/{layer_name}"
                self.table_widget.setItem(i, 0, QTableWidgetItem(vector_name))
                
                # 更新进度条
                progress = int((i + 1) / len(layers) * 100)
                self.updateProgress(progress, f"正在添加图层 {i+1}/{len(layers)}...")
            
            self.updateProgress(100, "所有图层添加完成")
            # 添加完成后隐藏进度容器
            self.progress_container.setVisible(False)
            
        except Exception as e:
                error_msg = f"添加所有图层到表格时出错: {e}"
                print(error_msg)
                self.showError(error_msg)
                # 出错时也要隐藏进度容器
                self.progress_container.setVisible(False)
    
    def clear_table(self):
        """清除表格内容"""
        # 清空表格
        self.table_widget.clear()
        # 重置表格状态
        self.table_widget.setRowCount(0)
        self.table_widget.setColumnCount(0)
        # 隐藏进度容器
        self.progress_container.setVisible(False)
    
    def delete_selected_rows(self):
        """删除选中的行"""
        # 获取选中的行索引
        selected_rows = set()
        for index in self.table_widget.selectedIndexes():
            selected_rows.add(index.row())
        
        if not selected_rows:
            from qfluentwidgets import InfoBar, InfoBarPosition
            InfoBar.warning(
                title="警告",
                content="请先选择要删除的行",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT
            )
            return
        
        # 按行号从大到小删除，避免索引混乱
        for row in sorted(selected_rows, reverse=True):
            self.table_widget.removeRow(row)
        
        # 如果表格为空，重置表格状态
        if self.table_widget.rowCount() == 0:
            self.table_widget.clear()
            self.table_widget.setColumnCount(0)
