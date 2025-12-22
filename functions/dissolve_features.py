# coding:utf-8
"""
融合要素功能
"""

from PyQt6.QtWidgets import QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from qfluentwidgets import LineEdit, PrimaryPushButton, StateToolTip
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction
import os
import sys


class DissolveThread(QThread):
    """融合功能线程"""
    
    success = pyqtSignal(str)  # 成功信号，传递结果信息
    error = pyqtSignal(str)    # 错误信号，传递错误信息
    
    def __init__(self, input_path, field_name=None, layer_name=None, parent=None):
        """
        Args:
            input_path: 要融合的目录路径或GDB文件路径
            field_name: 用于融合的字段名称，如果为None则不按字段融合
            layer_name: GDB中的图层名称，如果为None则处理所有SHP文件
        """
        super().__init__(parent)
        self.input_path = input_path
        self.field_name = field_name
        self.layer_name = layer_name
    
    def run(self):
        """线程运行方法"""
        try:
            from .矢量操作 import 融合要素
            result = 融合要素(self.input_path, field_name=self.field_name, layer_name=self.layer_name)
            
            if result:
                self.success.emit(f"处理完成！结果保存到: {result}")
            else:
                self.error.emit("融合操作执行失败，没有生成结果文件。")
                
        except Exception as e:
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
        # 第一行：开始执行按钮
        hBoxLayout1 = QHBoxLayout()
        self.buttonExecute = PrimaryPushButton(self.tr('开始执行'), self, FIF.SEND)
        self.buttonExecute.clicked.connect(self.execute)
        hBoxLayout1.addWidget(self.buttonExecute)
        hBoxLayout1.addStretch(1)
        self.contentLayout.addLayout(hBoxLayout1)
        
        # 第二行：目录路径选择（原有功能）
        hBoxLayout2 = QHBoxLayout()
        self.label10 = QLabel("目录路径：")
        self.lineEdit14 = LineEdit(self)
        self.lineEdit14.setPlaceholderText("请输入要融合的目录路径")
        self.buttonBrowseDir = PrimaryPushButton(self.tr('浏览'), self, FIF.FOLDER)
        self.buttonBrowseDir.clicked.connect(self._browseDirectory)
        hBoxLayout2.addWidget(self.label10)
        hBoxLayout2.addWidget(self.lineEdit14)
        hBoxLayout2.addWidget(self.buttonBrowseDir)
        self.contentLayout.addLayout(hBoxLayout2)
        
        # 第三行：GDB路径选择
        hBoxLayout3 = QHBoxLayout()
        self.labelGDB = QLabel("GDB文件：")
        self.lineEditGDB = LineEdit(self)
        self.lineEditGDB.setPlaceholderText("请输入GDB文件路径")
        self.buttonBrowseGDB = PrimaryPushButton(self.tr('浏览'), self, FIF.FOLDER)
        self.buttonBrowseGDB.clicked.connect(self._browseGDB)
        hBoxLayout3.addWidget(self.labelGDB)
        hBoxLayout3.addWidget(self.lineEditGDB)
        hBoxLayout3.addWidget(self.buttonBrowseGDB)
        self.contentLayout.addLayout(hBoxLayout3)
        
        # 第四行：GDB图层选择
        hBoxLayout4 = QHBoxLayout()
        self.labelLayers = QLabel("选择图层：")
        self.buttonLoadLayers = PrimaryPushButton(self.tr('加载图层'), self, FIF.DOWNLOAD)
        self.buttonLoadLayers.clicked.connect(self._loadGDBLayers)
        hBoxLayout4.addWidget(self.labelLayers)
        hBoxLayout4.addWidget(self.buttonLoadLayers)
        hBoxLayout4.addStretch(1)
        self.contentLayout.addLayout(hBoxLayout4)
        
        # 第五行：图层列表勾选框
        from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QCheckBox
        from PyQt6.QtCore import Qt
        self.listWidgetLayers = QListWidget(self)
        self.listWidgetLayers.setFixedHeight(150)
        self.listWidgetLayers.setEnabled(False)  # 初始禁用
        self.contentLayout.addWidget(self.listWidgetLayers)
        
        # 第六行：加载字段按钮
        hBoxLayout4_1 = QHBoxLayout()
        self.labelLoadField = QLabel("字段操作：")
        self.buttonLoadFields = PrimaryPushButton(self.tr('加载字段'), self, FIF.DOWNLOAD)
        self.buttonLoadFields.clicked.connect(self._onLoadFieldsClicked)
        self.buttonLoadFields.setEnabled(False)  # 初始禁用
        hBoxLayout4_1.addWidget(self.labelLoadField)
        hBoxLayout4_1.addWidget(self.buttonLoadFields)
        hBoxLayout4_1.addStretch(1)
        self.contentLayout.addLayout(hBoxLayout4_1)
        
        # 第七行：融合字段选择
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
        self.contentLayout.addLayout(hBoxLayout5)
        
        # 连接图层选择变化信号
        self.listWidgetLayers.itemClicked.connect(self._onLayerSelected)
        
        # 第七行：输出设置
        hBoxLayout6 = QHBoxLayout()
        self.labelOutput = QLabel("输出设置：")
        
        self.outputModeCombo = ComboBox(self)
        self.outputModeCombo.addItems(["输出到SHP文件", "输出到当前GDB"])
        self.outputModeCombo.setCurrentIndex(1)  # 默认输出到当前GDB
        
        # 输出路径（仅在输出到SHP时使用）
        self.labelOutputPath = QLabel("输出路径：")
        self.lineEditOutput = LineEdit(self)
        self.lineEditOutput.setPlaceholderText("请输入输出文件路径")
        self.buttonBrowseOutput = PrimaryPushButton(self.tr('浏览'), self, FIF.FOLDER)
        self.buttonBrowseOutput.clicked.connect(self._browseOutput)
        
        hBoxLayout6.addWidget(self.labelOutput)
        hBoxLayout6.addWidget(self.outputModeCombo)
        hBoxLayout6.addWidget(self.labelOutputPath)
        hBoxLayout6.addWidget(self.lineEditOutput)
        hBoxLayout6.addWidget(self.buttonBrowseOutput)
        self.contentLayout.addLayout(hBoxLayout6)
    
    def _browseDirectory(self):
        """浏览目录"""
        from PyQt6.QtWidgets import QFileDialog
        dir_path = QFileDialog.getExistingDirectory(self, "选择目录")
        if dir_path:
            self.lineEdit14.setText(dir_path)
            # 加载SHP文件的字段
            self._loadSHPFields(dir_path)
    
    def _browseGDB(self):
        """浏览GDB文件"""
        from PyQt6.QtWidgets import QFileDialog
        file_path = QFileDialog.getExistingDirectory(self, "选择GDB文件")
        if file_path and file_path.endswith('.gdb'):
            self.lineEditGDB.setText(file_path)
    
    def _loadSHPFields(self, dir_path):
        """加载SHP文件的字段"""
        try:
            # 清空当前字段列表
            self.fieldCombo.clear()
            self.fieldCombo.addItem("不按字段融合")
            self.fieldCombo.setEnabled(False)
            
            # 找到目录中的所有SHP文件
            import os
            shp_files = []
            for root, _, files in os.walk(dir_path):
                for file in files:
                    if file.endswith(".shp"):
                        shp_files.append(os.path.join(root, file))
            
            if not shp_files:
                self.showError("目录中没有找到SHP文件")
                return
            
            # 读取第一个SHP文件以获取字段
            import geopandas as gpd
            gdf = gpd.read_file(shp_files[0])
            
            # 清理字段名称
            from .矢量操作 import _clean_field_names
            gdf = _clean_field_names(gdf)
            
            # 添加字段到下拉列表
            for field in gdf.columns:
                if field != 'geometry':
                    self.fieldCombo.addItem(field)
            
            self.fieldCombo.setEnabled(True)
            self.showSuccess(f"成功加载SHP文件的字段")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.showError(f"加载SHP字段失败: {str(e)}")
    
    def _browseOutput(self):
        """浏览输出路径"""
        from PyQt6.QtWidgets import QFileDialog
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if dir_path:
            self.lineEditOutput.setText(dir_path)
    
    def _loadGDBLayers(self):
        """加载GDB图层"""
        gdb_path = self.lineEditGDB.text()
        if not gdb_path or not gdb_path.endswith('.gdb'):
            self.showError("请先选择有效的GDB文件")
            return
        
        try:
            # 清空当前图层列表
            self.listWidgetLayers.clear()
            
            # 使用geopandas和fiona获取GDB文件中的所有图层
            import fiona
            
            # 获取所有图层名称
            layer_names = []
            with fiona.Env():
                layer_names = fiona.listlayers(gdb_path)
            
            if not layer_names:
                self.showError("GDB文件中没有找到图层")
                return
            
            # 添加图层到勾选列表
            from PyQt6.QtWidgets import QListWidgetItem, QCheckBox
            from PyQt6.QtCore import Qt
            
            for layer_name in layer_names:
                # 创建复选框
                checkbox = QCheckBox(layer_name)
                
                # 创建列表项
                item = QListWidgetItem()
                item.setSizeHint(checkbox.sizeHint())
                
                # 添加到列表
                self.listWidgetLayers.addItem(item)
                self.listWidgetLayers.setItemWidget(item, checkbox)
            
            self.listWidgetLayers.setEnabled(True)
            self.buttonLoadFields.setEnabled(True)  # 启用加载字段按钮
            self.showSuccess(f"成功加载 {len(layer_names)} 个图层")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.showError(f"加载GDB图层失败: {str(e)}")
    
    def _onLoadFieldsClicked(self):
        """加载字段按钮点击事件"""
        # 检查是否有选中的图层
        gdb_path = self.lineEditGDB.text()
        checked_layers = []
        
        for i in range(self.listWidgetLayers.count()):
            item = self.listWidgetLayers.item(i)
            checkbox = self.listWidgetLayers.itemWidget(item)
            if checkbox and checkbox.isChecked():
                checked_layers.append(checkbox.text())
        
        if not checked_layers:
            self.showError("请先选择一个要加载字段的图层")
            return
        
        # 只处理第一个选中的图层
        layer_name = checked_layers[0]
        
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
            self.showSuccess(f"成功加载图层 {layer_name} 的字段")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.showError(f"加载图层字段失败: {str(e)}")
    
    def _onLayerSelected(self, item):
        """图层选择变化时的处理"""
        # 这里可以添加图层选择变化时的额外处理
        pass
    
    def validate(self) -> tuple[bool, str]:
        """验证输入"""
        # 检查是否至少提供了目录路径或GDB文件
        if not self.lineEdit14.text() and not self.lineEditGDB.text():
            return False, "请至少输入目录路径或GDB文件路径"
        
        # 如果选择了GDB文件，检查是否有勾选的图层
        if self.lineEditGDB.text():
            # 检查是否已加载图层
            if self.listWidgetLayers.count() == 0:
                return False, "请先加载GDB图层"
            
            # 检查是否有勾选的图层
            has_checked = False
            for i in range(self.listWidgetLayers.count()):
                item = self.listWidgetLayers.item(i)
                checkbox = self.listWidgetLayers.itemWidget(item)
                if checkbox and checkbox.isChecked():
                    has_checked = True
                    break
            
            if not has_checked:
                return False, "请至少选择一个要融合的GDB图层"
            
            # 如果输出到SHP文件，检查输出路径
            if self.outputModeCombo.currentText() == "输出到SHP文件" and not self.lineEditOutput.text():
                return False, "请输入输出路径"
        
        # 如果只选择了目录路径，不需要其他验证
        if self.lineEdit14.text() and not self.lineEditGDB.text():
            pass
        
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
        output_path = self.lineEditOutput.text()
        if not output_path:
            # 如果没有指定输出路径，使用默认路径
            if self.lineEdit14.text():
                output_path = self.lineEdit14.text()
            else:
                output_path = os.path.dirname(self.lineEditGDB.text())
        
        # 检查是目录融合还是GDB图层融合
        if self.lineEdit14.text() and not self.lineEditGDB.text():
            # 原有功能：融合目录中的SHP文件
            input_path = self.lineEdit14.text()
            layer_name = None
        elif self.lineEditGDB.text():
            # 新功能：融合GDB图层
            input_path = self.lineEditGDB.text()
            
            # 获取所有勾选的图层名称
            checked_layers = []
            for i in range(self.listWidgetLayers.count()):
                item = self.listWidgetLayers.item(i)
                checkbox = self.listWidgetLayers.itemWidget(item)
                if checkbox and checkbox.isChecked():
                    checked_layers.append(checkbox.text())
            
            # 目前只支持融合一个图层
            layer_name = checked_layers[0] if checked_layers else None
        else:
            # 两者都提供了，优先使用GDB图层融合
            input_path = self.lineEditGDB.text()
            
            # 获取所有勾选的图层名称
            checked_layers = []
            for i in range(self.listWidgetLayers.count()):
                item = self.listWidgetLayers.item(i)
                checkbox = self.listWidgetLayers.itemWidget(item)
                if checkbox and checkbox.isChecked():
                    checked_layers.append(checkbox.text())
            
            # 目前只支持融合一个图层
            layer_name = checked_layers[0] if checked_layers else None
        
        # 获取融合字段
        field_name = None
        if self.fieldCombo.currentIndex() > 0:
            field_name = self.fieldCombo.currentText()
        
        # 创建并启动融合线程
        self.dissolve_thread = DissolveThread(
            input_path=input_path,
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