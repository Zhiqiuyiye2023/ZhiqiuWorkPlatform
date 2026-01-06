# coding:utf-8
"""
SHP转WKT文本格式功能
"""

import os
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QFileDialog, QGroupBox
from qfluentwidgets import PrimaryPushButton, PushButton, LineEdit, StateToolTip, ComboBox
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction


class WktConversionThread(QThread):
    """转换线程类，用于在后台执行SHP转WKT任务"""
    success = pyqtSignal(str, str)  # 成功信号，传递SHP输出路径和WKT输出路径
    error = pyqtSignal(str)          # 错误信号
    
    def __init__(self, shp_path, layer_name, output_path):
        super().__init__()
        self.shp_path = shp_path
        self.layer_name = layer_name
        self.output_path = output_path
    
    def run(self):
        """执行转换任务"""
        try:
            import sys
            import os
            import geopandas as gpd
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            # 读取矢量数据
            if self.shp_path.lower().endswith('.gdb') and self.layer_name:
                gdf = gpd.read_file(self.shp_path, layer=self.layer_name)
            else:
                gdf = gpd.read_file(self.shp_path)
            
            # 导入格式转换模块
            from .格式转换 import SHP转WKT文本格式
            
            # 直接调用格式转换模块中的函数
            shp_output_path, txt_output_path = SHP转WKT文本格式(self.shp_path)
            
            # 发送成功信号
            self.success.emit(shp_output_path, txt_output_path)
            
        except Exception as e:
            import traceback
            error_msg = f'转换失败: {str(e)}\n\n{traceback.format_exc()}'
            # 发送错误信号
            self.error.emit(error_msg)


class ShpToWktFunction(BaseFunction):
    """SHP转WKT格式（含ZIP）功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <span style='color: orange; font-weight: bold;'>WKT格式说明：</span><br>"
            "1. 普通面格式：POLYGON((x1 y1, x2 y2, x3 y3, x1 y1))<br>"
            "2. 多面格式：MULTIPOLYGON(((x1 y1, x2 y2, x3 y3, x1 y1)), ((x4 y4, x5 y5, x6 y6, x4 y4)))<br>"
            "注意：坐标点需要首尾相连，形成闭合多边形<br>"
            "3. 转换时将同时生成ZIP格式文件"
        )
        super().__init__("SHP转WKT格式（含ZIP）", description, parent)
        
        self._initUI()
        # 不使用默认执行按钮
        self.stateTooltip = None
        self._running = False
    
    def _initUI(self):
        """初始化界面"""
        # 输入设置区域
        input_group = QGroupBox("输入矢量数据", self)
        input_layout = QVBoxLayout(input_group)
        
        # 输入文件选择
        shp_layout = QHBoxLayout()
        shp_label = QLabel("输入文件：")
        self.label18 = LineEdit(self)
        self.label18.setPlaceholderText("选择要转换的矢量文件")
        self.label18.setReadOnly(True)
        
        # 分别添加SHP和GDB文件选择按钮
        self.shp_btn = PushButton("选择SHP", self, FIF.FOLDER)
        self.shp_btn.clicked.connect(lambda: self._selectVectorFile(shp_only=True))
        self.shp_btn.setFixedWidth(120)
        
        self.gdb_btn = PushButton("选择GDB", self, FIF.FOLDER)
        self.gdb_btn.clicked.connect(lambda: self._selectVectorFile(gdb_only=True))
        self.gdb_btn.setFixedWidth(120)
        
        shp_layout.addWidget(shp_label)
        shp_layout.addWidget(self.label18, 1)
        shp_layout.addWidget(self.shp_btn)
        shp_layout.addWidget(self.gdb_btn)
        input_layout.addLayout(shp_layout)
        
        # GDB图层选择
        self.gdb_layer_layout = QHBoxLayout()
        gdb_layer_label = QLabel("GDB图层：")
        self.gdb_layer_combo = ComboBox(self)
        self.gdb_layer_combo.setPlaceholderText("请先选择GDB文件")
        self.gdb_layer_combo.setEnabled(False)
        
        self.gdb_layer_layout.addWidget(gdb_layer_label)
        self.gdb_layer_layout.addWidget(self.gdb_layer_combo, 1)
        # 默认隐藏GDB图层选择
        for i in range(self.gdb_layer_layout.count()):
            widget = self.gdb_layer_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(False)
        input_layout.addLayout(self.gdb_layer_layout)
        
        # 输出设置区域
        output_group = QGroupBox("输出设置", self)
        output_layout = QVBoxLayout(output_group)
        
        # WKT输出路径
        wkt_output_layout = QHBoxLayout()
        wkt_output_label = QLabel("WKT输出路径：")
        self.output_path_edit = LineEdit(self)
        self.output_path_edit.setPlaceholderText("选择输出WKT文件路径")
        self.output_path_edit.setReadOnly(True)
        
        self.output_wkt_btn = PushButton("选择输出路径", self, FIF.SAVE)
        self.output_wkt_btn.clicked.connect(self._selectOutputFile)
        
        wkt_output_layout.addWidget(wkt_output_label)
        wkt_output_layout.addWidget(self.output_path_edit, 1)
        wkt_output_layout.addWidget(self.output_wkt_btn)
        output_layout.addLayout(wkt_output_layout)
        
        # 将分组框添加到主布局
        self.contentLayout.addWidget(input_group)
        self.contentLayout.addWidget(output_group)
        
        # 添加执行按钮
        self.buttonConvert = PrimaryPushButton("开始转换", self, FIF.PLAY)
        self.buttonConvert.clicked.connect(self.execute)
        self.contentLayout.addWidget(self.buttonConvert, 0, Qt.AlignmentFlag.AlignCenter)
    
    def _selectVectorFile(self, shp_only=False, gdb_only=False):
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
                from qfluentwidgets import InfoBar, InfoBarPosition
                InfoBar.warning(
                    title="警告",
                    content="请选择GDB文件",
                    parent=self,
                    position=InfoBarPosition.TOP_RIGHT
                )
                return
            
            self.label18.setText(file_path)
            # 设置默认输出路径
            base_path, ext = os.path.splitext(file_path)
            default_path = f"{base_path}.txt"
            self.output_path_edit.setText(default_path)
            
            if file_path.lower().endswith('.gdb'):
                # 显示图层选择控件
                for i in range(self.gdb_layer_layout.count()):
                    widget = self.gdb_layer_layout.itemAt(i).widget()
                    if widget:
                        widget.setVisible(True)
                # 列出GDB中的所有图层
                self._update_gdb_layers(file_path)
            else:
                # 隐藏图层选择控件
                for i in range(self.gdb_layer_layout.count()):
                    widget = self.gdb_layer_layout.itemAt(i).widget()
                    if widget:
                        widget.setVisible(False)
    
    def _update_gdb_layers(self, gdb_path):
        """更新GDB图层列表"""
        try:
            import fiona
            with fiona.Env():
                layers = fiona.listlayers(gdb_path)
            self.gdb_layer_combo.clear()
            self.gdb_layer_combo.addItems(layers)
            self.gdb_layer_combo.setEnabled(True)
        except Exception as e:
            from qfluentwidgets import InfoBar, InfoBarPosition
            InfoBar.error(
                title="错误",
                content=f"无法读取GDB文件: {str(e)}",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT
            )
    
    def _selectOutputFile(self):
        """选择WKT输出文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存WKT文件", "", "文本文件 (*.txt)"
        )
        if file_path:
            if not file_path.endswith('.txt'):
                file_path += '.txt'
            self.output_path_edit.setText(file_path)
    
    def validate(self) -> tuple[bool, str]:
        """验证输入"""
        if not self.label18.text():
            return False, "请选择矢量文件"
        
        if not self.output_path_edit.text():
            return False, "请选择输出路径"
        
        # 验证GDB输入的图层选择
        if self.label18.text().lower().endswith('.gdb'):
            if not self.gdb_layer_combo.currentText():
                return False, "请选择GDB图层"
        
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
        
        # 获取参数
        shp_path = self.label18.text()
        # 获取GDB图层名称（如果是GDB文件）
        layer_name = self.gdb_layer_combo.currentText() if shp_path.lower().endswith('.gdb') else ""
        output_path = self.output_path_edit.text()
        
        # 创建转换线程
        self.wkt_thread = WktConversionThread(shp_path, layer_name, output_path)
        
        # 连接信号槽
        self.wkt_thread.success.connect(self._on_wkt_success)
        self.wkt_thread.error.connect(self._on_wkt_error)
        
        # 启动线程
        self.wkt_thread.start()
    
    def _on_wkt_success(self, shp_output_path, txt_output_path):
        """WKT转换成功处理"""
        try:
            if hasattr(self, 'stateTooltip') and self.stateTooltip is not None:
                self.stateTooltip.setContent('处理完成 ✅')
                self.stateTooltip.setState(True)
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(1000, self.stateTooltip.close)
        except RuntimeError:
            # 捕获QLabel已被删除的错误
            pass
        
        self.showSuccess(f"处理完成！\nSHP输出文件: {shp_output_path}\nWKT文本文件: {txt_output_path}")
        self._running = False
    
    def _on_wkt_error(self, error_msg):
        """WKT转换错误处理"""
        try:
            if hasattr(self, 'stateTooltip') and self.stateTooltip is not None:
                self.stateTooltip.setContent('处理失败 ❌')
                self.stateTooltip.setState(True)
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(1000, self.stateTooltip.close)
        except RuntimeError:
            # 捕获QLabel已被删除的错误
            pass
        
        self.showError(f'发生错误: {error_msg}')
        self._running = False
