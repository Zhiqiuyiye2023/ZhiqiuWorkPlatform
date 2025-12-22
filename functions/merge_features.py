# coding:utf-8
"""
合并指定目录中的所有要素功能
"""

from PyQt6.QtWidgets import QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from qfluentwidgets import LineEdit, PrimaryPushButton, StateToolTip
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction
import os
import sys


class MergeThread(QThread):
    """合并功能线程"""
    
    success = pyqtSignal(str)  # 成功信号，传递结果信息
    error = pyqtSignal(str)    # 错误信号，传递错误信息
    
    def __init__(self, merge_type, params, parent=None):
        """
        Args:
            merge_type: 合并类型，'dir' 或 'gdb'
            params: 合并参数，根据merge_type不同而不同
        """
        super().__init__(parent)
        self.merge_type = merge_type
        self.params = params
    
    def run(self):
        """线程运行方法"""
        try:
            result = None
            
            if self.merge_type == 'dir':
                # 合并目录中的SHP文件
                folder_path = self.params
                from .矢量操作 import 合并指定目录中的所有要素
                result = 合并指定目录中的所有要素(folder_path)
            elif self.merge_type == 'gdb':
                # 合并GDB图层
                gdb_path, checked_layers, output_mode, output_path = self.params
                
                if output_mode == "输出到当前GDB":
                    # 输出到当前GDB
                    result = self._mergeGDBLayersToGDB(gdb_path, checked_layers)
                else:
                    # 输出到SHP文件
                    result = self._mergeMultipleGDBLayers(gdb_path, checked_layers, output_path)
            
            if result:
                self.success.emit(f"处理完成！结果保存到: {result}")
            else:
                self.error.emit("合并操作执行失败，没有生成结果文件。")
                
        except Exception as e:
            self.error.emit(f"发生错误: {str(e)}")
    
    def _mergeMultipleGDBLayers(self, gdb_path, layer_names, output_path):
        """合并多个GDB图层到SHP文件"""
        import geopandas as gpd
        import pandas as pd
        from datetime import datetime
        
        if not layer_names:
            return None
        
        # 读取第一个图层作为基准
        try:
            merged_gdf = gpd.read_file(gdb_path, layer=layer_names[0])
        except Exception as e:
            raise Exception(f"读取图层 {layer_names[0]} 失败: {e}")
        
        # 清理字段名称
        from .矢量操作 import _clean_field_names
        merged_gdf = _clean_field_names(merged_gdf)
        
        # 添加图层来源字段
        merged_gdf['LAYER_SRC'] = layer_names[0]
        
        # 合并其他图层
        for layer_name in layer_names[1:]:
            try:
                # 读取当前图层
                gdf = gpd.read_file(gdb_path, layer=layer_name)
                
                # 清理字段名称
                gdf = _clean_field_names(gdf)
                
                # 添加图层来源字段
                gdf['LAYER_SRC'] = layer_name
                
                # 确保坐标系一致
                if gdf.crs != merged_gdf.crs:
                    if merged_gdf.crs is not None:
                        gdf = gdf.to_crs(merged_gdf.crs)
                    else:
                        merged_gdf = merged_gdf.to_crs(gdf.crs)
                
                # 确保字段匹配，只保留两个DataFrame共有的字段
                common_columns = list(set(merged_gdf.columns) & set(gdf.columns))
                # 确保geometry字段在common_columns中
                if 'geometry' not in common_columns:
                    common_columns.append('geometry')
                
                # 合并数据，使用ignore_index=True确保新索引
                merged_gdf = pd.concat([merged_gdf[common_columns], gdf[common_columns]], 
                                     ignore_index=True, sort=False)
                
            except Exception as e:
                raise Exception(f"处理图层 {layer_name} 时出错: {e}")
        
        # 保存合并结果
        output_file = os.path.join(output_path, 'gdb_layers_merged.shp')
        
        # 重置索引后再保存
        merged_gdf = merged_gdf.reset_index(drop=True)
        
        # 使用utf-8编码保存文件
        try:
            merged_gdf.to_file(output_file, encoding='utf-8')
            return output_file
        except Exception as e:
            # 尝试使用不同的文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(output_path, f'gdb_layers_merged_{timestamp}.shp')
            merged_gdf.to_file(output_file, encoding='utf-8')
            return output_file
    
    def _mergeGDBLayersToGDB(self, gdb_path, layer_names):
        """合并多个GDB图层到当前GDB文件"""
        import geopandas as gpd
        import pandas as pd
        from datetime import datetime
        
        if not layer_names:
            return None
        
        # 读取第一个图层作为基准
        try:
            merged_gdf = gpd.read_file(gdb_path, layer=layer_names[0])
        except Exception as e:
            raise Exception(f"读取图层 {layer_names[0]} 失败: {e}")
        
        # 清理字段名称
        from .矢量操作 import _clean_field_names
        merged_gdf = _clean_field_names(merged_gdf)
        
        # 添加图层来源字段
        merged_gdf['LAYER_SRC'] = layer_names[0]
        
        # 合并其他图层
        for layer_name in layer_names[1:]:
            try:
                # 读取当前图层
                gdf = gpd.read_file(gdb_path, layer=layer_name)
                
                # 清理字段名称
                gdf = _clean_field_names(gdf)
                
                # 添加图层来源字段
                gdf['LAYER_SRC'] = layer_name
                
                # 确保坐标系一致
                if gdf.crs != merged_gdf.crs:
                    if merged_gdf.crs is not None:
                        gdf = gdf.to_crs(merged_gdf.crs)
                    else:
                        merged_gdf = merged_gdf.to_crs(gdf.crs)
                
                # 确保字段匹配，只保留两个DataFrame共有的字段
                common_columns = list(set(merged_gdf.columns) & set(gdf.columns))
                # 确保geometry字段在common_columns中
                if 'geometry' not in common_columns:
                    common_columns.append('geometry')
                
                # 合并数据，使用ignore_index=True确保新索引
                merged_gdf = pd.concat([merged_gdf[common_columns], gdf[common_columns]], 
                                     ignore_index=True, sort=False)
                
            except Exception as e:
                raise Exception(f"处理图层 {layer_name} 时出错: {e}")
        
        # 生成输出图层名称
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_layer_name = f"merged_layers_{timestamp}"
        
        # 重置索引后再保存
        merged_gdf = merged_gdf.reset_index(drop=True)
        
        # 保存到当前GDB文件
        try:
            merged_gdf.to_file(gdb_path, layer=output_layer_name, driver='OpenFileGDB')
            return f"{gdb_path}#{output_layer_name}"
        except Exception as e:
            # 尝试使用不同的图层名称
            output_layer_name = f"merged_{timestamp}"
            merged_gdf.to_file(gdb_path, layer=output_layer_name, driver='OpenFileGDB')
            return f"{gdb_path}#{output_layer_name}"


class MergeFeaturesFunction(BaseFunction):
    """合并指定目录中的所有要素功能（包括子目录）"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>"
            "合并目录及子目录中的所有要素文件"
        )
        super().__init__("合并指定目录中的所有要素（包括子目录）", description, parent)
        
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
        self.lineEdit14.setPlaceholderText("请输入要合并的目录路径")
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
        
        # 第五行：输出设置
        hBoxLayout5 = QHBoxLayout()
        self.labelOutput = QLabel("输出设置：")
        
        from qfluentwidgets import ComboBox
        self.outputModeCombo = ComboBox(self)
        self.outputModeCombo.addItems(["输出到SHP文件", "输出到当前GDB"])
        self.outputModeCombo.setCurrentIndex(1)  # 默认输出到当前GDB
        
        # 输出路径（仅在输出到SHP时使用）
        self.labelOutputPath = QLabel("输出路径：")
        self.lineEditOutput = LineEdit(self)
        self.lineEditOutput.setPlaceholderText("请输入输出文件路径")
        self.buttonBrowseOutput = PrimaryPushButton(self.tr('浏览'), self, FIF.FOLDER)
        self.buttonBrowseOutput.clicked.connect(self._browseOutput)
        
        hBoxLayout5.addWidget(self.labelOutput)
        hBoxLayout5.addWidget(self.outputModeCombo)
        hBoxLayout5.addWidget(self.labelOutputPath)
        hBoxLayout5.addWidget(self.lineEditOutput)
        hBoxLayout5.addWidget(self.buttonBrowseOutput)
        self.contentLayout.addLayout(hBoxLayout5)
    
    def _browseDirectory(self):
        """浏览目录"""
        from PyQt6.QtWidgets import QFileDialog
        dir_path = QFileDialog.getExistingDirectory(self, "选择目录")
        if dir_path:
            self.lineEdit14.setText(dir_path)
    
    def _browseGDB(self):
        """浏览GDB文件"""
        from PyQt6.QtWidgets import QFileDialog
        file_path = QFileDialog.getExistingDirectory(self, "选择GDB文件")
        if file_path and file_path.endswith('.gdb'):
            self.lineEditGDB.setText(file_path)
    
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
            self.showSuccess(f"成功加载 {len(layer_names)} 个图层")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.showError(f"加载GDB图层失败: {str(e)}")
    
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
                return False, "请至少选择一个要合并的GDB图层"
            
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
        
        # 检查是目录合并还是GDB图层合并
        if self.lineEdit14.text() and not self.lineEditGDB.text():
            # 原有功能：合并目录中的SHP文件
            merge_type = 'dir'
            params = self.lineEdit14.text()
        elif self.lineEditGDB.text():
            # 新功能：合并多个勾选的GDB图层
            merge_type = 'gdb'
            gdb_path = self.lineEditGDB.text()
            
            # 获取所有勾选的图层名称
            checked_layers = []
            for i in range(self.listWidgetLayers.count()):
                item = self.listWidgetLayers.item(i)
                checkbox = self.listWidgetLayers.itemWidget(item)
                if checkbox and checkbox.isChecked():
                    checked_layers.append(checkbox.text())
            
            output_mode = self.outputModeCombo.currentText()
            params = (gdb_path, checked_layers, output_mode, output_path)
        else:
            # 两者都提供了，优先使用GDB图层合并
            merge_type = 'gdb'
            gdb_path = self.lineEditGDB.text()
            
            # 获取所有勾选的图层名称
            checked_layers = []
            for i in range(self.listWidgetLayers.count()):
                item = self.listWidgetLayers.item(i)
                checkbox = self.listWidgetLayers.itemWidget(item)
                if checkbox and checkbox.isChecked():
                    checked_layers.append(checkbox.text())
            
            output_mode = self.outputModeCombo.currentText()
            params = (gdb_path, checked_layers, output_mode, output_path)
        
        # 创建并启动合并线程
        self.merge_thread = MergeThread(
            merge_type=merge_type,
            params=params,
            parent=self
        )
        
        # 连接信号
        self.merge_thread.success.connect(self._onMergeSuccess)
        self.merge_thread.error.connect(self._onMergeError)
        self.merge_thread.finished.connect(self._onMergeFinished)
        
        # 启动线程
        self.merge_thread.start()
    
    def _onMergeSuccess(self, message: str):
        """合并操作成功处理"""
        if hasattr(self, 'stateTooltip') and self.stateTooltip is not None:
            self.stateTooltip.setContent('处理完成 ✅')
            self.stateTooltip.setState(True)
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1000, self.stateTooltip.close)
        
        self.showSuccess(message)
    
    def _onMergeError(self, message: str):
        """合并操作错误处理"""
        if hasattr(self, 'stateTooltip') and self.stateTooltip is not None:
            self.stateTooltip.setContent('处理失败 ❌')
            self.stateTooltip.setState(True)
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1000, self.stateTooltip.close)
        
        self.showError(message)
    
    def _onMergeFinished(self):
        """合并线程结束处理"""
        self._running = False
    
    def _mergeGDBLayers(self, gdb_path, layer_name, output_path):
        """合并单个GDB图层"""
        import geopandas as gpd
        import pandas as pd
        from datetime import datetime
        
        # 读取GDB图层
        gdf = gpd.read_file(gdb_path, layer=layer_name)
        
        # 清理字段名称
        from .矢量操作 import _clean_field_names
        gdf = _clean_field_names(gdf)
        
        # 保存合并结果
        output_file = os.path.join(output_path, f'{layer_name}_merged.shp')
        
        # 重置索引后再保存
        gdf = gdf.reset_index(drop=True)
        
        # 使用utf-8编码保存文件
        try:
            gdf.to_file(output_file, encoding='utf-8')
            print(f"GDB图层合并完成并保存为: {output_file}")
            return output_file
        except Exception as e:
            # 尝试使用不同的文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(output_path, f'{layer_name}_merged_{timestamp}.shp')
            gdf.to_file(output_file, encoding='utf-8')
            print(f"GDB图层合并完成并保存为: {output_file}")
            return output_file
    
    def _mergeMultipleGDBLayers(self, gdb_path, layer_names, output_path):
        """合并多个GDB图层到SHP文件"""
        import geopandas as gpd
        import pandas as pd
        from datetime import datetime
        
        if not layer_names:
            return None
        
        # 读取第一个图层作为基准
        try:
            merged_gdf = gpd.read_file(gdb_path, layer=layer_names[0])
        except Exception as e:
            print(f"读取图层 {layer_names[0]} 失败: {e}")
            return None
        
        # 清理字段名称
        from .矢量操作 import _clean_field_names
        merged_gdf = _clean_field_names(merged_gdf)
        
        # 添加图层来源字段
        merged_gdf['LAYER_SRC'] = layer_names[0]
        
        # 合并其他图层
        for layer_name in layer_names[1:]:
            try:
                # 读取当前图层
                gdf = gpd.read_file(gdb_path, layer=layer_name)
                
                # 清理字段名称
                gdf = _clean_field_names(gdf)
                
                # 添加图层来源字段
                gdf['LAYER_SRC'] = layer_name
                
                # 确保坐标系一致
                if gdf.crs != merged_gdf.crs:
                    if merged_gdf.crs is not None:
                        gdf = gdf.to_crs(merged_gdf.crs)
                    else:
                        merged_gdf = merged_gdf.to_crs(gdf.crs)
                
                # 确保字段匹配，只保留两个DataFrame共有的字段
                common_columns = list(set(merged_gdf.columns) & set(gdf.columns))
                # 确保geometry字段在common_columns中
                if 'geometry' not in common_columns:
                    common_columns.append('geometry')
                
                # 合并数据，使用ignore_index=True确保新索引
                merged_gdf = pd.concat([merged_gdf[common_columns], gdf[common_columns]], 
                                     ignore_index=True, sort=False)
                
            except Exception as e:
                print(f"处理图层 {layer_name} 时出错: {e}")
                continue
        
        # 保存合并结果
        output_file = os.path.join(output_path, 'gdb_layers_merged.shp')
        
        # 重置索引后再保存
        merged_gdf = merged_gdf.reset_index(drop=True)
        
        # 使用utf-8编码保存文件
        try:
            merged_gdf.to_file(output_file, encoding='utf-8')
            print(f"多个GDB图层合并完成并保存为: {output_file}")
            return output_file
        except Exception as e:
            # 尝试使用不同的文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(output_path, f'gdb_layers_merged_{timestamp}.shp')
            merged_gdf.to_file(output_file, encoding='utf-8')
            print(f"多个GDB图层合并完成并保存为: {output_file}")
            return output_file
    
    def _mergeGDBLayersToGDB(self, gdb_path, layer_names):
        """合并多个GDB图层到当前GDB文件"""
        import geopandas as gpd
        import pandas as pd
        from datetime import datetime
        
        if not layer_names:
            return None
        
        # 读取第一个图层作为基准
        try:
            merged_gdf = gpd.read_file(gdb_path, layer=layer_names[0])
        except Exception as e:
            print(f"读取图层 {layer_names[0]} 失败: {e}")
            return None
        
        # 清理字段名称
        from .矢量操作 import _clean_field_names
        merged_gdf = _clean_field_names(merged_gdf)
        
        # 添加图层来源字段
        merged_gdf['LAYER_SRC'] = layer_names[0]
        
        # 合并其他图层
        for layer_name in layer_names[1:]:
            try:
                # 读取当前图层
                gdf = gpd.read_file(gdb_path, layer=layer_name)
                
                # 清理字段名称
                gdf = _clean_field_names(gdf)
                
                # 添加图层来源字段
                gdf['LAYER_SRC'] = layer_name
                
                # 确保坐标系一致
                if gdf.crs != merged_gdf.crs:
                    if merged_gdf.crs is not None:
                        gdf = gdf.to_crs(merged_gdf.crs)
                    else:
                        merged_gdf = merged_gdf.to_crs(gdf.crs)
                
                # 确保字段匹配，只保留两个DataFrame共有的字段
                common_columns = list(set(merged_gdf.columns) & set(gdf.columns))
                # 确保geometry字段在common_columns中
                if 'geometry' not in common_columns:
                    common_columns.append('geometry')
                
                # 合并数据，使用ignore_index=True确保新索引
                merged_gdf = pd.concat([merged_gdf[common_columns], gdf[common_columns]], 
                                     ignore_index=True, sort=False)
                
            except Exception as e:
                print(f"处理图层 {layer_name} 时出错: {e}")
                continue
        
        # 生成输出图层名称
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_layer_name = f"merged_layers_{timestamp}"
        
        # 重置索引后再保存
        merged_gdf = merged_gdf.reset_index(drop=True)
        
        # 保存到当前GDB文件
        try:
            merged_gdf.to_file(gdb_path, layer=output_layer_name, driver='OpenFileGDB')
            print(f"多个GDB图层合并完成并保存到当前GDB，图层名称: {output_layer_name}")
            return f"{gdb_path}#{output_layer_name}"
        except Exception as e:
            # 尝试使用不同的图层名称
            output_layer_name = f"merged_{timestamp}"
            merged_gdf.to_file(gdb_path, layer=output_layer_name, driver='OpenFileGDB')
            print(f"多个GDB图层合并完成并保存到当前GDB，图层名称: {output_layer_name}")
            return f"{gdb_path}#{output_layer_name}"
