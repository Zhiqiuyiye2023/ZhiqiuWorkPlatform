# coding:utf-8
"""
标识卡片功能
"""

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData
from PyQt6.QtGui import QDrag
from qfluentwidgets import LineEdit, PrimaryPushButton, StateToolTip, ComboBox, BodyLabel
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction
import os
import sys


class IdentifyFeaturesFunction(BaseFunction):
    """标识卡片功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>"
            "标识卡片功能，支持添加SHP和GDB图层，可调整图层顺序"
        )
        super().__init__("标识卡片", description, parent)
        
        self._initUI()
        # 不使用默认执行按钮
        self.stateTooltip = None
        self._running = False
        self.layers = []  # 存储图层信息
    
    def _initUI(self):
        """初始化界面"""
        # 第一行：操作按钮区域
        hBoxLayout1 = QHBoxLayout()
        self.buttonAddSHP = PrimaryPushButton(self.tr('添加SHP文件'), self, FIF.DOCUMENT)
        self.buttonAddSHP.clicked.connect(self._addSHPFile)
        self.buttonAddGDB = PrimaryPushButton(self.tr('添加GDB图层'), self, FIF.FOLDER)
        self.buttonAddGDB.clicked.connect(self._addGDBLayersDialog)
        self.buttonExecute = PrimaryPushButton(self.tr('开始执行'), self, FIF.SEND)
        self.buttonExecute.clicked.connect(self.execute)
        hBoxLayout1.addWidget(self.buttonAddSHP)
        hBoxLayout1.addWidget(self.buttonAddGDB)
        hBoxLayout1.addStretch(1)
        hBoxLayout1.addWidget(self.buttonExecute)
        self.contentLayout.addLayout(hBoxLayout1)
        
        # 第二行：输出路径设置
        hBoxLayout2 = QHBoxLayout()
        self.buttonBrowseOutput = PrimaryPushButton(self.tr('设置输出路径'), self, FIF.FOLDER)
        self.buttonBrowseOutput.clicked.connect(self._browseOutput)
        self.outputPathLabel = BodyLabel("未设置输出路径")
        self.outputPathLabel.setStyleSheet("color: #666;")
        hBoxLayout2.addWidget(self.buttonBrowseOutput)
        hBoxLayout2.addWidget(self.outputPathLabel)
        hBoxLayout2.addStretch(1)
        self.contentLayout.addLayout(hBoxLayout2)
        
        # 第三行：图层列表
        self.labelLayers = BodyLabel("图层列表：")
        self.contentLayout.addWidget(self.labelLayers)
        
        # 图层列表控件
        from PyQt6.QtWidgets import QListWidget, QListWidgetItem
        from PyQt6.QtCore import Qt
        self.listWidgetLayers = QListWidget(self)
        self.listWidgetLayers.setFixedHeight(250)
        self.listWidgetLayers.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.listWidgetLayers.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.listWidgetLayers.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.contentLayout.addWidget(self.listWidgetLayers)
        
        # 图层顺序调整按钮
        buttonLayout = QHBoxLayout()
        self.buttonMoveUp = PrimaryPushButton(self.tr('上移'), self, FIF.UP)
        self.buttonMoveUp.clicked.connect(self._moveLayerUp)
        self.buttonMoveDown = PrimaryPushButton(self.tr('下移'), self, FIF.DOWN)
        self.buttonMoveDown.clicked.connect(self._moveLayerDown)
        self.buttonRemoveLayer = PrimaryPushButton(self.tr('移除图层'), self, FIF.DELETE)
        self.buttonRemoveLayer.clicked.connect(self._removeLayer)
        buttonLayout.addWidget(self.buttonMoveUp)
        buttonLayout.addWidget(self.buttonMoveDown)
        buttonLayout.addWidget(self.buttonRemoveLayer)
        buttonLayout.addStretch(1)
        self.contentLayout.addLayout(buttonLayout)
        
        # 启用拖拽功能
        self.listWidgetLayers.setAcceptDrops(True)
        self.listWidgetLayers.dragEnterEvent = self._dragEnterEvent
        self.listWidgetLayers.dragMoveEvent = self._dragMoveEvent
        self.listWidgetLayers.dropEvent = self._dropEvent
        
        # 保存输出路径
        self.outputPath = ""
    
    def _addSHPFile(self):
        """添加SHP文件的新方法"""
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(self, "选择SHP文件", "", "Shapefiles (*.shp)")
        if file_path and os.path.exists(file_path):
            # 直接添加SHP图层到列表
            self._addLayerToList(file_path, "SHP文件")
            self.showSuccess("SHP图层添加成功")
        else:
            self.showError("请选择有效的SHP文件")
    
    def _addGDBLayersDialog(self):
        """添加GDB图层的弹窗方法"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QCheckBox, QHBoxLayout, QPushButton, QLabel
        from PyQt6.QtCore import Qt
        
        # 创建弹窗
        dialog = QDialog(self)
        dialog.setWindowTitle("选择GDB图层")
        dialog.setFixedSize(500, 400)
        
        # 创建布局
        layout = QVBoxLayout(dialog)
        
        # 添加GDB选择
        gdb_layout = QHBoxLayout()
        gdb_label = QLabel("GDB文件：")
        gdb_button = PrimaryPushButton(self.tr('浏览'), self, FIF.FOLDER)
        gdb_path_label = BodyLabel("未选择GDB文件")
        gdb_path_label.setStyleSheet("color: #666;")
        gdb_layout.addWidget(gdb_label)
        gdb_layout.addWidget(gdb_button)
        gdb_layout.addWidget(gdb_path_label)
        layout.addLayout(gdb_layout)
        
        # 添加图层列表
        layers_label = QLabel("选择图层：")
        layout.addWidget(layers_label)
        
        layers_list = QListWidget(dialog)
        layers_list.setFixedHeight(200)
        layers_list.setEnabled(False)
        layout.addWidget(layers_list)
        
        # 添加按钮
        button_layout = QHBoxLayout()
        cancel_button = PrimaryPushButton(self.tr('取消'), self, FIF.CANCEL)
        ok_button = PrimaryPushButton(self.tr('确定'), self, FIF.ACCEPT)
        button_layout.addStretch(1)
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)
        layout.addLayout(button_layout)
        
        # 变量保存GDB路径
        selected_gdb_path = ""
        
        def onBrowseGDB():
            """浏览GDB文件"""
            from PyQt6.QtWidgets import QFileDialog
            gdb_path = QFileDialog.getExistingDirectory(dialog, "选择GDB文件")
            if gdb_path and gdb_path.endswith('.gdb'):
                nonlocal selected_gdb_path
                selected_gdb_path = gdb_path
                gdb_path_label.setText(os.path.basename(gdb_path))
                
                # 加载GDB图层
                try:
                    import fiona
                    with fiona.Env():
                        layer_names = fiona.listlayers(gdb_path)
                    
                    # 清空列表
                    layers_list.clear()
                    
                    # 添加图层到列表
                    for layer_name in layer_names:
                        checkbox = QCheckBox(layer_name)
                        item = QListWidgetItem()
                        item.setSizeHint(checkbox.sizeHint())
                        layers_list.addItem(item)
                        layers_list.setItemWidget(item, checkbox)
                    
                    layers_list.setEnabled(True)
                    
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    self.showError(f"加载GDB图层失败: {str(e)}")
        
        def onOk():
            """确定按钮点击事件"""
            nonlocal selected_gdb_path
            if not selected_gdb_path:
                self.showError("请先选择GDB文件")
                return
            
            # 获取选中的图层
            checked_layers = []
            for i in range(layers_list.count()):
                item = layers_list.item(i)
                checkbox = layers_list.itemWidget(item)
                if checkbox and checkbox.isChecked():
                    checked_layers.append(checkbox.text())
            
            if not checked_layers:
                self.showError("请至少选择一个要添加的GDB图层")
                return
            
            # 添加选中的图层到主列表
            for layer_name in checked_layers:
                full_layer_path = f"{selected_gdb_path}|{layer_name}"
                self._addLayerToList(full_layer_path, f"GDB图层: {layer_name}")
            
            self.showSuccess(f"成功添加 {len(checked_layers)} 个GDB图层")
            dialog.accept()
        
        # 连接信号
        gdb_button.clicked.connect(onBrowseGDB)
        cancel_button.clicked.connect(dialog.reject)
        ok_button.clicked.connect(onOk)
        
        # 显示弹窗
        dialog.exec()
    
    def _browseOutput(self):
        """浏览输出路径"""
        from PyQt6.QtWidgets import QFileDialog
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出路径")
        if dir_path:
            self.outputPath = dir_path
            self.outputPathLabel.setText(dir_path)
            self.outputPathLabel.setStyleSheet("color: #333;")
    
    def _addLayerToList(self, layer_path, layer_type):
        """将图层添加到列表中"""
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
            
            self.showSuccess("图层移除成功")
    
    def _updateLayersList(self):
        """更新图层列表"""
        self.layers.clear()
        for i in range(self.listWidgetLayers.count()):
            item = self.listWidgetLayers.item(i)
            layer_data = item.data(Qt.ItemDataRole.UserRole)
            self.layers.append(layer_data)
    
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
            
            self.showSuccess("图层拖拽添加成功")
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
        
        # 获取输出路径
        output_path = self.outputPath
        
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
            if hasattr(self, 'stateTooltip') and self.stateTooltip is not None:
                self.stateTooltip.setContent('处理失败 ❌')
                self.stateTooltip.setState(True)
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(1000, self.stateTooltip.close)
            
            self.showError(f"执行标识卡片功能失败: {str(e)}")
            self._running = False
    
    def _onExecuteSuccess(self, result_file):
        """执行成功处理"""
        if hasattr(self, 'stateTooltip') and self.stateTooltip is not None:
            self.stateTooltip.setContent('处理完成 ✅')
            self.stateTooltip.setState(True)
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1000, self.stateTooltip.close)
        
        # 显示结果位置
        self.showSuccess(f"标识卡片功能执行完成！\n结果文件保存到: {result_file}")
        self._running = False