# coding:utf-8
"""
坐标处理相关功能模块
"""

import os
import re
from datetime import datetime
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon, MultiPolygon
from pyproj import CRS


def 坐标转SHP格式(坐标串, 带号, 输出路径):
    """
    将坐标串转换为SHP矢量文件
    
    参数:
    坐标串: 坐标文本，支持多行格式，每行一个坐标点 (X,Y或X,Y,Z)
    带号: 投影带号，3度分带(≤39)或6度分带(>39)
    输出路径: 输出SHP文件的路径
    """
    if not 坐标串:
        raise ValueError("请输入坐标串")
    
    if not 输出路径:
        raise ValueError("请选择输出文件路径")
    
    try:
        print(f"\n开始处理坐标转SHP:")
        print(f"带号: {带号}")
        print(f"输出路径: {输出路径}")
        
        # 解析坐标串
        parts = 坐标串.strip().split('|')  # 支持多部件
        print(f"解析到 {len(parts)} 个部件")
        
        geometries = []
        
        for part_idx, part in enumerate(parts):
            print(f"\n处理第 {part_idx+1} 个部件:")
            coords = []
            lines = part.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 支持多种坐标格式
                # 1. 征地部格式：J1,1,X,Y 或 J2,1,X,Y
                # 2. 普通格式：X,Y 或 X Y 或 X;Y
                try:
                    # 检查是否为征地部格式
                    if line.startswith('J') and ',' in line:
                        coords_parts = line.split(',')
                        if len(coords_parts) >= 4:
                            # 征地部格式：J1,1,Y,X（用户指出XY坐标搞反了）
                            y = float(coords_parts[2])
                            x = float(coords_parts[3])
                            coords.append((x, y))
                            print(f"解析征地部坐标: ({x}, {y}) (Y={coords_parts[2]}, X={coords_parts[3]})")
                        else:
                            print(f"跳过无效征地部坐标行: {line}")
                    else:
                        # 普通格式，支持多种分隔符：逗号、冒号、空格等
                        coords_list = re.split(r'[,;:\s]+', line)
                        if len(coords_list) >= 2:
                            x = float(coords_list[0])
                            y = float(coords_list[1])
                            coords.append((x, y))
                            print(f"解析普通坐标: ({x}, {y})")
                        else:
                            print(f"跳过无效坐标行: {line}")
                except ValueError as e:
                    print(f"跳过无效坐标行: {line}，错误: {str(e)}")
            
            if len(coords) < 2:
                print(f"部件 {part_idx+1} 坐标点不足，跳过")
                continue
            
            # 处理几何类型
            if len(coords) == 2:
                # 线
                line = LineString(coords)
                geometries.append(line)
                print(f"创建线要素")
            elif len(coords) >= 3:
                # 检查是否闭合
                if coords[0] == coords[-1]:
                    # 多边形
                    polygon = Polygon(coords)
                    geometries.append(polygon)
                    print(f"创建多边形要素，{len(coords)} 个坐标点")
                else:
                    # 闭合多边形
                    coords.append(coords[0])
                    polygon = Polygon(coords)
                    geometries.append(polygon)
                    print(f"创建闭合多边形要素，{len(coords)} 个坐标点")
            else:
                # 点
                point = Point(coords[0])
                geometries.append(point)
                print(f"创建点要素")
        
        if not geometries:
            raise Exception("没有有效的几何对象可以转换")
        
        # 确定坐标系
        # 修正带号处理：3度分带和6度分带的EPSG代码生成
        # 3度分带：EPSG:326XX (XX为带号，范围1-60)
        # 6度分带：EPSG:327XX (XX为带号，范围1-60)
        # 通常带号范围为1-60，所以需要确保带号在有效范围内
        valid_带号 = 带号 % 60 if 带号 > 60 else 带号
        valid_带号 = max(1, min(60, valid_带号))  # 确保带号在1-60范围内
        
        if 带号 <= 39:
            # 3度分带，使用EPSG:326XX
            epsg = 32600 + valid_带号
            print(f"使用3度分带，带号: {valid_带号}，EPSG: {epsg}")
        else:
            # 6度分带，使用EPSG:327XX
            epsg = 32700 + valid_带号
            print(f"使用6度分带，带号: {valid_带号}，EPSG: {epsg}")
        
        # 创建GeoDataFrame，不设置坐标系
        gdf = gpd.GeoDataFrame({
            'geometry': geometries,
            '名称': [f'要素_{i+1}' for i in range(len(geometries))]
        }, crs=None)
        
        # 保存为SHP文件
        gdf.to_file(输出路径, encoding='utf-8')
        
        print(f"\n坐标转SHP成功！")
        print(f"输出文件: {输出路径}")
        return 输出路径  # 修正：使用中文参数名
        
    except Exception as e:
        print(f"坐标转SHP过程中出现错误: {str(e)}")
        import traceback
        print(f"错误堆栈: {traceback.format_exc()}")
        raise Exception(f"坐标转SHP格式失败: {str(e)}")


def 征地部坐标转换(文件路径, 输出目录, 合并地块=True):
    """
    征地部坐标转换功能
    
    参数:
    文件路径: 输入文件路径
    输出目录: 输出目录路径
    合并地块: 是否将所有地块合并为一个SHP文件，默认为True
    """
    if not 文件路径:
        raise ValueError("请选择输入文件")
    
    if not 输出目录:
        raise ValueError("请选择输出目录")
    
    try:
        print(f"\n开始处理征地部坐标转换:")
        print(f"输入文件: {文件路径}")
        print(f"输出目录: {输出目录}")
        
        # 读取征地部坐标文件，尝试不同的编码方式
        content = None
        encodings = ['utf-8', 'gbk', 'gb2312', 'ansi']
        
        for encoding in encodings:
            try:
                with open(文件路径, 'r', encoding=encoding) as f:
                    content = f.read()
                print(f"使用 {encoding} 编码成功读取文件，共 {len(content)} 字符")
                break
            except UnicodeDecodeError as e:
                print(f"尝试 {encoding} 编码失败: {str(e)}")
                continue
        
        if content is None:
            raise Exception("无法读取文件，请检查文件编码格式")
        
        base_name = os.path.splitext(os.path.basename(文件路径))[0]
        
        # 解析征地部坐标文件格式
        # 文件结构：
        # [文件头]
        # 格式版本号=
        # ...
        # [地块数据]
        # 地块1属性行,1,地块1,平,...
        # J1,1,X,Y
        # J2,1,X,Y
        # ...
        # J1,1,X,Y  # 闭合点
        # 地块2属性行,10,地块10,平,...
        # J1,1,X,Y
        # ...
        
        blocks = []
        current_block = []
        lines = content.strip().split('\n')
        
        # 跳过文件头，找到地块数据部分
        in_data_section = False
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检查是否进入数据部分（更宽松的条件）
            # 1. 检查是否包含[地块数据]或类似乱码标记
            # 2. 如果遇到可能的属性行也直接进入数据部分
            if '[地块数据]' in line or '[�ؿ' in line or line and line[0].isdigit() and ',' in line:
                in_data_section = True
            
            if not in_data_section:
                continue
            
            # 识别地块属性行：以数字开头，包含逗号分隔的属性
            is_property_line = False
            try:
                # 更宽松的属性行识别：只要以数字开头且包含逗号
                if line and line[0].isdigit() and ',' in line:
                    # 进一步验证是否包含地块名称字段
                    fields = line.split(',')
                    # 征地部属性行格式：面积,周长,编号,地块名称,地类,...
                    if len(fields) >= 4:
                        is_property_line = True
            except:
                pass
            
            if is_property_line:
                # 如果当前已有地块数据，先保存
                if current_block:
                    blocks.append(current_block)
                    current_block = []
                # 开始新地块
                current_block.append(line)
            else:
                # 添加坐标行到当前地块
                current_block.append(line)
        
        # 添加最后一个地块
        if current_block:
            blocks.append(current_block)
        
        print(f"解析到 {len(blocks)} 个地块")
        
        # 处理地块
        if 合并地块 and len(blocks) > 1:
            # 合并地块模式：收集所有地块的几何信息
            print(f"\n=== 合并地块模式 ===")
            
            # 收集所有地块的坐标和名称
            all_geometries = []
            all_names = []
            all_coords_info = []
            
            # 提取带号（从第一个地块提取）
            带号 = 35  # 默认带号
            if blocks:
                first_block = blocks[0]
                if len(first_block) >= 2:
                    坐标行_list = first_block[1:]
                    if 坐标行_list:
                        first_coord_line = 坐标行_list[0].strip()
                        coords_parts = first_coord_line.split(',')
                        if len(coords_parts) >= 3:
                            try:
                                x = float(coords_parts[2])
                                # 提取带号：假设X坐标为6位或8位，前两位或三位为带号
                                if x > 1000000:
                                    # 8位坐标，前三位为带号
                                    带号 = int(str(int(x))[:3])
                                else:
                                    # 6位坐标，前两位为带号
                                    带号 = int(str(int(x))[:2])
                                print(f"从第一个地块提取到带号: {带号}")
                            except Exception as e:
                                print(f"无法提取带号，使用默认带号: {str(e)}")
            
            # 处理每个地块，收集坐标信息
            for block_idx, block in enumerate(blocks):
                if not block or len(block) < 2:
                    continue
                
                # 提取地块名称和坐标
                属性行 = block[0]
                坐标行_list = block[1:]
                
                # 从属性行提取地块名称
                地块名称 = f"地块{block_idx+1}"  # 默认名称
                try:
                    fields = 属性行.split(',')
                    if len(fields) >= 4:
                        地块名称 = fields[3].strip()
                except Exception as e:
                    print(f"解析地块名称失败: {str(e)}")
                    continue
                
                print(f"\n收集地块 {block_idx+1}: {地块名称}")
                print(f"坐标行数: {len(坐标行_list)}")
                
                # 提取坐标点
                coords = []
                for line in 坐标行_list:
                    line = line.strip()
                    if not line:
                        continue
                    
                    if line.startswith('J') and ',' in line:
                        coords_parts = line.split(',')
                        if len(coords_parts) >= 4:
                            try:
                                # 征地部格式：J1,1,Y,X（用户指出XY坐标搞反了）
                                y = float(coords_parts[2])
                                x = float(coords_parts[3])
                                coords.append((x, y))
                            except ValueError as e:
                                print(f"跳过无效坐标行: {line}")
                                continue
                
                if len(coords) < 3:
                    print(f"地块 {block_idx+1} 坐标点不足，跳过")
                    continue
                
                # 创建多边形
                if coords[0] != coords[-1]:
                    coords.append(coords[0])  # 闭合多边形
                
                polygon = Polygon(coords)
                all_geometries.append(polygon)
                all_names.append(地块名称)
                all_coords_info.append((coords, 地块名称))
            
            if all_geometries:
                # 生成输出文件名
                shp_name = f"{base_name}_合并地块.shp"
                output_path = os.path.join(输出目录, shp_name)
                
                # 确定坐标系
                # 修正带号处理：3度分带和6度分带的EPSG代码生成
                # 3度分带：EPSG:326XX (XX为带号，范围1-60)
                # 6度分带：EPSG:327XX (XX为带号，范围1-60)
                # 通常带号范围为1-60，所以需要确保带号在有效范围内
                valid_带号 = 带号 % 60 if 带号 > 60 else 带号
                valid_带号 = max(1, min(60, valid_带号))  # 确保带号在1-60范围内
                
                if 带号 <= 39:
                    # 3度分带，使用EPSG:326XX
                    epsg = 32600 + valid_带号
                    print(f"使用3度分带，带号: {valid_带号}，EPSG: {epsg}")
                else:
                    # 6度分带，使用EPSG:327XX
                    epsg = 32700 + valid_带号
                    print(f"使用6度分带，带号: {valid_带号}，EPSG: {epsg}")
                
                # 创建GeoDataFrame，不设置坐标系
                gdf = gpd.GeoDataFrame({
                    'geometry': all_geometries,
                    '名称': all_names
                }, crs=None)
                
                # 保存为SHP文件
                gdf.to_file(output_path, encoding='utf-8')
                
                print(f"\n合并地块转换成功！")
                print(f"输出文件: {output_path}")
                print(f"共包含 {len(all_geometries)} 个地块要素")
                
                output_files = [output_path]
            else:
                print(f"没有有效的地块可以合并")
                output_files = []
        else:
            # 非合并地块模式：为每个地块生成一个独立的SHP文件
            output_files = []
            for block_idx, block in enumerate(blocks):
                if not block:
                    continue
                
                # 提取地块名称和坐标
                if len(block) >= 2:
                    # 地块属性行为第一行，后续行为坐标
                    属性行 = block[0]
                    坐标行_list = block[1:]
                    
                    # 从属性行提取地块名称
                    地块名称 = f"地块{block_idx+1}"  # 默认名称
                    try:
                        # 解析属性行，格式：面积,周长,编号,地块名称,地类,...
                        fields = 属性行.split(',')
                        if len(fields) >= 4:
                            地块名称 = fields[3].strip()
                    except Exception as e:
                        print(f"解析地块名称失败: {str(e)}")
                        continue
                    
                    print(f"\n处理地块 {block_idx+1}: {地块名称}")
                    print(f"属性行: {属性行}")
                    print(f"坐标行数: {len(坐标行_list)}")
                    
                    # 提取坐标串
                    坐标串 = '\n'.join(坐标行_list)
                    
                    # 提取带号（假设坐标X值的前两位或三位为带号）
                    带号 = 35  # 默认带号
                    
                    # 尝试从坐标中提取带号
                    if 坐标串:
                        first_coord_line = 坐标串.split('\n')[0].strip()
                        if first_coord_line:
                            # 解析坐标行，格式：J1,1,X,Y
                            coords_parts = first_coord_line.split(',')
                            if len(coords_parts) >= 3:
                                try:
                                    x = float(coords_parts[2])
                                    # 提取带号：假设X坐标为6位或8位，前两位或三位为带号
                                    if x > 1000000:
                                        # 8位坐标，前三位为带号
                                        带号 = int(str(int(x))[:3])
                                    else:
                                        # 6位坐标，前两位为带号
                                        带号 = int(str(int(x))[:2])
                                    print(f"从坐标中提取到带号: {带号}")
                                except Exception as e:
                                    print(f"无法提取带号，使用默认带号: {str(e)}")
                    
                    # 生成输出文件名
                    shp_name = f"{base_name}_{地块名称}_{block_idx+1}.shp"
                    output_path = os.path.join(输出目录, shp_name)
                    
                    # 调用坐标转SHP格式函数
                    try:
                        shp_file = 坐标转SHP格式(坐标串, 带号, output_path)
                        output_files.append(shp_file)
                        print(f"地块 {block_idx+1} 转换成功")
                    except Exception as e:
                        print(f"地块 {block_idx+1} 转换失败: {str(e)}")
                        continue
            
        if not output_files:
            # 如果没有生成任何SHP文件，尝试将整个文件作为一个地块处理
            print(f"\n尝试将整个文件作为一个地块处理")
            地块名称 = "地块"
            坐标串 = content.strip()
            
            # 提取带号
            带号 = 35  # 默认带号
            if 坐标串:
                first_coord_line = 坐标串.split('\n')[0].strip()
                if first_coord_line and ',' in first_coord_line:
                    coords_parts = first_coord_line.split(',')
                    if len(coords_parts) >= 3:
                        try:
                            x = float(coords_parts[2])
                            if x > 1000000:
                                带号 = int(str(int(x))[:3])
                            else:
                                带号 = int(str(int(x))[:2])
                            print(f"从坐标中提取到带号: {带号}")
                        except:
                            print("无法提取带号，使用默认带号")
            
            # 生成输出文件名
            shp_name = f"{base_name}_地块.shp"
            output_path = os.path.join(输出目录, shp_name)
            
            # 调用坐标转SHP格式函数
            try:
                shp_file = 坐标转SHP格式(坐标串, 带号, output_path)
                output_files.append(shp_file)
                print(f"整个文件转换成功")
            except Exception as e:
                print(f"整个文件转换失败: {str(e)}")
                raise Exception(f"征地部坐标转换失败: 无法处理文件内容")
        
        print(f"\n征地部坐标转换完成！")
        print(f"共生成 {len(output_files)} 个SHP文件")
        for file_path in output_files:
            print(f"- {file_path}")
        
        return output_files
        
    except Exception as e:
        print(f"征地部坐标转换过程中出现错误: {str(e)}")
        import traceback
        print(f"错误堆栈: {traceback.format_exc()}")
        raise Exception(f"征地部坐标转换失败: {str(e)}")
