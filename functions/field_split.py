# coding:utf-8
"""
根据矢量字段分离要素功能
"""

from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QFileDialog, QGroupBox
from PyQt6.QtCore import QThread, pyqtSignal
from qfluentwidgets import LineEdit, ComboBox, PushButton, PrimaryPushButton
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction
import geopandas as gpd
import os


class SplitThread(QThread):
    """字段分离线程"""
    
    success = pyqtSignal(str)  # 成功信号，传递结果信息
    error = pyqtSignal(str)    # 错误信号，传递错误信息
    
    def __init__(self, file_path, field_name, output_path=None, output_type="SHP文件", parent=None):
        """
        Args:
            file_path: 矢量文件路径
            field_name: 用于分离的字段名
            output_path: 输出路径
            output_type: 输出类型（SHP文件或GDB图层）
        """
        super().__init__(parent)
        self.file_path = file_path
        self.field_name = field_name
        self.output_path = output_path
        self.output_type = output_type
    
    def run(self):
        """线程运行方法"""
        try:
            from .矢量操作 import 根据矢量字段分离要素
            result = 根据矢量字段分离要素(self.file_path, self.field_name, self.output_path, self.output_type)
            if result:
                self.success.emit(f"分离完成！\n{result}")
            else:
                self.success.emit(f"分离完成！\n文件已保存到源文件目录")
        except Exception as e:
            import traceback
            self.error.emit(f"分离失败: {str(e)}\n\n{traceback.format_exc()}")


class FieldSplitFunction(BaseFunction):
    """根据矢量字段分离要素功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>"
            "1. 根据指定字段的值将矢量数据分离成多个文件<br>"
            "2. 支持SHP和GDB文件格式<br>"
            "3. 支持将结果保存为SHP文件或GDB图层<br>"
            "4. 自动生成默认输出路径"
        )
        super().__init__("根据矢量字段分离要素", description, parent)
        
        self._initUI()
        self.addExecuteButton("开始分离", self.execute)
    
    def _initUI(self):
        """初始化界面"""
        # 输入矢量数据选择区域
        input_vector_group = QGroupBox("输入矢量数据", self)
        input_vector_layout = QVBoxLayout(input_vector_group)
        
        # SHP/GDB文件选择
        vector_layout = QHBoxLayout()
        vector_layout.addWidget(QLabel("矢量文件："))
        
        self.vectorPath = LineEdit(self)
        self.vectorPath.setPlaceholderText("选择要分离的矢量文件")
        self.vectorPath.setReadOnly(True)
        
        # 添加SHP文件选择按钮
        self.shp_browse_btn = PushButton("选择SHP", self, FIF.FOLDER)
        self.shp_browse_btn.clicked.connect(lambda: self._selectVector(shp_only=True))
        self.shp_browse_btn.setFixedWidth(120)
        
        # 添加GDB文件选择按钮
        self.gdb_browse_btn = PushButton("选择GDB", self, FIF.FOLDER)
        self.gdb_browse_btn.clicked.connect(lambda: self._selectVector(gdb_only=True))
        self.gdb_browse_btn.setFixedWidth(120)
        
        vector_layout.addWidget(self.vectorPath, 1)
        vector_layout.addWidget(self.shp_browse_btn)
        vector_layout.addWidget(self.gdb_browse_btn)
        input_vector_layout.addLayout(vector_layout)
        
        # GDB图层选择
        self.layer_layout = QHBoxLayout()
        self.layer_label = QLabel("GDB图层：")
        self.layer_combo = ComboBox(self)
        self.layer_combo.setPlaceholderText("请先选择GDB文件")
        self.layer_combo.setEnabled(False)
        
        self.layer_layout.addWidget(self.layer_label)
        self.layer_layout.addWidget(self.layer_combo, 1)
        input_vector_layout.addLayout(self.layer_layout)
        
        # 分离字段选择
        field_layout = QHBoxLayout()
        field_layout.addWidget(QLabel("分离字段："))
        
        self.fieldCombo = ComboBox(self)
        self.fieldCombo.setPlaceholderText("选择分离字段")
        self.fieldCombo.setFixedWidth(150)
        
        field_layout.addWidget(self.fieldCombo)
        field_layout.addStretch(1)
        input_vector_layout.addLayout(field_layout)
        
        self.contentLayout.addWidget(input_vector_group)
        
        # 输出设置区域
        output_group = QGroupBox("输出设置", self)
        output_layout = QVBoxLayout(output_group)
        
        # 输出类型选择
        output_type_layout = QHBoxLayout()
        output_type_layout.addWidget(QLabel("输出类型："))
        
        self.output_type_combo = ComboBox(self)
        self.output_type_combo.addItems(["输出到SHP文件", "输出到GDB图层"])
        self.output_type_combo.setCurrentIndex(0)  # 默认输出到SHP文件
        
        output_type_layout.addWidget(self.output_type_combo)
        output_type_layout.addStretch(1)
        output_layout.addLayout(output_type_layout)
        
        # 输出路径设置
        output_path_layout = QHBoxLayout()
        output_path_layout.addWidget(QLabel("输出路径："))
        
        self.output_path_edit = LineEdit(self)
        self.output_path_edit.setPlaceholderText("选择输出路径")
        self.output_path_edit.setReadOnly(True)
        
        self.output_browse_btn = PrimaryPushButton("选择路径", self, FIF.FOLDER)
        self.output_browse_btn.clicked.connect(self._selectOutputPath)
        self.output_browse_btn.setFixedWidth(120)
        
        output_path_layout.addWidget(self.output_path_edit, 1)
        output_path_layout.addWidget(self.output_browse_btn)
        output_layout.addLayout(output_path_layout)
        
        self.contentLayout.addWidget(output_group)
    
    def _selectVector(self, shp_only=False, gdb_only=False):
        """选择矢量文件"""
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
        
        if file_path:
            # 验证GDB文件
            if gdb_only and not file_path.endswith('.gdb'):
                self.showError("请选择有效的GDB文件")
                return
            
            self.vectorPath.setText(file_path)
            
            if file_path.endswith('.gdb'):
                # GDB文件，加载图层列表
                self._loadGDBLayers(file_path)
            else:
                # SHP文件，直接加载字段
                self._loadFields(file_path)
                # 隐藏图层选择
                self.layer_label.setVisible(False)
                self.layer_combo.setVisible(False)
            
            # 自动生成默认输出路径
            self._autoGenerateOutputPath(file_path)
    
    def _loadGDBLayers(self, gdb_path):
        """加载GDB图层列表"""
        try:
            import fiona
            
            # 获取GDB中的所有图层
            with fiona.Env():
                layer_names = fiona.listlayers(gdb_path)
            
            # 更新图层下拉框
            self.layer_combo.clear()
            self.layer_combo.addItems(layer_names)
            self.layer_combo.setEnabled(True)
            
            # 显示图层选择
            self.layer_label.setVisible(True)
            self.layer_combo.setVisible(True)
            
            # 加载第一个图层的字段
            if layer_names:
                self._loadFields(f"{gdb_path}|{layer_names[0]}")
        except Exception as e:
            self.showError(f"加载GDB图层失败: {str(e)}")
    
    def _loadFields(self, file_path):
        """加载字段列表"""
        try:
            gdf = None
            
            if "|" in file_path:
                # GDB图层，格式为 "GDB路径|图层名称"
                gdb_path, layer_name = file_path.split("|", 1)
                gdf = gpd.read_file(gdb_path, layer=layer_name)
            else:
                # SHP文件
                gdf = gpd.read_file(file_path)
            
            fields = [col for col in gdf.columns if col != 'geometry']
            
            # 更新字段下拉框
            if hasattr(self, 'fieldCombo') and self.fieldCombo is not None:
                self.fieldCombo.clear()
                self.fieldCombo.addItems(fields)
        except RuntimeError:
            # 捕获UI元素已被删除的错误
            pass
        except Exception as e:
            try:
                if hasattr(self, 'showError'):
                    self.showError(f"读取字段失败: {str(e)}")
            except RuntimeError:
                # 捕获UI元素已被删除的错误
                pass
    
    def _autoGenerateOutputPath(self, input_path):
        """自动生成默认输出路径"""
        if input_path.endswith('.gdb'):
            # GDB文件，默认输出路径为GDB所在目录
            output_path = os.path.dirname(input_path)
        else:
            # SHP文件，默认输出路径为SHP所在目录
            output_path = os.path.dirname(input_path)
        
        self.output_path_edit.setText(output_path)
    
    def _selectOutputPath(self):
        """选择输出路径"""
        output_type = self.output_type_combo.currentText()
        
        if output_type == "输出到SHP文件":
            # 选择SHP输出目录
            dir_path = QFileDialog.getExistingDirectory(self, "选择SHP输出目录")
            if dir_path:
                self.output_path_edit.setText(dir_path)
        else:
            # 选择GDB输出文件
            gdb_path = QFileDialog.getExistingDirectory(self, "选择GDB输出文件")
            if gdb_path and gdb_path.endswith('.gdb'):
                self.output_path_edit.setText(gdb_path)
            else:
                self.showError("请选择有效的GDB文件")
    
    def validate(self) -> tuple[bool, str]:
        """验证输入"""
        if not self.vectorPath.text():
            return False, "请选择矢量文件"
        
        if self.vectorPath.text().endswith('.gdb') and not self.layer_combo.currentText():
            return False, "请选择GDB图层"
        
        if not self.fieldCombo.currentText():
            return False, "请选择分离字段"
        
        if not self.output_path_edit.text():
            return False, "请选择输出路径"
        
        return True, "" 
    
    def execute(self):
        """执行分离"""
        try:
            valid, message = self.validate()
            if not valid:
                if hasattr(self, 'showError'):
                    self.showError(message)
                return
            
            if hasattr(self, 'showProgress'):
                self.showProgress("正在分离要素...")
            
            # 获取输入参数
            vector_path = self.vectorPath.text()
            field_name = self.fieldCombo.currentText()
            output_path = self.output_path_edit.text()
            output_type = self.output_type_combo.currentText()
            
            # 处理GDB图层路径
            if vector_path.endswith('.gdb'):
                layer_name = self.layer_combo.currentText()
                vector_path = f"{vector_path}|{layer_name}"
            
            # 创建并启动分离线程
            self.split_thread = SplitThread(
                file_path=vector_path,
                field_name=field_name,
                output_path=output_path,
                output_type=output_type,
                parent=self
            )
            
            # 连接信号
            self.split_thread.success.connect(self._onSplitSuccess)
            self.split_thread.error.connect(self._onSplitError)
            self.split_thread.finished.connect(self._onSplitFinished)
            
            # 启动线程
            self.split_thread.start()
        except RuntimeError:
            # 捕获UI元素已被删除的错误
            pass
    
    def _onSplitSuccess(self, message: str):
        """分离成功处理"""
        if hasattr(self, 'showSuccess'):
            self.showSuccess(message)
    
    def _onSplitError(self, message: str):
        """分离错误处理"""
        if hasattr(self, 'showError'):
            self.showError(message)
    
    def _onSplitFinished(self):
        """分离线程结束处理"""
        if hasattr(self, 'hideProgress'):
            self.hideProgress()
