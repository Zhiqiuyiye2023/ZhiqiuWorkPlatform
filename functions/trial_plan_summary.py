# coding:utf-8
"""
试划成果总结统计功能
管理边界相交面积计算表1
"""

from PyQt6.QtWidgets import QFileDialog, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from qfluentwidgets import LineEdit, PushButton, FluentIcon as FIF
from .base_function import BaseFunction
import os
import sys
import geopandas as gpd
import pandas as pd
import openpyxl


class TrialPlanSummaryThread(QThread):
    """试划成果总结统计线程"""
    
    success = pyqtSignal(str)  # 成功信号，传递结果文件路径
    error = pyqtSignal(str)    # 错误信号，传递错误信息
    progress = pyqtSignal(int, str)  # 进度信号，传递进度百分比和状态文本
    
    def __init__(self, gdb_path, output_excel, template_path="", parent=None):
        """
        Args:
            gdb_path: GDB文件路径
            output_excel: 输出Excel文件路径
            template_path: 模板文件路径，可选
        """
        super().__init__(parent)
        self.gdb_path = gdb_path
        self.output_excel = output_excel
        self.template_path = template_path
    
    def run(self):
        """线程运行方法"""
        try:
            self.progress.emit(0, "开始执行试划成果总结统计")
            
            # 检查文件是否存在
            if not os.path.exists(self.gdb_path):
                self.error.emit(f"错误：GDB文件 {self.gdb_path} 不存在！")
                return
            
            self.progress.emit(5, "正在读取GDB文件...")
            
            # 读取YJJBNTBHTB图层
            self.progress.emit(10, "正在读取YJJBNTBHTB图层...")
            gdf_yjjb = gpd.read_file(self.gdb_path, layer='YJJBNTBHTB')
            
            # 读取管理边界划定成果图层
            self.progress.emit(20, "正在读取管理边界划定成果图层...")
            gdf_glbj = gpd.read_file(self.gdb_path, layer='管理边界划定成果')
            
            # 读取DLTB图层
            self.progress.emit(30, "正在读取DLTB图层...")
            gdf_dltb = gpd.read_file(self.gdb_path, layer='DLTB')
            
            # 读取LD图层
            self.progress.emit(40, "正在读取LD图层...")
            gdf_ld = gpd.read_file(self.gdb_path, layer='LD')
            
            # 检查必要字段是否存在
            self.progress.emit(50, "正在检查必要字段...")
            missing_fields = []
            
            # 检查YJJBNTBHTB图层
            if 'YJJBNTLX' not in gdf_yjjb.columns:
                missing_fields.append("YJJBNTBHTB.YJJBNTLX")
            
            # 检查管理边界划定成果图层
            for field in ['ZHLX', 'CLLX', 'HSHKCXS', 'GLBJLX', 'HSHPDJB']:
                if field not in gdf_glbj.columns:
                    missing_fields.append(f"管理边界划定成果.{field}")
            
            # 检查DLTB图层
            for field in ['TKJ_DLBM', 'KCXS']:
                if field not in gdf_dltb.columns:
                    missing_fields.append(f"DLTB.{field}")
            
            if missing_fields:
                self.error.emit(f"错误：图层中缺少以下必需字段: {', '.join(missing_fields)}")
                return
            
            # 确保几何数据是投影坐标系
            self.progress.emit(55, "正在转换坐标系...")
            crs_epsg = 4539  # CGCS2000 / 3-degree Gauss-Kruger zone 35（四川省达川区）
            
            # 转换所有图层到投影坐标系
            for gdf, name in [(gdf_yjjb, 'YJJBNTBHTB'), (gdf_glbj, '管理边界划定成果'), 
                            (gdf_dltb, 'DLTB'), (gdf_ld, 'LD')]:
                if gdf.crs is None or gdf.crs.is_geographic:
                    gdf = gdf.to_crs(epsg=crs_epsg)
            
            # 进行YJJBNTBHTB和管理边界划定成果图层的相交操作
            self.progress.emit(60, "正在进行图层相交操作...")
            intersection = gpd.overlay(gdf_yjjb, gdf_glbj, how='intersection')
            
            # 计算相交后的面积（平方米）和扣除系数面积
            self.progress.emit(65, "正在计算面积...")
            intersection['area_m2'] = intersection.geometry.area
            intersection['HSHKCXS'] = pd.to_numeric(intersection['HSHKCXS'], errors='coerce')
            intersection['deduction_coefficient'] = 1 - intersection['HSHKCXS']
            intersection['deducted_area_m2'] = intersection['area_m2'] * intersection['deduction_coefficient']
            
            # 计算管理边界划定成果图层的面积和扣除系数面积
            gdf_glbj['area_m2'] = gdf_glbj.geometry.area
            gdf_glbj['HSHKCXS'] = pd.to_numeric(gdf_glbj['HSHKCXS'], errors='coerce')
            gdf_glbj['deduction_coefficient'] = 1 - gdf_glbj['HSHKCXS']
            gdf_glbj['deducted_area_m2'] = gdf_glbj['area_m2'] * gdf_glbj['deduction_coefficient']
            
            # 计算DLTB图层中TKJ_DLBM LIKE "01%"的面积和扣除系数面积
            gdf_dltb['area_m2'] = gdf_dltb.geometry.area
            gdf_dltb['KCXS'] = pd.to_numeric(gdf_dltb['KCXS'], errors='coerce')
            gdf_dltb['deduction_coefficient'] = 1 - gdf_dltb['KCXS']
            gdf_dltb['deducted_area_m2'] = gdf_dltb['area_m2'] * gdf_dltb['deduction_coefficient']
            
            # 计算LD图层的面积
            gdf_ld['area_m2'] = gdf_ld.geometry.area
            
            # 准备结果列表
            self.progress.emit(70, "正在准备统计结果...")
            results = []
            
            # 0. 计算永农调出面积（不含待整改）
            # 条件：DLTB图层中TKJ_DLBM字段内容LIKE "01%"，管理边界划定成果图层中HSHPDDL字段内容不为 LIKE "01%"，与YJJBNTLX字段内容为"YJJBNT"相交
            
            # 先筛选DLTB图层中TKJ_DLBM LIKE "01%"的图斑
            dltb_01 = gdf_dltb[gdf_dltb['TKJ_DLBM'].str.startswith('01', na=False)].copy()
            
            # 筛选YJJBNTBHTB图层中YJJBNTLX为"YJJBNT"的图斑
            yjjb_ynt = gdf_yjjb[gdf_yjjb['YJJBNTLX'] == 'YJJBNT'].copy()
            
            # 筛选管理边界划定成果图层中HSHPDDL不为LIKE "01%"的图斑
            glbj_not_01 = gdf_glbj[~gdf_glbj['HSHPDDL'].str.startswith('01', na=False)].copy()
            
            # 进行三个图层的相交操作
            intersection_dltb_yjjb = gpd.overlay(dltb_01, yjjb_ynt, how='intersection')
            intersection_all = gpd.overlay(intersection_dltb_yjjb, glbj_not_01, how='intersection')
            
            # 计算相交后的面积（平方米）
            intersection_all['area_m2'] = intersection_all.geometry.area
            
            # 计算扣除系数面积，使用DLTB图层的KCXS字段
            intersection_all['KCXS'] = pd.to_numeric(intersection_all['KCXS'], errors='coerce')
            intersection_all['deduction_coefficient'] = 1 - intersection_all['KCXS']
            intersection_all['deducted_area_m2'] = intersection_all['area_m2'] * intersection_all['deduction_coefficient']
            
            # 计算永农调出面积
            area_m2_yongnong_out = intersection_all['area_m2'].sum()
            area_mu_yongnong_out = area_m2_yongnong_out / 666.6666667
            area_wanmu_yongnong_out = area_mu_yongnong_out / 10000
            
            deducted_area_m2_yongnong_out = intersection_all['deducted_area_m2'].sum()
            deducted_area_mu_yongnong_out = deducted_area_m2_yongnong_out / 666.6666667
            deducted_area_wanmu_yongnong_out = deducted_area_mu_yongnong_out / 10000
            
            results.append({
                '项目名称': '永农调出面积（不含待整改）',
                '面积(平方米)': area_m2_yongnong_out,
                '面积(亩)': area_mu_yongnong_out,
                '面积(万亩)': area_wanmu_yongnong_out,
                '扣除系数面积(平方米)': deducted_area_m2_yongnong_out,
                '扣除系数面积(亩)': deducted_area_mu_yongnong_out,
                '扣除系数面积(万亩)': deducted_area_wanmu_yongnong_out
            })
            
            # 1. 计算24"一上"耕地面积（DLTB图层中TKJ_DLBM LIKE "01%"）
            cond_dltb_01 = gdf_dltb['TKJ_DLBM'].str.startswith('01', na=False)
            area_m2_dltb_01 = gdf_dltb[cond_dltb_01]['area_m2'].sum()
            deducted_area_m2_dltb_01 = gdf_dltb[cond_dltb_01]['deducted_area_m2'].sum()
            area_mu_dltb_01 = area_m2_dltb_01 / 666.6666667
            deducted_area_mu_dltb_01 = deducted_area_m2_dltb_01 / 666.6666667
            area_wanmu_dltb_01 = area_mu_dltb_01 / 10000
            deducted_area_wanmu_dltb_01 = deducted_area_mu_dltb_01 / 10000
            results.append({
                '项目名称': '24"一上"耕地面积',
                '面积(平方米)': area_m2_dltb_01,
                '面积(亩)': area_mu_dltb_01,
                '面积(万亩)': area_wanmu_dltb_01,
                '扣除系数面积(平方米)': deducted_area_m2_dltb_01,
                '扣除系数面积(亩)': deducted_area_mu_dltb_01,
                '扣除系数面积(万亩)': deducted_area_wanmu_dltb_01
            })
            
            # 2. 计算24"一上"永农面积（含待整改，不含预调出）
            cond1 = intersection['YJJBNTLX'].isin(['YJJBNT', 'YTC_DZG'])
            area_m2_1 = intersection[cond1]['area_m2'].sum()
            deducted_area_m2_1 = intersection[cond1]['deducted_area_m2'].sum()
            area_mu_1 = area_m2_1 / 666.6666667
            deducted_area_mu_1 = deducted_area_m2_1 / 666.6666667
            area_wanmu_1 = area_mu_1 / 10000
            deducted_area_wanmu_1 = deducted_area_mu_1 / 10000
            results.append({
                '项目名称': '24"一上"永农面积（含待整改，不含预调出）',
                '面积(平方米)': area_m2_1,
                '面积(亩)': area_mu_1,
                '面积(万亩)': area_wanmu_1,
                '扣除系数面积(平方米)': deducted_area_m2_1,
                '扣除系数面积(亩)': deducted_area_mu_1,
                '扣除系数面积(万亩)': deducted_area_wanmu_1
            })
            
            # 3. 计算24"一上"永农面积（不含待整改，不含预调出）
            cond2 = intersection['YJJBNTLX'] == 'YJJBNT'
            area_m2_2 = intersection[cond2]['area_m2'].sum()
            deducted_area_m2_2 = intersection[cond2]['deducted_area_m2'].sum()
            area_mu_2 = area_m2_2 / 666.6666667
            deducted_area_mu_2 = deducted_area_m2_2 / 666.6666667
            area_wanmu_2 = area_mu_2 / 10000
            deducted_area_wanmu_2 = deducted_area_mu_2 / 10000
            results.append({
                '项目名称': '24"一上"永农面积（不含待整改，不含预调出）',
                '面积(平方米)': area_m2_2,
                '面积(亩)': area_mu_2,
                '面积(万亩)': area_wanmu_2,
                '扣除系数面积(平方米)': deducted_area_m2_2,
                '扣除系数面积(亩)': deducted_area_mu_2,
                '扣除系数面积(万亩)': deducted_area_wanmu_2
            })
            
            # 4. 计算置换一批耕地面积（仅统计【管理边界划定成果】图层）
            cond3 = (gdf_glbj['ZHLX'] == '1') | (gdf_glbj['ZHLX'] == '0')
            area_m2_3 = gdf_glbj[cond3]['area_m2'].sum()
            deducted_area_m2_3 = gdf_glbj[cond3]['deducted_area_m2'].sum()
            area_mu_3 = area_m2_3 / 666.6666667
            deducted_area_mu_3 = deducted_area_m2_3 / 666.6666667
            area_wanmu_3 = area_mu_3 / 10000
            deducted_area_wanmu_3 = deducted_area_mu_3 / 10000
            results.append({
                '项目名称': '置换一批耕地面积',
                '面积(平方米)': area_m2_3,
                '面积(亩)': area_mu_3,
                '面积(万亩)': area_wanmu_3,
                '扣除系数面积(平方米)': deducted_area_m2_3,
                '扣除系数面积(亩)': deducted_area_mu_3,
                '扣除系数面积(万亩)': deducted_area_wanmu_3
            })
            
            # 5. 计算置换一批永农面积（含待整改，不含预调出）
            cond4 = (intersection['YJJBNTLX'].isin(['YJJBNT', 'YTC_DZG'])) & ((intersection['ZHLX'] == '1') | (intersection['ZHLX'] == '0'))
            area_m2_4 = intersection[cond4]['area_m2'].sum()
            deducted_area_m2_4 = intersection[cond4]['deducted_area_m2'].sum()
            area_mu_4 = area_m2_4 / 666.6666667
            deducted_area_mu_4 = deducted_area_m2_4 / 666.6666667
            area_wanmu_4 = area_mu_4 / 10000
            deducted_area_wanmu_4 = deducted_area_mu_4 / 10000
            results.append({
                '项目名称': '置换一批永农面积（含待整改，不含预调出）',
                '面积(平方米)': area_m2_4,
                '面积(亩)': area_mu_4,
                '面积(万亩)': area_wanmu_4,
                '扣除系数面积(平方米)': deducted_area_m2_4,
                '扣除系数面积(亩)': deducted_area_mu_4,
                '扣除系数面积(万亩)': deducted_area_wanmu_4
            })
            
            # 6. 计算置换一批永农面积（不含待整改，不含预调出）
            cond5 = (intersection['YJJBNTLX'] == 'YJJBNT') & ((intersection['ZHLX'] == '1') | (intersection['ZHLX'] == '0'))
            area_m2_5 = intersection[cond5]['area_m2'].sum()
            deducted_area_m2_5 = intersection[cond5]['deducted_area_m2'].sum()
            area_mu_5 = area_m2_5 / 666.6666667
            deducted_area_mu_5 = deducted_area_m2_5 / 666.6666667
            area_wanmu_5 = area_mu_5 / 10000
            deducted_area_wanmu_5 = deducted_area_mu_5 / 10000
            results.append({
                '项目名称': '置换一批永农面积（不含待整改，不含预调出）',
                '面积(平方米)': area_m2_5,
                '面积(亩)': area_mu_5,
                '面积(万亩)': area_wanmu_5,
                '扣除系数面积(平方米)': deducted_area_m2_5,
                '扣除系数面积(亩)': deducted_area_mu_5,
                '扣除系数面积(万亩)': deducted_area_wanmu_5
            })
            
            # 7. 计算保留一批耕地面积（仅统计【管理边界划定成果】图层）
            cond6 = gdf_glbj['CLLX'] == '11'
            area_m2_6 = gdf_glbj[cond6]['area_m2'].sum()
            deducted_area_m2_6 = gdf_glbj[cond6]['deducted_area_m2'].sum()
            area_mu_6 = area_m2_6 / 666.6666667
            deducted_area_mu_6 = deducted_area_m2_6 / 666.6666667
            area_wanmu_6 = area_mu_6 / 10000
            deducted_area_wanmu_6 = deducted_area_mu_6 / 10000
            results.append({
                '项目名称': '保留一批耕地面积',
                '面积(平方米)': area_m2_6,
                '面积(亩)': area_mu_6,
                '面积(万亩)': area_wanmu_6,
                '扣除系数面积(平方米)': deducted_area_m2_6,
                '扣除系数面积(亩)': deducted_area_mu_6,
                '扣除系数面积(万亩)': deducted_area_wanmu_6
            })
            
            # 8. 计算保留一批永农面积（含待整改，不含预调出）
            cond7 = (intersection['YJJBNTLX'].isin(['YJJBNT', 'YTC_DZG'])) & (intersection['CLLX'] == '11') & ~((intersection['ZHLX'] == '1') | (intersection['ZHLX'] == '0'))
            area_m2_7 = intersection[cond7]['area_m2'].sum()
            deducted_area_m2_7 = intersection[cond7]['deducted_area_m2'].sum()
            area_mu_7 = area_m2_7 / 666.6666667
            deducted_area_mu_7 = deducted_area_m2_7 / 666.6666667
            area_wanmu_7 = area_mu_7 / 10000
            deducted_area_wanmu_7 = deducted_area_mu_7 / 10000
            results.append({
                '项目名称': '保留一批永农面积（含待整改，不含预调出）',
                '面积(平方米)': area_m2_7,
                '面积(亩)': area_mu_7,
                '面积(万亩)': area_wanmu_7,
                '扣除系数面积(平方米)': deducted_area_m2_7,
                '扣除系数面积(亩)': deducted_area_mu_7,
                '扣除系数面积(万亩)': deducted_area_wanmu_7
            })
            
            # 9. 计算保留一批永农面积（不含待整改、不含预调出）
            cond8 = (intersection['YJJBNTLX'] == 'YJJBNT') & (intersection['CLLX'] == '11') & ~((intersection['ZHLX'] == '1') | (intersection['ZHLX'] == '0'))
            area_m2_8 = intersection[cond8]['area_m2'].sum()
            deducted_area_m2_8 = intersection[cond8]['deducted_area_m2'].sum()
            area_mu_8 = area_m2_8 / 666.6666667
            deducted_area_mu_8 = deducted_area_m2_8 / 666.6666667
            area_wanmu_8 = area_mu_8 / 10000
            deducted_area_wanmu_8 = deducted_area_mu_8 / 10000
            results.append({
                '项目名称': '保留一批永农面积（不含待整改、不含预调出）',
                '面积(平方米)': area_m2_8,
                '面积(亩)': area_mu_8,
                '面积(万亩)': area_wanmu_8,
                '扣除系数面积(平方米)': deducted_area_m2_8,
                '扣除系数面积(亩)': deducted_area_mu_8,
                '扣除系数面积(万亩)': deducted_area_wanmu_8
            })
            
            # 10. 计算认定一批耕地面积（仅统计【管理边界划定成果】图层）
            cond9 = gdf_glbj['CLLX'] == '12'
            area_m2_9 = gdf_glbj[cond9]['area_m2'].sum()
            deducted_area_m2_9 = gdf_glbj[cond9]['deducted_area_m2'].sum()
            area_mu_9 = area_m2_9 / 666.6666667
            deducted_area_mu_9 = deducted_area_m2_9 / 666.6666667
            area_wanmu_9 = area_mu_9 / 10000
            deducted_area_wanmu_9 = deducted_area_mu_9 / 10000
            results.append({
                '项目名称': '认定一批耕地面积',
                '面积(平方米)': area_m2_9,
                '面积(亩)': area_mu_9,
                '面积(万亩)': area_wanmu_9,
                '扣除系数面积(平方米)': deducted_area_m2_9,
                '扣除系数面积(亩)': deducted_area_mu_9,
                '扣除系数面积(万亩)': deducted_area_wanmu_9
            })
            
            # 11. 计算认定一批永农面积（含待整改，不含预调出）
            cond10 = (intersection['YJJBNTLX'].isin(['YJJBNT', 'YTC_DZG'])) & (intersection['CLLX'] == '12')
            area_m2_10 = intersection[cond10]['area_m2'].sum()
            deducted_area_m2_10 = intersection[cond10]['deducted_area_m2'].sum()
            area_mu_10 = area_m2_10 / 666.6666667
            deducted_area_mu_10 = deducted_area_m2_10 / 666.6666667
            area_wanmu_10 = area_mu_10 / 10000
            deducted_area_wanmu_10 = deducted_area_mu_10 / 10000
            results.append({
                '项目名称': '认定一批永农面积（含待整改，不含预调出）',
                '面积(平方米)': area_m2_10,
                '面积(亩)': area_mu_10,
                '面积(万亩)': area_wanmu_10,
                '扣除系数面积(平方米)': deducted_area_m2_10,
                '扣除系数面积(亩)': deducted_area_mu_10,
                '扣除系数面积(万亩)': deducted_area_wanmu_10
            })
            
            # 12. 计算认定一批永农面积（不含待整改、不含预调出）
            cond11 = (intersection['YJJBNTLX'] == 'YJJBNT') & (intersection['CLLX'] == '12')
            area_m2_11 = intersection[cond11]['area_m2'].sum()
            deducted_area_m2_11 = intersection[cond11]['deducted_area_m2'].sum()
            area_mu_11 = area_m2_11 / 666.6666667
            deducted_area_mu_11 = deducted_area_m2_11 / 666.6666667
            area_wanmu_11 = area_mu_11 / 10000
            deducted_area_wanmu_11 = deducted_area_mu_11 / 10000
            results.append({
                '项目名称': '认定一批永农面积（不含待整改、不含预调出）',
                '面积(平方米)': area_m2_11,
                '面积(亩)': area_mu_11,
                '面积(万亩)': area_wanmu_11,
                '扣除系数面积(平方米)': deducted_area_m2_11,
                '扣除系数面积(亩)': deducted_area_mu_11,
                '扣除系数面积(万亩)': deducted_area_wanmu_11
            })
            
            # 13. 计算恢复一批耕地面积（仅统计【管理边界划定成果】图层）
            cond12 = gdf_glbj['CLLX'] == '13'
            area_m2_12 = gdf_glbj[cond12]['area_m2'].sum()
            deducted_area_m2_12 = gdf_glbj[cond12]['deducted_area_m2'].sum()
            area_mu_12 = area_m2_12 / 666.6666667
            deducted_area_mu_12 = deducted_area_m2_12 / 666.6666667
            area_wanmu_12 = area_mu_12 / 10000
            deducted_area_wanmu_12 = deducted_area_mu_12 / 10000
            results.append({
                '项目名称': '恢复一批耕地面积',
                '面积(平方米)': area_m2_12,
                '面积(亩)': area_mu_12,
                '面积(万亩)': area_wanmu_12,
                '扣除系数面积(平方米)': deducted_area_m2_12,
                '扣除系数面积(亩)': deducted_area_mu_12,
                '扣除系数面积(万亩)': deducted_area_wanmu_12
            })
            
            # 14. 计算恢复一批永农面积（含待整改，不含预调出）
            cond13 = (intersection['YJJBNTLX'].isin(['YJJBNT', 'YTC_DZG'])) & (intersection['CLLX'] == '13')
            area_m2_13 = intersection[cond13]['area_m2'].sum()
            deducted_area_m2_13 = intersection[cond13]['deducted_area_m2'].sum()
            area_mu_13 = area_m2_13 / 666.6666667
            deducted_area_mu_13 = deducted_area_m2_13 / 666.6666667
            area_wanmu_13 = area_mu_13 / 10000
            deducted_area_wanmu_13 = deducted_area_mu_13 / 10000
            results.append({
                '项目名称': '恢复一批永农面积（含待整改，不含预调出）',
                '面积(平方米)': area_m2_13,
                '面积(亩)': area_mu_13,
                '面积(万亩)': area_wanmu_13,
                '扣除系数面积(平方米)': deducted_area_m2_13,
                '扣除系数面积(亩)': deducted_area_mu_13,
                '扣除系数面积(万亩)': deducted_area_wanmu_13
            })
            
            # 15. 计算恢复一批永农面积（不含待整改，不含预调出）
            cond14 = (intersection['YJJBNTLX'] == 'YJJBNT') & (intersection['CLLX'] == '13')
            area_m2_14 = intersection[cond14]['area_m2'].sum()
            deducted_area_m2_14 = intersection[cond14]['deducted_area_m2'].sum()
            area_mu_14 = area_m2_14 / 666.6666667
            deducted_area_mu_14 = deducted_area_m2_14 / 666.6666667
            area_wanmu_14 = area_mu_14 / 10000
            deducted_area_wanmu_14 = deducted_area_mu_14 / 10000
            results.append({
                '项目名称': '恢复一批永农面积（不含待整改，不含预调出）',
                '面积(平方米)': area_m2_14,
                '面积(亩)': area_mu_14,
                '面积(万亩)': area_wanmu_14,
                '扣除系数面积(平方米)': deducted_area_m2_14,
                '扣除系数面积(亩)': deducted_area_mu_14,
                '扣除系数面积(万亩)': deducted_area_wanmu_14
            })
            
            # 16. 计算耕地边界试划面积（保留一批耕地面积+认定一批耕地面积+恢复一批耕地面积+置换一批耕地面积-置换一批耕地面积）
            # 简化后为：保留一批耕地面积+认定一批耕地面积+恢复一批耕地面积
            area_m2_15 = area_m2_6 + area_m2_9 + area_m2_12
            deducted_area_m2_15 = deducted_area_m2_6 + deducted_area_m2_9 + deducted_area_m2_12
            area_mu_15 = area_m2_15 / 666.6666667
            deducted_area_mu_15 = deducted_area_m2_15 / 666.6666667
            area_wanmu_15 = area_mu_15 / 10000
            deducted_area_wanmu_15 = deducted_area_mu_15 / 10000
            results.append({
                '项目名称': '耕地边界试划面积',
                '面积(平方米)': area_m2_15,
                '面积(亩)': area_mu_15,
                '面积(万亩)': area_wanmu_15,
                '扣除系数面积(平方米)': deducted_area_m2_15,
                '扣除系数面积(亩)': deducted_area_mu_15,
                '扣除系数面积(万亩)': deducted_area_wanmu_15
            })
            
            # 17. 计算耕地耕地后备资源面积标注一批（仅统计【管理边界划定成果】图层）
            # 根据用户需求，后备耕地标注一批不要扣除系数
            cond16 = gdf_glbj['GLBJLX'] == '40'
            area_m2_16 = gdf_glbj[cond16]['area_m2'].sum()
            # 不扣除系数，直接使用原始面积
            deducted_area_m2_16 = area_m2_16
            area_mu_16 = area_m2_16 / 666.6666667
            # 不扣除系数，直接使用原始面积
            deducted_area_mu_16 = area_mu_16
            area_wanmu_16 = area_mu_16 / 10000
            # 不扣除系数，直接使用原始面积
            deducted_area_wanmu_16 = area_wanmu_16
            results.append({
                '项目名称': '耕地耕地后备资源面积标注一批',
                '面积(平方米)': area_m2_16,
                '面积(亩)': area_mu_16,
                '面积(万亩)': area_wanmu_16,
                '扣除系数面积(平方米)': deducted_area_m2_16,
                '扣除系数面积(亩)': deducted_area_mu_16,
                '扣除系数面积(万亩)': deducted_area_wanmu_16
            })
            
            # 18. 计算林地一张图面积（仅统计【LD】图层）
            area_m2_ld = gdf_ld['area_m2'].sum()
            area_mu_ld = area_m2_ld / 666.6666667
            area_wanmu_ld = area_mu_ld / 10000
            # LD图层没有扣除系数，所以扣除系数面积和原始面积相同
            results.append({
                '项目名称': '林地一张图面积',
                '面积(平方米)': area_m2_ld,
                '面积(亩)': area_mu_ld,
                '面积(万亩)': area_wanmu_ld,
                '扣除系数面积(平方米)': area_m2_ld,
                '扣除系数面积(亩)': area_mu_ld,
                '扣除系数面积(万亩)': area_wanmu_ld
            })
            
            # 19. 计算保留一批林地面积（仅统计【管理边界划定成果】图层）
            cond19 = gdf_glbj['CLLX'] == '21'
            area_m2_19 = gdf_glbj[cond19]['area_m2'].sum()
            deducted_area_m2_19 = gdf_glbj[cond19]['deducted_area_m2'].sum()
            area_mu_19 = area_m2_19 / 666.6666667
            deducted_area_mu_19 = deducted_area_m2_19 / 666.6666667
            area_wanmu_19 = area_mu_19 / 10000
            deducted_area_wanmu_19 = deducted_area_mu_19 / 10000
            results.append({
                '项目名称': '保留一批林地面积',
                '面积(平方米)': area_m2_19,
                '面积(亩)': area_mu_19,
                '面积(万亩)': area_wanmu_19,
                '扣除系数面积(平方米)': deducted_area_m2_19,
                '扣除系数面积(亩)': deducted_area_mu_19,
                '扣除系数面积(万亩)': deducted_area_wanmu_19
            })
            
            # 20. 计算认定一批林地面积（仅统计【管理边界划定成果】图层）
            cond20 = gdf_glbj['CLLX'] == '22'
            area_m2_20 = gdf_glbj[cond20]['area_m2'].sum()
            deducted_area_m2_20 = gdf_glbj[cond20]['deducted_area_m2'].sum()
            area_mu_20 = area_m2_20 / 666.6666667
            deducted_area_mu_20 = deducted_area_m2_20 / 666.6666667
            area_wanmu_20 = area_mu_20 / 10000
            deducted_area_wanmu_20 = deducted_area_mu_20 / 10000
            results.append({
                '项目名称': '认定一批林地面积',
                '面积(平方米)': area_m2_20,
                '面积(亩)': area_mu_20,
                '面积(万亩)': area_wanmu_20,
                '扣除系数面积(平方米)': deducted_area_m2_20,
                '扣除系数面积(亩)': deducted_area_mu_20,
                '扣除系数面积(万亩)': deducted_area_wanmu_20
            })
            
            # 21. 计算恢复一批林地面积（仅统计【管理边界划定成果】图层）
            cond21 = gdf_glbj['CLLX'] == '23'
            area_m2_21 = gdf_glbj[cond21]['area_m2'].sum()
            deducted_area_m2_21 = gdf_glbj[cond21]['deducted_area_m2'].sum()
            area_mu_21 = area_m2_21 / 666.6666667
            deducted_area_mu_21 = deducted_area_m2_21 / 666.6666667
            area_wanmu_21 = area_mu_21 / 10000
            deducted_area_wanmu_21 = deducted_area_mu_21 / 10000
            results.append({
                '项目名称': '恢复一批林地面积',
                '面积(平方米)': area_m2_21,
                '面积(亩)': area_mu_21,
                '面积(万亩)': area_wanmu_21,
                '扣除系数面积(平方米)': deducted_area_m2_21,
                '扣除系数面积(亩)': deducted_area_mu_21,
                '扣除系数面积(万亩)': deducted_area_wanmu_21
            })
            
            # 22. 计算置换一批林地面积（仅统计【管理边界划定成果】图层）
            cond22 = gdf_glbj['ZHLX'] == '2'
            area_m2_22 = gdf_glbj[cond22]['area_m2'].sum()
            deducted_area_m2_22 = gdf_glbj[cond22]['deducted_area_m2'].sum()
            area_mu_22 = area_m2_22 / 666.6666667
            deducted_area_mu_22 = deducted_area_m2_22 / 666.6666667
            area_wanmu_22 = area_mu_22 / 10000
            deducted_area_wanmu_22 = deducted_area_mu_22 / 10000
            results.append({
                '项目名称': '置换一批林地面积',
                '面积(平方米)': area_m2_22,
                '面积(亩)': area_mu_22,
                '面积(万亩)': area_wanmu_22,
                '扣除系数面积(平方米)': deducted_area_m2_22,
                '扣除系数面积(亩)': deducted_area_mu_22,
                '扣除系数面积(万亩)': deducted_area_wanmu_22
            })
            
            # 23. 计算保留一批园地面积（即为园地试划面积）（仅统计【管理边界划定成果】图层）
            cond23 = gdf_glbj['CLLX'] == '31'
            area_m2_23 = gdf_glbj[cond23]['area_m2'].sum()
            deducted_area_m2_23 = gdf_glbj[cond23]['deducted_area_m2'].sum()
            area_mu_23 = area_m2_23 / 666.6666667
            deducted_area_mu_23 = deducted_area_m2_23 / 666.6666667
            area_wanmu_23 = area_mu_23 / 10000
            deducted_area_wanmu_23 = deducted_area_mu_23 / 10000
            results.append({
                '项目名称': '保留一批园地面积（即为园地试划面积）',
                '面积(平方米)': area_m2_23,
                '面积(亩)': area_mu_23,
                '面积(万亩)': area_wanmu_23,
                '扣除系数面积(平方米)': deducted_area_m2_23,
                '扣除系数面积(亩)': deducted_area_mu_23,
                '扣除系数面积(万亩)': deducted_area_wanmu_23
            })
            
            # 24. 计算林地国土绿化空间标注一批（仅统计【管理边界划定成果】图层）
            cond24 = gdf_glbj['GLBJLX'] == '50'
            area_m2_24 = gdf_glbj[cond24]['area_m2'].sum()
            deducted_area_m2_24 = gdf_glbj[cond24]['deducted_area_m2'].sum()
            area_mu_24 = area_m2_24 / 666.6666667
            deducted_area_mu_24 = deducted_area_m2_24 / 666.6666667
            area_wanmu_24 = area_mu_24 / 10000
            deducted_area_wanmu_24 = deducted_area_mu_24 / 10000
            results.append({
                '项目名称': '林地国土绿化空间标注一批',
                '面积(平方米)': area_m2_24,
                '面积(亩)': area_mu_24,
                '面积(万亩)': area_wanmu_24,
                '扣除系数面积(平方米)': deducted_area_m2_24,
                '扣除系数面积(亩)': deducted_area_mu_24,
                '扣除系数面积(万亩)': deducted_area_wanmu_24
            })
            
            # 25. 计算24"一上"园地面积（DLTB图层中TKJ_DLBM LIKE "02%"）
            cond25 = gdf_dltb['TKJ_DLBM'].str.startswith('02', na=False)
            area_m2_25 = gdf_dltb[cond25]['area_m2'].sum()
            deducted_area_m2_25 = gdf_dltb[cond25]['deducted_area_m2'].sum()
            area_mu_25 = area_m2_25 / 666.6666667
            deducted_area_mu_25 = deducted_area_m2_25 / 666.6666667
            area_wanmu_25 = area_mu_25 / 10000
            deducted_area_wanmu_25 = deducted_area_mu_25 / 10000
            results.append({
                '项目名称': '24"一上"园地面积',
                '面积(平方米)': area_m2_25,
                '面积(亩)': area_mu_25,
                '面积(万亩)': area_wanmu_25,
                '扣除系数面积(平方米)': deducted_area_m2_25,
                '扣除系数面积(亩)': deducted_area_mu_25,
                '扣除系数面积(万亩)': deducted_area_wanmu_25
            })
            
            # 26-30. 计算试划耕地坡度各级面积（仅统计【管理边界划定成果】图层）
            # 确保HSHPDJB是数值类型
            gdf_glbj['HSHPDJB'] = pd.to_numeric(gdf_glbj['HSHPDJB'], errors='coerce')
            
            # 坡度1级
            cond26 = (gdf_glbj['GLBJLX'] == '10') & (gdf_glbj['HSHPDJB'] == 1)
            area_m2_26 = gdf_glbj[cond26]['area_m2'].sum()
            deducted_area_m2_26 = gdf_glbj[cond26]['deducted_area_m2'].sum()
            area_mu_26 = area_m2_26 / 666.6666667
            deducted_area_mu_26 = deducted_area_m2_26 / 666.6666667
            area_wanmu_26 = area_mu_26 / 10000
            deducted_area_wanmu_26 = deducted_area_mu_26 / 10000
            results.append({
                '项目名称': '试划耕地坡度1级',
                '面积(平方米)': area_m2_26,
                '面积(亩)': area_mu_26,
                '面积(万亩)': area_wanmu_26,
                '扣除系数面积(平方米)': deducted_area_m2_26,
                '扣除系数面积(亩)': deducted_area_mu_26,
                '扣除系数面积(万亩)': deducted_area_wanmu_26
            })
            
            # 坡度2级
            cond27 = (gdf_glbj['GLBJLX'] == '10') & (gdf_glbj['HSHPDJB'] == 2)
            area_m2_27 = gdf_glbj[cond27]['area_m2'].sum()
            deducted_area_m2_27 = gdf_glbj[cond27]['deducted_area_m2'].sum()
            area_mu_27 = area_m2_27 / 666.6666667
            deducted_area_mu_27 = deducted_area_m2_27 / 666.6666667
            area_wanmu_27 = area_mu_27 / 10000
            deducted_area_wanmu_27 = deducted_area_mu_27 / 10000
            results.append({
                '项目名称': '试划耕地坡度2级',
                '面积(平方米)': area_m2_27,
                '面积(亩)': area_mu_27,
                '面积(万亩)': area_wanmu_27,
                '扣除系数面积(平方米)': deducted_area_m2_27,
                '扣除系数面积(亩)': deducted_area_mu_27,
                '扣除系数面积(万亩)': deducted_area_wanmu_27
            })
            
            # 坡度3级
            cond28 = (gdf_glbj['GLBJLX'] == '10') & (gdf_glbj['HSHPDJB'] == 3)
            area_m2_28 = gdf_glbj[cond28]['area_m2'].sum()
            deducted_area_m2_28 = gdf_glbj[cond28]['deducted_area_m2'].sum()
            area_mu_28 = area_m2_28 / 666.6666667
            deducted_area_mu_28 = deducted_area_m2_28 / 666.6666667
            area_wanmu_28 = area_mu_28 / 10000
            deducted_area_wanmu_28 = deducted_area_mu_28 / 10000
            results.append({
                '项目名称': '试划耕地坡度3级',
                '面积(平方米)': area_m2_28,
                '面积(亩)': area_mu_28,
                '面积(万亩)': area_wanmu_28,
                '扣除系数面积(平方米)': deducted_area_m2_28,
                '扣除系数面积(亩)': deducted_area_mu_28,
                '扣除系数面积(万亩)': deducted_area_wanmu_28
            })
            
            # 坡度4级
            cond29 = (gdf_glbj['GLBJLX'] == '10') & (gdf_glbj['HSHPDJB'] == 4)
            area_m2_29 = gdf_glbj[cond29]['area_m2'].sum()
            deducted_area_m2_29 = gdf_glbj[cond29]['deducted_area_m2'].sum()
            area_mu_29 = area_m2_29 / 666.6666667
            deducted_area_mu_29 = deducted_area_m2_29 / 666.6666667
            area_wanmu_29 = area_mu_29 / 10000
            deducted_area_wanmu_29 = deducted_area_mu_29 / 10000
            results.append({
                '项目名称': '试划耕地坡度4级',
                '面积(平方米)': area_m2_29,
                '面积(亩)': area_mu_29,
                '面积(万亩)': area_wanmu_29,
                '扣除系数面积(平方米)': deducted_area_m2_29,
                '扣除系数面积(亩)': deducted_area_mu_29,
                '扣除系数面积(万亩)': deducted_area_wanmu_29
            })
            
            # 坡度5级
            cond30 = (gdf_glbj['GLBJLX'] == '10') & (gdf_glbj['HSHPDJB'] == 5)
            area_m2_30 = gdf_glbj[cond30]['area_m2'].sum()
            deducted_area_m2_30 = gdf_glbj[cond30]['deducted_area_m2'].sum()
            area_mu_30 = area_m2_30 / 666.6666667
            deducted_area_mu_30 = deducted_area_m2_30 / 666.6666667
            area_wanmu_30 = area_mu_30 / 10000
            deducted_area_wanmu_30 = deducted_area_mu_30 / 10000
            results.append({
                '项目名称': '试划耕地坡度5级',
                '面积(平方米)': area_m2_30,
                '面积(亩)': area_mu_30,
                '面积(万亩)': area_wanmu_30,
                '扣除系数面积(平方米)': deducted_area_m2_30,
                '扣除系数面积(亩)': deducted_area_mu_30,
                '扣除系数面积(万亩)': deducted_area_wanmu_30
            })
            
            # 31-34. 计算不同坡度范围的总面积
            # 6度以下总面积（坡度1级+坡度2级）
            area_m2_31 = area_m2_26 + area_m2_27
            deducted_area_m2_31 = deducted_area_m2_26 + deducted_area_m2_27
            area_mu_31 = area_m2_31 / 666.6666667
            deducted_area_mu_31 = deducted_area_m2_31 / 666.6666667
            area_wanmu_31 = area_mu_31 / 10000
            deducted_area_wanmu_31 = deducted_area_mu_31 / 10000
            results.append({
                '项目名称': '试划耕地坡度6度以下总面积',
                '面积(平方米)': area_m2_31,
                '面积(亩)': area_mu_31,
                '面积(万亩)': area_wanmu_31,
                '扣除系数面积(平方米)': deducted_area_m2_31,
                '扣除系数面积(亩)': deducted_area_mu_31,
                '扣除系数面积(万亩)': deducted_area_wanmu_31
            })
            
            # 6-15度总面积（含6度，不含15度）（坡度3级）
            results.append({
                '项目名称': '试划耕地坡度6-15度总面积（含6度，不含15度）',
                '面积(平方米)': area_m2_28,
                '面积(亩)': area_mu_28,
                '面积(万亩)': area_wanmu_28,
                '扣除系数面积(平方米)': deducted_area_m2_28,
                '扣除系数面积(亩)': deducted_area_mu_28,
                '扣除系数面积(万亩)': deducted_area_wanmu_28
            })
            
            # 15-25度总面积（含15度，不含25度）（坡度4级）
            results.append({
                '项目名称': '试划耕地坡度15-25度总面积（含15度，不含25度）',
                '面积(平方米)': area_m2_29,
                '面积(亩)': area_mu_29,
                '面积(万亩)': area_wanmu_29,
                '扣除系数面积(平方米)': deducted_area_m2_29,
                '扣除系数面积(亩)': deducted_area_mu_29,
                '扣除系数面积(万亩)': deducted_area_wanmu_29
            })
            
            # 25度以上总面积（坡度5级）
            results.append({
                '项目名称': '试划耕地坡度25度以上总面积',
                '面积(平方米)': area_m2_30,
                '面积(亩)': area_mu_30,
                '面积(万亩)': area_wanmu_30,
                '扣除系数面积(平方米)': deducted_area_m2_30,
                '扣除系数面积(亩)': deducted_area_mu_30,
                '扣除系数面积(万亩)': deducted_area_wanmu_30
            })
            
            # 35-36. 计算不同面积范围的农地总面积
            # 1亩以下农地总面积（面积小于666.667平方米）
            cond35 = (gdf_glbj['GLBJLX'] == '10') & (gdf_glbj['area_m2'] < 666.6666667)
            area_m2_35 = gdf_glbj[cond35]['area_m2'].sum()
            deducted_area_m2_35 = gdf_glbj[cond35]['deducted_area_m2'].sum()
            area_mu_35 = area_m2_35 / 666.6666667
            deducted_area_mu_35 = deducted_area_m2_35 / 666.6666667
            area_wanmu_35 = area_mu_35 / 10000
            deducted_area_wanmu_35 = deducted_area_mu_35 / 10000
            results.append({
                '项目名称': '1亩以下农地总面积',
                '面积(平方米)': area_m2_35,
                '面积(亩)': area_mu_35,
                '面积(万亩)': area_wanmu_35,
                '扣除系数面积(平方米)': deducted_area_m2_35,
                '扣除系数面积(亩)': deducted_area_mu_35,
                '扣除系数面积(万亩)': deducted_area_wanmu_35
            })
            
            # 3亩以下农地总面积（面积小于2000.001平方米）
            cond36 = (gdf_glbj['GLBJLX'] == '10') & (gdf_glbj['area_m2'] < 2000.001)
            area_m2_36 = gdf_glbj[cond36]['area_m2'].sum()
            deducted_area_m2_36 = gdf_glbj[cond36]['deducted_area_m2'].sum()
            area_mu_36 = area_m2_36 / 666.6666667
            deducted_area_mu_36 = deducted_area_m2_36 / 666.6666667
            area_wanmu_36 = area_mu_36 / 10000
            deducted_area_wanmu_36 = deducted_area_mu_36 / 10000
            results.append({
                '项目名称': '3亩以下农地总面积（只要面积小于3亩以下都要统计）',
                '面积(平方米)': area_m2_36,
                '面积(亩)': area_mu_36,
                '面积(万亩)': area_wanmu_36,
                '扣除系数面积(平方米)': deducted_area_m2_36,
                '扣除系数面积(亩)': deducted_area_mu_36,
                '扣除系数面积(万亩)': deducted_area_wanmu_36
            })
            
            # 创建结果DataFrame
            df_results = pd.DataFrame(results)
            
            # 输出到Excel文件
            self.progress.emit(80, "正在写入Excel文件...")
            
            # 使用openpyxl引擎写入，支持替换工作表
            with pd.ExcelWriter(self.output_excel, engine='openpyxl') as writer:
                # 写入Sheet1，替换整个工作表
                df_results.to_excel(writer, sheet_name='Sheet1', index=False)
            
            # 写入模板文件
            self.progress.emit(90, "正在写入模板文件...")
            if self.template_path:
                try:
                    # 创建一个结果字典，方便查找
                    result_dict = {row['项目名称']: row for _, row in df_results.iterrows()}
                    
                    # 复制模板文件到输出路径
                    import shutil
                    shutil.copy(self.template_path, self.output_excel)
                    
                    # 使用openpyxl引擎打开Excel文件（输出文件，已包含模板内容）
                    with pd.ExcelWriter(self.output_excel, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
                        # 获取工作表
                        worksheet = writer.book['试划成果总结']
                        
                        # 定义需要写入的项目和对应的单元格
                        write_items = [
                            ('24"一上"耕地面积', '扣除系数面积(万亩)', 'C11'),
                            ('24"一上"永农面积（含待整改，不含预调出）', '扣除系数面积(万亩)', 'D11'),
                            ('24"一上"永农面积（不含待整改，不含预调出）', '扣除系数面积(万亩)', 'E11'),
                            ('置换一批耕地面积', '扣除系数面积(万亩)', 'O11'),
                            ('置换一批永农面积（含待整改，不含预调出）', '扣除系数面积(万亩)', 'P11'),
                            ('置换一批永农面积（不含待整改，不含预调出）', '扣除系数面积(万亩)', 'Q11'),
                            ('保留一批耕地面积', '扣除系数面积(万亩)', 'F11'),
                            ('保留一批永农面积（含待整改，不含预调出）', '扣除系数面积(万亩)', 'G11'),
                            ('保留一批永农面积（不含待整改、不含预调出）', '扣除系数面积(万亩)', 'H11'),
                            ('认定一批耕地面积', '扣除系数面积(万亩)', 'I11'),
                            ('认定一批永农面积（含待整改，不含预调出）', '扣除系数面积(万亩)', 'J11'),
                            ('认定一批永农面积（不含待整改、不含预调出）', '扣除系数面积(万亩)', 'K11'),
                            ('恢复一批耕地面积', '扣除系数面积(万亩)', 'L11'),
                            ('恢复一批永农面积（含待整改，不含预调出）', '扣除系数面积(万亩)', 'M11'),
                            ('恢复一批永农面积（不含待整改，不含预调出）', '扣除系数面积(万亩)', 'N11'),
                            ('耕地耕地后备资源面积标注一批', '扣除系数面积(万亩)', 'X11'),
                            ('林地一张图面积', '面积(万亩)', 'Z11'),
                            ('保留一批林地面积', '面积(万亩)', 'AA11'),
                            ('认定一批林地面积', '面积(万亩)', 'AB11'),
                            ('恢复一批林地面积', '面积(万亩)', 'AC11'),
                            ('置换一批林地面积', '面积(万亩)', 'AD11'),
                            ('保留一批园地面积（即为园地试划面积）', '面积(万亩)', 'AJ11'),
                            ('林地国土绿化空间标注一批', '面积(万亩)', 'AH11'),
                            ('试划耕地坡度6度以下总面积', '扣除系数面积(万亩)', 'F29'),
                            ('试划耕地坡度6-15度总面积（含6度，不含15度）', '扣除系数面积(万亩)', 'I29'),
                            ('试划耕地坡度15-25度总面积（含15度，不含25度）', '扣除系数面积(万亩)', 'O29'),
                            ('试划耕地坡度25度以上总面积', '扣除系数面积(万亩)', 'R29'),
                            ('1亩以下农地总面积', '扣除系数面积(万亩)', 'W29'),
                            ('3亩以下农地总面积（只要面积小于3亩以下都要统计）', '扣除系数面积(万亩)', 'Y29'),
                            ('永农调出面积（不含待整改）', '扣除系数面积(万亩)', 'C29')
                        ]
                        
                        # 写入数据到指定单元格
                        for project_name, value_column, cell in write_items:
                            if project_name in result_dict:
                                value = result_dict[project_name][value_column]
                                worksheet[cell] = round(value, 2)
                        
                        # 处理Sheet1：先删除旧的，再添加新的
                        if 'Sheet1' in writer.book.sheetnames:
                            # 删除旧的Sheet1
                            writer.book.remove(writer.book['Sheet1'])
                        # 添加新的Sheet1
                        df_results.to_excel(writer, sheet_name='Sheet1', index=False)
                except Exception as e:
                    self.error.emit(f"写入模板文件失败: {str(e)}")
            
            self.progress.emit(100, "统计完成")
            self.success.emit(f"试划成果总结统计完成，结果已保存至：{self.output_excel}")
            
        except Exception as e:
            self.error.emit(f"程序执行出错: {str(e)}")
            import traceback
            traceback.print_exc()


class TrialPlanSummaryFunction(BaseFunction):
    """试划成果总结统计功能"""
    
    def __init__(self, parent=None):
        description = (
            "📢 <b>功能说明：</b><br>"
            "管理边界相交面积计算表1，用于统计试划成果总结数据<br>"
            "支持GDB文件输入，自动计算各类面积指标并生成统计报表"
        )
        super().__init__("试划成果总结统计", description, parent)
        
        self.gdb_path = ""
        self.template_path = ""
        self.thread = None
        
        self._initUI()
        
    def _initUI(self):
        """初始化UI"""
        # GDB文件选择
        self._addFileSelector()
        
        # 模板文件选择
        self._addTemplateSelector()
        
        # 输出文件由系统自动生成，不需要用户选择
        
        # 添加执行按钮
        self.addExecuteButton("开始统计", self.execute)
    
    def _addFileSelector(self):
        """添加GDB文件选择器"""
        layout = QHBoxLayout()
        layout.setSpacing(10)
        
        label = QLabel("GDB文件:", self)
        label.setFixedWidth(80)
        layout.addWidget(label)
        
        self.gdbLineEdit = LineEdit(self)
        self.gdbLineEdit.setPlaceholderText("请选择GDB文件")
        self.gdbLineEdit.setReadOnly(True)
        layout.addWidget(self.gdbLineEdit)
        
        browseBtn = PushButton("浏览", self, FIF.FOLDER)
        browseBtn.setFixedWidth(80)
        browseBtn.clicked.connect(self._selectGdbFile)
        layout.addWidget(browseBtn)
        
        self.contentLayout.addLayout(layout)
    
    def _addTemplateSelector(self):
        """添加模板文件选择器"""
        layout = QHBoxLayout()
        layout.setSpacing(10)
        
        label = QLabel("模板文件:", self)
        label.setFixedWidth(80)
        layout.addWidget(label)
        
        self.templateLineEdit = LineEdit(self)
        self.templateLineEdit.setPlaceholderText("可选，不选则生成基础统计表格")
        self.templateLineEdit.setReadOnly(True)
        layout.addWidget(self.templateLineEdit)
        
        browseBtn = PushButton("浏览", self, FIF.DOCUMENT)
        browseBtn.setFixedWidth(80)
        browseBtn.clicked.connect(self._selectTemplateFile)
        layout.addWidget(browseBtn)
        
        self.contentLayout.addLayout(layout)
    
    def _selectGdbFile(self):
        """选择GDB文件"""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.Directory)
        file_dialog.setWindowTitle("选择GDB文件")
        
        if file_dialog.exec():
            selected_path = file_dialog.selectedFiles()[0]
            # 检查是否为GDB文件（以.gdb结尾）
            if selected_path.endswith('.gdb'):
                self.gdb_path = selected_path
                self.gdbLineEdit.setText(selected_path)
            else:
                self.showError("请选择有效的GDB文件（以.gdb结尾）")
    
    def _selectTemplateFile(self):
        """选择模板文件"""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter("Excel文件 (*.xlsx)")
        file_dialog.setWindowTitle("选择模板Excel文件")
        
        if file_dialog.exec():
            selected_path = file_dialog.selectedFiles()[0]
            self.template_path = selected_path
            self.templateLineEdit.setText(selected_path)
    

    
    def validate(self) -> tuple[bool, str]:
        """验证输入参数"""
        if not self.gdb_path:
            return False, "请选择GDB文件"
        
        # 输出路径可选，不选则生成到模板路径下
        return True, ""
    
    def execute(self):
        """执行功能"""
        # 验证输入
        valid, msg = self.validate()
        if not valid:
            self.showError(msg)
            return
        
        # 生成输出路径
        import datetime
        current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"试划成果总结统计_{current_time}.xlsx"
        
        if self.template_path:
            # 如果有模板，输出到模板所在文件夹
            template_dir = os.path.dirname(self.template_path)
            output_path = os.path.join(template_dir, default_filename)
        else:
            # 否则输出到当前目录
            output_path = default_filename
        
        # 显示进度提示
        self.showProgress("正在执行试划成果总结统计...")
        
        # 创建并启动线程
        self.thread = TrialPlanSummaryThread(self.gdb_path, output_path, self.template_path, self)
        self.thread.success.connect(self._onSuccess)
        self.thread.error.connect(self._onError)
        self.thread.progress.connect(self.updateProgress)
        self.thread.start()
    
    def _onSuccess(self, message):
        """处理成功信号"""
        self.showSuccess(message)
    
    def _onError(self, message):
        """处理错误信号"""
        self.showError(message)
