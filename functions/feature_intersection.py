# coding:utf-8
"""
要素相交功能模块
读取SHP或GDB文件，检测要素重叠区域，输出相交结果
"""

from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QFileDialog, QWidget, QFrame, QGroupBox
from PyQt6.QtCore import Qt
from qfluentwidgets import LineEdit, PushButton, ComboBox
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction
import threading
import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import MultiPolygon, Polygon

# 尝试从不同模块导入make_valid函数，兼容不同版本的shapely库
try:
    from shapely.ops import make_valid
except ImportError:
    try:
        from shapely.validation import make_valid
    except ImportError:
        # 如果都导入失败，定义一个简单的替代函数
        def make_valid(geom):
            return geom


class FeatureIntersectionFunction(BaseFunction):
    """要素相交功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>"
            "读取SHP或GDB文件，检测要素重叠区域，输出相交结果"
        )
        super().__init__("要素相交", description, parent)
        
        # 初始化UI
        self._initUI()
        
        # 添加执行按钮
        self.execute_btn = self.addExecuteButton("开始相交", self.execute)
        
        # 启用拖拽支持
        self.setAcceptDrops(True)
    
    def _initUI(self):
        """初始化UI界面"""
        # 连接进度信号到UI更新槽
        self.progress.connect(self._onProgressUpdate)
        
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
        
        # 添加到列表按钮
        self.add_to_list_btn = PushButton("添加到列表", self, FIF.ADD)
        self.add_to_list_btn.clicked.connect(self._addToLayerList)
        self.add_to_list_btn.setFixedWidth(120)
        self.add_to_list_btn.setEnabled(False)
        
        self.source_layer_layout.addWidget(source_label)
        self.source_layer_layout.addWidget(self.source_layer_combo, 1)
        self.source_layer_layout.addWidget(self.add_to_list_btn)
        # 默认隐藏图层选择和添加到列表按钮
        for i in range(self.source_layer_layout.count()):
            widget = self.source_layer_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(False)
        input_vector_layout.addLayout(self.source_layer_layout)
        
        # 相交图层列表
        list_label = QLabel("相交图层列表：")
        input_vector_layout.addWidget(list_label)
        
        # 图层列表
        from PyQt6.QtWidgets import QListWidget, QListWidgetItem
        self.layer_list = QListWidget(self)
        self.layer_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        # 启用拖拽支持
        self.layer_list.setAcceptDrops(True)
        # 增加列表高度
        self.layer_list.setFixedHeight(200)
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
        
        # 用于存储图层信息的列表
        self.layers_info = []
        
        # 输出设置区域
        output_group = QGroupBox("输出设置", self)
        output_layout = QVBoxLayout(output_group)
        
        # 输出类型和字段保留选择（同一行）
        output_top_layout = QHBoxLayout()
        
        # 输出类型选择
        output_type_label = QLabel("输出类型：")
        self.output_type_combo = ComboBox(self)
        self.output_type_combo.addItems(["SHP文件", "GDB图层"])
        self.output_type_combo.currentTextChanged.connect(self._on_output_type_changed)
        output_top_layout.addWidget(output_type_label)
        output_top_layout.addWidget(self.output_type_combo, 1)
        
        # 添加分隔符
        output_top_layout.addSpacing(20)
        
        # 字段保留设置
        field_label = QLabel("保留字段：")
        self.field_preserve_combo = ComboBox(self)
        self.field_preserve_combo.setPlaceholderText("选择要保留字段的图层")
        # 默认添加"保留所有字段"选项
        self.field_preserve_combo.addItem("保留所有字段")
        # 使用setProperty存储当前选中项信息
        self.field_preserve_combo.setProperty("currentFieldPreserveOption", "all")
        output_top_layout.addWidget(field_label)
        output_top_layout.addWidget(self.field_preserve_combo, 1)
        
        output_layout.addLayout(output_top_layout)
        
        # SHP输出路径
        self.shp_output_layout = QHBoxLayout()
        shp_output_label = QLabel("SHP输出路径：")
        self.outputFilePath = LineEdit(self)
        self.outputFilePath.setPlaceholderText("选择输出SHP文件路径")
        self.outputFilePath.setReadOnly(True)
        
        self.outputFileBtn = PushButton("选择输出路径", self, FIF.SAVE)
        self.outputFileBtn.clicked.connect(self._select_output_shp)
        self.outputFileBtn.setFixedWidth(150)
        
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
        self.output_gdb_btn.setFixedWidth(150)
        
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
        
        self.progress_layout = QVBoxLayout(self.progress_container)
        self.progress_layout.setContentsMargins(0, 0, 0, 0)
        self.progress_layout.setSpacing(5)
        
        # 进度文本
        self.progress_text = QLabel("准备开始相交...", self)
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
            # 选择SHP文件，支持多选
            file_paths, _ = QFileDialog.getOpenFileNames(
                self, 
                "选择SHP文件", 
                "", 
                "Shapefile文件 (*.shp);;所有文件 (*.*)"
            )
            for file_path in file_paths:
                if file_path:
                    self.source_path.setText(file_path)
                    # 隐藏图层选择
                    for i in range(self.source_layer_layout.count()):
                        widget = self.source_layer_layout.itemAt(i).widget()
                        if widget:
                            widget.setVisible(False)
                    # 设置默认输出路径
                    self._set_default_output_path(file_path)
                    # 直接添加到列表
                    self._addToLayerList()
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
                # 启用添加到列表按钮
                self.add_to_list_btn.setEnabled(True)
    
    def _updateFieldPreserveOptions(self):
        """更新字段保留选项下拉框"""
        # 保存当前选中项数据
        current_option = self.field_preserve_combo.property("currentFieldPreserveOption")
        
        # 清空现有选项
        self.field_preserve_combo.clear()
        
        # 创建选项列表和对应的选项数据列表
        options = ["保留所有字段", "不保留任何字段"]
        option_data = ["all", "none"]
        
        # 添加每个图层作为选项
        for i, layer_info in enumerate(self.layers_info):
            layer_name = os.path.basename(layer_info['path'])
            if layer_info['is_gdb']:
                layer_name += f"|{layer_info['layer']}"
            options.append(f"仅保留第{i+1}个图层的字段: {layer_name}")
            option_data.append(i)
        
        # 添加所有选项
        for option in options:
            self.field_preserve_combo.addItem(option)
        
        # 恢复选中项
        if current_option in option_data:
            new_index = option_data.index(current_option)
            self.field_preserve_combo.setCurrentIndex(new_index)
        else:
            # 默认选择"保留所有字段"
            self.field_preserve_combo.setCurrentIndex(0)
        
        # 更新属性
        self.field_preserve_combo.setProperty("optionDataList", option_data)
        
    def _addToLayerList(self):
        """添加图层到相交列表"""
        source_path = self.source_path.text()
        if not source_path:
            self.showError("请先选择源矢量文件")
            return
        
        is_gdb = source_path.lower().endswith('.gdb')
        if is_gdb:
            layer_name = self.source_layer_combo.currentText()
            if not layer_name:
                self.showError("请先选择GDB图层")
                return
            item_text = f"{os.path.basename(source_path)}|{layer_name}"
        else:
            layer_name = ""
            item_text = os.path.basename(source_path)
        
        # 添加到列表
        from PyQt6.QtWidgets import QListWidgetItem
        item = QListWidgetItem(item_text)
        self.layer_list.addItem(item)
        
        # 保存图层信息
        self.layers_info.append({
            'path': source_path,
            'layer': layer_name,
            'is_gdb': is_gdb
        })
        
        # 更新字段保留选项
        self._updateFieldPreserveOptions()
        
        # 如果是第一个图层，设置默认输出路径
        if len(self.layers_info) == 1:
            self._set_default_output_path(source_path)
    
    def _selectLayer(self):
        """选择图层（将选中的图层设为当前操作对象）"""
        selected_index = self.layer_list.currentRow()
        if selected_index < 0 or selected_index >= len(self.layers_info):
            self.showError("请先选择列表中的图层")
            return
        
        layer_info = self.layers_info[selected_index]
        self.source_path.setText(layer_info['path'])
        
        if layer_info['is_gdb']:
            # 显示图层选择
            for i in range(self.source_layer_layout.count()):
                widget = self.source_layer_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(True)
            # 加载GDB中的图层
            self._load_gdb_layers(layer_info['path'])
            # 设置当前图层
            index = self.source_layer_combo.findText(layer_info['layer'])
            if index >= 0:
                self.source_layer_combo.setCurrentIndex(index)
        else:
            # 隐藏图层选择
            for i in range(self.source_layer_layout.count()):
                widget = self.source_layer_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(False)
    
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
        # 更新字段保留选项
        self._updateFieldPreserveOptions()
        # 更新默认输出路径，按照列表第一条数据来设定
        if self.layers_info:
            first_layer_path = self.layers_info[0]['path']
            self._set_default_output_path(first_layer_path)
    
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
        # 更新字段保留选项
        self._updateFieldPreserveOptions()
        # 更新默认输出路径，按照列表第一条数据来设定
        if self.layers_info:
            first_layer_path = self.layers_info[0]['path']
            self._set_default_output_path(first_layer_path)
    
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
        
        # 更新字段保留选项
        self._updateFieldPreserveOptions()
        # 更新默认输出路径，按照列表第一条数据来设定
        if self.layers_info:
            first_layer_path = self.layers_info[0]['path']
            self._set_default_output_path(first_layer_path)
        else:
            # 如果列表为空，清空输出路径
            self.outputFilePath.clear()
            self.output_gdb_path.clear()
            self.output_gdb_layer.clear()
    
    def _clearLayerList(self):
        """清空图层列表"""
        if self.layer_list.count() == 0:
            return
        
        # 清空列表
        self.layer_list.clear()
        # 清空图层信息
        self.layers_info.clear()
        
        # 更新字段保留选项
        self._updateFieldPreserveOptions()
        # 清空输出路径
        self.outputFilePath.clear()
        self.output_gdb_path.clear()
        self.output_gdb_layer.clear()
    
    def _onProgressUpdate(self, percent: int, status: str = ""):
        """处理进度更新信号，在主线程更新UI"""
        try:
            # 如果子类有进度条UI元素，更新UI
            if hasattr(self, 'progress_text') and hasattr(self, 'progress_bar'):
                # 更新进度文本
                if status:
                    self.progress_text.setText(f"{status}")
                else:
                    self.progress_text.setText(f"正在执行... {percent}%")
                
                # 更新进度条样式
                progress_ratio = percent / 100.0
                # 使用字符串拼接构建CSS样式
                style = f"""QFrame {{
                        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                            stop:0 #0078D4, stop:{progress_ratio} #0078D4, 
                            stop:{progress_ratio} #e0e0e0, stop:1 #e0e0e0);
                        border-radius: 2px;
                    }}
                """
                self.progress_bar.setStyleSheet(style)
        except RuntimeError:
            # 捕获UI元素已被删除的错误
            pass
    
    def _load_gdb_layers(self, gdb_path):
        """加载GDB中的图层"""
        try:
            import fiona
            # 获取GDB中的所有图层
            layer_names = []
            with fiona.Env():
                # 列出所有图层名称
                all_layers = fiona.listlayers(gdb_path)
                for layer_name in all_layers:
                    # 打开图层获取其属性
                    with fiona.open(gdb_path, layer=layer_name) as src:
                        # 直接添加所有图层，不做几何类型过滤
                        layer_names.append(layer_name)
            
            self.source_layer_combo.clear()
            if layer_names:
                self.source_layer_combo.addItems(layer_names)
                self.source_layer_combo.setEnabled(True)
            else:
                self.source_layer_combo.addItem("GDB中未找到图层")
                self.source_layer_combo.setEnabled(False)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.showError(f"加载GDB图层失败: {str(e)}")
    
    def _on_layer_changed(self, layer_name):
        """图层选择变化时更新默认输出图层名"""
        source_path = self.source_path.text()
        if source_path.lower().endswith('.gdb') and layer_name:
            # 更新默认输出图层名
            default_layer_name = f"{layer_name}_intersection"
            self.output_gdb_layer.setText(default_layer_name)
    
    def dragEnterEvent(self, event):
        """拖拽进入事件处理"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dragMoveEvent(self, event):
        """拖拽移动事件处理"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        """拖拽释放事件处理"""
        from PyQt6.QtWidgets import QListWidgetItem
        
        # 处理拖拽的文件
        new_files_added = False
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):  # 只处理文件，不处理文件夹
                # 检查是否为支持的矢量文件格式
                if file_path.lower().endswith('.shp'):
                    # SHP文件
                    item_text = os.path.basename(file_path)
                    # 添加到列表
                    item = QListWidgetItem(item_text)
                    self.layer_list.addItem(item)
                    
                    # 保存图层信息
                    self.layers_info.append({
                        'path': file_path,
                        'layer': '',
                        'is_gdb': False
                    })
                    
                    new_files_added = True
                elif file_path.lower().endswith('.gdb'):
                    # GDB文件，需要选择图层
                    # 这里简化处理，直接添加GDB文件路径，实际使用时需要选择图层
                    item_text = os.path.basename(file_path) + "|需选择图层"
                    item = QListWidgetItem(item_text)
                    self.layer_list.addItem(item)
                    
                    # 保存图层信息
                    self.layers_info.append({
                        'path': file_path,
                        'layer': '',
                        'is_gdb': True
                    })
                    
                    new_files_added = True
        
        if new_files_added:
            # 更新字段保留选项
            self._updateFieldPreserveOptions()
            # 更新默认输出路径，按照列表第一条数据来设定
            if self.layers_info:
                first_layer_path = self.layers_info[0]['path']
                self._set_default_output_path(first_layer_path)
        
        event.acceptProposedAction()
    
    def _set_default_output_path(self, source_path):
        """根据源文件设置默认输出路径"""
        if source_path.lower().endswith('.shp'):
            # SHP文件：默认输出到源文件所在目录，文件名加上"_intersection"后缀
            dir_name = os.path.dirname(source_path)
            base_name = os.path.basename(source_path)
            name_without_ext = os.path.splitext(base_name)[0]
            default_output_path = os.path.join(dir_name, f"{name_without_ext}_intersection.shp")
            self.outputFilePath.setText(default_output_path)
        elif source_path.lower().endswith('.gdb'):
            # GDB文件：默认输出到同一GDB，图层名加上"_intersection"后缀
            self.output_gdb_path.setText(source_path)
            # 如果已经选择了图层，使用图层名作为默认输出图层名
            if self.source_layer_combo.currentText():
                default_layer_name = f"{self.source_layer_combo.currentText()}_intersection"
                self.output_gdb_layer.setText(default_layer_name)
            else:
                self.output_gdb_layer.setText("output_intersection")
    
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
    
    def validate(self):
        """验证输入参数"""
        # 验证相交图层列表
        if len(self.layers_info) < 2:
            return False, "请至少添加两个图层到相交列表"
        
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
                # 获取字段保留选项
                field_preserve_index = self.field_preserve_combo.currentIndex()
                option_data_list = self.field_preserve_combo.property("optionDataList")
                if option_data_list and field_preserve_index >= 0 and field_preserve_index < len(option_data_list):
                    field_preserve_option = option_data_list[field_preserve_index]
                else:
                    field_preserve_option = "all"
                
                # 更新属性，保存当前选择
                self.field_preserve_combo.setProperty("currentFieldPreserveOption", field_preserve_option)
                
                # 调用处理方法
                result = self._feature_intersection(self.layers_info, output_path, output_type, output_layer, field_preserve_option)
                
                # 发送成功信号
                self.show_success_signal.emit(f"相交处理完成！\n{result}")
                
            except Exception as e:
                import traceback
                error_msg = f"相交处理失败: {str(e)}\n\n{traceback.format_exc()}"
                self.show_error_signal.emit(error_msg)
        
        # 启动线程
        threading.Thread(target=run_process, daemon=True).start()
    
    def _feature_intersection(self, layers_info: list, output_path: str, output_type: str, output_layer: str, field_preserve_option) -> str:
        """
        执行要素相交操作
        
        参数:
            layers_info: 图层信息列表，每个元素包含path、layer、is_gdb字段
            output_path: 输出文件路径
            output_type: 输出类型（"SHP文件"或"GDB图层"）
            output_layer: 输出图层名称（仅GDB输出需要）
            field_preserve_option: 字段保留选项，可以是"all"或图层索引
            
        返回:
            处理结果描述
        """
        # 读取第一个图层作为初始结果
        self.update_progress_signal.emit(10, "正在读取第一个图层...")
        
        layer1 = layers_info[0]
        if layer1['is_gdb']:
            result_gdf = gpd.read_file(layer1['path'], layer=layer1['layer'])
        else:
            result_gdf = gpd.read_file(layer1['path'])
        
        # 确保是面要素
        if result_gdf.geometry.type.iloc[0] not in ['Polygon', 'MultiPolygon']:
            raise ValueError(f"图层 {os.path.basename(layer1['path'])} 不是面要素类型")
        
        # 记录原始图层数量和每个图层的要素数量
        original_layers = len(layers_info)
        original_features = [len(result_gdf)]
        layer_names = [os.path.basename(layer1['path'])]
        if layer1['is_gdb']:
            layer_names[0] += f"|{layer1['layer']}"
        
        # 存储要保留的字段列表
        preserve_fields = None
        if field_preserve_option != "all":
            if field_preserve_option == "none":
                # 不保留任何字段
                preserve_fields = []
            else:
                # 如果指定了要保留的图层，先获取该图层的字段
                preserve_layer = layers_info[field_preserve_option]
                if preserve_layer['is_gdb']:
                    preserve_gdf = gpd.read_file(preserve_layer['path'], layer=preserve_layer['layer'])
                else:
                    preserve_gdf = gpd.read_file(preserve_layer['path'])
                # 只保留非几何字段
                preserve_fields = [col for col in preserve_gdf.columns if col != 'geometry']
        
        # 依次与后续图层相交
        for i in range(1, len(layers_info)):
            layer = layers_info[i]
            layer_name = os.path.basename(layer['path'])
            if layer['is_gdb']:
                layer_name += f"|{layer['layer']}"
            layer_names.append(layer_name)
            
            self.update_progress_signal.emit(10 + i * 70 // len(layers_info), f"正在读取第{i+1}个图层: {layer_name}...")
            
            # 读取当前图层
            if layer['is_gdb']:
                current_gdf = gpd.read_file(layer['path'], layer=layer['layer'])
            else:
                current_gdf = gpd.read_file(layer['path'])
            
            # 确保是面要素
            if current_gdf.geometry.type.iloc[0] not in ['Polygon', 'MultiPolygon']:
                raise ValueError(f"图层 {layer_name} 不是面要素类型")
            
            original_features.append(len(current_gdf))
            
            # 确保坐标系一致
            if result_gdf.crs != current_gdf.crs:
                current_gdf = current_gdf.to_crs(result_gdf.crs)
            
            self.update_progress_signal.emit(20 + i * 70 // len(layers_info), f"正在将第{i+1}个图层与结果相交...")
            
            # 执行相交操作
            try:
                result_gdf = gpd.overlay(result_gdf, current_gdf, how='intersection')
            except Exception as e:
                # 处理列名冲突问题
                if 'duplicate columns' in str(e) or 'suffixes' in str(e):
                    # 为当前图层的列名添加唯一后缀，避免冲突
                    current_gdf_copy = current_gdf.copy()
                    # 为非几何列添加唯一后缀
                    unique_suffix = f'_layer{i+1}'
                    for col in current_gdf_copy.columns:
                        if col != 'geometry':
                            current_gdf_copy.rename(columns={col: f'{col}{unique_suffix}'}, inplace=True)
                    # 使用重命名后的图层重新执行相交操作
                    result_gdf = gpd.overlay(result_gdf, current_gdf_copy, how='intersection')
                else:
                    # 其他错误则抛出
                    raise
            
            # 检查结果是否为空
            if result_gdf.empty:
                # 不抛出异常，只返回提示信息
                self.update_progress_signal.emit(100, f"第{i+1}个图层 {layer_name} 与之前的相交结果没有重叠区域")
                result_msg = f"执行多图层相交完成\n"
                result_msg += f"参与相交的图层数量: {len(layers_info)}\n"
                result_msg += f"在第{i+1}个图层 {layer_name} 处，与之前的相交结果没有重叠区域\n"
                result_msg += f"最终相交结果数量: 0\n"
                return result_msg
        
        # 保存输出文件前处理字段保留
        if preserve_fields is not None:
            if field_preserve_option == "none":
                self.update_progress_signal.emit(85, "正在移除所有属性字段...")
                # 只保留geometry字段
                final_columns = ['geometry']
            else:
                self.update_progress_signal.emit(85, f"正在保留第{field_preserve_option+1}个图层的字段...")
                # 确保geometry字段始终保留
                final_columns = ['geometry'] + [col for col in preserve_fields if col in result_gdf.columns]
            result_gdf = result_gdf[final_columns]
        
        # 保存输出文件
        self.update_progress_signal.emit(90, "正在保存输出文件...")
        
        # 构建结果信息
        result_msg = f"成功执行多图层相交\n"
        result_msg += f"参与相交的图层数量: {original_layers}\n"
        for i in range(original_layers):
            result_msg += f"图层 {i+1}: {layer_names[i]} (要素数量: {original_features[i]})\n"
        result_msg += f"最终相交结果数量: {len(result_gdf)}\n"
        # 添加字段保留信息
        if field_preserve_option == "all":
            result_msg += f"字段保留选项: 保留所有字段\n"
        elif field_preserve_option == "none":
            result_msg += f"字段保留选项: 不保留任何字段\n"
        else:
            result_msg += f"字段保留选项: 仅保留第{field_preserve_option+1}个图层的字段\n"
        
        if output_type == "SHP文件":
            # 保存为SHP文件
            result_gdf.to_file(output_path, driver='ESRI Shapefile')
            result_msg += f"输出文件: {os.path.basename(output_path)}"
        else:
            # 保存为GDB图层
            result_gdf.to_file(output_path, layer=output_layer, driver='OpenFileGDB')
            result_msg += f"输出GDB: {os.path.basename(output_path)}\n"
            result_msg += f"输出图层: {output_layer}"
        
        self.update_progress_signal.emit(100, "处理完成")
        
        return result_msg
