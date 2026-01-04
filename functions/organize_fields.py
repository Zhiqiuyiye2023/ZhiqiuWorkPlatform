# coding:utf-8
"""
字段整理功能模块
整理要素的字段，根据字段映射关系将原始字段转换为新的字段结构
"""

from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QFileDialog, QWidget, QFrame, QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt
from qfluentwidgets import LineEdit, PushButton, ComboBox
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction
import threading
import os
import geopandas as gpd


class OrganizeFieldsFunction(BaseFunction):
    """字段整理功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>"
            "整理要素的字段，根据字段映射关系将原始字段转换为新的字段结构"
        )
        super().__init__("字段整理", description, parent)
        
        # 初始化UI
        self._initUI()
        
        # 添加执行按钮
        self.execute_btn = self.addExecuteButton("开始整理", self.execute)
    
    def _initUI(self):
        """初始化界面控件"""
        # 创建输入矢量选择区域
        input_vector_group = QGroupBox("输入矢量数据", self)
        input_vector_layout = QVBoxLayout(input_vector_group)
        
        # 输入矢量文件选择
        input_file_layout = QHBoxLayout()
        input_file_label = QLabel("输入矢量文件：")
        self.inputFilePath = LineEdit(self)
        self.inputFilePath.setPlaceholderText("选择需要整理字段的矢量文件")
        self.inputFilePath.setReadOnly(True)
        
        self.input_shp_btn = PushButton("选择SHP", self, FIF.FOLDER)
        self.input_shp_btn.clicked.connect(lambda: self._selectInputFile(shp_only=True))
        self.input_shp_btn.setFixedWidth(120)
        
        self.input_gdb_btn = PushButton("选择GDB", self, FIF.FOLDER)
        self.input_gdb_btn.clicked.connect(lambda: self._selectInputFile(gdb_only=True))
        self.input_gdb_btn.setFixedWidth(120)
        
        input_file_layout.addWidget(input_file_label)
        input_file_layout.addWidget(self.inputFilePath, 1)
        input_file_layout.addWidget(self.input_shp_btn)
        input_file_layout.addWidget(self.input_gdb_btn)
        input_vector_layout.addLayout(input_file_layout)
        
        # 输入矢量图层选择（仅GDB文件显示）
        input_layer_layout = QHBoxLayout()
        input_layer_label = QLabel("图层名称：")
        self.input_layer_combo = ComboBox(self)
        self.input_layer_combo.setPlaceholderText("请先选择文件")
        self.input_layer_combo.setEnabled(False)
        
        input_layer_layout.addWidget(input_layer_label)
        input_layer_layout.addWidget(self.input_layer_combo, 1)
        input_vector_layout.addLayout(input_layer_layout)
        
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
        
        # 字段映射设置区域
        mapping_group = QGroupBox("字段映射设置", self)
        mapping_layout = QVBoxLayout(mapping_group)
        
        # 字段映射表格
        self.mapping_table = QTableWidget(self)
        self.mapping_table.setColumnCount(3)
        self.mapping_table.setHorizontalHeaderLabels(["新字段名", "原始字段名", "默认值"])
        self.mapping_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # 添加默认字段映射
        self._addDefaultMapping()
        
        mapping_layout.addWidget(self.mapping_table)
        
        # 进度条容器
        self.progress_container = QWidget(self)
        self.progress_layout = QVBoxLayout(self.progress_container)
        self.progress_layout.setContentsMargins(0, 0, 0, 0)
        self.progress_layout.setSpacing(5)
        
        # 进度文本
        self.progress_text = QLabel("准备开始整理...", self)
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
        self.contentLayout.addWidget(mapping_group)
        self.contentLayout.addSpacing(20)
        self.contentLayout.addWidget(self.progress_container)
        self.contentLayout.addSpacing(20)
    
    def _addDefaultMapping(self):
        """添加默认字段映射"""
        default_mapping = [
            ["DLBM", "f_sddl", ""],
            ["QSXZ", "", ""],
            ["XZDWKD", "", ""],
            ["ZZSXDM", "f_zzsx", ""],
            ["CZCSXM", "", ""],
            ["TBXHDM", "", ""],
            ["JCBH", "f_tbbh", ""],
            ["JZLX", "f_jzlx_n1", ""],
            ["BZ", "f_bz2", ""],
            ["DDTC", "f_ddtc", ""]
        ]
        
        self.mapping_table.setRowCount(len(default_mapping))
        for i, row in enumerate(default_mapping):
            for j, item in enumerate(row):
                table_item = QTableWidgetItem(item)
                self.mapping_table.setItem(i, j, table_item)
    
    def _selectInputFile(self, shp_only=False, gdb_only=False):
        """选择输入文件"""
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
                self, "选择输入矢量文件", ".", "矢量文件 (*.shp *.geojson *.json *.gpkg);;所有文件 (*)"
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
            
            self.input_vector_path = file_path
            self.inputFilePath.setText(file_path)
            
            # 更新图层列表
            self._update_layer_list(file_path)
            
            # 自动生成输出文件名
            if shp_only or (not gdb_only and file_path.lower().endswith('.shp')):
                dir_name = os.path.dirname(file_path)
                base_name = os.path.basename(file_path)
                name, ext = os.path.splitext(base_name)
                output_path = os.path.join(dir_name, f"{name}_organized.shp")
                self.outputFilePath.setText(output_path)
            else:
                # 对于GDB文件，默认输出到GDB所在目录
                dir_name = file_path  # GDB文件本身就是目录
                base_name = os.path.basename(file_path)
                name = base_name.replace('.gdb', '')
                output_path = os.path.join(os.path.dirname(dir_name), f"{name}_organized.shp")
                self.outputFilePath.setText(output_path)
    
    def _update_layer_list(self, file_path):
        """更新矢量图层列表"""
        import fiona
        
        self.input_layer_combo.clear()
        self.input_layer_combo.setEnabled(False)
        
        if file_path.lower().endswith('.gdb'):
            # 列出GDB中的所有图层
            try:
                with fiona.Env():
                    layers = fiona.listlayers(file_path)
                self.input_layer_combo.addItems(layers)
                self.input_layer_combo.setEnabled(True)
                self.input_layer_name = layers[0] if layers else ""
                
                # 如果输入是GDB，默认输出类型设为GDB图层
                self.output_type_combo.setCurrentText("GDB图层")
                self.output_gdb_path.setText(file_path)
                
                # 默认输出图层名为输入图层名加_organized
                if layers:
                    self.output_gdb_layer.setText(f"{layers[0]}_organized")
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
            self.input_layer_combo.setPlaceholderText("SHP文件无需选择图层")
            self.input_layer_name = ""
            
            # 如果输入是SHP，默认输出类型设为SHP文件
            self.output_type_combo.setCurrentText("SHP文件")
    
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
        self.progress_text.setText(f"正在整理... {percent}%")
        
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
        self.progress_text.setText("准备开始整理...")
        self.progress_bar.setStyleSheet("""
            QFrame {
                background-color: #e0e0e0;
                border-radius: 2px;
            }
        """)
    
    def getFieldMapping(self):
        """获取字段映射关系"""
        field_mapping = {}
        for i in range(self.mapping_table.rowCount()):
            new_field = self.mapping_table.item(i, 0).text().strip()
            old_field = self.mapping_table.item(i, 1).text().strip()
            default_value = self.mapping_table.item(i, 2).text().strip()
            
            if new_field:
                field_mapping[new_field] = (old_field if old_field else None, default_value if default_value else None)
        return field_mapping
    
    def validate(self) -> tuple[bool, str]:
        """验证输入参数"""
        # 验证输入文件
        if not self.inputFilePath.text():
            return False, "请选择输入矢量文件"
        
        if not os.path.exists(self.inputFilePath.text()):
            return False, "输入文件不存在"
        
        # 检查GDB文件是否选择了图层
        if self.inputFilePath.text().lower().endswith('.gdb') and not self.input_layer_combo.isEnabled():
            return False, "无法读取GDB文件，请检查文件是否有效"
        
        if self.input_layer_combo.isEnabled() and not self.input_layer_combo.currentText():
            return False, "请选择GDB文件中的图层"
        
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
            return
        
        # 2. 获取参数
        input_file = self.inputFilePath.text()
        
        # 获取当前选择的图层名称
        if self.input_layer_combo.isEnabled():
            layer_name = self.input_layer_combo.currentText()
        else:
            layer_name = ""
        
        # 获取输出设置
        output_type = self.output_type_combo.currentText()
        if output_type == "SHP文件":
            output_path = self.outputFilePath.text()
            output_layer = ""
        else:
            output_path = self.output_gdb_path.text()
            output_layer = self.output_gdb_layer.text()
        
        # 获取字段映射
        field_mapping = self.getFieldMapping()
        
        # 3. 显示进度条
        self.progress_container.setVisible(True)
        self.updateProgress(0)
        
        # 4. 显示进度
        self.showProgress("正在整理...")
        
        # 5. 在线程中执行处理
        def run_process():
            try:
                # 调用整理方法
                result = self._organizeFields(input_file, output_path, layer_name, output_type, output_layer, field_mapping)
                
                # 发送成功信号，在主线程中显示成功消息
                self.show_success_signal.emit(f"整理完成！\n{result}")
                
                # 重置进度条
                self.reset_progress()
                
            except Exception as e:
                # 捕获并发送错误信号，在主线程中显示错误消息
                import traceback
                error_msg = f"整理失败: {str(e)}\n\n{traceback.format_exc()}"
                self.show_error_signal.emit(error_msg)
                
                # 重置进度条
                self.reset_progress()
        
        # 启动线程
        threading.Thread(target=run_process, daemon=True).start()
    
    def _organizeFields(self, input_file: str, output_path: str, layer_name: str, output_type: str, output_layer: str, field_mapping: dict) -> str:
        """
        整理要素字段
        
        参数:
            input_file: 输入矢量文件路径
            output_path: 输出文件路径
            layer_name: 输入图层名称（仅GDB文件需要）
            output_type: 输出类型（"SHP文件"或"GDB图层"）
            output_layer: 输出图层名称（仅GDB输出需要）
            field_mapping: 字段映射关系
            
        返回:
            处理结果描述
        """
        # 读取输入数据
        self.update_progress_signal.emit(20, "正在读取输入数据...")
        if input_file.lower().endswith('.gdb') and layer_name:
            # 读取GDB中的特定图层
            gdf = gpd.read_file(input_file, layer=layer_name)
        else:
            # 读取SHP或其他格式文件
            gdf = gpd.read_file(input_file)
        
        self.update_progress_signal.emit(40, "正在整理字段...")
        
        # 创建新的GeoDataFrame
        organized_gdf = gpd.GeoDataFrame(geometry=gdf.geometry, crs=gdf.crs)
        
        # 遍历字段映射关系
        for new_field, (old_field, default_value) in field_mapping.items():
            if old_field is not None:
                # 如果原始字段存在，则复制值
                if old_field in gdf.columns:
                    organized_gdf[new_field] = gdf[old_field]
                else:
                    # 如果原始字段不存在，则使用默认值
                    organized_gdf[new_field] = default_value
            else:
                # 如果原始字段名为None，表示继承
                if new_field in gdf.columns:
                    organized_gdf[new_field] = gdf[new_field]
                else:
                    # 如果原始字段不存在，则使用默认值
                    organized_gdf[new_field] = default_value
        
        self.update_progress_signal.emit(70, "正在保存输出文件...")
        
        # 保存输出文件
        if output_type == "SHP文件":
            # 保存为SHP文件
            organized_gdf.to_file(output_path, driver='ESRI Shapefile')
            result_msg = f"成功整理 {len(gdf)} 个要素的字段\n"
            result_msg += f"输入文件: {os.path.basename(input_file)}\n"
            result_msg += f"输出文件: {os.path.basename(output_path)}\n"
            result_msg += f"整理后的字段列表: {list(organized_gdf.columns)}"
        else:
            # 保存为GDB图层
            organized_gdf.to_file(output_path, layer=output_layer, driver='OpenFileGDB')
            result_msg = f"成功整理 {len(gdf)} 个要素的字段\n"
            result_msg += f"输入文件: {os.path.basename(input_file)}\n"
            result_msg += f"输出GDB: {os.path.basename(output_path)}\n"
            result_msg += f"输出图层: {output_layer}\n"
            result_msg += f"整理后的字段列表: {list(organized_gdf.columns)}"
        
        # 更新进度为100%
        self.update_progress_signal.emit(100, "整理完成！")
        
        return result_msg
