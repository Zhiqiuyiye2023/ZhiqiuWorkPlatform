# coding:utf-8
"""
影像拼接功能
"""

import sys
import os

# 添加根目录到path，以便导入数据处理方法模块
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QFileDialog, QHeaderView, QTableWidgetItem, QPushButton, QGroupBox, QVBoxLayout, QWidget, QFrame
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from qfluentwidgets import ComboBox, PushButton, ProgressBar, LineEdit, TableWidget
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction


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


class MosaicThread(QThread):
    """影像拼接线程"""
    
    success = pyqtSignal(str)      # 成功信号，传递结果信息
    error = pyqtSignal(str)        # 错误信号，传递错误信息
    progress_update = pyqtSignal(int) # 进度更新信号
    
    def __init__(self, files, out_format, output_path, output_name="mosaic_result", parent=None):
        """
        Args:
            files: 影像文件列表
            out_format: 输出格式
            output_path: 输出文件路径
            output_name: 输出影像名称
            parent: 父对象
        """
        super().__init__(parent)
        self.files = files
        self.out_format = out_format
        self.output_path = output_path
        self.output_name = output_name
    
    def run(self):
        """线程运行方法"""
        try:
            # 处理打包后可能出现的导入问题
            import sys
            import os
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if root_dir not in sys.path:
                sys.path.append(root_dir)
            # 使用动态导入来处理中文模块名
            import importlib
            影像处理 = importlib.import_module('functions.影像处理')
            影像拼接 = getattr(影像处理, '影像拼接')
            
            # 定义进度回调函数
            def update_progress(progress):
                self.progress_update.emit(int(progress))
            
            # 准备文件列表文本
            file_text = "\n".join(self.files)
            
            # 执行影像拼接
            影像拼接(file_text, update_progress, out_format=self.out_format, out_res=None, output_name=self.output_name, output_path=self.output_path)
            
            self.success.emit("影像拼接完成！")
        except Exception as e:
            import traceback
            self.error.emit(f"拼接失败: {str(e)}\n\n{traceback.format_exc()}")


class ImageMosaicFunction(BaseFunction):
    """影像拼接功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>"
            "多影像文件拼接处理<br>"
            "完整功能已实现"
        )
        super().__init__("影像拼接功能", description, parent)
        
        self._running = False
        self._initUI()
    
    def _initUI(self):
        """初始化界面"""
        # 移除提示标签，根据用户要求不再显示
        
        # 输入影像设置区域
        input_group = QGroupBox("输入影像设置", self)
        input_layout = QVBoxLayout(input_group)
        
        # 影像文件表格
        self.imageTable = DragDropTableWidget(self, self._add_images_to_table)
        self.imageTable.setColumnCount(5)
        self.imageTable.setHorizontalHeaderLabels(['路径', '坐标系', '分度带', '波段', '分辨率'])
        
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
        
        # 设置与表格比对功能一致的样式
        self.imageTable.setAlternatingRowColors(True)
        self.imageTable.setBorderVisible(True)
        
        input_layout.addWidget(self.imageTable)
        
        # 添加和移除影像文件按钮
        buttons_layout = QHBoxLayout()
        self.addImageButton = PushButton("添加影像", self, FIF.ADD)
        self.addImageButton.setToolTip("点击选择影像文件")
        self.addImageButton.clicked.connect(self._on_add_image)
        self.addImageButton.setFixedWidth(120)
        
        # 移除选中影像按钮
        self.removeImageButton = PushButton("移除选中", self, FIF.DELETE)
        self.removeImageButton.setToolTip("移除选中的影像文件")
        self.removeImageButton.clicked.connect(self._on_remove_image)
        self.removeImageButton.setFixedWidth(120)
        
        buttons_layout.addWidget(self.addImageButton)
        buttons_layout.addWidget(self.removeImageButton)
        buttons_layout.addStretch(1)
        input_layout.addLayout(buttons_layout)
        
        # 输出设置区域
        output_group = QGroupBox("输出设置", self)
        output_layout = QVBoxLayout(output_group)
        
        # 输出路径设置（包含输出名称和格式，全部放在同一行）
        output_row_layout = QHBoxLayout()
        output_row_layout.setSpacing(12)
        
        # 输出路径
        output_path_label = QLabel("输出路径：")
        self.output_path = LineEdit(self)
        self.output_path.setPlaceholderText("选择输出文件路径")
        self.output_path.setReadOnly(True)
        
        self.output_path_btn = PushButton("选择路径", self, FIF.FOLDER)
        self.output_path_btn.clicked.connect(self._select_output_path)
        self.output_path_btn.setFixedWidth(120)
        
        # 输出文件名
        output_name_label = QLabel("输出名称：")
        self.outputNameEdit = LineEdit(self)
        self.outputNameEdit.setText("mosaic_result")
        self.outputNameEdit.setPlaceholderText("输出影像名称")
        self.outputNameEdit.setFixedWidth(150)
        self.outputNameEdit.textChanged.connect(self._update_output_path)
        
        # 输出格式
        self.formatLabel = QLabel("输出格式：")
        self.formatCombo = ComboBox(self)
        self.formatCombo.addItems(["tif", "img"])
        self.formatCombo.setCurrentIndex(0)
        self.formatCombo.setFixedWidth(80)
        self.formatCombo.currentTextChanged.connect(self._update_output_path)
        
        # 将所有组件按顺序添加到同一行
        output_row_layout.addWidget(output_path_label)
        output_row_layout.addWidget(self.output_path, 1)
        output_row_layout.addWidget(self.output_path_btn)
        output_row_layout.addWidget(output_name_label)
        output_row_layout.addWidget(self.outputNameEdit)
        output_row_layout.addWidget(self.formatLabel)
        output_row_layout.addWidget(self.formatCombo)
        
        output_layout.addLayout(output_row_layout)
        
        # 进度条容器
        self.progress_container = QWidget(self)
        self.progress_layout = QVBoxLayout(self.progress_container)
        self.progress_layout.setContentsMargins(0, 0, 0, 0)
        self.progress_layout.setSpacing(5)
        
        # 进度文本
        self.progress_text = QLabel("准备开始拼接...", self)
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
        self.contentLayout.addWidget(output_group)
        self.contentLayout.addSpacing(20)
        self.contentLayout.addWidget(self.progress_container)
        
        # 添加执行按钮
        self.buttonAW = PushButton(self.tr('开始拼接'), self, FIF.SEND)
        self.buttonAW.clicked.connect(self.execute)
        self.buttonAW.setFixedWidth(180)
        
        # 执行按钮布局
        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.buttonAW)
        btn_layout.addStretch(1)
        self.contentLayout.addLayout(btn_layout)
    
    def _on_add_image(self):
        """添加影像文件"""
        files, _ = QFileDialog.getOpenFileNames(self, "选择影像文件", "", "影像文件 (*.tif *.tiff *.img)")
        if files:
            self._add_images_to_table(files)
            # 自动生成输出路径
            if files and not self.output_path.text():
                self._auto_generate_output_path(files[0])
    
    def _on_remove_image(self):
        """移除选中的影像文件"""
        # 获取选中的行
        selected_rows = set()
        for index in self.imageTable.selectedIndexes():
            selected_rows.add(index.row())
        
        # 按行号从大到小移除，避免索引混乱
        for row in sorted(selected_rows, reverse=True):
            self.imageTable.removeRow(row)
    
    def _select_output_path(self):
        """选择输出路径"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "选择输出文件", "", f"影像文件 (*.{self.formatCombo.currentText()})")
        if file_path:
            self.output_path.setText(file_path)
    
    def _auto_generate_output_path(self, input_path):
        """自动生成输出路径"""
        dir_name = os.path.dirname(input_path)
        base_name = self.outputNameEdit.text()
        ext = self.formatCombo.currentText()
        output_path = os.path.join(dir_name, f"{base_name}.{ext}")
        self.output_path.setText(output_path)
    
    def _update_output_path(self):
        """更新输出路径"""
        if self.output_path.text():
            # 保留目录部分，更新文件名和扩展名
            dir_name = os.path.dirname(self.output_path.text())
            base_name = self.outputNameEdit.text()
            ext = self.formatCombo.currentText()
            output_path = os.path.join(dir_name, f"{base_name}.{ext}")
            self.output_path.setText(output_path)
    
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
    
    def validate(self) -> tuple[bool, str]:
        """验证输入"""
        if self.imageTable.rowCount() == 0:
            return False, "请至少添加一个影像文件"
        if not self.output_path.text():
            return False, "请选择输出路径"
        return True, ""
    
    def execute(self):
        """执行影像拼接"""
        valid, message = self.validate()
        if not valid:
            self.showError(message)
            return
        
        if self._running:
            return
        
        self._running = True
        
        # 获取所有输入影像路径
        files = []
        for row in range(self.imageTable.rowCount()):
            item = self.imageTable.item(row, 0)
            if item:
                files.append(item.text())
        
        out_format = self.formatCombo.currentText()
        
        # 显示进度容器
        self.progress_container.setVisible(True)
        self.progress_text.setText("准备开始拼接...")
        
        # 创建并启动影像拼接线程
        self.mosaic_thread = MosaicThread(
            files=files,
            out_format=out_format,
            output_path=self.output_path.text(),
            parent=self
        )
        
        # 连接信号
        self.mosaic_thread.progress_update.connect(self._onMosaicProgress)
        self.mosaic_thread.success.connect(self._onMosaicSuccess)
        self.mosaic_thread.error.connect(self._onMosaicError)
        self.mosaic_thread.finished.connect(self._onMosaicFinished)
        
        # 启动线程
        self.mosaic_thread.start()
    
    def _onMosaicProgress(self, progress: int):
        """影像拼接进度更新处理"""
        # 更新进度文本，显示百分比
        self.progress_text.setText(f"正在拼接... {progress}%")
        
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
    
    def _onMosaicSuccess(self, result_msg: str):
        """影像拼接成功处理"""
        # 重置进度容器
        self.progress_container.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QFrame {
                background-color: #e0e0e0;
                border-radius: 2px;
            }
        """)
        self.progress_text.setText("准备开始拼接...")
        self.showSuccess(result_msg)
    
    def _onMosaicError(self, error_msg: str):
        """影像拼接错误处理"""
        # 重置进度容器
        self.progress_container.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QFrame {
                background-color: #e0e0e0;
                border-radius: 2px;
            }
        """)
        self.progress_text.setText("准备开始拼接...")
        self.showError(error_msg)
    
    def _onMosaicFinished(self):
        """影像拼接线程结束处理"""
        self._running = False