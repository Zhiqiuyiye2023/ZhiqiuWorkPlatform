# coding:utf-8
"""
空间挂接字段功能模块
执行空间挂接操作，将一个要素的字段信息挂接到另一个要素，基于重叠面积阈值
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


class SpatialJoinFieldsFunction(BaseFunction):
    """空间挂接字段功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>"
            "执行空间挂接操作，将要素A的字段信息挂接到要素B，基于重叠面积阈值"
        )
        super().__init__("空间挂接字段", description, parent)
        
        # 初始化UI
        self._initUI()
        
        # 添加执行按钮
        self.execute_btn = self.addExecuteButton("开始挂接", self.execute)
    
    def _initUI(self):
        """初始化界面控件"""
        # 创建输入矢量选择区域
        input_vector_group = QGroupBox("输入矢量数据", self)
        input_vector_layout = QVBoxLayout(input_vector_group)
        
        # 要素A文件选择
        feature_a_layout = QHBoxLayout()
        feature_a_label = QLabel("要素A（源数据）：")
        self.feature_a_path = LineEdit(self)
        self.feature_a_path.setPlaceholderText("选择包含要挂接属性的矢量文件")
        self.feature_a_path.setReadOnly(True)
        
        # 分别添加SHP和GDB文件选择按钮
        self.feature_a_shp_btn = PushButton("选择SHP", self, FIF.FOLDER)
        self.feature_a_shp_btn.clicked.connect(lambda: self._selectFeatureFile("A", shp_only=True))
        self.feature_a_shp_btn.setFixedWidth(120)
        
        self.feature_a_gdb_btn = PushButton("选择GDB", self, FIF.FOLDER)
        self.feature_a_gdb_btn.clicked.connect(lambda: self._selectFeatureFile("A", gdb_only=True))
        self.feature_a_gdb_btn.setFixedWidth(120)
        
        feature_a_layout.addWidget(feature_a_label)
        feature_a_layout.addWidget(self.feature_a_path, 1)
        feature_a_layout.addWidget(self.feature_a_shp_btn)
        feature_a_layout.addWidget(self.feature_a_gdb_btn)
        input_vector_layout.addLayout(feature_a_layout)
        
        # 要素A图层选择（仅GDB文件显示）
        self.feature_a_layer_layout = QHBoxLayout()
        feature_a_layer_label = QLabel("要素A图层：")
        self.feature_a_layer_combo = ComboBox(self)
        self.feature_a_layer_combo.setPlaceholderText("请先选择文件")
        self.feature_a_layer_combo.setEnabled(False)
        
        self.feature_a_layer_layout.addWidget(feature_a_layer_label)
        self.feature_a_layer_layout.addWidget(self.feature_a_layer_combo, 1)
        # 默认隐藏要素A图层选择
        for i in range(self.feature_a_layer_layout.count()):
            widget = self.feature_a_layer_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(False)
        input_vector_layout.addLayout(self.feature_a_layer_layout)
        
        # 要素B文件选择
        feature_b_layout = QHBoxLayout()
        feature_b_label = QLabel("要素B（目标数据）：")
        self.feature_b_path = LineEdit(self)
        self.feature_b_path.setPlaceholderText("选择要挂接属性的目标矢量文件")
        self.feature_b_path.setReadOnly(True)
        
        # 分别添加SHP和GDB文件选择按钮
        self.feature_b_shp_btn = PushButton("选择SHP", self, FIF.FOLDER)
        self.feature_b_shp_btn.clicked.connect(lambda: self._selectFeatureFile("B", shp_only=True))
        self.feature_b_shp_btn.setFixedWidth(120)
        
        self.feature_b_gdb_btn = PushButton("选择GDB", self, FIF.FOLDER)
        self.feature_b_gdb_btn.clicked.connect(lambda: self._selectFeatureFile("B", gdb_only=True))
        self.feature_b_gdb_btn.setFixedWidth(120)
        
        feature_b_layout.addWidget(feature_b_label)
        feature_b_layout.addWidget(self.feature_b_path, 1)
        feature_b_layout.addWidget(self.feature_b_shp_btn)
        feature_b_layout.addWidget(self.feature_b_gdb_btn)
        input_vector_layout.addLayout(feature_b_layout)
        
        # 要素B图层选择（仅GDB文件显示）
        self.feature_b_layer_layout = QHBoxLayout()
        feature_b_layer_label = QLabel("要素B图层：")
        self.feature_b_layer_combo = ComboBox(self)
        self.feature_b_layer_combo.setPlaceholderText("请先选择文件")
        self.feature_b_layer_combo.setEnabled(False)
        
        self.feature_b_layer_layout.addWidget(feature_b_layer_label)
        self.feature_b_layer_layout.addWidget(self.feature_b_layer_combo, 1)
        # 默认隐藏要素B图层选择
        for i in range(self.feature_b_layer_layout.count()):
            widget = self.feature_b_layer_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(False)
        input_vector_layout.addLayout(self.feature_b_layer_layout)
        
        # 挂接参数设置区域
        param_group = QGroupBox("挂接参数设置", self)
        param_layout = QVBoxLayout(param_group)
        
        # 重叠面积阈值
        threshold_layout = QHBoxLayout()
        threshold_label = QLabel("重叠面积阈值：")
        self.threshold_spinbox = SpinBox(self)
        self.threshold_spinbox.setValue(1)
        self.threshold_spinbox.setMinimum(0)
        self.threshold_spinbox.setMaximum(1000000)
        threshold_unit_label = QLabel("当重叠面积达到或超过此值时，挂接属性")
        
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
        self.progress_text = QLabel("准备开始挂接...", self)
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
                self, f"选择要素{feature_type}SHP文件", ".", "Shapefiles (*.shp)"
            )
        elif gdb_only:
            # 选择GDB文件（GDB是目录，所以使用getExistingDirectory）
            file_path = QFileDialog.getExistingDirectory(
                self, f"选择要素{feature_type}GDB文件", "."
            )
        else:
            # 选择所有矢量文件
            file_path, _ = QFileDialog.getOpenFileName(
                self, f"选择要素{feature_type}文件", ".", "矢量文件 (*.shp *.geojson *.json *.gpkg);;所有文件 (*)"
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
            
            if feature_type == "A":
                self.feature_a_path.setText(file_path)
                # 自动生成输出文件名
                self._autoGenerateOutputPath(file_path)
                # 更新图层列表
                self._update_feature_layer_list("A", file_path)
            else:
                self.feature_b_path.setText(file_path)
                # 更新图层列表
                self._update_feature_layer_list("B", file_path)
    
    def _update_feature_layer_list(self, feature_type, file_path):
        """更新要素图层列表"""
        if feature_type == "A":
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
    
    def _autoGenerateOutputPath(self, input_path):
        """自动生成输出文件名"""
        dir_name = os.path.dirname(input_path)
        base_name = os.path.basename(input_path)
        name, ext = os.path.splitext(base_name)
        output_path = os.path.join(dir_name, f"{name}_joined.shp")
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
    
    def updateProgress(self, percent: int, status: str = ""):
        """更新进度条和进度文本"""
        # 更新进度文本
        self.progress_text.setText(f"正在挂接... {percent}%")
        
        # 更新进度条样式
        progress_ratio = percent / 100.0
        style = """
            QFrame {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #0078D4, stop:"" + str(progress_ratio) + "" #0078D4, 
                    stop:"" + str(progress_ratio) + "" #e0e0e0, stop:1 #e0e0e0);
                border-radius: 2px;
            }
        """
        self.progress_bar.setStyleSheet(style)
    
    def reset_progress(self):
        """重置进度条"""
        self.progress_container.setVisible(False)
        self.progress_text.setText("准备开始挂接...")
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
            return False, "请选择要素A文件"
        
        if not self.feature_b_path.text():
            return False, "请选择要素B文件"
        
        if not os.path.exists(self.feature_a_path.text()):
            return False, "要素A文件不存在"
        
        if not os.path.exists(self.feature_b_path.text()):
            return False, "要素B文件不存在"
        
        # 验证GDB输入的图层选择
        if self.feature_a_path.text().lower().endswith('.gdb'):
            if not self.feature_a_layer_combo.currentText():
                return False, "请选择要素A的GDB图层"
        
        if self.feature_b_path.text().lower().endswith('.gdb'):
            if not self.feature_b_layer_combo.currentText():
                return False, "请选择要素B的GDB图层"
        
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
    
    def execute(self):
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
        threshold = self.threshold_spinbox.value()
        
        # 获取图层名称
        feature_a_layer = self.feature_a_layer_combo.currentText() if feature_a_path.lower().endswith('.gdb') else ""
        feature_b_layer = self.feature_b_layer_combo.currentText() if feature_b_path.lower().endswith('.gdb') else ""
        
        # 获取输出设置
        output_type = self.output_type_combo.currentText()
        if output_type == "SHP文件":
            output_path = self.outputFilePath.text()
            output_layer = ""
        else:
            output_path = self.output_gdb_path.text()
            output_layer = self.output_gdb_layer.text()
        
        print(f"开始执行空间挂接...")
        print(f"要素A: {feature_a_path}")
        print(f"要素A图层: {feature_a_layer}")
        print(f"要素B: {feature_b_path}")
        print(f"要素B图层: {feature_b_layer}")
        print(f"阈值: {threshold}")
        print(f"输出类型: {output_type}")
        print(f"输出路径: {output_path}")
        print(f"输出图层: {output_layer}")
        
        # 3. 显示进度条
        self.progress_container.setVisible(True)
        self.updateProgress(0)
        
        # 4. 显示进度
        self.showProgress("正在挂接...")
        
        # 5. 在线程中执行处理
        def run_process():
            try:
                # 调用挂接方法
                result = self._spatialJoinFields(feature_a_path, feature_a_layer, feature_b_path, feature_b_layer, threshold, output_path, output_type, output_layer)
                
                # 发送成功信号，在主线程中显示成功消息
                self.show_success_signal.emit(f"挂接完成！\n{result}")
                print(f"挂接成功: {result}")
                
                # 重置进度条
                self.reset_progress()
                
            except Exception as e:
                # 捕获并发送错误信号，在主线程中显示错误消息
                import traceback
                error_msg = f"挂接失败: {str(e)}\n\n{traceback.format_exc()}"
                self.show_error_signal.emit(error_msg)
                print(f"挂接失败: {str(e)}")
                print(f"详细错误: {traceback.format_exc()}")
                
                # 重置进度条
                self.reset_progress()
        
        # 启动线程
        threading.Thread(target=run_process, daemon=True).start()
    
    def _spatialJoinFields(self, feature_a_path: str, feature_a_layer: str, feature_b_path: str, feature_b_layer: str, threshold: int, output_path: str, output_type: str, output_layer: str) -> str:
        """
        执行空间挂接操作
        
        参数:
            feature_a_path: 要素A路径
            feature_a_layer: 要素A图层名称（仅GDB需要）
            feature_b_path: 要素B路径
            feature_b_layer: 要素B图层名称（仅GDB需要）
            threshold: 重叠面积阈值
            output_path: 输出文件路径
            output_type: 输出类型（"SHP文件"或"GDB图层"）
            output_layer: 输出图层名称（仅GDB输出需要）
            
        返回:
            处理结果描述
        """
        # 读取要素A和要素B
        self.update_progress_signal.emit(20, "正在读取要素数据...")
        # 根据文件类型选择读取方式
        if feature_a_path.lower().endswith('.gdb') and feature_a_layer:
            feature_a = gpd.read_file(feature_a_path, layer=feature_a_layer)
        else:
            feature_a = gpd.read_file(feature_a_path)
            
        if feature_b_path.lower().endswith('.gdb') and feature_b_layer:
            feature_b = gpd.read_file(feature_b_path, layer=feature_b_layer)
        else:
            feature_b = gpd.read_file(feature_b_path)
        
        self.update_progress_signal.emit(30, "正在检查坐标系...")
        # 检查坐标系是否一致
        if feature_a.crs != feature_b.crs:
            feature_b = feature_b.to_crs(feature_a.crs)
        
        self.update_progress_signal.emit(40, "正在执行初始相交连接...")
        # 步骤1: 先执行相交连接，获取所有可能的匹配对（以要素A为主体）
        joined_gdf = gpd.sjoin(feature_a, feature_b, how="left", predicate="intersects")
        
        self.update_progress_signal.emit(50, "正在计算匹配对的重叠面积...")
        # 步骤2: 计算每对匹配要素的重叠面积
        overlap_areas = []
        for idx, row in joined_gdf.iterrows():
            # 获取要素A的几何体
            a_geom = row['geometry']
            # 获取对应的要素B的几何体（如果存在）
            if not pd.isna(row['index_right']):
                b_idx = int(row['index_right'])
                b_geom = feature_b.iloc[b_idx]['geometry']
                
                # 计算重叠面积
                overlap_area = a_geom.intersection(b_geom).area
            else:
                overlap_area = 0
            
            overlap_areas.append(overlap_area)
        
        # 添加重叠面积列
        joined_gdf = joined_gdf.copy()
        joined_gdf.loc[:, 'overlap_area'] = overlap_areas
        
        self.update_progress_signal.emit(60, f"正在根据重叠面积阈值({threshold})筛选匹配对...")
        # 步骤3: 根据重叠面积阈值筛选匹配对
        filtered_gdf = joined_gdf[joined_gdf['overlap_area'] >= threshold]
        
        self.update_progress_signal.emit(70, "正在合并筛选结果与原始要素A...")
        # 步骤4: 处理原始要素A，确保所有要素都被保留
        # 获取匹配成功的要素A的索引
        matched_indices = set(filtered_gdf.index)
        
        # 分离匹配成功和未匹配成功的要素
        matched_a = filtered_gdf.copy()
        unmatched_a = feature_a[~feature_a.index.isin(matched_indices)].copy()
        
        # 将未匹配成功的要素转换为与matched_a相同的列结构
        if not unmatched_a.empty:
            for col in matched_a.columns:
                if col not in unmatched_a.columns and col != 'geometry':
                    # 使用更安全的方式设置列值，避免空DataFrame的问题
                    unmatched_a[col] = None
        else:
            # 如果unmatched_a为空，直接创建一个具有正确列结构的空GeoDataFrame
            unmatched_a = gpd.GeoDataFrame(columns=matched_a.columns, crs=feature_a.crs)
        
        # 重新排列列顺序，确保一致
        unmatched_a = unmatched_a[matched_a.columns].copy()
        
        # 合并匹配和未匹配的要素（确保所有要素A都被保留）
        final_gdf = gpd.GeoDataFrame(pd.concat([matched_a, unmatched_a], ignore_index=True), crs=feature_a.crs)
        
        # 移除overlap_area和index_right列，因为不需要保存到最终结果
        final_gdf = final_gdf.drop(columns=['overlap_area', 'index_right'], errors='ignore')
        
        self.update_progress_signal.emit(80, "正在保存输出文件...")
        # 保存输出文件
        if output_type == "SHP文件":
            # 保存为SHP文件
            final_gdf.to_file(output_path, driver='ESRI Shapefile')
            result_msg = f"成功执行空间挂接，重叠面积阈值: {threshold}\n"
            result_msg += f"要素A: {os.path.basename(feature_a_path)}\n"
            result_msg += f"要素B: {os.path.basename(feature_b_path)}\n"
            result_msg += f"输出文件: {os.path.basename(output_path)}\n"
            result_msg += f"要素A总数: {len(feature_a)} 个要素\n"
            result_msg += f"匹配成功: {len(matched_a)} 个要素\n"
            result_msg += f"匹配成功率: {len(matched_a) / len(feature_a) * 100:.2f}%"
        else:
            # 保存为GDB图层
            final_gdf.to_file(output_path, layer=output_layer, driver='OpenFileGDB')
            result_msg = f"成功执行空间挂接，重叠面积阈值: {threshold}\n"
            result_msg += f"要素A: {os.path.basename(feature_a_path)}\n"
            result_msg += f"要素B: {os.path.basename(feature_b_path)}\n"
            result_msg += f"输出GDB: {os.path.basename(output_path)}\n"
            result_msg += f"输出图层: {output_layer}\n"
            result_msg += f"要素A总数: {len(feature_a)} 个要素\n"
            result_msg += f"匹配成功: {len(matched_a)} 个要素\n"
            result_msg += f"匹配成功率: {len(matched_a) / len(feature_a) * 100:.2f}%"
        
        # 更新进度为100%
        self.update_progress_signal.emit(100, "挂接完成！")
        
        return result_msg
