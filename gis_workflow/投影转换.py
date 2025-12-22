#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
投影转换模块
实现数据投影定义和修改功能
"""

import os
import sys
import geopandas as gpd

# EPSG代码映射（与gis_workflow_interface.py中的保持一致）
epsg_codes = [4513, 4514, 4515, 4516, 4517, 4518, 4519, 4520, 4521, 4522, 4523, 
              4524, 4525, 4526, 4527, 4528, 4529, 4530, 4531, 4532, 4533, 4490]

def 定义数据投影(file_path, proj_index):
    """
    为无投影信息的矢量数据指定投影坐标系
    
    Args:
        file_path: 矢量文件路径
        proj_index: 投影索引（对应epsg_codes列表中的索引）
    """
    try:
        print(f"正在定义数据投影: {file_path}, 索引: {proj_index}")
        
        # 检查索引是否有效
        if 0 <= proj_index < len(epsg_codes):
            epsg_code = epsg_codes[proj_index]
            
            # 读取数据
            gdf = gpd.read_file(file_path)
            
            # 为数据设置投影，添加allow_override=True以允许覆盖现有CRS
            gdf = gdf.set_crs(f"EPSG:{epsg_code}", allow_override=True)
            
            # 生成输出文件路径（添加_prj后缀）
            base_path, ext = os.path.splitext(file_path)
            output_path = f"{base_path}_prj{ext}"
            
            # 保存文件
            gdf.to_file(output_path, encoding='utf-8')
            
            print(f"投影定义成功！输出文件: {output_path}")
            return output_path
        else:
            print(f"投影索引无效: {proj_index}")
            return False
            
    except Exception as e:
        print(f"定义数据投影时出错: {e}")
        return False

def 修改数据投影(file_path, proj_index):
    """
    将矢量数据从当前投影转换为指定投影
    
    Args:
        file_path: 矢量文件路径
        proj_index: 投影索引（对应epsg_codes列表中的索引）
    """
    try:
        print(f"正在修改数据投影: {file_path}, 索引: {proj_index}")
        
        # 检查索引是否有效
        if 0 <= proj_index < len(epsg_codes):
            epsg_code = epsg_codes[proj_index]
            
            # 读取数据
            gdf = gpd.read_file(file_path)
            
            # 检查数据是否已有投影
            if gdf.crs is None:
                print("警告：数据没有定义投影，将直接设置新投影")
                # 添加allow_override=True以允许覆盖现有CRS（如果存在）
                gdf = gdf.set_crs(f"EPSG:{epsg_code}", allow_override=True)
            else:
                # 转换投影
                gdf = gdf.to_crs(f"EPSG:{epsg_code}")
            
            # 生成输出文件路径（添加_prj后缀）
            base_path, ext = os.path.splitext(file_path)
            output_path = f"{base_path}_prj{ext}"
            
            # 保存文件
            gdf.to_file(output_path, encoding='utf-8')
            
            print(f"投影修改成功！输出文件: {output_path}")
            return output_path
        else:
            print(f"投影索引无效: {proj_index}")
            return False
            
    except Exception as e:
        print(f"修改数据投影时出错: {e}")
        return False

# 测试代码
if __name__ == "__main__":
    print("投影转换模块测试")
    print(f"支持的EPSG代码数量: {len(epsg_codes)}")
    print(f"EPSG代码列表: {epsg_codes}")