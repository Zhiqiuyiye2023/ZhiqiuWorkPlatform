# coding:utf-8
"""
融合要素功能
"""

from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from qfluentwidgets import LineEdit, PrimaryPushButton, StateToolTip, PushButton
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction
import os
import sys


class DissolveThread(QThread):
    """融合功能线程"""
    
    success = pyqtSignal(str)  # 成功信号，传递结果信息
    error = pyqtSignal(str)    # 错误信号，传递错误信息
    
    def __init__(self, input_path, output_path, output_type, output_layer=None, field_name=None, layer_name=None, parent=None):
        """
        Args:
            input_path: 要融合的目录路径或GDB文件路径
            output_path: 输出文件路径
            output_type: 输出类型（SHP文件或GDB图层）
            output_layer: 输出GDB图层名称
            field_name: 用于融合的字段名称，如果为None则不按字段融合
            layer_name: GDB中的图层名称，如果为None则处理所有SHP文件
        """
        super().__init__(parent)
        self.input_path = input_path
        self.output_path = output_path
        self.output_type = output_type
        self.output_layer = output_layer
        self.field_name = field_name
        self.layer_name = layer_name
    
    def run(self):
        """线程运行方法"""
        try:
            from .矢量操作 import 融合要素, _clean_field_names
            import geopandas as gpd
            import pandas as pd
            import os
            
            # 先读取和融合数据
            merged_gdf = None
            target_crs = None
            encoding = 'utf-8'
            
            if self.input_path.endswith('.gdb') and self.layer_name:
                # 处理GDB图层
                merged_gdf = gpd.read_file(self.input_path, layer=self.layer_name, encoding=encoding)
                target_crs = merged_gdf.crs
            else:
                # 处理单个SHP文件
                if not self.input_path.endswith('.shp'):
                    self.error.emit("请选择有效的SHP文件！")
                    return
                    
                # 读取SHP文件
                merged_gdf = gpd.read_file(self.input_path, encoding=encoding)
                target_crs = merged_gdf.crs
            
            # 清理字段名称，确保符合SHP格式要求
            merged_gdf = _clean_field_names(merged_gdf)
            
            # 重置索引以确保唯一性
            merged_gdf = merged_gdf.reset_index(drop=True)
            
            # 执行融合操作
            dissolved_gdf = merged_gdf.dissolve(by=self.field_name, aggfunc='first').reset_index(drop=True)
            
            # 保存结果
            if self.output_type == "SHP文件":
                # 输出到SHP文件
                dissolved_gdf.to_file(self.output_path, encoding=encoding)
                result_msg = f"融合完成！结果保存到: {self.output_path}"
            else:
                # 输出到GDB图层
                dissolved_gdf.to_file(self.output_path, layer=self.output_layer, driver='OpenFileGDB')
                result_msg = f"融合完成！结果保存到GDB: {self.output_path}#{self.output_layer}"
            
            self.success.emit(result_msg)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error.emit(f"发生错误: {str(e)}")


class DissolveFeaturesFunction(BaseFunction):
    """融合指定目录中的所有要素功能（包括子目录）"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>"
            "融合目录及子目录中的所有要素文件，将相同类型的要素合并为一个"
        )
        super().__init__("融合指定目录中的所有要素", description, parent)
        
        self._initUI()
        # 不使用默认执行按钮
        self.stateTooltip = None
        self._running = False
    
    def _initUI(self):
        """初始化界面"""
        from PyQt6.QtWidgets import QGroupBox
        
        # 添加执行按钮
        self.buttonExecute = self.addExecuteButton("开始融合", self.execute)
        
        # 输入数据选择区域
        input_group = QGroupBox("输入数据", self)
        input_layout = QVBoxLayout(input_group)
        
        # 第一行：SHP文件和GDB文件选择合并到同一行
        hBoxLayout1 = QHBoxLayout()
        self.labelInput = QLabel("输入路径：")
        self.lineEdit14 = LineEdit(self)
        self.lineEdit14.setPlaceholderText("请选择要融合的SHP文件或GDB文件")
        self.lineEdit14.setReadOnly(True)
        
        self.buttonBrowseDir = PushButton("选择SHP", self, FIF.FOLDER)
        self.buttonBrowseDir.clicked.connect(self._browseDirectory)
        self.buttonBrowseDir.setFixedWidth(140)
        
        self.buttonBrowseGDB = PushButton("选择GDB", self, FIF.FOLDER)
        self.buttonBrowseGDB.clicked.connect(self._browseGDB)
        self.buttonBrowseGDB.setFixedWidth(140)
        
        hBoxLayout1.addWidget(self.labelInput)
        hBoxLayout1.addWidget(self.lineEdit14, 1)
        hBoxLayout1.addWidget(self.buttonBrowseDir)
        hBoxLayout1.addWidget(self.buttonBrowseGDB)
        input_layout.addLayout(hBoxLayout1)
        
        # GDB图层选择（仅GDB文件显示）
        self.gdb_layer_layout = QHBoxLayout()
        self.labelLayers = QLabel("选择图层：")
        from qfluentwidgets import ComboBox
        self.layerCombo = ComboBox(self)
        self.layerCombo.setPlaceholderText("请先选择GDB文件")
        self.layerCombo.setEnabled(False)
        self.layerCombo.currentTextChanged.connect(self._on_layer_selected)
        
        self.buttonLoadLayers = PrimaryPushButton(self.tr('加载图层'), self, FIF.MENU)
        self.buttonLoadLayers.clicked.connect(self._loadGDBLayers)
        self.buttonLoadLayers.setEnabled(False)
        
        self.gdb_layer_layout.addWidget(self.labelLayers)
        self.gdb_layer_layout.addWidget(self.layerCombo, 1)
        self.gdb_layer_layout.addWidget(self.buttonLoadLayers)
        # 默认隐藏GDB图层选择
        for i in range(self.gdb_layer_layout.count()):
            widget = self.gdb_layer_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(False)
        input_layout.addLayout(self.gdb_layer_layout)
        
        # 字段操作区域
        field_group = QGroupBox("融合字段设置", self)
        field_layout = QVBoxLayout(field_group)
        

        
        # 融合字段选择
        hBoxLayout5 = QHBoxLayout()
        self.labelField = QLabel("融合字段：")
        
        from qfluentwidgets import ComboBox
        self.fieldCombo = ComboBox(self)
        self.fieldCombo.setPlaceholderText("选择用于融合的字段")
        self.fieldCombo.addItem("不按字段融合")
        self.fieldCombo.setEnabled(False)  # 初始禁用
        
        hBoxLayout5.addWidget(self.labelField)
        hBoxLayout5.addWidget(self.fieldCombo)
        hBoxLayout5.addStretch(1)
        field_layout.addLayout(hBoxLayout5)
        
        # 输出设置区域
        output_group = QGroupBox("输出设置", self)
        output_layout = QVBoxLayout(output_group)
        
        # 输出类型选择
        output_type_layout = QHBoxLayout()
        output_type_label = QLabel("输出类型：")
        self.outputModeCombo = ComboBox(self)
        self.outputModeCombo.addItems(["SHP文件", "GDB图层"])
        self.outputModeCombo.setCurrentIndex(0)  # 默认输出到SHP文件
        self.outputModeCombo.currentTextChanged.connect(self._on_output_type_changed)
        
        output_type_layout.addWidget(output_type_label)
        output_type_layout.addWidget(self.outputModeCombo, 1)
        output_layout.addLayout(output_type_layout)
        
        # SHP输出设置
        self.shp_output_layout = QHBoxLayout()
        shp_output_label = QLabel("SHP输出路径：")
        self.lineEditOutput = LineEdit(self)
        self.lineEditOutput.setPlaceholderText("选择输出SHP文件路径")
        self.lineEditOutput.setReadOnly(True)
        
        self.buttonBrowseOutput = PushButton("选择输出路径", self, FIF.SAVE)
        self.buttonBrowseOutput.clicked.connect(self._browseOutput)
        
        self.shp_output_layout.addWidget(shp_output_label)
        self.shp_output_layout.addWidget(self.lineEditOutput, 1)
        self.shp_output_layout.addWidget(self.buttonBrowseOutput)
        output_layout.addLayout(self.shp_output_layout)
        
        # GDB输出设置
        self.gdb_output_layout = QHBoxLayout()
        gdb_output_label = QLabel("GDB输出路径：")
        self.lineEditGDBOutput = LineEdit(self)
        self.lineEditGDBOutput.setPlaceholderText("选择输出GDB文件路径")
        self.lineEditGDBOutput.setReadOnly(True)
        
        self.buttonBrowseGDBOutput = PushButton("选择GDB", self, FIF.FOLDER)
        self.buttonBrowseGDBOutput.clicked.connect(self._browseGDBOutput)
        
        self.gdb_output_layout.addWidget(gdb_output_label)
        self.gdb_output_layout.addWidget(self.lineEditGDBOutput, 1)
        self.gdb_output_layout.addWidget(self.buttonBrowseGDBOutput)
        # 默认隐藏GDB输出设置
        for i in range(self.gdb_output_layout.count()):
            widget = self.gdb_output_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(False)
        output_layout.addLayout(self.gdb_output_layout)
        
        # GDB图层名称设置
        self.gdb_layer_name_layout = QHBoxLayout()
        gdb_layer_name_label = QLabel("GDB图层名称：")
        self.outputGDBLayer = LineEdit(self)
        self.outputGDBLayer.setPlaceholderText("输入输出图层名称")
        
        self.gdb_layer_name_layout.addWidget(gdb_layer_name_label)
        self.gdb_layer_name_layout.addWidget(self.outputGDBLayer, 1)
        # 默认隐藏GDB图层名称设置
        for i in range(self.gdb_layer_name_layout.count()):
            widget = self.gdb_layer_name_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(False)
        output_layout.addLayout(self.gdb_layer_name_layout)
        
        # 初始显示SHP输出选项
        self._on_output_type_changed("SHP文件")
        
        # 将所有组件添加到内容布局
        self.contentLayout.addWidget(input_group)
        self.contentLayout.addWidget(field_group)
        self.contentLayout.addWidget(output_group)
    
    def _browseDirectory(self):
        """浏览SHP文件"""
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择SHP文件", ".", "Shapefiles (*.shp);;所有文件 (*.*)"
        )
        if file_path:
            self.lineEdit14.setText(file_path)
            # 隐藏GDB相关控件
            self._hide_gdb_controls()
            # 加载SHP文件的字段
            self._loadSHPFields(file_path)
            # 自动生成输出路径
            self._autoGenerateOutputPath(file_path)
    
    def _browseGDB(self):
        """浏览GDB文件"""
        from PyQt6.QtWidgets import QFileDialog
        file_path = QFileDialog.getExistingDirectory(self, "选择GDB文件")
        if file_path and file_path.endswith('.gdb'):
            self.lineEdit14.setText(file_path)
            # 显示GDB相关控件
            self._show_gdb_controls()
            # 自动生成输出路径
            self._autoGenerateOutputPath(file_path)
            # 自动加载GDB图层到下拉控件
            self._loadGDBLayers()
    
    def _show_gdb_controls(self):
        """显示GDB相关控件"""
        for i in range(self.gdb_layer_layout.count()):
            widget = self.gdb_layer_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(True)
        self.buttonLoadLayers.setEnabled(True)
        self.layerCombo.setEnabled(True)
    
    def _hide_gdb_controls(self):
        """隐藏GDB相关控件"""
        for i in range(self.gdb_layer_layout.count()):
            widget = self.gdb_layer_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(False)
        self.buttonLoadLayers.setEnabled(False)
        self.layerCombo.setEnabled(False)
        self.layerCombo.clear()
        self.layerCombo.setPlaceholderText("请先选择GDB文件")
    
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
            
            for i in range(self.gdb_layer_name_layout.count()):
                widget = self.gdb_layer_name_layout.itemAt(i).widget()
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
            
            for i in range(self.gdb_layer_name_layout.count()):
                widget = self.gdb_layer_name_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(True)
    
    def _browseGDBOutput(self):
        """浏览GDB输出路径"""
        from PyQt6.QtWidgets import QFileDialog
        file_path = QFileDialog.getExistingDirectory(self, "选择输出GDB文件")
        if file_path and file_path.endswith('.gdb'):
            self.lineEditGDBOutput.setText(file_path)
    
    def _autoGenerateOutputPath(self, input_path):
        """自动生成输出文件名"""
        import os
        dir_name = os.path.dirname(input_path)
        base_name = os.path.basename(input_path)
        name, ext = os.path.splitext(base_name)
        
        if self.outputModeCombo.currentText() == "SHP文件":
            # 自动生成SHP输出路径
            output_path = os.path.join(dir_name, f"{name}_dissolved.shp")
            self.lineEditOutput.setText(output_path)
        else:
            # 自动生成GDB输出路径和图层名称
            if input_path.endswith('.gdb'):
                self.lineEditGDBOutput.setText(input_path)
                self.outputGDBLayer.setText(f"{name}_dissolved")
            else:
                # 如果输入是SHP文件，默认GDB输出路径为当前目录下的output.gdb
                output_gdb = os.path.join(dir_name, "output.gdb")
                self.lineEditGDBOutput.setText(output_gdb)
                self.outputGDBLayer.setText(f"{name}_dissolved")
    
    def _loadSHPFields(self, file_path):
        """加载SHP文件的字段"""
        try:
            # 清空当前字段列表
            self.fieldCombo.clear()
            self.fieldCombo.addItem("不按字段融合")
            self.fieldCombo.setEnabled(False)
            
            # 检查文件是否为SHP文件
            if not file_path.endswith(".shp"):
                self.showError("请选择有效的SHP文件")
                return
            
            # 读取SHP文件以获取字段
            import geopandas as gpd
            gdf = gpd.read_file(file_path)
            
            # 清理字段名称
            from .矢量操作 import _clean_field_names
            gdf = _clean_field_names(gdf)
            
            # 添加字段到下拉列表
            for field in gdf.columns:
                if field != 'geometry':
                    self.fieldCombo.addItem(field)
            
            self.fieldCombo.setEnabled(True)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.showError(f"加载SHP字段失败: {str(e)}")
    
    def _browseOutput(self):
        """浏览输出路径"""
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getSaveFileName(
            self, "选择输出SHP文件", ".", "Shapefiles (*.shp);;所有文件 (*.*)"
        )
        if file_path:
            # 确保文件扩展名是.shp
            if not file_path.lower().endswith('.shp'):
                file_path += '.shp'
            self.lineEditOutput.setText(file_path)
    
    def _loadGDBLayers(self):
        """加载GDB图层"""
        gdb_path = self.lineEdit14.text()
        if not gdb_path or not gdb_path.endswith('.gdb'):
            self.showError("请先选择有效的GDB文件")
            return
        
        try:
            # 清空当前图层列表
            self.layerCombo.clear()
            
            # 使用geopandas和fiona获取GDB文件中的所有图层
            import fiona
            
            # 获取所有图层名称
            layer_names = []
            with fiona.Env():
                layer_names = fiona.listlayers(gdb_path)
            
            if not layer_names:
                self.showError("GDB文件中没有找到图层")
                return
            
            # 添加图层到下拉列表
            self.layerCombo.addItems(layer_names)
            
            self.layerCombo.setEnabled(True)
            # 自动加载第一个图层的字段
            if layer_names:
                self.layerCombo.setCurrentIndex(0)
                self._loadGDBLayerFields(layer_names[0])
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.showError(f"加载GDB图层失败: {str(e)}")
    
    def _on_layer_selected(self, layer_name):
        """图层选择变化时的处理"""
        if layer_name:
            self._loadGDBLayerFields(layer_name)
    
    def _loadGDBLayerFields(self, layer_name):
        """加载GDB图层的字段"""
        # 检查是否有选中的图层
        gdb_path = self.lineEdit14.text()
        if not gdb_path or not gdb_path.endswith('.gdb'):
            self.showError("请先选择有效的GDB文件")
            return
        
        try:
            # 清空当前字段列表
            self.fieldCombo.clear()
            self.fieldCombo.addItem("不按字段融合")
            self.fieldCombo.setEnabled(False)
            
            # 读取图层以获取字段
            import geopandas as gpd
            gdf = gpd.read_file(gdb_path, layer=layer_name)
            
            # 清理字段名称
            from .矢量操作 import _clean_field_names
            gdf = _clean_field_names(gdf)
            
            # 添加字段到下拉列表
            for field in gdf.columns:
                if field != 'geometry':
                    self.fieldCombo.addItem(field)
            
            self.fieldCombo.setEnabled(True)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.showError(f"加载图层字段失败: {str(e)}")
    
    def validate(self) -> tuple[bool, str]:
        """验证输入"""
        import os
        # 检查是否提供了输入路径
        if not self.lineEdit14.text():
            return False, "请选择要融合的目录、SHP文件或GDB文件"
        
        # 如果是GDB文件，检查是否已选择图层
        if self.lineEdit14.text().endswith('.gdb'):
            # 检查是否已加载图层
            if self.layerCombo.count() == 0:
                return False, "请先加载GDB图层"
            
            # 检查是否已选择图层
            if not self.layerCombo.currentText():
                return False, "请选择一个要融合的GDB图层"
        
        # 验证输出设置
        output_type = self.outputModeCombo.currentText()
        if output_type == "SHP文件":
            # 验证SHP输出
            if not self.lineEditOutput.text():
                return False, "请选择SHP输出路径"
            
            # 检查输出目录是否存在
            import os
            output_dir = os.path.dirname(self.lineEditOutput.text())
            if not os.path.exists(output_dir):
                return False, "SHP输出目录不存在"
        else:
            # 验证GDB输出
            if not self.lineEditGDBOutput.text():
                return False, "请选择GDB输出路径"
            
            if not os.path.exists(self.lineEditGDBOutput.text()):
                return False, "GDB输出文件不存在"
            
            if not self.lineEditGDBOutput.text().lower().endswith('.gdb'):
                return False, "请选择有效的GDB文件"
            
            if not self.outputGDBLayer.text():
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
        
        # 获取输出设置
        output_type = self.outputModeCombo.currentText()
        if output_type == "SHP文件":
            output_path = self.lineEditOutput.text()
        else:
            output_path = self.lineEditGDBOutput.text()
        
        # 检查是SHP融合还是GDB图层融合
        input_path = self.lineEdit14.text()
        layer_name = None
        
        if input_path.endswith('.gdb'):
            # GDB图层融合
            # 获取下拉列表中选中的图层名称
            layer_name = self.layerCombo.currentText()
        
        # 获取融合字段
        field_name = None
        if self.fieldCombo.currentIndex() > 0:
            field_name = self.fieldCombo.currentText()
        
        # 获取输出参数
        output_type = self.outputModeCombo.currentText()
        output_path = self.lineEditOutput.text() if output_type == "SHP文件" else self.lineEditGDBOutput.text()
        output_layer = self.outputGDBLayer.text() if output_type == "GDB图层" else None
        
        # 创建并启动融合线程
        self.dissolve_thread = DissolveThread(
            input_path=input_path,
            output_path=output_path,
            output_type=output_type,
            output_layer=output_layer,
            field_name=field_name,
            layer_name=layer_name,
            parent=self
        )
        
        # 连接信号
        self.dissolve_thread.success.connect(self._onDissolveSuccess)
        self.dissolve_thread.error.connect(self._onDissolveError)
        self.dissolve_thread.finished.connect(self._onDissolveFinished)
        
        # 启动线程
        self.dissolve_thread.start()
    
    def _onDissolveSuccess(self, message: str):
        """融合操作成功处理"""
        if hasattr(self, 'stateTooltip') and self.stateTooltip is not None:
            self.stateTooltip.setContent('处理完成 ✅')
            self.stateTooltip.setState(True)
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1000, self.stateTooltip.close)
        
        self.showSuccess(message)
    
    def _onDissolveError(self, message: str):
        """融合操作错误处理"""
        if hasattr(self, 'stateTooltip') and self.stateTooltip is not None:
            self.stateTooltip.setContent('处理失败 ❌')
            self.stateTooltip.setState(True)
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1000, self.stateTooltip.close)
        
        self.showError(message)
    
    def _onDissolveFinished(self):
        """融合线程结束处理"""
        self._running = False