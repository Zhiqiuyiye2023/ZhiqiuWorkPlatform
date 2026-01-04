# coding:utf-8
"""
验证修复后的消除功能，确保合并后的面包含原面的位置
"""

import geopandas as gpd
from shapely.geometry import Polygon, Point

# 读取输入文件和输出文件
input_path = "c:\Project\知秋工作平台\LCXZ_P_BSM_Identity_fixed_fixed.shp"
output_path = "c:\Project\知秋工作平台\eliminated_20251230_113048.shp"

input_gdf = gpd.read_file(input_path)
output_gdf = gpd.read_file(output_path)

print("输入文件包含", len(input_gdf), "个面要素")
print("输出文件包含", len(output_gdf), "个面要素")

# 需要验证的面：FID1和FID11
verify_fids = [1, 11]

# 检查每个需要验证的面
for fid in verify_fids:
    print(f"\n=== 验证FID{fid} ===")
    
    # 获取原面的几何形状
    original_geom = input_gdf.geometry.loc[fid]
    print(f"原面FID{fid}的面积: {original_geom.area:.6f}")
    print(f"原面FID{fid}的边界点: {list(original_geom.exterior.coords)[:3]}...")
    
    # 获取原面的中心点
    original_center = original_geom.centroid
    print(f"原面FID{fid}的中心点: {original_center}")
    
    # 检查原面的中心点是否在输出文件的某个面内
    found = False
    for i, output_geom in output_gdf.geometry.items():
        if output_geom.contains(original_center) or output_geom.distance(original_center) < 0.01:
            print(f"✓ 原面FID{fid}的中心点在输出面{i}内")
            print(f"输出面{i}的面积: {output_geom.area:.6f}")
            found = True
            break
    
    if not found:
        print(f"✗ 原面FID{fid}的中心点不在任何输出面内")
    
    # 检查原面的边界点是否在输出文件的某个面内
    boundary_points = list(original_geom.exterior.coords)
    missing_points = []
    for point in boundary_points[:5]:  # 检查前5个边界点
        pt = Point(point)
        in_any_polygon = False
        for i, output_geom in output_gdf.geometry.items():
            if output_geom.contains(pt) or output_geom.distance(pt) < 0.01:
                in_any_polygon = True
                break
        if not in_any_polygon:
            missing_points.append(point)
    
    if missing_points:
        print(f"✗ 原面FID{fid}的边界点不在任何输出面内: {missing_points}")
    else:
        print(f"✓ 原面FID{fid}的所有检查边界点都在输出面内")

print("\n=== 验证完成 ===")
