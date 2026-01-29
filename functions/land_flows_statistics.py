# coding:utf-8
"""
耕园林流向一览表功能
用于统计GDB文件中耕地、林地、园地的流向情况
"""

from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QFileDialog
from PyQt6.QtCore import Qt
from qfluentwidgets import LineEdit, ComboBox, PushButton, TextEdit
from qfluentwidgets import FluentIcon as FIF
from .base_function import BaseFunction
import threading
import geopandas as gpd
import pandas as pd
import os
import datetime
from openpyxl import Workbook
from openpyxl.styles import Border, Side, Alignment
from openpyxl.utils.dataframe import dataframe_to_rows


# 代码值与描述的映射字典
code_description_map = {
    '1111': '建设用地审批备案内的',
    '1112': '设施农用地审批备案内的',
    '112': '符合政策的退耕还林范围内的;',
    '113': '属于毁林开垦等违法情形或者依法审批临时使用林地、林业直服设施占用林地及采伐更新形成的；',
    '1141': '非农化流出（坑塘、道路、设施农用地等）',
    '1142': '非粮化流出',
    '1143': '其他不纳入管理的耕地(矿权和碎面)',
    '1144': '位于城镇开发边界内，需要扣除的',
    '115': '位于河湖（库）管理范围内，经核实，属于法律法规、规范性文件禁止（限制）开垦或影响河湖（库）行（蓄）洪安全及水库安全的',
    '116': '其他自主扣除',
    '117': '重大项目扣除',
    '2101': '建设用地审批内',
    '2102': '设施农用地审批范围内',
    '2103': '河湖范围内',
    '2104': '林地流出部分',
    '2105': '依法建设项目永久占用林地',
    '2106': '其他自主扣除',
    '2107': '重大项目扣除',
    '3101': '建设用地审批内',
    '3102': '设施农用地审批范围内',
    '3103': '河湖范围内',
    '3104': '园地流出部分',
    '3105': '其他自主扣除',
    '3106': '重大项目扣除',
    '11': '现状耕地扣除耕地扣除项后，保留的耕地',
    '121': '耕地上以棚架等方式种植食用菌菇木耳等蔬菜、未直接利用耕作层且耕作层未破坏的；',
    '1221': '耕地上种植三七、人参、西洋参等中药材',
    '1222': '浅根系或藤本类水果及花卉',
    '123': '经核实，实地恢复耕种且具备耕作条件的',
    '124': '耕作层较好且具有粮食产能的林（园）与粮棉油糖菜等农作物套种间种的复合用地。',
    '125': '自然撂荒成林标注未耕',
    '1311': '临时种植且不破坏耕作层或轻度破坏耕作层的果树、茶树、苗木等土地',
    '1312': '未耕成林耕作层未破坏的',
    '2111': '生态保护红线范围内的',
    '2112': '自然保护地范围内的',
    '2121': '天然林范围内的',
    '2122': '公益林范围内的',
    '2123': '国有林范围内的',
    '213': '符合政策的退耕还林范围内的；',
    '214': '坡度25°以上的',
    '215': '原森林资源“一张图”范围内且与农村土地承包经营权不冲突的。',
    '216': '其他重点园区、储备林、造林空间范围内的林地等',
    '217': '上述范围外保留的林地',
    '221': '符合政策的退耕还林范围内的；',
    '222': '种植油茶、油橄榄、文冠果、油棕等木本油料的；',
    '223': '种植橡胶、油桐、杜仲、厚朴、银杏、黄柏、乌桕、棕榈、白蜡树、栓皮栎等工业原料的；',
    '224': '种植核桃、板栗等干果经济林木的；',
    '231': '耕地管理边界、耕地后备资源空间范围外，属于毁林开垦等违法情形或者依法审批临时使用林地、林业直服设施占用林地及采伐更新形成的现状耕地，尊重群众意愿，逐步恢复为林地。',
    '24': '可纳入也可不纳入的（如饮用水源地内的林地）',
    '30': '园地保留一批',
    '40': '耕地后备资源',
    '50': '国土绿化空间',
    '141': '坡度25°以上的（不含梯田梯地）；',
    '142': '生态保护红线、自然保护地、饮用水水源一级保护区范围内的；',
    '143': '图斑破碎、零星分散不便于耕种的。',
    '144': '历年耕地为0404，0305，0307的。',
    '34': '林地置换'
}

# 代码值与类别的映射字典
code_category_map = {
    # 耕地扣除项
    '1111': '耕地扣除项',
    '1112': '耕地扣除项',
    '112': '耕地扣除项',
    '113': '耕地扣除项',
    '1141': '耕地扣除项',
    '1142': '耕地扣除项',
    '1143': '耕地扣除项',
    '1144': '耕地扣除项',
    '115': '耕地扣除项',
    '116': '耕地扣除项',
    '117': '耕地扣除项',
    # 林地扣除项
    '2101': '林地扣除项',
    '2102': '林地扣除项',
    '2103': '林地扣除项',
    '2104': '林地扣除项',
    '2105': '林地扣除项',
    '2106': '林地扣除项',
    '2107': '林地扣除项',
    # 园地扣除项
    '3101': '园地扣除项',
    '3102': '园地扣除项',
    '3103': '园地扣除项',
    '3104': '园地扣除项',
    '3105': '园地扣除项',
    '3106': '园地扣除项',
    # 耕地保留一批
    '11': '耕地保留一批(11)',
    # 耕地认定一批
    '121': '耕地认定一批(12)',
    '1221': '耕地认定一批(12)',
    '1222': '耕地认定一批(12)',
    '123': '耕地认定一批(12)',
    '124': '耕地认定一批(12)',
    '125': '耕地认定一批(12)',
    # 耕地恢复一批
    '1311': '耕地恢复一批(13)',
    '1312': '耕地恢复一批(13)',
    # 林地保留一批
    '2111': '林地保留一批(21)',
    '2112': '林地保留一批(21)',
    '2121': '林地保留一批(21)',
    '2122': '林地保留一批(21)',
    '2123': '林地保留一批(21)',
    '213': '林地保留一批(21)',
    '214': '林地保留一批(21)',
    '215': '林地保留一批(21)',
    '216': '林地保留一批(21)',
    '217': '林地保留一批(21)',
    # 林地认定一批
    '221': '林地认定一批(22)',
    '222': '林地认定一批(22)',
    '223': '林地认定一批(22)',
    '224': '林地认定一批(22)',
    # 林地恢复一批
    '231': '林地恢复一批(23)',
    # 可纳入林地管理
    '24': '可纳入林地管理(24)',
    # 园地保留一批
    '30': '园地保留一批',
    # 其他类别
    '40': '耕地后备资源',
    '50': '国土绿化空间',
    # 耕地置换原因
    '141': '耕地置换原因',
    '142': '耕地置换原因',
    '143': '耕地置换原因',
    '144': '耕地置换原因',
    # 林地置换原因
    '34': '林地置换原因'
}

# 坡度级别描述
pdjb_description = {
    '1': '坡度≤2°',
    '2': '2°<坡度≤6°',
    '3': '6°<坡度≤15°',
    '4': '15°<坡度≤25°',
    '5': '坡度>25°'
}

# 定义保留2位小数的函数
def round_to_2(value):
    if pd.isna(value):
        return 0
    try:
        return round(float(value), 2)
    except:
        return 0


class LandFlowsStatisticsFunction(BaseFunction):
    """耕园林流向一览表功能"""
    
    def __init__(self, parent=None):
        description = "📢 功能说明："
        super().__init__("耕林园流向统计", description, parent)
        
        # 初始化UI
        self._initUI()
        
        # 添加执行按钮
        self.addExecuteButton("开始执行", self.execute)
    
    def _initUI(self):
        """初始化界面控件"""
        # GDB文件选择行
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("GDB文件："))
        
        self.gdbBtn = PushButton("选择GDB", self, FIF.FOLDER)
        self.gdbBtn.clicked.connect(self._selectGdb)
        
        self.gdbPath = LineEdit(self)
        self.gdbPath.setPlaceholderText("点击按钮选择GDB文件")
        self.gdbPath.setReadOnly(True)
        
        row1.addWidget(self.gdbBtn)
        row1.addWidget(self.gdbPath, 1)  # 1 表示拉伸因子
        self.contentLayout.addLayout(row1)
        
        # 图层名称输入行
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("图层名称："))
        
        self.layerName = LineEdit(self)
        self.layerName.setPlaceholderText("请输入GDB中的图层名称")
        self.layerName.setText("原始成果")  # 设置默认图层名称
        
        row2.addWidget(self.layerName, 1)
        self.contentLayout.addLayout(row2)
        
        # 地类代码字段输入行
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("地类代码字段："))
        
        self.landCodeField = LineEdit(self)
        self.landCodeField.setPlaceholderText("请输入地类代码字段名，默认为TKJ_DLBM")
        self.landCodeField.setText("TKJ_DLBM")  # 设置默认值
        
        row3.addWidget(self.landCodeField, 1)
        self.contentLayout.addLayout(row3)
        
        # 输出文件选择行
        row4 = QHBoxLayout()
        row4.addWidget(QLabel("输出Excel："))
        
        self.outputBtn = PushButton("选择路径", self, FIF.DOCUMENT)
        self.outputBtn.clicked.connect(self._selectOutput)
        
        # 设置默认保存路径
        default_output = os.path.join(os.getcwd(), "耕林园流向表.xlsx")
        self.outputPath = LineEdit(self)
        self.outputPath.setPlaceholderText("点击按钮选择输出路径")
        self.outputPath.setReadOnly(True)
        self.outputPath.setText(default_output)  # 设置默认保存路径
        
        row4.addWidget(self.outputBtn)
        row4.addWidget(self.outputPath, 1)  # 1 表示拉伸因子
        self.contentLayout.addLayout(row4)
    
    def _selectGdb(self):
        """选择GDB文件"""
        file_path = QFileDialog.getExistingDirectory(
            self, 
            "选择GDB文件", 
            "",
        )
        if file_path:
            self.gdbPath.setText(file_path)
    
    def _selectOutput(self):
        """选择输出Excel文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "选择输出Excel文件", 
            "", 
            "Excel文件 (*.xlsx)"
        )
        if file_path:
            self.outputPath.setText(file_path)
    
    def validate(self) -> tuple[bool, str]:
        """
        验证输入参数
        返回: (是否有效, 错误消息)
        """
        # 验证GDB文件
        if not self.gdbPath.text():
            return False, "请选择GDB文件"
        
        if not os.path.exists(self.gdbPath.text()):
            return False, "选择的GDB文件不存在"
        
        # 验证图层名称
        if not self.layerName.text():
            return False, "请输入图层名称"
        
        # 验证输出路径
        if not self.outputPath.text():
            return False, "请选择输出Excel文件路径"
        
        # 所有验证通过
        return True, ""
    
    def calculate_land_category_statistics(self, gdb_path, layer_name, output_excel=None, land_code_field='TKJ_DLBM'):
        """
        统计GDB文件中指定图层的耕地、林地、园地面积，以及这些地类分别对应HSHKCYY、HSHBLYY、HSHZHYY字段值的面积
        并为每个代码值提供对应的描述和类别信息，同时计算扣除系数面积
        
        参数:
        gdb_path: GDB文件路径
        layer_name: 图层名称
        output_excel: 输出Excel文件路径，默认为None
        land_code_field: 地类代码字段名，默认为'TKJ_DLBM'
        
        返回:
        统计结果DataFrame，包含地类、字段、值、描述、类别、面积(平方米)、面积(亩)、面积(万亩)、扣除系数面积(亩)、扣除系数面积(万亩)、图斑数量
        """
        # 检查文件是否存在
        if not os.path.exists(gdb_path):
            self.show_error_signal.emit(f"GDB文件 {gdb_path} 不存在！")
            return None
        
        try:
            # 读取GDB文件中的指定图层
            self.update_progress_signal.emit(0, f"正在读取GDB文件: {gdb_path} 中的图层: {layer_name}")
            gdf = gpd.read_file(gdb_path, layer=layer_name)
            self.update_progress_signal.emit(10, f"成功读取图层，包含 {len(gdf)} 个图斑")
            
            # 显示图层中的所有字段，便于用户确认字段名称
            self.update_progress_signal.emit(20, f"图层中的所有字段: {', '.join(gdf.columns)}")
            
            # 检查地类代码字段是否存在
            if land_code_field not in gdf.columns:
                self.show_error_signal.emit(f"图层中不包含 {land_code_field} 字段！")
                # 尝试显示类似的字段名称
                similar_fields = [col for col in gdf.columns if land_code_field in col or col in land_code_field]
                if similar_fields:
                    self.show_error_signal.emit(f"可能的相似字段: {', '.join(similar_fields)}")
                return None
            
            # 计算面积（平方米）
            # 检查HSHKCYY、HSHBLYY、HSHZHYY、HSHKCXS、HSHPDJB字段是否存在
            required_fields = ['HSHKCYY', 'HSHBLYY', 'HSHZHYY', 'HSHKCXS', 'HSHPDJB']
            missing_fields = [field for field in required_fields if field not in gdf.columns]
            
            if missing_fields:
                self.update_progress_signal.emit(30, f"警告：图层中缺少以下字段: {', '.join(missing_fields)}")
                # 尝试显示类似的字段名称
                for missing in missing_fields:
                    similar_fields = [col for col in gdf.columns if missing in col or col in missing]
                    if similar_fields:
                        self.update_progress_signal.emit(30, f"可能的相似字段 '{missing}': {', '.join(similar_fields)}")
            
            # 确保几何数据是投影坐标系
            if gdf.crs is None or gdf.crs.is_geographic:
                self.update_progress_signal.emit(40, "注意：当前图层使用的是地理坐标系，将转换为投影坐标系进行面积计算")
                # 尝试使用适合中国区域的投影
                try:
                    # 对于中国四川省达州市达川区的数据，可以使用CGCS2000 / 3-degree Gauss-Kruger zone 35
                    # EPSG:4539
                    gdf = gdf.to_crs(epsg=4539)
                except Exception as e:
                    self.update_progress_signal.emit(40, f"坐标系转换出错: {e}")
                    # 尝试备用投影
                    self.update_progress_signal.emit(40, "尝试使用备用投影 EPSG:32648 (WGS 84 / UTM zone 48N)")
                    try:
                        gdf = gdf.to_crs(epsg=32648)
                    except:
                        self.update_progress_signal.emit(40, "警告：无法转换坐标系，面积计算可能不准确！")
            
            # 计算面积（平方米）
            gdf.loc[:, 'area_m2'] = gdf.geometry.area
            
            # 统计耕地、林地、园地面积
            # 耕地：TKJ_DLBM LIKE '01%'
            cultivated_land = gdf[gdf[land_code_field].astype(str).str.startswith('01')].copy()
            cultivated_area_m2 = cultivated_land['area_m2'].sum()
            cultivated_area_mu = cultivated_area_m2 / 666.67
            
            # 园地：TKJ_DLBM LIKE '02%'
            garden_land = gdf[gdf[land_code_field].astype(str).str.startswith('02')].copy()
            garden_area_m2 = garden_land['area_m2'].sum()
            garden_area_mu = garden_area_m2 / 666.67
            
            # 林地：TKJ_DLBM LIKE '03%'
            forest_land = gdf[gdf[land_code_field].astype(str).str.startswith('03')].copy()
            forest_area_m2 = forest_land['area_m2'].sum()
            forest_area_mu = forest_area_m2 / 666.67
            
            # 初始化结果列表
            result_rows = []
            
            # 添加总的耕地统计
            # 计算扣除系数面积
            if 'HSHKCXS' in cultivated_land.columns:
                # 确保HSHKCXS是数值类型
                try:
                    cultivated_land.loc[:, 'HSHKCXS'] = pd.to_numeric(cultivated_land['HSHKCXS'], errors='coerce').fillna(0)
                    cultivated_land.loc[:, 'deducted_area_mu'] = cultivated_land['area_m2'] / 666.67 * (1 - cultivated_land['HSHKCXS'])
                    total_deducted_area_mu = cultivated_land['deducted_area_mu'].sum()
                except:
                    total_deducted_area_mu = 0
            else:
                total_deducted_area_mu = 0
            
            # 计算耕地各坡度级别的面积（万亩）和扣除系数面积（万亩）
            cultivated_slope_areas = {}
            if 'HSHPDJB' in gdf.columns:
                # 先添加所有坡度级别的面积
                for slope_level in ['1', '2', '3', '4', '5']:
                    slope_data = cultivated_land[pd.notna(cultivated_land['HSHPDJB']) & (cultivated_land['HSHPDJB'].astype(str) == slope_level)]
                    slope_area_mu = slope_data['area_m2'].sum() / 666.67
                    cultivated_slope_areas[f'坡度{slope_level}面积(万亩)'] = round_to_2(slope_area_mu / 10000)
                
                # 再添加所有坡度级别的扣除系数面积
                for slope_level in ['1', '2', '3', '4', '5']:
                    slope_data = cultivated_land[pd.notna(cultivated_land['HSHPDJB']) & (cultivated_land['HSHPDJB'].astype(str) == slope_level)]
                    # 计算坡度扣除系数面积
                    if 'HSHKCXS' in slope_data.columns:
                        try:
                            slope_data_copy = slope_data.copy()
                            slope_data_copy.loc[:, 'HSHKCXS'] = pd.to_numeric(slope_data_copy['HSHKCXS'], errors='coerce').fillna(0)
                            slope_data_copy.loc[:, 'deducted_area_mu'] = slope_data_copy['area_m2'] / 666.67 * (1 - slope_data_copy['HSHKCXS'])
                            slope_deducted_area_mu = slope_data_copy['deducted_area_mu'].sum()
                            cultivated_slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = round_to_2(slope_deducted_area_mu / 10000)
                        except:
                            cultivated_slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = 0
                    else:
                        cultivated_slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = 0
            else:
                # 先添加所有坡度级别的面积
                for slope_level in ['1', '2', '3', '4', '5']:
                    cultivated_slope_areas[f'坡度{slope_level}面积(万亩)'] = 0
                # 再添加所有坡度级别的扣除系数面积
                for slope_level in ['1', '2', '3', '4', '5']:
                    cultivated_slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = 0
                    
            total_cultivated_row = {
                '地类': '耕地',
                '字段': '总计',
                '值': '-',
                '描述': '',
                '类别': '',
                '面积(平方米)': round_to_2(cultivated_area_m2),
                '面积(亩)': round_to_2(cultivated_area_mu),
                '面积(万亩)': round_to_2(cultivated_area_mu / 10000),
                '扣除系数面积(亩)': round_to_2(total_deducted_area_mu),
                '扣除系数面积(万亩)': round_to_2(total_deducted_area_mu / 10000),
                '图斑数量': len(cultivated_land)
            }
            # 添加坡度面积列
            total_cultivated_row.update(cultivated_slope_areas)
            result_rows.append(total_cultivated_row)
            
            # 统计耕地HSHKCYY字段
            if 'HSHKCYY' in gdf.columns:
                # 为每个非空的HSHKCYY值统计面积
                hshkcyy_values = cultivated_land['HSHKCYY'].dropna().unique()
                for value in hshkcyy_values:
                    if pd.notna(value) and value != '':
                        filtered_data = cultivated_land[cultivated_land['HSHKCYY'] == value]
                        area_m2 = filtered_data['area_m2'].sum()
                        area_mu = area_m2 / 666.67
                        
                        # 计算扣除系数面积
                        if 'HSHKCXS' in filtered_data.columns:
                            try:
                                filtered_data_copy = filtered_data.copy()
                                filtered_data_copy.loc[:, 'HSHKCXS'] = pd.to_numeric(filtered_data_copy['HSHKCXS'], errors='coerce').fillna(0)
                                filtered_data_copy.loc[:, 'deducted_area_mu'] = filtered_data_copy['area_m2'] / 666.67 * (1 - filtered_data_copy['HSHKCXS'])
                                deducted_area_mu = filtered_data_copy['deducted_area_mu'].sum()
                            except:
                                deducted_area_mu = 0
                        else:
                            deducted_area_mu = 0
                        
                        # 获取描述信息
                        description = code_description_map.get(str(value), '')
                        # 获取类别信息
                        category = code_category_map.get(str(value), '')
                        
                        # 计算该分类下各坡度级别的面积（万亩）和扣除系数面积（万亩）
                        slope_areas = {}
                        if 'HSHPDJB' in gdf.columns:
                            # 先添加所有坡度级别的面积
                            for slope_level in ['1', '2', '3', '4', '5']:
                                slope_data = filtered_data[pd.notna(filtered_data['HSHPDJB']) & (filtered_data['HSHPDJB'].astype(str) == slope_level)]
                                slope_area_mu = slope_data['area_m2'].sum() / 666.67
                                slope_areas[f'坡度{slope_level}面积(万亩)'] = round_to_2(slope_area_mu / 10000)
                            
                            # 再添加所有坡度级别的扣除系数面积
                            for slope_level in ['1', '2', '3', '4', '5']:
                                slope_data = filtered_data[pd.notna(filtered_data['HSHPDJB']) & (filtered_data['HSHPDJB'].astype(str) == slope_level)]
                                # 计算坡度扣除系数面积
                                if 'HSHKCXS' in slope_data.columns:
                                    try:
                                        slope_data_copy = slope_data.copy()
                                        slope_data_copy.loc[:, 'HSHKCXS'] = pd.to_numeric(slope_data_copy['HSHKCXS'], errors='coerce').fillna(0)
                                        slope_data_copy.loc[:, 'deducted_area_mu'] = slope_data_copy['area_m2'] / 666.67 * (1 - slope_data_copy['HSHKCXS'])
                                        slope_deducted_area_mu = slope_data_copy['deducted_area_mu'].sum()
                                        slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = round_to_2(slope_deducted_area_mu / 10000)
                                    except:
                                        slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = 0
                                else:
                                    slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = 0
                        else:
                            # 先添加所有坡度级别的面积
                            for slope_level in ['1', '2', '3', '4', '5']:
                                slope_areas[f'坡度{slope_level}面积(万亩)'] = 0
                            # 再添加所有坡度级别的扣除系数面积
                            for slope_level in ['1', '2', '3', '4', '5']:
                                slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = 0
                        
                        row = {
                            '地类': '耕地',
                            '字段': 'HSHKCYY',
                            '值': value,
                            '描述': description,
                            '类别': category,
                            '面积(平方米)': round_to_2(area_m2),
                            '面积(亩)': round_to_2(area_mu),
                            '面积(万亩)': round_to_2(area_mu / 10000),
                            '扣除系数面积(亩)': round_to_2(deducted_area_mu),
                            '扣除系数面积(万亩)': round_to_2(deducted_area_mu / 10000),
                            '图斑数量': len(filtered_data)
                        }
                        # 添加坡度面积列
                        row.update(slope_areas)
                        result_rows.append(row)
            
            # 统计耕地HSHBLYY字段
            if 'HSHBLYY' in gdf.columns:
                # 为每个非空的HSHBLYY值统计面积
                hshblyy_values = cultivated_land['HSHBLYY'].dropna().unique()
                for value in hshblyy_values:
                    if pd.notna(value) and value != '':
                        filtered_data = cultivated_land[cultivated_land['HSHBLYY'] == value]
                        area_m2 = filtered_data['area_m2'].sum()
                        area_mu = area_m2 / 666.67
                        
                        # 计算扣除系数面积
                        if 'HSHKCXS' in filtered_data.columns:
                            try:
                                filtered_data_copy = filtered_data.copy()
                                filtered_data_copy.loc[:, 'HSHKCXS'] = pd.to_numeric(filtered_data_copy['HSHKCXS'], errors='coerce').fillna(0)
                                filtered_data_copy.loc[:, 'deducted_area_mu'] = filtered_data_copy['area_m2'] / 666.67 * (1 - filtered_data_copy['HSHKCXS'])
                                deducted_area_mu = filtered_data_copy['deducted_area_mu'].sum()
                            except:
                                deducted_area_mu = 0
                        else:
                            deducted_area_mu = 0
                        
                        # 获取描述信息
                        description = code_description_map.get(str(value), '')
                        # 获取类别信息
                        category = code_category_map.get(str(value), '')
                        
                        # 计算该分类下各坡度级别的面积（万亩）和扣除系数面积（万亩）
                        slope_areas = {}
                        if 'HSHPDJB' in gdf.columns:
                            # 先添加所有坡度级别的面积
                            for slope_level in ['1', '2', '3', '4', '5']:
                                slope_data = filtered_data[pd.notna(filtered_data['HSHPDJB']) & (filtered_data['HSHPDJB'].astype(str) == slope_level)]
                                slope_area_mu = slope_data['area_m2'].sum() / 666.67
                                slope_areas[f'坡度{slope_level}面积(万亩)'] = round_to_2(slope_area_mu / 10000)
                            
                            # 再添加所有坡度级别的扣除系数面积
                            for slope_level in ['1', '2', '3', '4', '5']:
                                slope_data = filtered_data[pd.notna(filtered_data['HSHPDJB']) & (filtered_data['HSHPDJB'].astype(str) == slope_level)]
                                # 计算坡度扣除系数面积
                                if 'HSHKCXS' in slope_data.columns:
                                    try:
                                        slope_data_copy = slope_data.copy()
                                        slope_data_copy.loc[:, 'HSHKCXS'] = pd.to_numeric(slope_data_copy['HSHKCXS'], errors='coerce').fillna(0)
                                        slope_data_copy.loc[:, 'deducted_area_mu'] = slope_data_copy['area_m2'] / 666.67 * (1 - slope_data_copy['HSHKCXS'])
                                        slope_deducted_area_mu = slope_data_copy['deducted_area_mu'].sum()
                                        slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = round_to_2(slope_deducted_area_mu / 10000)
                                    except:
                                        slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = 0
                                else:
                                    slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = 0
                        else:
                            # 先添加所有坡度级别的面积
                            for slope_level in ['1', '2', '3', '4', '5']:
                                slope_areas[f'坡度{slope_level}面积(万亩)'] = 0
                            # 再添加所有坡度级别的扣除系数面积
                            for slope_level in ['1', '2', '3', '4', '5']:
                                slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = 0
                        
                        row = {
                            '地类': '耕地',
                            '字段': 'HSHBLYY',
                            '值': value,
                            '描述': description,
                            '类别': category,
                            '面积(平方米)': round_to_2(area_m2),
                            '面积(亩)': round_to_2(area_mu),
                            '面积(万亩)': round_to_2(area_mu / 10000),
                            '扣除系数面积(亩)': round_to_2(deducted_area_mu),
                            '扣除系数面积(万亩)': round_to_2(deducted_area_mu / 10000),
                            '图斑数量': len(filtered_data)
                        }
                        # 添加坡度面积列
                        row.update(slope_areas)
                        result_rows.append(row)
            
            # 统计耕地HSHZHYY字段
            if 'HSHZHYY' in gdf.columns:
                # 为每个非空的HSHZHYY值统计面积
                hshzhyy_values = cultivated_land['HSHZHYY'].dropna().unique()
                for value in hshzhyy_values:
                    if pd.notna(value) and value != '':
                        filtered_data = cultivated_land[cultivated_land['HSHZHYY'] == value]
                        area_m2 = filtered_data['area_m2'].sum()
                        area_mu = area_m2 / 666.67
                        
                        # 计算扣除系数面积
                        if 'HSHKCXS' in filtered_data.columns:
                            try:
                                filtered_data_copy = filtered_data.copy()
                                filtered_data_copy.loc[:, 'HSHKCXS'] = pd.to_numeric(filtered_data_copy['HSHKCXS'], errors='coerce').fillna(0)
                                filtered_data_copy.loc[:, 'deducted_area_mu'] = filtered_data_copy['area_m2'] / 666.67 * (1 - filtered_data_copy['HSHKCXS'])
                                deducted_area_mu = filtered_data_copy['deducted_area_mu'].sum()
                            except:
                                deducted_area_mu = 0
                        else:
                            deducted_area_mu = 0
                        
                        # 获取描述信息
                        description = code_description_map.get(str(value), '')
                        # 获取类别信息
                        category = code_category_map.get(str(value), '')
                        
                        # 计算该分类下各坡度级别的面积（万亩）和扣除系数面积（万亩）
                        slope_areas = {}
                        if 'HSHPDJB' in gdf.columns:
                            # 先添加所有坡度级别的面积
                            for slope_level in ['1', '2', '3', '4', '5']:
                                slope_data = filtered_data[pd.notna(filtered_data['HSHPDJB']) & (filtered_data['HSHPDJB'].astype(str) == slope_level)]
                                slope_area_mu = slope_data['area_m2'].sum() / 666.67
                                slope_areas[f'坡度{slope_level}面积(万亩)'] = round_to_2(slope_area_mu / 10000)
                            
                            # 再添加所有坡度级别的扣除系数面积
                            for slope_level in ['1', '2', '3', '4', '5']:
                                slope_data = filtered_data[pd.notna(filtered_data['HSHPDJB']) & (filtered_data['HSHPDJB'].astype(str) == slope_level)]
                                # 计算坡度扣除系数面积
                                if 'HSHKCXS' in slope_data.columns:
                                    try:
                                        slope_data_copy = slope_data.copy()
                                        slope_data_copy.loc[:, 'HSHKCXS'] = pd.to_numeric(slope_data_copy['HSHKCXS'], errors='coerce').fillna(0)
                                        slope_data_copy.loc[:, 'deducted_area_mu'] = slope_data_copy['area_m2'] / 666.67 * (1 - slope_data_copy['HSHKCXS'])
                                        slope_deducted_area_mu = slope_data_copy['deducted_area_mu'].sum()
                                        slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = round_to_2(slope_deducted_area_mu / 10000)
                                    except:
                                        slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = 0
                                else:
                                    slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = 0
                        else:
                            # 先添加所有坡度级别的面积
                            for slope_level in ['1', '2', '3', '4', '5']:
                                slope_areas[f'坡度{slope_level}面积(万亩)'] = 0
                            # 再添加所有坡度级别的扣除系数面积
                            for slope_level in ['1', '2', '3', '4', '5']:
                                slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = 0
                        
                        row = {
                            '地类': '耕地',
                            '字段': 'HSHZHYY',
                            '值': value,
                            '描述': description,
                            '类别': category,
                            '面积(平方米)': round_to_2(area_m2),
                            '面积(亩)': round_to_2(area_mu),
                            '面积(万亩)': round_to_2(area_mu / 10000),
                            '扣除系数面积(亩)': round_to_2(deducted_area_mu),
                            '扣除系数面积(万亩)': round_to_2(deducted_area_mu / 10000),
                            '图斑数量': len(filtered_data)
                        }
                        # 添加坡度面积列
                        row.update(slope_areas)
                        result_rows.append(row)
            
            # 添加园地统计
            # 园地总计
            # 计算扣除系数面积
            if 'HSHKCXS' in garden_land.columns:
                try:
                    garden_land_copy = garden_land.copy()
                    garden_land_copy.loc[:, 'HSHKCXS'] = pd.to_numeric(garden_land_copy['HSHKCXS'], errors='coerce').fillna(0)
                    garden_land_copy.loc[:, 'deducted_area_mu'] = garden_land_copy['area_m2'] / 666.67 * (1 - garden_land_copy['HSHKCXS'])
                    garden_deducted_area_mu = garden_land_copy['deducted_area_mu'].sum()
                except:
                    garden_deducted_area_mu = 0
            else:
                garden_deducted_area_mu = 0
            
            # 计算园地各坡度级别的面积（万亩）和扣除系数面积（万亩）
            garden_slope_areas = {}
            if 'HSHPDJB' in gdf.columns:
                # 先添加所有坡度级别的面积
                for slope_level in ['1', '2', '3', '4', '5']:
                    slope_data = garden_land[pd.notna(garden_land['HSHPDJB']) & (garden_land['HSHPDJB'].astype(str) == slope_level)]
                    slope_area_mu = slope_data['area_m2'].sum() / 666.67
                    garden_slope_areas[f'坡度{slope_level}面积(万亩)'] = round_to_2(slope_area_mu / 10000)
                
                # 再添加所有坡度级别的扣除系数面积
                for slope_level in ['1', '2', '3', '4', '5']:
                    slope_data = garden_land[pd.notna(garden_land['HSHPDJB']) & (garden_land['HSHPDJB'].astype(str) == slope_level)]
                    # 计算坡度扣除系数面积
                    if 'HSHKCXS' in slope_data.columns:
                        try:
                            slope_data_copy = slope_data.copy()
                            slope_data_copy.loc[:, 'HSHKCXS'] = pd.to_numeric(slope_data_copy['HSHKCXS'], errors='coerce').fillna(0)
                            slope_data_copy.loc[:, 'deducted_area_mu'] = slope_data_copy['area_m2'] / 666.67 * (1 - slope_data_copy['HSHKCXS'])
                            slope_deducted_area_mu = slope_data_copy['deducted_area_mu'].sum()
                            garden_slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = round_to_2(slope_deducted_area_mu / 10000)
                        except:
                            garden_slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = 0
                    else:
                        garden_slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = 0
            else:
                # 先添加所有坡度级别的面积
                for slope_level in ['1', '2', '3', '4', '5']:
                    garden_slope_areas[f'坡度{slope_level}面积(万亩)'] = 0
                # 再添加所有坡度级别的扣除系数面积
                for slope_level in ['1', '2', '3', '4', '5']:
                    garden_slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = 0
                    
            garden_row = {
                '地类': '园地',
                '字段': '总计',
                '值': '-',
                '描述': '',
                '类别': '',
                '面积(平方米)': round_to_2(garden_area_m2),
                '面积(亩)': round_to_2(garden_area_mu),
                '面积(万亩)': round_to_2(garden_area_mu / 10000),
                '扣除系数面积(亩)': round_to_2(garden_deducted_area_mu),
                '扣除系数面积(万亩)': round_to_2(garden_deducted_area_mu / 10000),
                '图斑数量': len(garden_land)
            }
            # 添加坡度面积列
            garden_row.update(garden_slope_areas)
            result_rows.append(garden_row)
            
            # 统计园地HSHKCYY字段
            if 'HSHKCYY' in gdf.columns:
                # 为每个非空的HSHKCYY值统计面积
                hshkcyy_values = garden_land['HSHKCYY'].dropna().unique()
                for value in hshkcyy_values:
                    if pd.notna(value) and value != '':
                        filtered_data = garden_land[garden_land['HSHKCYY'] == value]
                        area_m2 = filtered_data['area_m2'].sum()
                        area_mu = area_m2 / 666.67
                        
                        # 计算扣除系数面积
                        if 'HSHKCXS' in filtered_data.columns:
                            try:
                                filtered_data_copy = filtered_data.copy()
                                filtered_data_copy.loc[:, 'HSHKCXS'] = pd.to_numeric(filtered_data_copy['HSHKCXS'], errors='coerce').fillna(0)
                                filtered_data_copy.loc[:, 'deducted_area_mu'] = filtered_data_copy['area_m2'] / 666.67 * (1 - filtered_data_copy['HSHKCXS'])
                                deducted_area_mu = filtered_data_copy['deducted_area_mu'].sum()
                            except:
                                deducted_area_mu = 0
                        else:
                            deducted_area_mu = 0
                        
                        # 获取描述信息
                        description = code_description_map.get(str(value), '')
                        # 获取类别信息
                        category = code_category_map.get(str(value), '')
                        
                        # 计算该分类下各坡度级别的面积（万亩）和扣除系数面积（万亩）
                        slope_areas = {}
                        if 'HSHPDJB' in gdf.columns:
                            # 先添加所有坡度级别的面积
                            for slope_level in ['1', '2', '3', '4', '5']:
                                slope_data = filtered_data[pd.notna(filtered_data['HSHPDJB']) & (filtered_data['HSHPDJB'].astype(str) == slope_level)]
                                slope_area_mu = slope_data['area_m2'].sum() / 666.67
                                slope_areas[f'坡度{slope_level}面积(万亩)'] = round_to_2(slope_area_mu / 10000)
                            
                            # 再添加所有坡度级别的扣除系数面积
                            for slope_level in ['1', '2', '3', '4', '5']:
                                slope_data = filtered_data[pd.notna(filtered_data['HSHPDJB']) & (filtered_data['HSHPDJB'].astype(str) == slope_level)]
                                # 计算坡度扣除系数面积
                                if 'HSHKCXS' in slope_data.columns:
                                    try:
                                        slope_data_copy = slope_data.copy()
                                        slope_data_copy.loc[:, 'HSHKCXS'] = pd.to_numeric(slope_data_copy['HSHKCXS'], errors='coerce').fillna(0)
                                        slope_data_copy.loc[:, 'deducted_area_mu'] = slope_data_copy['area_m2'] / 666.67 * (1 - slope_data_copy['HSHKCXS'])
                                        slope_deducted_area_mu = slope_data_copy['deducted_area_mu'].sum()
                                        slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = round_to_2(slope_deducted_area_mu / 10000)
                                    except:
                                        slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = 0
                                else:
                                    slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = 0
                        else:
                            # 先添加所有坡度级别的面积
                            for slope_level in ['1', '2', '3', '4', '5']:
                                slope_areas[f'坡度{slope_level}面积(万亩)'] = 0
                            # 再添加所有坡度级别的扣除系数面积
                            for slope_level in ['1', '2', '3', '4', '5']:
                                slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = 0
                        
                        row = {
                            '地类': '园地',
                            '字段': 'HSHKCYY',
                            '值': value,
                            '描述': description,
                            '类别': category,
                            '面积(平方米)': round_to_2(area_m2),
                            '面积(亩)': round_to_2(area_mu),
                            '面积(万亩)': round_to_2(area_mu / 10000),
                            '扣除系数面积(亩)': round_to_2(deducted_area_mu),
                            '扣除系数面积(万亩)': round_to_2(deducted_area_mu / 10000),
                            '图斑数量': len(filtered_data)
                        }
                        # 添加坡度面积列
                        row.update(slope_areas)
                        result_rows.append(row)
            
            # 统计园地HSHBLYY字段
            if 'HSHBLYY' in gdf.columns:
                # 为每个非空的HSHBLYY值统计面积
                hshblyy_values = garden_land['HSHBLYY'].dropna().unique()
                for value in hshblyy_values:
                    if pd.notna(value) and value != '':
                        filtered_data = garden_land[garden_land['HSHBLYY'] == value]
                        area_m2 = filtered_data['area_m2'].sum()
                        area_mu = area_m2 / 666.67
                        
                        # 计算扣除系数面积
                        if 'HSHKCXS' in filtered_data.columns:
                            try:
                                filtered_data_copy = filtered_data.copy()
                                filtered_data_copy.loc[:, 'HSHKCXS'] = pd.to_numeric(filtered_data_copy['HSHKCXS'], errors='coerce').fillna(0)
                                filtered_data_copy.loc[:, 'deducted_area_mu'] = filtered_data_copy['area_m2'] / 666.67 * (1 - filtered_data_copy['HSHKCXS'])
                                deducted_area_mu = filtered_data_copy['deducted_area_mu'].sum()
                            except:
                                deducted_area_mu = 0
                        else:
                            deducted_area_mu = 0
                        
                        # 获取描述信息
                        description = code_description_map.get(str(value), '')
                        # 获取类别信息
                        category = code_category_map.get(str(value), '')
                        
                        # 计算该分类下各坡度级别的面积（万亩）和扣除系数面积（万亩）
                        slope_areas = {}
                        if 'HSHPDJB' in gdf.columns:
                            # 先添加所有坡度级别的面积
                            for slope_level in ['1', '2', '3', '4', '5']:
                                slope_data = filtered_data[pd.notna(filtered_data['HSHPDJB']) & (filtered_data['HSHPDJB'].astype(str) == slope_level)]
                                slope_area_mu = slope_data['area_m2'].sum() / 666.67
                                slope_areas[f'坡度{slope_level}面积(万亩)'] = round_to_2(slope_area_mu / 10000)
                            
                            # 再添加所有坡度级别的扣除系数面积
                            for slope_level in ['1', '2', '3', '4', '5']:
                                slope_data = filtered_data[pd.notna(filtered_data['HSHPDJB']) & (filtered_data['HSHPDJB'].astype(str) == slope_level)]
                                # 计算坡度扣除系数面积
                                if 'HSHKCXS' in slope_data.columns:
                                    try:
                                        slope_data_copy = slope_data.copy()
                                        slope_data_copy.loc[:, 'HSHKCXS'] = pd.to_numeric(slope_data_copy['HSHKCXS'], errors='coerce').fillna(0)
                                        slope_data_copy.loc[:, 'deducted_area_mu'] = slope_data_copy['area_m2'] / 666.67 * (1 - slope_data_copy['HSHKCXS'])
                                        slope_deducted_area_mu = slope_data_copy['deducted_area_mu'].sum()
                                        slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = round_to_2(slope_deducted_area_mu / 10000)
                                    except:
                                        slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = 0
                                else:
                                    slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = 0
                        else:
                            # 先添加所有坡度级别的面积
                            for slope_level in ['1', '2', '3', '4', '5']:
                                slope_areas[f'坡度{slope_level}面积(万亩)'] = 0
                            # 再添加所有坡度级别的扣除系数面积
                            for slope_level in ['1', '2', '3', '4', '5']:
                                slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = 0
                        
                        row = {
                            '地类': '园地',
                            '字段': 'HSHBLYY',
                            '值': value,
                            '描述': description,
                            '类别': category,
                            '面积(平方米)': round_to_2(area_m2),
                            '面积(亩)': round_to_2(area_mu),
                            '面积(万亩)': round_to_2(area_mu / 10000),
                            '扣除系数面积(亩)': round_to_2(deducted_area_mu),
                            '扣除系数面积(万亩)': round_to_2(deducted_area_mu / 10000),
                            '图斑数量': len(filtered_data)
                        }
                        # 添加坡度面积列
                        row.update(slope_areas)
                        result_rows.append(row)
            
            # 统计园地HSHZHYY字段
            if 'HSHZHYY' in gdf.columns:
                # 为每个非空的HSHZHYY值统计面积
                hshzhyy_values = garden_land['HSHZHYY'].dropna().unique()
                for value in hshzhyy_values:
                    if pd.notna(value) and value != '':
                        filtered_data = garden_land[garden_land['HSHZHYY'] == value]
                        area_m2 = filtered_data['area_m2'].sum()
                        area_mu = area_m2 / 666.67
                        
                        # 计算扣除系数面积
                        if 'HSHKCXS' in filtered_data.columns:
                            try:
                                filtered_data_copy = filtered_data.copy()
                                filtered_data_copy.loc[:, 'HSHKCXS'] = pd.to_numeric(filtered_data_copy['HSHKCXS'], errors='coerce').fillna(0)
                                filtered_data_copy.loc[:, 'deducted_area_mu'] = filtered_data_copy['area_m2'] / 666.67 * (1 - filtered_data_copy['HSHKCXS'])
                                deducted_area_mu = filtered_data_copy['deducted_area_mu'].sum()
                            except:
                                deducted_area_mu = 0
                        else:
                            deducted_area_mu = 0
                        
                        # 获取描述信息
                        description = code_description_map.get(str(value), '')
                        # 获取类别信息
                        category = code_category_map.get(str(value), '')
                        
                        # 计算该分类下各坡度级别的面积（万亩）和扣除系数面积（万亩）
                        slope_areas = {}
                        if 'HSHPDJB' in gdf.columns:
                            # 先添加所有坡度级别的面积
                            for slope_level in ['1', '2', '3', '4', '5']:
                                slope_data = filtered_data[pd.notna(filtered_data['HSHPDJB']) & (filtered_data['HSHPDJB'].astype(str) == slope_level)]
                                slope_area_mu = slope_data['area_m2'].sum() / 666.67
                                slope_areas[f'坡度{slope_level}面积(万亩)'] = round_to_2(slope_area_mu / 10000)
                            
                            # 再添加所有坡度级别的扣除系数面积
                            for slope_level in ['1', '2', '3', '4', '5']:
                                slope_data = filtered_data[pd.notna(filtered_data['HSHPDJB']) & (filtered_data['HSHPDJB'].astype(str) == slope_level)]
                                # 计算坡度扣除系数面积
                                if 'HSHKCXS' in slope_data.columns:
                                    try:
                                        slope_data_copy = slope_data.copy()
                                        slope_data_copy.loc[:, 'HSHKCXS'] = pd.to_numeric(slope_data_copy['HSHKCXS'], errors='coerce').fillna(0)
                                        slope_data_copy.loc[:, 'deducted_area_mu'] = slope_data_copy['area_m2'] / 666.67 * (1 - slope_data_copy['HSHKCXS'])
                                        slope_deducted_area_mu = slope_data_copy['deducted_area_mu'].sum()
                                        slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = round_to_2(slope_deducted_area_mu / 10000)
                                    except:
                                        slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = 0
                                else:
                                    slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = 0
                        else:
                            # 先添加所有坡度级别的面积
                            for slope_level in ['1', '2', '3', '4', '5']:
                                slope_areas[f'坡度{slope_level}面积(万亩)'] = 0
                            # 再添加所有坡度级别的扣除系数面积
                            for slope_level in ['1', '2', '3', '4', '5']:
                                slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = 0
                        
                        row = {
                            '地类': '园地',
                            '字段': 'HSHZHYY',
                            '值': value,
                            '描述': description,
                            '类别': category,
                            '面积(平方米)': round_to_2(area_m2),
                            '面积(亩)': round_to_2(area_mu),
                            '面积(万亩)': round_to_2(area_mu / 10000),
                            '扣除系数面积(亩)': round_to_2(deducted_area_mu),
                            '扣除系数面积(万亩)': round_to_2(deducted_area_mu / 10000),
                            '图斑数量': len(filtered_data)
                        }
                        # 添加坡度面积列
                        row.update(slope_areas)
                        result_rows.append(row)
            
            # 添加林地统计
            # 林地总计
            # 计算扣除系数面积
            if 'HSHKCXS' in forest_land.columns:
                try:
                    forest_land_copy = forest_land.copy()
                    forest_land_copy.loc[:, 'HSHKCXS'] = pd.to_numeric(forest_land_copy['HSHKCXS'], errors='coerce').fillna(0)
                    forest_land_copy.loc[:, 'deducted_area_mu'] = forest_land_copy['area_m2'] / 666.67 * (1 - forest_land_copy['HSHKCXS'])
                    forest_deducted_area_mu = forest_land_copy['deducted_area_mu'].sum()
                except:
                    forest_deducted_area_mu = 0
            else:
                forest_deducted_area_mu = 0
            
            # 计算林地各坡度级别的面积（万亩）和扣除系数面积（万亩）
            forest_slope_areas = {}
            if 'HSHPDJB' in gdf.columns:
                # 先添加所有坡度级别的面积
                for slope_level in ['1', '2', '3', '4', '5']:
                    slope_data = forest_land[pd.notna(forest_land['HSHPDJB']) & (forest_land['HSHPDJB'].astype(str) == slope_level)]
                    slope_area_mu = slope_data['area_m2'].sum() / 666.67
                    forest_slope_areas[f'坡度{slope_level}面积(万亩)'] = round_to_2(slope_area_mu / 10000)
                
                # 再添加所有坡度级别的扣除系数面积
                for slope_level in ['1', '2', '3', '4', '5']:
                    slope_data = forest_land[pd.notna(forest_land['HSHPDJB']) & (forest_land['HSHPDJB'].astype(str) == slope_level)]
                    # 计算坡度扣除系数面积
                    if 'HSHKCXS' in slope_data.columns:
                        try:
                            slope_data_copy = slope_data.copy()
                            slope_data_copy.loc[:, 'HSHKCXS'] = pd.to_numeric(slope_data_copy['HSHKCXS'], errors='coerce').fillna(0)
                            slope_data_copy.loc[:, 'deducted_area_mu'] = slope_data_copy['area_m2'] / 666.67 * (1 - slope_data_copy['HSHKCXS'])
                            slope_deducted_area_mu = slope_data_copy['deducted_area_mu'].sum()
                            forest_slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = round_to_2(slope_deducted_area_mu / 10000)
                        except:
                            forest_slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = 0
                    else:
                        forest_slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = 0
            else:
                # 先添加所有坡度级别的面积
                for slope_level in ['1', '2', '3', '4', '5']:
                    forest_slope_areas[f'坡度{slope_level}面积(万亩)'] = 0
                # 再添加所有坡度级别的扣除系数面积
                for slope_level in ['1', '2', '3', '4', '5']:
                    forest_slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = 0
                    
            forest_row = {
                '地类': '林地',
                '字段': '总计',
                '值': '-',
                '描述': '',
                '类别': '',
                '面积(平方米)': round_to_2(forest_area_m2),
                '面积(亩)': round_to_2(forest_area_mu),
                '面积(万亩)': round_to_2(forest_area_mu / 10000),
                '扣除系数面积(亩)': round_to_2(forest_deducted_area_mu),
                '扣除系数面积(万亩)': round_to_2(forest_deducted_area_mu / 10000),
                '图斑数量': len(forest_land)
            }
            # 添加坡度面积列
            forest_row.update(forest_slope_areas)
            result_rows.append(forest_row)
            
            # 统计林地HSHKCYY字段
            if 'HSHKCYY' in gdf.columns:
                # 为每个非空的HSHKCYY值统计面积
                hshkcyy_values = forest_land['HSHKCYY'].dropna().unique()
                for value in hshkcyy_values:
                    if pd.notna(value) and value != '':
                        filtered_data = forest_land[forest_land['HSHKCYY'] == value]
                        area_m2 = filtered_data['area_m2'].sum()
                        area_mu = area_m2 / 666.67
                        
                        # 计算扣除系数面积
                        if 'HSHKCXS' in filtered_data.columns:
                            try:
                                filtered_data_copy = filtered_data.copy()
                                filtered_data_copy.loc[:, 'HSHKCXS'] = pd.to_numeric(filtered_data_copy['HSHKCXS'], errors='coerce').fillna(0)
                                filtered_data_copy.loc[:, 'deducted_area_mu'] = filtered_data_copy['area_m2'] / 666.67 * (1 - filtered_data_copy['HSHKCXS'])
                                deducted_area_mu = filtered_data_copy['deducted_area_mu'].sum()
                            except:
                                deducted_area_mu = 0
                        else:
                            deducted_area_mu = 0
                        
                        # 获取描述信息
                        description = code_description_map.get(str(value), '')
                        # 获取类别信息
                        category = code_category_map.get(str(value), '')
                        
                        # 计算该分类下各坡度级别的面积（万亩）和扣除系数面积（万亩）
                        slope_areas = {}
                        if 'HSHPDJB' in gdf.columns:
                            # 先添加所有坡度级别的面积
                            for slope_level in ['1', '2', '3', '4', '5']:
                                slope_data = filtered_data[pd.notna(filtered_data['HSHPDJB']) & (filtered_data['HSHPDJB'].astype(str) == slope_level)]
                                slope_area_mu = slope_data['area_m2'].sum() / 666.67
                                slope_areas[f'坡度{slope_level}面积(万亩)'] = round_to_2(slope_area_mu / 10000)
                            
                            # 再添加所有坡度级别的扣除系数面积
                            for slope_level in ['1', '2', '3', '4', '5']:
                                slope_data = filtered_data[pd.notna(filtered_data['HSHPDJB']) & (filtered_data['HSHPDJB'].astype(str) == slope_level)]
                                # 计算坡度扣除系数面积
                                if 'HSHKCXS' in slope_data.columns:
                                    try:
                                        slope_data_copy = slope_data.copy()
                                        slope_data_copy.loc[:, 'HSHKCXS'] = pd.to_numeric(slope_data_copy['HSHKCXS'], errors='coerce').fillna(0)
                                        slope_data_copy.loc[:, 'deducted_area_mu'] = slope_data_copy['area_m2'] / 666.67 * (1 - slope_data_copy['HSHKCXS'])
                                        slope_deducted_area_mu = slope_data_copy['deducted_area_mu'].sum()
                                        slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = round_to_2(slope_deducted_area_mu / 10000)
                                    except:
                                        slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = 0
                                else:
                                    slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = 0
                        else:
                            # 先添加所有坡度级别的面积
                            for slope_level in ['1', '2', '3', '4', '5']:
                                slope_areas[f'坡度{slope_level}面积(万亩)'] = 0
                            # 再添加所有坡度级别的扣除系数面积
                            for slope_level in ['1', '2', '3', '4', '5']:
                                slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = 0
                        
                        row = {
                            '地类': '林地',
                            '字段': 'HSHKCYY',
                            '值': value,
                            '描述': description,
                            '类别': category,
                            '面积(平方米)': round_to_2(area_m2),
                            '面积(亩)': round_to_2(area_mu),
                            '面积(万亩)': round_to_2(area_mu / 10000),
                            '扣除系数面积(亩)': round_to_2(deducted_area_mu),
                            '扣除系数面积(万亩)': round_to_2(deducted_area_mu / 10000),
                            '图斑数量': len(filtered_data)
                        }
                        # 添加坡度面积列
                        row.update(slope_areas)
                        result_rows.append(row)
            
            # 统计林地HSHBLYY字段
            if 'HSHBLYY' in gdf.columns:
                # 为每个非空的HSHBLYY值统计面积
                hshblyy_values = forest_land['HSHBLYY'].dropna().unique()
                for value in hshblyy_values:
                    if pd.notna(value) and value != '':
                        filtered_data = forest_land[forest_land['HSHBLYY'] == value]
                        area_m2 = filtered_data['area_m2'].sum()
                        area_mu = area_m2 / 666.67
                        
                        # 计算扣除系数面积
                        if 'HSHKCXS' in filtered_data.columns:
                            try:
                                filtered_data_copy = filtered_data.copy()
                                filtered_data_copy.loc[:, 'HSHKCXS'] = pd.to_numeric(filtered_data_copy['HSHKCXS'], errors='coerce').fillna(0)
                                filtered_data_copy.loc[:, 'deducted_area_mu'] = filtered_data_copy['area_m2'] / 666.67 * (1 - filtered_data_copy['HSHKCXS'])
                                deducted_area_mu = filtered_data_copy['deducted_area_mu'].sum()
                            except:
                                deducted_area_mu = 0
                        else:
                            deducted_area_mu = 0
                        
                        # 获取描述信息
                        description = code_description_map.get(str(value), '')
                        # 获取类别信息
                        category = code_category_map.get(str(value), '')
                        
                        # 计算该分类下各坡度级别的面积（万亩）和扣除系数面积（万亩）
                        slope_areas = {}
                        if 'HSHPDJB' in gdf.columns:
                            # 先添加所有坡度级别的面积
                            for slope_level in ['1', '2', '3', '4', '5']:
                                slope_data = filtered_data[pd.notna(filtered_data['HSHPDJB']) & (filtered_data['HSHPDJB'].astype(str) == slope_level)]
                                slope_area_mu = slope_data['area_m2'].sum() / 666.67
                                slope_areas[f'坡度{slope_level}面积(万亩)'] = round_to_2(slope_area_mu / 10000)
                            
                            # 再添加所有坡度级别的扣除系数面积
                            for slope_level in ['1', '2', '3', '4', '5']:
                                slope_data = filtered_data[pd.notna(filtered_data['HSHPDJB']) & (filtered_data['HSHPDJB'].astype(str) == slope_level)]
                                # 计算坡度扣除系数面积
                                if 'HSHKCXS' in slope_data.columns:
                                    try:
                                        slope_data_copy = slope_data.copy()
                                        slope_data_copy.loc[:, 'HSHKCXS'] = pd.to_numeric(slope_data_copy['HSHKCXS'], errors='coerce').fillna(0)
                                        slope_data_copy.loc[:, 'deducted_area_mu'] = slope_data_copy['area_m2'] / 666.67 * (1 - slope_data_copy['HSHKCXS'])
                                        slope_deducted_area_mu = slope_data_copy['deducted_area_mu'].sum()
                                        slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = round_to_2(slope_deducted_area_mu / 10000)
                                    except:
                                        slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = 0
                                else:
                                    slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = 0
                        else:
                            # 先添加所有坡度级别的面积
                            for slope_level in ['1', '2', '3', '4', '5']:
                                slope_areas[f'坡度{slope_level}面积(万亩)'] = 0
                            # 再添加所有坡度级别的扣除系数面积
                            for slope_level in ['1', '2', '3', '4', '5']:
                                slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = 0
                        
                        row = {
                            '地类': '林地',
                            '字段': 'HSHBLYY',
                            '值': value,
                            '描述': description,
                            '类别': category,
                            '面积(平方米)': round_to_2(area_m2),
                            '面积(亩)': round_to_2(area_mu),
                            '面积(万亩)': round_to_2(area_mu / 10000),
                            '扣除系数面积(亩)': round_to_2(deducted_area_mu),
                            '扣除系数面积(万亩)': round_to_2(deducted_area_mu / 10000),
                            '图斑数量': len(filtered_data)
                        }
                        # 添加坡度面积列
                        row.update(slope_areas)
                        result_rows.append(row)
            
            # 统计林地HSHZHYY字段
            if 'HSHZHYY' in gdf.columns:
                # 为每个非空的HSHZHYY值统计面积
                hshzhyy_values = forest_land['HSHZHYY'].dropna().unique()
                for value in hshzhyy_values:
                    if pd.notna(value) and value != '':
                        filtered_data = forest_land[forest_land['HSHZHYY'] == value]
                        area_m2 = filtered_data['area_m2'].sum()
                        area_mu = area_m2 / 666.67
                        
                        # 计算扣除系数面积
                        if 'HSHKCXS' in filtered_data.columns:
                            try:
                                filtered_data_copy = filtered_data.copy()
                                filtered_data_copy.loc[:, 'HSHKCXS'] = pd.to_numeric(filtered_data_copy['HSHKCXS'], errors='coerce').fillna(0)
                                filtered_data_copy.loc[:, 'deducted_area_mu'] = filtered_data_copy['area_m2'] / 666.67 * (1 - filtered_data_copy['HSHKCXS'])
                                deducted_area_mu = filtered_data_copy['deducted_area_mu'].sum()
                            except:
                                deducted_area_mu = 0
                        else:
                            deducted_area_mu = 0
                        
                        # 获取描述信息
                        description = code_description_map.get(str(value), '')
                        # 获取类别信息
                        category = code_category_map.get(str(value), '')
                        
                        # 计算该分类下各坡度级别的面积（万亩）和扣除系数面积（万亩）
                        slope_areas = {}
                        if 'HSHPDJB' in gdf.columns:
                            # 先添加所有坡度级别的面积
                            for slope_level in ['1', '2', '3', '4', '5']:
                                slope_data = filtered_data[pd.notna(filtered_data['HSHPDJB']) & (filtered_data['HSHPDJB'].astype(str) == slope_level)]
                                slope_area_mu = slope_data['area_m2'].sum() / 666.67
                                slope_areas[f'坡度{slope_level}面积(万亩)'] = round_to_2(slope_area_mu / 10000)
                            
                            # 再添加所有坡度级别的扣除系数面积
                            for slope_level in ['1', '2', '3', '4', '5']:
                                slope_data = filtered_data[pd.notna(filtered_data['HSHPDJB']) & (filtered_data['HSHPDJB'].astype(str) == slope_level)]
                                # 计算坡度扣除系数面积
                                if 'HSHKCXS' in slope_data.columns:
                                    try:
                                        slope_data_copy = slope_data.copy()
                                        slope_data_copy.loc[:, 'HSHKCXS'] = pd.to_numeric(slope_data_copy['HSHKCXS'], errors='coerce').fillna(0)
                                        slope_data_copy.loc[:, 'deducted_area_mu'] = slope_data_copy['area_m2'] / 666.67 * (1 - slope_data_copy['HSHKCXS'])
                                        slope_deducted_area_mu = slope_data_copy['deducted_area_mu'].sum()
                                        slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = round_to_2(slope_deducted_area_mu / 10000)
                                    except:
                                        slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = 0
                                else:
                                    slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = 0
                        else:
                            # 先添加所有坡度级别的面积
                            for slope_level in ['1', '2', '3', '4', '5']:
                                slope_areas[f'坡度{slope_level}面积(万亩)'] = 0
                            # 再添加所有坡度级别的扣除系数面积
                            for slope_level in ['1', '2', '3', '4', '5']:
                                slope_areas[f'坡度{slope_level}扣除系数面积(万亩)'] = 0
                        
                        row = {
                            '地类': '林地',
                            '字段': 'HSHZHYY',
                            '值': value,
                            '描述': description,
                            '类别': category,
                            '面积(平方米)': round_to_2(area_m2),
                            '面积(亩)': round_to_2(area_mu),
                            '面积(万亩)': round_to_2(area_mu / 10000),
                            '扣除系数面积(亩)': round_to_2(deducted_area_mu),
                            '扣除系数面积(万亩)': round_to_2(deducted_area_mu / 10000),
                            '图斑数量': len(filtered_data)
                        }
                        # 添加坡度面积列
                        row.update(slope_areas)
                        result_rows.append(row)
            
            # 创建结果DataFrame
            self.update_progress_signal.emit(95, "正在生成结果DataFrame")
            result_df = pd.DataFrame(result_rows)
            
            # 保存到Excel
            if output_excel:
                self.update_progress_signal.emit(98, f"正在保存到Excel文件: {output_excel}")
                # 确保输出目录存在
                output_dir = os.path.dirname(output_excel)
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir, exist_ok=True)
                
                # 保存到Excel
                result_df.to_excel(output_excel, index=False, sheet_name='耕园林流向一览表')
                self.update_progress_signal.emit(100, f"已成功保存到: {output_excel}")
            
            return result_df
            
        except Exception as e:
            self.show_error_signal.emit(f"处理出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def execute(self):
        """执行功能"""
        # 1. 验证输入
        valid, message = self.validate()
        if not valid:
            self.showError(message)
            return
        
        # 2. 获取参数
        gdb_path = self.gdbPath.text()
        layer_name = self.layerName.text()
        output_excel = self.outputPath.text()
        land_code_field = self.landCodeField.text() if self.landCodeField.text() else 'TKJ_DLBM'
        
        # 3. 显示进度
        self.showProgress("正在处理...")
        
        # 4. 在线程中执行处理
        def run_process():
            try:
                # 执行计算
                result_df = self.calculate_land_category_statistics(gdb_path, layer_name, output_excel, land_code_field)
                
                if result_df is not None:
                    # 使用信号通知主线程显示成功消息，避免线程安全问题
                    self.show_success_signal.emit(f"处理完成！结果已保存到: {output_excel}")
                else:
                    # 使用信号通知主线程显示错误消息
                    self.show_error_signal.emit("处理失败！")
                    
            except Exception as e:
                # 捕获并显示错误
                import traceback
                error_msg = f"处理失败: {str(e)}\n\n{traceback.format_exc()}"
                # 使用信号通知主线程显示错误消息
                self.show_error_signal.emit(error_msg)
        
        # 启动线程
        threading.Thread(target=run_process, daemon=True).start()