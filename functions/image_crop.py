# coding:utf-8
"""
影像裁剪功能
"""

import sys
import os

# 添加根目录到path，以便导入数据处理方法模块
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtWidgets import QFileDialog, QLabel, QHBoxLayout, QVBoxLayout, QGroupBox, QHeaderView, QTableWidgetItem, QWidget, QFrame
from qfluentwidgets import (
    ComboBox, LineEdit, PushButton, ProgressBar, 
    SpinBox, TextEdit, TransparentPushButton, MessageBox, InfoBar, TableWidget
)
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import StateToolTip
from .base_function import BaseFunction
import geopandas as gpd


class DragDropTableWidget(TableWidget):
    """支持拖拽的表格组件"""
    
    def __init__(self, parent=None, add_callback=None):
        super().__init__(parent)
        self.add_callback = add_callback
        self.setAcceptDrops(True)
        self.setDragDropMode(TableWidget.DragDropMode.DropOnly)
    
    def dragEnterEvent(self, e):
        if e and e.mimeData() and e.mimeData().hasUrls():
            e.acceptProposedAction()
        elif e:
            e.ignore()
    
    def dragMoveEvent(self, e):
        if e and e.mimeData() and e.mimeData().hasUrls():
            e.acceptProposedAction()
        elif e:
            e.ignore()
    
    def dropEvent(self, e):
        if e and e.mimeData() and e.mimeData().hasUrls():
            files = []
            for url in e.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith(('.tif', '.tiff', '.img')):
                    files.append(file_path)
            if files and self.add_callback:
                self.add_callback(files)
            e.acceptProposedAction()
        elif e:
            e.ignore()


class CropThread(QThread):
    """影像裁剪线程"""
    
    success = pyqtSignal(str)      # 成功信号，传递结果信息
    error = pyqtSignal(str)        # 错误信号，传递错误信息
    progress_update = pyqtSignal(int) # 进度更新信号
    log_update = pyqtSignal(str)   # 日志更新信号
    
    def __init__(self, params, parent=None):
        """
        Args:
            params: 裁剪参数，包含所有裁剪需要的参数
            parent: 父对象
        """
        super().__init__(parent)
        self.params = params
    
    def run(self):
        """线程运行方法"""
        try:
            # 解包参数
            image_path, vector_path, field_name, mode, field_value, buffer_distance, output_dir, crop_method = self.params
            
            # 处理打包后可能出现的导入问题
            import sys
            import os
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if root_dir not in sys.path:
                sys.path.append(root_dir)
            # 使用动态导入来处理中文模块名
            import importlib
            影像处理 = importlib.import_module('functions.影像处理')
            影像裁剪 = getattr(影像处理, '影像裁剪')
            
            # 定义更新进度条的回调函数
            def progress_cb(val):
                self.progress_update.emit(int(val))
            
            # 定义更新日志的回调函数
            def warning_cb(msg):
                self.log_update.emit(msg + "\n")
            
            # 执行裁剪
            output_files = 影像裁剪(
                影像路径=image_path,
                矢量路径=vector_path,
                字段名=field_name,
                字段值=field_value,
                输出目录=output_dir,
                进度回调=progress_cb,
                警告回调=warning_cb,
                缓冲距离=buffer_distance,
                裁剪方式=crop_method
            )
            
            if output_files:
                result_msg = f"裁剪完成！\n共生成 {len(output_files)} 个文件\n输出目录：{output_dir}\n\n前5个文件：\n"
                for i, file in enumerate(output_files[:5]):
                    result_msg += f"{i+1}. {file}\n"
                if len(output_files) > 5:
                    result_msg += f"... 等共 {len(output_files)} 个文件\n"
            else:
                result_msg = "裁剪完成，但没有生成任何文件！"
            
            self.success.emit(result_msg)
        except Exception as e:
            import traceback
            self.error.emit(f"裁剪失败: {str(e)}\n\n{traceback.format_exc()}")


class ImageCropFunction(BaseFunction):
    """影像裁剪功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>"
            "根据矢量范围裁剪影像，支持批量裁剪和单一裁剪模式，可设置缓冲距离"
        )
        super().__init__("影像裁剪功能", description, parent)
        
        self._running = False
        self._crop_image_full_path = ""
        self._crop_vector_full_path = ""
        self._crop_output_dir_full = ""
        self.stateTooltip = None
        # 初始化影像列表
        self.image_files = []
        self._initUI()
    
    def _initUI(self):
        """初始化界面"""
        # 移除重复的功能说明标签，只保留父类传递的功能说明
        
        # 输入设置区域 - 合并影像和矢量设置，调整为更紧凑的布局
        input_group = QGroupBox("输入设置", self)
        input_layout = QVBoxLayout(input_group)
        input_layout.setSpacing(12)
        input_layout.setContentsMargins(15, 15, 15, 15)
        
        # 影像文件表格 - 替换原来的简单选择
        self.imageTable = DragDropTableWidget(self, self._add_images_to_table)
        self.imageTable.setColumnCount(5)
        self.imageTable.setHorizontalHeaderLabels(['路径', '坐标系', '分度带', '波段', '分辨率'])
        # 加高列表
        self.imageTable.setFixedHeight(200)
        
        # 设置表格属性：内容不换行，显示省略号
        self.imageTable.setWordWrap(False)
        self.imageTable.setTextElideMode(Qt.TextElideMode.ElideMiddle)  # 设置文本省略方式为中间省略
        
        # 设置列宽策略：表格匹配页面宽度，列宽相对固定
        header = self.imageTable.horizontalHeader()
        if header:
            # 表格整体适应页面宽度
            self.imageTable.horizontalHeader().setStretchLastSection(False)
            
            # 设置各列的宽度分配：路径列拉伸，其他列固定宽度
            # 使用ResizeMode.Interactive允许用户手动调整，但初始宽度固定
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # 路径列拉伸，适应页面宽度
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)  # 坐标系列
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # 分度带列
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)  # 波段列
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)  # 分辨率列
            
            # 设置初始固定宽度
            header.resizeSection(1, 120)  # 坐标系列
            header.resizeSection(2, 150)  # 分度带列
            header.resizeSection(3, 60)   # 波段列
            header.resizeSection(4, 100)  # 分辨率列
        
        # 设置行高
        self.imageTable.verticalHeader().setDefaultSectionSize(30)
        
        # 设置样式
        self.imageTable.setAlternatingRowColors(True)
        self.imageTable.setBorderVisible(True)
        
        input_layout.addWidget(self.imageTable)
        
        # 添加和移除影像文件按钮
        buttons_layout = QHBoxLayout()
        self.crop_multi_image_btn = PushButton("选择影像", self, FIF.ADD)
        self.crop_multi_image_btn.setFixedHeight(32)
        self.crop_multi_image_btn.setFixedWidth(120)
        self.crop_multi_image_btn.setToolTip("选择一个或多个影像文件")
        self.crop_multi_image_btn.clicked.connect(self._on_crop_multi_image_btn)
        
        # 移除选中影像按钮
        self.remove_image_btn = PushButton("移除选中", self, FIF.DELETE)
        self.remove_image_btn.setFixedHeight(32)
        self.remove_image_btn.setFixedWidth(120)
        self.remove_image_btn.setToolTip("移除选中的影像文件")
        self.remove_image_btn.clicked.connect(self._on_remove_image)
        
        buttons_layout.addWidget(self.crop_multi_image_btn)
        buttons_layout.addWidget(self.remove_image_btn)
        buttons_layout.addStretch(1)
        input_layout.addLayout(buttons_layout)
        
        # 矢量文件选择部分
        vector_part_layout = QHBoxLayout()
        vector_part_layout.setSpacing(12)
        label_vector = QLabel("矢量文件：")
        label_vector.setFixedWidth(80)
        label_vector.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.crop_vector_btn = PushButton("选择矢量", self, FIF.DOCUMENT)
        self.crop_vector_btn.setFixedHeight(32)
        self.crop_vector_btn.setFixedWidth(120)
        self.crop_vector_btn.clicked.connect(self._on_crop_vector_btn)
        
        self.crop_vector_path_label = QLabel("")
        self.crop_vector_path_label.setStyleSheet("color: #888; border: 1px solid #ddd; padding: 6px 10px; border-radius: 4px;")
        self.crop_vector_path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.crop_vector_path_label.setMinimumWidth(200)
        # 移除最大宽度限制，让标签能够根据面板宽度自动调整
        # self.crop_vector_path_label.setMaximumWidth(300)
        self.crop_vector_path_label.setToolTip("矢量文件路径")
        self.crop_vector_path_label.setFixedHeight(32)
        self.crop_vector_path_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        label_vector_field = QLabel("字段：")
        label_vector_field.setFixedWidth(40)
        label_vector_field.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.crop_vector_field_cb = ComboBox(self)
        self.crop_vector_field_cb.setPlaceholderText("选择裁剪字段")
        self.crop_vector_field_cb.setFixedWidth(150)
        self.crop_vector_field_cb.setFixedHeight(32)
        self.crop_vector_field_cb.setEnabled(False)
        
        vector_part_layout.addWidget(label_vector)
        vector_part_layout.addWidget(self.crop_vector_btn)
        vector_part_layout.addWidget(self.crop_vector_path_label, 1)
        vector_part_layout.addWidget(label_vector_field)
        vector_part_layout.addWidget(self.crop_vector_field_cb)
        input_layout.addLayout(vector_part_layout)
        
        # 裁剪参数设置区域
        params_group = QGroupBox("裁剪参数设置", self)
        params_layout = QHBoxLayout(params_group)
        params_layout.setSpacing(12)
        params_layout.setContentsMargins(15, 15, 15, 15)
        
        # 裁剪模式选择
        label_mode = QLabel("裁剪模式：")
        label_mode.setFixedWidth(80)
        label_mode.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.crop_mode_combo = ComboBox(self)
        self.crop_mode_combo.addItems(["批量裁剪", "单一裁剪"])
        self.crop_mode_combo.setCurrentIndex(0)
        self.crop_mode_combo.setFixedWidth(120)
        self.crop_mode_combo.setFixedHeight(32)
        self.crop_mode_combo.currentTextChanged.connect(self._on_mode_changed)
        
        label_value = QLabel("字段值：")
        label_value.setFixedWidth(60)
        label_value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.crop_field_value_edit = LineEdit(self)
        self.crop_field_value_edit.setPlaceholderText("输入要裁剪的字段值")
        self.crop_field_value_edit.setFixedWidth(120)
        self.crop_field_value_edit.setFixedHeight(32)
        self.crop_field_value_edit.setEnabled(False)
        
        # 缓冲距离
        label_buffer = QLabel("缓冲距离：")
        label_buffer.setFixedWidth(80)
        label_buffer.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.crop_buffer_spin = SpinBox(self)
        self.crop_buffer_spin.setRange(0, 10000)
        self.crop_buffer_spin.setValue(0)
        self.crop_buffer_spin.setSuffix(" 米")
        self.crop_buffer_spin.setFixedWidth(120)
        self.crop_buffer_spin.setFixedHeight(32)
        self.crop_buffer_spin.setToolTip("设置缓冲距离，0表示不缓冲")
        
        # 裁剪方式
        label_crop_method = QLabel("裁剪方式：")
        label_crop_method.setFixedWidth(80)
        label_crop_method.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.crop_method_combo = ComboBox(self)
        self.crop_method_combo.addItems(["按要素边界裁剪", "按要素最大矩形框边界裁剪"])
        self.crop_method_combo.setCurrentIndex(0)
        self.crop_method_combo.setFixedWidth(180)
        self.crop_method_combo.setFixedHeight(32)
        
        # 将所有裁剪参数组件添加到一行
        params_layout.addWidget(label_mode)
        params_layout.addWidget(self.crop_mode_combo)
        params_layout.addWidget(label_value)
        params_layout.addWidget(self.crop_field_value_edit)
        params_layout.addWidget(label_buffer)
        params_layout.addWidget(self.crop_buffer_spin)
        params_layout.addWidget(label_crop_method)
        params_layout.addWidget(self.crop_method_combo)
        
        # 输出设置区域
        output_group = QGroupBox("输出设置", self)
        output_layout = QVBoxLayout(output_group)
        output_layout.setSpacing(12)
        output_layout.setContentsMargins(15, 15, 15, 15)
        
        # 输出目录和格式设置（单行，包含执行按钮）
        outputRow = QHBoxLayout()
        outputRow.setSpacing(12)
        
        # 输出目录
        label_output_dir = QLabel("输出目录：")
        label_output_dir.setFixedWidth(80)
        label_output_dir.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.crop_output_dir_btn = PushButton(self.tr('选择目录'), self, FIF.FOLDER)
        self.crop_output_dir_btn.setFixedHeight(32)
        self.crop_output_dir_btn.setFixedWidth(120)
        self.crop_output_dir_btn.clicked.connect(self._on_crop_output_dir_btn)
        
        self.crop_output_dir_label = QLabel("")
        self.crop_output_dir_label.setStyleSheet("color: #888; border: 1px solid #ddd; padding: 6px 10px; border-radius: 4px;")
        self.crop_output_dir_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.crop_output_dir_label.setMinimumWidth(200)
        # 移除最大宽度限制，让标签能够根据面板宽度自动调整
        # self.crop_output_dir_label.setMaximumWidth(400)
        self.crop_output_dir_label.setToolTip("输出目录路径")
        self.crop_output_dir_label.setFixedHeight(32)
        self.crop_output_dir_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        # 输出格式
        label_output_format = QLabel("输出格式：")
        label_output_format.setFixedWidth(80)
        label_output_format.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.output_format_combo = ComboBox(self)
        self.output_format_combo.addItems(["tif", "img"])
        self.output_format_combo.setCurrentIndex(0)
        self.output_format_combo.setFixedWidth(100)
        self.output_format_combo.setFixedHeight(32)
        
        # 开始裁剪按钮
        self.crop_run_btn = PushButton(self.tr('开始裁剪'), self, FIF.SEND)
        self.crop_run_btn.setFixedWidth(120)
        self.crop_run_btn.setFixedHeight(36)
        self.crop_run_btn.clicked.connect(self.execute)
        
        outputRow.addWidget(label_output_dir)
        outputRow.addWidget(self.crop_output_dir_btn)
        outputRow.addWidget(self.crop_output_dir_label, 1)
        outputRow.addWidget(label_output_format)
        outputRow.addWidget(self.output_format_combo)
        outputRow.addWidget(self.crop_run_btn)
        output_layout.addLayout(outputRow)
        
        # 进度条容器
        self.progress_container = QWidget(self)
        self.progress_layout = QVBoxLayout(self.progress_container)
        self.progress_layout.setContentsMargins(0, 0, 0, 0)
        self.progress_layout.setSpacing(5)
        
        # 进度文本
        self.progress_text = QLabel("准备开始裁剪...", self)
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
        
        # 将所有组件添加到内容布局
        self.contentLayout.addWidget(input_group)
        self.contentLayout.addWidget(params_group)
        self.contentLayout.addWidget(output_group)
        self.contentLayout.addSpacing(20)
        self.contentLayout.addWidget(self.progress_container)
    
    def _short_path(self, path):
        """缩短路径显示"""
        if len(path) > 30:
            return "..." + path[-27:]
        return path
    
    def _on_crop_image_btn(self):
        """选择单个影像文件"""
        file_path, _ = QFileDialog.getOpenFileName(self, "选择影像文件", "", "影像文件 (*.tif *.tiff *.img)")
        if file_path:
            self.crop_image_path_label.setText(self._short_path(file_path))
            self.crop_image_path_label.setToolTip(file_path)
            self._crop_image_full_path = file_path
            # 自动生成输出路径
            if not self._crop_output_dir_full:
                self._auto_generate_output_dir(file_path)
    
    def _on_crop_multi_image_btn(self):
        """选择多个影像文件"""
        files, _ = QFileDialog.getOpenFileNames(self, "选择多个影像文件", "", "影像文件 (*.tif *.tiff *.img)")
        if files:
            self._add_images_to_table(files)
            # 自动生成输出路径
            if not self._crop_output_dir_full and files:
                self._auto_generate_output_dir(files[0])
    
    def _add_images_to_table(self, files):
        """添加影像到表格"""
        for file_path in files:
            # 检查是否已存在
            exists = False
            for row in range(self.imageTable.rowCount()):
                item = self.imageTable.item(row, 0)
                if item and item.text() == file_path:
                    exists = True
                    break
            
            if not exists:
                # 读取影像信息
                try:
                    # 延迟导入 rasterio，只在实际需要时导入
                    import rasterio
                    with rasterio.open(file_path) as src:
                        try:
                            crs = src.crs
                            zone = ''
                            # 坐标系信息 - 精简显示
                            if crs:
                                crs_str = str(crs)
                                # 精简 CGCS2000 / 3-degree Gauss-Kruger zone 36 为 CGCS2000 3度带36
                                if 'CGCS2000' in crs_str and '3-degree' in crs_str:
                                    import re
                                    zone_match = re.search(r'zone\s+(\d+)', crs_str)
                                    if zone_match:
                                        zone_num = zone_match.group(1)
                                        coord_system = f"CGCS2000 3度带{zone_num}"
                                    else:
                                        coord_system = "CGCS2000 3度带"
                                else:
                                    coord_system = crs_str.split('/')[0].strip() if '/' in crs_str else crs_str
                            else:
                                coord_system = '未知'
                            if crs and crs.is_projected:
                                # 优先尝试UTM带
                                if 'utm_zone' in crs.to_dict():
                                    zone = str(crs.to_dict()['utm_zone'])
                                elif 'zone' in crs.to_dict():
                                    zone = str(crs.to_dict()['zone'])
                                else:
                                    # 尝试通过投影中心经线推算3度/6度带号
                                    proj4 = crs.to_proj4()
                                    # 只处理常见的投影
                                    if '+proj=tmerc' in proj4 or '+proj=utm' in proj4:
                                        # 获取中心经线
                                        import re
                                        match = re.search(r'\+lon_0=([\d\.]+)', proj4)
                                        if match:
                                            lon_0 = float(match.group(1))
                                            # 3度带号
                                            zone3 = int(lon_0 / 3)
                                            # 6度带号
                                            zone6 = int(lon_0 / 6)
                                            zone = f"3度带:{zone3} 6度带:{zone6}"
                        except Exception:
                            zone = ''
                            coord_system = '未知'
                        bands = str(src.count)
                        xres = abs(src.transform.a)
                        yres = abs(src.transform.e)
                        res_str = f"{xres:.3f} x {yres:.3f}"
                except Exception as e:
                    zone = ''
                    coord_system = '未知'
                    bands = ''
                    res_str = ''
                
                # 插入新行
                row = self.imageTable.rowCount()
                self.imageTable.insertRow(row)
                self.imageTable.setItem(row, 0, QTableWidgetItem(file_path))
                self.imageTable.setItem(row, 1, QTableWidgetItem(coord_system))
                self.imageTable.setItem(row, 2, QTableWidgetItem(str(zone)))
                self.imageTable.setItem(row, 3, QTableWidgetItem(bands))
                self.imageTable.setItem(row, 4, QTableWidgetItem(res_str))
    
    def _on_remove_image(self):
        """移除选中的影像文件"""
        # 获取选中的行
        selected_rows = set()
        for index in self.imageTable.selectedIndexes():
            selected_rows.add(index.row())
        
        # 按行号从大到小移除，避免索引混乱
        for row in sorted(selected_rows, reverse=True):
            self.imageTable.removeRow(row)
    
    def _on_crop_vector_btn(self):
        """选择矢量文件"""
        file_path, _ = QFileDialog.getOpenFileName(self, "选择矢量文件", "", "矢量文件 (*.shp)")
        if file_path:
            self.crop_vector_path_label.setText(self._short_path(file_path))
            self.crop_vector_path_label.setToolTip(file_path)
            self._crop_vector_full_path = file_path
            try:
                gdf = gpd.read_file(file_path)
                
                # 检查坐标系
                if gdf.crs is None:
                    print('矢量文件缺少坐标系信息，请先定义投影。')
                    return
                
                # 更新字段列表
                fields = gdf.columns.tolist()
                if 'geometry' in fields:
                    fields.remove('geometry')
                self.crop_vector_field_cb.clear()
                self.crop_vector_field_cb.addItems(fields)
                self.crop_vector_field_cb.setCurrentIndex(-1)
                self.crop_vector_field_cb.setEnabled(True)
                
            except Exception as e:
                print(f'读取矢量文件失败: {str(e)}')
    
    def _on_crop_output_dir_btn(self):
        """选择输出目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if dir_path:
            self.crop_output_dir_label.setText(self._short_path(dir_path))
            self.crop_output_dir_label.setToolTip(dir_path)
            self._crop_output_dir_full = dir_path
    
    def _on_mode_changed(self):
        """裁剪模式改变"""
        is_single = self.crop_mode_combo.currentText() == "单一裁剪"
        self.crop_field_value_edit.setEnabled(is_single)
        if is_single:
            self.crop_field_value_edit.setPlaceholderText("输入要裁剪的字段值")
        else:
            self.crop_field_value_edit.clear()
            self.crop_field_value_edit.setPlaceholderText("批量裁剪时无需填写")
    
    def _auto_generate_output_dir(self, input_path):
        """自动生成输出目录"""
        dir_name = os.path.dirname(input_path)
        output_dir = os.path.join(dir_name, "crop_results")
        self._crop_output_dir_full = output_dir
        self.crop_output_dir_label.setText(self._short_path(output_dir))
        self.crop_output_dir_label.setToolTip(output_dir)
    
    def validate(self) -> tuple[bool, str]:
        """验证输入"""
        # 检查表格中是否有影像文件
        if self.imageTable.rowCount() == 0:
            return False, "请选择影像文件！"
        if not self._crop_vector_full_path or not os.path.exists(self._crop_vector_full_path):
            return False, "请选择有效的矢量文件！"
        if not self.crop_vector_field_cb.currentText():
            return False, "请选择裁剪字段！"
        if self.crop_mode_combo.currentText() == "单一裁剪" and not self.crop_field_value_edit.text().strip():
            return False, "单一裁剪模式下请输入字段值！"
        return True, ""
    
    def execute(self):
        """执行影像裁剪"""
        valid, message = self.validate()
        if not valid:
            self.showError(message)
            return
        
        if self._running:
            return
        
        self._running = True
        
        # 从表格中获取影像文件列表
        image_files = []
        for row in range(self.imageTable.rowCount()):
            item = self.imageTable.item(row, 0)
            if item:
                image_files.append(item.text())
        
        # 获取参数
        image_path = "\n".join(image_files)
        vector_path = self._crop_vector_full_path
        field_name = self.crop_vector_field_cb.currentText()
        mode = self.crop_mode_combo.currentText()
        field_value = self.crop_field_value_edit.text().strip() if mode == "单一裁剪" else None
        buffer_distance = self.crop_buffer_spin.value() if self.crop_buffer_spin.value() > 0 else None
        output_dir = self._crop_output_dir_full
        crop_method = self.crop_method_combo.currentText()
        
        # 如果没有选择输出目录，使用影像文件所在目录
        if not output_dir and image_files:
            output_dir = os.path.dirname(image_files[0])
        
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                self.showError(f'无法创建输出目录: {str(e)}')
                self._running = False
                return
        
        # 显示进度容器
        self.progress_container.setVisible(True)
        self.progress_text.setText("准备开始裁剪...")
        self.stateTooltip = StateToolTip('正在运行程序', '客官请耐心等待哦~~', self)
        self.stateTooltip.show()
        
        # 准备裁剪参数
        crop_params = (
            image_path,
            vector_path,
            field_name,
            mode,
            field_value,
            buffer_distance,
            output_dir,
            crop_method
        )
        
        # 创建并启动裁剪线程
        self.crop_thread = CropThread(crop_params, parent=self)
        
        # 连接信号
        self.crop_thread.progress_update.connect(self._onCropProgress)
        self.crop_thread.success.connect(self._onCropSuccess)
        self.crop_thread.error.connect(self._onCropError)
        self.crop_thread.finished.connect(self._onCropFinished)
        
        # 启动线程
        self.crop_thread.start()
    
    def _onCropProgress(self, progress: int):
        """裁剪进度更新处理"""
        # 更新进度文本，显示百分比
        self.progress_text.setText(f"正在裁剪... {progress}%")
        
        # 使用字符串拼接方式，避免花括号冲突
        progress_ratio = progress / 100.0
        style = """
            QFrame {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #0078D4, stop:""" + str(progress_ratio) + """ #0078D4, 
                    stop:""" + str(progress_ratio) + """ #e0e0e0, stop:1 #e0e0e0);
                border-radius: 2px;
            }
        """
        self.progress_bar.setStyleSheet(style)
    
    def _onCropSuccess(self, result_msg: str):
        """裁剪成功处理"""
        # 使用qfluentwidgets的MessageBox组件
        msg_box = MessageBox(
            '裁剪完成',
            result_msg,
            self
        )
        msg_box.exec()
    
    def _onCropError(self, error_msg: str):
        """裁剪错误处理"""
        # 使用qfluentwidgets的MessageBox组件
        msg_box = MessageBox(
            '裁剪失败',
            error_msg,
            self
        )
        msg_box.exec()
    
    def _onCropFinished(self):
        """裁剪线程结束处理"""
        # 重置进度容器
        self.progress_container.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QFrame {
                background-color: #e0e0e0;
                border-radius: 2px;
            }
        """)
        self.progress_text.setText("准备开始裁剪...")
        
        if self.stateTooltip:
            try:
                self.stateTooltip.close()
                self.stateTooltip = None
            except RuntimeError:
                pass
        self._running = False
