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
        
        # 遍历所有裁剪范围（外层循环）
        for value in unique_values:
            print(f"\n处理裁剪范围: {字段名} = {value}")
            
            # 筛选当前裁剪范围的矢量数据
            mask_gdf = gdf[gdf[字段名] == value]
            if mask_gdf.empty:
                if 警告回调:
                    警告回调(f"未找到字段值为 {value} 的矢量要素")
                continue
            
            # 遍历所有影像文件（内层循环）
            for image_file in image_files:
                completed_tasks += 1
                
                # 更新进度
                if 进度回调:
                    progress = int((completed_tasks / total_tasks) * 100)
                    进度回调(progress)
                
                print(f"\n处理影像: {image_file}")
                
                # 读取影像元数据
                with rasterio.open(image_file) as src:
                    src_crs = src.crs
                    src_transform = src.transform
                    print(f"影像坐标系: {src_crs}")
                    print(f"影像分辨率: {src_transform.a}, {src_transform.e}")
                
                # 检查矢量与影像坐标系是否一致
                gdf_epsg = None
                src_epsg = None
                
                try:
                    if gdf.crs:
                        gdf_epsg = gdf.crs.to_epsg()
                except Exception:
                    pass
                
                try:
                    if src_crs:
                        src_epsg = src_crs.to_epsg()
                except Exception:
                    pass
                
                # 为当前影像创建临时的矢量数据副本，避免多次修改原数据
                current_mask_gdf = mask_gdf.copy()
                
                # 如果EPSG代码相同，或者坐标系统字符串相同，则认为坐标系一致
                if gdf.crs == src_crs or (gdf_epsg and src_epsg and gdf_epsg == src_epsg):
                    print(f"坐标系一致，继续执行裁剪")
                else:
                    # 坐标系统不一致时，自动进行转换
                    print(f"转换矢量坐标系从 {gdf.crs} 到 {src_crs}")
                    current_mask_gdf = current_mask_gdf.to_crs(src_crs)
                
                # 应用缓冲
                if 缓冲距离 and 缓冲距离 > 0:
                    print(f"应用缓冲距离: {缓冲距离}")
                    current_mask_gdf['geometry'] = current_mask_gdf.geometry.buffer(缓冲距离)
                
                # 裁剪影像
                try:
                    with rasterio.open(image_file) as src:
                        # 获取几何列表
                        geometries = current_mask_gdf.geometry.tolist()
                        
                        # 裁剪影像
                        out_image, out_transform = mask(src, geometries, crop=True)
                        
                        # 检查裁剪结果是否为空
                        if out_image.shape[1] == 0 or out_image.shape[2] == 0:
                            print(f"跳过裁剪: {image_file}，原因：矢量与影像不重叠")
                            if 警告回调:
                                警告回调(f"跳过裁剪: {os.path.basename(image_file)}，原因：矢量与影像不重叠")
                            continue
                        
                        # 检查裁剪区域内是否所有像素都是0值
                        # 对每个波段计算非零像素数量
                        non_zero_count = 0
                        for band in range(out_image.shape[0]):
                            non_zero_count += np.count_nonzero(out_image[band])
                        
                        # 如果所有波段的所有像素都是0值，跳过裁剪
                        if non_zero_count == 0:
                            print(f"跳过裁剪: {image_file}，原因：裁剪区域内所有像素都是0值")
                            if 警告回调:
                                警告回调(f"跳过裁剪: {os.path.basename(image_file)}，原因：裁剪区域内所有像素都是0值")
                            continue
                        
                        # 更新元数据
                        out_meta = src.meta.copy()
                        out_meta.update({
                            'driver': 'GTiff',
                            'height': out_image.shape[1],
                            'width': out_image.shape[2],
                            'transform': out_transform
                        })
                        
                        # 根据字段值创建文件夹
                        field_folder = os.path.join(输出目录, f"{字段名}_{value}")
                        if not os.path.exists(field_folder):
                            os.makedirs(field_folder)
                        
                        # 生成输出文件名
                        base_name = os.path.splitext(os.path.basename(image_file))[0]
                        output_file = os.path.join(field_folder, f"{base_name}.tif")
                        
                        # 保存裁剪结果
                        with rasterio.open(output_file, 'w', **out_meta) as dst:
                            dst.write(out_image)
                        
                        print(f"裁剪完成，输出文件: {output_file}")
                        output_files.append(output_file)
                except Exception as e:
                    if "Input shapes do not overlap raster" in str(e) or "Intersection is empty" in str(e):
                        print(f"跳过裁剪: {image_file}，原因：矢量与影像不重叠")
                        if 警告回调:
                            警告回调(f"跳过裁剪: {os.path.basename(image_file)}，原因：矢量与影像不重叠")
                    else:
                        print(f"裁剪失败: {image_file}，原因：{str(e)}")
                        if 警告回调:
                            警告回调(f"裁剪失败: {os.path.basename(image_file)}，原因：{str(e)}")
        
        print(f"\n影像裁剪完成！")
        print(f"共生成 {len(output_files)} 个文件")
        return output_files
        
    except Exception as e:
        print(f"影像裁剪失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise Exception(f"影像裁剪失败: {str(e)}")


def 影像拼接(file_list_text, progress_callback=None, out_format='tif', out_res=None, output_name='mosaic_result', output_path=None):
    """
    影像拼接功能
    
    参数:
    file_list_text: 影像文件列表文本，每行一个文件路径
    progress_callback: 进度回调函数
    out_format: 输出格式，支持tif和img
    out_res: 输出分辨率，None表示使用默认分辨率
    output_name: 输出影像名称，默认为'mosaic_result'
    output_path: 输出文件路径，None表示自动生成
    
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
        reference_crs = None
        
        for file in file_list:
            src = rasterio.open(file)
            src_files_to_mosaic.append(src)
            print(f"添加影像: {file}")
            print(f"  影像坐标系: {src.crs}")
            
            # 检查坐标系是否一致
            if reference_crs is None:
                reference_crs = src.crs
            else:
                if src.crs != reference_crs:
                    # 关闭已打开的文件
                    for s in src_files_to_mosaic:
                        s.close()
                    raise Exception(f"影像坐标系不一致！\n" \
                                  f"文件 {file_list[0]} 的坐标系: {reference_crs}\n" \
                                  f"文件 {file} 的坐标系: {src.crs}\n" \
                                  f"请确保所有影像使用相同的坐标系。")
        
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
        if output_path is None:
            first_file_dir = os.path.dirname(file_list[0])
            output_file = os.path.join(first_file_dir, f"{output_name}.{out_format}")
        else:
            # 使用指定的输出路径
            output_file = output_path
        
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