# coding:utf-8
"""
数据叠加套合占比功能
"""

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QFileDialog
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from qfluentwidgets import LineEdit, ComboBox, PushButton
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction
import geopandas as gpd
import os
import sys


class DataOverlayThread(QThread):
    """数据叠加套合线程"""
    
    success = pyqtSignal(str)  # 成功信号，传递结果信息
    error = pyqtSignal(str)    # 错误信号，传递错误信息
    
    def __init__(self, path1, path2, field1, field2, parent=None):
        """
        Args:
            path1: 主矢量文件路径
            path2: 叠加矢量文件路径
            field1: 主矢量字段
            field2: 叠加矢量字段
        """
        super().__init__(parent)
        self.path1 = path1
        self.path2 = path2
        self.field1 = field1
        self.field2 = field2
    
    def run(self):
        """线程运行方法"""
        try:
            # 实现数据套合占比功能
            import geopandas as gpd
            import pandas as pd
            import os
            from datetime import datetime
            
            # 读取矢量数据
            gdf1 = gpd.read_file(self.path1)
            gdf2 = gpd.read_file(self.path2)
            
            # 确保坐标系一致
            if gdf1.crs != gdf2.crs:
                gdf2 = gdf2.to_crs(gdf1.crs)
            
            # 计算主矢量要素的面积
            gdf1['主面积'] = gdf1.geometry.area
            
            # 执行空间连接，获取相交的要素
            joined = gpd.sjoin(gdf1, gdf2, how='left', predicate='intersects')
            
            # 保存原始索引，用于后续合并
            joined['原始索引'] = joined.index
            
            # 计算相交面积
            # 创建空间连接结果，包含几何信息
            spatial_join = gpd.overlay(gdf1, gdf2, how='intersection', keep_geom_type=False)
            
            # 计算相交部分的面积
            spatial_join['相交面积'] = spatial_join.geometry.area
            
            # 按主矢量字段和叠加矢量字段分组，计算叠加数据、总面积和唯一值
            def aggregate_data(group):
                # 获取唯一的叠加字段值，用逗号分隔
                unique_values = group[self.field2].unique()
                dj_data = ','.join(str(v) for v in unique_values if pd.notna(v))
                
                # 计算总相交面积
                total_area = group['相交面积'].sum()
                
                return pd.Series({
                    'DJSJ': dj_data,
                    '叠加面积': total_area
                })
            
            # 对空间连接结果进行聚合
            spatial_agg = spatial_join.groupby([self.field1]).apply(aggregate_data).reset_index()
            
            # 合并主矢量数据和空间聚合结果
            merged = gdf1.merge(spatial_agg, on=self.field1, how='left')
            
            # 计算叠加比例
            merged['叠加比例'] = merged['叠加面积'] / merged['主面积']
            merged['叠加比例'] = merged['叠加比例'].fillna(0)  # 填充空值为0
            
            # 处理没有叠加数据的情况
            merged['DJSJ'] = merged['DJSJ'].fillna('')
            merged['叠加面积'] = merged['叠加面积'].fillna(0)
            
            # 移除临时字段
            if '主面积' in merged.columns:
                merged = merged.drop(columns=['主面积'])
            
            # 生成Excel文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_path = os.path.join(os.path.dirname(self.path1), f'套合分析结果_{timestamp}.xlsx')
            
            # 准备Excel数据
            excel_data = merged.copy()
            if 'geometry' in excel_data.columns:
                excel_data = excel_data.drop(columns=['geometry'])
            excel_data.to_excel(excel_path, index=False)
            
            # 生成SHP文件
            output_path = os.path.join(os.path.dirname(self.path1), f'叠加分析结果_{os.path.basename(self.path1)}')
            if not output_path.endswith('.shp'):
                output_path += '.shp'
            merged.to_file(output_path, encoding='utf-8')
            
            # 生成TXT文件
            txt_path = output_path[:-4] + '.txt'
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write("数据套合占比分析结果\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"主矢量文件: {self.path1}\n")
                f.write(f"叠加矢量文件: {self.path2}\n")
                f.write(f"主矢量字段: {self.field1}\n")
                f.write(f"叠加矢量字段: {self.field2}\n")
                f.write("\n字段说明:\n")
                f.write("- DJSJ: 叠加数据，包含所有相交的叠加矢量字段值，用逗号分隔\n")
                f.write("- 叠加面积: 主矢量要素与叠加矢量要素的相交面积总和\n")
                f.write("- 叠加比例: 叠加面积与主矢量要素面积的比值\n\n")
                f.write("统计结果:\n")
                f.write(merged[[self.field1, 'DJSJ', '叠加面积', '叠加比例']].to_string(index=False))
            
            result_msg = (
                f"分析完成！\n\n"
                f"SHP文件：{output_path}\n"
                f"TXT文件：{txt_path}\n"
                f"Excel文件：{excel_path}\n\n"
                f"已添加字段：\n"
                f"- DJSJ: 叠加数据，包含所有相交的叠加矢量字段值\n"
                f"- 叠加面积: 相交面积总和\n"
                f"- 叠加比例: 叠加面积与主矢量面积的比值"
            )
            
            self.success.emit(result_msg)
            
        except Exception as e:
            self.error.emit(f"分析失败: {str(e)}")


class DataOverlayFunction(BaseFunction):
    """数据叠加套合占比功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>"
            "1. 计算两个矢量数据集的套合占比情况<br>"
            "2. 选择主矢量文件和叠加矢量文件<br>"
            "3. 选择对应的字段进行分析<br>"
            "4. 输出SHP、TXT和Excel分析报告"
        )
        super().__init__("数据叠加套合占比", description, parent)
        
        # 初始化UI
        self._initUI()
        
        # 添加执行按钮
        self.addExecuteButton("开始分析", self.execute)
    
    def _initUI(self):
        """初始化界面"""
        # 主矢量文件行
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("主矢量文件："))
        
        self.mainVectorBtn = PushButton("选择文件", self, FIF.DOCUMENT)
        self.mainVectorBtn.clicked.connect(self._selectMainVector)
        self.mainVectorBtn.setFixedWidth(120)  # 增加宽度以完整显示文字
        
        self.mainVectorPath = LineEdit(self)
        self.mainVectorPath.setPlaceholderText("点击按钮选择主矢量文件")
        self.mainVectorPath.setReadOnly(True)
        
        self.mainVectorField = ComboBox(self)
        self.mainVectorField.setPlaceholderText("选择字段")
        self.mainVectorField.setFixedWidth(150)
        
        row1.addWidget(self.mainVectorBtn)
        row1.addWidget(self.mainVectorPath, 1)
        row1.addWidget(self.mainVectorField)
        self.contentLayout.addLayout(row1)
        
        # 叠加矢量文件行
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("叠加矢量文件："))
        
        self.overlayVectorBtn = PushButton("选择文件", self, FIF.DOCUMENT)
        self.overlayVectorBtn.clicked.connect(self._selectOverlayVector)
        self.overlayVectorBtn.setFixedWidth(120)  # 增加宽度以完整显示文字
        
        self.overlayVectorPath = LineEdit(self)
        self.overlayVectorPath.setPlaceholderText("点击按钮选择叠加矢量文件")
        self.overlayVectorPath.setReadOnly(True)
        
        self.overlayVectorField = ComboBox(self)
        self.overlayVectorField.setPlaceholderText("选择字段")
        self.overlayVectorField.setFixedWidth(150)
        
        row2.addWidget(self.overlayVectorBtn)
        row2.addWidget(self.overlayVectorPath, 1)
        row2.addWidget(self.overlayVectorField)
        self.contentLayout.addLayout(row2)
    
    def _selectMainVector(self):
        """选择主矢量文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择主矢量文件", "", "SHP文件 (*.shp)"
        )
        if file_path:
            self.mainVectorPath.setText(file_path)
            self._loadFields(file_path, self.mainVectorField)
    
    def _selectOverlayVector(self):
        """选择叠加矢量文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择叠加矢量文件", "", "SHP文件 (*.shp)"
        )
        if file_path:
            self.overlayVectorPath.setText(file_path)
            self._loadFields(file_path, self.overlayVectorField)
    
    def _loadFields(self, file_path, combo_box):
        """加载字段列表"""
        try:
            gdf = gpd.read_file(file_path)
            fields = [col for col in gdf.columns if col != 'geometry']
            combo_box.clear()
            combo_box.addItems(fields)
        except Exception as e:
            self.showError(f"读取字段失败: {str(e)}")
    
    def validate(self) -> tuple[bool, str]:
        """验证输入"""
        if not self.mainVectorPath.text():
            return False, "请选择主矢量文件"
        if not self.overlayVectorPath.text():
            return False, "请选择叠加矢量文件"
        if not self.mainVectorField.currentText():
            return False, "请选择主矢量字段"
        if not self.overlayVectorField.currentText():
            return False, "请选择叠加矢量字段"
        return True, ""
    
    def execute(self):
        """执行分析"""
        # 验证输入
        valid, message = self.validate()
        if not valid:
            self.showError(message)
            return
        
        # 显示进度
        self.showProgress("正在分析数据...")
        
        # 创建并启动数据叠加套合线程
        self.overlay_thread = DataOverlayThread(
            path1=self.mainVectorPath.text(),
            path2=self.overlayVectorPath.text(),
            field1=self.mainVectorField.currentText(),
            field2=self.overlayVectorField.currentText(),
            parent=self
        )
        
        # 连接信号
        self.overlay_thread.success.connect(self._onOverlaySuccess)
        self.overlay_thread.error.connect(self._onOverlayError)
        self.overlay_thread.finished.connect(self._onOverlayFinished)
        
        # 启动线程
        self.overlay_thread.start()
    
    def _onOverlaySuccess(self, message: str):
        """叠加分析成功处理"""
        self.showSuccess(message)
    
    def _onOverlayError(self, message: str):
        """叠加分析错误处理"""
        self.showError(message)
    
    def _onOverlayFinished(self):
        """叠加分析线程结束处理"""
        self.hideProgress()
