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

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QFileDialog, QHeaderView, QTableWidgetItem, QPushButton, QTableWidget
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from qfluentwidgets import ComboBox, PrimaryPushButton, ProgressBar, LineEdit
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction


class DragDropTableWidget(QTableWidget):
    """支持拖拽的表格组件"""
    
    def __init__(self, parent=None, add_callback=None):
        super().__init__(parent)
        self.add_callback = add_callback
        self.setAcceptDrops(True)
        self.setDragDropMode(QTableWidget.DragDropMode.DropOnly)
    
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
    
    def __init__(self, files, out_format, output_name="mosaic_result", parent=None):
        """
        Args:
            files: 影像文件列表
            out_format: 输出格式
            output_name: 输出影像名称
            parent: 父对象
        """
        super().__init__(parent)
        self.files = files
        self.out_format = out_format
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
            影像拼接(file_text, update_progress, out_format=self.out_format, out_res=None, output_name=self.output_name)
            
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
        # 第一行：提示标签
        infoLabel = QLabel(
            "📢 <span style='color: orange; font-weight: bold;'>提示：</span>"
            "<br>1. 可拖拽或点击添加影像文件"
            "<br>2. 支持格式：TIF、IMG"
            "<br>3. 可设置输出格式和分辨率"
            "<br>4. 拼接结果保存在输入文件所在目录"
        )
        infoLabel.setWordWrap(True)
        self.contentLayout.addWidget(infoLabel)
        
        # 第二行：影像文件表格
        self.imageTable = DragDropTableWidget(self, self._add_images_to_table)
        self.imageTable.setColumnCount(5)
        self.imageTable.setHorizontalHeaderLabels(['路径', '分度带', '波段', '分辨率', '操作'])
        
        header = self.imageTable.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            for i in range(1, 5):
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        self.imageTable.setStyleSheet("""
            QTableWidget {
                background-color: #222;
                color: #fff;
                gridline-color: #444;
                font-size: 14px;
            }
            QHeaderView::section {
                background-color: #111;
                color: #fff;
                font-weight: bold;
                border: 1px solid #444;
            }
            QTableWidget QTableCornerButton::section {
                background-color: #111;
                border: 1px solid #444;
            }
            QTableWidget::item:selected {
                background-color: #444;
                color: #fff;
            }
        """)
        
        self.imageTable.setFixedWidth(1070)
        self.contentLayout.addWidget(self.imageTable, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        # 第三行：控件平铺一行
        fileParamLayout = QHBoxLayout()
        
        self.addImageButton = PrimaryPushButton(self.tr('添加'), self, FIF.ADD)
        self.addImageButton.setToolTip("点击选择影像文件")
        self.addImageButton.clicked.connect(self._on_add_image)
        fileParamLayout.addWidget(self.addImageButton)
        
        # 输出文件名输入框
        self.outputNameLabel = QLabel("输出名称：")
        fileParamLayout.addWidget(self.outputNameLabel)
        
        self.outputNameEdit = LineEdit(self)
        self.outputNameEdit.setText("mosaic_result")
        self.outputNameEdit.setPlaceholderText("请输入输出影像名称")
        self.outputNameEdit.setFixedWidth(150)
        fileParamLayout.addWidget(self.outputNameEdit)
        
        self.formatLabel = QLabel("输出格式：")
        fileParamLayout.addWidget(self.formatLabel)
        
        self.formatCombo = ComboBox(self)
        self.formatCombo.addItems(["tif", "img"])
        self.formatCombo.setCurrentIndex(0)
        self.formatCombo.setFixedWidth(80)
        fileParamLayout.addWidget(self.formatCombo)
        
        self.buttonAW = PrimaryPushButton(self.tr('开始拼接'), self, FIF.SEND)
        self.buttonAW.clicked.connect(self.execute)
        fileParamLayout.addWidget(self.buttonAW)
        
        self.contentLayout.addLayout(fileParamLayout)
        
        # 第四行：进度条
        self.progressBarImage = ProgressBar(self)
        self.progressBarImage.hide()
        self.contentLayout.addWidget(self.progressBarImage)
    
    def _on_add_image(self):
        """添加影像文件"""
        files, _ = QFileDialog.getOpenFileNames(self, "选择影像文件", "", "影像文件 (*.tif *.tiff *.img)")
        if files:
            self._add_images_to_table(files)
    
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
                        bands = str(src.count)
                        xres = abs(src.transform.a)
                        yres = abs(src.transform.e)
                        res_str = f"{xres:.3f} x {yres:.3f}"
                except Exception as e:
                    zone = ''
                    bands = ''
                    res_str = ''
                
                # 插入新行
                row = self.imageTable.rowCount()
                self.imageTable.insertRow(row)
                self.imageTable.setItem(row, 0, QTableWidgetItem(file_path))
                self.imageTable.setItem(row, 1, QTableWidgetItem(str(zone)))
                self.imageTable.setItem(row, 2, QTableWidgetItem(bands))
                self.imageTable.setItem(row, 3, QTableWidgetItem(res_str))
                
                # 移除按钮
                btn = QPushButton("移除")
                def make_remove_callback(current_row):
                    def remove_row():
                        self.imageTable.removeRow(current_row)
                    return remove_row
                btn.clicked.connect(make_remove_callback(row))
                self.imageTable.setCellWidget(row, 4, btn)
    
    def validate(self) -> tuple[bool, str]:
        """验证输入"""
        if self.imageTable.rowCount() == 0:
            return False, "请至少添加一个影像文件"
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
        
        # 显示进度条
        self.progressBarImage.show()
        self.progressBarImage.setValue(0)
        
        # 创建并启动影像拼接线程
        self.mosaic_thread = MosaicThread(
            files=files,
            out_format=out_format,
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
        self.progressBarImage.setValue(progress)
    
    def _onMosaicSuccess(self, result_msg: str):
        """影像拼接成功处理"""
        self.progressBarImage.hide()
        self.showSuccess(result_msg)
    
    def _onMosaicError(self, error_msg: str):
        """影像拼接错误处理"""
        self.progressBarImage.hide()
        self.showError(error_msg)
    
    def _onMosaicFinished(self):
        """影像拼接线程结束处理"""
        self._running = False