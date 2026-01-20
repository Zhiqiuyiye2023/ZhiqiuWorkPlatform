import os
import fiona
import geopandas as gpd
import pandas as pd
from collections import defaultdict
import threading
import glob
from openpyxl import load_workbook
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget,
    QFileDialog, QGroupBox, QFrame, QProgressBar
)
from qfluentwidgets import (
    LineEdit, PushButton, PrimaryPushButton, MessageBox, ListWidget,
    IndeterminateProgressBar, SmoothScrollArea, ComboBox
)
from qfluentwidgets.common.icon import FluentIcon as FIF

from .base_function import BaseFunction


class GDBMergerWorker(QThread):
    """GDB合并工作线程"""
    progress_updated = pyqtSignal(int)
    message_updated = pyqtSignal(str)
    finished = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, base_path, output_folder_name, source_folders):
        super().__init__()
        self.base_path = base_path
        self.output_folder_name = output_folder_name
        self.source_folders = source_folders
        self.is_running = True
        self.failed_layers = []  # 记录未能成功合并的图层和原因

    def run(self):
        """执行合并操作"""
        try:
            # 创建输出文件夹路径
            output_base_path = os.path.join(self.base_path, self.output_folder_name)
            os.makedirs(output_base_path, exist_ok=True)
            
            if not self.is_running:
                return
            
            # 按GDB类型进行合并
            unique_gdb_types = set()
            for gdb_path in self.source_folders:
                gdb_basename = os.path.basename(gdb_path)
                unique_gdb_types.add(gdb_basename)
            
            gdb_types = sorted(list(unique_gdb_types))
            total_gdb_types = len(gdb_types)
            
            for i, gdb_type in enumerate(gdb_types):
                if not self.is_running:
                    break
                
                progress = int((i / total_gdb_types) * 100)
                self.progress_updated.emit(progress)
                
                # 为每个GDB类型收集所有来源的同类型GDB
                source_gdb_paths_for_type = []
                for gdb_path in self.source_folders:
                    if gdb_type == os.path.basename(gdb_path):
                        source_gdb_paths_for_type.append(gdb_path)
                
                if source_gdb_paths_for_type:
                    # 输出GDB路径
                    output_gdb_path = os.path.join(output_base_path, gdb_type)
                    
                    # 获取所有图层名称
                    all_layers = set()
                    for gdb_path in source_gdb_paths_for_type:
                        try:
                            layers = fiona.listlayers(gdb_path)
                            all_layers.update(layers)
                        except Exception as e:
                            continue
                    
                    # 为每个图层进行合并
                    for layer_name in all_layers:
                        if not self.is_running:
                            break
                        
                        # 收集所有来源GDB中该图层的数据
                        layer_source_gdb_paths = []
                        for gdb_path in source_gdb_paths_for_type:
                            try:
                                layers = fiona.listlayers(gdb_path)
                                if layer_name in layers:
                                    layer_source_gdb_paths.append(gdb_path)
                            except Exception as e:
                                continue
                        
                        if layer_source_gdb_paths:
                            self.merge_gdb_layers(layer_source_gdb_paths, layer_name, output_gdb_path)
            
            if self.is_running:
                self.progress_updated.emit(100)
                self.finished.emit(self.failed_layers)
                
        except Exception as e:
            if self.is_running:
                self.error_occurred.emit(str(e))

    def merge_gdb_layers(self, source_gdb_paths, layer_name, output_gdb_path):
        """合并多个GDB中相同图层的数据"""
        all_gdfs = []
        failed_reasons = []
        
        # 收集所有GDB中指定图层的数据
        for gdb_path in source_gdb_paths:
            try:
                gdf = gpd.read_file(gdb_path, layer=layer_name)
                all_gdfs.append(gdf)
            except Exception as e:
                failed_reasons.append(f"读取 {gdb_path} 时出错: {str(e)}")
        
        if not all_gdfs:
            if failed_reasons:
                self.failed_layers.append((layer_name, "".join(failed_reasons)))
            return
        
        # 检测坐标系一致性
        crs_set = set()
        for gdf in all_gdfs:
            if gdf.crs is not None:
                crs_set.add(str(gdf.crs))
        
        if len(crs_set) > 1:
            self.failed_layers.append((layer_name, f"坐标系不一致: {', '.join(crs_set)}"))
            return
        
        # 合并所有GeoDataFrames
        try:
            merged_gdf = self.merge_dataframes(all_gdfs)
        except Exception as e:
            self.failed_layers.append((layer_name, f"合并失败: {str(e)}"))
            return
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_gdb_path), exist_ok=True)
        
        # 写入合并后的数据到输出文件
        try:
            # 尝试直接写入GDB格式
            merged_gdf.to_file(output_gdb_path, layer=layer_name, driver="OpenFileGDB")
        except Exception as e:
            # 尝试使用GPKG格式作为备选
            try:
                output_gpkg_path = output_gdb_path.replace('.gdb', '_merged.gpkg')
                merged_gdf.to_file(output_gpkg_path, layer=layer_name, driver="GPKG")
            except Exception as e2:
                # 如果所有方法都失败，保存为Shapefile
                try:
                    output_shp = output_gdb_path.replace('.gdb', f'_{layer_name}.shp')
                    output_dir = os.path.dirname(output_shp)
                    if output_dir == '':
                        output_shp = f'_{layer_name}.shp'
                    else:
                        os.makedirs(output_dir, exist_ok=True)
                    merged_gdf.to_file(output_shp)
                except Exception as e3:
                    self.failed_layers.append((layer_name, f"写入失败: {str(e3)}"))

    def merge_dataframes(self, gdfs):
        """合并多个GeoDataFrames"""
        if not gdfs:
            return gpd.GeoDataFrame()
        
        if len(gdfs) == 1:
            return gdfs[0].copy()
        
        # 获取所有唯一字段名
        all_columns = []
        seen_columns = set()
        
        first_gdf_columns = gdfs[0].columns.tolist()
        all_columns.extend(first_gdf_columns)
        seen_columns.update(first_gdf_columns)
        
        for gdf in gdfs[1:]:
            for col in gdf.columns.tolist():
                if col not in seen_columns:
                    all_columns.append(col)
                    seen_columns.add(col)
        
        # 统一CRS
        target_crs = None
        for gdf in gdfs:
            if gdf.crs is not None:
                target_crs = gdf.crs
                break
        
        # 对齐所有GeoDataFrame
        aligned_gdfs = []
        for i, gdf in enumerate(gdfs):
            new_data = {}
            
            for col in all_columns:
                if col in gdf.columns:
                    new_data[col] = gdf[col].copy()
                else:
                    new_data[col] = pd.Series([None] * len(gdf), index=gdf.index, dtype=object)
            
            aligned_gdf = gpd.GeoDataFrame(new_data)
            
            # 统一CRS
            if target_crs is not None and aligned_gdf.crs is not None:
                if str(aligned_gdf.crs) != str(target_crs):
                    try:
                        aligned_gdf = aligned_gdf.to_crs(target_crs)
                    except Exception as e:
                        pass
            elif target_crs is not None and aligned_gdf.crs is None:
                aligned_gdf.crs = target_crs
            
            aligned_gdf.index = range(i * len(aligned_gdf), (i + 1) * len(aligned_gdf))
            aligned_gdfs.append(aligned_gdf)
        
        if aligned_gdfs:
            merged_gdf = pd.concat(aligned_gdfs, ignore_index=True, sort=False)
            
            if 'geometry' in merged_gdf.columns:
                merged_gdf = merged_gdf.reset_index(drop=True)
                merged_gdf = gpd.GeoDataFrame(merged_gdf, geometry='geometry', crs=target_crs)
                
                # 清理可能引起冲突的字段
                columns_to_drop = []
                for col in merged_gdf.columns:
                    if col.lower() in ['objectid', 'fid'] or col.startswith('fid_') or col.startswith('objectid_'):
                        columns_to_drop.append(col)
                
                if columns_to_drop:
                    merged_gdf = merged_gdf.drop(columns=columns_to_drop)
            else:
                merged_gdf = gpd.GeoDataFrame(merged_gdf)
        else:
            merged_gdf = gpd.GeoDataFrame()
        
        return merged_gdf

    def stop(self):
        """停止合并操作"""
        self.is_running = False


class GDBMergerFunction(BaseFunction):
    """GDB合并功能"""
    def __init__(self, parent=None):
        super().__init__("GDB合并", "GDB文件合并与处理", parent)
        self.gdb_files = []
        self.worker = None
        self.setup_ui()

    def setup_ui(self):
        """设置UI界面"""
        # 基础路径设置
        base_group = QGroupBox("GDB文件设置")
        base_layout = QVBoxLayout(base_group)
        base_layout.setSpacing(15)
        base_layout.setContentsMargins(20, 20, 20, 20)
        
        # 基础路径选择
        path_layout = QHBoxLayout()
        path_label = QLabel("基础路径:")
        self.base_path_edit = LineEdit()
        self.base_path_edit.setPlaceholderText("请选择基础路径")
        browse_btn = PushButton("浏览")
        browse_btn.setFixedWidth(120)
        browse_btn.clicked.connect(self.browse_base_path)
        
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.base_path_edit, 1)
        path_layout.addWidget(browse_btn)
        base_layout.addLayout(path_layout)
        
        # 输出文件夹名称
        output_layout = QHBoxLayout()
        output_label = QLabel("输出文件夹:")
        self.output_folder_edit = LineEdit()
        self.output_folder_edit.setText("合并结果")
        
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_folder_edit, 1)
        base_layout.addLayout(output_layout)
        
        # 添加到内容布局
        self.contentLayout.addWidget(base_group)
        
        # GDB文件列表区域
        gdb_group = QGroupBox("GDB文件列表")
        gdb_layout = QVBoxLayout(gdb_group)
        gdb_layout.setSpacing(15)
        gdb_layout.setContentsMargins(20, 20, 20, 20)
        
        # GDB文件列表
        self.gdb_list = ListWidget()
        self.gdb_list.setAcceptDrops(True)
        self.gdb_list.setDragEnabled(True)
        self.gdb_list.dragEnterEvent = self.dragEnterEvent
        self.gdb_list.dropEvent = self.dropEvent
        self.gdb_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        gdb_layout.addWidget(self.gdb_list)
        
        # 添加到内容布局
        self.contentLayout.addWidget(gdb_group)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.contentLayout.addWidget(self.progress_bar)
        
        # 列表操作按钮添加到基类提供的按钮布局
        delete_btn = PushButton("删除选中")
        delete_btn.setFixedWidth(120)
        delete_btn.clicked.connect(self.delete_selected_gdb)
        self.buttonLayout.addWidget(delete_btn)
        
        clear_btn = PushButton("清除列表")
        clear_btn.setFixedWidth(120)
        clear_btn.clicked.connect(self.clear_gdb_list)
        self.buttonLayout.addWidget(clear_btn)
        
        # 合并和取消按钮添加到基类提供的按钮布局
        self.merge_button = PrimaryPushButton("开始合并")
        self.merge_button.clicked.connect(self.start_merge)
        self.buttonLayout.addWidget(self.merge_button)
        
        self.cancel_button = PushButton("取消")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_operation)
        self.buttonLayout.addWidget(self.cancel_button)
        
        # 添加弹性空间
        self.buttonLayout.addStretch(1)

    def browse_base_path(self):
        """浏览并选择基础路径，自动检测GDB文件"""
        path = QFileDialog.getExistingDirectory(self, "选择基础路径")
        if path:
            self.base_path_edit.setText(path)
            self.detect_gdb_files(path)

    def detect_gdb_files(self, base_path):
        """自动检测指定路径下的GDB文件"""
        self.gdb_files.clear()
        
        # 递归查找所有GDB文件
        for root, dirs, files in os.walk(base_path):
            for dir_name in dirs:
                if dir_name.lower().endswith('.gdb'):
                    gdb_path = os.path.join(root, dir_name)
                    self.gdb_files.append(gdb_path)
        
        self.update_gdb_list()

    def update_gdb_list(self):
        """更新GDB文件列表"""
        self.gdb_list.clear()
        for gdb_file in self.gdb_files:
            self.gdb_list.addItem(gdb_file)

    def dragEnterEvent(self, event):
        """拖拽进入事件处理"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """拖拽释放事件处理"""
        for url in event.mimeData().urls():
            gdb_path = url.toLocalFile()
            if gdb_path.lower().endswith('.gdb') and gdb_path not in self.gdb_files:
                self.gdb_files.append(gdb_path)
        
        self.update_gdb_list()

    def delete_selected_gdb(self):
        """删除选中的GDB文件"""
        selected_items = self.gdb_list.selectedItems()
        if not selected_items:
            return
        
        for item in selected_items:
            gdb_path = item.text()
            if gdb_path in self.gdb_files:
                self.gdb_files.remove(gdb_path)
        
        self.update_gdb_list()

    def clear_gdb_list(self):
        """清除GDB文件列表"""
        self.gdb_files.clear()
        self.update_gdb_list()



    def start_merge(self):
        """开始合并操作"""
        if not self.gdb_files:
            msg_box = MessageBox("错误", "请至少选择一个GDB文件", self)
            msg_box.exec()
            return
        
        self.merge_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 创建并启动工作线程
        base_path = self.base_path_edit.text()
        output_folder_name = self.output_folder_edit.text()
        
        self.worker = GDBMergerWorker(base_path, output_folder_name, self.gdb_files)
        self.worker.progress_updated.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self.merge_completed)
        self.worker.error_occurred.connect(self.merge_error)
        self.worker.start()

    def cancel_operation(self):
        """取消合并操作"""
        if self.worker:
            self.worker.stop()
            self.worker.wait()
        self.operation_completed()

    def merge_completed(self, failed_layers=None):
        """合并操作完成"""
        self.operation_completed()
        
        # 显示合并结果弹窗
        if failed_layers and len(failed_layers) > 0:
            # 有失败的图层，显示详细信息
            message = "GDB合并操作已完成，但部分图层未能成功合并：\n\n"
            for layer_name, reason in failed_layers:
                message += f"- {layer_name}: {reason}\n"
            
            msg_box = MessageBox("合并完成", message, self)
            msg_box.exec()
        else:
            # 所有图层都成功合并
            msg_box = MessageBox("成功", "GDB合并操作已完成！", self)
            msg_box.exec()

    def merge_error(self, error):
        """合并操作出错"""
        msg_box = MessageBox("错误", f"合并操作过程中出现错误: {error}", self)
        msg_box.exec()
        self.operation_completed()

    def operation_completed(self):
        """操作完成后的处理"""
        self.merge_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.progress_bar.setValue(100)
        self.progress_bar.setVisible(False)
        self.worker = None


class GDBMergerFunctionWrapper:
    """GDB合并功能包装器"""
    def __init__(self):
        self.function = None

    def create_function(self, parent=None):
        """创建GDB合并功能实例"""
        self.function = GDBMergerFunction(parent)
        return self.function

    def get_function(self):
        """获取GDB合并功能实例"""
        return self.function

    def resize_function(self, size):
        """调整功能实例大小"""
        if self.function:
            self.function.resize(size)
