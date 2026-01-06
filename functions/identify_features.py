# coding:utf-8
"""
标识要素功能
"""

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QGroupBox, QFrame, QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData
from PyQt6.QtGui import QDrag
from qfluentwidgets import LineEdit, PrimaryPushButton, StateToolTip, ComboBox, BodyLabel, PushButton
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction
import os
import sys


class IdentifyFeaturesFunction(BaseFunction):
    """标识要素功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>"
            "标识要素功能，支持添加SHP和GDB图层，可调整图层顺序"
        )
        super().__init__("标识要素", description, parent)
        
        self._initUI()
        
        # 添加执行按钮
        self.execute_btn = self.addExecuteButton("开始标识", self.execute)
        
        # 初始化状态
        self._running = False
        self.layers = []  # 存储图层信息
    
    def _initUI(self):
        """初始化界面"""
        # 创建输入矢量选择区域
        input_vector_group = QGroupBox("输入图层数据", self)
        input_vector_layout = QVBoxLayout(input_vector_group)
        
        # 合并SHP和GDB选择为一个路径显示
        layer_select_layout = QHBoxLayout()
        layer_select_label = QLabel("选择图层文件：")
        self.layer_path = LineEdit(self)
        self.layer_path.setPlaceholderText("选择要添加的SHP或GDB文件")
        self.layer_path.setReadOnly(True)
        
        self.shp_select_btn = PushButton("选择SHP", self, FIF.FOLDER)
        self.shp_select_btn.clicked.connect(lambda: self._selectFeatureFile(shp_only=True))
        self.shp_select_btn.setFixedWidth(120)
        
        self.gdb_select_btn = PushButton("选择GDB", self, FIF.FOLDER)
        self.gdb_select_btn.clicked.connect(lambda: self._selectFeatureFile(gdb_only=True))
        self.gdb_select_btn.setFixedWidth(120)
        
        layer_select_layout.addWidget(layer_select_label)
        layer_select_layout.addWidget(self.layer_path, 1)
        layer_select_layout.addWidget(self.shp_select_btn)
        layer_select_layout.addWidget(self.gdb_select_btn)
        input_vector_layout.addLayout(layer_select_layout)
        
        # GDB图层选择（仅GDB文件显示）
        self.gdb_layer_widget = QWidget()  # 创建一个容器widget
        self.gdb_layer_widget.setObjectName("gdbLayerWidget")
        
        self.gdb_layer_layout = QHBoxLayout(self.gdb_layer_widget)
        gdb_layer_label = QLabel("GDB图层：")
        gdb_layer_label.setObjectName("gdbLayerLabel")
        
        self.gdb_layer_combo = ComboBox(self)
        self.gdb_layer_combo.setObjectName("gdbLayerCombo")
        self.gdb_layer_combo.setPlaceholderText("请先选择GDB文件")
        self.gdb_layer_combo.setEnabled(False)
        
        self.gdb_add_btn = PushButton("添加所选图层", self, FIF.ACCEPT)
        self.gdb_add_btn.setObjectName("gdbAddBtn")
        self.gdb_add_btn.clicked.connect(self._addSelectedGDBLayer)
        self.gdb_add_btn.setEnabled(False)
        self.gdb_add_btn.setFixedWidth(180)
        
        self.gdb_layer_layout.addWidget(gdb_layer_label)
        self.gdb_layer_combo.addItems([])
        self.gdb_layer_layout.addWidget(self.gdb_layer_combo, 1)
        self.gdb_layer_layout.addWidget(self.gdb_add_btn)
        
        # 默认隐藏GDB图层选择容器
        self.gdb_layer_widget.setVisible(False)
        
        # 将容器添加到布局
        input_vector_layout.addWidget(self.gdb_layer_widget)
        
        # 图层列表
        layers_label = QLabel("已添加图层列表：")
        input_vector_layout.addSpacing(10)
        input_vector_layout.addWidget(layers_label)
        
        # 图层列表控件
        from PyQt6.QtWidgets import QListWidget, QListWidgetItem
        from PyQt6.QtCore import Qt
        self.listWidgetLayers = QListWidget(self)
        self.listWidgetLayers.setFixedHeight(200)
        self.listWidgetLayers.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.listWidgetLayers.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.listWidgetLayers.setDefaultDropAction(Qt.DropAction.MoveAction)
        input_vector_layout.addWidget(self.listWidgetLayers)
        
        # 图层操作按钮
        layer_ops_layout = QHBoxLayout()
        self.buttonMoveUp = PushButton(self.tr('上移'), self, FIF.UP)
        self.buttonMoveUp.clicked.connect(self._moveLayerUp)
        self.buttonMoveDown = PushButton(self.tr('下移'), self, FIF.DOWN)
        self.buttonMoveDown.clicked.connect(self._moveLayerDown)
        self.buttonRemoveLayer = PushButton(self.tr('移除图层'), self, FIF.DELETE)
        self.buttonRemoveLayer.clicked.connect(self._removeLayer)
        layer_ops_layout.addWidget(self.buttonMoveUp)
        layer_ops_layout.addWidget(self.buttonMoveDown)
        layer_ops_layout.addWidget(self.buttonRemoveLayer)
        layer_ops_layout.addStretch(1)
        input_vector_layout.addLayout(layer_ops_layout)
        
        # 创建输出设置区域
        output_group = QGroupBox("输出设置", self)
        output_layout = QVBoxLayout(output_group)
        
        # 输出路径设置
        output_path_layout = QHBoxLayout()
        output_path_label = QLabel("输出路径：")
        self.output_path_edit = LineEdit(self)
        self.output_path_edit.setPlaceholderText("选择输出路径")
        self.output_path_edit.setReadOnly(True)
        
        self.output_browse_btn = PushButton("选择路径", self, FIF.FOLDER)
        self.output_browse_btn.clicked.connect(self._browseOutput)
        self.output_browse_btn.setFixedWidth(120)
        
        output_path_layout.addWidget(output_path_label)
        output_path_layout.addWidget(self.output_path_edit, 1)
        output_path_layout.addWidget(self.output_browse_btn)
        output_layout.addLayout(output_path_layout)
        
        # 输出类型选择
        output_type_layout = QHBoxLayout()
        output_type_label = QLabel("输出类型：")
        self.output_type_combo = ComboBox(self)
        self.output_type_combo.addItems(["SHP文件", "GDB图层"])
        self.output_type_combo.currentTextChanged.connect(self._on_output_type_changed)
        
        output_type_layout.addWidget(output_type_label)
        output_type_layout.addWidget(self.output_type_combo, 1)
        output_layout.addLayout(output_type_layout)
        
        # GDB图层名称设置（默认隐藏）
        self.gdb_layer_layout = QHBoxLayout()
        gdb_layer_label = QLabel("GDB图层名称：")
        self.gdb_layer_edit = LineEdit(self)
        self.gdb_layer_edit.setPlaceholderText("输入GDB图层名称")
        
        self.gdb_layer_layout.addWidget(gdb_layer_label)
        self.gdb_layer_layout.addWidget(self.gdb_layer_edit, 1)
        # 默认隐藏GDB图层名称设置
        for i in range(self.gdb_layer_layout.count()):
            widget = self.gdb_layer_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(False)
        output_layout.addLayout(self.gdb_layer_layout)
        
        # 创建进度条容器
        self.progress_container = QWidget(self)
        self.progress_layout = QVBoxLayout(self.progress_container)
        self.progress_layout.setContentsMargins(0, 0, 0, 0)
        self.progress_layout.setSpacing(5)
        
        # 进度文本
        self.progress_text = QLabel("准备开始标识...", self)
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
        
        # 启用拖拽功能
        self.listWidgetLayers.setAcceptDrops(True)
        self.listWidgetLayers.dragEnterEvent = self._dragEnterEvent
        self.listWidgetLayers.dragMoveEvent = self._dragMoveEvent
        self.listWidgetLayers.dropEvent = self._dropEvent
        
        # 初始化输出路径为空
        self.outputPath = ""
    
    def _selectFeatureFile(self, shp_only=False, gdb_only=False):
        """选择要素文件"""
        file_path = ""
        
        from PyQt6.QtWidgets import QFileDialog
        
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
                self, "选择矢量文件", ".", "矢量文件 (*.shp *.geojson *.json *.gpkg);;所有文件 (*)"
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
            
            # 更新统一的图层路径显示
            self.layer_path.setText(file_path)
            
            if shp_only:
                # 直接添加SHP图层到列表
                self._addLayerToList(file_path, "SHP文件")
            elif gdb_only:
                # 更新GDB图层列表
                self._update_gdb_layer_list(file_path)
    
    def _update_gdb_layer_list(self, file_path):
        """更新GDB图层列表"""
        print(f"开始更新GDB图层列表，文件路径: {file_path}")
        
        # 显示整个GDB图层选择容器
        self.gdb_layer_widget.setVisible(True)
        print(f"设置GDB图层选择容器可见: {self.gdb_layer_widget.isVisible()}")
        
        # 清空现有图层列表
        self.gdb_layer_combo.clear()
        
        # 加载GDB图层
        try:
            import fiona
            print("正在使用fiona加载GDB图层...")
            with fiona.Env():
                layer_names = fiona.listlayers(file_path)
            
            print(f"成功加载GDB图层，图层数量: {len(layer_names)}")
            
            # 添加图层到列表
            self.gdb_layer_combo.addItems(layer_names)
            
            # 启用控件
            self.gdb_layer_combo.setEnabled(True)
            self.gdb_add_btn.setEnabled(True)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.showError(f"加载GDB图层失败: {str(e)}")
            # 即使加载失败，也保持容器可见，但禁用添加按钮
            self.gdb_layer_combo.setEnabled(True)  # 允许用户查看错误信息
            self.gdb_add_btn.setEnabled(False)  # 但禁用添加按钮
    
    def _addSelectedGDBLayer(self):
        """添加选中的GDB图层"""
        # 获取选中的图层名称
        layer_name = self.gdb_layer_combo.currentText()
        if not layer_name:
            self.showError("请先选择GDB图层")
            return
        
        # 获取GDB路径 - 使用统一的layer_path
        gdb_path = self.layer_path.text()
        if not gdb_path:
            self.showError("请先选择GDB文件")
            return
        
        # 构建完整的图层路径
        full_layer_path = f"{gdb_path}|{layer_name}"
        
        # 添加图层到列表
        self._addLayerToList(full_layer_path, f"GDB图层: {layer_name}")
        
    def _on_output_type_changed(self, output_type):
        """输出类型变化处理"""
        if output_type == "SHP文件":
            # 隐藏GDB图层名称设置
            for i in range(self.gdb_layer_layout.count()):
                widget = self.gdb_layer_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(False)
        else:
            # 显示GDB图层名称设置
            for i in range(self.gdb_layer_layout.count()):
                widget = self.gdb_layer_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(True)
    
    def _browseOutput(self):
        """浏览输出路径"""
        from PyQt6.QtWidgets import QFileDialog
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出路径")
        if dir_path:
            self.outputPath = dir_path
            self.output_path_edit.setText(dir_path)
            self.output_path_edit.setStyleSheet("color: #333;")
    
    def _addLayerToList(self, layer_path, layer_type):
        """将图层添加到列表中"""
        # 检查是否已经添加了相同路径的图层
        for i in range(self.listWidgetLayers.count()):
            item = self.listWidgetLayers.item(i)
            existing_layer_data = item.data(Qt.ItemDataRole.UserRole)
            if existing_layer_data['path'] == layer_path:
                # 已存在相同路径的图层，不重复添加
                return
        
        # 创建列表项
        item = QListWidgetItem()
        item.setText(f"{layer_type}: {os.path.basename(layer_path)}")
        item.setData(Qt.ItemDataRole.UserRole, {
            'path': layer_path,
            'type': layer_type
        })
        
        # 添加到列表
        self.listWidgetLayers.addItem(item)
        
        # 保存到图层列表
        self.layers.append({
            'path': layer_path,
            'type': layer_type
        })
        
        # 如果是第一个图层，设置默认输出路径为该图层所在目录
        if not self.outputPath:
            # 提取图层所在目录
            if '|' in layer_path:
                # 处理GDB图层，使用GDB文件所在目录
                gdb_path = layer_path.split('|', 1)[0]
                output_dir = os.path.dirname(gdb_path)
            else:
                # 处理SHP图层，使用SHP文件所在目录
                output_dir = os.path.dirname(layer_path)
            
            # 直接使用图层所在目录作为默认输出路径，不创建子文件夹
            self.outputPath = output_dir
            # 更新输出路径显示
            self.output_path_edit.setText(self.outputPath)
            self.output_path_edit.setStyleSheet("color: #333;")
    
    def _moveLayerUp(self):
        """上移图层"""
        current_row = self.listWidgetLayers.currentRow()
        if current_row > 0:
            item = self.listWidgetLayers.takeItem(current_row)
            self.listWidgetLayers.insertItem(current_row - 1, item)
            self.listWidgetLayers.setCurrentRow(current_row - 1)
            
            # 更新图层列表
            self._updateLayersList()
    
    def _moveLayerDown(self):
        """下移图层"""
        current_row = self.listWidgetLayers.currentRow()
        if current_row < self.listWidgetLayers.count() - 1:
            item = self.listWidgetLayers.takeItem(current_row)
            self.listWidgetLayers.insertItem(current_row + 1, item)
            self.listWidgetLayers.setCurrentRow(current_row + 1)
            
            # 更新图层列表
            self._updateLayersList()
    
    def _removeLayer(self):
        """移除图层"""
        current_row = self.listWidgetLayers.currentRow()
        if current_row >= 0:
            self.listWidgetLayers.takeItem(current_row)
            
            # 更新图层列表
            self._updateLayersList()
    
    def _updateLayersList(self):
        """更新图层列表"""
        self.layers.clear()
        for i in range(self.listWidgetLayers.count()):
            item = self.listWidgetLayers.item(i)
            layer_data = item.data(Qt.ItemDataRole.UserRole)
            self.layers.append(layer_data)
        
        # 如果图层列表不为空，更新默认输出路径为第一个图层的路径
        if self.layers:
            first_layer = self.layers[0]
            layer_path = first_layer['path']
            
            # 提取图层所在目录
            if '|' in layer_path:
                # 处理GDB图层，使用GDB文件所在目录
                gdb_path = layer_path.split('|', 1)[0]
                output_dir = os.path.dirname(gdb_path)
            else:
                # 处理SHP图层，使用SHP文件所在目录
                output_dir = os.path.dirname(layer_path)
            
            # 更新输出路径
            self.outputPath = output_dir
            self.output_path_edit.setText(self.outputPath)
            self.output_path_edit.setStyleSheet("color: #333;")
    
    def _dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().endswith('.shp'):
                    event.acceptProposedAction()
                    return
        event.ignore()
    
    def _dragMoveEvent(self, event):
        """拖拽移动事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def _dropEvent(self, event):
        """拖拽释放事件"""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.endswith('.shp'):
                    # 添加SHP文件到列表
                    self._addLayerToList(file_path, "SHP文件")
            
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def validate(self) -> tuple[bool, str]:
        """验证输入"""
        # 检查是否至少添加了一个图层
        if self.listWidgetLayers.count() == 0:
            return False, "请至少添加一个图层"
        
        # 检查是否设置了输出路径
        if not self.outputPath:
            return False, "请设置输出路径"
        
        # 检查输出路径是否存在
        if not os.path.exists(self.outputPath):
            return False, "输出路径不存在，请选择有效的输出路径"
        
        return True, ""
    
    def updateProgress(self, percent: int, status: str = ""):
        """更新进度条和进度文本"""
        # 更新进度文本
        self.progress_text.setText(f"正在标识... {percent}%")
        
        # 更新进度条样式
        progress_ratio = percent / 100.0
        style = f"""
            QFrame {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #0078D4, stop:{progress_ratio} #0078D4, 
                    stop:{progress_ratio} #e0e0e0, stop:1 #e0e0e0);
                border-radius: 2px;
            }}
        """
        self.progress_bar.setStyleSheet(style)
    
    def reset_progress(self):
        """重置进度条"""
        self.progress_container.setVisible(False)
        self.progress_text.setText("准备开始标识...")
        self.progress_bar.setStyleSheet("""
            QFrame {
                background-color: #e0e0e0;
                border-radius: 2px;
            }
        """)
    
    def execute(self):
        """执行功能"""
        valid, message = self.validate()
        if not valid:
            self.showError(message)
            print(f"验证失败: {message}")
            return
        
        if self._running:
            return
        
        self._running = True
        
        # 显示进度条
        self.progress_container.setVisible(True)
        self.updateProgress(0)
        
        # 显示进度
        self.showProgress("正在标识...")
        
        # 获取输出路径
        output_path = self.outputPath
        
        # 获取输出类型
        output_type = self.output_type_combo.currentText()
        
        # 在线程中执行处理
        def run_process():
            try:
                # 获取图层列表
                layers = []
                for i in range(self.listWidgetLayers.count()):
                    item = self.listWidgetLayers.item(i)
                    layer_data = item.data(Qt.ItemDataRole.UserRole)
                    layers.append(layer_data)
                
                # 调用矢量操作模块中的标识要素功能
                from .矢量操作 import 标识要素
                result_file = 标识要素(layers, output_path)
                
                # 显示结果
                self._onExecuteSuccess(result_file)
                
            except Exception as e:
                # 显示错误信息
                import traceback
                error_msg = f"执行标识要素功能失败: {str(e)}\n\n{traceback.format_exc()}"
                self.show_error_signal.emit(error_msg)
                print(f"执行失败: {str(e)}")
                print(f"详细错误: {traceback.format_exc()}")
                
                # 重置进度条
                self.reset_progress()
                self._running = False
        
        # 启动线程
        import threading
        threading.Thread(target=run_process, daemon=True).start()
    
    def _onExecuteSuccess(self, result_file):
        """执行成功处理"""
        # 更新进度条
        self.updateProgress(100, "标识完成！")
        
        # 显示结果位置
        self.show_success_signal.emit(f"标识要素功能执行完成！\n结果文件保存到: {result_file}")
        print(f"标识成功: {result_file}")
        
        # 重置进度条
        self.reset_progress()
        self._running = False