# coding:utf-8
"""
数据叠加套合占比功能
"""

from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QFileDialog, QGroupBox
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from qfluentwidgets import LineEdit, ComboBox, PushButton
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction
import geopandas as gpd
import os
import sys


class DataOverlayThread(QThread):
    """数据叠加套合线程"""
    
    success = pyqtSignal(str)  # 成功信号，传递结果信息
    error = pyqtSignal(str)    # 错误信号，传递错误信息
    
    def __init__(self, path1, path2, field1, field2, file_type1="shp", file_type2="shp", 
                 layer1=None, layer2=None, output_type="SHP文件", output_path=None, 
                 output_layer=None, parent=None):
        """
        Args:
            path1: 主矢量文件路径
            path2: 叠加矢量文件路径
            field1: 主矢量字段
            field2: 叠加矢量字段
            file_type1: 主矢量文件类型（shp或gdb）
            file_type2: 叠加矢量文件类型（shp或gdb）
            layer1: 主矢量图层名称（仅GDB需要）
            layer2: 叠加矢量图层名称（仅GDB需要）
            output_type: 输出类型（SHP文件或GDB图层）
            output_path: 输出路径
            output_layer: 输出图层名称（仅GDB输出需要）
        """
        super().__init__(parent)
        self.path1 = path1
        self.path2 = path2
        self.field1 = field1
        self.field2 = field2
        self.file_type1 = file_type1
        self.file_type2 = file_type2
        self.layer1 = layer1
        self.layer2 = layer2
        self.output_type = output_type
        self.output_path = output_path
        self.output_layer = output_layer
    
    def run(self):
        """线程运行方法"""
        try:
            # 实现数据套合占比功能
            import geopandas as gpd
            import pandas as pd
            import os
            from datetime import datetime
            
            # 读取矢量数据（支持SHP和GDB）
            if self.file_type1 == "shp":
                gdf1 = gpd.read_file(self.path1)
            else:  # gdb
                gdf1 = gpd.read_file(self.path1, layer=self.layer1)
            
            if self.file_type2 == "shp":
                gdf2 = gpd.read_file(self.path2)
            else:  # gdb
                gdf2 = gpd.read_file(self.path2, layer=self.layer2)
            
            # 确保坐标系一致
            if gdf1.crs != gdf2.crs:
                gdf2 = gdf2.to_crs(gdf1.crs)
            
            # 计算主矢量要素的面积
            gdf1['主面积'] = gdf1.geometry.area
            
            # 执行空间连接，获取相交的要素
            joined = gpd.sjoin(gdf1, gdf2, how='left', predicate='intersects')
            
            # 保存原始索引，用于后续合并
            joined['原始索引'] = joined.index
            
            # 计算相交面积
            # 创建空间连接结果，包含几何信息
            spatial_join = gpd.overlay(gdf1, gdf2, how='intersection', keep_geom_type=False)
            
            # 计算相交部分的面积
            spatial_join['相交面积'] = spatial_join.geometry.area
            
            # 按主矢量字段和叠加矢量字段分组，计算叠加数据、总面积和唯一值
            def aggregate_data(group):
                # 获取唯一的叠加字段值，用逗号分隔
                unique_values = group[self.field2].unique()
                dj_data = ','.join(str(v) for v in unique_values if pd.notna(v))
                
                # 计算总相交面积
                total_area = group['相交面积'].sum()
                
                return pd.Series({
                    'DJSJ': dj_data,
                    '叠加面积': total_area
                })
            
            # 对空间连接结果进行聚合
            spatial_agg = spatial_join.groupby([self.field1]).apply(aggregate_data).reset_index()
            
            # 合并主矢量数据和空间聚合结果
            merged = gdf1.merge(spatial_agg, on=self.field1, how='left')
            
            # 计算叠加比例
            merged['叠加比例'] = merged['叠加面积'] / merged['主面积']
            merged['叠加比例'] = merged['叠加比例'].fillna(0)  # 填充空值为0
            
            # 处理没有叠加数据的情况
            merged['DJSJ'] = merged['DJSJ'].fillna('')
            merged['叠加面积'] = merged['叠加面积'].fillna(0)
            
            # 移除临时字段
            if '主面积' in merged.columns:
                merged = merged.drop(columns=['主面积'])
            
            # 生成Excel文件（始终生成，用于结果查看）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_path = os.path.join(os.path.dirname(self.output_path), f'套合分析结果_{timestamp}.xlsx')
            
            # 准备Excel数据
            excel_data = merged.copy()
            if 'geometry' in excel_data.columns:
                excel_data = excel_data.drop(columns=['geometry'])
            excel_data.to_excel(excel_path, index=False)
            
            # 保存结果到指定输出路径
            if self.output_type == "SHP文件":
                # 保存为SHP文件
                merged.to_file(self.output_path, encoding='utf-8')
                
                # 生成TXT文件
                txt_path = self.output_path[:-4] + '.txt'
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write("数据套合占比分析结果\n")
                    f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"主矢量文件: {self.path1}\n")
                    f.write(f"叠加矢量文件: {self.path2}\n")
                    f.write(f"主矢量字段: {self.field1}\n")
                    f.write(f"叠加矢量字段: {self.field2}\n")
                    f.write("\n字段说明:\n")
                    f.write("- DJSJ: 叠加数据，包含所有相交的叠加矢量字段值，用逗号分隔\n")
                    f.write("- 叠加面积: 主矢量要素与叠加矢量要素的相交面积总和\n")
                    f.write("- 叠加比例: 叠加面积与主矢量要素面积的比值\n\n")
                    f.write("统计结果:\n")
                    f.write(merged[[self.field1, 'DJSJ', '叠加面积', '叠加比例']].to_string(index=False))
                
                result_msg = (
                    f"分析完成！\n\n"
                    f"SHP文件：{self.output_path}\n"
                    f"TXT文件：{txt_path}\n"
                    f"Excel文件：{excel_path}\n\n"
                    f"已添加字段：\n"
                    f"- DJSJ: 叠加数据，包含所有相交的叠加矢量字段值\n"
                    f"- 叠加面积: 相交面积总和\n"
                    f"- 叠加比例: 叠加面积与主矢量面积的比值"
                )
            else:  # GDB图层
                # 保存为GDB图层
                merged.to_file(self.output_path, layer=self.output_layer, driver='OpenFileGDB')
                
                result_msg = (
                    f"分析完成！\n\n"
                    f"GDB文件：{self.output_path}\n"
                    f"输出图层：{self.output_layer}\n"
                    f"Excel文件：{excel_path}\n\n"
                    f"已添加字段：\n"
                    f"- DJSJ: 叠加数据，包含所有相交的叠加矢量字段值\n"
                    f"- 叠加面积: 相交面积总和\n"
                    f"- 叠加比例: 叠加面积与主矢量面积的比值"
                )
            
            self.success.emit(result_msg)
            
        except Exception as e:
            self.error.emit(f"分析失败: {str(e)}")


class DataOverlayFunction(BaseFunction):
    """数据叠加套合占比功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>"
            "1. 计算两个矢量数据集的套合占比情况<br>"
            "2. 选择主矢量文件和叠加矢量文件<br>"
            "3. 选择对应的字段进行分析<br>"
            "4. 输出SHP、TXT和Excel分析报告"
        )
        super().__init__("数据叠加套合占比", description, parent)
        
        # 初始化UI
        self._initUI()
        
        # 添加执行按钮
        self.addExecuteButton("开始分析", self.execute)
    
    def _initUI(self):
        """初始化界面"""
        # 输入矢量设置区域
        input_group = QGroupBox("输入矢量设置", self)
        input_layout = QVBoxLayout(input_group)
        
        # 主矢量文件设置
        main_vector_layout = QHBoxLayout()
        main_vector_label = QLabel("主矢量文件：")
        self.mainVectorPath = LineEdit(self)
        self.mainVectorPath.setPlaceholderText("选择主矢量文件")
        self.mainVectorPath.setReadOnly(True)
        
        # 主矢量选择按钮（SHP和GDB）
        self.mainVectorShpBtn = PushButton("选择SHP", self, FIF.DOCUMENT)
        self.mainVectorShpBtn.clicked.connect(lambda: self._selectVectorFile("main", "shp"))
        self.mainVectorGdbBtn = PushButton("选择GDB", self, FIF.FOLDER)
        self.mainVectorGdbBtn.clicked.connect(lambda: self._selectVectorFile("main", "gdb"))
        
        main_vector_layout.addWidget(main_vector_label)
        main_vector_layout.addWidget(self.mainVectorPath, 1)
        main_vector_layout.addWidget(self.mainVectorShpBtn)
        main_vector_layout.addWidget(self.mainVectorGdbBtn)
        input_layout.addLayout(main_vector_layout)
        
        # 主矢量图层选择（仅GDB文件显示）
        self.mainVectorLayerLayout = QHBoxLayout()
        main_vector_layer_label = QLabel("主矢量图层：")
        self.mainVectorLayerCombo = ComboBox(self)
        self.mainVectorLayerCombo.setPlaceholderText("请先选择GDB文件")
        self.mainVectorLayerCombo.setEnabled(False)
        
        self.mainVectorLayerLayout.addWidget(main_vector_layer_label)
        self.mainVectorLayerLayout.addWidget(self.mainVectorLayerCombo, 1)
        # 默认隐藏主矢量图层选择
        for i in range(self.mainVectorLayerLayout.count()):
            widget = self.mainVectorLayerLayout.itemAt(i).widget()
            if widget:
                widget.setVisible(False)
        input_layout.addLayout(self.mainVectorLayerLayout)
        
        # 叠加矢量文件设置
        overlay_vector_layout = QHBoxLayout()
        overlay_vector_label = QLabel("叠加矢量文件：")
        self.overlayVectorPath = LineEdit(self)
        self.overlayVectorPath.setPlaceholderText("选择叠加矢量文件")
        self.overlayVectorPath.setReadOnly(True)
        
        # 叠加矢量选择按钮（SHP和GDB）
        self.overlayVectorShpBtn = PushButton("选择SHP", self, FIF.DOCUMENT)
        self.overlayVectorShpBtn.clicked.connect(lambda: self._selectVectorFile("overlay", "shp"))
        self.overlayVectorGdbBtn = PushButton("选择GDB", self, FIF.FOLDER)
        self.overlayVectorGdbBtn.clicked.connect(lambda: self._selectVectorFile("overlay", "gdb"))
        
        overlay_vector_layout.addWidget(overlay_vector_label)
        overlay_vector_layout.addWidget(self.overlayVectorPath, 1)
        overlay_vector_layout.addWidget(self.overlayVectorShpBtn)
        overlay_vector_layout.addWidget(self.overlayVectorGdbBtn)
        input_layout.addLayout(overlay_vector_layout)
        
        # 叠加矢量图层选择（仅GDB文件显示）
        self.overlayVectorLayerLayout = QHBoxLayout()
        overlay_vector_layer_label = QLabel("叠加矢量图层：")
        self.overlayVectorLayerCombo = ComboBox(self)
        self.overlayVectorLayerCombo.setPlaceholderText("请先选择GDB文件")
        self.overlayVectorLayerCombo.setEnabled(False)
        
        self.overlayVectorLayerLayout.addWidget(overlay_vector_layer_label)
        self.overlayVectorLayerLayout.addWidget(self.overlayVectorLayerCombo, 1)
        # 默认隐藏叠加矢量图层选择
        for i in range(self.overlayVectorLayerLayout.count()):
            widget = self.overlayVectorLayerLayout.itemAt(i).widget()
            if widget:
                widget.setVisible(False)
        input_layout.addLayout(self.overlayVectorLayerLayout)
        
        # 字段选择布局
        fields_layout = QHBoxLayout()
        
        # 主矢量字段选择
        main_field_layout = QHBoxLayout()
        main_field_label = QLabel("主矢量字段：")
        self.mainVectorField = ComboBox(self)
        self.mainVectorField.setPlaceholderText("选择字段")
        main_field_layout.addWidget(main_field_label)
        main_field_layout.addWidget(self.mainVectorField)
        
        # 叠加矢量字段选择
        overlay_field_layout = QHBoxLayout()
        overlay_field_label = QLabel("叠加矢量字段：")
        self.overlayVectorField = ComboBox(self)
        self.overlayVectorField.setPlaceholderText("选择字段")
        overlay_field_layout.addWidget(overlay_field_label)
        overlay_field_layout.addWidget(self.overlayVectorField)
        
        fields_layout.addLayout(main_field_layout)
        fields_layout.addStretch(1)
        fields_layout.addLayout(overlay_field_layout)
        input_layout.addLayout(fields_layout)
        
        # 输出设置区域
        output_group = QGroupBox("输出设置", self)
        output_layout = QVBoxLayout(output_group)
        
        # 输出类型选择
        output_type_layout = QHBoxLayout()
        output_type_label = QLabel("输出类型：")
        self.outputTypeCombo = ComboBox(self)
        self.outputTypeCombo.addItems(["SHP文件", "GDB图层"])
        self.outputTypeCombo.currentTextChanged.connect(self._on_output_type_changed)
        
        output_type_layout.addWidget(output_type_label)
        output_type_layout.addWidget(self.outputTypeCombo, 1)
        output_layout.addLayout(output_type_layout)
        
        # 输出文件/图层设置
        # SHP输出路径
        self.shpOutputLayout = QHBoxLayout()
        shp_output_label = QLabel("SHP输出路径：")
        self.outputFilePath = LineEdit(self)
        self.outputFilePath.setPlaceholderText("选择输出SHP文件路径")
        self.outputFilePath.setReadOnly(True)
        
        self.outputFileBtn = PushButton("选择输出路径", self, FIF.SAVE)
        self.outputFileBtn.clicked.connect(lambda: self._selectOutputFile("shp"))
        
        self.shpOutputLayout.addWidget(shp_output_label)
        self.shpOutputLayout.addWidget(self.outputFilePath, 1)
        self.shpOutputLayout.addWidget(self.outputFileBtn)
        output_layout.addLayout(self.shpOutputLayout)
        
        # GDB输出设置
        self.gdbOutputLayout = QHBoxLayout()
        gdb_output_label = QLabel("GDB输出路径：")
        self.outputGdbPath = LineEdit(self)
        self.outputGdbPath.setPlaceholderText("选择输出GDB文件")
        self.outputGdbPath.setReadOnly(True)
        
        self.outputGdbBtn = PushButton("选择GDB", self, FIF.FOLDER)
        self.outputGdbBtn.clicked.connect(lambda: self._selectOutputFile("gdb"))
        
        gdb_layer_label = QLabel("输出图层名称：")
        self.outputGdbLayerEdit = LineEdit(self)
        self.outputGdbLayerEdit.setPlaceholderText("输入输出图层名称")
        
        self.gdbOutputLayout.addWidget(gdb_output_label)
        self.gdbOutputLayout.addWidget(self.outputGdbPath, 1)
        self.gdbOutputLayout.addWidget(self.outputGdbBtn)
        self.gdbOutputLayout.addWidget(gdb_layer_label)
        self.gdbOutputLayout.addWidget(self.outputGdbLayerEdit)
        # 默认隐藏GDB输出设置
        for i in range(self.gdbOutputLayout.count()):
            widget = self.gdbOutputLayout.itemAt(i).widget()
            if widget:
                widget.setVisible(False)
        output_layout.addLayout(self.gdbOutputLayout)
        
        # 将分组框添加到主布局
        self.contentLayout.addWidget(input_group)
        self.contentLayout.addWidget(output_group)
    
    def _selectVectorFile(self, vector_type: str, file_type: str):
        """选择矢量文件"""
        if file_type == "shp":
            # 选择SHP文件
            file_path, _ = QFileDialog.getOpenFileName(
                self, f"选择{vector_type == 'main' and '主' or '叠加'}矢量SHP文件", "", "SHP文件 (*.shp)"
            )
            if file_path:
                if vector_type == "main":
                    self.mainVectorPath.setText(file_path)
                    self._loadFields(file_path, self.mainVectorField, "shp")
                    # 隐藏图层选择
                    for i in range(self.mainVectorLayerLayout.count()):
                        widget = self.mainVectorLayerLayout.itemAt(i).widget()
                        if widget:
                            widget.setVisible(False)
                else:
                    self.overlayVectorPath.setText(file_path)
                    self._loadFields(file_path, self.overlayVectorField, "shp")
                    # 隐藏图层选择
                    for i in range(self.overlayVectorLayerLayout.count()):
                        widget = self.overlayVectorLayerLayout.itemAt(i).widget()
                        if widget:
                            widget.setVisible(False)
        else:
            # 选择GDB文件
            file_path = QFileDialog.getExistingDirectory(
                self, f"选择{vector_type == 'main' and '主' or '叠加'}矢量GDB文件", ""
            )
            if file_path and file_path.endswith('.gdb'):
                if vector_type == "main":
                    self.mainVectorPath.setText(file_path)
                    self._loadLayers(file_path, self.mainVectorLayerCombo, self.mainVectorField, "main")
                    # 显示图层选择
                    for i in range(self.mainVectorLayerLayout.count()):
                        widget = self.mainVectorLayerLayout.itemAt(i).widget()
                        if widget:
                            widget.setVisible(True)
                else:
                    self.overlayVectorPath.setText(file_path)
                    self._loadLayers(file_path, self.overlayVectorLayerCombo, self.overlayVectorField, "overlay")
                    # 显示图层选择
                    for i in range(self.overlayVectorLayerLayout.count()):
                        widget = self.overlayVectorLayerLayout.itemAt(i).widget()
                        if widget:
                            widget.setVisible(True)
    
    def _loadLayers(self, gdb_path: str, layer_combo: ComboBox, field_combo: ComboBox, vector_type: str):
        """加载GDB文件中的图层列表"""
        try:
            import fiona
            layers = fiona.listlayers(gdb_path)
            layer_combo.clear()
            layer_combo.addItems(layers)
            layer_combo.setEnabled(True)
            
            # 连接图层选择变化信号
            if vector_type == "main":
                layer_combo.currentTextChanged.connect(lambda layer: self._loadFields(gdb_path, field_combo, "gdb", layer))
            else:
                layer_combo.currentTextChanged.connect(lambda layer: self._loadFields(gdb_path, field_combo, "gdb", layer))
            
            # 如果有图层，默认选择第一个
            if layers:
                layer_combo.setCurrentIndex(0)
        except Exception as e:
            self.showError(f"读取GDB图层失败: {str(e)}")
    
    def _on_output_type_changed(self, output_type: str):
        """输出类型变化处理"""
        if output_type == "SHP文件":
            # 显示SHP输出设置，隐藏GDB输出设置
            for i in range(self.shpOutputLayout.count()):
                widget = self.shpOutputLayout.itemAt(i).widget()
                if widget:
                    widget.setVisible(True)
            for i in range(self.gdbOutputLayout.count()):
                widget = self.gdbOutputLayout.itemAt(i).widget()
                if widget:
                    widget.setVisible(False)
        else:
            # 显示GDB输出设置，隐藏SHP输出设置
            for i in range(self.shpOutputLayout.count()):
                widget = self.shpOutputLayout.itemAt(i).widget()
                if widget:
                    widget.setVisible(False)
            for i in range(self.gdbOutputLayout.count()):
                widget = self.gdbOutputLayout.itemAt(i).widget()
                if widget:
                    widget.setVisible(True)
    
    def _selectOutputFile(self, output_type: str):
        """选择输出文件"""
        if output_type == "shp":
            # 选择SHP输出文件
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存SHP文件", "", "SHP文件 (*.shp)"
            )
            if file_path:
                # 确保文件扩展名为.shp
                if not file_path.endswith('.shp'):
                    file_path += '.shp'
                self.outputFilePath.setText(file_path)
        else:
            # 选择GDB输出文件
            file_path = QFileDialog.getExistingDirectory(
                self, "选择输出GDB文件", ""
            )
            if file_path and file_path.endswith('.gdb'):
                self.outputGdbPath.setText(file_path)
    
    def _loadFields(self, file_path, combo_box, file_type="shp", layer_name=None):
        """加载字段列表"""
        try:
            if file_type == "shp":
                gdf = gpd.read_file(file_path)
            else:  # gdb
                gdf = gpd.read_file(file_path, layer=layer_name)
            fields = [col for col in gdf.columns if col != 'geometry']
            combo_box.clear()
            combo_box.addItems(fields)
        except Exception as e:
            self.showError(f"读取字段失败: {str(e)}")
    
    def validate(self) -> tuple[bool, str]:
        """验证输入"""
        # 验证输入矢量文件
        if not self.mainVectorPath.text():
            return False, "请选择主矢量文件"
        if not self.overlayVectorPath.text():
            return False, "请选择叠加矢量文件"
        
        # 验证字段选择
        if not self.mainVectorField.currentText():
            return False, "请选择主矢量字段"
        if not self.overlayVectorField.currentText():
            return False, "请选择叠加矢量字段"
        
        # 验证输出设置
        output_type = self.outputTypeCombo.currentText()
        if output_type == "SHP文件":
            if not self.outputFilePath.text():
                return False, "请选择SHP输出路径"
        else:  # GDB图层
            if not self.outputGdbPath.text():
                return False, "请选择GDB输出文件"
            if not self.outputGdbLayerEdit.text():
                return False, "请输入GDB输出图层名称"
        
        return True, ""
    
    def execute(self):
        """执行分析"""
        # 验证输入
        valid, message = self.validate()
        if not valid:
            self.showError(message)
            return
        
        # 显示进度
        self.showProgress("正在分析数据...")
        
        # 获取输入参数
        main_vector_path = self.mainVectorPath.text()
        overlay_vector_path = self.overlayVectorPath.text()
        main_vector_field = self.mainVectorField.currentText()
        overlay_vector_field = self.overlayVectorField.currentText()
        
        # 判断文件类型和获取图层名称
        main_file_type = "gdb" if main_vector_path.endswith('.gdb') else "shp"
        overlay_file_type = "gdb" if overlay_vector_path.endswith('.gdb') else "shp"
        
        main_layer_name = self.mainVectorLayerCombo.currentText() if main_file_type == "gdb" else None
        overlay_layer_name = self.overlayVectorLayerCombo.currentText() if overlay_file_type == "gdb" else None
        
        # 获取输出参数
        output_type = self.outputTypeCombo.currentText()
        if output_type == "SHP文件":
            output_path = self.outputFilePath.text()
            output_layer = None
        else:  # GDB图层
            output_path = self.outputGdbPath.text()
            output_layer = self.outputGdbLayerEdit.text()
        
        # 创建并启动数据叠加套合线程
        self.overlay_thread = DataOverlayThread(
            path1=main_vector_path,
            path2=overlay_vector_path,
            field1=main_vector_field,
            field2=overlay_vector_field,
            file_type1=main_file_type,
            file_type2=overlay_file_type,
            layer1=main_layer_name,
            layer2=overlay_layer_name,
            output_type=output_type,
            output_path=output_path,
            output_layer=output_layer,
            parent=self
        )
        
        # 连接信号
        self.overlay_thread.success.connect(self._onOverlaySuccess)
        self.overlay_thread.error.connect(self._onOverlayError)
        self.overlay_thread.finished.connect(self._onOverlayFinished)
        
        # 启动线程
        self.overlay_thread.start()
    
    def _onOverlaySuccess(self, message: str):
        """叠加分析成功处理"""
        self.showSuccess(message)
    
    def _onOverlayError(self, message: str):
        """叠加分析错误处理"""
        self.showError(message)
    
    def _onOverlayFinished(self):
        """叠加分析线程结束处理"""
        self.hideProgress()
