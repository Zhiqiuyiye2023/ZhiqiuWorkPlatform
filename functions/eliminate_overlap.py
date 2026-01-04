# coding:utf-8
"""
要素去重叠功能模块
读取SHP或GDB文件，检测要素重叠区域，移除重叠部分并保留边界，使用边界分割重叠图斑
"""

from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QFileDialog, QWidget, QFrame, QGroupBox
from PyQt6.QtCore import Qt
from qfluentwidgets import LineEdit, PushButton, ComboBox, SpinBox, CheckBox
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction
import threading
import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union, polygonize


class EliminateOverlapFunction(BaseFunction):
    """要素去重叠功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>"
            "读取SHP或GDB文件，检测要素重叠区域，移除重叠部分并保留边界，使用边界分割重叠图斑"
        )
        super().__init__("要素去重叠", description, parent)
        
        # 初始化UI
        self._initUI()
        
        # 添加执行按钮
        self.execute_btn = self.addExecuteButton("开始处理", self.execute)
    
    def _initUI(self):
        """初始化UI界面"""
        # 输入矢量文件设置区域
        input_vector_group = QGroupBox("输入矢量文件", self)
        input_vector_layout = QVBoxLayout(input_vector_group)
        
        # 源文件选择
        source_layout = QHBoxLayout()
        source_label = QLabel("源矢量数据：")
        self.source_path = LineEdit(self)
        self.source_path.setPlaceholderText("选择要处理的矢量文件")
        self.source_path.setReadOnly(True)
        
        # 分别添加SHP和GDB文件选择按钮
        self.source_shp_btn = PushButton("选择SHP", self, FIF.FOLDER)
        self.source_shp_btn.clicked.connect(lambda: self._selectSourceFile(shp_only=True))
        self.source_shp_btn.setFixedWidth(120)
        
        self.source_gdb_btn = PushButton("选择GDB", self, FIF.FOLDER)
        self.source_gdb_btn.clicked.connect(lambda: self._selectSourceFile(gdb_only=True))
        self.source_gdb_btn.setFixedWidth(120)
        
        source_layout.addWidget(source_label)
        source_layout.addWidget(self.source_path, 1)
        source_layout.addWidget(self.source_shp_btn)
        source_layout.addWidget(self.source_gdb_btn)
        input_vector_layout.addLayout(source_layout)
        
        # 图层选择（仅GDB文件显示）
        self.source_layer_layout = QHBoxLayout()
        source_layer_label = QLabel("源图层：")
        self.source_layer_combo = ComboBox(self)
        self.source_layer_combo.setPlaceholderText("请先选择文件")
        self.source_layer_combo.setEnabled(False)
        # 连接图层选择变化信号
        self.source_layer_combo.currentTextChanged.connect(self._on_layer_changed)
        
        self.source_layer_layout.addWidget(source_layer_label)
        self.source_layer_layout.addWidget(self.source_layer_combo, 1)
        # 默认隐藏图层选择
        for i in range(self.source_layer_layout.count()):
            widget = self.source_layer_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(False)
        input_vector_layout.addLayout(self.source_layer_layout)
        
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
        
        # SHP输出路径
        self.shp_output_layout = QHBoxLayout()
        shp_output_label = QLabel("SHP输出路径：")
        self.outputFilePath = LineEdit(self)
        self.outputFilePath.setPlaceholderText("选择输出SHP文件路径")
        self.outputFilePath.setReadOnly(True)
        
        self.outputFileBtn = PushButton("选择输出路径", self, FIF.SAVE)
        self.outputFileBtn.clicked.connect(self._select_output_shp)
        self.outputFileBtn.setFixedWidth(120)
        
        self.shp_output_layout.addWidget(shp_output_label)
        self.shp_output_layout.addWidget(self.outputFilePath, 1)
        self.shp_output_layout.addWidget(self.outputFileBtn)
        output_layout.addLayout(self.shp_output_layout)
        
        # GDB输出设置
        self.gdb_output_layout = QHBoxLayout()
        gdb_output_label = QLabel("GDB输出文件：")
        self.output_gdb_path = LineEdit(self)
        self.output_gdb_path.setPlaceholderText("选择输出GDB文件")
        self.output_gdb_path.setReadOnly(True)
        
        self.output_gdb_btn = PushButton("选择GDB", self, FIF.FOLDER)
        self.output_gdb_btn.clicked.connect(self._select_output_gdb)
        self.output_gdb_btn.setFixedWidth(120)
        
        self.gdb_output_layout.addWidget(gdb_output_label)
        self.gdb_output_layout.addWidget(self.output_gdb_path, 1)
        self.gdb_output_layout.addWidget(self.output_gdb_btn)
        
        # GDB图层名称
        self.gdb_layer_layout = QHBoxLayout()
        gdb_layer_label = QLabel("GDB图层名称：")
        self.output_gdb_layer = LineEdit(self)
        self.output_gdb_layer.setPlaceholderText("输入输出图层名称")
        
        self.gdb_layer_layout.addWidget(gdb_layer_label)
        self.gdb_layer_layout.addWidget(self.output_gdb_layer, 1)
        
        # 默认隐藏GDB输出设置
        for i in range(self.gdb_output_layout.count()):
            widget = self.gdb_output_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(False)
        output_layout.addLayout(self.gdb_output_layout)
        
        for i in range(self.gdb_layer_layout.count()):
            widget = self.gdb_layer_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(False)
        output_layout.addLayout(self.gdb_layer_layout)
        
        # 进度显示区域
        self.progress_container = QFrame(self)
        self.progress_container.setFixedHeight(60)
        self.progress_container.setStyleSheet("QFrame { border-radius: 8px; }")
        
        # 连接主题变化信号，实现自动跟随系统主题
        from configs.config import cfg
        from qfluentwidgets import isDarkTheme
        cfg.themeChanged.connect(self._onThemeChanged)
        self._onThemeChanged()
        
        self.progress_layout = QVBoxLayout(self.progress_container)
        self.progress_layout.setContentsMargins(0, 0, 0, 0)
        self.progress_layout.setSpacing(5)
        
        # 进度文本
        self.progress_text = QLabel("准备开始处理...", self)
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
        self.contentLayout.addWidget(output_group)
        self.contentLayout.addSpacing(20)
        self.contentLayout.addWidget(self.progress_container)
        self.contentLayout.addSpacing(20)
    
    def _selectSourceFile(self, shp_only=False, gdb_only=False):
        """选择源矢量文件"""
        if shp_only:
            # 选择SHP文件
            file_path, _ = QFileDialog.getOpenFileName(
                self, 
                "选择SHP文件", 
                "", 
                "Shapefile文件 (*.shp);;所有文件 (*.*)"
            )
            if file_path:
                self.source_path.setText(file_path)
                # 隐藏图层选择
                for i in range(self.source_layer_layout.count()):
                    widget = self.source_layer_layout.itemAt(i).widget()
                    if widget:
                        widget.setVisible(False)
                # 设置默认输出路径
                self._set_default_output_path(file_path)
        elif gdb_only:
            # 选择GDB文件
            file_path = QFileDialog.getExistingDirectory(
                self, 
                "选择GDB文件夹", 
                ""
            )
            if file_path and file_path.lower().endswith('.gdb'):
                self.source_path.setText(file_path)
                # 显示图层选择
                for i in range(self.source_layer_layout.count()):
                    widget = self.source_layer_layout.itemAt(i).widget()
                    if widget:
                        widget.setVisible(True)
                # 加载GDB中的图层
                self._load_gdb_layers(file_path)
                # 设置默认输出路径
                self._set_default_output_path(file_path)
    
    def _load_gdb_layers(self, gdb_path):
        """加载GDB中的图层"""
        try:
            # 获取GDB中的所有图层
            layers = [layer for layer in gpd.list_layers(gdb_path) if layer.geom_type == 'Polygon']
            layer_names = [layer.name for layer in layers]
            
            self.source_layer_combo.clear()
            self.source_layer_combo.addItems(layer_names)
            self.source_layer_combo.setEnabled(True)
        except Exception as e:
            self.showError(f"加载GDB图层失败: {str(e)}")
    
    def _on_layer_changed(self, layer_name):
        """图层选择变化时更新默认输出图层名"""
        source_path = self.source_path.text()
        if source_path.lower().endswith('.gdb') and layer_name:
            # 更新默认输出图层名
            default_layer_name = f"{layer_name}_no_overlap"
            self.output_gdb_layer.setText(default_layer_name)
    
    def _set_default_output_path(self, source_path):
        """根据源文件设置默认输出路径"""
        if source_path.lower().endswith('.shp'):
            # SHP文件：默认输出到源文件所在目录，文件名加上"_no_overlap"后缀
            dir_name = os.path.dirname(source_path)
            base_name = os.path.basename(source_path)
            name_without_ext = os.path.splitext(base_name)[0]
            default_output_path = os.path.join(dir_name, f"{name_without_ext}_no_overlap.shp")
            self.outputFilePath.setText(default_output_path)
        elif source_path.lower().endswith('.gdb'):
            # GDB文件：默认输出到同一GDB，图层名加上"_no_overlap"后缀
            self.output_gdb_path.setText(source_path)
            # 如果已经选择了图层，使用图层名作为默认输出图层名
            if self.source_layer_combo.currentText():
                default_layer_name = f"{self.source_layer_combo.currentText()}_no_overlap"
                self.output_gdb_layer.setText(default_layer_name)
            else:
                self.output_gdb_layer.setText("output_no_overlap")
    
    def _select_output_shp(self):
        """选择SHP输出路径"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "选择输出SHP文件", 
            "", 
            "Shapefile文件 (*.shp);;所有文件 (*.*)"
        )
        if file_path:
            # 确保文件扩展名是.shp
            if not file_path.lower().endswith('.shp'):
                file_path += '.shp'
            self.outputFilePath.setText(file_path)
    
    def _select_output_gdb(self):
        """选择GDB输出文件"""
        file_path = QFileDialog.getExistingDirectory(
            self, "选择输出GDB文件", "."
        )
        if file_path and file_path.lower().endswith('.gdb'):
            self.output_gdb_path.setText(file_path)
    
    def _onThemeChanged(self):
        """主题变化时更新进度容器背景色和文字颜色"""
        # 先调用父类的主题处理逻辑，确保文字颜色正确设置
        super()._onThemeChanged()
        
        # 然后更新进度容器的背景色
        from qfluentwidgets import isDarkTheme
        # 检查progress_container是否已经创建
        if hasattr(self, 'progress_container'):
            if isDarkTheme():
                self.progress_container.setStyleSheet("QFrame { background-color: #2d2d2d; border-radius: 8px; }")
            else:
                self.progress_container.setStyleSheet("QFrame { background-color: #f0f0f0; border-radius: 8px; }")
    
    def _on_output_type_changed(self, output_type):
        """输出类型变化时更新UI"""
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
    
    def validate(self):
        """验证输入参数"""
        # 验证源文件
        if not self.source_path.text():
            return False, "请选择源矢量文件"
        
        # 验证输出设置
        output_type = self.output_type_combo.currentText()
        if output_type == "SHP文件":
            if not self.outputFilePath.text():
                return False, "请选择SHP输出路径"
        else:
            if not self.output_gdb_path.text():
                return False, "请选择GDB输出文件"
            
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
            return
        
        # 2. 获取参数
        source_path = self.source_path.text()
        source_layer = self.source_layer_combo.currentText() if source_path.lower().endswith('.gdb') else ""
        
        # 获取输出设置
        output_type = self.output_type_combo.currentText()
        if output_type == "SHP文件":
            output_path = self.outputFilePath.text()
            output_layer = ""
        else:
            output_path = self.output_gdb_path.text()
            output_layer = self.output_gdb_layer.text()
        
        # 3. 显示进度条
        self.progress_container.setVisible(True)
        self.updateProgress(0)
        
        # 4. 在线程中执行处理
        def run_process():
            try:
                # 调用处理方法
                result = self._eliminate_overlap(source_path, source_layer, output_path, output_type, output_layer)
                
                # 发送成功信号
                self.show_success_signal.emit(f"处理完成！\n{result}")
                
            except Exception as e:
                import traceback
                error_msg = f"处理失败: {str(e)}\n\n{traceback.format_exc()}"
                self.show_error_signal.emit(error_msg)
        
        # 启动线程
        threading.Thread(target=run_process, daemon=True).start()
    
    def _eliminate_overlap(self, source_path: str, source_layer: str, output_path: str, output_type: str, output_layer: str) -> str:
        """
        执行要素去重叠操作
        
        参数:
            source_path: 源文件路径
            source_layer: 源图层名称（仅GDB需要）
            output_path: 输出文件路径
            output_type: 输出类型（"SHP文件"或"GDB图层"）
            output_layer: 输出图层名称（仅GDB输出需要）
            
        返回:
            处理结果描述
        """
        # 读取源数据
        self.update_progress_signal.emit(20, "正在读取源数据...")
        
        if source_path.lower().endswith('.gdb'):
            # 从GDB读取图层
            gdf = gpd.read_file(source_path, layer=source_layer)
        else:
            # 读取SHP文件
            gdf = gpd.read_file(source_path)
        
        # 确保是面要素
        if gdf.geometry.type.iloc[0] != 'Polygon':
            raise ValueError("仅支持面要素类型")
        
        original_count = len(gdf)
        
        # 计算重叠区域
        self.update_progress_signal.emit(40, "正在计算重叠区域...")
        
        # 计算所有要素的并集
        all_polygons = unary_union(gdf.geometry)
        
        # 计算重叠区域的边界线
        self.update_progress_signal.emit(50, "正在提取重叠边界...")
        
        # 提取所有要素的边界
        all_boundaries = unary_union([geom.boundary for geom in gdf.geometry])
        
        # 使用边界线分割所有多边形
        self.update_progress_signal.emit(60, "正在分割重叠图斑...")
        
        # 使用边界线分割所有多边形
        split_polygons = list(polygonize(all_boundaries))
        
        # 移除可能产生的无效多边形（面积为0或非常小的）
        split_polygons = [poly for poly in split_polygons if poly.area > 1e-8]
        
        # 将分割后的多边形转换为GeoDataFrame
        self.update_progress_signal.emit(70, "正在构建结果数据...")
        
        result_gdf = gpd.GeoDataFrame(
            {'id': range(len(split_polygons))}, 
            geometry=split_polygons, 
            crs=gdf.crs
        )
        
        # 保存输出文件
        self.update_progress_signal.emit(90, "正在保存输出文件...")
        
        if output_type == "SHP文件":
            # 保存为SHP文件
            result_gdf.to_file(output_path, driver='ESRI Shapefile')
            result_msg = f"成功执行要素去重叠\n"
            result_msg += f"源文件: {os.path.basename(source_path)}\n"
            result_msg += f"原始要素数量: {original_count}\n"
            result_msg += f"处理后要素数量: {len(result_gdf)}\n"
            result_msg += f"输出文件: {os.path.basename(output_path)}"
        else:
            # 保存为GDB图层
            result_gdf.to_file(output_path, layer=output_layer, driver='OpenFileGDB')
            result_msg = f"成功执行要素去重叠\n"
            result_msg += f"源文件: {os.path.basename(source_path)}\n"
            result_msg += f"原始要素数量: {original_count}\n"
            result_msg += f"处理后要素数量: {len(result_gdf)}\n"
            result_msg += f"输出GDB: {os.path.basename(output_path)}\n"
            result_msg += f"输出图层: {output_layer}"
        
        self.update_progress_signal.emit(100, "处理完成")
        
        return result_msg
