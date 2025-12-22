# coding:utf-8
"""
影像处理相关功能模块
"""

import os
import numpy as np
import geopandas as gpd


def 影像裁剪(
    影像路径,
    矢量路径,
    字段名,
    字段值=None,
    输出目录=None,
    进度回调=None,
    警告回调=None,
    缓冲距离=None,
    裁剪方式=None
):
    """
    根据矢量范围裁剪影像
    
    参数:
    影像路径: 影像文件路径，可以是单个文件路径或多行文本
    矢量路径: 矢量文件路径
    字段名: 用于裁剪的字段名
    字段值: 用于裁剪的字段值，None表示批量裁剪
    输出目录: 输出目录，None表示使用影像文件所在目录
    进度回调: 进度回调函数
    警告回调: 警告回调函数
    缓冲距离: 缓冲距离，单位与矢量坐标系一致
    
    返回:
    输出文件列表
    """
    
    try:
        # 延迟导入 rasterio，只在实际需要时导入
        import rasterio
        from rasterio.mask import mask
        
        print(f"\n开始影像裁剪处理")
        print(f"影像路径: {影像路径}")
        print(f"矢量路径: {矢量路径}")
        print(f"字段名: {字段名}")
        print(f"字段值: {字段值}")
        print(f"缓冲距离: {缓冲距离}")
        
        # 处理影像路径，支持多个文件
        if '\n' in 影像路径:
            image_files = [f.strip() for f in 影像路径.strip().split('\n') if f.strip()]
        else:
            image_files = [影像路径.strip()]
        
        print(f"处理影像数量: {len(image_files)}")
        
        # 读取矢量文件
        gdf = gpd.read_file(矢量路径)
        print(f"矢量要素数量: {len(gdf)}")
        print(f"矢量坐标系: {gdf.crs}")
        
        # 处理裁剪范围
        if 字段值 is None:
            # 批量裁剪，使用所有唯一值
            unique_values = gdf[字段名].unique()
            print(f"批量裁剪，共 {len(unique_values)} 个唯一值")
        else:
            # 单一裁剪，只使用指定字段值
            unique_values = [字段值]
            print(f"单一裁剪，字段值: {字段值}")
        
        # 确保输出目录存在
        if 输出目录 is None:
            输出目录 = os.path.dirname(image_files[0])
        os.makedirs(输出目录, exist_ok=True)
        
        output_files = []
        total_tasks = len(image_files) * len(unique_values)
        completed_tasks = 0
        
        # 遍历所有影像文件
        for image_file in image_files:
            print(f"\n处理影像: {image_file}")
            
            # 读取影像元数据
            with rasterio.open(image_file) as src:
                src_crs = src.crs
                src_transform = src.transform
                src_meta = src.meta.copy()
                print(f"影像坐标系: {src_crs}")
                print(f"影像分辨率: {src_transform.a}, {src_transform.e}")
            
            # 确保矢量与影像坐标系一致
            if gdf.crs != src_crs:
                print(f"转换矢量坐标系从 {gdf.crs} 到 {src_crs}")
                gdf = gdf.to_crs(src_crs)
            
            # 遍历所有裁剪范围
            for value in unique_values:
                completed_tasks += 1
                
                # 更新进度
                if 进度回调:
                    progress = int((completed_tasks / total_tasks) * 100)
                    进度回调(progress)
                
                print(f"\n裁剪范围: {字段名} = {value}")
                
                # 筛选当前裁剪范围的矢量数据
                mask_gdf = gdf[gdf[字段名] == value]
                if mask_gdf.empty:
                    if 警告回调:
                        警告回调(f"未找到字段值为 {value} 的矢量要素")
                    continue
                
                # 应用缓冲
                if 缓冲距离 and 缓冲距离 > 0:
                    print(f"应用缓冲距离: {缓冲距离}")
                    mask_gdf['geometry'] = mask_gdf.geometry.buffer(缓冲距离)
                
                # 裁剪影像
                with rasterio.open(image_file) as src:
                    # 获取几何列表
                    geometries = mask_gdf.geometry.tolist()
                    
                    # 裁剪影像
                    out_image, out_transform = mask(src, geometries, crop=True)
                    
                    # 更新元数据
                    out_meta = src.meta.copy()
                    out_meta.update({
                        'driver': 'GTiff',
                        'height': out_image.shape[1],
                        'width': out_image.shape[2],
                        'transform': out_transform
                    })
                    
                    # 生成输出文件名
                    base_name = os.path.splitext(os.path.basename(image_file))[0]
                    output_file = os.path.join(输出目录, f"{base_name}_{字段名}_{value}.tif")
                    
                    # 保存裁剪结果
                    with rasterio.open(output_file, 'w', **out_meta) as dst:
                        dst.write(out_image)
                    
                    print(f"裁剪完成，输出文件: {output_file}")
                    output_files.append(output_file)
        
        print(f"\n影像裁剪完成！")
        print(f"共生成 {len(output_files)} 个文件")
        return output_files
        
    except Exception as e:
        print(f"影像裁剪失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise Exception(f"影像裁剪失败: {str(e)}")


def 影像拼接(file_list_text, progress_callback=None, out_format='tif', out_res=None, output_name='mosaic_result'):
    """
    影像拼接功能
    
    参数:
    file_list_text: 影像文件列表文本，每行一个文件路径
    progress_callback: 进度回调函数
    out_format: 输出格式，支持tif和img
    out_res: 输出分辨率，None表示使用默认分辨率
    output_name: 输出影像名称，默认为'mosaic_result'
    
    返回:
    输出文件路径
    """
    
    try:
        # 延迟导入 rasterio，只在实际需要时导入
        import rasterio
        from rasterio.merge import merge
        from rasterio.warp import calculate_default_transform, reproject, Resampling
        
        print(f"\n开始影像拼接处理")
        print(f"输出格式: {out_format}")
        print(f"输出分辨率: {out_res}")
        
        # 解析文件列表
        file_list = [f.strip() for f in file_list_text.strip().split('\n') if f.strip()]
        print(f"处理影像数量: {len(file_list)}")
        
        if not file_list:
            raise ValueError("请至少选择一个影像文件")
        
        # 读取所有影像文件
        src_files_to_mosaic = []
        for file in file_list:
            src = rasterio.open(file)
            src_files_to_mosaic.append(src)
            print(f"添加影像: {file}")
        
        # 更新进度
        if progress_callback:
            progress_callback(20)
        
        # 合并影像
        print("开始合并影像...")
        mosaic, out_trans = merge(src_files_to_mosaic, res=out_res)
        
        # 更新进度
        if progress_callback:
            progress_callback(70)
        
        # 复制元数据
        out_meta = src_files_to_mosaic[0].meta.copy()
        
        # 更新元数据
        out_meta.update({
            "driver": "GTiff",
            "height": mosaic.shape[1],
            "width": mosaic.shape[2],
            "transform": out_trans,
            "crs": src_files_to_mosaic[0].crs
        })
        
        # 生成输出文件名
        first_file_dir = os.path.dirname(file_list[0])
        output_file = os.path.join(first_file_dir, f"{output_name}.{out_format}")
        
        # 保存合并结果
        print(f"保存拼接结果到: {output_file}")
        with rasterio.open(output_file, "w", **out_meta) as dest:
            dest.write(mosaic)
        
        # 关闭所有源文件
        for src in src_files_to_mosaic:
            src.close()
        
        # 更新进度
        if progress_callback:
            progress_callback(100)
        
        print(f"\n影像拼接完成！")
        print(f"输出文件: {output_file}")
        return output_file
        
    except Exception as e:
        print(f"影像拼接失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise Exception(f"影像拼接失败: {str(e)}")