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
from PyQt6.QtWidgets import QFileDialog, QLabel, QHBoxLayout, QVBoxLayout
from qfluentwidgets import (
    ComboBox, LineEdit, PrimaryPushButton, ProgressBar, 
    SpinBox, TextEdit, TransparentPushButton, MessageBox, InfoBar
)
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import StateToolTip
from .base_function import BaseFunction
import geopandas as gpd


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
            "根据矢量范围裁剪影像<br>"
            "完整功能已实现"
        )
        super().__init__("影像裁剪功能", description, parent)
        
        self._running = False
        self._crop_image_full_path = ""
        self._crop_vector_full_path = ""
        self._crop_output_dir_full = ""
        self.stateTooltip = None
        self._initUI()
    
    def _initUI(self):
        """初始化界面"""
        # 第一行：说明标签
        infoLabel = QLabel(
            "📢 <span style='color: orange; font-weight: bold;'>功能说明：</span>"
            "<br>1. <b>批量裁剪</b>：根据矢量字段的所有唯一值进行裁剪，每个值生成一个影像文件"
            "<br>2. <b>单一裁剪</b>：根据指定的字段值进行裁剪，只生成一个影像文件"
            "<br>3. 支持多影像文件批量处理（.tif, .tiff, .img等格式）"
            "<br>4. <b>坐标系要求</b>：影像和矢量必须使用投影坐标系，不支持经纬度坐标系"
            "<br>5. 自动处理坐标系不一致的情况"
            "<br>6. 支持设置缓冲距离进行裁剪"
            "<br>7. 输出文件命名格式：原文件名_字段名_字段值.tif"
        )
        infoLabel.setWordWrap(True)
        infoLabel.setStyleSheet('''
            QLabel {
                padding: 10px 0 18px 0;
                font-size: 13px;
                line-height: 1.5;
            }
        ''')
        self.contentLayout.addWidget(infoLabel)
        
        # 第二行：影像文件选择
        imageRow = QHBoxLayout()
        imageRow.setSpacing(12)
        label_image = QLabel("影像文件：")
        label_image.setFixedWidth(60)
        
        crop_image_btn = TransparentPushButton(self.tr('选择'), self, FIF.DOCUMENT)
        crop_image_btn.setFixedHeight(32)
        crop_image_btn.clicked.connect(self._on_crop_image_btn)
        
        crop_multi_image_btn = TransparentPushButton(self.tr('多选'), self, FIF.DOCUMENT)
        crop_multi_image_btn.setFixedHeight(32)
        crop_multi_image_btn.setToolTip("选择多个影像文件")
        crop_multi_image_btn.clicked.connect(self._on_crop_multi_image_btn)
        
        self.crop_image_path_label = QLabel("")
        self.crop_image_path_label.setStyleSheet("color: #888;")
        self.crop_image_path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.crop_image_path_label.setMinimumWidth(180)
        self.crop_image_path_label.setMaximumWidth(320)
        self.crop_image_path_label.setToolTip("影像文件路径")
        self.crop_image_path_label.setFixedHeight(32)
        
        imageRow.addWidget(label_image)
        imageRow.addWidget(crop_image_btn)
        imageRow.addWidget(crop_multi_image_btn)
        imageRow.addWidget(self.crop_image_path_label)
        imageRow.addStretch(1)
        self.contentLayout.addLayout(imageRow)
        
        # 第三行：矢量文件选择
        vectorRow = QHBoxLayout()
        vectorRow.setSpacing(12)
        label_vector = QLabel("矢量文件：")
        label_vector.setFixedWidth(60)
        
        crop_vector_btn = TransparentPushButton(self.tr('选择'), self, FIF.DOCUMENT)
        crop_vector_btn.setFixedHeight(32)
        crop_vector_btn.clicked.connect(self._on_crop_vector_btn)
        
        self.crop_vector_path_label = QLabel("")
        self.crop_vector_path_label.setStyleSheet("color: #888;")
        self.crop_vector_path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.crop_vector_path_label.setMinimumWidth(180)
        self.crop_vector_path_label.setMaximumWidth(320)
        self.crop_vector_path_label.setToolTip("矢量文件路径")
        self.crop_vector_path_label.setFixedHeight(32)
        
        label_vector_field = QLabel("字段：")
        label_vector_field.setFixedWidth(40)
        
        self.crop_vector_field_cb = ComboBox(self)
        self.crop_vector_field_cb.setPlaceholderText("选择裁剪字段")
        self.crop_vector_field_cb.setFixedWidth(150)
        self.crop_vector_field_cb.setFixedHeight(32)
        self.crop_vector_field_cb.setEnabled(False)
        
        vectorRow.addWidget(label_vector)
        vectorRow.addWidget(crop_vector_btn)
        vectorRow.addWidget(self.crop_vector_path_label)
        vectorRow.addWidget(label_vector_field)
        vectorRow.addWidget(self.crop_vector_field_cb)
        vectorRow.addStretch(1)
        self.contentLayout.addLayout(vectorRow)
        
        # 第四行：裁剪模式选择
        modeRow = QHBoxLayout()
        modeRow.setSpacing(12)
        label_mode = QLabel("裁剪模式：")
        label_mode.setFixedWidth(60)
        
        self.crop_mode_combo = ComboBox(self)
        self.crop_mode_combo.addItems(["批量裁剪", "单一裁剪"])
        self.crop_mode_combo.setCurrentIndex(0)
        self.crop_mode_combo.setFixedWidth(120)
        self.crop_mode_combo.setFixedHeight(32)
        self.crop_mode_combo.currentTextChanged.connect(self._on_mode_changed)
        
        label_value = QLabel("字段值：")
        label_value.setFixedWidth(50)
        
        self.crop_field_value_edit = LineEdit(self)
        self.crop_field_value_edit.setPlaceholderText("输入要裁剪的字段值")
        self.crop_field_value_edit.setFixedWidth(150)
        self.crop_field_value_edit.setFixedHeight(32)
        self.crop_field_value_edit.setEnabled(False)
        
        label_buffer = QLabel("缓冲距离：")
        label_buffer.setFixedWidth(60)
        
        self.crop_buffer_spin = SpinBox(self)
        self.crop_buffer_spin.setRange(0, 10000)
        self.crop_buffer_spin.setValue(0)
        self.crop_buffer_spin.setSuffix(" 米")
        self.crop_buffer_spin.setFixedWidth(120)
        self.crop_buffer_spin.setFixedHeight(32)
        self.crop_buffer_spin.setToolTip("设置缓冲距离，0表示不缓冲")
        
        modeRow.addWidget(label_mode)
        modeRow.addWidget(self.crop_mode_combo)
        modeRow.addWidget(label_value)
        modeRow.addWidget(self.crop_field_value_edit)
        modeRow.addWidget(label_buffer)
        modeRow.addWidget(self.crop_buffer_spin)
        modeRow.addStretch(1)
        self.contentLayout.addLayout(modeRow)
        
        # 裁剪方式选择
        cropMethodRow = QHBoxLayout()
        cropMethodRow.setSpacing(12)
        label_crop_method = QLabel("裁剪方式：")
        label_crop_method.setFixedWidth(60)
        
        self.crop_method_combo = ComboBox(self)
        self.crop_method_combo.addItems(["按要素边界裁剪", "按要素最大矩形框边界裁剪"])
        self.crop_method_combo.setCurrentIndex(1)
        self.crop_method_combo.setFixedWidth(200)
        self.crop_method_combo.setFixedHeight(32)
        
        cropMethodRow.addWidget(label_crop_method)
        cropMethodRow.addWidget(self.crop_method_combo)
        cropMethodRow.addStretch(1)
        self.contentLayout.addLayout(cropMethodRow)
        
        # 第五行：输出目录设置
        outputRow = QHBoxLayout()
        outputRow.setSpacing(12)
        label_output_dir = QLabel("输出目录：")
        label_output_dir.setFixedWidth(60)
        
        crop_output_dir_btn = TransparentPushButton(self.tr('选择'), self, FIF.FOLDER)
        crop_output_dir_btn.setFixedHeight(32)
        crop_output_dir_btn.clicked.connect(self._on_crop_output_dir_btn)
        
        self.crop_output_dir_label = QLabel("")
        self.crop_output_dir_label.setStyleSheet("color: #888;")
        self.crop_output_dir_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.crop_output_dir_label.setMinimumWidth(180)
        self.crop_output_dir_label.setMaximumWidth(320)
        self.crop_output_dir_label.setToolTip("输出目录路径")
        self.crop_output_dir_label.setFixedHeight(32)
        
        outputRow.addWidget(label_output_dir)
        outputRow.addWidget(crop_output_dir_btn)
        outputRow.addWidget(self.crop_output_dir_label)
        outputRow.addStretch(1)
        self.contentLayout.addLayout(outputRow)
        
        # 第六行：进度条和日志显示
        progressLogLayout = QVBoxLayout()
        progressLogLayout.setSpacing(10)
        
        self.crop_log_text = TextEdit(self)
        self.crop_log_text.setReadOnly(True)
        self.crop_log_text.setFixedHeight(120)
        # 移除固定宽度，让日志框自适应面板宽度
        self.crop_log_text.setPlaceholderText("处理日志将显示在这里...")
        self.crop_log_text.hide()
        
        self.crop_progress = ProgressBar(self)
        # 移除固定宽度，让进度条自适应面板宽度
        self.crop_progress.hide()
        
        progressLogLayout.addWidget(self.crop_log_text)
        progressLogLayout.addWidget(self.crop_progress)
        self.contentLayout.addLayout(progressLogLayout)
        
        # 第七行：执行按钮
        btnRow = QHBoxLayout()
        btnRow.setContentsMargins(0, 10, 0, 0)
        btnRow.addStretch(1)
        
        crop_run_btn = PrimaryPushButton(self.tr('开始裁剪'), self, FIF.SEND)
        crop_run_btn.setFixedWidth(180)
        crop_run_btn.setFixedHeight(36)
        crop_run_btn.clicked.connect(self.execute)
        
        btnRow.addWidget(crop_run_btn)
        btnRow.addStretch(1)
        self.contentLayout.addLayout(btnRow)
    
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
    
    def _on_crop_multi_image_btn(self):
        """选择多个影像文件"""
        files, _ = QFileDialog.getOpenFileNames(self, "选择多个影像文件", "", "影像文件 (*.tif *.tiff *.img)")
        if files:
            file_text = "\n".join(files)
            self.crop_image_path_label.setText(f"已选择 {len(files)} 个文件")
            self.crop_image_path_label.setToolTip(file_text)
            self._crop_image_full_path = file_text
    
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
                    # 使用qfluentwidgets的MessageBox组件
                    msg_box = MessageBox(
                        '警告',
                        '矢量文件缺少坐标系信息，请先定义投影。',
                        self
                    )
                    msg_box.exec()
                    return
                
                if gdf.crs.is_geographic:
                    # 使用qfluentwidgets的MessageBox组件
                    msg_box = MessageBox(
                        '警告',
                        f'矢量文件使用地理坐标系（经纬度），无法直接进行裁剪。\n'
                        f'当前坐标系: {gdf.crs}\n'
                        f'请先将矢量文件投影到投影坐标系。',
                        self
                    )
                    msg_box.exec()
                    return
                
                # 显示坐标系信息
                crs_info = f"坐标系: {gdf.crs}"
                if hasattr(gdf.crs, 'to_epsg') and gdf.crs.to_epsg():
                    crs_info += f" (EPSG:{gdf.crs.to_epsg()})"
                
                # 更新字段列表
                fields = gdf.columns.tolist()
                if 'geometry' in fields:
                    fields.remove('geometry')
                self.crop_vector_field_cb.clear()
                self.crop_vector_field_cb.addItems(fields)
                self.crop_vector_field_cb.setCurrentIndex(-1)
                self.crop_vector_field_cb.setEnabled(True)
                
                # 显示成功信息
                msg_box = MessageBox(
                    '成功',
                    f'矢量文件加载成功！\n{crs_info}',
                    self
                )
                msg_box.exec()
                
            except Exception as e:
                # 使用qfluentwidgets的MessageBox组件
                msg_box = MessageBox(
                    '错误',
                    f'读取矢量文件失败: {str(e)}',
                    self
                )
                msg_box.exec()
    
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
    
    def validate(self) -> tuple[bool, str]:
        """验证输入"""
        if not self._crop_image_full_path:
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
        
        # 获取参数
        image_path = self._crop_image_full_path
        vector_path = self._crop_vector_full_path
        field_name = self.crop_vector_field_cb.currentText()
        mode = self.crop_mode_combo.currentText()
        field_value = self.crop_field_value_edit.text().strip() if mode == "单一裁剪" else None
        buffer_distance = self.crop_buffer_spin.value() if self.crop_buffer_spin.value() > 0 else None
        output_dir = self._crop_output_dir_full
        crop_method = self.crop_method_combo.currentText()
        
        # 如果没有选择输出目录，使用影像文件所在目录
        if not output_dir:
            if os.path.isfile(image_path):
                output_dir = os.path.dirname(image_path)
            else:
                # 多文件情况，使用第一个文件的目录
                first_file = image_path.split('\n')[0].strip()
                output_dir = os.path.dirname(first_file)
        
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                self.showError(f'无法创建输出目录: {str(e)}')
                self._running = False
                return
        
        # 显示进度条和日志
        self.crop_progress.show()
        self.crop_log_text.show()
        self.crop_progress.setValue(0)
        self.crop_log_text.clear()
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
        self.crop_thread.log_update.connect(self._onCropLogUpdate)
        self.crop_thread.success.connect(self._onCropSuccess)
        self.crop_thread.error.connect(self._onCropError)
        self.crop_thread.finished.connect(self._onCropFinished)
        
        # 启动线程
        self.crop_thread.start()
    
    def _onCropProgress(self, progress: int):
        """裁剪进度更新处理"""
        self.crop_progress.setValue(progress)
    
    def _onCropLogUpdate(self, log_text: str):
        """裁剪日志更新处理"""
        current_text = self.crop_log_text.toPlainText()
        new_text = current_text + log_text
        self.crop_log_text.setText(new_text)
        # 滚动到底部
        scrollbar = self.crop_log_text.verticalScrollBar()
        if scrollbar:
            scrollbar.setValue(scrollbar.maximum())
    
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
        self.crop_progress.hide()
        self.crop_log_text.hide()
        if self.stateTooltip:
            try:
                self.stateTooltip.close()
                self.stateTooltip = None
            except RuntimeError:
                pass
        self._running = False
