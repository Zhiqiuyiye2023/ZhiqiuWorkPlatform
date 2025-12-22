# coding:utf-8
"""
影像裁剪按行政区域分类功能
"""

import sys
import os
import threading

# 添加根目录到path，以便导入数据处理方法模块
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QFileDialog, QMessageBox, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from qfluentwidgets import (
    PrimaryPushButton, ProgressBar, 
    TextEdit, TransparentPushButton
)
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import StateToolTip
from .base_function import BaseFunction
import geopandas as gpd
import numpy as np
from shapely.geometry import mapping, box
import fiona


class CropThread(QThread):
    """影像裁剪线程"""
    
    success = pyqtSignal(str)  # 成功信号，传递结果信息
    error = pyqtSignal(str)    # 错误信号，传递错误信息
    progress = pyqtSignal(str) # 进度信号，传递进度信息
    
    def __init__(self, image_folder, vector_path, output_folder, use_simplify, parent=None):
        """
        Args:
            image_folder: 影像文件夹路径
            vector_path: 矢量文件路径
            output_folder: 输出文件夹路径
            use_simplify: 是否使用简化几何形状
            parent: 父对象
        """
        super().__init__(parent)
        self.image_folder = image_folder
        self.vector_path = vector_path
        self.output_folder = output_folder
        self.use_simplify = use_simplify
    
    def run(self):
        """线程运行方法"""
        try:
            # 读取矢量数据
            self.progress.emit("正在读取矢量数据...")
            gdf = gpd.read_file(self.vector_path)
            
            # 确保输出文件夹存在
            os.makedirs(self.output_folder, exist_ok=True)
            
            # 获取所有影像文件
            self.progress.emit("正在获取影像文件列表...")
            image_files = []
            for ext in ['.tif', '.tiff', '.jpg', '.jpeg', '.png', '.bmp']:
                image_files.extend([os.path.join(self.image_folder, f) for f in os.listdir(self.image_folder) 
                                   if f.lower().endswith(ext)])
            
            if not image_files:
                raise ValueError("未找到任何影像文件")
            
            self.progress.emit(f"找到 {len(image_files)} 个影像文件，开始裁剪...")
            
            # 遍历每个影像文件
            for i, image_path in enumerate(image_files):
                image_name = os.path.basename(image_path)
                self.progress.emit(f"正在处理 {image_name} ({i+1}/{len(image_files)})...")
                
                try:
                    # 延迟导入 rasterio，只在实际需要时导入
                    import rasterio
                    from rasterio.mask import mask
                    
                    # 打开影像文件
                    with rasterio.open(image_path) as src:
                        # 读取影像边界
                        image_bounds = box(*src.bounds)
                        
                        # 筛选与影像相交的矢量要素
                        intersecting_gdf = gdf[gdf.intersects(image_bounds)]
                        
                        if intersecting_gdf.empty:
                            self.progress.emit(f"  跳过: 无相交行政区域")
                            continue
                        
                        # 遍历每个相交的行政区域
                        for idx, row in intersecting_gdf.iterrows():
                            geom = row.geometry
                            admin_name = str(row.iloc[0])  # 假设第一个字段是行政区域名称
                            
                            # 创建行政区域文件夹
                            admin_folder = os.path.join(self.output_folder, admin_name)
                            os.makedirs(admin_folder, exist_ok=True)
                            
                            # 生成输出文件名
                            output_name = f"{os.path.splitext(image_name)[0]}_{admin_name}{os.path.splitext(image_name)[1]}"
                            output_path = os.path.join(admin_folder, output_name)
                            
                            try:
                                # 裁剪影像
                                self.progress.emit(f"  正在裁剪 {admin_name}...")
                                out_image, out_transform = mask(src, [mapping(geom)], crop=True)
                                
                                # 更新元数据
                                out_meta = src.meta.copy()
                                out_meta.update({
                                    "driver": "GTiff",
                                    "height": out_image.shape[1],
                                    "width": out_image.shape[2],
                                    "transform": out_transform
                                })
                                
                                # 保存裁剪结果
                                with rasterio.open(output_path, "w", **out_meta) as dest:
                                    dest.write(out_image)
                                
                                self.progress.emit(f"  成功: 保存到 {output_path}")
                                
                            except Exception as e:
                                if self.use_simplify:
                                    # 尝试使用简化的几何形状
                                    self.progress.emit(f"  错误: 裁剪失败，尝试使用简化几何形状: {str(e)}")
                                    
                                    # 简化几何形状
                                    simplified_geom = geom.simplify(0.001, preserve_topology=True)
                                    
                                    try:
                                        # 使用简化后的几何形状裁剪
                                        out_image, out_transform = mask(
                                            src, 
                                            [mapping(simplified_geom)], 
                                            crop=True, 
                                            all_touched=True
                                        )
                                        
                                        # 更新元数据
                                        out_meta = src.meta.copy()
                                        out_meta.update({
                                            "driver": "GTiff",
                                            "height": out_image.shape[1],
                                            "width": out_image.shape[2],
                                            "transform": out_transform
                                        })
                                        
                                        # 保存简化后的裁剪结果
                                        with rasterio.open(output_path, "w", **out_meta) as dest:
                                            dest.write(out_image)
                                        
                                        self.progress.emit(f"  成功: 使用简化几何形状裁剪并保存到 {output_path}")
                                        
                                    except Exception as simplified_error:
                                        self.progress.emit(f"  错误: 简化几何形状裁剪也失败: {str(simplified_error)}")
                                        continue
                                else:
                                    self.progress.emit(f"  错误: 裁剪失败: {str(e)}")
                                    continue
                        
                except Exception as e:
                    self.progress.emit(f"  错误: 处理 {image_name} 时出错: {str(e)}")
                    continue
            
            self.progress.emit("\n影像裁剪完成！")
            self.success.emit("影像裁剪按行政区域分类完成！")
            
        except Exception as e:
            self.error.emit(f"裁剪失败: {str(e)}")


class ImageCropByAdminRegionFunction(BaseFunction):
    """影像裁剪按行政区域分类功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br> "
            "根据行政区域矢量文件裁剪影像，并按区域分类保存"
        )
        super().__init__("影像裁剪按行政区域分类", description, parent)
        
        self._running = False
        self._shapefile_path = ""
        self._work_dir = ""
        self.stateTooltip = None
        self._initUI()
    
    def _initUI(self):
        """初始化界面"""
        # 第一行：说明标签
        infoLabel = QLabel(
            "📢 <span style='color: orange; font-weight: bold;'>功能说明：</span>"
            "<br>1. 自动读取指定目录下的所有影像文件"
            "<br>2. 根据行政区域矢量文件裁剪影像"
            "<br>3. 按行政区域名称创建子文件夹保存裁剪结果"
            "<br>4. 支持多种影像格式：.tif, .tiff, .img"
            "<br>5. 自动处理坐标系不一致问题"
            "<br>6. 支持几何形状修复和简化"
            "<br>7. 跳过不重叠的区域"
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
        
        # 第二行：工作目录选择
        workDirRow = QHBoxLayout()
        workDirRow.setSpacing(12)
        label_workdir = QLabel("工作目录：")
        label_workdir.setFixedWidth(60)
        
        workdir_btn = TransparentPushButton(self.tr('选择'), self, FIF.FOLDER)
        workdir_btn.setFixedHeight(32)
        workdir_btn.clicked.connect(self._on_workdir_btn)
        
        self.workdir_label = QLabel("")
        self.workdir_label.setStyleSheet("color: #888;")
        self.workdir_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.workdir_label.setMinimumWidth(180)
        self.workdir_label.setMaximumWidth(320)
        self.workdir_label.setToolTip("")
        self.workdir_label.setFixedHeight(32)
        
        workDirRow.addWidget(label_workdir)
        workDirRow.addWidget(workdir_btn)
        workDirRow.addWidget(self.workdir_label)
        workDirRow.addStretch(1)
        self.contentLayout.addLayout(workDirRow)
        
        # 第三行：矢量文件选择
        vectorRow = QHBoxLayout()
        vectorRow.setSpacing(12)
        label_vector = QLabel("矢量文件：")
        label_vector.setFixedWidth(60)
        
        vector_btn = TransparentPushButton(self.tr('选择'), self, FIF.DOCUMENT)
        vector_btn.setFixedHeight(32)
        vector_btn.clicked.connect(self._on_vector_btn)
        
        self.vector_path_label = QLabel("")
        self.vector_path_label.setStyleSheet("color: #888;")
        self.vector_path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.vector_path_label.setMinimumWidth(180)
        self.vector_path_label.setMaximumWidth(320)
        self.vector_path_label.setToolTip("")
        self.vector_path_label.setFixedHeight(32)
        
        vectorRow.addWidget(label_vector)
        vectorRow.addWidget(vector_btn)
        vectorRow.addWidget(self.vector_path_label)
        vectorRow.addStretch(1)
        self.contentLayout.addLayout(vectorRow)
        
        # 第四行：进度条和日志显示
        progressLogLayout = QVBoxLayout()
        progressLogLayout.setSpacing(10)
        
        self.log_text = TextEdit(self)
        self.log_text.setReadOnly(True)
        self.log_text.setFixedHeight(120)
        self.log_text.setFixedWidth(400)
        self.log_text.setPlaceholderText("处理日志将显示在这里...")
        self.log_text.hide()
        
        self.progress = ProgressBar(self)
        self.progress.setFixedWidth(400)
        self.progress.hide()
        
        progressLogLayout.addWidget(self.log_text)
        progressLogLayout.addWidget(self.progress)
        
        # 添加到主布局
        self.contentLayout.addLayout(progressLogLayout)
        
        # 第五行：执行按钮
        btnRow = QHBoxLayout()
        btnRow.setContentsMargins(0, 10, 0, 0)
        btnRow.addStretch(1)
        
        run_btn = PrimaryPushButton(self.tr('开始裁剪'), self, FIF.SEND)
        run_btn.setFixedWidth(180)
        run_btn.setFixedHeight(36)
        run_btn.clicked.connect(self.execute)
        
        btnRow.addWidget(run_btn)
        btnRow.addStretch(1)
        self.contentLayout.addLayout(btnRow)
    
    def _short_path(self, path):
        """缩短路径显示"""
        if len(path) > 30:
            return "..." + path[-27:]
        return path
    
    def _on_workdir_btn(self):
        """选择工作目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择工作目录")
        if dir_path:
            self.workdir_label.setText(self._short_path(dir_path))
            self.workdir_label.setToolTip(dir_path)
            self._work_dir = dir_path
    
    def _on_vector_btn(self):
        """选择矢量文件"""
        file_path, _ = QFileDialog.getOpenFileName(self, "选择矢量文件", "", "矢量文件 (*.shp)")
        if file_path:
            self.vector_path_label.setText(self._short_path(file_path))
            self.vector_path_label.setToolTip(file_path)
            self._shapefile_path = file_path
    
    def validate(self) -> tuple[bool, str]:
        """验证输入"""
        if not self._work_dir or not os.path.exists(self._work_dir):
            return False, "请选择有效的工作目录！"
        if not self._shapefile_path or not os.path.exists(self._shapefile_path):
            return False, "请选择有效的矢量文件！"
        return True, ""
    
    def execute(self):
        """执行影像裁剪按行政区域分类"""
        valid, message = self.validate()
        if not valid:
            self.showError(message)
            return
        
        if self._running:
            return
        
        self._running = True
        
        # 显示进度条和日志
        self.progress.show()
        self.log_text.show()
        self.progress.setValue(0)
        self.log_text.clear()
        self.stateTooltip = StateToolTip('正在运行程序', '客官请耐心等待哦~~', self)
        self.stateTooltip.show()
        
        def run_crop():
            import logging
            import traceback
            try:
                # 导入所需模块
                import geopandas as gpd
                import numpy as np
                from shapely.geometry import mapping, box
                
                def log_cb(msg):
                    def update_log():
                        current_text = self.log_text.toPlainText()
                        new_text = current_text + msg + "\n"
                        self.log_text.setText(new_text)
                        # 滚动到底部
                        scrollbar = self.log_text.verticalScrollBar()
                        if scrollbar:
                            scrollbar.setValue(scrollbar.maximum())
                    QTimer.singleShot(0, update_log)
                
                # 设置工作路径
                work_dir = self._work_dir
                shapefile_path = self._shapefile_path
                
                # 读取矢量数据
                log_cb(f"正在读取矢量数据: {shapefile_path}")
                gdf = gpd.read_file(shapefile_path)
                log_cb(f"成功读取矢量数据，包含 {len(gdf)} 个行政区域")
                log_cb(f"矢量数据的坐标系统: {gdf.crs}")
                
                # 检查矢量数据是否有坐标系统，如果没有则尝试设置
                if gdf.crs is None:
                    log_cb("警告: 矢量数据没有坐标系统信息，尝试使用EPSG:4326(WGS84)")
                    gdf.set_crs("EPSG:4326", inplace=True)
                    log_cb(f"已设置矢量数据坐标系统为: {gdf.crs}")
                
                # 列出所有待裁剪的影像文件
                supported_formats = ['.tif', '.tiff', '.img']
                image_files = []
                for file in os.listdir(work_dir):
                    ext = os.path.splitext(file)[1].lower()
                    if ext in supported_formats:
                        image_files.append(os.path.join(work_dir, file))
                
                log_cb(f"发现 {len(image_files)} 个影像文件")
                
                # 计算总进度
                total_steps = len(gdf) * len(image_files)
                current_step = 0
                
                # 按行政区域裁剪影像
                for idx, row in gdf.iterrows():
                    # 获取行政区名称
                    xzqmc = row['XZQMC']
                    log_cb(f"\n处理第 {idx+1}/{len(gdf)} 个行政区域: {xzqmc}")
                    
                    # 创建对应的输出文件夹
                    output_dir = os.path.join(work_dir, xzqmc)
                    os.makedirs(output_dir, exist_ok=True)
                    log_cb(f"创建输出文件夹: {output_dir}")
                    
                    # 获取当前行政区的几何形状
                    original_geometry = row['geometry']
                    
                    # 裁剪每个影像文件
                    for image_path in image_files:
                        current_step += 1
                        progress = int((current_step / total_steps) * 100)
                        self.progress.setValue(progress)
                        
                        image_name = os.path.basename(image_path)
                        output_path = os.path.join(output_dir, image_name)
                        
                        log_cb(f"  裁剪影像: {image_name} -> {xzqmc}/{image_name}")
                        
                        try:
                            # 延迟导入 rasterio，只在实际需要时导入
                            import rasterio
                            from rasterio.mask import mask
                            
                            # 打开影像文件
                            with rasterio.open(image_path) as src:
                                # 获取影像的坐标系统
                                raster_crs = src.crs
                                log_cb(f"  影像坐标系统: {raster_crs}")
                                
                                # 检查影像是否有坐标系统
                                if raster_crs is None:
                                    log_cb(f"  警告: 影像 {image_name} 没有坐标系统信息，跳过")
                                    continue
                                
                                # 获取影像边界框
                                raster_bounds = src.bounds
                                raster_bbox = box(*raster_bounds)
                                log_cb(f"  影像边界: {raster_bounds}")
                                
                                # 创建临时GeoDataFrame用于坐标转换
                                temp_gdf = gpd.GeoDataFrame([row], crs=gdf.crs)
                                
                                # 转换矢量数据到影像的坐标系统
                                try:
                                    temp_gdf = temp_gdf.to_crs(raster_crs)
                                    geometry = temp_gdf.iloc[0]['geometry']
                                    log_cb(f"  成功转换矢量数据到影像坐标系统: {raster_crs}")
                                except Exception as crs_error:
                                    log_cb(f"  错误: 坐标系统转换失败: {str(crs_error)}")
                                    log_cb(f"  尝试使用通用坐标系统EPSG:4326进行转换...")
                                    # 尝试使用EPSG:4326作为中间转换
                                    try:
                                        temp_gdf_wgs84 = temp_gdf.to_crs("EPSG:4326")
                                        temp_gdf = temp_gdf_wgs84.to_crs(raster_crs)
                                        geometry = temp_gdf.iloc[0]['geometry']
                                        log_cb(f"  成功通过EPSG:4326中间转换")
                                    except Exception as intermediate_error:
                                        log_cb(f"  错误: 中间转换也失败: {str(intermediate_error)}")
                                        continue
                                
                                # 检查几何形状是否有效
                                if not geometry.is_valid:
                                    log_cb(f"  警告: 几何形状无效，正在修复...")
                                    geometry = geometry.buffer(0)
                                    if not geometry.is_valid:
                                        log_cb(f"  错误: 几何形状修复失败")
                                        continue
                                
                                # 获取转换后的矢量边界框
                                vector_bounds = geometry.bounds
                                vector_bbox = box(*vector_bounds)
                                log_cb(f"  矢量边界: {vector_bounds}")
                                
                                # 检查矢量和影像是否空间重叠
                                if not raster_bbox.intersects(vector_bbox):
                                    log_cb(f"  警告: {xzqmc} 区域与 {image_name} 影像不重叠，跳过")
                                    continue
                                
                                # 计算重叠度
                                intersection_area = raster_bbox.intersection(vector_bbox).area
                                vector_area = vector_bbox.area
                                overlap_ratio = intersection_area / vector_area if vector_area > 0 else 0
                                log_cb(f"  重叠比例: {overlap_ratio:.4f}")
                                
                                # 尝试裁剪，使用all_touched=True提高成功率
                                try:
                                    out_image, out_transform = mask(
                                        src, 
                                        [mapping(geometry)], 
                                        crop=True, 
                                        all_touched=True,
                                        filled=True,
                                        nodata=src.nodata if src.nodata is not None else 0
                                    )
                                    
                                    # 更新元数据
                                    out_meta = src.meta.copy()
                                    out_meta.update({
                                        "driver": "GTiff",
                                        "height": out_image.shape[1],
                                        "width": out_image.shape[2],
                                        "transform": out_transform
                                    })
                                    
                                    # 检查裁剪后是否有有效数据
                                    if out_image.size == 0 or (out_meta.get('nodata') is not None and np.all(out_image == out_meta['nodata'])):
                                        log_cb(f"  警告: {xzqmc} 区域与 {image_name} 影像不重叠，跳过")
                                        continue
                                    
                                    # 保存裁剪后的影像
                                    with rasterio.open(output_path, "w", **out_meta) as dest:
                                        dest.write(out_image)
                                    
                                    log_cb(f"  成功: 裁剪完成并保存到 {output_path}")
                                    
                                except Exception as mask_error:
                                    log_cb(f"  错误: 裁剪过程失败: {str(mask_error)}")
                                    # 尝试使用简化的几何形状
                                    try:
                                        log_cb(f"  尝试使用简化的几何形状进行裁剪...")
                                        simplified_geom = geometry.simplify(tolerance=0.01)
                                        out_image, out_transform = mask(
                                            src, 
                                            [mapping(simplified_geom)], 
                                            crop=True, 
                                            all_touched=True
                                        )
                                        
                                        # 保存简化后的裁剪结果
                                        out_meta = src.meta.copy()
                                        out_meta.update({
                                            "driver": "GTiff",
                                            "height": out_image.shape[1],
                                            "width": out_image.shape[2],
                                            "transform": out_transform
                                        })
                                        
                                        with rasterio.open(output_path, "w", **out_meta) as dest:
                                            dest.write(out_image)
                                        
                                        log_cb(f"  成功: 使用简化几何形状裁剪并保存到 {output_path}")
                                        
                                    except Exception as simplified_error:
                                        log_cb(f"  错误: 简化几何形状裁剪也失败: {str(simplified_error)}")
                                        continue
                                
                        except Exception as e:
                            log_cb(f"  错误: 处理 {image_name} 时出错: {str(e)}")
                            # 继续处理下一个影像文件
                            continue
                
                log_cb("\n影像裁剪完成！")
                QTimer.singleShot(0, lambda: QMessageBox.information(self, '成功', '影像裁剪按行政区域分类完成！'))
                
            except Exception as e:
                tb = traceback.format_exc()
                logging.error(f"影像裁剪按行政区域分类异常: {e}\n{tb}")
                QTimer.singleShot(0, lambda: QMessageBox.critical(self, '错误', f'裁剪失败: {e}\n\n{tb}'))
            finally:
                self.progress.hide()
                self.log_text.hide()
                if self.stateTooltip:
                    try:
                        self.stateTooltip.close()
                        self.stateTooltip = None
                    except RuntimeError:
                        pass
                self._running = False
        
        thread = threading.Thread(target=run_crop)
        thread.daemon = True
        thread.start()